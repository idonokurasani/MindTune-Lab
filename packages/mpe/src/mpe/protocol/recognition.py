"""Recognition protocol runner using the existing MPE Runtime."""

from __future__ import annotations

from dataclasses import dataclass

from mpe.aggregates import RuntimeState
from mpe.enums import (
    AnswerStatus,
    BlockType,
    FeedbackCategory,
    FeedbackType,
    InstructionType,
    ResponseMode,
    ResponseRequirement,
)
from mpe.event_store import EventStore
from mpe.events import Event
from mpe.protocol.bounded_repeat import (
    SOURCE_BEHAVIOR,
    SOURCE_LATENCY,
    BoundedRepeatPlan,
    RepeatDecision,
    RepeatMetadata,
)
from mpe.protocol.fixture_minimal import AdaptationRule, default_adaptation_rule
from mpe.protocol.fixture_recognition import (
    RecognitionFixture,
    RecognitionFixtureItem,
    make_minimal_recognition_fixture,
)
from mpe.protocol.providers_recognition import RecognitionProviderSet
from mpe.protocol.trial_pipeline import (
    FeedbackSpec,
    InstructionSpec,
    ObservationSpec,
    ResponseWindowSpec,
    StimulusSpec,
    TrialIdentity,
    TrialPipeline,
)
from mpe.providers import ContentItem
from mpe.runtime import Clock, Runtime
from mpe.types import (
    BlockID,
    ProtocolVersionID,
    SessionID,
    TrialID,
    make_id,
)


@dataclass(frozen=True)
class RecognitionItemOutcome:
    """Per-item execution result for Recognition."""

    content_item_id: str
    selected_choice_index: int
    correct_choice_index: int
    latency: float
    repeats_used: int
    answer_status: str


@dataclass(frozen=True)
class RecognitionResult:
    """Result of a complete Recognition session."""

    runtime: Runtime
    state: RuntimeState
    events: list[Event]
    item_outcomes: list[RecognitionItemOutcome]
    fixture: RecognitionFixture
    rule: AdaptationRule


