"""CLM-04B live closed-loop state containers."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from mindtune_clm.audio.playback import PlaybackReceipt
from mindtune_clm.audio.renderer import RenderedAudioArtifact
from mindtune_clm.state import MantraControlState


class LiveLoopStatus(str, Enum):
    """High-level lifecycle status of the closed loop."""

    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    KILLED = "killed"
    COMPLETED = "completed"


@dataclass
class LiveCycleState:
    """Playback-cycle state: current audio, pending audio, and safe boundaries."""

    current_control_state: MantraControlState = field(default_factory=MantraControlState.baseline)
    current_artifact: RenderedAudioArtifact | None = None
    pending_artifact: RenderedAudioArtifact | None = None
    current_playback_receipt: PlaybackReceipt | None = None
    current_cycle_start: float = 0.0
    current_cycle_end: float = 0.0
    current_artifact_id: str | None = None
    pending_artifact_id: str | None = None

    def between_cycles(self, now: float) -> bool:
        """Return True when the current cycle has ended and a switch is safe."""
        return now >= self.current_cycle_end

    def set_pending(self, artifact: RenderedAudioArtifact) -> None:
        """Queue an artifact for activation at the next safe boundary."""
        self.pending_artifact = artifact
        self.pending_artifact_id = artifact.artifact_id

    def activate_pending(self, now: float) -> RenderedAudioArtifact | None:
        """Activate the pending artifact and start a new cycle."""
        if self.pending_artifact is None:
            return None
        self.current_artifact = self.pending_artifact
        self.current_artifact_id = self.pending_artifact.artifact_id
        self.pending_artifact = None
        self.pending_artifact_id = None
        self.current_cycle_start = now
        self.current_cycle_end = now + (self.current_artifact.duration if self.current_artifact else 0.0)
        return self.current_artifact

    def start_cycle(self, now: float, artifact: RenderedAudioArtifact) -> None:
        """Immediately start a new cycle with the supplied artifact."""
        self.current_artifact = artifact
        self.current_artifact_id = artifact.artifact_id
        self.current_cycle_start = now
        self.current_cycle_end = now + artifact.duration


@dataclass
class LiveClosedLoopState:
    """Mutable runtime state for the live closed-loop orchestrator."""

    session_id: str = ""
    status: LiveLoopStatus = LiveLoopStatus.STOPPED
    cycle: LiveCycleState = field(default_factory=LiveCycleState)
    frame_count: int = 0
    decision_count: int = 0
    render_count: int = 0
    playback_count: int = 0
    last_decision_timestamp: float = 0.0
    last_switch_timestamp: float = 0.0
    consecutive_degraded: int = 0
    consecutive_missing: int = 0
    pending_commands: int = 0
    cache_misses: int = 0
    render_failures: int = 0
    playback_failures: int = 0
    switch_history: list[tuple[float, str, str]] = field(default_factory=list)
    decision_history: list[tuple[float, str]] = field(default_factory=list)
    baseline_forced: bool = False
    policy_frozen: bool = False
    killed: bool = False
    last_event_id: str = ""

    def record_decision(self, timestamp: float, decision_id: str) -> None:
        self.decision_count += 1
        self.last_decision_timestamp = timestamp
        self.decision_history.append((timestamp, decision_id))

    def record_switch(self, timestamp: float, from_id: str, to_id: str) -> None:
        self.switch_history.append((timestamp, from_id, to_id))
        self.last_switch_timestamp = timestamp
        self.playback_count += 1

    def record_render(self) -> None:
        self.render_count += 1

    def as_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "status": self.status.value,
            "frame_count": self.frame_count,
            "decision_count": self.decision_count,
            "render_count": self.render_count,
            "playback_count": self.playback_count,
            "consecutive_degraded": self.consecutive_degraded,
            "consecutive_missing": self.consecutive_missing,
            "pending_commands": self.pending_commands,
            "cache_misses": self.cache_misses,
            "render_failures": self.render_failures,
            "playback_failures": self.playback_failures,
            "baseline_forced": self.baseline_forced,
            "policy_frozen": self.policy_frozen,
            "current_artifact_id": self.cycle.current_artifact_id,
            "pending_artifact_id": self.cycle.pending_artifact_id,
            "current_cycle_end": self.cycle.current_cycle_end,
        }
