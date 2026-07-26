"""Deterministic offline audio transforms for CLM-03."""

from __future__ import annotations

import math
from typing import Iterable


def _pcm_to_samples(pcm: bytes) -> list[int]:
    return [int.from_bytes(pcm[i : i + 2], "little", signed=True) for i in range(0, len(pcm), 2)]


def _samples_to_pcm(samples: Iterable[int]) -> bytes:
    return b"".join(s.to_bytes(2, "little", signed=True) for s in samples)


def ms_to_frames(ms: int, sample_rate: int) -> int:
    """Convert milliseconds to a frame count using floor rounding."""
    return int(ms * sample_rate / 1000.0)


def silence_transform(duration_ms: int, sample_rate: int) -> bytes:
    """Generate exact digital silence of the requested duration."""
    frames = ms_to_frames(duration_ms, sample_rate)
    return b"\x00\x00" * frames


def tempo_transform(pcm: bytes, tempo_ratio: float, sample_rate: int) -> bytes:
    """Nearest-neighbor tempo adjustment preserving pitch relationship.

    ``tempo_ratio`` is the speed multiplier: 1.0 preserves frames, <1.0
    produces a longer output.  Output length is ``floor(input_frames / ratio)``.
    """
    samples = _pcm_to_samples(pcm)
    in_frames = len(samples)
    if in_frames == 0 or tempo_ratio <= 0.0:
        return b""
    ratio = max(0.1, min(2.0, tempo_ratio))
    out_frames = int(in_frames / ratio)
    out: list[int] = []
    for i in range(out_frames):
        idx = int(i * ratio)
        if idx >= in_frames:
            idx = in_frames - 1
        out.append(samples[idx])
    return _samples_to_pcm(out)


def compute_peak(pcm: bytes) -> float:
    """Return the absolute peak amplitude of a PCM buffer (0..1 normalized)."""
    if not pcm:
        return 0.0
    samples = _pcm_to_samples(pcm)
    peak = max(abs(s) for s in samples)
    return peak / 32768.0


def compute_rms(pcm: bytes) -> float:
    """Return the RMS amplitude of a PCM buffer (0..1 normalized)."""
    if not pcm:
        return 0.0
    samples = _pcm_to_samples(pcm)
    squares = sum(s * s for s in samples)
    rms = math.sqrt(squares / len(samples))
    return min(1.0, rms / 32768.0)


def gain_and_emphasis(pcm: bytes, vocal_energy: float, prosodic_emphasis: float) -> tuple[bytes, int, float, float]:
    """Apply bounded vocal energy and prosodic emphasis to a PCM buffer.

    ``vocal_energy`` adds a uniform gain multiplier of ``1.0 + 0.5 * energy``.
    ``prosodic_emphasis`` adds a sinusoidal emphasis envelope that peaks at the
    segment midpoint.  The combined gain is clamped to ``MAX_GAIN`` (3.0).
    Returns the transformed bytes, clipping count, peak, and RMS.
    """
    samples = _pcm_to_samples(pcm)
    n = len(samples)
    if n == 0:
        return b"", 0, 0.0, 0.0

    MAX_GAIN = 3.0
    base_gain = 1.0 + 0.5 * max(0.0, min(1.0, vocal_energy))

    out: list[int] = []
    clip_count = 0
    sum_squares = 0
    peak_abs = 0

    for i, s in enumerate(samples):
        emphasis = 1.0 + max(0.0, min(1.0, prosodic_emphasis)) * math.sin(math.pi * i / max(1, n - 1))
        multiplier = min(MAX_GAIN, base_gain * emphasis)
        value = int(round(s * multiplier))
        if value > 32767:
            value = 32767
            clip_count += 1
        elif value < -32768:
            value = -32768
            clip_count += 1
        out.append(value)
        sum_squares += value * value
        if abs(value) > peak_abs:
            peak_abs = abs(value)

    rms = math.sqrt(sum_squares / n)
    return (
        _samples_to_pcm(out),
        clip_count,
        peak_abs / 32768.0,
        min(1.0, rms / 32768.0),
    )
