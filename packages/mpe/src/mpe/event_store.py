"""In-memory event store with optimistic concurrency."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from mpe.errors import ConcurrencyError, ValidationError
from mpe.events import SUPPORTED_EVENT_TYPES, Event
from mpe.types import SessionID
from mpe.validation import validate_event


@dataclass(frozen=True)
class SessionSummary:
    """Lightweight summary of a session stream."""

    session_id: SessionID
    event_count: int
    last_sequence: int


class EventStore(Protocol):
    """Common event-store contract for in-memory and persistent backends."""

    def append(self, event: Event, expected_version: int | None = None) -> None: ...
    def read(
        self,
        session_id: SessionID,
        from_seq: int | None = None,
        to_seq: int | None = None,
    ) -> list[Event]: ...
    def get_last_sequence(self, session_id: SessionID) -> int: ...
    def all_events(self) -> list[Event]: ...
    def list_sessions(self) -> list[SessionSummary]: ...
    def close(self) -> None: ...


class InMemoryEventStore:
    """Append-only in-memory event store."""

    def __init__(self) -> None:
        self._streams: dict[SessionID, list[Event]] = {}
        self._event_ids: set[str] = set()

    def append(self, event: Event, expected_version: int | None = None) -> None:
        if not isinstance(event, Event):
            raise ValidationError("Can only append Event instances")

        if event.event_type not in SUPPORTED_EVENT_TYPES:
            raise ValidationError(f"Unsupported event type: {event.event_type}")

        validate_event(event)

        stream = self._streams.setdefault(event.session_id, [])

        if str(event.event_id) in self._event_ids:
            raise ConcurrencyError(
                f"Event {event.event_id} already exists in store"
            )

        current_version = len(stream)
        if expected_version is not None and expected_version != current_version:
            raise ConcurrencyError(
                f"Expected version {expected_version}, current {current_version}"
            )

        if stream and event.session_sequence_number <= stream[-1].session_sequence_number:
            raise ConcurrencyError(
                "Event session_sequence_number must be strictly increasing"
            )

        if stream and event.timestamp < stream[-1].timestamp:
            raise ValidationError("Event timestamps must be non-decreasing")

        if not self._provenance_exists(event):
            raise ValidationError(
                f"Provenance event(s) not found for {event.event_id}"
            )

        self._event_ids.add(str(event.event_id))
        stream.append(event)

    def _provenance_exists(self, event: Event) -> bool:
        stream = self._streams.get(event.session_id, [])
        ids = {str(e.event_id) for e in stream}
        for prov_id in event.provenance:
            if str(prov_id) not in ids:
                return False
        return True

    def read(
        self,
        session_id: SessionID,
        from_seq: int | None = None,
        to_seq: int | None = None,
    ) -> list[Event]:
        stream = self._streams.get(session_id, [])
        start = (from_seq - 1) if from_seq is not None else 0
        end = to_seq if to_seq is not None else len(stream)
        return stream[start:end]

    def get_last_sequence(self, session_id: SessionID) -> int:
        stream = self._streams.get(session_id, [])
        return stream[-1].session_sequence_number if stream else 0

    def all_events(self) -> list[Event]:
        events: list[Event] = []
        for stream in self._streams.values():
            events.extend(stream)
        return events

    def list_sessions(self) -> list[SessionSummary]:
        return [
            SessionSummary(
                session_id=session_id,
                event_count=len(stream),
                last_sequence=stream[-1].session_sequence_number if stream else 0,
            )
            for session_id, stream in sorted(self._streams.items(), key=lambda item: str(item[0]))
        ]

    def close(self) -> None:
        """No-op for the in-memory store."""
