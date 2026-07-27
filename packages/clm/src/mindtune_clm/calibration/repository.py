"""In-memory profile repository for CLM-07."""

from __future__ import annotations

import threading
from typing import Any

from mindtune_clm.calibration.models import CalibrationProfile, ProfileStatus
from mindtune_clm.calibration.protocol import CalibrationProtocol


class InMemoryCalibrationProfileRepository:
    """Store and retrieve immutable CalibrationProfile versions."""

    def __init__(self) -> None:
        self._profiles: dict[str, CalibrationProfile] = {}
        self._versions: dict[str, list[str]] = {}  # participant_id -> ordered profile_ids
        self._lock = threading.RLock()

    def add(self, profile: CalibrationProfile) -> None:
        with self._lock:
            self._profiles[profile.profile_id] = profile
            self._versions.setdefault(profile.participant_id, []).append(profile.profile_id)

    def get(self, profile_id: str) -> CalibrationProfile | None:
        with self._lock:
            return self._profiles.get(profile_id)

    def list_for_participant(self, participant_id: str) -> list[CalibrationProfile]:
        with self._lock:
            return [
                self._profiles[pid]
                for pid in self._versions.get(participant_id, [])
                if pid in self._profiles
            ]

    def list_all(self) -> list[CalibrationProfile]:
        with self._lock:
            return list(self._profiles.values())

    def invalidate(self, profile_id: str, reason: str) -> CalibrationProfile | None:
        with self._lock:
            profile = self._profiles.get(profile_id)
            if profile is None or not profile.is_valid():
                return profile
            from dataclasses import replace
            new_profile = replace(
                profile,
                validity_status=ProfileStatus.INVALID,
                invalidation_reasons=list(profile.invalidation_reasons) + [reason],
            )
            self._profiles[profile_id] = new_profile
            return new_profile

    def expire(self, profile_id: str) -> CalibrationProfile | None:
        with self._lock:
            profile = self._profiles.get(profile_id)
            if profile is None:
                return None
            if profile.validity_status in {ProfileStatus.INVALID, ProfileStatus.EXPIRED, ProfileStatus.SUPERSEDED}:
                return profile
            from dataclasses import replace
            new_profile = replace(profile, validity_status=ProfileStatus.EXPIRED)
            self._profiles[profile_id] = new_profile
            return new_profile

    def supersede(self, old_profile_id: str, new_profile_id: str) -> CalibrationProfile | None:
        with self._lock:
            profile = self._profiles.get(old_profile_id)
            if profile is None:
                return None
            from dataclasses import replace
            new_profile = replace(
                profile,
                validity_status=ProfileStatus.SUPERSEDED,
                superseded_profile_id=new_profile_id,
            )
            self._profiles[old_profile_id] = new_profile
            return new_profile

    def latest_compatible(
        self,
        participant_id: str,
        sensor_family: str,
        sensor_config_fingerprint: str,
        parser_version: str,
        feature_schema_version: str,
    ) -> CalibrationProfile | None:
        from mindtune_clm.calibration.profiles import ProfileSelector
        selector = ProfileSelector(CalibrationProtocol.default())
        profiles = self.list_for_participant(participant_id)
        result = selector.select(
            profiles,
            participant_id,
            sensor_family,
            sensor_config_fingerprint,
            parser_version,
            feature_schema_version,
        )
        return self.get(result.profile_id) if result.profile_id else None

    def as_dict(self) -> dict[str, Any]:
        with self._lock:
            return {
                "profile_count": len(self._profiles),
                "participants": list(self._versions.keys()),
            }
