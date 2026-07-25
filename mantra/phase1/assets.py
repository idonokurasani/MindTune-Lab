"""Global durable audio asset registry and shared cache for Mantra/Domino.

Assets are keyed by stable asset_ids (e.g. ``he.lehitkasher.past.1sg``).
Each asset maps to a deterministic TTS cache key (provider + voice + exact
Unicode text + settings), so Mantra, Domino, review and feedback all share
one synthesized copy and never call SpeechGen twice for the same utterance.
"""
from __future__ import annotations

import json
import shutil
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, cast

import numpy as np
from numpy.typing import NDArray

from mantra.domain.audio_profile import AudioProfile

from .assembly import _decode_wav_to_int16, _encode_int16_to_wav, _silence_int16
from .tts import SpeechGenTTSProvider, TTSCache, TTSRuntimeError, _cache_key, sha256_hex
from .utils import normalize_unicode

GLOBAL_CACHE_DIR = Path("output/mantra_global_tts_cache")
ASSET_REGISTRY_PATH = Path("output/mantra_audio_assets.json")
TARGET_SAMPLE_RATE = 22050


@dataclass
class AudioAsset:
    """A durable, reusable audio asset."""

    asset_id: str
    provider: str
    voice: str
    locale: str
    text: str
    source_text: str
    rate: float
    pitch: float
    format: str
    cache_key: str
    duration: float = 0.0
    checksum: str = ""
    binyan: str = ""
    root: str = ""
    tense: str = ""
    mood: str = ""
    person: str = ""
    number: str = ""
    gender: str = ""
    subject: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v not in (None, "", 0.0)}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AudioAsset":
        return cls(**{k: data.get(k, "") for k in cls.__dataclass_fields__})


class AudioAssetRegistry:
    """Persisted registry mapping asset_ids to global TTS cache entries."""

    def __init__(self, registry_path: Path = ASSET_REGISTRY_PATH):
        self.registry_path = registry_path
        self._assets: dict[str, AudioAsset] = {}
        self._load()

    def _load(self) -> None:
        if not self.registry_path.exists():
            return
        data = json.loads(self.registry_path.read_text(encoding="utf-8"))
        for asset_id, record in data.items():
            self._assets[asset_id] = AudioAsset.from_dict(record)

    def save(self) -> None:
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {aid: asset.to_dict() for aid, asset in self._assets.items()}
        self.registry_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def register(self, asset: AudioAsset) -> None:
        self._assets[asset.asset_id] = asset
        self.save()

    def get(self, asset_id: str) -> AudioAsset | None:
        return self._assets.get(asset_id)

    def resolve_path(self, asset_id: str) -> Path | None:
        asset = self._assets.get(asset_id)
        if not asset:
            return None
        cache = TTSCache(GLOBAL_CACHE_DIR)
        return cache.cached_path(asset.cache_key)

    def ensure(
        self,
        asset_id: str,
        text: str,
        voice: str,
        locale: str,
        provider_name: str = "speechgen",
        rate: float = 1.0,
        pitch: float = 0.0,
        fmt: str = "wav",
        source_text: str = "",
        api_key: str | None = None,
        email: str | None = None,
        provider: Any = None,
        **metadata: Any,
    ) -> Path:
        """Return the asset WAV path, synthesizing only if missing globally."""
        normalized_text = normalize_unicode(text)
        cache_key = _cache_key(normalized_text, provider_name, voice, rate, pitch, fmt, None, locale=locale)

        cache = TTSCache(GLOBAL_CACHE_DIR)
        existing = cache.get(cache_key)
        if existing is not None:
            duration = len(existing.audio_bytes) / TARGET_SAMPLE_RATE
            # Use cached result; update registry if new asset_id.
            if asset_id not in self._assets:
                wav_path = cache.cached_path(cache_key)
                checksum = sha256_hex(existing.audio_bytes) if wav_path is None else sha256_hex(wav_path.read_bytes())
                self.register(
                    AudioAsset(
                        asset_id=asset_id,
                        provider=provider_name,
                        voice=voice,
                        locale=locale,
                        text=normalized_text,
                        source_text=source_text or normalized_text,
                        rate=rate,
                        pitch=pitch,
                        format=fmt,
                        cache_key=cache_key,
                        duration=existing.duration or duration,
                        checksum=checksum,
                        **metadata,
                    )
                )
            return cast(Path, cache.cached_path(cache_key))

        # Synthesize and cache.
        speech_provider = provider or SpeechGenTTSProvider(
            voice=voice, rate=rate, pitch=pitch, fmt=fmt, locale=locale
        )
        segment = type(
            "Segment",
            (object,),
            {
                "segment_id": asset_id,
                "source_text": normalized_text,
                "tts_text": normalized_text,
                "voice": voice,
                "locale": locale,
            },
        )()
        result = speech_provider.synthesize(segment)
        cache.put(cache_key, result)
        wav_path = cast(Path, cache.cached_path(cache_key))
        checksum = sha256_hex(wav_path.read_bytes())
        self.register(
            AudioAsset(
                asset_id=asset_id,
                provider=provider_name,
                voice=voice,
                locale=locale,
                text=normalized_text,
                source_text=source_text or normalized_text,
                rate=rate,
                pitch=pitch,
                format=fmt,
                cache_key=cache_key,
                duration=result.duration,
                checksum=checksum,
                **metadata,
            )
        )
        return wav_path

    def migrate_package_cache(self, package_cache_dir: Path) -> int:
        """Copy existing valid cache entries into the global cache."""
        global_cache = TTSCache(GLOBAL_CACHE_DIR)
        copied = 0
        for wav_path in sorted(package_cache_dir.glob("*.wav")):
            meta_path = wav_path.with_suffix(".meta.json")
            if not meta_path.exists():
                continue
            target_wav = global_cache.cache_dir / wav_path.name
            target_meta = global_cache.cache_dir / meta_path.name
            if target_wav.exists() and target_meta.exists():
                continue
            GLOBAL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
            shutil.copy2(wav_path, target_wav)
            shutil.copy2(meta_path, target_meta)
            copied += 1
        return copied


