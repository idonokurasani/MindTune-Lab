"""Rebuild-from-empty through the supported interchange (SR-M1 WP-4).

Every rebuild here goes through `export_stream` / `import_stream` and the two CLI
commands. No test writes SQLite tables directly: that would test the test rather
than the system (implementation plan sec. 3.4.1).
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from mpe import cli
from mpe.errors import IntegrityError, ValidationError
from mpe.event_store import InMemoryEventStore
from mpe.integrity import (
    INTEGRITY_VERIFIED,
    TAIL_TRUNCATION_UNDETERMINED,
    canonical_record_bytes,
    verify_stream,
)
from mpe.persistence.interchange import export_stream, import_stream
from mpe.persistence.store import SQLiteEventStore
from mpe.protocol.recognition import run_recognition_session
from mpe.protocol.summary_recognition import derive_recognition_summary
from mpe.replay import Replay
from mpe.types import SessionID


class InterchangeTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.source_path = self.root / "source.sqlite3"
        self.target_path = self.root / "target.sqlite3"

        with SQLiteEventStore(self.source_path) as store:
            result = run_recognition_session(store)
            self.session_id = result.state.session_id
            self.events = store.read(self.session_id)
        assert self.session_id is not None

    def exported_lines(self) -> list[bytes]:
        with SQLiteEventStore(self.source_path) as store:
            return list(export_stream(store, self.session_id))


class RebuildFromEmptyTests(InterchangeTestCase):
    def test_records_are_canonical_and_ordered(self) -> None:
        lines = self.exported_lines()
        self.assertEqual(lines, [canonical_record_bytes(e) for e in self.events])
        sequences = [json.loads(line)["session_sequence_number"] for line in lines]
        self.assertEqual(sequences, sorted(sequences))

    def test_records_carry_both_digest_fields(self) -> None:
        for line in self.exported_lines():
            record = json.loads(line)
            self.assertIn("content_digest", record)
            self.assertIn("previous_digest", record)
            self.assertIsNotNone(record["content_digest"])

    def test_rebuild_yields_identical_bytes_digest_state_and_summary(self) -> None:
        lines = self.exported_lines()
        with SQLiteEventStore(self.target_path) as store:
            imported = import_stream(store, lines)
            rebuilt = store.read(self.session_id)
            self.assertEqual(store.integrity_status(self.session_id), INTEGRITY_VERIFIED)

        self.assertEqual(imported, len(self.events))
        self.assertEqual(
            [canonical_record_bytes(e) for e in rebuilt],
            [canonical_record_bytes(e) for e in self.events],
        )
        self.assertEqual(rebuilt[-1].content_digest, self.events[-1].content_digest)
        with SQLiteEventStore(self.target_path) as store:
            rebuilt_state = Replay(store).replay(self.session_id)
        with SQLiteEventStore(self.source_path) as store:
            source_state = Replay(store).replay(self.session_id)
        self.assertEqual(rebuilt_state.as_dict(), source_state.as_dict())
        self.assertEqual(
            derive_recognition_summary(rebuilt).as_dict(),
            derive_recognition_summary(self.events).as_dict(),
        )

    def test_import_reapplies_the_ordinary_invariants(self) -> None:
        """Ingest is not a bulk load: a broken chain is rejected on append."""
        lines = self.exported_lines()
        record = json.loads(lines[3])
        record["payload"] = dict(record["payload"])
        record["component_version"] = "9.9.9"
        lines[3] = json.dumps(record).encode("utf-8")
        with SQLiteEventStore(self.target_path) as store:
            with self.assertRaises(IntegrityError):
                import_stream(store, lines)

    def test_import_refuses_a_stream_that_already_exists(self) -> None:
        lines = self.exported_lines()
        with SQLiteEventStore(self.target_path) as store:
            import_stream(store, lines)
            with self.assertRaises(ValidationError):
                import_stream(store, lines)

    def test_import_refuses_empty_and_malformed_input(self) -> None:
        with SQLiteEventStore(self.target_path) as store:
            with self.assertRaises(ValidationError):
                import_stream(store, [])
            with self.assertRaises(ValidationError):
                import_stream(store, [b"{not json"])

    def test_import_refuses_more_than_one_session(self) -> None:
        with SQLiteEventStore(self.source_path) as store:
            other = run_recognition_session(store).state.session_id
            mixed = list(export_stream(store, self.session_id)) + list(export_stream(store, other))
        with SQLiteEventStore(self.target_path) as store:
            with self.assertRaises(ValidationError):
                import_stream(store, mixed)

    def test_export_reads_through_the_verified_path(self) -> None:
        """Export refuses a stream that fails verification."""
        store = InMemoryEventStore()
        session_id = run_recognition_session(store).state.session_id
        assert session_id is not None
        stream = store._streams[session_id]
        stream.pop(4)
        with self.assertRaises(IntegrityError):
            list(export_stream(store, session_id))

    def test_unanchored_tail_truncation_remains_undetermined(self) -> None:
        """The negative case ADR-0001 sec. 2.10 requires us to state openly.

        A truncated export re-imports cleanly and verifies as `verified`: the
        chain proves nothing about events that were removed from the end. Only
        an independently retained anchor — here the expected terminal digest —
        detects it, and SR-M1 does not deliver one.
        """
        lines = self.exported_lines()
        truncated = lines[:-3]
        with SQLiteEventStore(self.target_path) as store:
            import_stream(store, truncated)
            rebuilt = store.read(self.session_id)
            self.assertEqual(store.integrity_status(self.session_id), INTEGRITY_VERIFIED)

        self.assertEqual(verify_stream(rebuilt), INTEGRITY_VERIFIED)
        self.assertEqual(TAIL_TRUNCATION_UNDETERMINED, "undetermined")
        self.assertLess(len(rebuilt), len(self.events))

        expected_terminal = self.events[-1].content_digest
        self.assertNotEqual(rebuilt[-1].content_digest, expected_terminal)


class InterchangeCLITests(InterchangeTestCase):
    def _run(self, argv: list[str]) -> tuple[int, str]:
        import contextlib
        import io

        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            code = cli.main(argv)
        return code, out.getvalue()

    def test_export_then_import_round_trip(self) -> None:
        dump = self.root / "session.jsonl"
        code, out = self._run(
            [
                "--store-path",
                str(self.source_path),
                "export-session",
                "--session-id",
                str(self.session_id),
                "--out",
                str(dump),
                "--format",
                "json",
            ]
        )
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["event_count"], len(self.events))

        code, out = self._run(
            [
                "--store-path",
                str(self.target_path),
                "import-session",
                "--in",
                str(dump),
                "--format",
                "json",
            ]
        )
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["event_count"], len(self.events))

        with SQLiteEventStore(self.target_path) as store:
            rebuilt = store.read(self.session_id)
        self.assertEqual(
            [canonical_record_bytes(e) for e in rebuilt],
            [canonical_record_bytes(e) for e in self.events],
        )

    def test_export_of_an_unknown_session_is_not_found(self) -> None:
        code, _ = self._run(
            [
                "--store-path",
                str(self.source_path),
                "export-session",
                "--session-id",
                str(SessionID("sess_" + "0" * 8)),
                "--out",
                str(self.root / "missing.jsonl"),
            ]
        )
        self.assertEqual(code, cli.EXIT_NOT_FOUND)

    def test_import_of_a_missing_file_is_not_found(self) -> None:
        code, _ = self._run(
            [
                "--store-path",
                str(self.target_path),
                "import-session",
                "--in",
                str(self.root / "absent.jsonl"),
            ]
        )
        self.assertEqual(code, cli.EXIT_NOT_FOUND)


if __name__ == "__main__":
    unittest.main()
