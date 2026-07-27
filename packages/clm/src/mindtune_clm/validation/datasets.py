"""Deterministic analysis datasets for CLM-08."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

from mindtune_clm.validation.deviations import ProtocolDeviation
from mindtune_clm.validation.quality import QualityReport, evaluate_dataset_quality


def _stable_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def _checksum(rows: list[dict[str, Any]]) -> str:
    body = _stable_json(rows).encode("utf-8")
    return hashlib.sha256(body).hexdigest()


@dataclass(frozen=True)
class AnalysisRow:
    """One analysis-dataset row with full traceability."""

    study_id: str
    study_version: int
    participant_id: str
    session_id: str
    period: int
    sequence_order: int
    condition: str
    protocol_version: str
    curriculum_version: str
    calibration_profile: str
    trial_id: str
    item_id: str
    response: str
    correct: bool
    response_time_ms: float
    confidence: float | None
    error_types: list[str] = field(default_factory=list)
    clm_state: dict[str, Any] = field(default_factory=dict)
    intervention_exposure: float = 0.0
    audio_artifact: str | None = None
    safety_events: list[str] = field(default_factory=list)
    sensor_quality_summary: dict[str, Any] = field(default_factory=dict)
    inclusion_flags: dict[str, bool] = field(default_factory=dict)
    deviation_flags: list[str] = field(default_factory=list)
    playback_receipt: bool = True
    event_chain_corrupted: bool = False
    timestamp: float = 0.0

    def as_dict(self) -> dict[str, Any]:
        return {
            "study_id": self.study_id,
            "study_version": self.study_version,
            "participant_id": self.participant_id,
            "session_id": self.session_id,
            "period": self.period,
            "sequence_order": self.sequence_order,
            "condition": self.condition,
            "protocol_version": self.protocol_version,
            "curriculum_version": self.curriculum_version,
            "calibration_profile": self.calibration_profile,
            "trial_id": self.trial_id,
            "item_id": self.item_id,
            "response": self.response,
            "correct": self.correct,
            "response_time_ms": self.response_time_ms,
            "confidence": self.confidence,
            "error_types": list(self.error_types),
            "clm_state": dict(self.clm_state),
            "intervention_exposure": self.intervention_exposure,
            "audio_artifact": self.audio_artifact,
            "safety_events": list(self.safety_events),
            "sensor_quality_summary": dict(self.sensor_quality_summary),
            "inclusion_flags": dict(self.inclusion_flags),
            "deviation_flags": list(self.deviation_flags),
            "playback_receipt": self.playback_receipt,
            "event_chain_corrupted": self.event_chain_corrupted,
            "timestamp": self.timestamp,
        }


@dataclass(frozen=True)
class AnalysisDataset:
    """A deterministic analysis dataset with quality and checksum."""

    rows: list[AnalysisRow]
    checksum: str
    quality: QualityReport
    population: str = "intention-to-treat"
    study_id: str | None = None
    study_version: int | None = None

    @classmethod
    def build(
        cls,
        rows: list[AnalysisRow],
        population: str = "intention-to-treat",
        study_id: str | None = None,
        study_version: int | None = None,
    ) -> "AnalysisDataset":
        dict_rows = [r.as_dict() for r in rows]
        return cls(
            rows=list(rows),
            checksum=_checksum(dict_rows),
            quality=evaluate_dataset_quality(dict_rows),
            population=population,
            study_id=study_id,
            study_version=study_version,
        )

    def as_dicts(self) -> list[dict[str, Any]]:
        return [r.as_dict() for r in self.rows]

    def filter(self, predicate: Any) -> "AnalysisDataset":
        kept = [r for r in self.rows if predicate(r)]
        return AnalysisDataset.build(kept, population=self.population, study_id=self.study_id, study_version=self.study_version)

    def build_intention_to_treat(self) -> "AnalysisDataset":
        return AnalysisDataset.build(
            [r for r in self.rows if r.inclusion_flags.get("assigned", True)],
            population="intention-to-treat",
            study_id=self.study_id,
            study_version=self.study_version,
        )

    def build_per_protocol(self) -> "AnalysisDataset":
        return AnalysisDataset.build(
            [r for r in self.rows if not r.deviation_flags and r.inclusion_flags.get("protocol_adherent", True)],
            population="per-protocol",
            study_id=self.study_id,
            study_version=self.study_version,
        )

    def build_complete_case(self) -> "AnalysisDataset":
        return AnalysisDataset.build(
            [r for r in self.rows if r.correct is not None and r.response_time_ms is not None],
            population="complete-case",
            study_id=self.study_id,
            study_version=self.study_version,
        )


def apply_deviation_flags(
    rows: list[AnalysisRow], deviations: list[ProtocolDeviation]
) -> list[AnalysisRow]:
    """Tag rows with deviations by session/participant."""
    dev_by_session: dict[str, list[ProtocolDeviation]] = {}
    for d in deviations:
        dev_by_session.setdefault(d.session_id, []).append(d)
    updated: list[AnalysisRow] = []
    for row in rows:
        flags = list(row.deviation_flags)
        for d in dev_by_session.get(row.session_id, []):
            flags.append(d.category)
        updated.append(
            AnalysisRow(
                study_id=row.study_id,
                study_version=row.study_version,
                participant_id=row.participant_id,
                session_id=row.session_id,
                period=row.period,
                sequence_order=row.sequence_order,
                condition=row.condition,
                protocol_version=row.protocol_version,
                curriculum_version=row.curriculum_version,
                calibration_profile=row.calibration_profile,
                trial_id=row.trial_id,
                item_id=row.item_id,
                response=row.response,
                correct=row.correct,
                response_time_ms=row.response_time_ms,
                confidence=row.confidence,
                error_types=list(row.error_types),
                clm_state=dict(row.clm_state),
                intervention_exposure=row.intervention_exposure,
                audio_artifact=row.audio_artifact,
                safety_events=list(row.safety_events),
                sensor_quality_summary=dict(row.sensor_quality_summary),
                inclusion_flags=dict(row.inclusion_flags),
                deviation_flags=flags,
                timestamp=row.timestamp,
            )
        )
    return updated
