"""Property and invariant tests for MPE core."""

from __future__ import annotations

import unittest

from mpe.demo import run_demo


class InvariantTests(unittest.TestCase):
    def test_sequence_numbers_never_decrease(self) -> None:
        _live_state, events, _replayed, _store = run_demo()
        prev = 0
        for event in events:
            self.assertGreater(event.session_sequence_number, prev)
            prev = event.session_sequence_number

    def test_completed_session_cannot_emit_normal_flow_events(self) -> None:
        # The mock flow ends with session_completed; no trial events follow it.
        _live_state, events, _replayed, _store = run_demo()
        terminal_idx = next(
            i for i, e in enumerate(events) if e.event_type == "session_completed"
        )
        after_terminal = events[terminal_idx + 1:]
        for event in after_terminal:
            self.assertNotIn(event.event_type, {"trial_created", "response_window_opened"})

    def test_evaluation_follows_domain_normalization(self) -> None:
        _live_state, events, _replayed, _store = run_demo()
        types = [e.event_type for e in events]
        eval_idx = types.index("evaluation_completed")
        norm_idx = types.index("domain_response_normalized")
        self.assertLess(norm_idx, eval_idx)

    def test_captured_response_follows_observation(self) -> None:
        _live_state, events, _replayed, _store = run_demo()
        types = [e.event_type for e in events]
        cap_idx = types.index("captured_response_created")
        obs_idx = types.index("observation_received")
        self.assertLess(obs_idx, cap_idx)
