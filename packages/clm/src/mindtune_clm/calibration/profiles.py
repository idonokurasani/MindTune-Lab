"""Profile creation, versioning, and deterministic selection."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from typing import Any

from mindtune_clm.calibration.compatibility import (
    CompatibilityResult,
    ProfileCompatibility,
    is_valid_for_selection,
)
from mindtune_clm.calibration.estimators import BaselineEstimator, validate_stability
from mindtune_clm.calibration.models import (
    CalibrationProfile,
    CalibrationSession,
    ProfileStatus,
    RawObservation,
)
from mindtune_clm.calibration.protocol import CalibrationProtocol
from mindtune_clm.calibration.quality import is_profile_quality_valid


@dataclass
class ProfileSelectionResult:
    """Outcome of profile selection for a session."""

    profile_id: str | None
    profile_version: str | None
    reason: str
    compatibility: CompatibilityResult | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "profile_version": self.profile_version,
            "reason": self.reason,
            "compatibility": self.compatibility.as_dict() if self.compatibility else None,
        }


class ProfileBuilder:
    """Build a CalibrationProfile from a calibration session."""

    ALGORITHM_VERSION = "clm07.robust.v1"

    def build(
        self,
        session: CalibrationSession,
        protocol: CalibrationProtocol | None = None,
    ) -> CalibrationProfile:
        protocol = protocol or session.protocol or CalibrationProtocol.default()
        estimator = BaselineEstimator()
        quality = session.quality_summary
        baselines, stability = estimator.estimate_session(
            session.blocks, protocol, quality
        )

        accepted = quality.accepted_count
        rejected = quality.rejected_count
        duration = session.updated_at - session.created_at
        coverage = sorted({b.block_type for b in session.blocks})

        # Quality validation
        validity = ProfileStatus.VALID
        invalidation: list[str] = []
        if not is_profile_quality_valid(ProfileStatus.VALID, quality.as_dict(), protocol):
            validity = ProfileStatus.INSUFFICIENT_DATA
            invalidation.append("insufficient_accepted_observations_or_excessive_artifacts")
        elif not validate_stability(stability, protocol):
            validity = ProfileStatus.UNSTABLE
            invalidation.append("stability_validation_failed")

        profile_id = f"profile-{uuid.uuid4()}"
        return CalibrationProfile(
            profile_id=profile_id,
            profile_version="1",
            participant_id=session.participant_id,
            protocol_id=protocol.protocol_id,
            protocol_version=protocol.protocol_version,
            source_session_ids=(session.session_id,),
            sensor_family=session.sensor_family,
            sensor_config_fingerprint=session.sensor_config_fingerprint,
            parser_version=session.parser_version,
            feature_schema_version=session.feature_schema_version,
            modality_coverage=coverage,
            accepted_observation_count=accepted,
            rejected_observation_count=rejected,
            start_semantic_time=session.created_at,
            end_semantic_time=session.updated_at or time.time(),
            calibration_duration_seconds=max(0.0, duration),
            quality_summary=quality,
            stability_summary=stability,
            feature_baselines=baselines,
            compatibility_constraints={
                "sample_rate_policy": f"min_{protocol.min_sample_rate_hz}hz",
                "quality_policy_version": protocol.protocol_version,
                "task_domain": "hebrew_adaptive",
            },
            validity_status=validity,
            invalidation_reasons=invalidation,
            created_from_event_ids=[],
            algorithm_versions={"baseline": self.ALGORITHM_VERSION},
            provenance=[session.session_id],
        )


class ProfileSelector:
    """Deterministic selection of a compatible calibration profile."""

    def __init__(self, protocol: CalibrationProtocol = CalibrationProtocol.default()) -> None:
        self.protocol = protocol
        self.compatibility = ProfileCompatibility(protocol)

    def select(
        self,
        profiles: list[CalibrationProfile],
        participant_id: str,
        sensor_family: str,
        sensor_config_fingerprint: str,
        parser_version: str,
        feature_schema_version: str,
        pinned_profile_id: str | None = None,
    ) -> ProfileSelectionResult:
        """Select a pinned profile, then the latest valid compatible profile."""
        # 1. Explicit pinned compatible profile.
        if pinned_profile_id is not None:
            for p in profiles:
                if p.profile_id == pinned_profile_id:
                    result = self.compatibility.check(
                        p,
                        participant_id,
                        sensor_family,
                        sensor_config_fingerprint,
                        parser_version,
                        feature_schema_version,
                    )
                    if result.compatible and is_valid_for_selection(p):
                        return ProfileSelectionResult(
                            profile_id=p.profile_id,
                            profile_version=result.pin_version,
                            reason="explicit_pinned_compatible_profile",
                            compatibility=result,
                        )
                    return ProfileSelectionResult(
                        profile_id=None,
                        profile_version=None,
                        reason="pinned_profile_incompatible_or_invalid",
                        compatibility=result,
                    )
            return ProfileSelectionResult(
                profile_id=None,
                profile_version=None,
                reason="pinned_profile_not_found",
            )

        # 2. Latest valid compatible profile.
        compatible: list[tuple[CalibrationProfile, CompatibilityResult]] = []
        for p in profiles:
            if not is_valid_for_selection(p):
                continue
            result = self.compatibility.check(
                p,
                participant_id,
                sensor_family,
                sensor_config_fingerprint,
                parser_version,
                feature_schema_version,
            )
            if result.compatible:
                compatible.append((p, result))

        if compatible:
            # Sort by end_semantic_time descending; deterministic tie-break by profile_id.
            latest = max(
                compatible,
                key=lambda item: (item[0].end_semantic_time, item[0].profile_id),
            )[0]
            result = self.compatibility.check(
                latest,
                participant_id,
                sensor_family,
                sensor_config_fingerprint,
                parser_version,
                feature_schema_version,
            )
            return ProfileSelectionResult(
                profile_id=latest.profile_id,
                profile_version=result.pin_version,
                reason="latest_valid_compatible_profile",
                compatibility=result,
            )

        # 3. No profile.
        return ProfileSelectionResult(
            profile_id=None,
            profile_version=None,
            reason="no_compatible_profile",
        )


def recalibration_recommendation(
    profile: CalibrationProfile | None,
    recent_observations: list[RawObservation],
    sessions_since_calibration: int,
    drift_sessions: int,
) -> str | None:
    """Recommend recalibration without mutating the profile."""
    if profile is None:
        return "no_valid_profile"
    if profile.validity_status in {ProfileStatus.EXPIRED, ProfileStatus.INCOMPATIBLE, ProfileStatus.INVALID}:
        return f"profile_{profile.validity_status.value}"
    if drift_sessions >= 3 and sessions_since_calibration >= 3:
        return "persistent_baseline_drift"
    return None