def merge_package_caches(package_cache_dirs: list[Path]) -> int:
    """Merge multiple package caches into the global shared cache."""
    registry = AudioAssetRegistry()
    total = 0
    for path in package_cache_dirs:
        if path.exists():
            total += registry.migrate_package_cache(path)
    return total


def concatenate_audio(paths: list[Path], pause_seconds: float = 0.3) -> bytes:
    """Concatenate WAV files with short local silence."""
    parts: list[NDArray[np.int16]] = []
    silence = _silence_int16(pause_seconds, TARGET_SAMPLE_RATE)
    for idx, path in enumerate(paths):
        wav_bytes = path.read_bytes()
        samples, source_sr = _decode_wav_to_int16(wav_bytes)
        if source_sr != TARGET_SAMPLE_RATE:
            from .assembly import _resample_mono_int16

            samples = _resample_mono_int16(samples, source_sr, TARGET_SAMPLE_RATE)
        parts.append(samples)
        if idx < len(paths) - 1:
            parts.append(silence)
    if not parts:
        return b""
    combined = np.concatenate(parts)
    return _encode_int16_to_wav(combined, TARGET_SAMPLE_RATE)


def build_compact_mantra(
    registry: AudioAssetRegistry,
    items: Sequence[tuple[str, float | None]],
    output_path: Path,
    default_pause: float = 0.3,
) -> dict[str, Any]:
    """Assemble a compact mantra from asset_ids and per-item trailing pauses.

    ``items`` is a list of (asset_id, pause_after_seconds).  ``None`` uses
    ``default_pause``.  The final pause is omitted.  Returns a manifest entry
    describing the result.
    """
    paths: list[Path] = []
    pauses: list[float | None] = []
    for asset_id, pause in items:
        p = registry.resolve_path(asset_id)
        if p is None:
            raise TTSRuntimeError(f"Asset {asset_id!r} not found in registry")
        paths.append(p)
        pauses.append(pause)

    parts: list[NDArray[np.int16]] = []
    for idx, path in enumerate(paths):
        wav_bytes = path.read_bytes()
        samples, source_sr = _decode_wav_to_int16(wav_bytes)
        if source_sr != TARGET_SAMPLE_RATE:
            from .assembly import _resample_mono_int16

            samples = _resample_mono_int16(samples, source_sr, TARGET_SAMPLE_RATE)
        parts.append(samples)
        if idx < len(paths) - 1:
            trailing_pause = pauses[idx]
            trailing = default_pause if trailing_pause is None else trailing_pause
            parts.append(_silence_int16(trailing, TARGET_SAMPLE_RATE))
    if not parts:
        return {}
    combined = np.concatenate(parts)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(_encode_int16_to_wav(combined, TARGET_SAMPLE_RATE))
    duration = len(combined) / TARGET_SAMPLE_RATE
    return {
        "name": output_path.name,
        "file": str(output_path),
        "duration": duration,
        "sample_rate": TARGET_SAMPLE_RATE,
        "checksum": sha256_hex(output_path.read_bytes()),
        "asset_ids": [aid for aid, _ in items],
    }


def domino_feedback_asset_id(target_asset_id: str) -> str:
    """Return the asset_id played as positive feedback for a correct answer."""
    return target_asset_id


TENSE_MARKER_ASSETS = {
    "he.tense.past": "בֶּעָבָר",
    "he.tense.present": "בַּהוֹוֶה",
    "he.tense.future": "בֶּעָתִיד",
}


def ensure_tense_markers(
    registry: AudioAssetRegistry,
    api_key: str | None = None,
    email: str | None = None,
    provider: Any = None,
    audio_profile: AudioProfile | None = None,
) -> dict[str, Path]:
    """Generate or reuse the three global Hebrew tense markers."""
    if audio_profile is not None:
        voice, locale = audio_profile.voice_for("he")
    else:
        voice, locale = "Hannah", "he-IL"
    paths: dict[str, Path] = {}
    for asset_id, text in TENSE_MARKER_ASSETS.items():
        paths[asset_id] = registry.ensure(
            asset_id=asset_id,
            text=text,
            voice=voice,
            locale=locale,
            source_text=text,
            api_key=api_key,
            email=email,
            provider=provider,
            binyan="",
            root="",
            tense="marker",
            mood="marker",
        )
    return paths
