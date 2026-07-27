"""Hebrew audio asset resolution for CLM-03B Giuseppe/Aaron contracts."""

from __future__ import annotations

import hashlib
import io
import math
import wave
from dataclasses import dataclass
from typing import Any

from mindtune_clm.audio.assets import AudioAsset, AudioAssetRegistry, AudioRole
from mindtune_clm.hebrew_slice.models import HebrewAdaptiveItem


class HebrewAssetError(Exception):
    """Raised when a required Hebrew audio asset cannot be resolved."""

    def __init__(self, message: str, missing_assets: list[str], fallback_triggered: bool = False):
        super().__init__(message)
        self.missing_assets = missing_assets
        self.fallback_triggered = fallback_triggered


@dataclass
class HebrewResolvedAssets:
    """Resolved Italian and Hebrew audio assets for one trial."""

    item_id: str
    hebrew_asset_id: str
    hebrew_asset: AudioAsset
    hebrew_pointed_text: str
    italian_asset_id: str | None
    italian_asset: AudioAsset | None
    fallback_used: bool
    fallback_reason: str | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "item_id": self.item_id,
            "hebrew_asset_id": self.hebrew_asset_id,
            "hebrew_asset": self.hebrew_asset.as_dict(),
            "hebrew_pointed_text": self.hebrew_pointed_text,
            "italian_asset_id": self.italian_asset_id,
            "italian_asset": self.italian_asset.as_dict() if self.italian_asset else None,
            "fallback_used": self.fallback_used,
            "fallback_reason": self.fallback_reason,
        }


class HebrewAssetResolver:
    """Resolve cached Giuseppe/Aaron assets without live synthesis."""

    def __init__(
        self,
        registry: AudioAssetRegistry,
        *,
        aaron_fallback_asset_id: str | None = None,
        giuseppe_fallback_asset_id: str | None = None,
        allow_hila_hannah: bool = False,
    ) -> None:
        self.registry = registry
        self.aaron_fallback = aaron_fallback_asset_id
        self.giuseppe_fallback = giuseppe_fallback_asset_id
        self.allow_hila_hannah = allow_hila_hannah

    def resolve(self, item: HebrewAdaptiveItem) -> HebrewResolvedAssets:
        """Resolve assets for a Hebrew item."""
        hebrew_id = item.required_audio_asset_ids[0] if item.required_audio_asset_ids else ""
        hebrew_asset = self._get(hebrew_id, must_be_aaron=True)
        fallback_used = False
        fallback_reason = None
        if hebrew_asset is None:
            if self.aaron_fallback:
                hebrew_asset = self._get(self.aaron_fallback, must_be_aaron=True)
                if hebrew_asset is None:
                    raise HebrewAssetError(
                        f"missing Hebrew asset and fallback for {item.item_id}",
                        [hebrew_id, self.aaron_fallback],
                    )
                hebrew_id = self.aaron_fallback
                fallback_used = True
                fallback_reason = f"missing_asset:{item.required_audio_asset_ids[0]}"
            else:
                raise HebrewAssetError(
                    f"missing required Hebrew audio asset for {item.item_id}",
                    [hebrew_id],
                )

        # Ensure the asset carries the current approved pointed synthesis text.
        if hebrew_asset.label != item.canonical_pointed and hebrew_asset.label:
            fallback_reason = (fallback_reason or "") + ";label_mismatch"

        italian_id = f"clm06.giuseppe.{item.lemma_unpointed}"
        italian_asset = self._get(italian_id, must_be_giuseppe=True)
        if italian_asset is None and self.giuseppe_fallback:
            italian_asset = self._get(self.giuseppe_fallback, must_be_giuseppe=True)

        return HebrewResolvedAssets(
            item_id=item.item_id,
            hebrew_asset_id=hebrew_id,
            hebrew_asset=hebrew_asset,
            hebrew_pointed_text=item.canonical_pointed,
            italian_asset_id=italian_id,
            italian_asset=italian_asset,
            fallback_used=fallback_used,
            fallback_reason=fallback_reason,
        )

    def _get(self, asset_id: str, *, must_be_aaron: bool = False, must_be_giuseppe: bool = False) -> AudioAsset | None:
        asset = self.registry.get(asset_id)
        if asset is None:
            return None
        provenance = " ".join(asset.provenance) if isinstance(asset.provenance, (list, tuple)) else str(asset.provenance)
        label = asset.label or ""
        if not self.allow_hila_hannah:
            for forbidden in ("Hila", "Hannah"):
                if forbidden in provenance or forbidden in label:
                    return None
        if must_be_aaron and "aaron" not in provenance.lower() and "aaron" not in label.lower() and "he-IL" not in provenance:
            return None
        if must_be_giuseppe and "giuseppe" not in provenance.lower() and "giuseppe" not in label.lower():
            return None
        return asset


