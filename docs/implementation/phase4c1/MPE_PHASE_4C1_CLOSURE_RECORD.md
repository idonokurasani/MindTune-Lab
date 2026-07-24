# MPE Phase 4C.1 — Closure Record

**Date:** 2026-07-24  
**Phase:** MPE Phase 4C.1 — Minimal Protocol Vertical Slice  
**Protocol in scope:** Immediate Recall (`immediate-recall`)  
**Fixture in scope:** `minimal` (`item.alpha`, `item.beta`)  
**Final recommendation:** `APPROVE_MINIMAL_PROTOCOL_VERTICAL_SLICE`

---

## 1. Documents reviewed

- `docs/implementation/phase4c1/MPE_PHASE_4C1_MINIMAL_PROTOCOL_VERTICAL_SLICE_PLAN.md`
- `docs/implementation/phase4c1/MPE_PHASE_4C1_IMPLEMENTATION_REPORT.md`
- `docs/project/PROJECT_STATE.md`
- `docs/project/NEXT_TASK.md`
- `docs/project/AGENTS.md`
- `docs/MPE_ARCHITECTURE_V1_1.md`
- `docs/MPE_EVENT_MODEL_V1_1.md`
- `docs/MPE_PROVIDER_BOUNDARIES.md`
- `docs/MPE_ADAPTATION_CONTRACT.md`

## 2. Implementation files reviewed

- `packages/mpe/src/mpe/protocol/__init__.py`
- `packages/mpe/src/mpe/protocol/fixture_minimal.py`
- `packages/mpe/src/mpe/protocol/providers.py`
- `packages/mpe/src/mpe/protocol/immediate_recall.py`
- `packages/mpe/src/mpe/protocol/summary.py`
- `packages/mpe/tests/test_protocol_immediate_recall.py`
- `packages/mpe/src/mpe/cli.py`
- `packages/mpe/src/mpe/cli_helpers.py`
- `packages/mpe/src/mpe/runtime.py`

## 3. Corrective-audit outcome

Three issues identified in the acceptance review were resolved:

### 3.1 Scheduler / `schedule_decision` scope

- Classification: **A. REQUIRED_EXISTING_RUNTIME_INTERFACE_NO_OP**
- `ImmediateRecallScheduler` was replaced by `NoOpScheduler`.
- `NoOpScheduler` is a never-called provider-set placeholder required only because `mpe.providers.ProviderSet` (and therefore `mpe.runtime.Runtime`) requires a `Scheduler` object.
- It performs no spacing, future scheduling, curriculum selection, or adaptive scheduling.
- The Immediate Recall runner no longer emits `schedule_decision` events. Bounded adaptation metadata is carried on `trial_created` events (`repeat_count`, `adaptation_source`, `cap`).

### 3.2 Behavior-authoritative test isolation

Isolated tests in `packages/mpe/tests/test_protocol_immediate_recall.py` now prove:

- Negative self-confirmation with normal latency causes the bounded repeat.
- Positive self-confirmation with slow latency triggers a repeat but does **not** change correctness.
- Latency is recorded but never determines correctness; only `self_confirmation` does.
- Repeat cap is exactly one.
- Adaptation source and reason are represented accurately (`behavior` vs `latency`).

### 3.3 Final recommendation token

The implementation report was updated to use the allowed token:

```
APPROVE_MINIMAL_PROTOCOL_VERTICAL_SLICE
```

## 4. Verification evidence

```bash
PYTHONPATH=packages/mpe/src python3 -m unittest discover -s packages/mpe/tests -p 'test_*.py'
```

Result: **111 tests, 0 failures, 1 skipped** (pre-existing skip).

```bash
.venv/bin/ruff check packages/mpe/src packages/mpe/tests
```

Result: **All checks passed.**

```bash
PYTHONPATH=packages/mpe/src .venv/bin/mypy packages/mpe/src
```

Result: **Success: no issues found in 25 source files.**

## 5. Scope-conformance summary

- Added files are limited to the `mpe/protocol/` package and `test_protocol_immediate_recall.py`.
- Modified files are limited to:
  - `packages/mpe/src/mpe/cli.py`
  - `packages/mpe/src/mpe/cli_helpers.py`
  - `packages/mpe/src/mpe/runtime.py` (additive optional `start_parameters` only)
- `docs/project/PROJECT_STATE.md` and `docs/project/NEXT_TASK.md` were updated only to record completion and define the next phase.
- No Python source code, tests, or dependencies were changed during the closure documentation step.
- No network, provider API, EEG, ASR, TTS, `mpe_audio`, spaced-repetition, or domain-specific dependency was introduced.

## 6. Git baseline status

The repository was initialized and a baseline commit was created after Phase 4C.1:

```
dc26bada Baseline after MPE Phase 4C.1
```

Working tree is clean.

## 7. Residual limitations

The Phase 4C.1 slice intentionally excludes:

- additional protocols beyond Immediate Recall;
- SpeechGen / provider TTS / `mpe_audio` / live audio synthesis;
- ASR and EEG signals;
- spaced-repetition and adaptive scheduling;
- stochastic policies;
- protocol composition and multi-protocol orchestration;
- counterfactual / EEG-ablation replay;
- durable learning-state / mastery store / curriculum.

These exclusions remain in force until explicitly approved in a later phase.

## 8. Phase 4C.2 dependency

The next phase is **MPE Phase 4C.2 — Protocol Execution Generalization**.

It must be a planning and design-reconciliation phase that:

- analyzes which parts of `ImmediateRecallRunner` are generic and which are protocol-specific;
- decides whether a shared protocol runner is justified;
- identifies a candidate second protocol (preferred: **Recognition**);
- avoids premature abstraction and implementation.

The deliverable is:

```
docs/implementation/phase4c2/MPE_PHASE_4C2_PROTOCOL_EXECUTION_GENERALIZATION_PLAN.md
```

## 9. Final closure token

```
CLOSE_MPE_PHASE_4C1
```
