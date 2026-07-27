"""Canonical serialization and the per-stream hash chain (ADR-0001).

Scope of the guarantee (ADR-0001 sec. 2.10): within a retained stream the chain
makes mutation, interior deletion, insertion, and reordering detectable. It does
not detect removal of the tail of a stream, because a truncated chain is still
internally consistent. Tail truncation is only detectable against an
independently retained anchor (expected terminal digest, event count, signed
manifest, external append-only log), which this milestone does not deliver.

The mechanism is therefore tamper-evident, not tamper-proof.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
from typing import Any

from mpe.enums import CanonicalEnum
from mpe.errors import IntegrityError
from mpe.events import Event
from mpe.types import Identifier

_JSON_SEPARATORS = (",", ":")

DIGEST_ALGORITHM = "sha256"

INTEGRITY_VERIFIED = "verified"
INTEGRITY_UNAVAILABLE = "unavailable"

TAIL_TRUNCATION_UNDETERMINED = "undetermined"
"""Tail truncation cannot be decided without an independently retained anchor."""

_DIGEST_EXCLUDED_FIELDS = frozenset({"content_digest"})


def _json_default(obj: Any) -> Any:
    """Fallback JSON encoder for Identifier and CanonicalEnum values."""
    if isinstance(obj, Identifier):
        return obj.value
    if isinstance(obj, CanonicalEnum):
        return obj.value
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def canonical_json(value: Any) -> str:
    """Encode a value deterministically: sorted keys, no insignificant spacing."""
    return json.dumps(
        value,
        sort_keys=True,
        separators=_JSON_SEPARATORS,
        ensure_ascii=False,
        default=_json_default,
    )


def canonical_digest_bytes(event: Event) -> bytes:
    """Return the exact bytes hashed to produce `content_digest`.

    Covers every semantically bound envelope and payload field, including
    `previous_digest`, and excludes `content_digest` itself.
    """
    fields = {
        key: value for key, value in event.as_dict().items() if key not in _DIGEST_EXCLUDED_FIELDS
    }
    return canonical_json(fields).encode("utf-8")


def canonical_record_bytes(event: Event) -> bytes:
    """Return the complete stored/exported record, including both digest fields.

    Shares the encoder with `canonical_digest_bytes` but not the field set: this
    is the record, not the hash input.
    """
    return canonical_json(event.as_dict()).encode("utf-8")


def compute_content_digest(event: Event) -> str:
    """Return the hex SHA-256 of `canonical_digest_bytes(event)`."""
    return hashlib.sha256(canonical_digest_bytes(event)).hexdigest()


def is_chained_schema(schema_version: str) -> bool:
    """Whether events of this schema version carry a chain."""
    return schema_version >= "1.2"


def chain_event(event: Event, previous_digest: str | None) -> Event:
    """Return a copy of `event` linked to `previous_digest` and self-digested.

    Schema-1.1 events are returned unchanged: historical streams are never
    retro-chained.
    """
    if not is_chained_schema(event.schema_version):
        return event

    linked = dataclasses.replace(event, previous_digest=previous_digest, content_digest=None)
    return dataclasses.replace(linked, content_digest=compute_content_digest(linked))


def verify_link(event: Event, previous_digest: str | None) -> None:
    """Verify one event against the digest of its predecessor.

    Raises `IntegrityError` on a broken link, a mismatching digest, or missing
    digest fields on a schema-1.2 event.
    """
    if not is_chained_schema(event.schema_version):
        return

    where = f"event {event.event_id} (sequence {event.session_sequence_number})"

    if event.content_digest is None:
        raise IntegrityError(f"Missing content_digest on schema-1.2 {where}")
    if event.previous_digest != previous_digest:
        raise IntegrityError(
            f"Broken hash chain at {where}: expected previous_digest "
            f"{previous_digest!r}, stored {event.previous_digest!r}"
        )

    recomputed = compute_content_digest(event)
    if recomputed != event.content_digest:
        raise IntegrityError(
            f"Content digest mismatch at {where}: recomputed {recomputed}, "
            f"stored {event.content_digest}"
        )


def verify_stream(events: list[Event]) -> str:
    """Verify a complete stream and return its integrity status.

    Returns `verified` for a schema-1.2 chain that checks out, `unavailable` for
    a historical schema-1.1 stream. Raises `IntegrityError` for a broken chain
    or for a stream mixing schema versions.
    """
    if not events:
        return INTEGRITY_UNAVAILABLE

    versions = {event.schema_version for event in events}
    if len(versions) > 1:
        raise IntegrityError(
            f"Stream {events[0].session_id} mixes schema versions: {sorted(versions)}"
        )

    if not is_chained_schema(events[0].schema_version):
        return INTEGRITY_UNAVAILABLE

    previous_digest: str | None = None
    for event in events:
        verify_link(event, previous_digest)
        previous_digest = event.content_digest
    return INTEGRITY_VERIFIED


def stream_schema_version(events: list[Event]) -> str | None:
    """Return the schema version of a stream, or None when it is empty."""
    return events[0].schema_version if events else None
