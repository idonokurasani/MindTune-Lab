"""Versioned calibration protocols and threshold policies."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class CalibrationProtocol:
    """A versioned personal calibration protocol."""

    protocol_id: str
    protocol_version: str
    block_types: tuple[str, ...] = field(default_factory=lambda: ("rest", "low_load", "moderate_load", "recovery"))
    min_duration_seconds: float = 60.0
    min_accepted_observations: int = 10
    max_missingness_rate: float = 0.2
    max_artifact_rate: float = 0.15
    max_movement_contamination_rate: float = 0.2
    min_sample_rate_hz: float = 1.0
    max_sample_rate_drift: float = 0.05
    max_within_block_drift: float = 0.2
    min_block_agreement: float = 0.10
    expiry_seconds: float = 86400.0
    features: tuple[str, ...] = field(
        default_factory=lambda: (
            "eeg_stability",
            "behavioral_latency_ms",
            "hesitation_score",
            "error_score",
            "respiration_stability",
            "voice_stability",
            "vendor_attention",
            "vendor_meditation",
            "confidence",
            "response_time_correct",
            "response_time_incorrect",
            "omission",
            "audio_exposure",
            "movement",
        )
    )
    normalization_defaults: dict[str, str] = field(default_factory=dict)
    threshold_policy: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "normalization_defaults",
            {
                "eeg_stability": "robust_z",
                "behavioral_latency_ms": "robust_z",
                "hesitation_score": "bounded_relative_change",
                "error_score": "categorical_deviation",
                "respiration_stability": "robust_z",
                "voice_stability": "robust_z",
                "vendor_attention": "percentile",
                "vendor_meditation": "percentile",
                "confidence": "robust_z",
                "response_time_correct": "robust_z",
                "response_time_incorrect": "robust_z",
                "omission": "categorical_deviation",
                "audio_exposure": "baseline_ratio",
                "movement": "bounded_relative_change",
            },
        )
        object.__setattr__(
            self,
            "threshold_policy",
            {
                "min_duration_seconds": self.min_duration_seconds,
                "min_accepted_observations": self.min_accepted_observations,
                "max_missingness_rate": self.max_missingness_rate,
                "max_artifact_rate": self.max_artifact_rate,
                "max_movement_contamination_rate": self.max_movement_contamination_rate,
                "min_sample_rate_hz": self.min_sample_rate_hz,
                "max_sample_rate_drift": self.max_sample_rate_drift,
                "max_within_block_drift": self.max_within_block_drift,
                "min_block_agreement": self.min_block_agreement,
                "expiry_seconds": self.expiry_seconds,
            },
        )

    @classmethod
    def default(cls) -> "CalibrationProtocol":
        """Return the built-in CLM-07 protocol."""
        return cls(
            protocol_id="clm07.personal-baseline",
            protocol_version="v1",
        )

    @classmethod
    def by_id(cls, protocol_id: str, protocol_version: str = "v1") -> "CalibrationProtocol | None":
        if protocol_id == cls.default().protocol_id and protocol_version == cls.default().protocol_version:
            return cls.default()
        return None

    def as_dict(self) -> dict[str, Any]:
        return {
            "protocol_id": self.protocol_id,
            "protocol_version": self.protocol_version,
            "block_types": list(self.block_types),
            "min_duration_seconds": self.min_duration_seconds,
            "min_accepted_observations": self.min_accepted_observations,
            "max_missingness_rate": self.max_missingness_rate,
            "max_artifact_rate": self.max_artifact_rate,
            "max_movement_contamination_rate": self.max_movement_contamination_rate,
            "min_sample_rate_hz": self.min_sample_rate_hz,
            "max_sample_rate_drift": self.max_sample_rate_drift,
            "max_within_block_drift": self.max_within_block_drift,
            "min_block_agreement": self.min_block_agreement,
            "expiry_seconds": self.expiry_seconds,
            "features": list(self.features),
            "normalization_defaults": dict(self.normalization_defaults),
            "threshold_policy": dict(self.threshold_policy),
        }
