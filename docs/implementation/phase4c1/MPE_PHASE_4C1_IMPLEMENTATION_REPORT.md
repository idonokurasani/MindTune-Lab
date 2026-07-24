# MPE Phase 4C.1 — Immediate Recall Minimal Protocol Vertical Slice

## Implementation Report

**Date:** 2026-07-24  
**Repository root:** `/Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console`  
**MPE package:** `packages/mpe`  
**Protocol in scope:** Immediate Recall only (`immediate-recall`)  
**Fixture in scope:** `minimal` (`item.alpha`, `item.beta`)

---

## 1. Summary

This report documents the implementation of the MPE Phase 4C.1 minimal vertical slice for the **Immediate Recall** protocol. The slice executes end-to-end through the existing MPE v1.1 runtime, reusing the `Event`/`EventStore`/`Replay`/`Runtime`/`CLI` contracts and adding only new, additive code. No new DSL, provider, EEG, ASR, scheduler, or audio synthesis code path was introduced.

Key characteristics:

- Exactly one protocol: **Immediate Recall**.
- Domain-neutral fixture: `item.alpha` (positive/fast) and `item.beta` (negative/slow).
- One bounded adaptation rule: repeat once on negative self-confirmation or slow latency, cap = 1.
- Deterministic fixture-driven observation; no live user input, no EEG, no provider API calls.
- Asset-version pins are carried on stimulus events using fixture-local versioned media handles.
- Protocol summary is derived exclusively from persisted events.
- All existing tests continue to pass.

---

## 2. Repository reconciliation

### 2.1 Root and layout

The MPE repository is located at `/Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console`. The runtime package lives under `packages/mpe/src/mpe`, tests under `packages/mpe/tests`. `PROJECT_STATE.md` and `NEXT_TASK.md` exist and were **not modified**.

### 2.2 Contract-symbol mapping

| Conceptual element | Assumed symbol | Verified symbol | Reconciliation |
|---|---|---|---|
| Protocol definition | `Protocol` / `ProtocolStep` | `mpe.protocol.fixture_minimal.ImmediateRecallFixture` | New additive fixture dataclass; no core-contract change. |
| Typed instruction | `Instruction` | `mpe.events.Event` with `instruction_started`/`instruction_completed` | Reused existing events. |
| Stimulus request | `StimulusRequest` | `stimulus_requested` event + `FixtureRenderer` | Reused event; renderer is a new provider. |
| Rendered stimulus | `RenderedStimulus` | `stimulus_ready` event payload | Reused event; added `media_handle`, `asset_version`, `asset_role`, `renderer_id` fields. |
| Observation | `Observation` | `observation_received` event | Reused event; payload carries `self_confirmation` string and `latency` proxy. |
| Adaptation decision | `AdaptationDecision` | `trial_created` event with `repeat_count`, `adaptation_source`, `cap` | Bounded adaptation metadata is carried on the trial itself; no `schedule_decision` event is emitted by the runner. |
| Schedule decision | `ScheduleDecision` | not used in this slice | The `ProviderSet` interface still requires a `Scheduler` slot, but it is filled by a documented no-op stub that is never called. |
| Execution plan | `ExecutionPlan` | In-memory `ImmediateRecallRunner` plan (fixture items + rule) | Not persisted as a core contract. |
| Execution result | `ExecutionResult` | `ImmediateRecallResult` dataclass | Derived from runtime state + events. |
| Protocol summary | `ProtocolSummary` / `SessionSummary` | `mpe.protocol.summary.ProtocolSummary` | New derived summary type. |
| Event store | `EventStore.append` / replay | `InMemoryEventStore` / `SQLiteEventStore` + `Replay` | Reused existing contracts. |
| Asset-version pin | approved-asset registry | Fixture `FixtureAsset.version` | Pinned version carried in `stimulus_ready`/`stimulus_requested` payload. |
| CLI | `mpe` entry point | `mpe run-immediate-recall`, `mpe show-protocol-summary` | Added flat-verb subcommands matching existing style. |

### 2.3 Event reuse / new-event decision

