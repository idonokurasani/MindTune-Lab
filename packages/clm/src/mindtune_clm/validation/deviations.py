"""Typed protocol-deviation capture for CLM-08."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class DeviationSeverity(str, Enum):
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"


class DeviationCategory(str, Enum):
    WRONG_CONDITION = "wrong_condition"
    WRONG_PROTOCOL_VERSION = "wrong_protocol_version"
    MISSING_REQUIRED_CALIBRATION = "missing_required_calibration"
    SENSOR_UNAVAILABLE = "sensor_unavailable"
    EXCESSIVE_MISSING_DATA = "excessive_missing_data"
    PLAYBACK_FAILURE = "playback_failure"
    WRONG_VOICE_ASSET = "wrong_voice_asset"
    UNAPPROVED_LINGUISTIC_ITEM = "unapproved_linguistic_item"
    INCORRECT_CURRICULUM_VERSION = "incorrect_curriculum_version"
    SESSION_INTERRUPTED = "session_interrupted"
    SAFETY_KILL = "safety_kill"
    MANUAL_RESEARCHER_OVERRIDE = "manual_researcher_override"
    RANDOMIZATION_FAILURE = "randomization_failure"
    DATA_EXPORT_CORRUPTION = "data_export_corruption"
    ANALYSIS_PLAN_DEVIATION = "analysis_plan_deviation"


@dataclass(frozen=True)
class ProtocolDeviation:
    """A prespecified, auditable protocol deviation."""

    deviation_id: str
    session_id: str
    participant_pseudonym: str
    study_id: str
    study_version: int
    category: str
    severity: str
    detection_time: float
    description: str
    prespecified_consequence: str
    inclusion_impact: str
    event_references: list[str] = field(default_factory=list)
    reviewer_status: str = "pending"

    @classmethod
    def create(
        cls,
        session_id: str,
        participant_pseudonym: str,
        study_id: str,
        study_version: int,
        category: str,
        severity: str,
        description: str,
        prespecified_consequence: str,
        inclusion_impact: str,
        event_references: list[str] | None = None,
    ) -> "ProtocolDeviation":
        return cls(
            deviation_id=str(uuid.uuid4()),
            session_id=session_id,
            participant_pseudonym=participant_pseudonym,
            study_id=study_id,
            study_version=study_version,
            category=category,
            severity=severity,
            detection_time=time.time(),
            description=description,
            prespecified_consequence=prespecified_consequence,
            inclusion_impact=inclusion_impact,
            event_references=list(event_references or []),
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "deviation_id": self.deviation_id,
            "session_id": self.session_id,
            "participant_pseudonym": self.participant_pseudonym,
            "study_id": self.study_id,
            "study_version": self.study_version,
            "category": self.category,
            "severity": self.severity,
            "detection_time": self.detection_time,
            "description": self.description,
            "prespecified_consequence": self.prespecified_consequence,
            "inclusion_impact": self.inclusion_impact,
            "event_references": list(self.event_references),
            "reviewer_status": self.reviewer_status,
        }

