"""Live/replay equality through a persistent SQLite store."""

from __future__ import annotations

import tempfile
import unittest

from mpe.fixtures import make_mock_fixtures
from mpe.persistence.store import SQLiteEventStore
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
from mpe.runtime import Clock, Runtime
from mpe.types import SessionID


class ReplayFromDiskTests(unittest.TestCase):
    def test_live_equals_replay_from_disk(self) -> None:
        providers = ProviderSet(
            renderer=MockRenderer(),
            observation=MockKeyboardObservationProvider(),
            interpreter=MockResponseInterpreter(),
            normalizer=MockDomainNormalizer(),
            evaluator=MockEvaluator(),
            scheduler=MockScheduler(),
        )
        fixtures = make_mock_fixtures()
        session_id = SessionID("disk-replay-session")

        with tempfile.TemporaryDirectory() as td:
            path = f"{td}/events.db"
            store = SQLiteEventStore(path)
            clock = Clock()
            runtime = Runtime(store, providers, clock)
            live_state = runtime.run_mock_session(
                program_version=fixtures["program_version"],
                protocol_version=fixtures["protocol_version"],
                task_definition=fixtures["task_definition"],
                block=fixtures["block"],
                content_item=fixtures["content_item"],
                learner_id="learner_001",
                random_seed="seed_0",
                session_id=session_id,
            )
            store.close()

            store2 = SQLiteEventStore(path)
            replayed_state = Replay(store2).replay(session_id)
            store2.close()

        self.assertEqual(live_state.as_dict(), replayed_state.as_dict())
