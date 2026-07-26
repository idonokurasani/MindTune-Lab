"""CLM-03 real mantra audio actuator event types."""

from __future__ import annotations

from enum import Enum


class CLM03EventType(str, Enum):
    """MPE-registered audio actuator events for CLM-03."""

    AUDIO_ASSET_REGISTERED = "audio_asset_registered"
    UTTERANCE_PLAN_CREATED = "utterance_plan_created"
    AUDIO_RENDER_STARTED = "audio_render_started"
    AUDIO_SEGMENT_TRANSFORMED = "audio_segment_transformed"
    AUDIO_ARTIFACT_RENDERED = "audio_artifact_rendered"
    AUDIO_ARTIFACT_VALIDATED = "audio_artifact_validated"
    AUDIO_RENDER_FAILED = "audio_render_failed"
    PLAYBACK_COMMAND_CREATED = "playback_command_created"
    PLAYBACK_SCHEDULED = "playback_scheduled"
    PLAYBACK_STARTED = "playback_started"
    PLAYBACK_COMPLETED = "playback_completed"
    PLAYBACK_REJECTED = "playback_rejected"
    AUDIO_FALLBACK_APPLIED = "audio_fallback_applied"
    AUDIO_DIGEST_COMPUTED = "audio_digest_computed"
