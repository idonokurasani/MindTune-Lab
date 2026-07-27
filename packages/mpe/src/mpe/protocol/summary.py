"""Protocol summary derived exclusively from persisted Immediate Recall events."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from mpe.events import Event
from mpe.protocol.summary_walk import (
    SessionWalk,
    TrialItemRecord,
    walk_session,
    walk_session_legacy,
)
from mpe.provenance import ProvenanceReference
from mpe.types import SessionID


@dataclass(frozen=True)
class ItemSummary:
    """Per-item summary derived from the event stream."""

    content_item_id: str
    self_confirmation: str | None
    latency: float | None
    repeats_used: int
    outcome: str
    completed: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "content_item_id": self.content_item_id,
            "self_confirmation": self.self_confirmation,
            "latency": self.latency,
            "repeats_used": self.repeats_used,
            "outcome": self.outcome,
            "completed": self.completed,
        }


@dataclass(frozen=True)
class ProtocolSummary:
    """Summary of an Immediate Recall session derived from events."""

    session_id: str
    protocol_id: str | None
    fixture_id: str | None
    status: str | None
    event_count: int
    item_count: int
    completed_item_count: int
    unresolved_count: int
    total_repeats: int
    provenance: ProvenanceReference | None = None
    items: list[ItemSummary] = field(default_factory=list)
    latency_bound: float | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "protocol_id": self.protocol_id,
            "fixture_id": self.fixture_id,
            "status": self.status,
            "event_count": self.event_count,
            "item_count": self.item_count,
            "completed_item_count": self.completed_item_count,
            "unresolved_count": self.unresolved_count,
            "total_repeats": self.total_repeats,
            "items": [item.as_dict() for item in self.items],
            "latency_bound": self.latency_bound,
            **(self.provenance.as_dict() if self.provenance else {}),
        }


def _outcome_from(self_confirmation: str | None, repeats_used: int, cap: int) -> str:
    """Map a self-confirmation and repeat usage to a terminal outcome."""
    if self_confirmation is None:
        return "incomplete"
    if self_confirmation == "positive":
        return "positive"
    if self_confirmation == "negative":
        if repeats_used >= cap:
            return "unresolved"
        return "negative"
    return "unknown"


def _self_confirmation_from(record: TrialItemRecord) -> str | None:
    """Project the Immediate Recall self-confirmation from correlated events."""
    raw_payload = record.observation_payload
    if isinstance(raw_payload, str):
        return raw_payload
    if record.answer_status == "correct":
        return "positive"
    if record.answer_status == "incorrect":
        return "negative"
    return None


def derive_protocol_summary(
    events: list[Event],
    latency_bound: float | None = None,
    repeat_cap: int = 1,
) -> ProtocolSummary:
    """Derive an Immediate Recall summary from a schema-1.2 event stream.

    The summary is computed entirely from events; no live state or side channel is
    consulted.  Deterministic event ordering is preserved by reading the stream
    in sequence order. The result is bound to the session's provenance event and
    cannot be produced without one.
    """
    if not events:
        raise ValueError("Cannot derive summary from empty event stream")
    return _derive(events, walk_session(events), latency_bound, repeat_cap)


def derive_protocol_summary_legacy(
    events: list[Event],
    latency_bound: float | None = None,
    repeat_cap: int = 1,
) -> ProtocolSummary:
    """Legacy API for historical schema-1.1 streams.

    Produces a result marked `provenance_status: "unavailable_legacy"`. Not
    reachable from the normal path, and refuses schema-1.2 streams.
    """
    if not events:
        raise ValueError("Cannot derive summary from empty event stream")
    return _derive(events, walk_session_legacy(events), latency_bound, repeat_cap)


def _derive(
    events: list[Event],
    walk: SessionWalk,
    latency_bound: float | None,
    repeat_cap: int,
) -> ProtocolSummary:

    items: list[ItemSummary] = []
    completed_count = 0
    unresolved_count = 0
    total_repeats = 0

    for record in walk.items:
        repeats_used = record.repeat_count
        self_confirmation = _self_confirmation_from(record)
        if record.completed:
            completed_count += 1
        outcome = _outcome_from(self_confirmation, repeats_used, repeat_cap)
        if outcome == "unresolved":
            unresolved_count += 1
        total_repeats += repeats_used
        items.append(
            ItemSummary(
                content_item_id=record.content_item_id,
                self_confirmation=self_confirmation,
                latency=record.latency,
                repeats_used=repeats_used,
                outcome=outcome,
                completed=record.completed,
            )
        )

    return ProtocolSummary(
        session_id=walk.session_id,
        protocol_id=walk.protocol_id,
        fixture_id=walk.fixture_id,
        status=walk.last_event_type,
        event_count=len(events),
        item_count=len(items),
        completed_item_count=completed_count,
        unresolved_count=unresolved_count,
        total_repeats=total_repeats,
        items=items,
        latency_bound=latency_bound,
        provenance=walk.provenance,
    )


def summarize_session(
    session_id: SessionID,
    store: Any,
    latency_bound: float | None = None,
) -> ProtocolSummary:
    """Read a session from an event store and derive its Immediate Recall summary."""
    events = store.read(session_id)
    return derive_protocol_summary(events, latency_bound=latency_bound)


def summarize_session_legacy(
    session_id: SessionID,
    store: Any,
    latency_bound: float | None = None,
) -> ProtocolSummary:
    """Legacy entry point for historical schema-1.1 sessions."""
    events = store.read(session_id)
    return derive_protocol_summary_legacy(events, latency_bound=latency_bound)
