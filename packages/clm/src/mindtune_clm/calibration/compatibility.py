"""Profile compatibility checks and session selection rules."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from mindtune_clm.calibration.models import CalibrationProfile, ProfileStatus
from mindtune_clm.calibration.protocol import CalibrationProtocol


@dataclass
class CompatibilityResult:
    """Result of a profile-compatibility check."""

    compatible: bool
    reasons: list[str] = field(default_factory=list)
    pin_version: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "compatible": self.compatible,
            "reasons": list(self.reasons),
            "pin_version": self.pin_version,
        }


def _same(a: Any, b: Any) -> bool:
    return str(a) == str(b)


class ProfileCompatibility:
    """Compare a profile to a session or observation context."""

    def __init__(self, protocol: CalibrationProtocol) -> None:
        self.protocol = protocol

    def check(  # noqa: C901
        self,
        profile: CalibrationProfile,
        participant_id: str,
        sensor_family: str,
        sensor_config_fingerprint: str,
        parser_version: str,
        feature_schema_version: str,
        sample_rate_policy: str | None = None,
        quality_policy_version: str | None = None,
        task_domain: str | None = None,
    ) -> CompatibilityResult:
        """Return compatibility result and, if compatible, the exact version to pin."""
        reasons: list[str] = []

        if not _same(profile.participant_id, participant_id):
            reasons.append("participant_mismatch")
        if not _same(profile.sensor_family, sensor_family):
            reasons.append("sensor_family_mismatch")
        if not _same(profile.sensor_config_fingerprint, sensor_config_fingerprint):
            reasons.append("sensor_config_mismatch")
        if parser_version and not _same(profile.parser_version, parser_version):
            reasons.append("parser_version_mismatch")
        if not _same(profile.feature_schema_version, feature_schema_version):
            reasons.append("feature_schema_mismatch")
        if sample_rate_policy and not _same(profile.compatibility_constraints.get("sample_rate_policy"), sample_rate_policy):
            reasons.append("sample_rate_policy_mismatch")
        if quality_policy_version and not _same(
            profile.compatibility_constraints.get("quality_policy_version"), quality_policy_version
        ):
            reasons.append("quality_policy_version_mismatch")
        if task_domain and not _same(profile.compatibility_constraints.get("task_domain"), task_domain):
            reasons.append("task_domain_mismatch")

        if profile.validity_status in {
            ProfileStatus.EXPIRED,
            ProfileStatus.INCOMPATIBLE,
            ProfileStatus.SUPERSEDED,
            ProfileStatus.INVALID,
        }:
            reasons.append(f"profile_status:{profile.validity_status.value}")

        if reasons:
            return CompatibilityResult(compatible=False, reasons=reasons)

        return CompatibilityResult(
            compatible=True,
            reasons=["compatible"],
            pin_version=profile.profile_version,
        )

    def is_expired(self, profile: CalibrationProfile, now: float | None = None) -> bool:
        if profile.validity_status == ProfileStatus.EXPIRED:
            return True
        now = now or time.time()
        age = now - profile.end_semantic_time
        return age > self.protocol.expiry_seconds


def is_valid_for_selection(profile: CalibrationProfile) -> bool:
    """Return True when a profile is eligible for automatic selection."""
    return profile.is_valid() and profile.validity_status not in {
        ProfileStatus.DEGRADED,
        ProfileStatus.EXPIRED,
        ProfileStatus.INCOMPATIBLE,
        ProfileStatus.SUPERSEDED,
        ProfileStatus.INVALID,
    }
