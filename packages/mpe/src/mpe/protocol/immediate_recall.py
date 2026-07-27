"""Immediate Recall protocol runner using the existing MPE Runtime."""

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
from mpe.protocol.fixture_minimal import (
    AdaptationRule,
    FixtureItem,
    ImmediateRecallFixture,
    default_adaptation_rule,
    make_minimal_fixture,
)
from mpe.protocol.providers import FixtureProviderSet
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
from mpe.runtime import Clock, Runtime, WallClock
from mpe.types import (
    BlockID,
    ProtocolVersionID,
    SessionID,
    TrialID,
    make_id,
)


@dataclass(frozen=True)
class ItemOutcome:
    """Per-item execution result."""

    content_item_id: str
    self_confirmation: str
    latency: float
    repeats_used: int
    answer_status: str


@dataclass(frozen=True)
class ImmediateRecallResult:
    """Result of a complete Immediate Recall session."""

    runtime: Runtime
    state: RuntimeState
    events: list[Event]
    item_outcomes: list[ItemOutcome]
    fixture: ImmediateRecallFixture
    rule: AdaptationRule


class ImmediateRecallRunner:
    """Execute the Immediate Recall protocol over the existing MPE Runtime."""

    def __init__(
        self,
        store: EventStore,
        fixture: ImmediateRecallFixture | None = None,
        rule: AdaptationRule | None = None,
        clock: Clock | None = None,
        wall_clock: WallClock | None = None,
    ) -> None:
        self.fixture = fixture or make_minimal_fixture()
        self.rule = rule or default_adaptation_rule()
        self.clock = clock or Clock()
        self.providers = FixtureProviderSet(self.fixture).set
        self.runtime = Runtime(store, self.providers, self.clock, wall_clock)
        self.pipeline = TrialPipeline(self.runtime, self.providers)
        self.item_outcomes: list[ItemOutcome] = []
        self._trial_index = 0

    def run_session(
        self,
        learner_id: str,
        random_seed: str = "seed_0",
        session_id: SessionID | None = None,
    ) -> ImmediateRecallResult:
        """Plan and execute an Immediate Recall session, persisting all events."""
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

        plan: BoundedRepeatPlan[FixtureItem] = BoundedRepeatPlan(
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
        return ImmediateRecallResult(
            runtime=self.runtime,
            state=state,
            events=events,
            item_outcomes=self.item_outcomes,
            fixture=self.fixture,
            rule=self.rule,
        )

    def _repeat_decision(self, outcome: ItemOutcome) -> RepeatDecision:
        """Immediate Recall repeat rule: behavior first, then latency."""
        if outcome.self_confirmation == "negative":
            return RepeatDecision(True, SOURCE_BEHAVIOR, "self_confirmation_negative")
        if outcome.latency > self.rule.latency_bound:
            return RepeatDecision(True, SOURCE_LATENCY, "latency_above_bound")
        return RepeatDecision.none()

    def _execute_item_trial(
        self,
        item: FixtureItem,
        block_id: BlockID,
        repeat: RepeatMetadata,
        repeats_used: int,
    ) -> ItemOutcome:
        self._trial_index += 1
        trial_id = TrialID(str(make_id(TrialID)))
        trial_index = self._trial_index

        content_item = ContentItem(
            content_item_id=item.content_item_id,
            provider_id="fixture",
            provider_version="1.0.0",
            content_type="fixture_item",
            checksum="fixture_checksum",
            surface_form=item.content_item_id,
            normalized_form=item.content_item_id,
            metadata={"expected_relation": item.expected_relation},
        )

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
        )

        # 1. Present cue (prompt).
        pipeline.emit_instruction(
            trial_id,
            InstructionSpec(
                instruction_type=InstructionType.PRESENT_STIMULUS,
                payload=f"Recall the target for {item.content_item_id}",
                target_operation="covert_recall",
                duration=1.0,
                observable_response_expected=False,
            ),
        )
        pipeline.emit_stimulus(
            trial_id,
            StimulusSpec(
                content_item_id=item.content_item_id,
                asset_role="prompt",
                renderer_id="fixture_renderer",
            ),
        )

        # 2. Open anticipation/self-confirmation window.
        pipeline.emit_instruction(
            trial_id,
            InstructionSpec(
                instruction_type=InstructionType.REQUEST_OVERT_RESPONSE,
                payload="Indicate whether you recalled the target: positive or negative",
                target_operation="self_confirm",
                duration=3.0,
                observable_response_expected=True,
            ),
        )
        response_window_id = pipeline.open_response_window(
            trial_id,
            ResponseWindowSpec(response_modes=(ResponseMode.TOUCH.value,)),
        )

        # 3. Collect deterministic self-confirmation observation.
        observation_spec = ObservationSpec(
            injection=f"{item.latency}:{item.self_confirmation}",
            provider_id="fixture_self_confirmation",
        )
        observation = pipeline.poll_observation(observation_spec)
        self_confirmation = observation.raw_payload
        latency = observation.latency
        received_at = self.runtime.clock.now()
        pipeline.emit_observation_received(
            trial_id,
            response_window_id,
            observation_spec,
            observation,
            payload_value=self_confirmation,
            received_at=received_at,
        )

        # 4. Response pipeline (captured -> interpreted -> normalized -> evaluated).
        normalized = pipeline.run_response_pipeline(
            trial_id,
            response_window_id,
            observation,
            captured_payload=self_confirmation,
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

        # 5. Present confirmation (correct target).
        pipeline.emit_instruction(
            trial_id,
            InstructionSpec(
                instruction_type=InstructionType.PRESENT_STIMULUS,
                payload=f"Target for {item.content_item_id}",
                target_operation="confirm",
                duration=1.0,
                observable_response_expected=False,
            ),
        )
        pipeline.emit_stimulus(
            trial_id,
            StimulusSpec(
                content_item_id=item.content_item_id,
                asset_role="confirmation",
                renderer_id="fixture_renderer",
            ),
        )

        # 6. Mark trial completed.
        pipeline.emit_feedback(
            trial_id,
            FeedbackSpec(
                feedback_category=FeedbackCategory.KNOWLEDGE,
                feedback_type=FeedbackType.CORRECT_ANSWER,
                content_item_id=item.content_item_id,
            ),
        )

        answer_status = (
            AnswerStatus.CORRECT.value
            if self_confirmation == "positive"
            else AnswerStatus.INCORRECT.value
        )
        return ItemOutcome(
            content_item_id=item.content_item_id,
            self_confirmation=self_confirmation,
            latency=latency,
            repeats_used=repeats_used,
            answer_status=answer_status,
        )



def run_immediate_recall_session(
    store: EventStore,
    learner_id: str = "learner_001",
    random_seed: str = "seed_0",
    session_id: SessionID | None = None,
    fixture: ImmediateRecallFixture | None = None,
    rule: AdaptationRule | None = None,
    clock: Clock | None = None,
    wall_clock: WallClock | None = None,
) -> ImmediateRecallResult:
    """High-level entry point for running an Immediate Recall session."""
    runner = ImmediateRecallRunner(
        store, fixture=fixture, rule=rule, clock=clock, wall_clock=wall_clock
    )
    return runner.run_session(
        learner_id=learner_id,
        random_seed=random_seed,
        session_id=session_id,
    )
