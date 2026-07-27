"""Readiness and health checks for calibration sessions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from mindtune_clm.calibration.models import (
    CalibrationReadiness,
    CalibrationSession,
    CalibrationSessionStatus,
)
from mindtune_clm.calibration.protocol import CalibrationProtocol


@dataclass
class CalibrationHealth:
    """Health and readiness state for a calibration session."""

    status: str = "unknown"
    ready: bool = False
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "ready": self.ready,
            "blockers": list(self.blockers),
            "warnings": list(self.warnings),
        }


class CalibrationReadinessEvaluator:
    """Evaluate readiness before a calibration session may start."""

    def __init__(self, protocol: CalibrationProtocol = CalibrationProtocol.default()) -> None:
        self.protocol = protocol

    def evaluate(  # noqa: C901
        self,
        session: CalibrationSession,
        sensor_quality_ok: bool = True,
        task_assets_cached: bool = True,
        event_store_writable: bool = True,
        playback_backend_ready: bool = True,
        safety_controller_ready: bool = True,
        incompatible_sensor_owner: str | None = None,
    ) -> CalibrationReadiness:
        blockers: list[str] = []
        warnings: list[str] = []

        if not session.participant_id:
            blockers.append("missing_participant_pseudonym")
        if session.protocol is None:
            blockers.append("invalid_protocol")
        if not session.sensor_family:
            warnings.append("sensor_family_defaulted")
        if not session.sensor_config_fingerprint:
            blockers.append("missing_sensor_configuration")
        if not sensor_quality_ok:
            blockers.append("sensor_quality_unacceptable")
        if not task_assets_cached:
            blockers.append("missing_task_assets")
        if not event_store_writable:
            blockers.append("event_store_not_writable")
        if incompatible_sensor_owner is not None:
            blockers.append("incompatible_active_sensor_owner")
        if not playback_backend_ready:
            warnings.append("playback_backend_not_ready")
        if not safety_controller_ready:
            blockers.append("safety_controller_not_ready")
        if not session.feature_schema_version:
            blockers.append("unknown_feature_schema_version")

        ready = len(blockers) == 0
        session.readiness = CalibrationReadiness(
            ready=ready,
            blocking_reasons=blockers,
            warnings=warnings,
        )
        session.status = (
            CalibrationSessionStatus.READINESS_CHECKED
            if ready
            else CalibrationSessionStatus.CREATED
        )
        return session.readiness
