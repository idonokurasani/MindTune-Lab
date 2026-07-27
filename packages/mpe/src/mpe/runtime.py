"""MPE runtime orchestrator and deterministic mock session runner."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Protocol

from mpe.aggregates import RuntimeState
from mpe.enums import (
    AnswerStatus,
    DataClassification,
    DecisionType,
    FeedbackCategory,
    FeedbackType,
    InstructionType,
    ResponseMode,
    ResponseRequirement,
    SessionStatus,
)
from mpe.errors import IllegalStateTransitionError, ProviderFailureError
from mpe.event_store import EventStore
from mpe.events import CURRENT_EVENT_SCHEMA_VERSION, Event
from mpe.provenance import resolve_software_revision
from mpe.providers import ContentItem, ProviderSet, SchedulingContext, TrialContext
from mpe.replay import Replay
from mpe.types import (
    BlockID,
    CapturedResponseID,
    CorrelationID,
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
from mpe.validation import validate_session_transition


@dataclass
class Outcome:
    """Read-only computed summary of a completed session."""

    session_id: str
    status: str
    trial_count: int
    completed_trial_count: int
    accuracy: float | None
    omission_rate: float = 0.0
    coverage: float = 0.0
    dropout: bool = False
    early_termination: bool = False
    protocol_adherence: float = 1.0


class Clock:
    """Deterministic monotonic session clock.

    Measures protocol time. It is not a record of when the session happened;
    that is `WallClock`.
    """

    def __init__(self, start: float = 1.0, step: float = 0.1) -> None:
        self._time = start
        self._step = step

    def now(self) -> float:
        return self._time

    def advance(self) -> None:
        self._time += self._step


class WallClock(Protocol):
    """Source of UTC epoch seconds recorded alongside protocol time."""

    def now_utc(self) -> float: ...


class SystemWallClock:
    """UTC wall clock backed by the operating system.

    The value is self-asserted: it records what this machine believed the time
    to be, and is not externally attested (ADR-0001 sec. 2.6).
    """

    def now_utc(self) -> float:
        return time.time()


class FixedWallClock:
    """Wall clock returning a pinned value, for deterministic tests."""

    def __init__(self, value: float = 0.0, step: float = 0.0) -> None:
        self._value = value
        self._step = step

    def now_utc(self) -> float:
        value = self._value
        self._value += self._step
        return value


_PRE_PROVENANCE_EVENT_TYPES = frozenset(
    {"session_created", "session_provenance_recorded"}
)


class Runtime:
    """MPE runtime: emits canonical events and reconstructs state via replay."""

    def __init__(
        self,
        store: EventStore,
        providers: ProviderSet,
        clock: Clock | None = None,
        wall_clock: WallClock | None = None,
    ) -> None:
        self.store = store
        self.providers = providers
        self.clock = clock or Clock()
        self.wall_clock: WallClock = wall_clock or SystemWallClock()
        self.state = RuntimeState()

        self._session_id: SessionID | None = None
        self._protocol_version_id: ProtocolVersionID | None = None
        self._program_version_id: Any = None
        self._learner_id: str | None = None
        self._resolved_revision = resolve_software_revision()
        self._writer_revision = self._resolved_revision.revision

    # --------------------------------------------------------------------- #
    # Event emission
    # --------------------------------------------------------------------- #

    def emit(
        self,
        event_type: str,
        payload: dict[str, Any],
        *,
        provenance: list[EventID] | None = None,
        component: str = "runtime",
        component_version: str = "1.0.0",
        trial_id: TrialID | None = None,
        block_id: BlockID | None = None,
        correlation_id: CorrelationID | None = None,
        sensitive: bool = False,
        data_classification: DataClassification | None = None,
    ) -> Event:
        """Create, validate, append, and apply one event."""
        if self._session_id is None:
            raise IllegalStateTransitionError("Cannot emit event before session is created")
        if self._protocol_version_id is None:
            raise IllegalStateTransitionError("Cannot emit event before session is created")
        if (
            event_type not in _PRE_PROVENANCE_EVENT_TYPES
            and self.state.provenance_event_id is None
        ):
            raise IllegalStateTransitionError(
                f"Cannot emit {event_type} before session_provenance_recorded"
            )

        provenance = list(provenance or [])
        if (
            event_type == "trial_created"
            and not self.state.trials
            and self.state.provenance_event_id is not None
        ):
            provenance.append(EventID(self.state.provenance_event_id))

        last_seq = self.store.get_last_sequence(self._session_id)
        expected_version = last_seq
        next_seq = last_seq + 1
        timestamp = self.clock.now()
        self.clock.advance()
        wallclock_at = self.wall_clock.now_utc()

        event = Event(
            event_id=make_id(EventID),
            event_type=event_type,
            schema_version=CURRENT_EVENT_SCHEMA_VERSION,
            session_id=self._session_id,
            session_sequence_number=next_seq,
            protocol_version_id=ProtocolVersionID(str(self._protocol_version_id)),
            timestamp=timestamp,
            wallclock_at=wallclock_at,
            component=component,
            component_version=component_version,
            correlation_id=correlation_id,
            provenance=provenance,
            payload=payload,
            sensitive=sensitive,
            data_classification=data_classification,
            trial_id=trial_id,
            block_id=block_id,
            writer_revision=self._writer_revision,
        )
        stored = self.store.append(event, expected_version=expected_version)
        self.state.apply(stored)
        return stored

    # --------------------------------------------------------------------- #
    # Session lifecycle
    # --------------------------------------------------------------------- #

    def create_session(
        self,
        program_version_id: Any,
        protocol_version_id: ProtocolVersionID,
        learner_id: str,
        session_id: SessionID | None = None,
        *,
        provenance: dict[str, Any] | None = None,
        record_provenance: bool = True,
    ) -> Event:
        """Create the session and, by default, record its provenance at once.

        `record_provenance=False` exists only so a test can observe that the
        runtime refuses every later event until provenance is recorded.
        """
        if session_id is None:
            session_id = SessionID(str(make_id(SessionID)))
        self._session_id = session_id
        self._protocol_version_id = protocol_version_id
        self._program_version_id = program_version_id
        self._learner_id = learner_id

        event = self.emit(
            "session_created",
            {
                "session_id": str(session_id),
                "program_version_id": str(program_version_id),
                "protocol_version_id": str(protocol_version_id),
                "learner_id": learner_id,
            },
        )
        if record_provenance:
            self.record_provenance(**(provenance or {}))
        return event

    def record_provenance(
        self,
        *,
        protocol_id: str | None = None,
        curriculum_id: str | None = None,
        curriculum_version: str | None = None,
        experimental_condition: str | None = None,
        randomization_seed: str = "seed_0",
        stimulus_set_id: str | None = None,
        stimulus_set_version: str | None = None,
        scoring_policy_version: str | None = None,
        rt_policy_version: str | None = None,
        signal_processing_policy_version: str | None = None,
    ) -> Event:
        """Emit `session_provenance_recorded`, always at sequence 2.

        Fields with no source yet are recorded as explicit `null`, never as an
        invented default. The software revision is recorded together with the
        source it came from, so a reader can judge its strength; `source:
        "unknown"` is a valid but weak record that downstream reports must flag.
        """
        return self.emit(
            "session_provenance_recorded",
            {
                "session_id": str(self._session_id),
                "protocol_id": protocol_id or str(self._protocol_version_id),
                "protocol_version_id": str(self._protocol_version_id),
                "curriculum_id": curriculum_id,
                "curriculum_version": curriculum_version,
                "experimental_condition": experimental_condition,
                "randomization_seed": randomization_seed,
                "stimulus_set_id": stimulus_set_id,
                "stimulus_set_version": stimulus_set_version,
                "scoring_policy_version": scoring_policy_version,
                "rt_policy_version": rt_policy_version,
                "signal_processing_policy_version": signal_processing_policy_version,
                "software_revision": self._resolved_revision.as_dict(),
                "provider_versions": self.providers.version_map(),
                "writer_component": "runtime",
                "writer_version": "1.0.0",
            },
        )

    def start_session(
        self, random_seed: str = "seed_0", start_parameters: dict[str, Any] | None = None
    ) -> Event:
        self._ensure_started_can_create()
        event = self.emit(
            "session_started",
            {
                "session_id": str(self._session_id),
                "program_version_id": str(self._program_version_id),
                "protocol_version_id": str(self._protocol_version_id),
                "learner_id": self._learner_id,
                "random_seed": random_seed,
                "start_parameters": start_parameters or {},
            },
        )
        return event

    def complete_session(self, final_trial_index: int = 0) -> Event:
        event = self.emit(
            "session_completed",
            {
                "session_id": str(self._session_id),
                "completed_at": self.clock.now(),
                "final_trial_index": final_trial_index,
            },
        )
        return event

    # --------------------------------------------------------------------- #
    # Trial and block execution
    # --------------------------------------------------------------------- #

    def run_mock_session(
        self,
        program_version: Any,
        protocol_version: Any,
        task_definition: Any,
        block: Any,
        content_item: ContentItem,
        learner_id: str,
        random_seed: str = "seed_0",
        session_id: SessionID | None = None,
    ) -> RuntimeState:
        """Execute the reference mock protocol end-to-end."""
        self.providers.check_versions(protocol_version.dependency_versions)

        self.create_session(
            program_version.program_version_id,
            protocol_version.protocol_version_id,
            learner_id,
            session_id=session_id,
        )
        self.start_session(random_seed)

        # Initial scheduling decision.
        schedule_event = self._select_next(
            trial_index=1,
            item_sequence=block.trial_sequence,
            source_event_ids=[self.state.events[-1].event_id],
        )
        if schedule_event.payload["decision_type"] == DecisionType.SESSION_END.value:
            raise ProviderFailureError("Scheduler unexpectedly ended session before any trial")

        self.emit(
            "block_started",
            {
                "session_id": str(self._session_id),
                "block_id": block.block_id,
                "block_type": block.block_type,
            },
            block_id=BlockID(block.block_id),
        )

        schedule_event.payload["selected_item_ids"][0]
        self._execute_trial(
            trial_index=1,
            block_id=BlockID(block.block_id),
            task_definition=task_definition,
            content_item=content_item,
            source_event_id=schedule_event.event_id,
        )

        # Post-trial scheduling decision -> session_end.
        post_trial_schedule = self._select_next(
            trial_index=2,
            item_sequence=block.trial_sequence,
            source_event_ids=[self.state.events[-1].event_id],
        )
        if post_trial_schedule.payload["decision_type"] != DecisionType.SESSION_END.value:
            raise ProviderFailureError("Scheduler unexpectedly selected another trial")

        self.emit(
            "block_completed",
            {
                "session_id": str(self._session_id),
                "block_id": block.block_id,
                "completed_trial_count": 1,
            },
            block_id=BlockID(block.block_id),
        )

        self.complete_session(final_trial_index=1)
        return self.state

    def _select_next(
        self,
        trial_index: int,
        item_sequence: list[str],
        source_event_ids: list[EventID],
    ) -> Event:
        ctx = SchedulingContext(
            protocol_version_id=str(self._protocol_version_id),
            session_id=str(self._session_id),
            trial_index=trial_index,
            protocol_policy={"item_sequence": item_sequence},
            random_seed=self.state.random_seed or "seed_0",
            source_event_ids=[str(e) for e in source_event_ids],
        )
        decision = self.providers.scheduler.select_next(ctx)
        return self.emit(
            "schedule_decision",
            {
                "schedule_decision_id": decision["schedule_decision_id"],
                "session_id": str(self._session_id),
                "scheduler_id": decision["scheduler_id"],
                "scheduler_version": decision["scheduler_version"],
                "policy_id": decision["policy_id"],
                "policy_version": decision["policy_version"],
                "source_event_ids": decision["source_event_ids"],
                "item_history_snapshot_id": decision["item_history_snapshot_id"],
                "candidate_item_ids": decision["candidate_item_ids"],
                "excluded_candidates": decision["excluded_candidates"],
                "selection_rule": decision["selection_rule"],
                "tie_break_rule": decision["tie_break_rule"],
                "random_seed": decision["random_seed"],
                "selected_item_ids": decision["selected_item_ids"],
                "decision_type": decision["decision_type"],
                "decision_status": decision["decision_status"],
            },
            component="scheduler",
            component_version=self.providers.scheduler.capabilities()["scheduler_version"],
            provenance=source_event_ids,
        )

    def _execute_trial(
        self,
        trial_index: int,
        block_id: BlockID,
        task_definition: Any,
        content_item: ContentItem,
        source_event_id: EventID,
    ) -> None:
        trial_id = TrialID(str(make_id(TrialID)))
        task_def_id = task_definition.task_definition_id
        accepted_mode_values = [ResponseMode.TYPED.value]

        self.emit(
            "trial_created",
            {
                "trial_id": str(trial_id),
                "session_id": str(self._session_id),
                "block_id": str(block_id),
                "trial_index": trial_index,
                "task_definition_id": task_def_id,
                "content_item_ids": [content_item.content_item_id],
                "response_requirement": ResponseRequirement.REQUIRED.value,
                "accepted_response_modes": accepted_mode_values,
            },
            trial_id=trial_id,
            block_id=block_id,
            provenance=[source_event_id],
        )

        for role in task_definition.trial_role_sequence:
            if role == "STIMULUS":
                self._emit_stimulus_cue(trial_id, content_item)
            elif role == "RESPONSE_WINDOW":
                self._emit_response_pipeline(trial_id, content_item, [ResponseMode.TYPED])
            elif role == "KNOWLEDGE_FEEDBACK":
                self._emit_feedback(trial_id, content_item)

    def _emit_stimulus_cue(self, trial_id: TrialID, content_item: ContentItem) -> None:
        instruction_id = InstructionID(str(make_id(InstructionID)))
        ts = self.clock.now()
        self.emit(
            "instruction_started",
            {
                "trial_id": str(trial_id),
                "instruction_id": str(instruction_id),
                "instruction_type": InstructionType.PRESENT_STIMULUS.value,
                "instruction_payload": f"Listen to the word: {content_item.surface_form}",
                "target_operation": "listen",
                "allotted_duration": 1.0,
                "observable_response_expected": False,
                "started_at": ts,
            },
            trial_id=trial_id,
            component="runtime",
        )
        self.emit(
            "instruction_completed",
            {
                "trial_id": str(trial_id),
                "instruction_id": str(instruction_id),
                "completed_at": self.clock.now(),
                "duration": 1.0,
            },
            trial_id=trial_id,
            provenance=[self.state.events[-1].event_id],
        )

        stimulus_request_id = StimulusRequestID(str(make_id(StimulusRequestID)))
        requested_at = self.clock.now()
        self.emit(
            "stimulus_requested",
            {
                "stimulus_request_id": str(stimulus_request_id),
                "trial_id": str(trial_id),
                "content_item_id": content_item.content_item_id,
                "renderer_id": "mock_renderer",
                "requested_at": requested_at,
                "scheduled_for": requested_at,
            },
            trial_id=trial_id,
            provenance=[self.state.events[-1].event_id],
        )

        rendered = self.providers.renderer.render({
            "stimulus_request_id": str(stimulus_request_id),
            "trial_id": str(trial_id),
            "content_item_id": content_item.content_item_id,
        })
        self.emit(
            "stimulus_ready",
            {
                "stimulus_request_id": rendered["stimulus_request_id"],
                "rendered_stimulus_id": rendered["rendered_stimulus_id"],
                "renderer_version": rendered["renderer_version"],
                "duration": rendered["duration"],
                "rendered_at": rendered["rendered_at"],
            },
            trial_id=trial_id,
            component="renderer",
            component_version=rendered["renderer_version"],
            provenance=[self.state.events[-1].event_id],
        )

    def _emit_response_pipeline(
        self,
        trial_id: TrialID,
        content_item: ContentItem,
        accepted_modes: list[ResponseMode],
    ) -> None:
        # Pre-response instruction
        instruction_id = InstructionID(str(make_id(InstructionID)))
        ts = self.clock.now()
        self.emit(
            "instruction_started",
            {
                "trial_id": str(trial_id),
                "instruction_id": str(instruction_id),
                "instruction_type": InstructionType.REQUEST_OVERT_RESPONSE.value,
                "instruction_payload": "Please type the expected answer.",
                "target_operation": "type the expected answer",
                "allotted_duration": 10.0,
                "observable_response_expected": True,
                "started_at": ts,
            },
            trial_id=trial_id,
        )
        self.emit(
            "instruction_completed",
            {
                "trial_id": str(trial_id),
                "instruction_id": str(instruction_id),
                "completed_at": self.clock.now(),
                "duration": 0.5,
            },
            trial_id=trial_id,
            provenance=[self.state.events[-1].event_id],
        )

        response_window_id = ResponseWindowID(str(make_id(ResponseWindowID)))
        opened_at = self.clock.now()
        self.emit(
            "response_window_opened",
            {
                "response_window_id": str(response_window_id),
                "trial_id": str(trial_id),
                "response_modes_accepted": [m.value for m in accepted_modes],
                "opened_at": opened_at,
                "deadline_at": opened_at + 10.0,
                "timeout_policy": "hard",
            },
            trial_id=trial_id,
            provenance=[self.state.events[-1].event_id],
        )

        # Inject deterministic mock observation.
        self.providers.observation.inject(content_item.surface_form)
        observations = self.providers.observation.poll()
        if not observations:
            raise ProviderFailureError("Mock observation provider returned no observation")
        raw_obs = observations[0]
        observation_id = ObservationID(raw_obs["observation_id"])
        received_at = self.clock.now()
        self.emit(
            "observation_received",
            {
                "observation_id": str(observation_id),
                "response_window_id": str(response_window_id),
                "provider_id": self.providers.observation.capabilities()["provider_id"],
                "provider_version": self.providers.observation.capabilities()["provider_version"],
                "observation_type": raw_obs["observation_type"],
                "received_at": received_at,
                "payload": raw_obs["payload"],
                "quality_dimensions": raw_obs.get("quality_dimensions", {}),
                "quality_flags": raw_obs.get("quality_flags", []),
                "quality_model_id": raw_obs["quality_model_id"],
                "quality_model_version": raw_obs["quality_model_version"],
            },
            trial_id=trial_id,
            component="observation_provider",
            component_version=self.providers.observation.capabilities()["provider_version"],
            sensitive=False,
            data_classification=DataClassification.CONSENT_GATED,
            provenance=[self.state.events[-1].event_id],
        )

        captured_response_id = CapturedResponseID(str(make_id(CapturedResponseID)))
        captured_at = self.clock.now()
        self.emit(
            "captured_response_created",
            {
                "captured_response_id": str(captured_response_id),
                "response_window_id": str(response_window_id),
                "observation_ids": [str(observation_id)],
                "response_mode": ResponseMode.TYPED.value,
                "captured_payload": raw_obs["payload"],
                "captured_at": captured_at,
                "device_provenance": [self.providers.observation.capabilities()["device_id"]],
                "quality_flags": [],
            },
            trial_id=trial_id,
            provenance=[self.state.events[-1].event_id],
        )

        interpretation = self.providers.interpreter.interpret({
            "captured_response_id": str(captured_response_id),
            "response_window_id": str(response_window_id),
            "response_mode": ResponseMode.TYPED.value,
            "captured_payload": raw_obs["payload"],
            "captured_at": captured_at,
        })
        self.emit(
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
            sensitive=False,
            data_classification=DataClassification.CONSENT_GATED,
            provenance=[self.state.events[-1].event_id],
        )

        normalized = self.providers.normalizer.normalize(interpretation)
        normalized["response_mode"] = ResponseMode.TYPED.value
        self.emit(
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
            sensitive=False,
            data_classification=DataClassification.CONSENT_GATED,
            provenance=[self.state.events[-1].event_id],
        )

        eval_result = self.providers.evaluator.evaluate(
            normalized,
            content_item,
            TrialContext(
                trial_id=str(trial_id),
                session_id=str(self._session_id),
                response_mode=ResponseMode.TYPED.value,
                protocol_version_id=str(self._protocol_version_id),
            ),
        )
        self.emit(
            "evaluation_completed",
            {
                "evaluation_id": eval_result["evaluation_id"],
                "trial_id": str(trial_id),
                "evaluator_id": eval_result["evaluator_id"],
                "evaluator_version": eval_result["evaluator_version"],
                "domain_normalized_response_id": normalized["domain_normalized_response_id"],
                "expected_content_item_id": content_item.content_item_id,
                "answer_status": eval_result["answer_status"],
                "evaluation_status": eval_result["evaluation_status"],
                "correctness_credit": eval_result.get("correctness_credit", 0.0),
                "scope_status": eval_result.get("scope_status"),
            },
            trial_id=trial_id,
            component="evaluator",
            component_version=eval_result["evaluator_version"],
            provenance=[self.state.events[-1].event_id],
        )

    def _emit_feedback(self, trial_id: TrialID, content_item: ContentItem) -> None:
        feedback_event_id = FeedbackEventID(str(make_id(FeedbackEventID)))
        trial = self.state.trials.get(str(trial_id))
        answer = AnswerStatus.CORRECT if (trial and trial.answer_status == AnswerStatus.CORRECT) else AnswerStatus.INCORRECT
        feedback_type = (
            FeedbackType.CORRECT_ANSWER.value
            if answer == AnswerStatus.CORRECT
            else FeedbackType.INCORRECT_INDICATOR.value
        )
        started_at = self.clock.now()
        self.emit(
            "feedback_started",
            {
                "feedback_event_id": str(feedback_event_id),
                "trial_id": str(trial_id),
                "feedback_category": FeedbackCategory.KNOWLEDGE.value,
                "feedback_type": feedback_type,
                "content_item_id": content_item.content_item_id,
                "started_at": started_at,
            },
            trial_id=trial_id,
            component="runtime",
            provenance=[self.state.events[-1].event_id],
        )
        self.emit(
            "feedback_completed",
            {
                "feedback_event_id": str(feedback_event_id),
                "trial_id": str(trial_id),
                "completed_at": self.clock.now(),
                "duration_observed": 1.0,
            },
            trial_id=trial_id,
            provenance=[self.state.events[-1].event_id],
        )

    # --------------------------------------------------------------------- #
    # Replay and outcome
    # --------------------------------------------------------------------- #

    def replay(self, session_id: SessionID) -> RuntimeState:
        """Reconstruct state exclusively from stored events."""
        return Replay(self.store).replay(session_id)

    def outcome(self) -> Outcome:
        """Compute an Outcome from the current live state."""
        total = len(self.state.trials)
        completed = sum(
            1 for t in self.state.trials.values() if t.status == "completed"
        )
        evaluated = [t for t in self.state.trials.values() if t.answer_status is not None]
        correct = sum(
            1 for t in evaluated if t.answer_status == AnswerStatus.CORRECT
        )
        accuracy = correct / len(evaluated) if evaluated else None
        status = self.state.session_status.value if self.state.session_status else "unknown"
        return Outcome(
            session_id=str(self._session_id),
            status=status,
            trial_count=total,
            completed_trial_count=completed,
            accuracy=accuracy,
        )

    # --------------------------------------------------------------------- #
    # Helpers
    # --------------------------------------------------------------------- #

    def _ensure_started_can_create(self) -> None:
        validate_session_transition(self.state.session_status, SessionStatus.STARTED)
