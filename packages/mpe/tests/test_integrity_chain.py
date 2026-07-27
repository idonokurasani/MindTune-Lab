"""Tests for the per-stream hash chain (SR-M1 WP-1, ADR-0001 sec. 2.3-2.11)."""

from __future__ import annotations

import dataclasses
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from mpe.errors import IntegrityError, ValidationError
from mpe.event_store import InMemoryEventStore
from mpe.events import CURRENT_EVENT_SCHEMA_VERSION, Event
from mpe.integrity import (
    INTEGRITY_UNAVAILABLE,
    INTEGRITY_VERIFIED,
    canonical_digest_bytes,
    canonical_record_bytes,
    compute_content_digest,
    verify_stream,
)
from mpe.persistence.store import (
    CURRENT_DATABASE_VERSION,
    SQLiteEventStore,
    migrate_v1_to_v2,
)
from mpe.protocol.recognition import run_recognition_session
from mpe.runtime import FixedWallClock
from mpe.types import EventID, ProtocolVersionID, SessionID, make_id

_V1_CREATE_EVENTS_TABLE = """
CREATE TABLE events (
    event_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    session_sequence_number INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    protocol_version_id TEXT NOT NULL,
    timestamp REAL NOT NULL,
    wallclock_at REAL,
    component TEXT NOT NULL,
    component_version TEXT NOT NULL,
    correlation_id TEXT,
    provenance TEXT NOT NULL,
    payload TEXT NOT NULL,
    sensitive INTEGER NOT NULL,
    data_classification TEXT,
    trial_id TEXT,
    block_id TEXT,
    quality_flags TEXT NOT NULL,
    inserted_at REAL NOT NULL,
    UNIQUE (session_id, session_sequence_number)
);
"""


def make_event(
    session_id: SessionID,
    seq: int,
    *,
    schema_version: str = CURRENT_EVENT_SCHEMA_VERSION,
    event_id: EventID | None = None,
) -> Event:
    return Event(
        event_id=event_id or make_id(EventID),
        event_type="session_created" if seq == 1 else "session_started",
        schema_version=schema_version,
        session_id=session_id,
        session_sequence_number=seq,
        protocol_version_id=ProtocolVersionID("protocol_v1"),
        timestamp=float(seq),
        component="runtime",
        component_version="1.0.0",
        payload={
            "session_id": str(session_id),
            "program_version_id": "program_v1",
            "protocol_version_id": "protocol_v1",
            "learner_id": "learner_1",
            **({} if seq == 1 else {"random_seed": "seed_0"}),
        },
    )


def write_v1_database(path: Path, session_id: SessionID, count: int = 2) -> None:
    """Create a layout-v1 database holding historical schema-1.1 events."""
    conn = sqlite3.connect(str(path), isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute(_V1_CREATE_EVENTS_TABLE)
    conn.execute("PRAGMA user_version = 1")
    for seq in range(1, count + 1):
        event = make_event(session_id, seq, schema_version="1.1")
        conn.execute(
            "INSERT INTO events (event_id, session_id, session_sequence_number, "
            "event_type, schema_version, protocol_version_id, timestamp, component, "
            "component_version, provenance, payload, sensitive, quality_flags, "
            "inserted_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                str(event.event_id),
                str(event.session_id),
                event.session_sequence_number,
                event.event_type,
                event.schema_version,
                str(event.protocol_version_id),
                event.timestamp,
                event.component,
                event.component_version,
                "[]",
                json.dumps(dict(event.payload), sort_keys=True, separators=(",", ":")),
                0,
                "[]",
                0.0,
            ),
        )
    conn.close()


def _unreferenced_interior_sequence(events: list[Event]) -> int:
    """An interior sequence no later event names in its provenance.

    Deleting a referenced event would trip provenance validation before the
    chain check, which would prove nothing about the chain.
    """
    referenced = {str(prov) for event in events for prov in event.provenance}
    for event in events[1:-1]:
        if str(event.event_id) not in referenced:
            return event.session_sequence_number
    raise AssertionError("no unreferenced interior event in the stream")


class CanonicalSerializationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.event = make_event(SessionID("s1"), 1)

    def test_digest_bytes_exclude_content_digest_and_include_previous(self) -> None:
        fields = json.loads(canonical_digest_bytes(self.event))
        self.assertNotIn("content_digest", fields)
        self.assertIn("previous_digest", fields)

    def test_record_bytes_carry_both_digest_fields(self) -> None:
        fields = json.loads(canonical_record_bytes(self.event))
        self.assertIn("content_digest", fields)
        self.assertIn("previous_digest", fields)

    def test_the_two_representations_are_distinct(self) -> None:
        self.assertNotEqual(canonical_digest_bytes(self.event), canonical_record_bytes(self.event))

    def test_digest_is_deterministic(self) -> None:
        self.assertEqual(compute_content_digest(self.event), compute_content_digest(self.event))

    def test_digest_changes_when_a_bound_field_changes(self) -> None:
        other = dataclasses.replace(self.event, component_version="9.9.9")
        self.assertNotEqual(compute_content_digest(self.event), compute_content_digest(other))


