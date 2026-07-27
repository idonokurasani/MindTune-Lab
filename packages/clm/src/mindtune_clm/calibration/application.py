"""Apply a CalibrationProfile to raw observations and estimator inputs."""

from __future__ import annotations

import math
import uuid
from typing import Any

from mindtune_clm.calibration.models import (
    CalibratedObservation,
    CalibrationProfile,
    FeatureBaseline,
    ProfileStatus,
    RawObservation,
)
from mindtune_clm.calibration.robust_stats import percentile_rank, zero_dispersion
from mindtune_clm.observations import ObservationFrame

# Features that can be extracted from an ObservationFrame for calibration.
_FRAME_FEATURE_MAP: list[tuple[str, str]] = [
    ("eeg_stability", "eeg"),
    ("behavioral_latency_ms", "behavioral"),
    ("hesitation_score", "behavioral"),
    ("error_score", "behavioral"),
    ("respiration_stability", "respiration"),
    ("voice_stability", "voice"),
]


def _is_profile_usable(profile: CalibrationProfile) -> bool:
    return profile.validity_status in {ProfileStatus.VALID, ProfileStatus.DEGRADED}


def _apply_method(  # noqa: C901
    raw_value: float,
    baseline: FeatureBaseline,
    method: str,
) -> tuple[float, list[str]]:
    """Apply the chosen normalization method and return (value, reasons)."""
    center = baseline.central_tendency
    dispersion = baseline.dispersion

    if zero_dispersion(dispersion):
        if method == "none":
            return raw_value, ["calibration_zero_dispersion_ignored"]
        return raw_value, ["calibration_zero_dispersion"]

    if method == "robust_z":
        scaled_mad = 1.4826 * dispersion
        if scaled_mad == 0.0:
            return 0.0, ["calibration_zero_dispersion"]
        return (raw_value - center) / scaled_mad, []

    if method == "bounded_relative_change":
        span = baseline.robust_max - baseline.robust_min
        if span == 0.0:
            return 0.0, ["calibration_zero_dispersion"]
        return (raw_value - center) / span, []

    if method == "baseline_ratio":
        if center <= 0.0 or raw_value < 0.0:
            return raw_value, ["calibration_method_not_applicable"]
        return raw_value / center, []

    if method == "percentile":
        # Percentile position is derived from the baseline quantiles.
        q = baseline.selected_quantiles
        if not q:
            return 0.0, ["calibration_feature_missing"]
        sorted_qs = sorted(q.values())
        return percentile_rank(sorted_qs, raw_value), []

    if method == "categorical_deviation":
        return 0.0 if math.isclose(raw_value, center) else 1.0, []

    if method == "none":
        return raw_value, []

    return raw_value, ["calibration_method_not_applicable"]


def calibrate_value(
    raw_value: float,
    baseline: FeatureBaseline | None,
    method: str,
) -> tuple[float | None, list[str]]:
    """Normalize a single value against a feature baseline."""
    if baseline is None:
        return None, ["calibration_feature_missing"]
    try:
        raw_float = float(raw_value)
    except (TypeError, ValueError):
        return None, ["calibration_feature_missing"]
    calibrated, reasons = _apply_method(raw_float, baseline, method)
    return calibrated, reasons


def apply_profile_to_raw_observation(
    observation: RawObservation,
    profile: CalibrationProfile,
) -> CalibratedObservation:
    """Calibrate one raw observation relative to a profile."""
    baseline = profile.feature_baselines.get(observation.feature_name)
    method = "none"
    if baseline is not None:
        method = baseline.transformation_recommendation or "robust_z"

    calibrated_value, reasons = calibrate_value(observation.value, baseline, method)

    compatibility = "compatible" if _is_profile_usable(profile) else "incompatible"
    if not _is_profile_usable(profile):
        reasons.append("calibration_profile_incompatible")

    quality = "ok"
    if baseline is None:
        quality = "feature_missing"
    elif baseline.dispersion == 0.0:
        quality = "zero_dispersion"

    return CalibratedObservation(
        calibrated_observation_id=f"cal-{uuid.uuid4()}",
        source_observation_id=observation.observation_id,
        participant_id=observation.participant_id,
        profile_id=profile.profile_id,
        profile_version=profile.profile_version,
        algorithm_version="clm07.apply.v1",
        feature_name=observation.feature_name,
        modality=observation.modality,
        raw_value=observation.value,
        calibrated_value=calibrated_value,
        normalization_method=method,
        baseline_center=baseline.central_tendency if baseline else None,
        baseline_dispersion=baseline.dispersion if baseline else None,
        percentile=None,
        compatibility_status=compatibility,
        quality_status=quality,
        reason_codes=reasons,
        semantic_timestamp=observation.timestamp,
        provenance=[profile.profile_id, observation.observation_id],
    )


def apply_profile_to_observation_frame(
    frame: ObservationFrame,
    profile: CalibrationProfile,
    participant_id: str,
) -> tuple[list[CalibratedObservation], dict[str, float]]:
    """Return calibrated observations and a numeric map for the estimator."""
    calibrated: list[CalibratedObservation] = []
    calibrated_values: dict[str, float] = {}

    for field_name, modality in _FRAME_FEATURE_MAP:
        raw_value = getattr(frame, field_name, None)
        if raw_value is None:
            continue
        baseline = profile.feature_baselines.get(field_name)
        method = "none"
        if baseline is not None:
            method = baseline.transformation_recommendation or "robust_z"
        value, reasons = calibrate_value(raw_value, baseline, method)

        compatibility = "compatible" if _is_profile_usable(profile) else "incompatible"
        if not _is_profile_usable(profile):
            reasons.append("calibration_profile_incompatible")
        if baseline is None:
            reasons.append("calibration_feature_missing")

        obs = CalibratedObservation(
            calibrated_observation_id=f"cal-{uuid.uuid4()}",
            source_observation_id=frame.observation_frame_id,
            participant_id=participant_id,
            profile_id=profile.profile_id,
            profile_version=profile.profile_version,
            algorithm_version="clm07.apply.v1",
            feature_name=field_name,
            modality=modality,
            raw_value=raw_value,
            calibrated_value=value,
            normalization_method=method,
            baseline_center=baseline.central_tendency if baseline else None,
            baseline_dispersion=baseline.dispersion if baseline else None,
            percentile=None,
            compatibility_status=compatibility,
            quality_status="ok" if value is not None else "failed",
            reason_codes=reasons,
            semantic_timestamp=frame.observation_timestamp,
            provenance=[profile.profile_id, frame.observation_frame_id],
        )
        calibrated.append(obs)
        if value is not None and isinstance(value, (int, float)):
            calibrated_values[field_name] = float(value)

    return calibrated, calibrated_values


class CalibrationApplier:
    """Apply a selected CalibrationProfile to incoming observations."""

    def __init__(self, profile: CalibrationProfile) -> None:
        self.profile = profile

    def apply_raw(self, observation: RawObservation) -> CalibratedObservation:
        return apply_profile_to_raw_observation(observation, self.profile)

    def apply_frame(
        self,
        frame: ObservationFrame,
        participant_id: str,
    ) -> tuple[list[CalibratedObservation], dict[str, float]]:
        return apply_profile_to_observation_frame(frame, self.profile, participant_id)

    def as_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile.profile_id,
            "profile_version": self.profile.profile_version,
            "validity_status": self.profile.validity_status.value,
        }
