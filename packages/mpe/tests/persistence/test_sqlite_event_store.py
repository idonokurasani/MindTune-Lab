"""SQLite-specific persistence tests."""

from __future__ import annotations

import sqlite3
import tempfile
import threading
import unittest

from mpe.errors import ConcurrencyError, ReplayError, UnknownSchemaVersionError, ValidationError
from mpe.events import Event
from mpe.persistence.serializer import to_row
from mpe.persistence.store import SQLiteEventStore
from mpe.types import EventID, ProgramVersionID, ProtocolVersionID, SessionID, make_id


class SQLiteEventStorePersistenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self._td = tempfile.TemporaryDirectory()
        self.addCleanup(self._td.cleanup)
        self.path = f"{self._td.name}/events.db"
        self.session_id = SessionID("test-session")
        self.protocol_version_id = ProtocolVersionID("pv-1")

    def _make_event(
        self,
        seq: int,
        event_id: EventID | None = None,
        provenance: list[EventID] | None = None,
        timestamp: float | None = None,
    ) -> Event:
        return Event(
            event_id=event_id or make_id(EventID),
            event_type="session_created" if seq == 1 else "session_started",
            schema_version="1.1",
            session_id=self.session_id,
            session_sequence_number=seq,
            protocol_version_id=self.protocol_version_id,
            timestamp=timestamp if timestamp is not None else 1.0 + (seq - 1) * 0.1,
            component="runtime",
            component_version="1.0.0",
            provenance=provenance or [],
            payload={
                "session_id": str(self.session_id),
                "program_version_id": str(ProgramVersionID("pv-1")),
                "protocol_version_id": str(self.protocol_version_id),
                "learner_id": "learner_1",
            }
            if seq == 1
            else {
                "session_id": str(self.session_id),
                "program_version_id": str(ProgramVersionID("pv-1")),
                "protocol_version_id": str(self.protocol_version_id),
                "learner_id": "learner_1",
                "random_seed": "seed_0",
            },
        )

    def test_wal_and_recovery(self) -> None:
        e1 = self._make_event(1)
        e2 = self._make_event(2, provenance=[e1.event_id])

        store1 = SQLiteEventStore(self.path)
        store1.append(e1)
        store1.append(e2)
        store1.close()

        store2 = SQLiteEventStore(self.path)
        events = store2.read(self.session_id)
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0], e1)
        self.assertEqual(events[1], e2)
        store2.close()

    def test_uncommitted_transaction_rollback(self) -> None:
        e1 = self._make_event(1)
        store = SQLiteEventStore(self.path)
        store.append(e1)
        store.close()

        # Open a raw connection and start a transaction but do not commit.
        conn = sqlite3.connect(self.path)
        row = to_row(self._make_event(2))
        columns = ",".join(row.keys())
        placeholders = ",".join("?" * len(row))
        conn.execute("BEGIN")
        conn.execute(f"INSERT INTO events ({columns}) VALUES ({placeholders})", tuple(row.values()))
        conn.close()

        store2 = SQLiteEventStore(self.path)
        events = store2.read(self.session_id)
        self.assertEqual(len(events), 1)
        store2.close()

    def test_batch_append_atomic(self) -> None:
        e1 = self._make_event(1)
        e2 = self._make_event(2, provenance=[e1.event_id])
        e3 = self._make_event(2)  # invalid: duplicate seq

        store = SQLiteEventStore(self.path)
        store.append_batch([e1, e2])
        events = store.read(self.session_id)
        self.assertEqual(len(events), 2)

        with self.assertRaises(ConcurrencyError):
            store.append_batch([self._make_event(3, provenance=[e1.event_id, e2.event_id]), e3])

        events = store.read(self.session_id)
        self.assertEqual(len(events), 2)
        store.close()

    def test_duplicate_event_id(self) -> None:
        e1 = self._make_event(1)
        other_session = SessionID("other-session")
        e2 = Event(
            event_id=e1.event_id,
            event_type="session_created",
            schema_version="1.1",
            session_id=other_session,
            session_sequence_number=1,
            protocol_version_id=self.protocol_version_id,
            timestamp=5.0,
            component="runtime",
            component_version="1.0.0",
            payload={
                "session_id": str(other_session),
                "program_version_id": str(ProgramVersionID("pv-1")),
                "protocol_version_id": str(self.protocol_version_id),
                "learner_id": "learner_2",
            },
        )

        store = SQLiteEventStore(self.path)
        store.append(e1)
        with self.assertRaises(ConcurrencyError):
            store.append(e2)
        store.close()

    def test_duplicate_sequence(self) -> None:
        e1 = self._make_event(1)
        e2 = self._make_event(1)
        store = SQLiteEventStore(self.path)
        store.append(e1)
        with self.assertRaises(ConcurrencyError):
            store.append(e2)
        store.close()

    def test_optimistic_concurrency(self) -> None:
        e1 = self._make_event(1)
        e2 = self._make_event(2, provenance=[e1.event_id])
        store = SQLiteEventStore(self.path)
        store.append(e1, expected_version=0)
        with self.assertRaises(ConcurrencyError):
            store.append(e2, expected_version=0)
        store.close()

    def test_unknown_schema_version(self) -> None:
        e1 = self._make_event(1)
        store = SQLiteEventStore(self.path)
        store.append(e1)
        store.close()

        conn = sqlite3.connect(self.path)
        conn.execute("UPDATE events SET schema_version = '2.0' WHERE event_id = ?", (str(e1.event_id),))
        conn.commit()
        conn.close()

        store2 = SQLiteEventStore(self.path)
        with self.assertRaises(UnknownSchemaVersionError):
            store2.read(self.session_id)
        store2.close()

    def test_corrupt_payload(self) -> None:
        e1 = self._make_event(1)
        store = SQLiteEventStore(self.path)
        store.append(e1)
        store.close()

        conn = sqlite3.connect(self.path)
        conn.execute("UPDATE events SET payload = 'not-json' WHERE event_id = ?", (str(e1.event_id),))
        conn.commit()
        conn.close()

        store2 = SQLiteEventStore(self.path)
        with self.assertRaises(ReplayError):
            store2.read(self.session_id)
        store2.close()

    def test_schema_version_rejection_on_open(self) -> None:
        conn = sqlite3.connect(self.path)
        conn.execute("PRAGMA user_version = 99")
        conn.close()

        with self.assertRaises(ValidationError):
            SQLiteEventStore(self.path)

    def test_concurrent_writers(self) -> None:
        store = SQLiteEventStore(self.path)
        e1 = self._make_event(1)
        store.append(e1)

        errors: list[Exception] = []
        results: list[int] = []

        def writer(seq: int) -> None:
            try:
                store_local = SQLiteEventStore(self.path)
                event = self._make_event(
                    seq,
                    event_id=make_id(EventID),
                    provenance=[e1.event_id],
                )
                store_local.append(event)
                results.append(seq)
                store_local.close()
            except Exception as exc:
                errors.append(exc)

        t1 = threading.Thread(target=writer, args=(2,))
        t2 = threading.Thread(target=writer, args=(2,))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        self.assertEqual(len(results), 1)
        self.assertEqual(len(errors), 1)
        self.assertIsInstance(errors[0], ConcurrencyError)
        store.close()

    def test_partial_replay(self) -> None:
        e1 = self._make_event(1)
        e2 = self._make_event(2, provenance=[e1.event_id])
        e3 = self._make_event(3, provenance=[e2.event_id])
        store = SQLiteEventStore(self.path)
        store.append(e1)
        store.append(e2)
        store.append(e3)

        partial = store.read(self.session_id, from_seq=2, to_seq=2)
        self.assertEqual(len(partial), 1)
        self.assertEqual(partial[0].session_sequence_number, 2)
        store.close()
