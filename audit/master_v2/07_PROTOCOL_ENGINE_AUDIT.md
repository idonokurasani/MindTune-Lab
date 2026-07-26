# 07 — Protocol Engine Audit

## 1. MPE v1.1 Implementation

`packages/mpe/` is the canonical MindTune Protocol Engine.

### Modules

| Module | Purpose | Status |
|---|---|---|
| `runtime.py` | `Runtime`, `Clock`, `Outcome`, event emission, mock session runner | Production |
| `events.py` | `Event` envelope, `SUPPORTED_EVENT_TYPES`, `PAYLOAD_SCHEMAS` | Production |
| `event_store.py` | `EventStore` Protocol + `InMemoryEventStore` | Production |
| `replay.py` | `Replay.replay(session_id)` | Production |
| `aggregates.py` | `RuntimeState` and per-event handlers | Production |
| `validation.py` | State transition and event payload validation | Production |
| `providers.py` | Provider Protocol classes + mock implementations | Production |
| `types.py` | Strongly-typed ID wrappers + `make_id` | Production |
| `enums.py` | Canonical enums (`SessionStatus`, `CognitiveState`, `DecisionType`, etc.) | Production |
| `cli.py` | `mpe` CLI (`run-mock-session`, `replay`, `list-sessions`, `inspect-state`, `export-events`) | Production |

## 2. Protocol Runners

| Runner | File | Status | Notes |
|---|---|---|---|
| Immediate Recall | `mpe/protocol/immediate_recall.py` | Production | Closed-loop adaptation of `response_deadline` |
| Recognition | `mpe/protocol/recognition.py` | Production | Recognition protocol |
| Fixture Minimal | `mpe/protocol/fixture_minimal.py` | Production | Domain-neutral fixture and `AdaptationRule` |
| Trial Pipeline | `mpe/protocol/trial_pipeline.py` | Production | Domain-agnostic trial event emission |

## 3. Determinism

- `Clock` advances by fixed step (`runtime.py:60-70`).
- `Runtime.emit()` assigns `session_sequence_number = last_seq + 1` and validates monotonicity.
- `EventStore.append()` validates `expected_version`, `session_sequence_number`, timestamp ordering, and provenance existence.
- `BoundedRepeatPlan` is deterministic and terminates due to `cap` (`bounded_repeat.py`).

## 4. Test Evidence

- `packages/mpe/tests/test_event_store.py` validates append, concurrency, and ordering.
- `packages/mpe/tests/test_replay.py` validates `Replay` reconstructs state.
- `packages/mpe/tests/test_protocol_immediate_recall.py` validates the Immediate Recall runner.
- `packages/mpe/tests/test_state_machines.py` validates lifecycle transitions.
- 224 tests passed in `packages/mpe/tests/` during the audit.

## 5. Disposition

**KEEP** — `packages/mpe/` is the strongest candidate for migration into V2. The main gap is persistent backend variety (only in-memory by default; SQLite experiments in `persistence/`).
