"""Shared event traversal used to derive protocol summaries.

The traversal correlates `trial_created`, `observation_received`,
`evaluation_completed`, and `feedback_completed` events per content item.
Interpretation of the correlated values (what an observation payload means,
what counts as an outcome) stays in the protocol-specific summary modules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from mpe.events import Event
from mpe.protocol.trial_pipeline import canonical_trial_fields


@dataclass
class TrialItemRecord:
    """Correlated event data for a single content item."""

    content_item_id: str
    repeat_count: int = 0
    observation_payload: Any = None
    latency: float | None = None
    answer_status: str | None = None
    completed: bool = False
    trial_extensions: dict[str, Any] = field(default_factory=dict)


@dataclass
class SessionWalk:
    """Session-level values plus per-item records, in event order."""

    session_id: str
    protocol_id: str | None
    fixture_id: str | None
    last_event_type: str | None
    session_completed: bool
    event_count: int
    items: list[TrialItemRecord] = field(default_factory=list)


def first_content_item_id(payload: dict[str, Any]) -> str | None:
    """Return the first content item id carried by a trial payload."""
    content_item_ids = payload.get("content_item_ids")
    if isinstance(content_item_ids, list) and content_item_ids:
        first = content_item_ids[0]
        if isinstance(first, str):
            return first
    return None


def _build_trial_to_item_index(events: list[Event]) -> dict[str, str | None]:
    """One-pass index from trial_id to the first content item id."""
    index: dict[str, str | None] = {}
    for event in events:
        if event.event_type == "trial_created":
            trial_id = str(event.payload.get("trial_id"))
            if trial_id and trial_id not in index:
                index[trial_id] = first_content_item_id(event.payload)
    return index


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def walk_session(events: list[Event]) -> SessionWalk:  # noqa: C901
    """Correlate the canonical trial events of a session, in event order."""
    session_id = str(events[0].session_id) if events else "unknown"
    protocol_id: str | None = None
    fixture_id: str | None = None
    session_completed = False
    canonical = canonical_trial_fields()

    records: dict[str, TrialItemRecord] = {}
    order: list[str] = []
    trial_to_item = _build_trial_to_item_index(events)

    for event in events:
        payload = dict(event.payload)
        event_type = event.event_type

        if event_type == "session_started":
            protocol_id = str(event.protocol_version_id)
            start_parameters = payload.get("start_parameters") or {}
            fixture_id = start_parameters.get("fixture_id")

        elif event_type == "session_completed":
            session_completed = True

        elif event_type == "trial_created":
            item_id = first_content_item_id(payload)
            if item_id:
                record = records.get(item_id)
                if record is None:
                    record = TrialItemRecord(content_item_id=item_id)
                    records[item_id] = record
                    order.append(item_id)
                record.repeat_count = int(payload.get("repeat_count", 0))
                record.trial_extensions = {
                    key: value for key, value in payload.items() if key not in canonical
                }

        elif event_type == "observation_received":
            item_id = trial_to_item.get(str(event.trial_id)) if event.trial_id is not None else None
            record = records.get(item_id) if item_id else None
            if record is not None:
                raw_payload = payload.get("payload")
                record.observation_payload = raw_payload
                latency = payload.get("latency")
                if latency is None and isinstance(raw_payload, dict):
                    latency = raw_payload.get("latency")
                parsed_latency = _float_or_none(latency)
                if parsed_latency is not None:
                    record.latency = parsed_latency

        elif event_type == "evaluation_completed":
            item_id = payload.get("expected_content_item_id")
            record = records.get(item_id) if item_id else None
            if record is not None:
                answer_status = payload.get("answer_status")
                record.answer_status = str(answer_status) if answer_status is not None else None

        elif event_type == "feedback_completed":
            item_id = trial_to_item.get(str(event.trial_id)) if event.trial_id is not None else None
            record = records.get(item_id) if item_id else None
            if record is not None:
                record.completed = True

    return SessionWalk(
        session_id=session_id,
        protocol_id=protocol_id,
        fixture_id=fixture_id,
        last_event_type=events[-1].event_type if events else None,
        session_completed=session_completed,
        event_count=len(events),
        items=[records[item_id] for item_id in order],
    )
