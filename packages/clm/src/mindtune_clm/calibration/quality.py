"""Quality filtering and rejection reason codes for calibration observations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from mindtune_clm.calibration.models import ProfileStatus, RawObservation

if TYPE_CHECKING:
    from mindtune_clm.calibration.protocol import CalibrationProtocol

REJECTION_REASONS = frozenset(
    {
        "artifact",
        "movement",
        "packet_loss",
        "stale_window",
        "disconnected_interval",
        "malformed_record",
        "missing_behavioral_response",
        "poor_signal",
        "impossible_value",
        "sensor_disconnected",
    }
)


@dataclass
class ObservationQuality:
    """Quality evaluation for a single raw observation."""

    accepted: bool = False
    reason_codes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {"accepted": self.accepted, "reason_codes": list(self.reason_codes)}


class ObservationQualityGate:
    """Determine whether a raw observation is accepted for baseline estimation."""

    def __init__(self, allowed_modalities: set[str] | None = None) -> None:
        self.allowed_modalities = allowed_modalities or {
            "eeg",
            "behavioral",
            "respiration",
            "voice",
            "vendor",
            "audio",
            "movement",
        }

    def evaluate(self, observation: RawObservation) -> ObservationQuality:
        """Return quality evaluation and reason codes for an observation."""
        reasons: list[str] = []

        if observation.quality_status != "accepted":
            reasons.append(f"quality_status:{observation.quality_status}")

        for code in observation.reason_codes:
            if code in REJECTION_REASONS:
                reasons.append(f"rejection:{code}")

        if observation.modality not in self.allowed_modalities:
            reasons.append("modality_not_allowed")

        if observation.value is None:
            reasons.append("missing_value")

        if observation.sensor_config_fingerprint == "incompatible":
            reasons.append("incompatible_sensor_config")

        if observation.feature_name == "eeg_amplitude" and observation.sensor_family != "fc11":
            # Raw EEG amplitude is not calibrated across incompatible devices.
            reasons.append("incompatible_eeg_acquisition")

        if not reasons:
            return ObservationQuality(accepted=True, reason_codes=["quality_accepted"])

        return ObservationQuality(accepted=False, reason_codes=reasons)

    def summarize(self, observations: list[RawObservation]) -> dict[str, Any]:
        """Return counts by quality outcome."""
        accepted = 0
        rejected = 0
        reason_counts: dict[str, int] = {}
        for obs in observations:
            result = self.evaluate(obs)
            if result.accepted:
                accepted += 1
            else:
                rejected += 1
            for code in result.reason_codes:
                reason_counts[code] = reason_counts.get(code, 0) + 1
        return {
            "accepted": accepted,
            "rejected": rejected,
            "reason_counts": reason_counts,
        }


def is_profile_quality_valid(profile_status: ProfileStatus, quality: dict[str, Any], protocol: "CalibrationProtocol") -> bool:
    """Return True when quality summary meets protocol thresholds."""
    total = quality["accepted_count"] + quality["rejected_count"] + quality["missing_count"]
    if total == 0:
        return False
    if quality["accepted_count"] < protocol.min_accepted_observations:
        return False
    if total > 0 and quality["rejected_count"] / total > protocol.max_artifact_rate:
        return False
    return True
