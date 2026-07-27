"""The supported stream interchange: JSONL export and import (ADR-0001 sec. 2.9).

Export reads through the normal verified path and emits one
`canonical_record_bytes(event)` object per line, ascending by sequence. Import
appends through the ordinary store API, so schema validation, ordering,
provenance existence, and chain continuity are all re-applied on ingest.

This is an internal reproducibility path — the one a rebuild-from-empty test is
allowed to use instead of touching SQLite tables. It is not a scientific archive
format and not BIDS.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Iterator
from typing import Any, cast

from mpe.enums import DataClassification
from mpe.errors import ValidationError
from mpe.events import Event
from mpe.integrity import canonical_record_bytes
from mpe.types import (
    BlockID,
    CorrelationID,
    EventID,
    ProtocolVersionID,
    SessionID,
    TrialID,
)


def export_stream(store: Any, session_id: SessionID) -> Iterator[bytes]:
    """Yield one canonical record per event, in ascending sequence order.

    Read-only, and it reads through `store.read`, so a stream that fails
    verification raises instead of being exported.
    """
    for event in store.read(session_id):
        yield canonical_record_bytes(event)


def write_stream(store: Any, session_id: SessionID, out: Any) -> int:
    """Write an exported stream as JSONL to a binary file object."""
    count = 0
    for record in export_stream(store, session_id):
        out.write(record)
        out.write(b"\n")
        count += 1
    return count


def event_from_record(record: dict[str, Any]) -> Event:
    """Rebuild an `Event` from one exported canonical record."""
    classification = record.get("data_classification")
    return Event(
        event_id=EventID(record["event_id"]),
        event_type=record["event_type"],
        schema_version=record["schema_version"],
        session_id=SessionID(record["session_id"]),
        session_sequence_number=record["session_sequence_number"],
        protocol_version_id=ProtocolVersionID(record["protocol_version_id"]),
        timestamp=record["timestamp"],
        wallclock_at=record.get("wallclock_at"),
        component=record["component"],
        component_version=record["component_version"],
        correlation_id=(
            CorrelationID(record["correlation_id"]) if record.get("correlation_id") else None
        ),
        provenance=[EventID(eid) for eid in record.get("provenance", [])],
        payload=record.get("payload", {}),
        sensitive=bool(record.get("sensitive", False)),
        data_classification=cast(
            "DataClassification | None",
            (
                DataClassification.validate(classification, required=False)
                if classification is not None
                else None
            ),
        ),
        trial_id=TrialID(record["trial_id"]) if record.get("trial_id") else None,
        block_id=BlockID(record["block_id"]) if record.get("block_id") else None,
        quality_flags=list(record.get("quality_flags", [])),
        content_digest=record.get("content_digest"),
        previous_digest=record.get("previous_digest"),
        writer_revision=record.get("writer_revision"),
    )


def import_stream(store: Any, lines: Iterable[bytes | str]) -> int:
    """Append an exported stream to `store` through the ordinary append API.

    Refuses to write into a session that already has events: import reconstructs
    a stream, it never merges into one.
    """
    events: list[Event] = []
    for number, line in enumerate(lines, start=1):
        text = line.decode("utf-8") if isinstance(line, bytes) else line
        if not text.strip():
            continue
        try:
            record = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValidationError(f"Malformed record on line {number}: {exc}") from exc
        events.append(event_from_record(record))

    if not events:
        raise ValidationError("Nothing to import: the stream is empty")

    sessions = {event.session_id for event in events}
    if len(sessions) > 1:
        raise ValidationError(f"An import covers exactly one session, got {len(sessions)}")

    session_id = events[0].session_id
    if store.get_last_sequence(session_id) != 0:
        raise ValidationError(
            f"Session {session_id} already exists in the target store; import "
            "requires an empty stream"
        )

    for event in events:
        store.append(event)
    return len(events)
