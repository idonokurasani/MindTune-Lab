"""Playback command, scheduling, and simulated backend for CLM-03."""

from __future__ import annotations

import wave
from dataclasses import dataclass, field
from io import BytesIO
from typing import Any, Callable

from mindtune_clm.audio.events import CLM03EventType
from mindtune_clm.audio.renderer import RenderedAudioArtifact


@dataclass(frozen=True)
class PlaybackCommand:
    """An instruction to play a validated audio artifact at a safe boundary."""

    command_id: str
    artifact_id: str
    render_cycle_id: str
    scheduled_semantic_timestamp: float
    safe_boundary: str
    expected_duration: float
    control_state_id: str
    source_receipt_id: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "command_id": self.command_id,
            "artifact_id": self.artifact_id,
            "render_cycle_id": self.render_cycle_id,
            "scheduled_semantic_timestamp": self.scheduled_semantic_timestamp,
            "safe_boundary": self.safe_boundary,
            "expected_duration": self.expected_duration,
            "control_state_id": self.control_state_id,
            "source_receipt_id": self.source_receipt_id,
        }


@dataclass(frozen=True)
class PlaybackReceipt:
    """Receipt from the playback backend for a scheduled command."""

    playback_receipt_id: str
    command_id: str
    artifact_id: str
    accepted: bool
    semantic_start_timestamp: float
    semantic_end_timestamp: float
    expected_duration: float
    observed_duration: float
    latency: float
    rejection_reason: str | None
    fallback_used: bool
    control_state_id: str
    source_actuation_receipt_id: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "playback_receipt_id": self.playback_receipt_id,
            "command_id": self.command_id,
            "artifact_id": self.artifact_id,
            "accepted": self.accepted,
            "semantic_start_timestamp": self.semantic_start_timestamp,
            "semantic_end_timestamp": self.semantic_end_timestamp,
            "expected_duration": self.expected_duration,
            "observed_duration": self.observed_duration,
            "latency": self.latency,
            "rejection_reason": self.rejection_reason,
            "fallback_used": self.fallback_used,
            "control_state_id": self.control_state_id,
            "source_actuation_receipt_id": self.source_actuation_receipt_id,
        }


def _validate_artifact_bytes(canonical_bytes: bytes) -> int:
    """Simulated backend validation. Returns frame count or raises ValueError."""
    with BytesIO(canonical_bytes) as bio:
        with wave.open(bio, "rb") as w:
            if w.getnchannels() != 1 or w.getsampwidth() != 2:
                raise ValueError("invalid audio format")
            return w.getnframes()


def simulated_playback_backend(command: PlaybackCommand, artifact: RenderedAudioArtifact, latency: float) -> PlaybackReceipt:
    """A deterministic speaker-free backend that validates the real rendered WAV."""
    start = command.scheduled_semantic_timestamp
    try:
        frames = _validate_artifact_bytes(artifact.canonical_bytes)
    except ValueError as exc:
        return PlaybackReceipt(
            playback_receipt_id=f"pr-{command.command_id}",
            command_id=command.command_id,
            artifact_id=artifact.artifact_id,
            accepted=False,
            semantic_start_timestamp=start,
            semantic_end_timestamp=start,
            expected_duration=command.expected_duration,
            observed_duration=0.0,
            latency=latency,
            rejection_reason=str(exc),
            fallback_used=False,
            control_state_id=command.control_state_id,
            source_actuation_receipt_id=command.source_receipt_id,
        )

    observed = frames / artifact.sample_rate
    return PlaybackReceipt(
        playback_receipt_id=f"pr-{command.command_id}",
        command_id=command.command_id,
        artifact_id=artifact.artifact_id,
        accepted=True,
        semantic_start_timestamp=start,
        semantic_end_timestamp=start + observed,
        expected_duration=command.expected_duration,
        observed_duration=observed,
        latency=latency,
        rejection_reason=None,
        fallback_used=artifact.fallback_used,
        control_state_id=command.control_state_id,
        source_actuation_receipt_id=command.source_receipt_id,
    )


