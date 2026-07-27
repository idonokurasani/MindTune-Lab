"""Data models for personal calibration and individual baselines."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mindtune_clm.calibration.protocol import CalibrationProtocol


class ProfileStatus(str, Enum):
    """Lifecycle status of a CalibrationProfile."""

    COLLECTING = "collecting"
    INSUFFICIENT_DATA = "insufficient_data"
    UNSTABLE = "unstable"
    VALID = "valid"
    DEGRADED = "degraded"
    EXPIRED = "expired"
    INCOMPATIBLE = "incompatible"
    SUPERSEDED = "superseded"
    INVALID = "invalid"


class CalibrationSessionStatus(str, Enum):
    """Lifecycle status of a calibration session."""

    CREATED = "created"
    PREPARED = "prepared"
    READINESS_CHECKED = "readiness_checked"
    COLLECTING = "collecting"
    PAUSED = "paused"
    VALIDATING = "validating"
    VALID = "valid"
    INSUFFICIENT_DATA = "insufficient_data"
    RETRYABLE = "retryable"
    QUALITY_FAILED = "quality_failed"
    UNSTABLE = "unstable"
    ABORTED = "aborted"


class NormalizationMethod(str, Enum):
    """Explicit, versioned normalization methods."""

    ROBUST_Z = "robust_z"
    PERCENTILE = "percentile"
    BOUNDED_RELATIVE_CHANGE = "bounded_relative_change"
    BASELINE_RATIO = "baseline_ratio"
    CATEGORICAL_DEVIATION = "categorical_deviation"
    NONE = "none"


@dataclass(frozen=True)
class RawObservation:
    """Immutable measured or derived source value."""

    observation_id: str
    participant_id: str
    session_id: str
    modality: str
    feature_name: str
    value: Any
    timestamp: float
    sensor_family: str
    sensor_config_fingerprint: str
    feature_schema_version: str
    quality_status: str = "accepted"
    reason_codes: list[str] = field(default_factory=list)
    source_event_id: str = ""
    parser_version: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "observation_id": self.observation_id,
            "participant_id": self.participant_id,
            "session_id": self.session_id,
            "modality": self.modality,
            "feature_name": self.feature_name,
            "value": self.value,
            "timestamp": self.timestamp,
            "sensor_family": self.sensor_family,
            "sensor_config_fingerprint": self.sensor_config_fingerprint,
            "feature_schema_version": self.feature_schema_version,
            "quality_status": self.quality_status,
            "reason_codes": list(self.reason_codes),
            "source_event_id": self.source_event_id,
            "parser_version": self.parser_version,
        }


@dataclass(frozen=True)
class FeatureBaseline:
    """Baseline statistics for one feature."""

    feature_name: str
    modality: str
    unit: str
    sample_count: int
    accepted_count: int
    rejected_count: int
    missing_count: int
    central_tendency: float
    dispersion: float
    robust_min: float
    robust_max: float
    selected_quantiles: dict[str, float] = field(default_factory=dict)
    outlier_policy: str = "iqr_1.5"
    distribution_shape: dict[str, Any] = field(default_factory=dict)
    stability_metrics: dict[str, float] = field(default_factory=dict)
    quality_status: str = ""
    transformation_recommendation: str = NormalizationMethod.ROBUST_Z
    algorithm_version: str = "clm07.robust.v1"

    def as_dict(self) -> dict[str, Any]:
        return {
            "feature_name": self.feature_name,
            "modality": self.modality,
            "unit": self.unit,
            "sample_count": self.sample_count,
            "accepted_count": self.accepted_count,
            "rejected_count": self.rejected_count,
            "missing_count": self.missing_count,
            "central_tendency": self.central_tendency,
            "dispersion": self.dispersion,
            "robust_min": self.robust_min,
            "robust_max": self.robust_max,
            "selected_quantiles": dict(self.selected_quantiles),
            "outlier_policy": self.outlier_policy,
            "distribution_shape": dict(self.distribution_shape),
            "stability_metrics": dict(self.stability_metrics),
            "quality_status": self.quality_status,
            "transformation_recommendation": self.transformation_recommendation,
            "algorithm_version": self.algorithm_version,
        }


@dataclass
class QualitySummary:
    """Quality summary for a calibration profile."""

    accepted_count: int = 0
    rejected_count: int = 0
    missing_count: int = 0
    artifact_rate: float = 0.0
    movement_contamination_rate: float = 0.0
    reason_distribution: dict[str, int] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "accepted_count": self.accepted_count,
            "rejected_count": self.rejected_count,
            "missing_count": self.missing_count,
            "artifact_rate": self.artifact_rate,
            "movement_contamination_rate": self.movement_contamination_rate,
            "reason_distribution": dict(self.reason_distribution),
        }


@dataclass
class StabilitySummary:
    """Stability summary for a calibration profile."""

    within_block_drift: float = 0.0
    block_agreement: float = 0.0
    sample_rate_stability: float = 0.0
    convergence: bool = False
    reason_codes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "within_block_drift": self.within_block_drift,
            "block_agreement": self.block_agreement,
            "sample_rate_stability": self.sample_rate_stability,
            "convergence": self.convergence,
            "reason_codes": list(self.reason_codes),
        }


@dataclass(frozen=True)
class CalibrationProfile:
    """Immutable, versioned personal calibration profile."""

    profile_id: str
    profile_version: str
    participant_id: str
    protocol_id: str
    protocol_version: str
    source_session_ids: tuple[str, ...]
    sensor_family: str
    sensor_config_fingerprint: str
    parser_version: str
    feature_schema_version: str
    modality_coverage: list[str]
    accepted_observation_count: int
    rejected_observation_count: int
    start_semantic_time: float
    end_semantic_time: float
    calibration_duration_seconds: float
    quality_summary: QualitySummary
    stability_summary: StabilitySummary
    feature_baselines: dict[str, FeatureBaseline]
    compatibility_constraints: dict[str, Any]
    validity_status: ProfileStatus
    invalidation_reasons: list[str] = field(default_factory=list)
    created_from_event_ids: list[str] = field(default_factory=list)
    algorithm_versions: dict[str, str] = field(default_factory=dict)
    provenance: list[str] = field(default_factory=list)
    superseded_profile_id: str | None = None

    def is_valid(self) -> bool:
        return self.validity_status == ProfileStatus.VALID

    def as_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "profile_version": self.profile_version,
            "participant_id": self.participant_id,
            "protocol_id": self.protocol_id,
            "protocol_version": self.protocol_version,
            "source_session_ids": list(self.source_session_ids),
            "sensor_family": self.sensor_family,
            "sensor_config_fingerprint": self.sensor_config_fingerprint,
            "parser_version": self.parser_version,
            "feature_schema_version": self.feature_schema_version,
            "modality_coverage": list(self.modality_coverage),
            "accepted_observation_count": self.accepted_observation_count,
            "rejected_observation_count": self.rejected_observation_count,
            "start_semantic_time": self.start_semantic_time,
            "end_semantic_time": self.end_semantic_time,
            "calibration_duration_seconds": self.calibration_duration_seconds,
            "quality_summary": self.quality_summary.as_dict(),
            "stability_summary": self.stability_summary.as_dict(),
            "feature_baselines": {k: v.as_dict() for k, v in self.feature_baselines.items()},
            "compatibility_constraints": dict(self.compatibility_constraints),
            "validity_status": self.validity_status.value,
            "invalidation_reasons": list(self.invalidation_reasons),
            "created_from_event_ids": list(self.created_from_event_ids),
            "algorithm_versions": dict(self.algorithm_versions),
            "provenance": list(self.provenance),
            "superseded_profile_id": self.superseded_profile_id,
        }


@dataclass(frozen=True)
class CalibratedObservation:
    """Normalized interpretation relative to one exact profile version."""

    calibrated_observation_id: str
    source_observation_id: str
    participant_id: str
    profile_id: str
    profile_version: str
    algorithm_version: str
    feature_name: str
    modality: str
    raw_value: Any
    calibrated_value: Any
    normalization_method: str
    baseline_center: float | None
    baseline_dispersion: float | None
    percentile: float | None
    compatibility_status: str
    quality_status: str
    reason_codes: list[str]
    semantic_timestamp: float
    provenance: list[str]

    def as_dict(self) -> dict[str, Any]:
        return {
            "calibrated_observation_id": self.calibrated_observation_id,
            "source_observation_id": self.source_observation_id,
            "participant_id": self.participant_id,
            "profile_id": self.profile_id,
            "profile_version": self.profile_version,
            "algorithm_version": self.algorithm_version,
            "feature_name": self.feature_name,
            "modality": self.modality,
            "raw_value": self.raw_value,
            "calibrated_value": self.calibrated_value,
            "normalization_method": self.normalization_method,
            "baseline_center": self.baseline_center,
            "baseline_dispersion": self.baseline_dispersion,
            "percentile": self.percentile,
            "compatibility_status": self.compatibility_status,
            "quality_status": self.quality_status,
            "reason_codes": list(self.reason_codes),
            "semantic_timestamp": self.semantic_timestamp,
            "provenance": list(self.provenance),
        }


@dataclass
class CalibrationReadiness:
    """Readiness evaluation for a calibration session."""

    ready: bool = False
    blocking_reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "ready": self.ready,
            "blocking_reasons": list(self.blocking_reasons),
            "warnings": list(self.warnings),
        }


@dataclass
class CalibrationBlock:
    """One block of a calibration session."""

    block_id: str
    block_type: str
    target_duration_seconds: float
    accepted_feature_observations: dict[str, list[RawObservation]] = field(default_factory=dict)
    rejected_observations: list[RawObservation] = field(default_factory=list)
    missing_count: int = 0
    start_time: float = 0.0
    end_time: float = 0.0

    def as_dict(self) -> dict[str, Any]:
        return {
            "block_id": self.block_id,
            "block_type": self.block_type,
            "target_duration_seconds": self.target_duration_seconds,
            "accepted_feature_observations": {
                k: [o.as_dict() for o in v] for k, v in self.accepted_feature_observations.items()
            },
            "rejected_observations": [o.as_dict() for o in self.rejected_observations],
            "missing_count": self.missing_count,
            "start_time": self.start_time,
            "end_time": self.end_time,
        }


@dataclass
class CalibrationSession:
    """State machine for a personal calibration session."""

    session_id: str
    participant_id: str
    protocol: CalibrationProtocol | None = None
    sensor_family: str = ""
    sensor_config_fingerprint: str = ""
    parser_version: str = ""
    feature_schema_version: str = ""
    status: CalibrationSessionStatus = CalibrationSessionStatus.CREATED
    blocks: list[CalibrationBlock] = field(default_factory=list)
    current_block: CalibrationBlock | None = None
    event_log: list[Any] = field(default_factory=list)
    created_at: float = 0.0
    updated_at: float = 0.0
    readiness: CalibrationReadiness = field(default_factory=CalibrationReadiness)
    collected_observations: list[RawObservation] = field(default_factory=list)
    quality_summary: QualitySummary = field(default_factory=QualitySummary)
    pinned_profile_id: str | None = None
    pinned_profile_version: str | None = None
    abort_reason: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "participant_id": self.participant_id,
            "protocol_id": self.protocol.protocol_id if self.protocol else None,
            "protocol_version": self.protocol.protocol_version if self.protocol else None,
            "sensor_family": self.sensor_family,
            "sensor_config_fingerprint": self.sensor_config_fingerprint,
            "parser_version": self.parser_version,
            "feature_schema_version": self.feature_schema_version,
            "status": self.status.value,
            "blocks": [b.as_dict() for b in self.blocks],
            "current_block": self.current_block.as_dict() if self.current_block else None,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "readiness": self.readiness.as_dict(),
            "pinned_profile_id": self.pinned_profile_id,
            "pinned_profile_version": self.pinned_profile_version,
            "abort_reason": self.abort_reason,
        }
