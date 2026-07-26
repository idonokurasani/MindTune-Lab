"""Content-addressed voice-aware cache for CLM-03B."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from mindtune_clm.voice.models import VoiceAsset


class VoiceCache:
    """Disk-backed cache keyed by provider, voice, locale, exact tts_text, and synthesis params."""

    def __init__(self, cache_dir: Path):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.wav_dir = self.cache_dir / "wav"
        self.meta_dir = self.cache_dir / "meta"
        self.wav_dir.mkdir(parents=True, exist_ok=True)
        self.meta_dir.mkdir(parents=True, exist_ok=True)

    def _paths(self, key: str) -> tuple[Path, Path, Path]:
        # Sharded directories by first two hex chars for file-system friendliness.
        shard = key[:2]
        return (
            self.wav_dir / shard / f"{key}.wav",
            self.meta_dir / shard / f"{key}.json",
            self.meta_dir / shard / f"{key}.lock",
        )

    def _asset_from_meta(self, meta: dict[str, Any], wav_path: Path) -> VoiceAsset | None:
        if not wav_path.exists():
            return None
        canonical_pcm = wav_path.read_bytes()
        # wav_path stores canonical PCM bytes (not a WAV container) for compactness.
        return VoiceAsset(
            asset_id=meta["asset_id"],
            provider=meta["provider"],
            voice_display_name=meta["voice_display_name"],
            provider_voice_id=meta["provider_voice_id"],
            locale=meta["locale"],
            source_text=meta["source_text"],
            tts_text=meta["tts_text"],
            source_text_checksum=meta["source_text_checksum"],
            tts_text_checksum=meta["tts_text_checksum"],
            provider_audio_checksum=meta["provider_audio_checksum"],
            canonical_audio_checksum=meta["canonical_audio_checksum"],
            cache_key=meta["cache_key"],
            sample_rate=meta["sample_rate"],
            sample_width=meta["sample_width"],
            channels=meta["channels"],
            frame_count=meta["frame_count"],
            duration=meta["duration"],
            provider_receipt_id=meta["provider_receipt_id"],
            grammatical_entry_ids=tuple(meta.get("grammatical_entry_ids", [])),
            human_review_status=meta.get("human_review_status", "pending"),
            reviewer_notes=meta.get("reviewer_notes", ""),
            provenance=meta.get("provenance", {}),
            canonical_pcm=canonical_pcm,
        )

    def get(self, key: str) -> VoiceAsset | None:
        """Return cached VoiceAsset or None if missing or corrupted."""
        wav_path, meta_path, _lock = self._paths(key)
        if not meta_path.exists():
            return None
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None
        expected_canonical_checksum = meta.get("canonical_audio_checksum")
        if not wav_path.exists():
            return None
        canonical_pcm = wav_path.read_bytes()
        import hashlib
        actual = hashlib.sha256(canonical_pcm).hexdigest()
        if actual != expected_canonical_checksum:
            return None
        return self._asset_from_meta(meta, wav_path)

    def put(self, asset: VoiceAsset) -> Path:
        """Store VoiceAsset atomically, keyed by its cache_key."""
        wav_path, meta_path, _lock = self._paths(asset.cache_key)
        wav_path.parent.mkdir(parents=True, exist_ok=True)
        meta_path.parent.mkdir(parents=True, exist_ok=True)

        tmp_wav = wav_path.with_suffix(".wav.tmp")
        tmp_meta = meta_path.with_suffix(".json.tmp")

        tmp_wav.write_bytes(asset.canonical_pcm)

        # Validate expected checksum immediately.
        import hashlib
        actual = hashlib.sha256(asset.canonical_pcm).hexdigest()
        if actual != asset.canonical_audio_checksum:
            raise CacheChecksumError("canonical PCM does not match stored checksum")

        meta = {
            "asset_id": asset.asset_id,
            "provider": asset.provider,
            "voice_display_name": asset.voice_display_name,
            "provider_voice_id": asset.provider_voice_id,
            "locale": asset.locale,
            "source_text": asset.source_text,
            "tts_text": asset.tts_text,
            "source_text_checksum": asset.source_text_checksum,
            "tts_text_checksum": asset.tts_text_checksum,
            "provider_audio_checksum": asset.provider_audio_checksum,
            "canonical_audio_checksum": asset.canonical_audio_checksum,
            "cache_key": asset.cache_key,
            "sample_rate": asset.sample_rate,
            "sample_width": asset.sample_width,
            "channels": asset.channels,
            "frame_count": asset.frame_count,
            "duration": asset.duration,
            "provider_receipt_id": asset.provider_receipt_id,
            "grammatical_entry_ids": list(asset.grammatical_entry_ids),
            "human_review_status": asset.human_review_status,
            "reviewer_notes": asset.reviewer_notes,
            "provenance": asset.provenance,
        }
        tmp_meta.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        shutil.move(str(tmp_wav), str(wav_path))
        shutil.move(str(tmp_meta), str(meta_path))
        return wav_path

    def invalidate(self, key: str) -> None:
        """Remove a corrupted cache entry."""
        wav_path, meta_path, _lock = self._paths(key)
        wav_path.unlink(missing_ok=True)
        meta_path.unlink(missing_ok=True)


class CacheChecksumError(Exception):
    """Raised when a cached asset checksum does not match."""
