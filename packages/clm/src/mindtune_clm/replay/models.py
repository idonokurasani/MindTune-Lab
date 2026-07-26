"""Immutable data models for deterministic sensor replay (CLM-02)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from mindtune_clm.loop import ControlLoopResult
from mindtune_clm.observations import ObservationFrame


@dataclass(frozen=True)
class SensorSample:
    """A raw sample as parsed from the source recording."""

    source_sample_index: int
    source_timestamp: float | None
    channel_values: dict[str, str | float | None]
    raw_quality: str | None = None
    parsed: bool = True
    parse_reason: str | None = None


@dataclass(frozen=True)
class NormalizedSensorSample:
    """A sample after deterministic normalization and unit conversion."""

    normalized_sample_id: str
    source_sample_index: int
    source_timestamp: float | None
    replay_relative_timestamp: float | None
    channel_values: dict[str, float | None]
    units: str
    missing_channel_indicators: dict[str, bool]
    normalization_operations: list[str]
    source_provenance: list[str]


@dataclass(frozen=True)
class QualityAssessment:
    """Deterministic quality decision for one sample or one replay window."""

    assessment_id: str
    accepted: bool
    quality_score: float
    reason_codes: list[str]
    detected_artifacts: list[str]
    missingness: float
    policy_version: str
    source_ids: list[str]
    sample_id: str | None = None
    window_id: str | None = None


@dataclass(frozen=True)
class ReplayWindow:
    """A fixed deterministic window of normalized sensor samples."""

    window_id: str
    start_replay_timestamp: float
    end_replay_timestamp: float
    ordered_sample_ids: list[str]
    accepted_sample_count: int
    rejected_sample_count: int
    channel_coverage: list[str]
    aggregate_quality: float
    deterministic_feature_values: dict[str, float]
    quality_assessment_id: str
    provenance: list[str]
    accepted: bool = True
    reason_codes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ReplayDigest:
    """Canonical deterministic digest of a replay execution."""

    digest_hex: str
    canonical_json: str


@dataclass
class ReplayResult:
    """Complete deterministic output of a sensor replay through CLM."""

    replay_manifest: Any
    source_checksum: str
    normalized_samples: list[NormalizedSensorSample]
    quality_assessments: list[QualityAssessment]
    windows: list[ReplayWindow]
    observation_frames: list[ObservationFrame]
    clm_session_result: ControlLoopResult
    canonical_replay_digest: ReplayDigest
    warnings: list[str]
    rejected_data_summary: dict[str, int]
