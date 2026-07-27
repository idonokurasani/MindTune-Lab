"""Event-derived summary for the Recognition protocol."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from mpe.enums import AnswerStatus, SessionStatus
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
class RecognitionItemSummary:
    """Summary for a single Recognition item."""

    content_item_id: str
    selected_choice_index: int | None
    correct_choice_index: int | None
    correct: bool | None
    latency: float | None
    repeats_used: int
    outcome: str
    completed: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "content_item_id": self.content_item_id,
            "selected_choice_index": self.selected_choice_index,
            "correct_choice_index": self.correct_choice_index,
            "correct": self.correct,
            "latency": self.latency,
            "repeats_used": self.repeats_used,
            "outcome": self.outcome,
            "completed": self.completed,
        }


@dataclass(frozen=True)
class RecognitionSummary:
    """Full event-derived Recognition session summary."""

    session_id: str
    protocol_id: str
    fixture_id: str
    status: str
    item_count: int
    completed_item_count: int
    correct_count: int
    total_repeats: int
    event_count: int
    latency_bound: float
    provenance: ProvenanceReference | None = None
    items: list[RecognitionItemSummary] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "protocol_id": self.protocol_id,
            "fixture_id": self.fixture_id,
            "status": self.status,
            "item_count": self.item_count,
            "completed_item_count": self.completed_item_count,
            "correct_count": self.correct_count,
            "total_repeats": self.total_repeats,
            "event_count": self.event_count,
            "latency_bound": self.latency_bound,
            "items": [item.as_dict() for item in self.items],
            **(self.provenance.as_dict() if self.provenance else {}),
        }


def _int_or_none(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except (TypeError, ValueError):
            return None
    return None


def _correct_from(record: TrialItemRecord) -> bool | None:
    if record.answer_status == AnswerStatus.CORRECT.value:
        return True
    if record.answer_status == AnswerStatus.INCORRECT.value:
        return False
    return None


def derive_recognition_summary(
    events: list[Event],
    repeat_cap: int = 1,
    latency_bound: float = 2.0,
) -> RecognitionSummary:
    """Derive a Recognition summary from a schema-1.2 event stream.

    The summary is built solely from the persisted event stream: no fixture
    is consulted and no runtime state is reconstructed. The result is bound to
    the session's provenance event and cannot be produced without one.
    """
    return _derive(events, walk_session(events), repeat_cap, latency_bound)


def derive_recognition_summary_legacy(
    events: list[Event],
    repeat_cap: int = 1,
    latency_bound: float = 2.0,
) -> RecognitionSummary:
    """Legacy API for historical schema-1.1 streams (`unavailable_legacy`)."""
    return _derive(events, walk_session_legacy(events), repeat_cap, latency_bound)


def _derive(
    events: list[Event],
    walk: SessionWalk,
    repeat_cap: int,
    latency_bound: float,
) -> RecognitionSummary:

    item_summaries: list[RecognitionItemSummary] = []
    total_repeats = 0
    completed_count = 0
    correct_count = 0

    for record in walk.items:
        selected_choice_index = _int_or_none(record.observation_payload)
        correct_choice_index = _int_or_none(record.trial_extensions.get("correct_choice_index"))
        repeats_used = record.repeat_count
        correct = _correct_from(record)

        total_repeats += repeats_used
        if record.completed:
            completed_count += 1
        if correct is True:
            correct_count += 1

        if correct is True:
            outcome = "correct"
        elif correct is False:
            outcome = "incorrect"
        elif record.completed:
            outcome = "completed"
        else:
            outcome = "incomplete"

        item_summaries.append(
            RecognitionItemSummary(
                content_item_id=record.content_item_id,
                selected_choice_index=selected_choice_index,
                correct_choice_index=correct_choice_index,
                correct=correct,
                latency=record.latency,
                repeats_used=repeats_used,
                outcome=outcome,
                completed=record.completed,
            )
        )

    if walk.session_completed:
        status = SessionStatus.COMPLETED.value
    else:
        status = walk.last_event_type or SessionStatus.CREATED.value

    return RecognitionSummary(
        session_id=walk.session_id,
        protocol_id=walk.protocol_id or "recognition",
        fixture_id=walk.fixture_id or "unknown",
        status=status,
        item_count=len(item_summaries),
        completed_item_count=completed_count,
        correct_count=correct_count,
        total_repeats=total_repeats,
        event_count=len(events),
        latency_bound=latency_bound,
        items=item_summaries,
        provenance=walk.provenance,
    )


def summarize_session(
    session_id: SessionID,
    store: Any,
    repeat_cap: int = 1,
    latency_bound: float = 2.0,
) -> RecognitionSummary:
    """Load a session's events from a store and derive its Recognition summary."""
    events = store.read(session_id)
    return derive_recognition_summary(events, repeat_cap=repeat_cap, latency_bound=latency_bound)


def summarize_session_legacy(
    session_id: SessionID,
    store: Any,
    repeat_cap: int = 1,
    latency_bound: float = 2.0,
) -> RecognitionSummary:
    """Legacy entry point for historical schema-1.1 sessions."""
    events = store.read(session_id)
    return derive_recognition_summary_legacy(
        events, repeat_cap=repeat_cap, latency_bound=latency_bound
    )
