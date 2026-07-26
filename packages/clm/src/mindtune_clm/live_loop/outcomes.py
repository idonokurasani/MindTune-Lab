"""CLM-04B intervention outcomes and health reporting."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class InterventionOutcome:
    """Immutable record of one closed-loop intervention cycle outcome."""

    outcome_id: str
    render_cycle_id: str
    observation_frame_id: str
    control_cycle_id: str
    decision_id: str
    actuation_receipt_id: str
    artifact_id: str | None
    playback_receipt_id: str | None
    intended_control_state_id: str
    observed_control_state_id: str
    cognitive_state: str
    assistance_level: float
    successful: bool
    safety_fallback: bool
    reason_codes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "outcome_id": self.outcome_id,
            "render_cycle_id": self.render_cycle_id,
            "observation_frame_id": self.observation_frame_id,
            "control_cycle_id": self.control_cycle_id,
            "decision_id": self.decision_id,
            "actuation_receipt_id": self.actuation_receipt_id,
            "artifact_id": self.artifact_id,
            "playback_receipt_id": self.playback_receipt_id,
            "intended_control_state_id": self.intended_control_state_id,
            "observed_control_state_id": self.observed_control_state_id,
            "cognitive_state": self.cognitive_state,
            "assistance_level": self.assistance_level,
            "successful": self.successful,
            "safety_fallback": self.safety_fallback,
            "reason_codes": list(self.reason_codes),
        }
