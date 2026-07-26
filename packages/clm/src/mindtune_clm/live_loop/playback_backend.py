"""Playback backends for CLM-04B: deterministic test backend and macOS afplay."""

from __future__ import annotations

import io
import shutil
import subprocess
import tempfile
import time
import wave
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mindtune_clm.audio.playback import PlaybackCommand, PlaybackReceipt
from mindtune_clm.audio.renderer import RenderedAudioArtifact


class PlaybackBackend(ABC):
    """Abstract playback backend for scheduled audio artifacts."""

    version: str = "0.0.0"

    @abstractmethod
    def play(
        self,
        command: PlaybackCommand,
        artifact: RenderedAudioArtifact,
        latency: float = 0.0,
    ) -> PlaybackReceipt:
        """Begin or simulate playback and return a deterministic receipt."""

    @abstractmethod
    def stop(self) -> bool:
        """Stop the currently playing audio, if any."""


def _validate_wav_bytes(wav_bytes: bytes) -> int:
    """Validate a WAV container and return its frame count."""
    try:
        with io.BytesIO(wav_bytes) as bio:
            with wave.open(bio, "rb") as handle:
                if handle.getnchannels() != 1 or handle.getsampwidth() != 2:
                    raise ValueError("invalid audio format")
                frames = handle.getnframes()
                if frames == 0:
                    raise ValueError("empty audio artifact")
                return frames
    except (EOFError, wave.Error) as exc:
        raise ValueError(f"invalid wav bytes: {exc}") from exc


@dataclass
class DeterministicPlaybackBackend(PlaybackBackend):
    """Speaker-free deterministic backend for CLM-04B tests.

    Validates the WAV container, returns deterministic timing, and supports
    injected success/failure/cancellation. No wall-clock is used.
    """

    version: str = "deterministic.v1"
    success: bool = True
    failure_reason: str | None = None
    cancelled: bool = False
    playback_counter: int = 0
    last_command_id: str = ""
    last_artifact_id: str = ""

    def play(
        self,
        command: PlaybackCommand,
        artifact: RenderedAudioArtifact,
        latency: float = 0.0,
    ) -> PlaybackReceipt:
        """Return a deterministic playback receipt."""
        self.playback_counter += 1
        self.last_command_id = command.command_id
        self.last_artifact_id = artifact.artifact_id
        start = command.scheduled_semantic_timestamp
        if self.cancelled:
            return PlaybackReceipt(
                playback_receipt_id=f"pb-cancelled-{self.playback_counter}",
                command_id=command.command_id,
                artifact_id=artifact.artifact_id,
                accepted=False,
                semantic_start_timestamp=start,
                semantic_end_timestamp=start,
                expected_duration=command.expected_duration,
                observed_duration=0.0,
                latency=latency,
                rejection_reason="cancelled",
                fallback_used=False,
                control_state_id=command.control_state_id,
                source_actuation_receipt_id=command.source_receipt_id,
            )
        if not self.success:
            return PlaybackReceipt(
                playback_receipt_id=f"pb-failed-{self.playback_counter}",
                command_id=command.command_id,
                artifact_id=artifact.artifact_id,
                accepted=False,
                semantic_start_timestamp=start,
                semantic_end_timestamp=start,
                expected_duration=command.expected_duration,
                observed_duration=0.0,
                latency=latency,
                rejection_reason=self.failure_reason or "injected_failure",
                fallback_used=False,
                control_state_id=command.control_state_id,
                source_actuation_receipt_id=command.source_receipt_id,
            )
        frames = _validate_wav_bytes(artifact.canonical_bytes)
        observed = frames / artifact.sample_rate
        return PlaybackReceipt(
            playback_receipt_id=f"pb-ok-{self.playback_counter}",
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

    def stop(self) -> bool:
        self.cancelled = True
        return True

    def as_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "success": self.success,
            "cancelled": self.cancelled,
            "playback_counter": self.playback_counter,
            "last_command_id": self.last_command_id,
            "last_artifact_id": self.last_artifact_id,
        }


