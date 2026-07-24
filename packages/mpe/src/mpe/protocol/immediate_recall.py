"""Immediate Recall protocol runner using the existing MPE Runtime."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from mpe.aggregates import RuntimeState
from mpe.enums import (
    AnswerStatus,
    BlockType,
    DataClassification,
    FeedbackCategory,
    FeedbackType,
    InstructionType,
    ResponseMode,
    ResponseRequirement,
)
from mpe.errors import ProviderFailureError
from mpe.event_store import EventStore
from mpe.events import Event
from mpe.protocol.fixture_minimal import (
    AdaptationRule,
    FixtureItem,
    ImmediateRecallFixture,
    default_adaptation_rule,
    make_minimal_fixture,
)
from mpe.protocol.providers import FixtureProviderSet
from mpe.providers import ContentItem, TrialContext
from mpe.runtime import Clock, Runtime
from mpe.types import (
    BlockID,
    CapturedResponseID,
    EventID,
    FeedbackEventID,
    InstructionID,
    ObservationID,
    ProtocolVersionID,
    ResponseWindowID,
    SessionID,
    StimulusRequestID,
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
    ) -> None:
        self.fixture = fixture or make_minimal_fixture()
        self.rule = rule or default_adaptation_rule()
        self.clock = clock or Clock()
        self.providers = FixtureProviderSet(self.fixture).set
        self.runtime = Runtime(store, self.providers, self.clock)
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
        self._emit_block_started(block_id)

        plan = list(self.fixture.items)
        index = 0
        source_event_id: EventID = self.runtime.state.events[-1].event_id

        while index < len(plan):
            item = plan[index]
            previous_outcome = (
                self.item_outcomes[-1]
                if self.item_outcomes and self.item_outcomes[-1].content_item_id == item.content_item_id
                else None
            )
            repeats_so_far = previous_outcome.repeats_used if previous_outcome else 0

            if previous_outcome is None:
                repeat_count = 0
                adaptation_source: str | None = None
            else:
                repeat_count = repeats_so_far + 1
                if previous_outcome.self_confirmation == "negative":
                    adaptation_source = "behavior"
                elif previous_outcome.latency > self.rule.latency_bound:
                    adaptation_source = "latency"
                else:
                    adaptation_source = "behavior"

            outcome = self._execute_item_trial(
                item=item,
                block_id=block_id,
                source_event_id=source_event_id,
                repeat_count=repeat_count,
                adaptation_source=adaptation_source,
                cap=self.rule.repeat_cap,
            )
            self.item_outcomes.append(outcome)
            source_event_id = self.runtime.state.events[-1].event_id

            # Apply the bounded adaptation rule.
            should_repeat = (
                outcome.self_confirmation == "negative"
                or outcome.latency > self.rule.latency_bound
            ) and outcome.repeats_used < self.rule.repeat_cap
            if should_repeat:
                plan.insert(index + 1, item)

            index += 1

        self._emit_block_completed(block_id, completed_trial_count=len(self.item_outcomes))
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

    def _emit_block_started(self, block_id: BlockID) -> Event:
        return self.runtime.emit(
            "block_started",
            {
                "session_id": str(self.runtime.state.session_id),
                "block_id": str(block_id),
                "block_type": BlockType.PRACTICE.value,
            },
            block_id=block_id,
        )

    def _emit_block_completed(self, block_id: BlockID, completed_trial_count: int) -> Event:
        return self.runtime.emit(
            "block_completed",
            {
                "session_id": str(self.runtime.state.session_id),
                "block_id": str(block_id),
                "completed_trial_count": completed_trial_count,
            },
            block_id=block_id,
        )

    def _execute_item_trial(
        self,
        item: FixtureItem,
        block_id: BlockID,
        source_event_id: EventID,
        repeat_count: int = 0,
        adaptation_source: str | None = None,
        cap: int = 0,
    ) -> ItemOutcome:
        self._trial_index += 1
        trial_id = TrialID(str(make_id(TrialID)))
        trial_index = self._trial_index

        # Track repeats for this item within the current trial sequence.
        repeats_used = sum(
            1
            for outcome in self.item_outcomes
            if outcome.content_item_id == item.content_item_id
        )

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

        trial_payload: dict[str, Any] = {
            "trial_id": str(trial_id),
            "session_id": str(self.runtime.state.session_id),
            "block_id": str(block_id),
            "trial_index": trial_index,
            "task_definition_id": self.fixture.task_definition_id,
            "content_item_ids": [item.content_item_id],
            "response_requirement": ResponseRequirement.REQUIRED.value,
            "accepted_response_modes": [ResponseMode.TOUCH.value],
            "repeat_count": repeat_count,
        }
        if adaptation_source is not None:
            trial_payload["adaptation_source"] = adaptation_source
        if cap:
            trial_payload["cap"] = cap
        self.runtime.emit(
            "trial_created",
            trial_payload,
            trial_id=trial_id,
            block_id=block_id,
            provenance=[source_event_id],
        )
        source_event_id = self.runtime.state.events[-1].event_id

        # 1. Present cue (prompt).
        source_event_id = self._emit_instruction(
            trial_id=trial_id,
            instruction_type=InstructionType.PRESENT_STIMULUS,
            payload=f"Recall the target for {item.content_item_id}",
            target_operation="covert_recall",
            duration=1.0,
            observable_response_expected=False,
            source_event_id=source_event_id,
        )
        source_event_id = self._emit_stimulus(
            trial_id=trial_id,
            content_item=content_item,
            asset_role="prompt",
            source_event_id=source_event_id,
        )

        # 2. Open anticipation/self-confirmation window.
        source_event_id = self._emit_instruction(
            trial_id=trial_id,
            instruction_type=InstructionType.REQUEST_OVERT_RESPONSE,
            payload="Indicate whether you recalled the target: positive or negative",
            target_operation="self_confirm",
            duration=3.0,
            observable_response_expected=True,
            source_event_id=source_event_id,
        )

        response_window_id = ResponseWindowID(str(make_id(ResponseWindowID)))
        opened_at = self.runtime.clock.now()
        self.runtime.emit(
            "response_window_opened",
            {
                "response_window_id": str(response_window_id),
                "trial_id": str(trial_id),
                "response_modes_accepted": [ResponseMode.TOUCH.value],
                "opened_at": opened_at,
                "deadline_at": opened_at + 10.0,
                "timeout_policy": "hard",
            },
            trial_id=trial_id,
            provenance=[source_event_id],
        )
        source_event_id = self.runtime.state.events[-1].event_id

        # 3. Collect deterministic self-confirmation observation.
        self.providers.observation.inject(f"{item.latency}:{item.self_confirmation}")
        raw_obs = self.providers.observation.poll()
        if not raw_obs:
            raise ProviderFailureError("Fixture observation provider returned no observation")
        obs = raw_obs[0]
        observation_id = ObservationID(obs["observation_id"])
        latency = float(obs.get("latency", 0.0))
        self_confirmation = str(obs["payload"])
        received_at = self.runtime.clock.now()

        self.runtime.emit(
            "observation_received",
            {
                "observation_id": str(observation_id),
                "response_window_id": str(response_window_id),
                "provider_id": "fixture_self_confirmation",
                "provider_version": "1.0.0",
                "observation_type": "touch_input",
                "received_at": received_at,
                "payload": self_confirmation,
                "latency": latency,
                "quality_dimensions": obs.get("quality_dimensions", {}),
                "quality_flags": obs.get("quality_flags", []),
                "quality_model_id": obs["quality_model_id"],
                "quality_model_version": obs["quality_model_version"],
            },
            trial_id=trial_id,
            component="observation_provider",
            component_version="1.0.0",
            provenance=[source_event_id],
            data_classification=DataClassification.INTERNAL,
        )
        source_event_id = self.runtime.state.events[-1].event_id

        # 4. Response pipeline (captured -> interpreted -> normalized -> evaluated).
        captured_response_id = CapturedResponseID(str(make_id(CapturedResponseID)))
        self.runtime.emit(
            "captured_response_created",
            {
                "captured_response_id": str(captured_response_id),
                "response_window_id": str(response_window_id),
                "observation_ids": [str(observation_id)],
                "response_mode": ResponseMode.TOUCH.value,
                "captured_payload": self_confirmation,
                "captured_at": received_at,
                "device_provenance": ["fixture_button_0"],
                "quality_flags": [],
            },
            trial_id=trial_id,
            provenance=[source_event_id],
        )
        source_event_id = self.runtime.state.events[-1].event_id

        interpretation = self.providers.interpreter.interpret({
            "captured_response_id": str(captured_response_id),
            "response_window_id": str(response_window_id),
            "response_mode": ResponseMode.TOUCH.value,
            "captured_payload": self_confirmation,
            "captured_at": received_at,
        })
        self.runtime.emit(
            "response_interpreted",
            {
                "response_interpretation_id": interpretation["response_interpretation_id"],
                "response_window_id": interpretation["response_window_id"],
                "captured_response_id": interpretation["captured_response_id"],
                "interpreter_id": interpretation["interpreter_id"],
                "interpreter_version": interpretation["interpreter_version"],
                "interpreted_payload": interpretation["interpreted_payload"],
                "interpretation_confidence": interpretation["interpretation_confidence"],
                "interpretation_type": interpretation["interpretation_type"],
                "component_timestamp": interpretation["component_timestamp"],
            },
            trial_id=trial_id,
            component="interpreter",
            component_version=interpretation["interpreter_version"],
            provenance=[source_event_id],
        )
        source_event_id = self.runtime.state.events[-1].event_id

        normalized = self.providers.normalizer.normalize(interpretation)
        normalized["response_mode"] = ResponseMode.TOUCH.value
        normalized["normalized_payload"] = self_confirmation
        self.runtime.emit(
            "domain_response_normalized",
            {
                "domain_normalized_response_id": normalized["domain_normalized_response_id"],
                "response_window_id": normalized["response_window_id"],
                "response_interpretation_id": normalized["response_interpretation_id"],
                "response_mode": normalized["response_mode"],
                "normalizer_id": normalized["normalizer_id"],
                "normalizer_version": normalized["normalizer_version"],
                "normalized_payload": normalized["normalized_payload"],
                "extracted_at": normalized["extracted_at"],
                "uncertainty": normalized["uncertainty"],
            },
            trial_id=trial_id,
            component="normalizer",
            component_version=normalized["normalizer_version"],
            provenance=[source_event_id],
        )
        source_event_id = self.runtime.state.events[-1].event_id

        eval_result = self.providers.evaluator.evaluate(
            normalized,
            content_item,
            TrialContext(
                trial_id=str(trial_id),
                session_id=str(self.runtime.state.session_id),
                response_mode=ResponseMode.TOUCH.value,
                protocol_version_id=self.fixture.protocol_version_id,
            ),
        )
        self.runtime.emit(
            "evaluation_completed",
            {
                "evaluation_id": eval_result["evaluation_id"],
                "trial_id": str(trial_id),
                "evaluator_id": eval_result["evaluator_id"],
                "evaluator_version": eval_result["evaluator_version"],
                "domain_normalized_response_id": eval_result["domain_normalized_response_id"],
                "expected_content_item_id": eval_result["expected_content_item_id"],
                "answer_status": eval_result["answer_status"],
                "evaluation_status": eval_result["evaluation_status"],
                "correctness_credit": eval_result.get("correctness_credit", 0.0),
                "scope_status": eval_result.get("scope_status"),
            },
            trial_id=trial_id,
            component="evaluator",
            component_version=eval_result["evaluator_version"],
            provenance=[source_event_id],
        )
        source_event_id = self.runtime.state.events[-1].event_id

        # 5. Present confirmation (correct target).
        source_event_id = self._emit_instruction(
            trial_id=trial_id,
            instruction_type=InstructionType.PRESENT_STIMULUS,
            payload=f"Target for {item.content_item_id}",
            target_operation="confirm",
            duration=1.0,
            observable_response_expected=False,
            source_event_id=source_event_id,
        )
        source_event_id = self._emit_stimulus(
            trial_id=trial_id,
            content_item=content_item,
            asset_role="confirmation",
            source_event_id=source_event_id,
        )

        # 6. Mark trial completed.
        feedback_event_id = FeedbackEventID(str(make_id(FeedbackEventID)))
        self.runtime.emit(
            "feedback_started",
            {
                "feedback_event_id": str(feedback_event_id),
                "trial_id": str(trial_id),
                "feedback_category": FeedbackCategory.KNOWLEDGE.value,
                "feedback_type": FeedbackType.CORRECT_ANSWER.value,
                "content_item_id": item.content_item_id,
                "started_at": self.runtime.clock.now(),
            },
            trial_id=trial_id,
            provenance=[source_event_id],
        )
        source_event_id = self.runtime.state.events[-1].event_id

        self.runtime.emit(
            "feedback_completed",
            {
                "feedback_event_id": str(feedback_event_id),
                "trial_id": str(trial_id),
                "completed_at": self.runtime.clock.now(),
                "duration_observed": 1.0,
            },
            trial_id=trial_id,
            provenance=[source_event_id],
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

    def _emit_instruction(
        self,
        trial_id: TrialID,
        instruction_type: InstructionType,
        payload: str,
        target_operation: str,
        duration: float,
        observable_response_expected: bool,
        source_event_id: EventID,
    ) -> EventID:
        instruction_id = InstructionID(str(make_id(InstructionID)))
        started_at = self.runtime.clock.now()
        event = self.runtime.emit(
            "instruction_started",
            {
                "trial_id": str(trial_id),
                "instruction_id": str(instruction_id),
                "instruction_type": instruction_type.value,
                "instruction_payload": payload,
                "target_operation": target_operation,
                "allotted_duration": duration,
                "observable_response_expected": observable_response_expected,
                "started_at": started_at,
            },
            trial_id=trial_id,
            provenance=[source_event_id],
        )
        self.runtime.emit(
            "instruction_completed",
            {
                "trial_id": str(trial_id),
                "instruction_id": str(instruction_id),
                "completed_at": self.runtime.clock.now(),
                "duration": duration,
            },
            trial_id=trial_id,
            provenance=[event.event_id],
        )
        return self.runtime.state.events[-1].event_id

    def _emit_stimulus(
        self,
        trial_id: TrialID,
        content_item: ContentItem,
        asset_role: str,
        source_event_id: EventID,
    ) -> EventID:
        stimulus_request_id = StimulusRequestID(str(make_id(StimulusRequestID)))
        requested_at = self.runtime.clock.now()
        self.runtime.emit(
            "stimulus_requested",
            {
                "stimulus_request_id": str(stimulus_request_id),
                "trial_id": str(trial_id),
                "content_item_id": content_item.content_item_id,
                "renderer_id": "fixture_renderer",
                "requested_at": requested_at,
                "scheduled_for": requested_at,
                "asset_role": asset_role,
            },
            trial_id=trial_id,
            provenance=[source_event_id],
        )
        provenance_event_id = self.runtime.state.events[-1].event_id

        rendered = self.providers.renderer.render({
            "stimulus_request_id": str(stimulus_request_id),
            "trial_id": str(trial_id),
            "content_item_id": content_item.content_item_id,
            "asset_role": asset_role,
        })
        event = self.runtime.emit(
            "stimulus_ready",
            {
                "stimulus_request_id": rendered["stimulus_request_id"],
                "rendered_stimulus_id": rendered["rendered_stimulus_id"],
                "renderer_id": rendered["renderer_id"],
                "renderer_version": rendered["renderer_version"],
                "duration": rendered["duration"],
                "rendered_at": rendered["rendered_at"],
                "media_handle": rendered["media_handle"],
                "asset_version": rendered["asset_version"],
                "asset_role": rendered["asset_role"],
            },
            trial_id=trial_id,
            component="renderer",
            component_version=rendered["renderer_version"],
            provenance=[provenance_event_id],
        )
        return event.event_id


def run_immediate_recall_session(
    store: EventStore,
    learner_id: str = "learner_001",
    random_seed: str = "seed_0",
    session_id: SessionID | None = None,
    fixture: ImmediateRecallFixture | None = None,
    rule: AdaptationRule | None = None,
    clock: Clock | None = None,
) -> ImmediateRecallResult:
    """High-level entry point for running an Immediate Recall session."""
    runner = ImmediateRecallRunner(store, fixture=fixture, rule=rule, clock=clock)
    return runner.run_session(
        learner_id=learner_id,
        random_seed=random_seed,
        session_id=session_id,
    )