class InMemoryChainTests(unittest.TestCase):
    def setUp(self) -> None:
        self.store = InMemoryEventStore()
        self.session_id = SessionID("s1")

    def _append(self, count: int) -> list[Event]:
        return [self.store.append(make_event(self.session_id, seq)) for seq in range(1, count + 1)]

    def test_append_links_each_event_to_its_predecessor(self) -> None:
        stored = self._append(3)
        self.assertIsNone(stored[0].previous_digest)
        for previous, current in zip(stored, stored[1:], strict=False):
            self.assertEqual(current.previous_digest, previous.content_digest)

    def test_chained_stream_verifies(self) -> None:
        self._append(3)
        self.assertEqual(self.store.integrity_status(self.session_id), INTEGRITY_VERIFIED)

    def test_schema_11_stream_reports_unavailable(self) -> None:
        self.store.append(make_event(self.session_id, 1, schema_version="1.1"))
        self.assertEqual(self.store.integrity_status(self.session_id), INTEGRITY_UNAVAILABLE)
        self.assertIsNone(self.store.read(self.session_id)[0].content_digest)

    def test_mixing_schema_versions_in_one_stream_is_refused(self) -> None:
        self.store.append(make_event(self.session_id, 1, schema_version="1.1"))
        with self.assertRaises(IntegrityError):
            self.store.append(make_event(self.session_id, 2))

    def test_read_unverified_requires_a_reason(self) -> None:
        with self.assertRaises(ValidationError):
            self.store.read_unverified(self.session_id, reason="  ")


class ChainDetectionTests(unittest.TestCase):
    """What the chain does and does not detect (ADR-0001 sec. 2.10)."""

    def setUp(self) -> None:
        store = InMemoryEventStore()
        self.session_id = SessionID("s1")
        self.events = [store.append(make_event(self.session_id, seq)) for seq in range(1, 5)]

    def test_mutation_is_detected(self) -> None:
        tampered = list(self.events)
        tampered[2] = dataclasses.replace(tampered[2], component_version="9.9.9")
        with self.assertRaises(IntegrityError):
            verify_stream(tampered)

    def test_interior_deletion_is_detected(self) -> None:
        with self.assertRaises(IntegrityError):
            verify_stream([self.events[0], self.events[1], self.events[3]])

    def test_insertion_is_detected(self) -> None:
        foreign = InMemoryEventStore().append(make_event(SessionID("s2"), 1))
        with self.assertRaises(IntegrityError):
            verify_stream([*self.events[:2], foreign, *self.events[2:]])

    def test_reordering_is_detected(self) -> None:
        reordered = [self.events[0], self.events[2], self.events[1], self.events[3]]
        with self.assertRaises(IntegrityError):
            verify_stream(reordered)

    def test_tail_truncation_is_not_detected(self) -> None:
        """Negative test: a truncated chain is still internally consistent.

        Removing the tail leaves a valid chain, so verification accepts it. Tail
        truncation is only detectable against an independently retained anchor,
        which SR-M1 does not deliver.
        """
        self.assertEqual(verify_stream(self.events[:2]), INTEGRITY_VERIFIED)

    def test_tail_truncation_is_detected_against_a_retained_anchor(self) -> None:
        """The same truncation becomes detectable given an independent anchor."""
        expected_terminal = self.events[-1].content_digest
        expected_count = len(self.events)

        truncated = self.events[:2]
        self.assertEqual(verify_stream(truncated), INTEGRITY_VERIFIED)
        self.assertNotEqual(truncated[-1].content_digest, expected_terminal)
        self.assertNotEqual(len(truncated), expected_count)


