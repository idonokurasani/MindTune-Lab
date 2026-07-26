"""CLM-04B frame-to-render and render-to-playback latency tracker."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class LatencySample:
    """One cycle's latency sample."""

    frame_timestamp: float
    render_start: float | None = None
    render_end: float | None = None
    playback_start: float | None = None
    playback_end: float | None = None

    def frame_to_render_ms(self) -> float | None:
        if self.render_end is None or self.render_start is None:
            return None
        return (self.render_end - self.frame_timestamp) * 1000.0

    def render_to_playback_ms(self) -> float | None:
        if self.playback_start is None or self.render_end is None:
            return None
        return (self.playback_start - self.render_end) * 1000.0

    def playback_duration_ms(self) -> float | None:
        if self.playback_end is None or self.playback_start is None:
            return None
        return (self.playback_end - self.playback_start) * 1000.0


@dataclass
class LatencyTracker:
    """Track per-frame latency without wall-clock assumptions."""

    samples: dict[str, LatencySample] = field(default_factory=dict)
    max_frame_to_render_ms: float = 200.0
    max_render_to_playback_ms: float = 50.0

    def start_frame(self, frame_id: str, timestamp: float) -> None:
        if frame_id not in self.samples:
            self.samples[frame_id] = LatencySample(frame_timestamp=timestamp)
        else:
            self.samples[frame_id].frame_timestamp = timestamp

    def start_render(self, frame_id: str, timestamp: float) -> None:
        self._ensure(frame_id)
        self.samples[frame_id].render_start = timestamp

    def finish_render(self, frame_id: str, timestamp: float) -> None:
        self._ensure(frame_id)
        self.samples[frame_id].render_end = timestamp

    def start_playback(self, frame_id: str, timestamp: float) -> None:
        self._ensure(frame_id)
        self.samples[frame_id].playback_start = timestamp

    def finish_playback(self, frame_id: str, timestamp: float) -> None:
        self._ensure(frame_id)
        self.samples[frame_id].playback_end = timestamp

    def _ensure(self, frame_id: str) -> None:
        if frame_id not in self.samples:
            self.samples[frame_id] = LatencySample(frame_timestamp=0.0)

    def check(self, frame_id: str) -> tuple[bool, list[str]]:
        """Return (ok, reason_codes) for the given frame sample."""
        sample = self.samples.get(frame_id)
        if sample is None:
            return False, ["latency_sample_missing"]
        reasons: list[str] = []
        f2r = sample.frame_to_render_ms()
        r2p = sample.render_to_playback_ms()
        if f2r is not None and f2r > self.max_frame_to_render_ms:
            reasons.append(f"frame_to_render_exceeded:{f2r:.2f}ms")
        if r2p is not None and r2p > self.max_render_to_playback_ms:
            reasons.append(f"render_to_playback_exceeded:{r2p:.2f}ms")
        return not reasons, reasons

    def as_dict(self, frame_id: str) -> dict[str, Any]:
        sample = self.samples.get(frame_id)
        if sample is None:
            return {}
        return {
            "frame_id": frame_id,
            "frame_timestamp": sample.frame_timestamp,
            "frame_to_render_ms": sample.frame_to_render_ms(),
            "render_to_playback_ms": sample.render_to_playback_ms(),
            "playback_duration_ms": sample.playback_duration_ms(),
        }
