from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import sys

CONSOLE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CONSOLE_DIR))

import server


class BehavioralEventStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.eeg = self.root / "eeg"
        self.behavioral = self.root / "behavioral"
        self.eeg.mkdir()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def params(self) -> dict:
        return {
            "persist_without_eeg": True,
            "behavioral_session_id": "conjugation-test-session",
            "annotation_type": "conjugation_response",
            "event": {
                "event_id": "answer-1",
                "timestamp": "2026-07-19T10:00:00Z",
                "ok": True,
                "expected": "אכל",
            },
            "study_context": {"test": "hebrew_conjugations"},
        }

    def test_persists_without_eeg_and_is_idempotent(self) -> None:
        with (
            patch.object(server, "BEHAVIORAL_EVENTS", self.behavioral),
            patch.object(server, "MAC_SESSIONS", self.eeg),
            patch.object(server, "mac_status", return_value={"phase": "idle"}),
        ):
            first = server.append_task_event(self.params())
            second = server.append_task_event(self.params())

        self.assertTrue(first["recorded"])
        self.assertFalse(first["deduplicated"])
        self.assertEqual(first["storage"], "local_behavioral")
        self.assertTrue(second["deduplicated"])
        rows = (self.behavioral / "conjugation-test-session.events.jsonl").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(rows), 1)
        self.assertEqual(json.loads(rows[0])["behavioral_event_id"], "answer-1")

    def test_active_eeg_writes_only_the_eeg_sidecar(self) -> None:
        csv_path = self.eeg / "session_conjugation.csv"
        csv_path.write_text("sample\n", encoding="utf-8")
        status = {"phase": "recording", "csv": str(csv_path), "condition": "hebrew_conjugations"}
        with (
            patch.object(server, "BEHAVIORAL_EVENTS", self.behavioral),
            patch.object(server, "MAC_SESSIONS", self.eeg),
            patch.object(server, "mac_status", return_value=status),
            patch.object(server, "session_covariates_from_state", return_value={}),
        ):
            result = server.append_task_event(self.params())

        self.assertEqual(result["storage"], "eeg_sidecar")
        self.assertTrue(csv_path.with_suffix(".events.jsonl").exists())
        self.assertFalse(self.behavioral.exists())


if __name__ == "__main__":
    unittest.main()
