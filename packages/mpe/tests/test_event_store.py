"""Shared event-store contract tests for in-memory and SQLite backends."""

from __future__ import annotations

import tempfile
import unittest

from mpe.errors import ConcurrencyError, ValidationError
from mpe.event_store import EventStore, InMemoryEventStore
from mpe.events import Event
from mpe.persistence.store import SQLiteEventStore
from mpe.types import EventID, ProgramVersionID, ProtocolVersionID, SessionID, make_id


class EventStoreContractTests:
    """Behavioral contract every event-store backend must satisfy."""

    def setUp(self) -> None:
        self.session_id = SessionID(str(make_id(SessionID)))
        self.protocol_version_id = ProtocolVersionID(str(make_id(ProtocolVersionID)))
        self.store = self._make_store()

    def _make_store(self) -> EventStore:
        raise NotImplementedError

    def _make_event(
        self,
        seq: int,
        event_type: str = "session_created",
        payload: dict | None = None,
        provenance: list[EventID] | None = None,
        timestamp: float | None = None,
    ) -> Event:
        return Event(
            event_id=make_id(EventID),
            event_type=event_type,
            schema_version="1.1",
            session_id=self.session_id,
            session_sequence_number=seq,
            protocol_version_id=self.protocol_version_id,
            timestamp=timestamp if timestamp is not None else 1.0 + (seq - 1) * 0.1,
            component="runtime",
            component_version="1.0.0",
            provenance=provenance or [],
            payload=payload or {
                "session_id": str(self.session_id),
                "program_version_id": str(ProgramVersionID("pv")),
                "protocol_version_id": str(self.protocol_version_id),
                "learner_id": "learner_1",
            },
        )

    def test_append_and_read(self) -> None:
        e1 = self._make_event(1)
        e2 = self._make_event(2, provenance=[e1.event_id])
        self.store.append(e1)
        self.store.append(e2)
        events = self.store.read(self.session_id)
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0].session_sequence_number, 1)
        self.assertEqual(events[1].session_sequence_number, 2)

    def test_expected_version_success(self) -> None:
        e1 = self._make_event(1)
        e2 = self._make_event(2)
        self.store.append(e1, expected_version=0)
        self.store.append(e2, expected_version=1)

    def test_optimistic_concurrency_failure(self) -> None:
        e1 = self._make_event(1)
        e2 = self._make_event(2)
        self.store.append(e1, expected_version=0)
        with self.assertRaises(ConcurrencyError):
            self.store.append(e2, expected_version=0)

    def test_sequence_number_monotonicity(self) -> None:
        e1 = self._make_event(1)
        e2 = self._make_event(1)
        self.store.append(e1)
        with self.assertRaises(ConcurrencyError):
            self.store.append(e2)

    def test_stored_events_are_immutable(self) -> None:
        e1 = self._make_event(1)
        self.store.append(e1)
        stored = self.store.read(self.session_id)[0]
        with self.assertRaises((TypeError, AttributeError)):
            stored.payload["new_key"] = "value"

    def test_payload_validation(self) -> None:
        bad = self._make_event(
            1,
            payload={
                "session_id": str(self.session_id),
            },
        )
        with self.assertRaises(ValidationError):
            self.store.append(bad)

    def test_session_isolation(self) -> None:
        other_session = SessionID(str(make_id(SessionID)))
        e1 = self._make_event(1)
        e_other = Event(
            event_id=make_id(EventID),
            event_type="session_created",
            schema_version="1.1",
            session_id=other_session,
            session_sequence_number=1,
            protocol_version_id=self.protocol_version_id,
            timestamp=1.0,
            component="runtime",
            component_version="1.0.0",
            payload={
                "session_id": str(other_session),
                "program_version_id": str(ProgramVersionID("pv")),
                "protocol_version_id": str(self.protocol_version_id),
                "learner_id": "learner_2",
            },
        )
        self.store.append(e1)
        self.store.append(e_other)
        self.assertEqual(self.store.get_last_sequence(self.session_id), 1)
        self.assertEqual(self.store.get_last_sequence(other_session), 1)

    def test_provenance_must_exist(self) -> None:
        e1 = self._make_event(1)
        e2 = self._make_event(2, provenance=[make_id(EventID)])
        self.store.append(e1)
        with self.assertRaises(ValidationError):
            self.store.append(e2)

    def test_timestamp_must_be_non_decreasing(self) -> None:
        e1 = self._make_event(1, timestamp=2.0)
        e2 = self._make_event(2, timestamp=1.5, provenance=[e1.event_id])
        self.store.append(e1)
        with self.assertRaises(ValidationError):
            self.store.append(e2)

    def test_list_sessions(self) -> None:
        other_session = SessionID(str(make_id(SessionID)))
        e1 = self._make_event(1)
        e2 = self._make_event(2, provenance=[e1.event_id])
        self.store.append(e1)
        self.store.append(e2)

        e_other = Event(
            event_id=make_id(EventID),
            event_type="session_created",
            schema_version="1.1",
            session_id=other_session,
            session_sequence_number=1,
            protocol_version_id=self.protocol_version_id,
            timestamp=1.0,
            component="runtime",
            component_version="1.0.0",
            payload={
                "session_id": str(other_session),
                "program_version_id": str(ProgramVersionID("pv")),
                "protocol_version_id": str(self.protocol_version_id),
                "learner_id": "learner_2",
            },
        )
        self.store.append(e_other)

        sessions = self.store.list_sessions()
        session_ids = [str(s.session_id) for s in sessions]
        self.assertEqual(session_ids, sorted([str(self.session_id), str(other_session)]))
        by_id = {str(s.session_id): s for s in sessions}
        self.assertEqual(by_id[str(self.session_id)].event_count, 2)
        self.assertEqual(by_id[str(self.session_id)].last_sequence, 2)
        self.assertEqual(by_id[str(other_session)].event_count, 1)
        self.assertEqual(by_id[str(other_session)].last_sequence, 1)

    def tearDown(self) -> None:
        self.store.close()


class InMemoryEventStoreTests(EventStoreContractTests, unittest.TestCase):
    def _make_store(self) -> EventStore:
        return InMemoryEventStore()


class SQLiteEventStoreTests(EventStoreContractTests, unittest.TestCase):
    def _make_store(self) -> EventStore:
        self._td = tempfile.TemporaryDirectory()
        self.addCleanup(self._td.cleanup)
        store = SQLiteEventStore(f"{self._td.name}/events.db")
        self.addCleanup(store.close)
        return store
