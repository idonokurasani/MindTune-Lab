"""In-memory deterministic mantra actuator for CLM-01."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from mindtune_clm.decision import ControlDecision
from mindtune_clm.state import MantraControlState


@dataclass(frozen=True)
class ActuationReceipt:
    """Immutable receipt from the mantra actuator."""

    command_id: str
    decision_id: str
    applied_control_state_id: str
    requested_state: MantraControlState
    applied_state: MantraControlState
    timestamp: float
    safe_boundary: str
    success: bool
    rejection_reason: str | None = None

    def as_dict(self) -> dict[str, Any]:
        """Return a serializable representation for event payloads."""
        return {
            "command_id": self.command_id,
            "decision_id": self.decision_id,
            "applied_control_state_id": self.applied_control_state_id,
            "requested_state": self.requested_state.as_dict(),
            "applied_state": self.applied_state.as_dict(),
            "timestamp": self.timestamp,
            "safe_boundary": self.safe_boundary,
            "success": self.success,
            "rejection_reason": self.rejection_reason,
        }


@dataclass
class MantraActuator:
    """Deterministic in-memory actuator for mantra control parameters.

    The actuator exposes its current control state, validates proposed states
    against the safety envelope, applies changes only at the declared safe
    application boundary, and returns an immutable ``ActuationReceipt``.  It
    never produces real audio in CLM-01.
    """

    safe_boundary: str = "between_mantra_cycles"
    current_state: MantraControlState = field(default_factory=MantraControlState.baseline)
    command_counter: int = 0

    def apply(self, decision: ControlDecision, timestamp: float, command_id: str | None = None) -> ActuationReceipt:
        """Validate and apply a control decision, returning a receipt."""
        if command_id is None:
            self.command_counter += 1
            command_id = f"actuate-{self.command_counter}"

        if decision.safe_application_boundary != self.safe_boundary:
            return ActuationReceipt(
                command_id=command_id,
                decision_id=decision.decision_id,
                applied_control_state_id=self.current_state.control_state_id,
                requested_state=decision.proposed_control_state,
                applied_state=self.current_state,
                timestamp=timestamp,
                safe_boundary=decision.safe_application_boundary,
                success=False,
                rejection_reason=(
                    f"unsafe_application_boundary: expected {self.safe_boundary}, "
                    f"got {decision.safe_application_boundary}"
                ),
            )

        clamped = decision.proposed_control_state.clamped()
        self.current_state = clamped

        return ActuationReceipt(
            command_id=command_id,
            decision_id=decision.decision_id,
            applied_control_state_id=clamped.control_state_id,
            requested_state=decision.proposed_control_state,
            applied_state=clamped,
            timestamp=timestamp,
            safe_boundary=self.safe_boundary,
            success=True,
        )