No new persisted event types were introduced. The existing `SUPPORTED_EVENT_TYPES` set in `mpe/events.py` already contains all required event types. The following existing events are emitted:

| # | Event | When | Classification | Payload extensions (additive only) |
|---|---|---|---|---|
| E1 | `session_started` | session begins | existing & reused | `start_parameters.fixture_id` |
| E2 | `instruction_started` / `instruction_completed` | cue presentation | existing & reused | — |
| E3 | `stimulus_requested` / `stimulus_ready` | cue (prompt) | existing + additive payload | `asset_role`, `media_handle`, `asset_version`, `renderer_id` |
| E4 | `instruction_started` / `instruction_completed` | anticipation window | existing & reused | — |
| E5 | `response_window_opened` | self-confirmation window | existing & reused | `response_modes_accepted = ["touch"]` |
| E6 | `observation_received` | deterministic self-confirmation | existing + additive payload | `payload` = `"positive"`/`"negative"`, `latency` = proxy seconds |
| E7 | `captured_response_created`, `response_interpreted`, `domain_response_normalized`, `evaluation_completed` | response pipeline | existing + additive payload | evaluator answer-status maps self-confirmation |
| E8 | `feedback_started` / `feedback_completed` | confirmation presentation | existing & reused | `content_item_id` = item id |
| — | `trial_created` | trial begins | existing + additive payload | `repeat_count` (0 or 1), `adaptation_source` (on repeats), `cap` |
| — | `block_started`, `block_completed`, `session_completed` | protocol lifecycle | existing & reused | — |

`ProtocolSummary` is **derived only** and not persisted.

### 2.4 Scheduler / `schedule_decision` scope

- The `Runtime` constructor accepts a `ProviderSet` dataclass whose `scheduler` field must be populated. The Immediate Recall slice fills this slot with a documented no-op stub, `NoOpScheduler`, that raises if ever called.
- The stub performs no spacing, no future scheduling, no curriculum selection, and no adaptive scheduling.
- The Immediate Recall runner makes all item-selection decisions itself (fixed sequence plus one bounded repeat). No `schedule_decision` event is emitted.
- Bounded adaptation metadata is carried on `trial_created` events (`repeat_count`, `adaptation_source`, `cap`) so that the summary can still be derived from events alone.

### 2.5 CLI reconciliation

Existing CLI conventions were preserved:

- Flat verbs under `mpe`.
- `--store-path`, `--format`, `-v` options.
- Exit codes 0 (success), 2 (usage), 3 (not found), 4 (store invalid), 5 (concurrency), 6 (invariant).
- JSON mode emits one JSON document on stdout.

Two commands were added:

- `mpe run-immediate-recall [--session-id] [--learner-id] [--random-seed] [--format]`
- `mpe show-protocol-summary <session_id> [--format]`

### 2.6 Persistence / replay verification

- `InMemoryEventStore` and `SQLiteEventStore` provide append + read APIs.
- `Replay` reconstructs `RuntimeState` from events.
- Deterministic ordering is guaranteed by monotonic `session_sequence_number` and non-decreasing `timestamp` enforced by both stores and `Runtime.emit`.

### 2.7 Asset-version pin representation

Asset pinning is exercised by `FixtureAsset` carrying `asset_id`, `role`, `media_handle`, and `version`. The renderer returns `asset_version` and `media_handle` in `stimulus_ready`, and `stimulus_requested` carries `asset_role`. Replay reproduces the same pins.

### 2.8 Test commands

- Tests: `PYTHONPATH=packages/mpe/src python3 -m unittest discover -s packages/mpe/tests -p 'test_*.py'`
- Lint: `.venv/bin/ruff check packages/mpe/src packages/mpe/tests`
- Type check: `PYTHONPATH=packages/mpe/src .venv/bin/mypy packages/mpe/src`

---

## 3. Files changed

### 3.1 New files