class RecognitionRunner:
    """Execute the Recognition protocol over the existing MPE Runtime."""

    def __init__(
        self,
        store: EventStore,
        fixture: RecognitionFixture | None = None,
        rule: AdaptationRule | None = None,
        clock: Clock | None = None,
    ) -> None:
        self.fixture = fixture or make_minimal_recognition_fixture()
        self.rule = rule or default_adaptation_rule()
        self.clock = clock or Clock()
        self.providers = RecognitionProviderSet(self.fixture).set
        self.runtime = Runtime(store, self.providers, self.clock)
        self.pipeline = TrialPipeline(self.runtime, self.providers)
        self.item_outcomes: list[RecognitionItemOutcome] = []
        self._trial_index = 0

    def run_session(
        self,
        learner_id: str,
        random_seed: str = "seed_0",
        session_id: SessionID | None = None,
    ) -> RecognitionResult:
        """Plan and execute a Recognition session, persisting all events."""
        protocol_version_id = ProtocolVersionID(self.fixture.protocol_version_id)

        self.runtime.create_session(
            program_version_id=self.fixture.program_version_id,
            protocol_version_id=protocol_version_id,
            learner_id=learner_id,
            session_id=session_id,
        )
        self.runtime.start_session(
            random_seed=random_seed,
            start_parameters={"fixture_id": self.fixture.fixture_id},
        )

        block_id = BlockID(self.fixture.block_id)
        self.pipeline.emit_block_started(block_id, BlockType.PRACTICE.value)

        plan: BoundedRepeatPlan[RecognitionFixtureItem] = BoundedRepeatPlan(
            self.fixture.items,
            cap=self.rule.repeat_cap,
            key=lambda fixture_item: fixture_item.content_item_id,
        )
        for step in plan:
            outcome = self._execute_item_trial(
                item=step.item,
                block_id=block_id,
                repeat=step.metadata,
                repeats_used=step.repeats_used,
            )
            self.item_outcomes.append(outcome)
            step.record(self._repeat_decision(outcome))

        self.pipeline.emit_block_completed(
            block_id, completed_trial_count=len(self.item_outcomes)
        )
        self.runtime.complete_session(final_trial_index=self._trial_index)

        state = self.runtime.state
        assert self.runtime.state.session_id is not None
        events = self.runtime.store.read(self.runtime.state.session_id)
        return RecognitionResult(
            runtime=self.runtime,
            state=state,
            events=events,
            item_outcomes=self.item_outcomes,
            fixture=self.fixture,
            rule=self.rule,
        )

    def _repeat_decision(self, outcome: RecognitionItemOutcome) -> RepeatDecision:
        """Recognition repeat rule: behavior takes precedence over latency."""
        if outcome.answer_status == AnswerStatus.INCORRECT.value:
            return RepeatDecision(True, SOURCE_BEHAVIOR, "incorrect_choice")
        if outcome.latency > self.rule.latency_bound:
            return RepeatDecision(True, SOURCE_LATENCY, "latency_above_bound")
        return RepeatDecision.none()

    def _execute_item_trial(
        self,
        item: RecognitionFixtureItem,
        block_id: BlockID,
        repeat: RepeatMetadata,
        repeats_used: int,
    ) -> RecognitionItemOutcome:
        self._trial_index += 1
        trial_id = TrialID(str(make_id(TrialID)))
        trial_index = self._trial_index

        content_item = ContentItem(
            content_item_id=item.content_item_id,
            provider_id="fixture_recognition",
            provider_version="1.0.0",
            content_type="fixture_recognition_item",
            checksum="fixture_checksum",
            surface_form=item.content_item_id,
            normalized_form=item.content_item_id,
            metadata={"correct_choice_index": item.correct_choice_index},
        )

        choice_count = len(item.assets)

        pipeline = self.pipeline
        pipeline.emit_trial_created(
            TrialIdentity(
                trial_id=trial_id,
                block_id=block_id,
                trial_index=trial_index,
                task_definition_id=self.fixture.task_definition_id,
                content_item_ids=(item.content_item_id,),
            ),
            repeat=repeat,
            response_requirement=ResponseRequirement.REQUIRED.value,
            accepted_response_modes=[ResponseMode.TOUCH.value],
            extensions={
                "correct_choice_index": item.correct_choice_index,
                "choice_count": choice_count,
            },
        )

        # 1. Present the prompt/instruction.
        pipeline.emit_instruction(
            trial_id,
            InstructionSpec(
                instruction_type=InstructionType.PRESENT_STIMULUS,
                payload=f"Select the correct choice for {item.content_item_id}",
                target_operation="discrete_choice",
                duration=1.0,
                observable_response_expected=False,
            ),
        )

        # 2. Render each choice as a separate stimulus, in choice order.
        pipeline.emit_stimuli(
            trial_id,
            [
                StimulusSpec(
                    content_item_id=item.content_item_id,
                    asset_role=f"choice_{choice_index}",
                    renderer_id="fixture_recognition_renderer",
                )
                for choice_index in range(choice_count)
            ],
        )

        # 3. Open the response window.
        pipeline.emit_instruction(
            trial_id,
            InstructionSpec(
                instruction_type=InstructionType.REQUEST_OVERT_RESPONSE,
                payload="Touch the correct choice",
                target_operation="select_choice",
                duration=3.0,
                observable_response_expected=True,
            ),
        )
        response_window_id = pipeline.open_response_window(
            trial_id,
            ResponseWindowSpec(response_modes=(ResponseMode.TOUCH.value,)),
        )

        # 4. Collect deterministic discrete-choice observation.
        observation_spec = ObservationSpec(
            injection=f"{item.latency}:{item.selected_choice_index}",
            provider_id="fixture_recognition_choice",
        )
        observation = pipeline.poll_observation(observation_spec)
        selected_choice_index = int(observation.raw_payload)
        latency = observation.latency
        received_at = self.runtime.clock.now()
        pipeline.emit_observation_received(
            trial_id,
            response_window_id,
            observation_spec,
            observation,
            payload_value=selected_choice_index,
            received_at=received_at,
        )

        # 5. Response pipeline.
        normalized = pipeline.run_response_pipeline(
            trial_id,
            response_window_id,
            observation,
            captured_payload=str(selected_choice_index),
            response_mode=ResponseMode.TOUCH.value,
            captured_at=received_at,
            device_provenance=["fixture_button_0"],
        )
        pipeline.emit_evaluation(
            trial_id,
            normalized,
            content_item,
            response_mode=ResponseMode.TOUCH.value,
            protocol_version_id=self.fixture.protocol_version_id,
        )

        # 6. Present feedback (correct target or incorrect indicator).
        answer_status = (
            AnswerStatus.CORRECT.value
            if selected_choice_index == item.correct_choice_index
            else AnswerStatus.INCORRECT.value
        )
        feedback_type = (
            FeedbackType.CORRECT_ANSWER
            if answer_status == AnswerStatus.CORRECT.value
            else FeedbackType.INCORRECT_INDICATOR
        )
        pipeline.emit_feedback(
            trial_id,
            FeedbackSpec(
                feedback_category=FeedbackCategory.KNOWLEDGE,
                feedback_type=feedback_type,
                content_item_id=item.content_item_id,
            ),
        )

        return RecognitionItemOutcome(
            content_item_id=item.content_item_id,
            selected_choice_index=selected_choice_index,
            correct_choice_index=item.correct_choice_index,
            latency=latency,
            repeats_used=repeats_used,
            answer_status=answer_status,
        )



def run_recognition_session(
    store: EventStore,
    learner_id: str = "learner_001",
    random_seed: str = "seed_0",
    session_id: SessionID | None = None,
    fixture: RecognitionFixture | None = None,
    rule: AdaptationRule | None = None,
    clock: Clock | None = None,
) -> RecognitionResult:
    """High-level entry point for running a Recognition session."""
    runner = RecognitionRunner(store, fixture=fixture, rule=rule, clock=clock)
    return runner.run_session(
        learner_id=learner_id,
        random_seed=random_seed,
        session_id=session_id,
    )
