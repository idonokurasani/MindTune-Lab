"""Canonical serialization between Event objects and SQLite rows."""

from __future__ import annotations

import json
import time
from typing import Any, cast

from mpe.enums import CanonicalEnum, DataClassification
from mpe.errors import ReplayError
from mpe.events import Event
from mpe.types import (
    BlockID,
    CorrelationID,
    EventID,
    Identifier,
    ProtocolVersionID,
    SessionID,
    TrialID,
)

_JSON_SEPARATORS = (",", ":")


def _json_default(obj: Any) -> Any:
    """Fallback JSON encoder for Identifier and CanonicalEnum values."""
    if isinstance(obj, Identifier):
        return obj.value
    if isinstance(obj, CanonicalEnum):
        return obj.value
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def _to_json(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=_JSON_SEPARATORS,
        ensure_ascii=False,
        default=_json_default,
    )


def _identifier_or_none(cls: type[Identifier], value: str | None) -> Identifier | None:
    return cls(value) if value is not None else None


def to_row(event: Event) -> dict[str, Any]:
    """Convert an Event into a dict suitable for SQLite insertion."""
    return {
        "event_id": str(event.event_id),
        "session_id": str(event.session_id),
        "session_sequence_number": event.session_sequence_number,
        "event_type": event.event_type,
        "schema_version": event.schema_version,
        "protocol_version_id": str(event.protocol_version_id),
        "timestamp": event.timestamp,
        "wallclock_at": event.wallclock_at,
        "component": event.component,
        "component_version": event.component_version,
        "correlation_id": str(event.correlation_id) if event.correlation_id else None,
        "provenance": _to_json([str(e) for e in event.provenance]),
        "payload": _to_json(dict(event.payload)),
        "sensitive": 1 if event.sensitive else 0,
        "data_classification": (
            event.data_classification.value if event.data_classification else None
        ),
        "trial_id": str(event.trial_id) if event.trial_id else None,
        "block_id": str(event.block_id) if event.block_id else None,
        "quality_flags": _to_json(list(event.quality_flags)),
        "inserted_at": time.time(),
    }


def from_row(row: Any) -> Event:
    """Reconstruct an Event from a SQLite row (sqlite3.Row or mapping)."""
    try:
        provenance_raw = json.loads(row["provenance"])
        payload_raw = json.loads(row["payload"])
        quality_flags_raw = json.loads(row["quality_flags"])
    except json.JSONDecodeError as exc:
        raise ReplayError(f"Corrupt JSON in stored event row: {exc}") from exc

    data_classification_value = row["data_classification"]
    data_classification = cast(
        DataClassification | None,
        (
            DataClassification.validate(data_classification_value, required=False)
            if data_classification_value is not None
            else None
        ),
    )

    return Event(
        event_id=EventID(row["event_id"]),
        event_type=row["event_type"],
        schema_version=row["schema_version"],
        session_id=SessionID(row["session_id"]),
        session_sequence_number=row["session_sequence_number"],
        protocol_version_id=ProtocolVersionID(row["protocol_version_id"]),
        timestamp=row["timestamp"],
        wallclock_at=row["wallclock_at"],
        component=row["component"],
        component_version=row["component_version"],
        correlation_id=cast(
            CorrelationID | None,
            _identifier_or_none(CorrelationID, row["correlation_id"]),
        ),
        provenance=[EventID(eid) for eid in provenance_raw],
        payload=payload_raw,
        sensitive=bool(row["sensitive"]),
        data_classification=data_classification,
        trial_id=cast(TrialID | None, _identifier_or_none(TrialID, row["trial_id"])),
        block_id=cast(BlockID | None, _identifier_or_none(BlockID, row["block_id"])),
        quality_flags=list(quality_flags_raw),
    )
