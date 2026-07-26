"""CLM-04B live closed-loop cycle receipts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from mindtune_clm.actuator import ActuationReceipt
from mindtune_clm.audio.playback import PlaybackReceipt
from mindtune_clm.audio.renderer import RenderedAudioArtifact
from mindtune_clm.live_loop.outcomes import InterventionOutcome
from mindtune_clm.state import CognitiveStateEstimate


@dataclass(frozen=True)
class LiveLoopCycleReceipt:
    """Receipt summarizing one full live closed-loop cycle."""

    control_cycle_id: str
    render_cycle_id: str
    observation_frame_id: str
    estimate: CognitiveStateEstimate
    actuation_receipt: ActuationReceipt
    artifact: RenderedAudioArtifact | None
    playback_receipt: PlaybackReceipt | None
    outcome: InterventionOutcome | None
    safety_fallback: bool
    safety_reason_codes: list[str]
    render_failed: bool
    playback_failed: bool
    cache_miss: bool
    killed: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "control_cycle_id": self.control_cycle_id,
            "render_cycle_id": self.render_cycle_id,
            "observation_frame_id": self.observation_frame_id,
            "cognitive_state": self.estimate.cognitive_state.value,
            "actuation_receipt_id": self.actuation_receipt.command_id,
            "applied_control_state_id": self.actuation_receipt.applied_control_state_id,
            "artifact_id": self.artifact.artifact_id if self.artifact else None,
            "playback_receipt_id": self.playback_receipt.playback_receipt_id if self.playback_receipt else None,
            "playback_accepted": self.playback_receipt.accepted if self.playback_receipt else None,
            "outcome_id": self.outcome.outcome_id if self.outcome else None,
            "safety_fallback": self.safety_fallback,
            "safety_reason_codes": list(self.safety_reason_codes),
            "render_failed": self.render_failed,
            "playback_failed": self.playback_failed,
            "cache_miss": self.cache_miss,
            "killed": self.killed,
        }
