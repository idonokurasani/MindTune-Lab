"""Deterministic event-stream replay."""

from __future__ import annotations

from mpe.aggregates import RuntimeState
from mpe.errors import ReplayError
from mpe.event_store import EventStore
from mpe.types import SessionID


class Replay:
    """Reconstruct a RuntimeState exclusively from stored events."""

    def __init__(self, store: EventStore) -> None:
        self.store = store

    def replay(self, session_id: SessionID) -> RuntimeState:
        """Replay all events for a session and return the aggregate state."""
        events = self.store.read(session_id)
        if not events:
            raise ReplayError(f"No events found for session {session_id}")

        state = RuntimeState()
        for event in events:
            try:
                state.apply(event)
            except Exception as exc:
                raise ReplayError(
                    f"Replay failed at sequence {event.session_sequence_number}: {exc}"
                ) from exc

        return state
