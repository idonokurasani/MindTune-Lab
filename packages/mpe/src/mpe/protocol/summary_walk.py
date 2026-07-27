"""Shared event traversal used to derive protocol summaries.

The traversal correlates `trial_created`, `observation_received`,
`evaluation_completed`, and `feedback_completed` events per content item.
Interpretation of the correlated values (what an observation payload means,
what counts as an outcome) stays in the protocol-specific summary modules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from mpe.errors import ValidationError
from mpe.events import CURRENT_EVENT_SCHEMA_VERSION, Event
from mpe.integrity import is_chained_schema
from mpe.protocol.trial_pipeline import canonical_trial_fields
from mpe.provenance import ProvenanceReference


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
    provenance: ProvenanceReference
    items: list[TrialItemRecord] = field(default_factory=list)


def first_content_item_id(payload: dict[str, Any]) -> str | None:
    """Return the first content item id carried by a trial payload."""
    content_item_ids = payload.get("content_item_ids")
    if isinstance(content_item_ids, list) and content_item_ids:
        first = content_item_ids[0]
        if isinstance(first, str):
            return first
    return None


def _content_item_id_for_trial(trial_id: Any, events: list[Event]) -> str | None:
    if trial_id is None:
        return None
    trial_id_str = str(trial_id)
    for event in events:
        if event.event_type == "trial_created" and event.payload.get("trial_id") == trial_id_str:
            return first_content_item_id(event.payload)
    return None


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _stream_schema_version(events: list[Event]) -> str:
    return events[0].schema_version if events else CURRENT_EVENT_SCHEMA_VERSION


def _recorded_provenance(events: list[Event]) -> ProvenanceReference:
    """Bind the walk to `session_provenance_recorded`, or refuse to produce one."""
    schema_version = _stream_schema_version(events)
    if not is_chained_schema(schema_version):
        raise ValidationError(
            f"Schema-{schema_version} stream cannot be analysed through the normal "
            "API; use walk_session_legacy"
        )
    for event in events:
        if event.event_type == "session_provenance_recorded":
            return ProvenanceReference.recorded(event.event_id, schema_version)
    raise ValidationError(
        "Schema-1.2 stream has no session_provenance_recorded event; no derived "
        "result can be produced from it"
    )


def walk_session(events: list[Event]) -> SessionWalk:
    """Correlate a schema-1.2 session, bound to its provenance event.

    Raises if the stream is schema 1.1 or carries no provenance event: a
    schema-1.2 derived result cannot exist without a provenance reference
    (ADR-0001 sec. 2.8.1).
    """
    return _walk(events, _recorded_provenance(events))


def walk_session_legacy(events: list[Event]) -> SessionWalk:
    """Correlate a historical schema-1.1 session, explicitly unprovenanced.

    The deliberately separate entry point for streams that predate provenance.
    Every result it produces declares `unavailable_legacy`; it refuses schema
    1.2, which must go through `walk_session`.
    """
    schema_version = _stream_schema_version(events)
    if is_chained_schema(schema_version):
        raise ValidationError(
            f"The legacy API does not accept schema-{schema_version} streams; use "
            "walk_session"
        )
    return _walk(events, ProvenanceReference.unavailable_legacy(schema_version))


def _walk(events: list[Event], provenance: ProvenanceReference) -> SessionWalk:  # noqa: C901
    """Correlate the canonical trial events of a session, in event order."""
    session_id = str(events[0].session_id) if events else "unknown"
    protocol_id: str | None = None
    fixture_id: str | None = None
    session_completed = False
    canonical = canonical_trial_fields()

    records: dict[str, TrialItemRecord] = {}
    order: list[str] = []

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
            item_id = _content_item_id_for_trial(event.trial_id, events)
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
            item_id = _content_item_id_for_trial(event.trial_id, events)
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
        provenance=provenance,
        items=[records[item_id] for item_id in order],
    )
