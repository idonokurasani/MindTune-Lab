"""Serializer round-trip tests."""

from __future__ import annotations

import sqlite3
import unittest

from mpe.demo import run_demo
from mpe.enums import DataClassification
from mpe.events import Event
from mpe.persistence.serializer import from_row, to_row
from mpe.types import (
    BlockID,
    CorrelationID,
    EventID,
    ProtocolVersionID,
    SessionID,
    TrialID,
    make_id,
)


class SerializationTests(unittest.TestCase):
    def test_demo_events_round_trip(self) -> None:
        _live_state, events, _replayed, _store = run_demo()
        self.assertEqual(len(events), 23)
        for original in events:
            row = to_row(original)
            reconstructed = from_row(row)
            self.assertEqual(original, reconstructed)

    def test_identifier_and_enum_reconstruction(self) -> None:
        session_id = SessionID(str(make_id(SessionID)))
        event_id = make_id(EventID)
        trial_id = make_id(TrialID)
        block_id = make_id(BlockID)
        correlation_id = make_id(CorrelationID)

        event = Event(
            event_id=event_id,
            event_type="session_created",
            schema_version="1.1",
            session_id=session_id,
            session_sequence_number=1,
            protocol_version_id=session_id,
            timestamp=1.0,
            component="runtime",
            component_version="1.0.0",
            correlation_id=correlation_id,
            provenance=[],
            payload={
                "session_id": str(session_id),
                "program_version_id": str(session_id),
                "protocol_version_id": str(session_id),
                "learner_id": "learner_1",
            },
            trial_id=trial_id,
            block_id=block_id,
            data_classification=DataClassification.RESTRICTED,
            quality_flags=["q1"],
            wallclock_at=2.0,
            sensitive=True,
        )

        row = to_row(event)
        reconstructed = from_row(row)
        self.assertEqual(reconstructed.event_id, event_id)
        self.assertIsInstance(reconstructed.event_id, EventID)
        self.assertIsInstance(reconstructed.session_id, SessionID)
        self.assertIsInstance(reconstructed.trial_id, TrialID)
        self.assertIsInstance(reconstructed.block_id, BlockID)
        self.assertIsInstance(reconstructed.correlation_id, CorrelationID)
        self.assertEqual(reconstructed.data_classification, DataClassification.RESTRICTED)
        self.assertEqual(reconstructed.quality_flags, ("q1",))
        self.assertTrue(reconstructed.sensitive)
        self.assertEqual(reconstructed.wallclock_at, 2.0)

    def test_nullable_fields_are_none(self) -> None:
        event = Event(
            event_id=make_id(EventID),
            event_type="session_created",
            schema_version="1.1",
            session_id=SessionID(str(make_id(SessionID))),
            session_sequence_number=1,
            protocol_version_id=SessionID(str(make_id(SessionID))),
            timestamp=1.0,
            component="runtime",
            component_version="1.0.0",
            payload={
                "session_id": str(SessionID(str(make_id(SessionID)))),
                "program_version_id": str(SessionID(str(make_id(SessionID)))),
                "protocol_version_id": str(SessionID(str(make_id(SessionID)))),
                "learner_id": "learner_1",
            },
        )
        row = to_row(event)
        reconstructed = from_row(row)
        self.assertIsNone(reconstructed.data_classification)
        self.assertIsNone(reconstructed.trial_id)
        self.assertIsNone(reconstructed.block_id)
        self.assertIsNone(reconstructed.correlation_id)
        self.assertIsNone(reconstructed.wallclock_at)
        self.assertFalse(reconstructed.sensitive)

    def test_sqlite_row_factory_compatibility(self) -> None:
        event = Event(
            event_id=make_id(EventID),
            event_type="session_created",
            schema_version="1.1",
            session_id=SessionID("session_1"),
            session_sequence_number=1,
            protocol_version_id=ProtocolVersionID("protocol_1"),
            timestamp=1.0,
            component="runtime",
            component_version="1.0.0",
            payload={
                "session_id": "session_1",
                "program_version_id": "pv_1",
                "protocol_version_id": "protocol_1",
                "learner_id": "learner_1",
            },
        )
        row = to_row(event)

        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        conn.execute(
            "CREATE TABLE events ("
            "event_id TEXT, session_id TEXT, session_sequence_number INTEGER, "
            "event_type TEXT, schema_version TEXT, protocol_version_id TEXT, "
            "timestamp REAL, wallclock_at REAL, component TEXT, component_version TEXT, "
            "correlation_id TEXT, provenance TEXT, payload TEXT, sensitive INTEGER, "
            "data_classification TEXT, trial_id TEXT, block_id TEXT, quality_flags TEXT, "
            "content_digest TEXT, previous_digest TEXT, writer_revision TEXT, "
            "inserted_at REAL)"
        )
        columns = ",".join(row.keys())
        placeholders = ",".join("?" * len(row))
        conn.execute(f"INSERT INTO events ({columns}) VALUES ({placeholders})", tuple(row.values()))
        sqlite_row = conn.execute("SELECT * FROM events").fetchone()
        reconstructed = from_row(sqlite_row)
        self.assertEqual(event, reconstructed)
