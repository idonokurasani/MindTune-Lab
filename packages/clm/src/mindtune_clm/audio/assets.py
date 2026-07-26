"""Canonical audio asset contracts for CLM-03."""

from __future__ import annotations

import hashlib
import wave
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class AudioRole(str, Enum):
    """Semantic roles an audio asset may play in an utterance plan."""

    SPEECH_SEGMENT = "speech_segment"
    BREATHING_CUE = "breathing_cue"
    SILENCE = "silence"
    TONE_FIXTURE = "tone_fixture"


@dataclass(frozen=True)
class AudioAsset:
    """A canonical, language-neutral, deterministic audio asset."""

    asset_id: str
    content_checksum: str
    role: AudioRole
    label: str
    sample_rate: int
    sample_width: int
    channels: int
    frame_count: int
    duration: float
    source_type: str
    provenance: list[str]
    semantic_tags: frozenset[str] = field(default_factory=frozenset)
    canonical_pcm: bytes = field(default=b"", repr=False)

    def as_dict(self) -> dict[str, Any]:
        """Return a serializable, byte-light representation."""
        return {
            "asset_id": self.asset_id,
            "content_checksum": self.content_checksum,
            "role": self.role.value,
            "label": self.label,
            "sample_rate": self.sample_rate,
            "sample_width": self.sample_width,
            "channels": self.channels,
            "frame_count": self.frame_count,
            "duration": self.duration,
            "source_type": self.source_type,
            "provenance": list(self.provenance),
            "semantic_tags": sorted(self.semantic_tags),
        }


def _resample_nearest(input_frames: list[int], in_rate: int, out_rate: int) -> list[int]:
    if in_rate == out_rate:
        return input_frames
    ratio = in_rate / out_rate
    n_out = int(len(input_frames) / ratio)
    return [input_frames[int(i * ratio)] for i in range(n_out)]


def load_wav_asset(
    path: Path,
    asset_id: str,
    role: AudioRole,
    label: str,
    source_type: str = "fixture",
    target_sample_rate: int = 16000,
    target_sample_width: int = 2,
    target_channels: int = 1,
    provenance: list[str] | None = None,
    semantic_tags: frozenset[str] | None = None,
) -> AudioAsset:
    """Load a WAV file and normalize it to the canonical CLM-03 format."""
    path = Path(path)
    with wave.open(str(path), "rb") as handle:
        in_channels = handle.getnchannels()
        in_width = handle.getsampwidth()
        in_rate = handle.getframerate()
        in_frames = handle.getnframes()
        raw = handle.readframes(in_frames)

    if in_width == 1:
        samples = [int(b) - 128 for b in raw]
    elif in_width == 2:
        samples = [int.from_bytes(raw[i : i + 2], "little", signed=True) for i in range(0, len(raw), 2)]
    else:
        raise ValueError(f"unsupported sample width: {in_width}")

    if in_channels == 2:
        mono = []
        for i in range(0, len(samples), 2):
            mono.append((samples[i] + samples[i + 1]) // 2)
        samples = mono
    elif in_channels != 1:
        raise ValueError(f"unsupported channel count: {in_channels}")

    if in_rate != target_sample_rate:
        samples = _resample_nearest(samples, in_rate, target_sample_rate)

    # Convert to 16-bit PCM little-endian canonical bytes.
    canonical_pcm = b"".join(s.to_bytes(2, "little", signed=True) for s in samples)

    header = (
        b"RIFF"
        + (36 + len(canonical_pcm)).to_bytes(4, "little")
        + b"WAVEfmt "
        + (16).to_bytes(4, "little")
        + (1).to_bytes(2, "little")
        + (target_channels).to_bytes(2, "little")
        + (target_sample_rate).to_bytes(4, "little")
        + (target_sample_rate * target_sample_width * target_channels).to_bytes(4, "little")
        + (target_sample_width * target_channels).to_bytes(2, "little")
        + (target_sample_width * 8).to_bytes(2, "little")
        + b"data"
        + len(canonical_pcm).to_bytes(4, "little")
    )
    canonical_bytes = header + canonical_pcm
    content_checksum = hashlib.sha256(canonical_bytes).hexdigest()
    frame_count = len(samples)

    return AudioAsset(
        asset_id=asset_id,
        content_checksum=content_checksum,
        role=role,
        label=label,
        sample_rate=target_sample_rate,
        sample_width=target_sample_width,
        channels=target_channels,
        frame_count=frame_count,
        duration=frame_count / target_sample_rate,
        source_type=source_type,
        provenance=provenance or [asset_id, content_checksum],
        semantic_tags=semantic_tags or frozenset(),
        canonical_pcm=canonical_pcm,
    )


class AudioAssetRegistry:
    """Immutable lookup table for canonical audio assets."""

    def __init__(self, assets: list[AudioAsset] | None = None) -> None:
        self._assets: dict[str, AudioAsset] = {a.asset_id: a for a in (assets or [])}

    def register(self, asset: AudioAsset) -> None:
        self._assets[asset.asset_id] = asset

    def get(self, asset_id: str) -> AudioAsset | None:
        return self._assets.get(asset_id)

    def list_by_role(self, role: AudioRole) -> list[AudioAsset]:
        return [a for a in self._assets.values() if a.role == role]

    def assets(self) -> list[AudioAsset]:
        return list(self._assets.values())