class SQLiteIntegrityTests(unittest.TestCase):
    def setUp(self) -> None:
        self._td = tempfile.TemporaryDirectory()
        self.addCleanup(self._td.cleanup)
        self.path = Path(self._td.name) / "events.db"

    def _tamper(self, sql: str, params: tuple[object, ...] = ()) -> None:
        conn = sqlite3.connect(str(self.path), isolation_level=None)
        conn.execute(sql, params)
        conn.close()

    def test_new_databases_are_created_at_layout_v2(self) -> None:
        with SQLiteEventStore(self.path) as store:
            self.assertEqual(store.database_version, CURRENT_DATABASE_VERSION)

    def test_a_recognition_session_is_verified_end_to_end(self) -> None:
        with SQLiteEventStore(self.path) as store:
            result = run_recognition_session(store, wall_clock=FixedWallClock(1_700_000_000.0))
            self.assertEqual(store.integrity_status(result.state.session_id), INTEGRITY_VERIFIED)

        with SQLiteEventStore(self.path) as reopened:
            events = reopened.read(result.state.session_id)
            self.assertTrue(all(event.content_digest for event in events))

    def test_a_mutated_event_is_detected_on_read(self) -> None:
        with SQLiteEventStore(self.path) as store:
            result = run_recognition_session(store)
            session_id = result.state.session_id

        self._tamper(
            "UPDATE events SET component_version = ? WHERE session_sequence_number = 2",
            ("9.9.9",),
        )

        with SQLiteEventStore(self.path) as reopened:
            with self.assertRaises(IntegrityError):
                reopened.read(session_id)

    def test_a_deleted_interior_event_is_detected_on_read(self) -> None:
        with SQLiteEventStore(self.path) as store:
            result = run_recognition_session(store)
            session_id = result.state.session_id
            unreferenced = _unreferenced_interior_sequence(store.read(session_id))

        self._tamper("DELETE FROM events WHERE session_sequence_number = ?", (unreferenced,))

        with SQLiteEventStore(self.path) as reopened:
            with self.assertRaises(IntegrityError):
                reopened.read(session_id)

    def test_a_missing_digest_on_a_schema_12_event_is_invalid(self) -> None:
        with SQLiteEventStore(self.path) as store:
            result = run_recognition_session(store)
            session_id = result.state.session_id

        self._tamper("UPDATE events SET content_digest = NULL WHERE session_sequence_number = 2")

        with SQLiteEventStore(self.path) as reopened:
            with self.assertRaises(IntegrityError):
                reopened.read(session_id)

    def test_the_recovery_path_still_reads_a_damaged_stream(self) -> None:
        with SQLiteEventStore(self.path) as store:
            result = run_recognition_session(store)
            session_id = result.state.session_id
            expected = len(store.read(session_id))

        self._tamper(
            "UPDATE events SET component_version = ? WHERE session_sequence_number = 2",
            ("9.9.9",),
        )

        with SQLiteEventStore(self.path) as reopened:
            recovered = reopened.read_unverified(
                session_id, reason="inspecting a stream that fails verification"
            )
            self.assertEqual(len(recovered), expected)

    def test_truncating_the_tail_in_storage_is_not_detected(self) -> None:
        """Negative test, in storage: the store cannot see a removed tail."""
        with SQLiteEventStore(self.path) as store:
            result = run_recognition_session(store)
            session_id = result.state.session_id
            full_length = len(store.read(session_id))

        self._tamper("DELETE FROM events WHERE session_sequence_number > ?", (full_length - 3,))

        with SQLiteEventStore(self.path) as reopened:
            self.assertEqual(reopened.integrity_status(session_id), INTEGRITY_VERIFIED)
            self.assertEqual(len(reopened.read(session_id)), full_length - 3)


class MigrationTests(unittest.TestCase):
    """ADR-0001 sec. 5.11 migration acceptance."""

    def setUp(self) -> None:
        self._td = tempfile.TemporaryDirectory()
        self.addCleanup(self._td.cleanup)
        self.path = Path(self._td.name) / "legacy.db"
        self.legacy_session = SessionID("legacy-session")
        write_v1_database(self.path, self.legacy_session)

    def _migrate(self) -> None:
        conn = sqlite3.connect(str(self.path), isolation_level=None)
        conn.row_factory = sqlite3.Row
        migrate_v1_to_v2(conn)
        conn.close()

    def test_a_v1_database_is_readable_but_closed_to_append(self) -> None:
        with SQLiteEventStore(self.path) as store:
            self.assertEqual(store.database_version, 1)
            events = store.read(self.legacy_session)
            self.assertEqual(len(events), 2)
            self.assertEqual(store.integrity_status(self.legacy_session), INTEGRITY_UNAVAILABLE)
            with self.assertRaises(IntegrityError):
                store.append(make_event(SessionID("new-session"), 1))

    def test_migration_preserves_historical_streams(self) -> None:
        with SQLiteEventStore(self.path) as store:
            before = store.read(self.legacy_session)

        self._migrate()

        with SQLiteEventStore(self.path) as store:
            self.assertEqual(store.database_version, CURRENT_DATABASE_VERSION)
            after = store.read(self.legacy_session)
            self.assertEqual(before, after)
            self.assertEqual(store.integrity_status(self.legacy_session), INTEGRITY_UNAVAILABLE)

    def test_migration_accepts_new_schema_12_sessions(self) -> None:
        self._migrate()
        with SQLiteEventStore(self.path) as store:
            result = run_recognition_session(store)
            self.assertEqual(store.integrity_status(result.state.session_id), INTEGRITY_VERIFIED)
            self.assertEqual(store.integrity_status(self.legacy_session), INTEGRITY_UNAVAILABLE)

    def test_migration_refuses_schema_12_appends_to_a_historical_stream(self) -> None:
        self._migrate()
        with SQLiteEventStore(self.path) as store:
            with self.assertRaises(IntegrityError):
                store.append(make_event(self.legacy_session, 3))

    def test_opening_with_migrate_performs_the_migration(self) -> None:
        with SQLiteEventStore(self.path, migrate=True) as store:
            self.assertEqual(store.database_version, CURRENT_DATABASE_VERSION)
            self.assertEqual(len(store.read(self.legacy_session)), 2)

    def test_migration_is_idempotent(self) -> None:
        self._migrate()
        self._migrate()
        with SQLiteEventStore(self.path) as store:
            self.assertEqual(store.database_version, CURRENT_DATABASE_VERSION)


if __name__ == "__main__":
    unittest.main()
