"""Shared utilities for the MPE CLI."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

from mpe.aggregates import RuntimeState
from mpe.event_store import EventStore
from mpe.fixtures import make_mock_fixtures
from mpe.persistence.store import SQLiteEventStore
from mpe.protocol.fixture_minimal import make_minimal_fixture
from mpe.protocol.immediate_recall import run_immediate_recall_session
from mpe.protocol.summary import ProtocolSummary, derive_protocol_summary, summarize_session
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

DEFAULT_STORE_PATH = "/data/mpe/events.db"
ENV_STORE_PATH = "MPE_EVENT_STORE_PATH"


def resolve_store_path(cli_value: str | None) -> Path:
    """Resolve the store path from CLI option, environment, or default."""
    raw = cli_value or os.environ.get(ENV_STORE_PATH) or DEFAULT_STORE_PATH
    return Path(raw).expanduser().resolve(strict=False)


def open_store(path: Path) -> SQLiteEventStore:
    """Open a SQLite event store at the given path."""
    return SQLiteEventStore(path)


def build_mock_providers() -> ProviderSet:
    """Construct the standard mock provider set."""
    return ProviderSet(
        renderer=MockRenderer(),
        observation=MockKeyboardObservationProvider(),
        interpreter=MockResponseInterpreter(),
        normalizer=MockDomainNormalizer(),
        evaluator=MockEvaluator(),
        scheduler=MockScheduler(),
    )


def run_mock_session(
    store: EventStore,
    *,
    session_id: SessionID | None,
    learner_id: str,
    random_seed: str,
) -> RuntimeState:
    """Execute the reference mock session and return the terminal state."""
    providers = build_mock_providers()
    fixtures = make_mock_fixtures()
    clock = Clock()
    runtime = Runtime(store, providers, clock)
    return runtime.run_mock_session(
        program_version=fixtures["program_version"],
        protocol_version=fixtures["protocol_version"],
        task_definition=fixtures["task_definition"],
        block=fixtures["block"],
        content_item=fixtures["content_item"],
        learner_id=learner_id,
        random_seed=random_seed,
        session_id=session_id,
    )


def format_json(data: Any) -> str:
    """Render data as a deterministic JSON string."""
    return json.dumps(data, sort_keys=True, indent=2)


def emit(text: str, file: Any = sys.stdout) -> None:
    """Print text to the given stream."""
    print(text, file=file)


def log_verbose(message: str) -> None:
    """Log a diagnostic line to stderr."""
    print(message, file=sys.stderr)


def replay_session(store: EventStore, session_id: SessionID) -> RuntimeState:
    """Replay a session and return its terminal state."""
    return Replay(store).replay(session_id)


def make_in_memory_reference_state(
    *,
    session_id: SessionID | None,
    learner_id: str,
    random_seed: str,
) -> RuntimeState:
    """Return an independent in-memory terminal state for the mock session.

    This is used by tests to verify that a persisted-and-replayed session
    matches a fresh in-memory execution, up to runtime-generated identifiers.
    """
    from mpe.event_store import InMemoryEventStore

    return run_mock_session(
        InMemoryEventStore(),
        session_id=session_id,
        learner_id=learner_id,
        random_seed=random_seed,
    )


def normalize_state_dict(state_dict: dict[str, Any]) -> dict[str, Any]:
    """Return an ID-agnostic projection of a RuntimeState snapshot.

    Runtime-generated identifiers differ between executions, so this projection
    removes or neutralizes them while preserving deterministic state-machine
    attributes (status, counts, payload-derived values).
    """
    normalized: dict[str, Any] = {
        "session_status": state_dict.get("session_status"),
        "terminal": state_dict.get("terminal"),
        "final_trial_index": state_dict.get("final_trial_index"),
        "learner_id": state_dict.get("learner_id"),
        "program_version_id": state_dict.get("program_version_id"),
        "protocol_version_id": state_dict.get("protocol_version_id"),
        "random_seed": state_dict.get("random_seed"),
        "trial_count": len(state_dict.get("trials", {})),
        "block_count": len(state_dict.get("blocks", {})),
    }

    trials: list[dict[str, Any]] = []
    for _trial_id, trial in sorted(state_dict.get("trials", {}).items()):
        trials.append(
            {
                "status": trial.get("status"),
                "answer_status": trial.get("answer_status"),
                "block_id": trial.get("block_id"),
            }
        )
    normalized["trials"] = trials

    blocks: list[dict[str, Any]] = []
    for _block_id, block in sorted(state_dict.get("blocks", {}).items()):
        blocks.append(
            {
                "block_id": block.get("block_id"),
                "block_type": block.get("block_type"),
                "completed_trial_count": block.get("completed_trial_count"),
                "status": block.get("status"),
            }
        )
    normalized["blocks"] = blocks

    return normalized


def run_immediate_recall(
    store: EventStore,
    *,
    session_id: SessionID | None,
    learner_id: str,
    random_seed: str,
) -> tuple[RuntimeState, ProtocolSummary]:
    """Execute an Immediate Recall session and derive its summary from events."""
    result = run_immediate_recall_session(
        store,
        learner_id=learner_id,
        random_seed=random_seed,
        session_id=session_id,
        fixture=make_minimal_fixture(),
    )
    summary = derive_protocol_summary(
        result.events,
        repeat_cap=result.rule.repeat_cap,
        latency_bound=result.rule.latency_bound,
    )
    return result.state, summary


def load_protocol_summary(
    store: EventStore,
    session_id: SessionID,
) -> ProtocolSummary:
    """Derive an Immediate Recall protocol summary from persisted events."""
    return summarize_session(session_id, store)
