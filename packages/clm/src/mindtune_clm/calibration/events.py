"""Typed calibration events and MPE integration helpers."""

from __future__ import annotations

import time
from typing import Any

from mpe.events import Event
from mpe.types import EventID, SessionID, make_id


class CalibrationEventType:
    """Calibration event type constants for MPE registration."""

    CALIBRATION_SESSION_CREATED = "calibration_session_created"
    CALIBRATION_READINESS_EVALUATED = "calibration_readiness_evaluated"
    CALIBRATION_COLLECTION_STARTED = "calibration_collection_started"
    CALIBRATION_OBSERVATION_ACCEPTED = "calibration_observation_accepted"
    CALIBRATION_OBSERVATION_REJECTED = "calibration_observation_rejected"
    CALIBRATION_BLOCK_COMPLETED = "calibration_block_completed"
    CALIBRATION_STABILITY_EVALUATED = "calibration_stability_evaluated"
    CALIBRATION_PROFILE_CREATED = "calibration_profile_created"
    CALIBRATION_PROFILE_VALIDATED = "calibration_profile_validated"
    CALIBRATION_PROFILE_INVALIDATED = "calibration_profile_invalidated"
    CALIBRATION_PROFILE_SUPERSEDED = "calibration_profile_superseded"
    CALIBRATION_PROFILE_SELECTED = "calibration_profile_selected"
    CALIBRATION_PROFILE_REJECTED_AS_INCOMPATIBLE = "calibration_profile_rejected_as_incompatible"
    CALIBRATED_OBSERVATION_CREATED = "calibrated_observation_created"
    CALIBRATION_DRIFT_DETECTED = "calibration_drift_detected"
    CALIBRATION_RECALIBRATION_RECOMMENDED = "calibration_recalibration_recommended"
    CALIBRATION_SESSION_ABORTED = "calibration_session_aborted"

    @classmethod
    def all(cls) -> frozenset[str]:
        return frozenset(
            {
                cls.CALIBRATION_SESSION_CREATED,
                cls.CALIBRATION_READINESS_EVALUATED,
                cls.CALIBRATION_COLLECTION_STARTED,
                cls.CALIBRATION_OBSERVATION_ACCEPTED,
                cls.CALIBRATION_OBSERVATION_REJECTED,
                cls.CALIBRATION_BLOCK_COMPLETED,
                cls.CALIBRATION_STABILITY_EVALUATED,
                cls.CALIBRATION_PROFILE_CREATED,
                cls.CALIBRATION_PROFILE_VALIDATED,
                cls.CALIBRATION_PROFILE_INVALIDATED,
                cls.CALIBRATION_PROFILE_SUPERSEDED,
                cls.CALIBRATION_PROFILE_SELECTED,
                cls.CALIBRATION_PROFILE_REJECTED_AS_INCOMPATIBLE,
                cls.CALIBRATED_OBSERVATION_CREATED,
                cls.CALIBRATION_DRIFT_DETECTED,
                cls.CALIBRATION_RECALIBRATION_RECOMMENDED,
                cls.CALIBRATION_SESSION_ABORTED,
            }
        )


def make_calibration_event(
    event_type: str,
    session_id: str,
    payload: dict[str, Any],
    provenance: list[str] | None = None,
    sequence: int = 1,
) -> Event:
    """Build an MPE Event for a calibration event."""
    return Event(
        event_id=make_id(EventID),
        event_type=event_type,
        schema_version="1.1",
        session_id=SessionID(session_id),
        session_sequence_number=sequence,
        protocol_version_id="clm07.personal-baseline.v1",
        timestamp=time.time(),
        component="calibration",
        component_version="clm07.v1",
        provenance=list(provenance or []),
        payload=payload,
    )
