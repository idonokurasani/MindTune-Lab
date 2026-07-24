# MindTune Lab — Testing Strategy

## 1. Purpose

This document defines how MindTune Lab will be tested. It covers unit, integration, event replay, provider, Hebrew, EEG, and performance tests. It is architecture-only; no test code is implemented in Phase 4A.6.

## 2. Testing principles

1. **Events are the source of truth.** Integration and replay tests verify that the event stream correctly reconstructs session state.
2. **Provider boundaries are tested in isolation.** Each provider has a contract test.
3. **Domain engines own their correctness tests.** MPE tests do not assert Hebrew correctness directly.
4. **Safety and failure paths are first-class.** Every failure branch in the walkthroughs must have a test.
5. **Performance is measured, not assumed.** Latency and throughput tests are diagnostic, not gating in Phase 4.

## 3. Test categories

### 3.1 Unit tests

| Target | Scope | Location | Examples |
|---|---|---|---|
| Object construction | Verify every `MPE_OBJECT_MODEL_V1_1.md` object can be instantiated with required fields | `packages/<package>/tests/unit/` | `Session`, `Trial`, `Evaluation` construction |
| Event validation | Verify every event payload passes `SCHEMA_VALIDATION_RULES.md` | `packages/mpe/tests/unit/events/` | `trial_created`, `evaluation_completed` validation |
| Enum validation | Verify canonical enums reject invalid values | `packages/mpe/tests/unit/enums/` | `answer_status`, `evaluation_status`, `instruction_type` |
| Pure functions | Utility functions and state-transition predicates | `packages/<package>/tests/unit/` | Schedule decision helpers, replay reducers |

### 3.2 Integration tests

| Target | Scope | Location | Examples |
|---|---|---|---|
| Runtime + event store | End-to-end session execution with in-memory event store | `tests/integration/` | Hebrew recall session completes and emits expected events |
| Runtime + scheduler | Scheduling policies produce expected `ScheduleDecision` events | `tests/integration/scheduler/` | Single-trial session emits `session_end` |
| Runtime + renderer | `StimulusRequest` flows through renderer and produces `stimulus_ready` | `tests/integration/providers/` | Cue audio render succeeds and fails gracefully |
| Runtime + persistence | Snapshots can be written and restored | `tests/integration/persistence/` | Session state reloads from snapshot + events |

### 3.3 Event replay tests

| Target | Scope | Location | Examples |
|---|---|---|---|
| Full session replay | Given a recorded event stream, reconstruct final state exactly | `tests/replay/` | `sess_vocab_001` from walkthroughs |
| Determinism | Same event stream with same seed produces identical `Outcome` | `tests/replay/` | Recompute `Outcome` twice, compare |
| Partial replay | Replay from snapshot mid-session and continue | `tests/replay/` | Snapshot after `trial_created` + remaining events |
| Branch replay | Replay failure/timeout branches and verify terminal state | `tests/replay/branches/` | Timeout, abstention, provider failure |

### 3.4 Provider tests

| Provider | Test type | Scope | Examples |
|---|---|---|---|
| `KeyboardObservationProvider` | Contract | Produces valid `Observation` for typed input | Payload, quality dimensions, timestamps |
| `HebrewRenderer` | Contract | `StimulusRequest` -> `RenderedStimulus` with valid media handle and duration | Hebrew cue render |
| `TypedTextInterpreter` | Contract | `CapturedResponse` -> `ResponseInterpretation` | Extract typed text |
| `HebrewDomainNormalizer` | Contract + domain | `ResponseInterpretation` -> `DomainNormalizedResponse` | Normalize "ללמוד" |
| `HebrewEvaluator` | Contract + domain | `DomainNormalizedResponse` -> `Evaluation` | Correct/incorrect/partial/variant |

### 3.5 Hebrew tests

