"""Replay determinism tests."""

from __future__ import annotations

import unittest

from mpe.aggregates import RuntimeState
from mpe.demo import run_demo
from mpe.replay import Replay


class ReplayTests(unittest.TestCase):
    def test_full_replay_matches_live_state(self) -> None:
        live_state, events, replayed_state, _store = run_demo()
        self.assertEqual(live_state.as_dict(), replayed_state.as_dict())
        self.assertEqual(len(events), 23)

    def test_repeated_replay_is_equal(self) -> None:
        live_state, _events, _replayed, store = run_demo()
        session_id = live_state.session_id
        first = Replay(store).replay(session_id)
        second = Replay(store).replay(session_id)
        self.assertEqual(first.as_dict(), second.as_dict())

    def test_partial_replay_of_first_events(self) -> None:
        live_state, events, _replayed, store = run_demo()
        session_id = live_state.session_id
        partial = store.read(session_id, from_seq=1, to_seq=3)
        state = RuntimeState()
        for event in partial:
            state.apply(event)
        self.assertEqual(state.session_status.value, "started")
        self.assertFalse(state.terminal)