@dataclass
class PlaybackScheduler:
    """Deterministic scheduler enforcing safe between_mantra_cycles boundaries."""

    scheduler_id: str = "mindtune_clm.audio.scheduler.v1"
    version: str = "1.0.0"
    safe_boundary: str = "between_mantra_cycles"
    backend: Callable[[PlaybackCommand, RenderedAudioArtifact, float], PlaybackReceipt] = field(default=simulated_playback_backend)
    backend_latency: float = 0.005
    command_counter: int = 0
    current_artifact: RenderedAudioArtifact | None = None
    pending_artifact: RenderedAudioArtifact | None = None
    pending_command: PlaybackCommand | None = None
    last_valid_artifact: RenderedAudioArtifact | None = None

    def schedule(
        self,
        artifact: RenderedAudioArtifact,
        render_cycle_id: str,
        semantic_start_timestamp: float,
        safe_boundary: str,
        control_state_id: str,
        source_receipt_id: str,
        runtime: Any | None = None,
    ) -> PlaybackReceipt:
        """Propose playback; validate boundary and activate only at next boundary."""
        self.command_counter += 1
        command_id = f"pb-{render_cycle_id}-{self.command_counter}"
        command = PlaybackCommand(
            command_id=command_id,
            artifact_id=artifact.artifact_id,
            render_cycle_id=render_cycle_id,
            scheduled_semantic_timestamp=semantic_start_timestamp,
            safe_boundary=safe_boundary,
            expected_duration=artifact.duration,
            control_state_id=control_state_id,
            source_receipt_id=source_receipt_id,
        )

        if runtime is not None:
            runtime.emit(
                CLM03EventType.PLAYBACK_COMMAND_CREATED,
                command.as_dict(),
                component="clm03_audio",
                component_version=self.version,
            )

        if safe_boundary != self.safe_boundary:
            if runtime is not None:
                runtime.emit(
                    CLM03EventType.PLAYBACK_REJECTED,
                    {"command_id": command_id, "reason": "unsafe_boundary"},
                    component="clm03_audio",
                    component_version=self.version,
                )
            return PlaybackReceipt(
                playback_receipt_id=f"pr-{command_id}",
                command_id=command_id,
                artifact_id=artifact.artifact_id,
                accepted=False,
                semantic_start_timestamp=semantic_start_timestamp,
                semantic_end_timestamp=semantic_start_timestamp,
                expected_duration=artifact.duration,
                observed_duration=0.0,
                latency=self.backend_latency,
                rejection_reason=f"unsafe_boundary: expected {self.safe_boundary}, got {safe_boundary}",
                fallback_used=True,
                control_state_id=control_state_id,
                source_actuation_receipt_id=source_receipt_id,
            )

        self.pending_artifact = artifact
        self.pending_command = command

        if runtime is not None:
            runtime.emit(
                CLM03EventType.PLAYBACK_SCHEDULED,
                {"command_id": command_id, "artifact_id": artifact.artifact_id},
                component="clm03_audio",
                component_version=self.version,
            )

        receipt = self.backend(command, artifact, self.backend_latency)
        if receipt.accepted:
            self.last_valid_artifact = artifact
            if self.current_artifact is None:
                self.current_artifact = artifact
        else:
            # fallback to last valid or pending if invalid
            fallback = self.last_valid_artifact if self.last_valid_artifact is not None else artifact
            receipt = self.backend(command, fallback, self.backend_latency)

        if runtime is not None:
            event_type = CLM03EventType.PLAYBACK_COMPLETED if receipt.accepted else CLM03EventType.PLAYBACK_REJECTED
            runtime.emit(
                event_type,
                receipt.as_dict(),
                component="clm03_audio",
                component_version=self.version,
            )

        return receipt

    def advance_boundary(self) -> RenderedAudioArtifact | None:
        """Activate the pending artifact if it exists; otherwise keep current."""
        if self.pending_artifact is not None:
            self.current_artifact = self.pending_artifact
            self.last_valid_artifact = self.pending_artifact
            self.pending_artifact = None
            self.pending_command = None
        return self.current_artifact
