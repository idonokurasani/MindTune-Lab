"""Digest helpers for CLM-03B voice assets."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def _canonical_json(payload: dict[str, Any]) -> str:
    """Deterministic compact JSON with sorted keys."""
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def text_checksum(text: str) -> str:
    """SHA-256 checksum of UTF-8 text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def asset_digest(
    *,
    provider: str,
    voice_id: str,
    locale: str,
    tts_text: str,
    parameters: Any,
    provider_audio_checksum: str,
    canonical_audio_checksum: str,
) -> str:
    """Compute a provenance digest for a VoiceAsset."""
    payload = {
        "provider": provider,
        "voice": voice_id,
        "locale": locale,
        "tts_text": tts_text,
        "parameters": parameters,
        "provider_audio_checksum": provider_audio_checksum,
        "canonical_audio_checksum": canonical_audio_checksum,
    }
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()