@dataclass
class MacOSPlaybackBackend(PlaybackBackend):
    """Optional macOS afplay backend for manual real-hardware smoke tests."""

    version: str = "macos.afplay.v1"
    _process: subprocess.Popen[bytes] | None = None
    _temp_path: Path | None = None

    def play(
        self,
        command: PlaybackCommand,
        artifact: RenderedAudioArtifact,
        latency: float = 0.0,
    ) -> PlaybackReceipt:
        """Start ``afplay`` with a temporary WAV file and return a receipt."""
        afplay = shutil.which("afplay")
        if afplay is None:
            return PlaybackReceipt(
                playback_receipt_id=f"pb-macos-{command.command_id}",
                command_id=command.command_id,
                artifact_id=artifact.artifact_id,
                accepted=False,
                semantic_start_timestamp=command.scheduled_semantic_timestamp,
                semantic_end_timestamp=command.scheduled_semantic_timestamp,
                expected_duration=command.expected_duration,
                observed_duration=0.0,
                latency=latency,
                rejection_reason="afplay_not_found",
                fallback_used=False,
                control_state_id=command.control_state_id,
                source_actuation_receipt_id=command.source_receipt_id,
            )

        # Validate before writing to disk.
        try:
            frames = _validate_wav_bytes(artifact.canonical_bytes)
        except ValueError as exc:
            return PlaybackReceipt(
                playback_receipt_id=f"pb-macos-{command.command_id}",
                command_id=command.command_id,
                artifact_id=artifact.artifact_id,
                accepted=False,
                semantic_start_timestamp=command.scheduled_semantic_timestamp,
                semantic_end_timestamp=command.scheduled_semantic_timestamp,
                expected_duration=command.expected_duration,
                observed_duration=0.0,
                latency=latency,
                rejection_reason=str(exc),
                fallback_used=False,
                control_state_id=command.control_state_id,
                source_actuation_receipt_id=command.source_receipt_id,
            )

        self._cleanup()
        fd, tmp = tempfile.mkstemp(suffix=".wav")
        try:
            with open(fd, "wb") as f:
                f.write(artifact.canonical_bytes)
        except OSError:
            Path(tmp).unlink(missing_ok=True)
            return PlaybackReceipt(
                playback_receipt_id=f"pb-macos-{command.command_id}",
                command_id=command.command_id,
                artifact_id=artifact.artifact_id,
                accepted=False,
                semantic_start_timestamp=command.scheduled_semantic_timestamp,
                semantic_end_timestamp=command.scheduled_semantic_timestamp,
                expected_duration=command.expected_duration,
                observed_duration=0.0,
                latency=latency,
                rejection_reason="temp_file_write_failed",
                fallback_used=False,
                control_state_id=command.control_state_id,
                source_actuation_receipt_id=command.source_receipt_id,
            )

        self._temp_path = Path(tmp)
        self._process = subprocess.Popen(
            [afplay, str(self._temp_path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        observed = frames / artifact.sample_rate
        start = time.time()
        return PlaybackReceipt(
            playback_receipt_id=f"pb-macos-{command.command_id}",
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

    def stop(self) -> bool:
        """Terminate the afplay process and clean up the temporary file."""
        stopped = False
        if self._process is not None:
            try:
                if self._process.poll() is None:
                    self._process.terminate()
                    try:
                        self._process.wait(timeout=1.0)
                    except subprocess.TimeoutExpired:
                        self._process.kill()
                        self._process.wait(timeout=1.0)
                stopped = True
            except Exception:
                pass
            self._process = None
        self._cleanup()
        return stopped

    def _cleanup(self) -> None:
        if self._temp_path is not None:
            self._temp_path.unlink(missing_ok=True)
            self._temp_path = None

    def is_running(self) -> bool:
        return self._process is not None and self._process.poll() is None
