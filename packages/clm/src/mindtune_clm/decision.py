"""Typed control decisions for CLM-01."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from mpe.control.state import MantraControlState


class ControlDecisionKind(str, Enum):
    """Canonical control decision kinds for the mantra actuator."""

    APPLY = "apply"
    MAINTAIN = "maintain"
    WITHDRAW = "withdraw"
    ABSTAIN = "abstain"
    STOP = "stop"


@dataclass(frozen=True)
class ControlDecision:
    """A typed, immutable decision produced by the control policy."""

    decision_id: str
    decision_kind: ControlDecisionKind
    previous_control_state: MantraControlState
    proposed_control_state: MantraControlState
    evidence: list[str] = field(default_factory=list)
    confidence: float = 0.0
    reason_codes: list[str] = field(default_factory=list)
    safe_application_boundary: str = "between_mantra_cycles"
    decision_timestamp: float = 0.0

    def as_dict(self) -> dict[str, Any]:
        """Return a serializable dictionary for event payloads."""
        return {
            "decision_id": self.decision_id,
            "decision_kind": self.decision_kind.value,
            "previous_control_state": self.previous_control_state.as_dict(),
            "proposed_control_state": self.proposed_control_state.as_dict(),
            "evidence": list(self.evidence),
            "confidence": self.confidence,
            "reason_codes": list(self.reason_codes),
            "safe_application_boundary": self.safe_application_boundary,
            "decision_timestamp": self.decision_timestamp,
        }
