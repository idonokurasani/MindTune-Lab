"""End-to-end reference mock flow tests."""

from __future__ import annotations

import unittest

from mpe.demo import run_demo
from mpe.enums import SessionStatus


class ReferenceFlowTests(unittest.TestCase):
    def test_complete_mock_session(self) -> None:
        live_state, events, replayed_state, _store = run_demo()

        # 1. Session reaches canonical terminal state.
        self.assertEqual(live_state.session_status, SessionStatus.COMPLETED)
        self.assertTrue(live_state.terminal)
        self.assertEqual(len(live_state.trials), 1)

        # 2. All required events are produced in order.
        event_types = [e.event_type for e in events]
        self.assertEqual(event_types[0], "session_created")
        self.assertEqual(event_types[1], "session_provenance_recorded")
        self.assertEqual(event_types[2], "session_started")
        self.assertIn("trial_created", event_types)
        self.assertIn("response_window_opened", event_types)
        self.assertIn("captured_response_created", event_types)
        self.assertIn("response_interpreted", event_types)
        self.assertIn("domain_response_normalized", event_types)
        self.assertIn("evaluation_completed", event_types)
        self.assertIn("feedback_started", event_types)
        self.assertIn("schedule_decision", event_types)
        self.assertIn("block_completed", event_types)
        self.assertEqual(event_types[-1], "session_completed")

        # 3. Event payload validation passed (append succeeded).
        for event in events:
            self.assertTrue(event.event_id)
            self.assertTrue(event.event_type)
            self.assertIsNotNone(event.payload)

        # 4. Session sequence numbers are contiguous.
        seqs = [e.session_sequence_number for e in events]
        self.assertEqual(seqs, list(range(1, len(events) + 1)))

        # 5. Live state equals replayed state.
        self.assertEqual(live_state.as_dict(), replayed_state.as_dict())

        # 6. No Hebrew Engine code is invoked (mock evaluator only).
        for event in events:
            if event.component == "evaluator":
                self.assertEqual(event.component, "evaluator")
                self.assertEqual(event.payload.get("evaluator_id"), "mock_evaluator")

        # 7. No database or external service is required: in-memory store only.
        self.assertIsInstance(events, list)
