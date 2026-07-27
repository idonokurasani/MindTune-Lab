"""CLM-08 validation event types and immutable log."""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any


class CLM08EventType:
    """Canonical event names for the scientific-validation lifecycle."""

    STUDY_DEFINITION_CREATED = "study_definition_created"
    STUDY_DEFINITION_VALIDATED = "study_definition_validated"
    STUDY_PREREGISTERED = "study_preregistered"
    CONDITION_RANDOMIZED = "condition_randomized"
    CONDITION_ASSIGNMENT_REVEALED = "condition_assignment_revealed"
    PROTOCOL_DEVIATION_RECORDED = "protocol_deviation_recorded"
    ANALYSIS_DATASET_BUILT = "analysis_dataset_built"
    ANALYSIS_QUALITY_EVALUATED = "analysis_quality_evaluated"
    ANALYSIS_RUN_STARTED = "analysis_run_started"
    ANALYSIS_RUN_COMPLETED = "analysis_run_completed"
    ANALYSIS_RUN_FAILED = "analysis_run_failed"
    SENSITIVITY_ANALYSIS_COMPLETED = "sensitivity_analysis_completed"
    STUDY_REPORT_GENERATED = "study_report_generated"
    STUDY_CLOSED = "study_closed"

    @classmethod
    def all(cls) -> frozenset[str]:
        return frozenset(
            {
                cls.STUDY_DEFINITION_CREATED,
                cls.STUDY_DEFINITION_VALIDATED,
                cls.STUDY_PREREGISTERED,
                cls.CONDITION_RANDOMIZED,
                cls.CONDITION_ASSIGNMENT_REVEALED,
                cls.PROTOCOL_DEVIATION_RECORDED,
                cls.ANALYSIS_DATASET_BUILT,
                cls.ANALYSIS_QUALITY_EVALUATED,
                cls.ANALYSIS_RUN_STARTED,
                cls.ANALYSIS_RUN_COMPLETED,
                cls.ANALYSIS_RUN_FAILED,
                cls.SENSITIVITY_ANALYSIS_COMPLETED,
                cls.STUDY_REPORT_GENERATED,
                cls.STUDY_CLOSED,
            }
        )


def _stable_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def _event_id(payload: dict[str, Any]) -> str:
    nonce = str(uuid.uuid4())
    h = hashlib.sha256((_stable_json(payload) + nonce).encode("utf-8")).hexdigest()
    return f"clm08-{h[:24]}"


@dataclass(frozen=True)
class ValidationEvent:
    """Immutable validation-domain event."""

    event_id: str
    event_type: str
    study_id: str | None
    study_version: int | None
    timestamp: float
    component: str
    component_version: str
    payload: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        event_type: str,
        component: str,
        component_version: str,
        study_id: str | None = None,
        study_version: int | None = None,
        payload: dict[str, Any] | None = None,
    ) -> "ValidationEvent":
        payload = payload or {}
        return cls(
            event_id=_event_id(payload),
            event_type=event_type,
            study_id=study_id,
            study_version=study_version,
            timestamp=time.time(),
            component=component,
            component_version=component_version,
            payload=payload,
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "study_id": self.study_id,
            "study_version": self.study_version,
            "timestamp": self.timestamp,
            "component": self.component,
            "component_version": self.component_version,
            "payload": dict(self.payload),
        }


class ValidationEventLog:
    """Append-only validation event log."""

    def __init__(self) -> None:
        self._events: list[ValidationEvent] = []

    def append(self, event: ValidationEvent) -> None:
        self._events.append(event)

    def for_study(self, study_id: str) -> list[ValidationEvent]:
        return [e for e in self._events if e.study_id == study_id]

    def all_events(self) -> list[ValidationEvent]:
        return list(self._events)
