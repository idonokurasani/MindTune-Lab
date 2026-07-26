"""MPE runtime aggregate state and event application handlers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from mpe.enums import AnswerStatus, BlockType, SessionStatus
from mpe.errors import IllegalStateTransitionError
from mpe.events import Event
from mpe.types import SessionID
from mpe.validation import validate_session_transition


@dataclass
class ResponseWindowState:
    """Response window sub-state within a trial."""

    response_window_id: str
    trial_id: str
    status: str = "listening"  # listening | captured | interpreted | normalized | timeout
    captured_response_id: str | None = None
    response_interpretation_id: str | None = None
    domain_normalized_response_id: str | None = None
    observation_ids: list[str] = field(default_factory=list)


@dataclass
class TrialState:
    """Trial aggregate state."""

    trial_id: str
    session_id: str
    block_id: str | None = None
    task_definition_id: str | None = None
    status: str = "started"  # started | awaiting_response | evaluated | completed | aborted
    answer_status: AnswerStatus | None = None
    response_window: ResponseWindowState | None = None
    content_item_ids: list[str] = field(default_factory=list)
    evaluation_id: str | None = None


@dataclass
class BlockState:
    """Block aggregate state."""

    block_id: str
    block_type: str
    status: str = "in_progress"  # in_progress | completed
    completed_trial_count: int = 0


@dataclass
class RuntimeState:
    """Top-level runtime aggregate reconstructed from events."""

    session_id: SessionID | None = None
    session_status: SessionStatus | None = None
    learner_id: str | None = None
    program_version_id: str | None = None
    protocol_version_id: str | None = None
    random_seed: str | None = None
    terminal: bool = False
    final_trial_index: int | None = None
    events: list[Event] = field(default_factory=list)
    trials: dict[str, TrialState] = field(default_factory=dict)
    blocks: dict[str, BlockState] = field(default_factory=dict)
    current_block_id: str | None = None

    # --------------------------------------------------------------------- #
    # Dispatch
    # --------------------------------------------------------------------- #

    def apply(self, event: Event) -> None:
        """Apply a single canonical event to this state."""
        handler = _EVENT_HANDLERS.get(event.event_type)
        if handler is None:
            raise IllegalStateTransitionError(
                f"No state handler for event type {event.event_type}"
            )
        handler(self, event)
        self.events.append(event)

    def as_dict(self) -> dict[str, Any]:
        """Return a serializable snapshot for deterministic comparison."""
        return {
            "session_id": str(self.session_id) if self.session_id else None,
            "session_status": self.session_status.value if self.session_status else None,
            "learner_id": self.learner_id,
            "program_version_id": self.program_version_id,
            "protocol_version_id": self.protocol_version_id,
            "random_seed": self.random_seed,
            "terminal": self.terminal,
            "final_trial_index": self.final_trial_index,
            "trials": {
                tid: {
                    "trial_id": t.trial_id,
                    "block_id": t.block_id,
                    "status": t.status,
                    "answer_status": t.answer_status.value if t.answer_status else None,
                    "response_window_id": t.response_window.response_window_id if t.response_window else None,
                    "evaluation_id": t.evaluation_id,
                }
                for tid, t in self.trials.items()
            },
            "blocks": {
                bid: {
                    "block_id": b.block_id,
                    "block_type": b.block_type,
                    "status": b.status,
                    "completed_trial_count": b.completed_trial_count,
                }
                for bid, b in self.blocks.items()
            },
        }


# --------------------------------------------------------------------------- #
# Event handlers
# --------------------------------------------------------------------------- #


def _on_session_created(state: RuntimeState, event: Event) -> None:
    if state.session_status is not None:
        raise IllegalStateTransitionError("session_created when session already exists")
    state.session_id = event.session_id
    state.session_status = SessionStatus.CREATED
    state.learner_id = event.payload.get("learner_id")
    state.program_version_id = event.payload.get("program_version_id")
    state.protocol_version_id = str(event.protocol_version_id)


def _on_session_started(state: RuntimeState, event: Event) -> None:
    validate_session_transition(state.session_status, SessionStatus.STARTED)
    state.session_status = SessionStatus.STARTED
    state.random_seed = event.payload.get("random_seed")


def _on_session_completed(state: RuntimeState, event: Event) -> None:
    validate_session_transition(state.session_status, SessionStatus.COMPLETED)
    state.session_status = SessionStatus.COMPLETED
    state.terminal = True
    state.final_trial_index = event.payload.get("final_trial_index")


def _on_session_cancelled(state: RuntimeState, event: Event) -> None:
    validate_session_transition(state.session_status, SessionStatus.CANCELLED)
    state.session_status = SessionStatus.CANCELLED
    state.terminal = True


def _on_block_started(state: RuntimeState, event: Event) -> None:
    p = event.payload
    block_id = p.get("block_id")
    if block_id is None:
        raise IllegalStateTransitionError("block_started missing block_id")
    if str(block_id) in state.blocks:
        raise IllegalStateTransitionError(f"block {block_id} already started")
    block_type = p.get("block_type")
    BlockType.validate(block_type)
    state.blocks[str(block_id)] = BlockState(
        block_id=str(block_id),
        block_type=str(block_type),
    )
    state.current_block_id = str(block_id)


def _on_block_completed(state: RuntimeState, event: Event) -> None:
    p = event.payload
    block_id = p.get("block_id")
    if block_id is None:
        raise IllegalStateTransitionError("block_completed missing block_id")
    block = state.blocks.get(str(block_id))
    if block is None or block.status != "in_progress":
        raise IllegalStateTransitionError(
            f"block {block_id} cannot complete from {getattr(block, 'status', None)}"
        )
    block.status = "completed"
    block.completed_trial_count = p.get("completed_trial_count", 0)


def _on_trial_created(state: RuntimeState, event: Event) -> None:
    p = event.payload
    trial_id = p.get("trial_id")
    if trial_id is None:
        raise IllegalStateTransitionError("trial_created missing trial_id")
    if str(trial_id) in state.trials:
        raise IllegalStateTransitionError(f"trial {trial_id} already exists")
    block_id = p.get("block_id")
    if block_id is not None and str(block_id) not in state.blocks:
        raise IllegalStateTransitionError(f"trial {trial_id} references unknown block {block_id}")
    state.trials[str(trial_id)] = TrialState(
        trial_id=str(trial_id),
        session_id=str(event.session_id),
        block_id=str(block_id) if block_id else None,
        task_definition_id=p.get("task_definition_id"),
        content_item_ids=list(p.get("content_item_ids", [])),
    )


def _on_instruction_started(state: RuntimeState, event: Event) -> None:
    # Instructions are valid during trial execution; no persistent state needed.
    pass


def _on_instruction_completed(state: RuntimeState, event: Event) -> None:
    pass


def _on_stimulus_requested(state: RuntimeState, event: Event) -> None:
    pass


def _on_stimulus_ready(state: RuntimeState, event: Event) -> None:
    pass


def _on_response_window_opened(state: RuntimeState, event: Event) -> None:
    p = event.payload
    trial_id = p.get("trial_id")
    response_window_id = p.get("response_window_id")
    if trial_id is None or response_window_id is None:
        raise IllegalStateTransitionError("response_window_opened missing trial_id or response_window_id")
    trial = state.trials.get(str(trial_id))
    if trial is None:
        raise IllegalStateTransitionError(f"response_window_opened for unknown trial {trial_id}")
    if trial.status not in ("started", "awaiting_response"):
        raise IllegalStateTransitionError(
            f"response_window_opened for trial {trial_id} in status {trial.status}"
        )
    if trial.response_window is not None:
        raise IllegalStateTransitionError(f"trial {trial_id} already has an open response window")
    trial.response_window = ResponseWindowState(
        response_window_id=str(response_window_id),
        trial_id=str(trial_id),
    )
    trial.status = "awaiting_response"


def _on_observation_received(state: RuntimeState, event: Event) -> None:
    # Observations are recorded in the event stream; the captured response binds them.
    pass


def _on_captured_response_created(state: RuntimeState, event: Event) -> None:
    p = event.payload
    response_window_id = p.get("response_window_id")
    trial_id = event.trial_id
    if response_window_id is None:
        raise IllegalStateTransitionError("captured_response_created missing response_window_id")
    trial = _require_trial(state, trial_id, "captured_response_created")
    if trial.response_window is None or trial.response_window.response_window_id != str(response_window_id):
        raise IllegalStateTransitionError(
            f"captured_response_created without open response window {response_window_id}"
        )
    if trial.response_window.status != "listening":
        raise IllegalStateTransitionError(
            f"captured_response_created for response window {response_window_id} in status {trial.response_window.status}"
        )
    trial.response_window.status = "captured"
    trial.response_window.captured_response_id = p.get("captured_response_id")
    trial.response_window.observation_ids = list(p.get("observation_ids", []))


def _on_response_interpreted(state: RuntimeState, event: Event) -> None:
    p = event.payload
    trial_id = event.trial_id
    trial = _require_trial(state, trial_id, "response_interpreted")
    if trial.response_window is None or trial.response_window.status != "captured":
        raise IllegalStateTransitionError(
            "response_interpreted does not follow captured_response_created"
        )
    if trial.response_window.captured_response_id != p.get("captured_response_id"):
        raise IllegalStateTransitionError("response_interpreted references wrong captured_response_id")
    trial.response_window.status = "interpreted"
    trial.response_window.response_interpretation_id = p.get("response_interpretation_id")


def _on_domain_response_normalized(state: RuntimeState, event: Event) -> None:
    p = event.payload
    trial_id = event.trial_id
    trial = _require_trial(state, trial_id, "domain_response_normalized")
    if trial.response_window is None or trial.response_window.status != "interpreted":
        raise IllegalStateTransitionError(
            "domain_response_normalized does not follow response_interpreted"
        )
    if trial.response_window.response_interpretation_id != p.get("response_interpretation_id"):
        raise IllegalStateTransitionError(
            "domain_response_normalized references wrong response_interpretation_id"
        )
    trial.response_window.status = "normalized"
    trial.response_window.domain_normalized_response_id = p.get("domain_normalized_response_id")


def _on_evaluation_completed(state: RuntimeState, event: Event) -> None:
    p = event.payload
    trial_id = p.get("trial_id")
    trial = _require_trial(state, trial_id, "evaluation_completed")
    if trial.status not in ("awaiting_response", "started"):
        raise IllegalStateTransitionError(
            f"evaluation_completed for trial {trial_id} in status {trial.status}"
        )
    if trial.response_window is None or trial.response_window.status != "normalized":
        raise IllegalStateTransitionError(
            f"evaluation_completed for trial {trial_id} without normalized response"
        )
    if trial.response_window.domain_normalized_response_id != p.get("domain_normalized_response_id"):
        raise IllegalStateTransitionError(
            "evaluation_completed references wrong domain_normalized_response_id"
        )
    trial.status = "evaluated"
    trial.answer_status = AnswerStatus(p.get("answer_status"))
    trial.evaluation_id = p.get("evaluation_id")


def _on_evaluation_abstained(state: RuntimeState, event: Event) -> None:
    p = event.payload
    trial_id = p.get("trial_id")
    trial = _require_trial(state, trial_id, "evaluation_abstained")
    if trial.status not in ("awaiting_response", "started"):
        raise IllegalStateTransitionError(
            f"evaluation_abstained for trial {trial_id} in status {trial.status}"
        )
    trial.status = "evaluated"
    trial.answer_status = AnswerStatus(p.get("answer_status"))
    trial.evaluation_id = p.get("evaluation_id")


def _on_evaluation_failed(state: RuntimeState, event: Event) -> None:
    p = event.payload
    trial_id = p.get("trial_id")
    trial = _require_trial(state, trial_id, "evaluation_failed")
    trial.status = "evaluated"
    trial.answer_status = AnswerStatus.UNEVALUABLE


def _on_feedback_started(state: RuntimeState, event: Event) -> None:
    # Feedback events follow evaluation; no persistent window state change.
    pass


def _on_feedback_completed(state: RuntimeState, event: Event) -> None:
    trial_id = event.trial_id
    if trial_id is not None:
        trial = state.trials.get(str(trial_id))
        if trial is not None and trial.status == "evaluated":
            trial.status = "completed"


def _on_schedule_decision(state: RuntimeState, event: Event) -> None:
    # Scheduler decisions are stored as audit events; runtime acts on them.
    pass


def _on_adaptation_decision(state: RuntimeState, event: Event) -> None:
    # Adaptation decisions are stored as audit events; the policy is replayed
    # by re-applying the same source events, not by reconstructing policy state.
    pass


def _on_observation_frame_created(state: RuntimeState, event: Event) -> None:
    # CLM-01 observation frames are audit events; control-loop state is replayed
    # by re-applying the same source events, not reconstructed from this handler.
    pass


def _on_cognitive_state_estimated(state: RuntimeState, event: Event) -> None:
    pass


def _on_control_decision_made(state: RuntimeState, event: Event) -> None:
    pass


def _on_actuation_requested(state: RuntimeState, event: Event) -> None:
    pass


def _on_actuation_applied(state: RuntimeState, event: Event) -> None:
    pass


def _on_adapted_stimulus_rendered(state: RuntimeState, event: Event) -> None:
    pass


def _on_intervention_outcome_evaluated(state: RuntimeState, event: Event) -> None:
    pass


def _on_session_cancelled_or_terminated(state: RuntimeState, event: Event) -> None:
    state.session_status = SessionStatus.TERMINATED
    state.terminal = True


def _require_trial(state: RuntimeState, trial_id: Any, context: str) -> TrialState:
    if trial_id is None:
        raise IllegalStateTransitionError(f"{context} missing trial_id")
    trial = state.trials.get(str(trial_id))
    if trial is None:
        raise IllegalStateTransitionError(f"{context} for unknown trial {trial_id}")
    return trial


_EVENT_HANDLERS: dict[str, Any] = {
    "session_created": _on_session_created,
    "session_started": _on_session_started,
    "session_completed": _on_session_completed,
    "session_cancelled": _on_session_cancelled,
    "block_started": _on_block_started,
    "block_completed": _on_block_completed,
    "trial_created": _on_trial_created,
    "instruction_started": _on_instruction_started,
    "instruction_completed": _on_instruction_completed,
    "stimulus_requested": _on_stimulus_requested,
    "stimulus_ready": _on_stimulus_ready,
    "response_window_opened": _on_response_window_opened,
    "observation_received": _on_observation_received,
    "captured_response_created": _on_captured_response_created,
    "response_interpreted": _on_response_interpreted,
    "domain_response_normalized": _on_domain_response_normalized,
    "evaluation_completed": _on_evaluation_completed,
    "evaluation_abstained": _on_evaluation_abstained,
    "evaluation_failed": _on_evaluation_failed,
    "feedback_started": _on_feedback_started,
    "feedback_completed": _on_feedback_completed,
    "schedule_decision": _on_schedule_decision,
    "adaptation_decision": _on_adaptation_decision,
    "protocol_terminated": _on_session_cancelled_or_terminated,
    "observation_frame_created": _on_observation_frame_created,
    "cognitive_state_estimated": _on_cognitive_state_estimated,
    "control_decision_made": _on_control_decision_made,
    "actuation_requested": _on_actuation_requested,
    "actuation_applied": _on_actuation_applied,
    "adapted_stimulus_rendered": _on_adapted_stimulus_rendered,
    "intervention_outcome_evaluated": _on_intervention_outcome_evaluated,
}