| Target | Scope | Location | Examples |
|---|---|---|---|
| Phase 3 gold dataset | All 100 verbs produce expected forms and status | `packages/mpe-hebrew/tests/` | Verify `A_4_למד` infinitive `ללמוד` |
| Accepted variants | Engine recognizes canonical and variant forms | `packages/mpe-hebrew/tests/` | Full/defective spellings, vocalized/unvocalized |
| Abstention | Engine returns `evaluation_status: abstained` for unsupported inputs | `packages/mpe-hebrew/tests/` | Out-of-scope verb form |
| Evidence propagation | `evidence_group`, `scope_status` flow through `Evaluation` | `packages/mpe-hebrew/tests/` | `verified_consensus` on consensus items |

### 3.6 Future EEG / BrainLab tests

| Target | Scope | Location | Examples |
|---|---|---|---|
| Sensor observation ingestion | EEG or sensor data produces valid `SensorObservation` | `packages/brainlab/tests/` | Mock EEG window -> `SensorObservation` |
| State estimate production | Offline model produces `StateEstimate` with uncertainty | `packages/brainlab/tests/` | Drowsiness risk estimate |
| Non-blocking guarantee | `StateEstimate` cannot block `ResponseWindow` or `Evaluation` | `tests/integration/safety/` | Diagnostic estimate does not alter trial flow |

### 3.7 Performance tests

| Target | Scope | Location | Examples |
|---|---|---|---|
| Event throughput | Event append and replay rate under load | `tests/performance/` | 1000 sessions replayed in under N seconds |
| Latency distribution | Trial latency per `task_definition` and `response_mode` | `tests/performance/` | Median typed-response latency |
| Render latency | `StimulusRequest` to `stimulus_ready` latency | `tests/performance/providers/` | Hebrew TTS render latency |
| Memory use | Snapshot and event-store growth | `tests/performance/` | Memory per 100 sessions |

## 4. Test environments

| Environment | Purpose | Notes |
|---|---|---|
| Local | Fast unit and contract tests | No Docker required. |
| Docker compose test | Integration, replay, and provider tests | Defined in `compose/testing.yaml` (future). |
| CI | All tests on every pull request | Future GitHub Actions or equivalent. |
| Research | BrainLab and performance diagnostics | Optional, non-blocking. |

## 5. Test data

| Data source | Use | Notes |
|---|---|---|
| `data/hebrew/phase3/automatic_gold_100.json` | Hebrew provider and evaluator tests | Immutable; do not modify. |
| `data/hebrew/phase3/PHASE_3_FINAL_REPORT.md` | Hebrew test expectations | Immutable; do not modify. |
| Walkthrough event fixtures | Replay and integration tests | Generated from `docs/specification/v1.1/walkthroughs/`. |
| Synthetic fixtures | Edge cases (timeout, failure, abstention) | Created in `tests/fixtures/`. |

## 6. Test-driven workflow

1. For every new feature, write a failing test first.
2. Implement the feature.
3. Run unit tests.
4. Run integration and replay tests.
5. Update documentation.
6. Open a pull request.

## 7. Quality gates

| Gate | When enforced | Phase |
|---|---|---|
| Unit tests pass | Pre-commit and CI | 4B |
| Integration tests pass | CI | 4B |
| Replay tests pass | CI | 4B |
| Schema validation passes | Pre-commit and CI | 4B |
| Hebrew contract tests pass | CI | 4B |
| Lint and type checks pass | Pre-commit and CI | 4B |
| Performance baselines recorded | CI | 5+ |

## 8. Failure taxonomy

Tests should verify these failure categories from `ERROR_MODEL.md`:

- `provider_not_found`
- `render_failed`
- `interpretation_failed`
- `normalization_failed`
- `out_of_scope`
- `evaluation_failed` / `evaluation_abstained`
- `scheduling_failed`
- `response_timeout`
- `safety_rule_triggered`
- `device_error`

## 9. Reporting

Test results should produce:

- JUnit XML for CI.
- Human-readable summary.
- Event-replay diff for failed replay tests.
- Latency distribution artifacts for performance tests.
