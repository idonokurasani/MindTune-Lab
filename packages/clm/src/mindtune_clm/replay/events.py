"""Typed replay event constants for CLM-02."""

from __future__ import annotations

from enum import Enum


class CLM02EventType(str, Enum):
    """Canonical event types emitted by the deterministic sensor replay layer."""

    SENSOR_SOURCE_REGISTERED = "sensor_source_registered"
    REPLAY_MANIFEST_CREATED = "replay_manifest_created"
    SENSOR_SAMPLE_PARSED = "sensor_sample_parsed"
    SENSOR_SAMPLE_NORMALIZED = "sensor_sample_normalized"
    SENSOR_QUALITY_ASSESSED = "sensor_quality_assessed"
    REPLAY_WINDOW_CREATED = "replay_window_created"
    REPLAY_WINDOW_REJECTED = "replay_window_rejected"
    OBSERVATION_FRAME_GENERATED_FROM_REPLAY = "observation_frame_generated_from_replay"
    SENSOR_REPLAY_STARTED = "sensor_replay_started"
    SENSOR_REPLAY_COMPLETED = "sensor_replay_completed"
    SENSOR_REPLAY_FAILED = "sensor_replay_failed"
    REPLAY_DIGEST_COMPUTED = "replay_digest_computed"

    @classmethod
    def all(cls) -> list[str]:
        return [member.value for member in cls]