- `packages/mpe/src/mpe/protocol/__init__.py`
- `packages/mpe/src/mpe/protocol/fixture_minimal.py`
- `packages/mpe/src/mpe/protocol/providers.py`
- `packages/mpe/src/mpe/protocol/immediate_recall.py`
- `packages/mpe/src/mpe/protocol/summary.py`
- `packages/mpe/tests/test_protocol_immediate_recall.py`

### 3.2 Modified files

- `packages/mpe/src/mpe/cli.py` — added `run-immediate-recall` and `show-protocol-summary` commands.
- `packages/mpe/src/mpe/cli_helpers.py` — added `run_immediate_recall` and `load_protocol_summary` helpers.
- `packages/mpe/src/mpe/runtime.py` — added optional `start_parameters` argument to `Runtime.start_session` (additive, backward-compatible).

### 3.3 Files explicitly not changed

- `PROJECT_STATE.md`
- `NEXT_TASK.md`
- `mpe/events.py` (no new event types, no schema-breaking changes)
- `mpe/event_store.py`, `mpe/persistence/store.py`, `mpe/aggregates.py` (existing contracts preserved)

---

## 4. Reused / added contracts

### 4.1 Fixture contract

```python
ImmediateRecallFixture(
    fixture_id="minimal",
    protocol_id="immediate-recall",
    protocol_version_id="immediate-recall-v1.0.0",
    program_id="immediate-recall-program",
    program_version_id="immediate-recall-program-v1.0.0",
    task_definition_id="immediate_recall_self_confirm",
    block_id="minimal-block",
    block_type="practice",
    items=[
        FixtureItem(
            content_item_id="item.alpha",
            expected_relation="associate(item.alpha.prompt, item.alpha.target)",
            self_confirmation="positive",
            latency=0.5,
            assets={...},
        ),
        FixtureItem(
            content_item_id="item.beta",
            expected_relation="associate(item.beta.prompt, item.beta.target)",
            self_confirmation="negative",
            latency=5.0,
            assets={...},
        ),
    ],
)
```

### 4.2 Bounded adaptation rule

```python
AdaptationRule(repeat_cap=1, latency_bound=2.0)
```

Rule: if `self_confirmation == "negative"` or `latency > 2.0`, and `repeats_used < 1`, repeat the item once. Correctness (`positive`/`negative`) is determined solely by the fixture `self_confirmation`; latency is only a retry trigger.

### 4.3 Provider set

- `FixtureRenderer` — deterministic, returns versioned `media_handle`.
- `FixtureObservationProvider` — deterministic self-confirmation `touch_input` observation.
- `FixtureResponseInterpreter` — passthrough interpreter.
- `FixtureResponseNormalizer` — passthrough normalizer.
- `SelfConfirmationEvaluator` — maps `positive` → `correct`, `negative` → `incorrect`.
- `NoOpScheduler` — provider-set placeholder only; raises if invoked.

---

## 5. Event flow

For the default `minimal` fixture the event sequence is deterministic:

1. `session_created`
2. `session_started` (with `start_parameters.fixture_id = "minimal"`)
3. `block_started`
4. For each item:
   - `trial_created` (with `repeat_count`, `adaptation_source`, `cap` on repeats)
   - cue: `instruction_started` → `instruction_completed` → `stimulus_requested` → `stimulus_ready`
   - anticipation: `instruction_started` → `instruction_completed` → `response_window_opened`
   - observation: `observation_received`
   - response pipeline: `captured_response_created` → `response_interpreted` → `domain_response_normalized` → `evaluation_completed`
   - confirmation: `instruction_started` → `instruction_completed` → `stimulus_requested` → `stimulus_ready` → `feedback_started` → `feedback_completed`
5. `block_completed`
6. `session_completed`

Total events for the default fixture: **62**.

---

## 6. Execution example

```bash
PYTHONPATH=packages/mpe/src python3 -m mpe \
  --store-path /tmp/ir_demo.db \
  run-immediate-recall \
  --format json
```

Example JSON output (abridged):

