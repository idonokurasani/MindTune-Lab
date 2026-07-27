"""Tests for wall-clock recording (SR-M1 WP-2, ADR-0001 sec. 2.6)."""

from __future__ import annotations

import json
import tempfile
import time
import unittest
from pathlib import Path

from mpe.cli_helpers import normalize_state_dict
from mpe.event_store import InMemoryEventStore
from mpe.persistence.store import SQLiteEventStore
from mpe.protocol.recognition import run_recognition_session
from mpe.providers import (
    MockDomainNormalizer,
    MockEvaluator,
    MockKeyboardObservationProvider,
    MockRenderer,
    MockResponseInterpreter,
    MockScheduler,
    ProviderSet,
)
from mpe.replay import Replay
from mpe.runtime import Clock, FixedWallClock, Runtime, SystemWallClock, WallClock
from mpe.types import ProtocolVersionID


def _providers() -> ProviderSet:
    return ProviderSet(
        renderer=MockRenderer(),
        observation=MockKeyboardObservationProvider(),
        interpreter=MockResponseInterpreter(),
        normalizer=MockDomainNormalizer(),
        evaluator=MockEvaluator(),
        scheduler=MockScheduler(),
    )


def _order_independent(normalized: dict[str, object]) -> dict[str, object]:
    """Sort the trial list, whose order follows randomly generated trial ids."""
    trials = normalized.get("trials")
    if isinstance(trials, list):
        normalized = {**normalized, "trials": sorted(trials, key=json.dumps)}
    return normalized


def _runtime(store: InMemoryEventStore, wall_clock: WallClock | None = None) -> Runtime:
    return Runtime(store, _providers(), Clock(), wall_clock)


class WallClockSourceTests(unittest.TestCase):
    def test_system_wall_clock_returns_current_utc_epoch(self) -> None:
        before = time.time()
        value = SystemWallClock().now_utc()
        after = time.time()
        self.assertGreaterEqual(value, before)
        self.assertLessEqual(value, after)

    def test_fixed_wall_clock_is_pinned(self) -> None:
        clock = FixedWallClock(1_700_000_000.0)
        self.assertEqual(clock.now_utc(), 1_700_000_000.0)
        self.assertEqual(clock.now_utc(), 1_700_000_000.0)

    def test_fixed_wall_clock_can_step(self) -> None:
        clock = FixedWallClock(100.0, step=5.0)
        self.assertEqual([clock.now_utc(), clock.now_utc()], [100.0, 105.0])


class RuntimeWallClockTests(unittest.TestCase):
    def setUp(self) -> None:
        self.store = InMemoryEventStore()

    def test_emitted_events_record_wallclock(self) -> None:
        runtime = _runtime(self.store, FixedWallClock(1_700_000_000.0))
        event = runtime.create_session(
            program_version_id="program_v1",
            protocol_version_id=ProtocolVersionID("protocol_v1"),
            learner_id="learner_001",
        )
        self.assertEqual(event.wallclock_at, 1_700_000_000.0)

    def test_default_wall_clock_is_the_system_clock(self) -> None:
        runtime = _runtime(self.store)
        self.assertIsInstance(runtime.wall_clock, SystemWallClock)

        before = time.time()
        event = runtime.create_session(
            program_version_id="program_v1",
            protocol_version_id=ProtocolVersionID("protocol_v1"),
            learner_id="learner_001",
        )
        after = time.time()
        self.assertIsNotNone(event.wallclock_at)
        assert event.wallclock_at is not None
        self.assertGreaterEqual(event.wallclock_at, before)
        self.assertLessEqual(event.wallclock_at, after)

    def test_protocol_clock_is_unaffected_by_the_wall_clock(self) -> None:
        runtime = _runtime(self.store, FixedWallClock(1_700_000_000.0, step=60.0))
        first = runtime.create_session(
            program_version_id="program_v1",
            protocol_version_id=ProtocolVersionID("protocol_v1"),
            learner_id="learner_001",
        )
        second = runtime.start_session(random_seed="seed_0")

        # Sequence 2 is session_provenance_recorded, emitted by create_session.
        self.assertEqual(first.timestamp, 1.0)
        self.assertAlmostEqual(second.timestamp, 1.2)
        self.assertEqual(first.wallclock_at, 1_700_000_000.0)
        self.assertEqual(second.wallclock_at, 1_700_000_120.0)

    def test_two_clocks_are_independent(self) -> None:
        """Protocol time is deterministic; wall time is not derived from it."""
        runtime = _runtime(self.store, FixedWallClock(0.0))
        runtime.create_session(
            program_version_id="program_v1",
            protocol_version_id=ProtocolVersionID("protocol_v1"),
            learner_id="learner_001",
        )
        event = runtime.start_session(random_seed="seed_0")
        self.assertNotEqual(event.timestamp, event.wallclock_at)


class WallClockPersistenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self._td = tempfile.TemporaryDirectory()
        self.addCleanup(self._td.cleanup)
        self.store_path = Path(self._td.name) / "events.db"

    def test_wallclock_survives_a_persistence_round_trip(self) -> None:
        store = SQLiteEventStore(self.store_path)
        self.addCleanup(store.close)
        result = run_recognition_session(store, wall_clock=FixedWallClock(1_700_000_000.0))

        reloaded = store.read(result.state.session_id)
        self.assertTrue(reloaded)
        for event in reloaded:
            self.assertEqual(event.wallclock_at, 1_700_000_000.0)

    def test_wall_time_does_not_affect_the_replayed_projection(self) -> None:
        """Two runs differing only in wall time produce the same projection."""
        first_store = InMemoryEventStore()
        second_store = InMemoryEventStore()

        first = run_recognition_session(first_store, wall_clock=FixedWallClock(1_700_000_000.0))
        second = run_recognition_session(
            second_store, wall_clock=FixedWallClock(1_900_000_000.0, step=3600.0)
        )

        first_state = Replay(first_store).replay(first.state.session_id)
        second_state = Replay(second_store).replay(second.state.session_id)
        self.assertEqual(
            _order_independent(normalize_state_dict(first_state.as_dict())),
            _order_independent(normalize_state_dict(second_state.as_dict())),
        )

        first_events = first_store.read(first.state.session_id)
        second_events = second_store.read(second.state.session_id)
        self.assertEqual(
            [event.timestamp for event in first_events],
            [event.timestamp for event in second_events],
        )
        self.assertNotEqual(
            [event.wallclock_at for event in first_events],
            [event.wallclock_at for event in second_events],
        )

    def test_replaying_one_stream_twice_is_identical(self) -> None:
        store = SQLiteEventStore(self.store_path)
        self.addCleanup(store.close)
        result = run_recognition_session(store, wall_clock=FixedWallClock(1_700_000_000.0))

        replay = Replay(store)
        self.assertEqual(
            replay.replay(result.state.session_id).as_dict(),
            replay.replay(result.state.session_id).as_dict(),
        )


if __name__ == "__main__":
    unittest.main()
