"""Synthetic data fixtures for CLM-07 tests and smoke scenarios."""

from __future__ import annotations

import time
import uuid
from typing import Any

from mindtune_clm.calibration.collector import SessionCollector
from mindtune_clm.calibration.models import (
    CalibrationBlock,
    CalibrationProfile,
    CalibrationSession,
    CalibrationSessionStatus,
    QualitySummary,
    RawObservation,
)
from mindtune_clm.calibration.profiles import ProfileBuilder
from mindtune_clm.calibration.protocol import CalibrationProtocol
from mindtune_clm.observations import ObservationFrame


def _now() -> float:
    return time.time()


def make_raw_observation(
    participant_id: str,
    feature_name: str,
    value: Any,
    modality: str,
    session_id: str | None = None,
    sensor_family: str = "fc11",
    sensor_config_fingerprint: str = "fc11.default",
    quality_status: str = "accepted",
    reason_codes: list[str] | None = None,
    timestamp: float | None = None,
) -> RawObservation:
    """Build a synthetic RawObservation."""
    return RawObservation(
        observation_id=f"obs-{uuid.uuid4()}",
        participant_id=participant_id,
        session_id=session_id or f"cal-session-{uuid.uuid4()}",
        modality=modality,
        feature_name=feature_name,
        value=value,
        timestamp=timestamp or _now(),
        sensor_family=sensor_family,
        sensor_config_fingerprint=sensor_config_fingerprint,
        feature_schema_version="clm07.schema.v1",
        quality_status=quality_status,
        reason_codes=reason_codes or [],
    )


def _make_block(
    session_id: str,
    block_type: str,
    participant_id: str,
    feature: str,
    count: int,
    base: float,
    noise: float,
    quality_status: str = "accepted",
) -> CalibrationBlock:
    block = CalibrationBlock(
        block_id=f"block-{block_type}-{uuid.uuid4()}",
        block_type=block_type,
        target_duration_seconds=30.0,
        start_time=_now(),
    )
    block.accepted_feature_observations[feature] = []
    denom = max(count - 1, 1)
    for i in range(count):
        value = base + ((i / denom) - 0.5) * noise
        obs = make_raw_observation(
            participant_id=participant_id,
            feature_name=feature,
            value=value,
            modality="eeg" if feature == "eeg_stability" else "behavioral",
            session_id=session_id,
            quality_status=quality_status,
            timestamp=_now(),
        )
        block.accepted_feature_observations[feature].append(obs)
    block.end_time = _now()
    return block


def build_calibration_session(
    participant_id: str,
    accepted_per_block: int = 15,
    noise: float = 0.05,
    movement_rate: float = 0.0,
    zero_dispersion: bool = False,
    sensor_config_fingerprint: str = "fc11.default",
    bases: dict[str, float] | None = None,
) -> CalibrationSession:
    """Build a calibration session with four blocks."""
    protocol = CalibrationProtocol.default()
    session = CalibrationSession(
        session_id=f"cal-session-{uuid.uuid4()}",
        participant_id=participant_id,
        protocol=protocol,
        sensor_family="fc11",
        sensor_config_fingerprint=sensor_config_fingerprint,
        parser_version="fc11.parser.v1",
        feature_schema_version="clm07.schema.v1",
        status=CalibrationSessionStatus.COLLECTING,
        created_at=_now(),
        updated_at=_now(),
    )
    collector = SessionCollector(session)

    # Per-participant shift ensures different participants have different baselines.
    participant_shift = (hash(participant_id) % 1000) / 10000.0
    feature = "eeg_stability"
    base_map = bases or {"rest": 0.80, "low_load": 0.70, "moderate_load": 0.55, "recovery": 0.75}
    for block_type, base in base_map.items():
        base = base + participant_shift
        block = _make_block(
            session.session_id, block_type, participant_id, feature, accepted_per_block, base, noise
        )
        # Add some movement-contaminated observations if requested.
        for _ in range(int(accepted_per_block * movement_rate)):
            obs = make_raw_observation(
                participant_id=participant_id,
                feature_name=feature,
                value=0.1,
                modality="eeg",
                session_id=session.session_id,
                quality_status="rejected",
                reason_codes=["movement"],
                timestamp=_now(),
            )
            block.rejected_observations.append(obs)

        if zero_dispersion:
            for obs in block.accepted_feature_observations[feature]:
                object.__setattr__(obs, "value", 0.50)

        collector.start_block(block)
        for obs in block.accepted_feature_observations[feature]:
            collector.collect(obs)
        for obs in block.rejected_observations:
            collector.reject(obs, "movement")
        collector.missing("synthetic_missing")

    # Aggregate quality summary from collectors.
    accepted = 0
    rejected = 0
    missing = 0
    for coll in collector.block_collectors.values():
        q = coll.quality_summary()
        accepted += q.accepted_count
        rejected += q.rejected_count
        missing += q.missing_count
    session.quality_summary = QualitySummary(
        accepted_count=accepted,
        rejected_count=rejected,
        missing_count=missing,
    )
    session.updated_at = _now()
    return session


