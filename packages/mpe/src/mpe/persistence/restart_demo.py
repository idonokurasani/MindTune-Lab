"""Idempotent persistence/restart demonstration.

Run once to create and persist a mock session; run again on the same database
path (e.g., in a separate Docker container) to replay and verify state equality.
"""

from __future__ import annotations

import os
import sys
import uuid
from contextlib import contextmanager

from mpe.aggregates import RuntimeState
from mpe.event_store import InMemoryEventStore
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

SESSION_ID = SessionID("phase4b2-restart-demo-session")
LEARNER_ID = "learner_001"
RANDOM_SEED = "seed_0"


@contextmanager
def _deterministic_uuids():
    """Make uuid.uuid4 deterministic across the demo lifetime."""
    counter = 0
    original = uuid.uuid4

    def _uuid4() -> uuid.UUID:
        nonlocal counter
        counter += 1
        return uuid.UUID(int=counter)

    uuid.uuid4 = _uuid4
    try:
        yield
    finally:
        uuid.uuid4 = original


def _make_providers() -> ProviderSet:
    return ProviderSet(
        renderer=MockRenderer(),
        observation=MockKeyboardObservationProvider(),
        interpreter=MockResponseInterpreter(),
        normalizer=MockDomainNormalizer(),
        evaluator=MockEvaluator(),
        scheduler=MockScheduler(),
    )


def _expected_state() -> RuntimeState:
    """Compute the expected terminal state deterministically in memory."""
    providers = _make_providers()
    fixtures = make_mock_fixtures()
    store = InMemoryEventStore()
    runtime = Runtime(store, providers, Clock())
    runtime.run_mock_session(
        program_version=fixtures["program_version"],
        protocol_version=fixtures["protocol_version"],
        task_definition=fixtures["task_definition"],
        block=fixtures["block"],
        content_item=fixtures["content_item"],
        learner_id=LEARNER_ID,
        random_seed=RANDOM_SEED,
        session_id=SESSION_ID,
    )
    return runtime.state


def _write_session(store: SQLiteEventStore) -> RuntimeState:
    """Execute the mock session and persist it."""
    providers = _make_providers()
    fixtures = make_mock_fixtures()
    runtime = Runtime(store, providers, Clock())
    runtime.run_mock_session(
        program_version=fixtures["program_version"],
        protocol_version=fixtures["protocol_version"],
        task_definition=fixtures["task_definition"],
        block=fixtures["block"],
        content_item=fixtures["content_item"],
        learner_id=LEARNER_ID,
        random_seed=RANDOM_SEED,
        session_id=SESSION_ID,
    )
    return runtime.state


def main() -> int:
    path = os.environ.get("MPE_EVENT_STORE_PATH", "/data/mpe/events.db")

    with _deterministic_uuids():
        with SQLiteEventStore(path) as store:
            if store.get_last_sequence(SESSION_ID) == 0:
                live_state = _write_session(store)
                print(f"Session persisted: {len(store.read(SESSION_ID))} events")
                print(f"Terminal status: {live_state.session_status}")
                return 0

            replayed_state = Replay(store).replay(SESSION_ID)
            expected = _expected_state()

            if replayed_state.as_dict() == expected.as_dict():
                print("Cross-process replay verified: live state equals replayed state")
                print(f"Events replayed: {len(store.read(SESSION_ID))}")
                return 0

            print("LIVE/REPLAY MISMATCH", file=sys.stderr)
            print(f"Expected: {expected.as_dict()}", file=sys.stderr)
            print(f"Replayed: {replayed_state.as_dict()}", file=sys.stderr)
            return 1


if __name__ == "__main__":
    raise SystemExit(main())
