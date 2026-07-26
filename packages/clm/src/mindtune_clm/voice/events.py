"""CLM-03B SpeechGen Giuseppe/Aaron voice pipeline events."""

from __future__ import annotations

from enum import Enum


class CLM03BEventType(str, Enum):
    """MPE-registered voice pipeline events for CLM-03B."""

    PEDAGOGICAL_VOICE_REQUEST_CREATED = "pedagogical_voice_request_created"
    VOICE_ROUTE_SELECTED = "voice_route_selected"
    SPEECHGEN_REQUEST_CREATED = "speechgen_request_created"
    SPEECHGEN_CACHE_HIT = "speechgen_cache_hit"
    SPEECHGEN_CACHE_MISS = "speechgen_cache_miss"
    SPEECHGEN_SYNTHESIS_STARTED = "speechgen_synthesis_started"
    SPEECHGEN_SYNTHESIS_COMPLETED = "speechgen_synthesis_completed"
    SPEECHGEN_SYNTHESIS_FAILED = "speechgen_synthesis_failed"
    SPEECHGEN_AUDIO_VALIDATED = "speechgen_audio_validated"
    VOICE_ASSET_CANONICALIZED = "voice_asset_canonicalized"
    VOICE_ASSET_REGISTERED_WITH_CLM03 = "voice_asset_registered_with_clm03"
    VOICE_CACHE_CORRUPTION_DETECTED = "voice_cache_corruption_detected"
    HUMAN_PRONUNCIATION_REVIEW_RECORDED = "human_pronunciation_review_recorded"