```json
{
  "completed_item_count": 2,
  "event_count": 62,
  "fixture_id": "minimal",
  "item_count": 2,
  "items": [
    {
      "completed": true,
      "content_item_id": "item.alpha",
      "latency": 0.5,
      "outcome": "positive",
      "repeats_used": 0,
      "self_confirmation": "positive"
    },
    {
      "completed": true,
      "content_item_id": "item.beta",
      "latency": 5.0,
      "outcome": "unresolved",
      "repeats_used": 1,
      "self_confirmation": "negative"
    }
  ],
  "latency_bound": 2.0,
  "protocol_id": "immediate-recall-v1.0.0",
  "status": "session_completed",
  "total_repeats": 1,
  "unresolved_count": 1
}
```

Show the same session later:

```bash
PYTHONPATH=packages/mpe/src python3 -m mpe \
  --store-path /tmp/ir_demo.db \
  show-protocol-summary <session_id>
```

---

## 7. Replay and persistence verification

The implementation was verified with SQLite round-trips and `Replay` equality:

```python
from mpe.persistence.store import SQLiteEventStore
from mpe.protocol.immediate_recall import run_immediate_recall_session
from mpe.replay import Replay

store1 = SQLiteEventStore("/tmp/ir_test.db")
result = run_immediate_recall_session(store1)

store2 = SQLiteEventStore("/tmp/ir_test.db")
events = store2.read(result.runtime.state.session_id)
assert events == result.events

replayed_state = Replay(store2).replay(result.runtime.state.session_id)
assert replayed_state.as_dict() == result.state.as_dict()
```

The test suite `test_protocol_immediate_recall.py` contains dedicated tests for persistence round-trip, replay equality, deterministic event ordering, and asset-version pin retention through replay.

---

## 8. Tests

A new test module `packages/mpe/tests/test_protocol_immediate_recall.py` covers the acceptance matrix:

| ID | Test | Status |
|---|---|---|
| T1 | Successful execution (`item.alpha` positive, no repeat) | pass |
| T2 | Repeat on negative confirmation (`item.beta` repeated once) | pass |
| T3 | No repeat on positive confirmation (`item.alpha` never repeats) | pass |
| T4 | Repeat cap enforced (second negative completes unresolved) | pass |
| T5 | Deterministic event order | pass |
| T6 | Persistence round trip | pass |
| T7 | Replay equality | pass |
| T8 | Summary derivation | pass |
| T9 | Asset-version pin retained | pass |
| T10 | No provider access (fixture-only providers) | pass |
| T11 | No EEG influence | pass |
| T12 | CLI success (exit 0, single JSON document) | pass |
| T13 | CLI invalid input (unknown session → exit 3, bad ID → exit 2) | pass |
| — | Negative with normal latency causes the bounded repeat | pass |
| — | Positive with slow latency triggers repeat but stays correct | pass |
| — | Latency never determines correctness / answer status | pass |
| — | Adaptation source (`behavior` vs `latency`) recorded on `trial_created` | pass |
| — | Repeat cap is exactly one | pass |

All tests run with:

```bash
PYTHONPATH=packages/mpe/src python3 -m unittest discover -s packages/mpe/tests -p 'test_*.py'
```

Result: **111 tests, 0 failures, 1 skipped** (pre-existing skip).

---

## 9. Linting and type checking

- **Ruff:** `.venv/bin/ruff check packages/mpe/src packages/mpe/tests` — **All checks passed.**
- **mypy:** `PYTHONPATH=packages/mpe/src .venv/bin/mypy packages/mpe/src` — **Success: no issues found in 25 source files.**

---

## 10. Limitations and exclusions

The implementation intentionally excludes everything listed in §15 of the planning document:

- No additional protocols (only Immediate Recall).
- No Hebrew Lab, Piano Lab, or real domain adapters.
- No SpeechGen / provider TTS / `mpe_audio` / live audio synthesis.
- No ASR, no EEG events or fields.
- No spaced-repetition scheduler or `schedule_decision` usage.
- No stochastic policies; adaptation is deterministic.
- No protocol composition or multi-protocol orchestration.
- No counterfactual / EEG-ablation replay; only event replay.
- No durable learning-state / mastery store / curriculum.
- No changes to `PROJECT_STATE.md` or `NEXT_TASK.md`.

