"""Deterministic language-to-voice routing for CLM-03B."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from mindtune_clm.voice.models import PedagogicalVoiceRequest, SynthesisParameters

# Accepted provider and voice identifiers from existing production evidence.
PROVIDER = "speechgen"
HEBREW_VOICE_ID = "Aaron"
ITALIAN_VOICE_ID = "Giuseppe"
HEBREW_LOCALE = "he-IL"
ITALIAN_LOCALE = "it-IT"


@dataclass(frozen=True)
class VoiceRoute:
    """Resolved route for a pedagogical voice request."""

    provider: str
    provider_voice_id: str
    locale: str
    language: str
    voice_display_name: str
    normalization_policy_version: str
    synthesis_parameter_version: str


class VoiceRoutingError(Exception):
    """Raised when a request cannot be routed to an exact voice."""


SUPPORTED_LOCALES = {HEBREW_LOCALE, ITALIAN_LOCALE}


def route(request: PedagogicalVoiceRequest) -> VoiceRoute:
    """Return the exact SpeechGen voice route for a request."""
    locale = request.locale.strip()
    language = request.language.strip().lower()

    if locale == ITALIAN_LOCALE or language == "it" or language == "ita":
        if has_hebrew(request.tts_text) or has_hebrew(request.source_text):
            raise VoiceRoutingError("Hebrew text cannot route to Giuseppe")
        return VoiceRoute(
            provider=PROVIDER,
            provider_voice_id=ITALIAN_VOICE_ID,
            locale=ITALIAN_LOCALE,
            language=language,
            voice_display_name="Giuseppe",
            normalization_policy_version=request.normalization_policy_version,
            synthesis_parameter_version=request.synthesis_parameter_version,
        )

    if locale == HEBREW_LOCALE or language == "he" or language == "heb" or language == "iw":
        if has_italian_latin_only(request.tts_text):
            # Reject if the tts_text looks like Italian; Aaron must not receive Italian.
            if not has_hebrew(request.tts_text):
                raise VoiceRoutingError("Italian text cannot route to Aaron")
        return VoiceRoute(
            provider=PROVIDER,
            provider_voice_id=HEBREW_VOICE_ID,
            locale=HEBREW_LOCALE,
            language=language,
            voice_display_name="Aaron",
            normalization_policy_version=request.normalization_policy_version,
            synthesis_parameter_version=request.synthesis_parameter_version,
        )

    raise VoiceRoutingError(
        f"Unsupported language/locale: language={request.language!r}, locale={request.locale!r}"
    )


def has_hebrew(text: str) -> bool:
    """Return True if text contains Hebrew block code points."""
    return any("\u0590" <= c <= "\u05FF" for c in text)


def has_italian_latin_only(text: str) -> bool:
    """Quick heuristic: text contains only Latin-1 characters and no Hebrew."""
    if not text:
        return False
    return not has_hebrew(text) and all(ord(c) < 256 for c in text)


def default_synthesis_parameters() -> SynthesisParameters:
    """Return accepted default SpeechGen synthesis parameters."""
    return SynthesisParameters(
        rate=1.0,
        pitch=0.0,
        format="wav",
        emotion="good",
        sample_rate=22050,
        channels=1,
    )


def build_speechgen_request_text(request: PedagogicalVoiceRequest, route: VoiceRoute) -> str:
    """Return the exact text to send to SpeechGen after deterministic normalization."""
    if route.provider_voice_id == HEBREW_VOICE_ID:
        from mindtune_clm.voice.hebrew import (
            normalize_source,
            validate_tts_text,
            validate_word_separation,
        )
        normalized = normalize_source(request.tts_text)
        validate_tts_text(
            normalized,
            request.source_text,
            unpointed_exception_approved=request.unpointed_exception_approved,
        )
        validate_word_separation(normalized)
        return normalized

    if route.provider_voice_id == ITALIAN_VOICE_ID:
        from mindtune_clm.voice.italian import normalize_source, validate_italian_text
        normalized = normalize_source(request.tts_text)
        validate_italian_text(normalized)
        return normalized

    raise VoiceRoutingError(f"Unknown provider voice id: {route.provider_voice_id}")


def _canonical_json(payload: dict[str, Any]) -> str:
    """Return a deterministic compact JSON string with sorted keys."""
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def request_checksum(route: VoiceRoute, tts_text: str, params: SynthesisParameters) -> str:
    """Compute a checksum over the normalized SpeechGen request inputs."""
    payload = {
        "provider": route.provider,
        "voice": route.provider_voice_id,
        "locale": route.locale,
        "text": tts_text,
        "rate": params.rate,
        "pitch": params.pitch,
        "format": params.format,
        "emotion": params.emotion,
        "sample_rate": params.sample_rate,
        "channels": params.channels,
        "normalization_policy_version": route.normalization_policy_version,
        "synthesis_parameter_version": route.synthesis_parameter_version,
    }
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def cache_key(route: VoiceRoute, tts_text: str, params: SynthesisParameters) -> str:
    """Return the content-addressed voice-aware cache key."""
    return request_checksum(route, tts_text, params)
