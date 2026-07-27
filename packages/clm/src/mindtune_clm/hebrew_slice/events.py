"""Typed CLM-06 Hebrew slice events with explicit causal links."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from mindtune_clm.hebrew_slice.models import HebrewAdaptiveEvent


class HebrewSliceEventType:
    """Canonical event type strings for the Hebrew slice."""

    HEBREW_SESSION_STARTED = "hebrew_session_started"
    HEBREW_TRIAL_PREPARED = "hebrew_trial_prepared"
    HEBREW_TRIAL_PRESENTED = "hebrew_trial_presented"
    HEBREW_AUDIO_ASSET_RESOLVED = "hebrew_audio_asset_resolved"
    HEBREW_RESPONSE_SUBMITTED = "hebrew_response_submitted"
    HEBREW_RESPONSE_SCORED = "hebrew_response_scored"
    HEBREW_ERROR_CLASSIFIED = "hebrew_error_classified"
    HEBREW_LEARNING_STATE_UPDATED = "hebrew_learning_state_updated"
    HEBREW_PEDAGOGICAL_ADAPTATION_DECIDED = "hebrew_pedagogical_adaptation_decided"
    HEBREW_TRIAL_REPEATED = "hebrew_trial_repeated"
    HEBREW_ITEM_INTERLEAVED = "hebrew_item_interleaved"
    HEBREW_ITEM_DEFERRED = "hebrew_item_deferred"
    HEBREW_ASSISTANCE_CHANGED = "hebrew_assistance_changed"
    HEBREW_TRIAL_COMPLETED = "hebrew_trial_completed"
    HEBREW_SESSION_COMPLETED = "hebrew_session_completed"
    HEBREW_SESSION_ABORTED = "hebrew_session_aborted"


@dataclass
class HebrewEventLog:
    """Append-only event log for a Hebrew adaptive session."""

    session_id: str
    events: list[HebrewAdaptiveEvent] = field(default_factory=list)
    _counter: int = 0

    def emit(
        self,
        event_type: str,
        payload: dict[str, Any],
        component: str = "hebrew_slice",
        provenance: list[str] | None = None,
        timestamp: float | None = None,
    ) -> HebrewAdaptiveEvent:
        self._counter += 1
        event = HebrewAdaptiveEvent(
            event_id=f"heb-{self.session_id}-{self._counter}-{uuid.uuid4().hex[:8]}",
            event_type=event_type,
            session_id=self.session_id,
            timestamp=timestamp if timestamp is not None else time.time(),
            component=component,
            payload=payload,
            provenance=list(provenance or []),
        )
        self.events.append(event)
        return event

    def causal_graph(self) -> dict[str, Any]:
        """Return a reconstructable graph of event ids and provenance."""
        return {
            "session_id": self.session_id,
            "event_count": len(self.events),
            "event_ids": [e.event_id for e in self.events],
            "edges": [
                {"from": p, "to": e.event_id}
                for e in self.events
                for p in e.provenance
            ],
        }
