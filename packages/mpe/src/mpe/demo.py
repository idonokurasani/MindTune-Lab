"""Executable demonstration of the Phase 4B.1 MPE core mock flow."""

from __future__ import annotations

from mpe.aggregates import RuntimeState
from mpe.event_store import InMemoryEventStore
from mpe.events import Event
from mpe.fixtures import make_mock_fixtures
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


def run_demo() -> tuple[RuntimeState, list[Event], RuntimeState, InMemoryEventStore]:
    """Execute and replay the mock session, returning live state, events, replayed state, and the store."""

    providers = ProviderSet(
        renderer=MockRenderer(),
        observation=MockKeyboardObservationProvider(),
        interpreter=MockResponseInterpreter(),
        normalizer=MockDomainNormalizer(),
        evaluator=MockEvaluator(),
        scheduler=MockScheduler(),
    )

    fixtures = make_mock_fixtures()

    store = InMemoryEventStore()
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
    )

    session_id = runtime.state.session_id
    assert session_id is not None
    events = store.read(session_id)
    replayed_state = Replay(store).replay(session_id)

    return live_state, events, replayed_state, store


def main() -> None:
    live_state, events, replayed_state, _store = run_demo()

    print("=" * 70)
    print("MindTune MPE Phase 4B.1 — Mock Session Demonstration")
    print("=" * 70)
    print(f"Events emitted: {len(events)}")
    print(f"Session status (live):    {live_state.session_status}")
    print(f"Session status (replay):  {replayed_state.session_status}")
    print(f"Trial count (live):       {len(live_state.trials)}")
    print(f"Trial count (replay):     {len(replayed_state.trials)}")
    print(f"Terminal (live):          {live_state.terminal}")
    print(f"Terminal (replay):        {replayed_state.terminal}")

    live_dict = live_state.as_dict()
    replay_dict = replayed_state.as_dict()
    match = live_dict == replay_dict
    print(f"Live/Replay state match:  {match}")

    if not match:
        print("\nLIVE:")
        print(live_dict)
        print("\nREPLAY:")
        print(replay_dict)
        raise SystemExit(1)

    print("\nCanonical event sequence:")
    for event in events:
        print(f"  {event.session_sequence_number:2d}  {event.event_type}")

    print("\nLive execution and deterministic replay produced the same terminal")
    print("MPE state without requiring changes to the approved MPE v1.1 architecture.")


if __name__ == "__main__":
    main()
