"""FC11-specific deterministic replay events for CLM-02B."""

from __future__ import annotations

from enum import Enum


class FC11EventType(str, Enum):
    """MPE-registered FC11 replay event payload types."""

    FC11_SOURCE_REGISTERED = "fc11_source_registered"
    FC11_METADATA_PARSED = "fc11_metadata_parsed"
    FC11_RECORD_PARSED = "fc11_record_parsed"
    FC11_RECORD_REJECTED = "fc11_record_rejected"
    FC11_TIMESTAMP_POLICY_APPLIED = "fc11_timestamp_policy_applied"
    FC11_SAMPLE_NORMALIZED = "fc11_sample_normalized"
    FC11_QUALITY_ASSESSED = "fc11_quality_assessed"
    FC11_WINDOW_CREATED = "fc11_window_created"
    FC11_WINDOW_REJECTED = "fc11_window_rejected"
    FC11_OBSERVATION_FRAME_GENERATED = "fc11_observation_frame_generated"
    FC11_REPLAY_DIGEST_COMPUTED = "fc11_replay_digest_computed"
    FC11_SENSOR_REPLAY_FAILED = "fc11_sensor_replay_failed"
    FC11_SENSOR_REPLAY_COMPLETED = "fc11_sensor_replay_completed"