The only core file touched was `mpe/runtime.py`, and the change is a strictly additive optional parameter to `Runtime.start_session`.

---

## 11. FINAL SCOPE-CONFORMANCE AUDIT

### 11.1 Scheduler / `schedule_decision` classification

- Classification: **A. REQUIRED_EXISTING_RUNTIME_INTERFACE_NO_OP**
- The `NoOpScheduler` class in `packages/mpe/src/mpe/protocol/providers.py` exists only because `mpe.providers.ProviderSet` (and therefore `mpe.runtime.Runtime`) requires a `Scheduler`-protocol object.
- It is a deterministic, never-called no-op. Its `select_next` raises `ProviderFailureError` if invoked.
- It does not implement spacing, future scheduling, curriculum selection, or adaptive scheduling.
- The class and its docstring explicitly state that it is a provider-set placeholder and that the runner makes all item-selection decisions directly.
- **No `schedule_decision` event is emitted** by the Immediate Recall runner. Bounded adaptation is recorded on `trial_created` events (`repeat_count`, `adaptation_source`, `cap`).
- `schedule_decision` is therefore **not used as a new protocol scheduling feature** in this slice.

### 11.2 Behavior-versus-latency proof

Isolated tests in `test_protocol_immediate_recall.py` prove:

1. **Negative self-confirmation with normal latency causes the bounded repeat.**
   - Fixture: `item.beta` with `self_confirmation="negative"` and `latency=0.5`.
   - Result: two `trial_created` events for `item.beta`; the repeat's `adaptation_source` is `"behavior"`; final summary outcome is `unresolved` (negative, cap reached).

2. **Positive self-confirmation with slow latency triggers a repeat but does not change correctness.**
   - Fixture: `item.beta` with `self_confirmation="positive"` and `latency=5.0`.
   - Result: two `trial_created` events; the repeat's `adaptation_source` is `"latency"`; all `evaluation_completed` events for the item have `answer_status="correct"`; final summary outcome is `positive`.

3. **Latency never determines correctness.**
   - Correctness is derived from `self_confirmation` only: `positive` → `answer_status="correct"`, `negative` → `answer_status="incorrect"`.
   - The slow positive item is repeated once (bounded attention/retry policy) but remains `positive`.

4. **Repeat cap remains exactly one.**
   - The default `AdaptationRule(repeat_cap=1, latency_bound=2.0)` is enforced for both behavior-driven and latency-driven repeats.
   - Tests assert at most two `trial_created` events per item and `repeat_count == 1` for the second trial.

5. **Adaptation source and reason are represented accurately.**
   - `adaptation_source` is `"behavior"` when `self_confirmation == "negative"`.
   - `adaptation_source` is `"latency"` when `self_confirmation == "positive"` but `latency > latency_bound`.
   - `cap` is `1` on repeat trials.

### 11.3 Final verification results

```bash
PYTHONPATH=packages/mpe/src python3 -m unittest discover -s packages/mpe/tests -p 'test_*.py'
# 111 tests, 0 failures, 1 skipped

.venv/bin/ruff check packages/mpe/src packages/mpe/tests
# All checks passed

PYTHONPATH=packages/mpe/src .venv/bin/mypy packages/mpe/src
# Success: no issues found in 25 source files
```

### 11.4 Diff / scope audit

- No Git repository is present at the project root, so a Git diff cannot be produced.
- Added files are limited to the `mpe/protocol/` package and `test_protocol_immediate_recall.py`.
- Modified files are limited to:
  - `packages/mpe/src/mpe/cli.py`
  - `packages/mpe/src/mpe/cli_helpers.py`
  - `packages/mpe/src/mpe/runtime.py` (additive optional parameter only)
- `PROJECT_STATE.md` and `NEXT_TASK.md` were not changed.
- No network, provider, EEG, ASR, TTS, `mpe_audio`, spaced-repetition, or domain-specific dependency was introduced.

### 11.5 Final allowed recommendation

APPROVE_MINIMAL_PROTOCOL_VERTICAL_SLICE