def build_valid_profile(
    participant_id: str,
    sensor_config_fingerprint: str = "fc11.default",
) -> CalibrationProfile:
    """Build a valid, stable calibration profile."""
    session = build_calibration_session(participant_id, sensor_config_fingerprint=sensor_config_fingerprint)
    builder = ProfileBuilder()
    return builder.build(session)


def build_insufficient_data_profile(participant_id: str) -> CalibrationProfile:
    """Build a profile with too few accepted observations."""
    session = build_calibration_session(participant_id, accepted_per_block=2)
    builder = ProfileBuilder()
    return builder.build(session)


def build_unstable_profile(participant_id: str) -> CalibrationProfile:
    """Build a profile with excessive within-block drift."""
    session = build_calibration_session(
        participant_id,
        noise=0.02,
        bases={"rest": 0.95, "low_load": 0.20, "moderate_load": 0.90, "recovery": 0.15},
    )
    builder = ProfileBuilder()
    return builder.build(session)


def build_movement_contamination_profile(participant_id: str) -> CalibrationProfile:
    """Build a session with many rejected movement windows."""
    session = build_calibration_session(participant_id, movement_rate=0.6)
    builder = ProfileBuilder()
    return builder.build(session)


def build_zero_dispersion_profile(participant_id: str) -> CalibrationProfile:
    """Build a profile where one feature has zero dispersion."""
    session = build_calibration_session(participant_id, zero_dispersion=True)
    builder = ProfileBuilder()
    return builder.build(session)


def build_incompatible_config_profile(participant_id: str) -> CalibrationProfile:
    """Build a valid profile with a non-default sensor config fingerprint."""
    return build_valid_profile(participant_id, sensor_config_fingerprint="fc11.incompatible")


def make_observation_frame(
    eeg_stability: float | None = 0.75,
    behavioral_latency_ms: float | None = 850.0,
    hesitation_score: float | None = 0.1,
    error_score: float | None = 0.0,
    respiration_stability: float | None = None,
    voice_stability: float | None = None,
) -> ObservationFrame:
    """Build a deterministic ObservationFrame for calibration tests."""
    return ObservationFrame(
        observation_frame_id=f"frame-{uuid.uuid4()}",
        control_cycle_id=f"cc-{uuid.uuid4()}",
        session_id=f"session-{uuid.uuid4()}",
        sequence_number=1,
        observation_timestamp=_now(),
        eeg_stability=eeg_stability,
        behavioral_latency_ms=behavioral_latency_ms,
        hesitation_score=hesitation_score,
        error_score=error_score,
        respiration_stability=respiration_stability,
        voice_stability=voice_stability,
        available_modalities=["behavioral", "eeg"],
        source_event_ids=["source-1"],
    )


def build_two_participant_profiles() -> tuple[CalibrationProfile, CalibrationProfile, CalibrationProfile]:
    """Return (profileA, profileB, profileForB) to test isolation."""
    profile_a = build_valid_profile("participant-a")
    profile_b = build_valid_profile("participant-b")
    # A second profile for B used to prove recalibration creates a new version.
    profile_b2 = build_valid_profile("participant-b")
    return profile_a, profile_b, profile_b2