def _synthetic_tone_pcm(sample_rate: int = 16000, duration: float = 0.5) -> bytes:
    """Return deterministic 16-bit mono PCM for a synthetic test asset."""
    n_frames = int(sample_rate * duration)
    amp = 0.2 * 32767
    samples = bytearray()
    for i in range(n_frames):
        v = int(amp * math.sin(2.0 * math.pi * 440.0 * i / sample_rate))
        samples.extend(v.to_bytes(2, "little", signed=True))
    return bytes(samples)


def _synthetic_wav(pcm: bytes, sample_rate: int = 16000) -> bytes:
    with io.BytesIO() as bio:
        with wave.open(bio, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(sample_rate)
            w.writeframes(pcm)
        return bio.getvalue()


def make_synthetic_hebrew_audio_asset(
    asset_id: str,
    pointed_text: str,
    sample_rate: int = 16000,
    duration: float = 0.5,
) -> AudioAsset:
    """Build a synthetic Aaron-style Hebrew audio asset for tests."""
    pcm = _synthetic_tone_pcm(sample_rate, duration)
    canonical_bytes = _synthetic_wav(pcm, sample_rate)
    content_checksum = hashlib.sha256(canonical_bytes).hexdigest()
    return AudioAsset(
        asset_id=asset_id,
        content_checksum=content_checksum,
        role=AudioRole.SPEECH_SEGMENT,
        label=pointed_text,
        sample_rate=sample_rate,
        sample_width=2,
        channels=1,
        frame_count=len(pcm) // 2,
        duration=len(pcm) / 2 / sample_rate,
        source_type="synthetic_fixture_aaron",
        provenance=["aaron", "synthetic_fixture", asset_id, content_checksum],
        semantic_tags=frozenset({"he", "aaron", "pointed"}),
        canonical_pcm=pcm,
    )


def make_synthetic_giuseppe_audio_asset(
    asset_id: str,
    italian_text: str,
    sample_rate: int = 16000,
    duration: float = 0.5,
) -> AudioAsset:
    """Build a synthetic Giuseppe-style Italian audio asset for tests."""
    pcm = _synthetic_tone_pcm(sample_rate, duration)
    canonical_bytes = _synthetic_wav(pcm, sample_rate)
    content_checksum = hashlib.sha256(canonical_bytes).hexdigest()
    return AudioAsset(
        asset_id=asset_id,
        content_checksum=content_checksum,
        role=AudioRole.SPEECH_SEGMENT,
        label=italian_text,
        sample_rate=sample_rate,
        sample_width=2,
        channels=1,
        frame_count=len(pcm) // 2,
        duration=len(pcm) / 2 / sample_rate,
        source_type="synthetic_fixture_giuseppe",
        provenance=["giuseppe", "it-IT", "synthetic_fixture", asset_id, content_checksum],
        semantic_tags=frozenset({"it", "giuseppe"}),
        canonical_pcm=pcm,
    )
