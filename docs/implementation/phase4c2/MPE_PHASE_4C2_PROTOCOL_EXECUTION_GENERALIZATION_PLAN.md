# MPE Phase 4C.2 — Protocol Execution Generalization Plan

**Document:** `docs/implementation/phase4c2/MPE_PHASE_4C2_PROTOCOL_EXECUTION_GENERALIZATION_PLAN.md`  
**Type:** Planning and design reconciliation (documentation only)  
**Date:** 2026-07-24  
**Builds on:** Phase 4C.1 Minimal Protocol Vertical Slice (Immediate Recall)  
**Status:** Repository-reconciled; no `PROVISIONAL_DESIGN_MAPPING` labels remain  

> **This is a planning document.** No production code is written, no Git action is taken, and no `mpe_audio`, EEG, ASR, live TTS, spaced-repetition scheduler, Hebrew/Piano adapter, or broad protocol framework is introduced. The plan is grounded in the actual repository state and contracts.

---

## 1. Repository verification record

The following files were inspected to produce this revised plan:

- `docs/project/PROJECT_STATE.md`
- `docs/project/NEXT_TASK.md`
- `docs/implementation/phase4c1/MPE_PHASE_4C1_MINIMAL_PROTOCOL_VERTICAL_SLICE_PLAN.md`
- `docs/implementation/phase4c1/MPE_PHASE_4C1_IMPLEMENTATION_REPORT.md`
- `docs/implementation/phase4c1/MPE_PHASE_4C1_CLOSURE_RECORD.md`
- `packages/mpe/src/mpe/protocol/immediate_recall.py`
- `packages/mpe/src/mpe/protocol/fixture_minimal.py`
- `packages/mpe/src/mpe/protocol/providers.py`
- `packages/mpe/src/mpe/protocol/summary.py`
- `packages/mpe/src/mpe/protocol/__init__.py`
- `packages/mpe/src/mpe/cli.py`
- `packages/mpe/src/mpe/cli_helpers.py`
- `packages/mpe/src/mpe/runtime.py`
- `packages/mpe/src/mpe/events.py`
- `packages/mpe/src/mpe/aggregates.py`
- `packages/mpe/src/mpe/providers.py`
- `packages/mpe/src/mpe/enums.py`
- `packages/mpe/src/mpe/types.py`
- `packages/mpe/src/mpe/event_store.py`
- `packages/mpe/tests/test_protocol_immediate_recall.py`

Verification state from Phase 4C.1 closure is unchanged because no source was modified:

- `PYTHONPATH=packages/mpe/src python3 -m unittest discover -s packages/mpe/tests -p 'test_*.py'` — 111 tests, 0 failures, 1 skipped.
- `.venv/bin/ruff check packages/mpe/src packages/mpe/tests` — all checks passed.
- `PYTHONPATH=packages/mpe/src .venv/bin/mypy packages/mpe/src` — no issues found in 25 source files.

---

## 2. Actual symbol and contract map

Every symbol below was verified in the local repository. No `PROVISIONAL_DESIGN_MAPPING` labels remain.

| Concept | Verified repository symbol | Path | Current responsibility |
|---|---|---|---|
| Runtime orchestrator | `Runtime` | `packages/mpe/src/mpe/runtime.py` | Creates/starts/completes sessions; emits and validates canonical `Event` instances; applies events to `RuntimeState`; replay is external. |
| Runtime state | `RuntimeState` | `packages/mpe/src/mpe/aggregates.py` | Mutable aggregate reconstructed by applying events (`apply()`); tracks `trials`, `blocks`, `session_status`, `terminal`. |
| Event envelope | `Event` | `packages/mpe/src/mpe/events.py` | Immutable frozen dataclass with `event_id`, `event_type`, `payload`, `provenance`, `trial_id`, `block_id`, etc. |
| Supported events | `SUPPORTED_EVENT_TYPES` | `packages/mpe/src/mpe/events.py` | Closed set including `session_created`, `trial_created`, `instruction_started`, `instruction_completed`, `stimulus_requested`, `stimulus_ready`, `response_window_opened`, `observation_received`, `captured_response_created`, `response_interpreted`, `domain_response_normalized`, `evaluation_completed`, `feedback_started`, `feedback_completed`, `block_completed`, `session_completed`, `schedule_decision`, `protocol_terminated`. |
| Event payload schemas | `PAYLOAD_SCHEMAS` | `packages/mpe/src/mpe/events.py` | Per-event required/optional field rules; extra payload keys are permitted. |
| Event store | `EventStore` (protocol), `InMemoryEventStore`, `SQLiteEventStore` | `packages/mpe/src/mpe/event_store.py`, `packages/mpe/src/mpe/persistence/store.py` | Append, read by `session_id`, `get_last_sequence`. |
| Replay | `Replay` | `packages/mpe/src/mpe/replay.py` | Reconstructs `RuntimeState` from persisted events. |
| Provider set | `ProviderSet` (dataclass) | `packages/mpe/src/mpe/providers.py` | Aggregates `Renderer`, `ObservationProvider`, `ResponseInterpreter`, `DomainNormalizer`, `Evaluator`, `Scheduler` instances passed to `Runtime`. |
| Provider protocols | `Renderer`, `ObservationProvider`, `ResponseInterpreter`, `DomainNormalizer`, `Evaluator`, `Scheduler` | `packages/mpe/src/mpe/providers.py` | Typed Python `Protocol`s defining capabilities + one operation each. |
| Content item | `ContentItem` | `packages/mpe/src/mpe/providers.py` | Immutable data passed to `Evaluator` as the expected answer. |
| Trial context | `TrialContext` | `packages/mpe/src/mpe/providers.py` | Metadata passed to `Evaluator`. |
| Scheduling context | `SchedulingContext` | `packages/mpe/src/mpe/providers.py` | Passed to `Scheduler.select_next`; not used by Immediate Recall. |
| Immediate Recall fixture | `ImmediateRecallFixture`, `FixtureItem`, `FixtureAsset` | `packages/mpe/src/mpe/protocol/fixture_minimal.py` | Typed, domain-neutral fixture carrying `content_item_id`, `expected_relation`, `self_confirmation`, `latency`, and role-versioned assets. |
| Adaptation rule | `AdaptationRule` | `packages/mpe/src/mpe/protocol/fixture_minimal.py` | A single typed dataclass with `repeat_cap` and `latency_bound`. |
| Immediate Recall runner | `ImmediateRecallRunner`, `run_immediate_recall_session` | `packages/mpe/src/mpe/protocol/immediate_recall.py` | Protocol-specific executor that drives `Runtime` to emit the full trial event sequence. |
| Immediate Recall outcome | `ItemOutcome`, `ImmediateRecallResult` | `packages/mpe/src/mpe/protocol/immediate_recall.py` | Per-item and per-session runtime artifacts, not persisted. |
| Immediate Recall providers | `FixtureRenderer`, `FixtureObservationProvider`, `FixtureResponseInterpreter`, `FixtureResponseNormalizer`, `SelfConfirmationEvaluator`, `NoOpScheduler` | `packages/mpe/src/mpe/protocol/providers.py` | Fixture-backed provider implementations that satisfy the `ProviderSet` contract. |
| Event-derived summary | `derive_protocol_summary`, `ProtocolSummary`, `ItemSummary` | `packages/mpe/src/mpe/protocol/summary.py` | Reads a session's event stream and produces an Immediate-Recall-specific summary. |
| CLI | `mpe.cli.main`, `_build_parser`, `cmd_run_immediate_recall`, `cmd_show_protocol_summary` | `packages/mpe/src/mpe/cli.py` | Flat subcommand pattern; `--store-path`, `--format`, `--learner-id`, `--random-seed`; exit codes 0, 2, 3, 4, 5, 6. |
| CLI helpers | `run_immediate_recall`, `load_protocol_summary` | `packages/mpe/src/mpe/cli_helpers.py` | Shared entry points used by CLI commands. |
| Canonical enums | `InstructionType`, `ResponseMode`, `AnswerStatus`, `ObservationType`, `InterpretationType`, `FeedbackType`, `FeedbackCategory`, `EvaluationStatus`, etc. | `packages/mpe/src/mpe/enums.py` | Already-defined values for event payloads. |

---

## 3. MindTune architectural invariants

The following invariants are binding for Phase 4C.2:

1. **EVENT-FIRST.** All runtime state is derived from the immutable event stream.
2. **BEHAVIOR IS AUTHORITATIVE FOR CORRECTNESS.** The learner's observable response, not latency or EEG, determines correctness.
3. **LATENCY IS AN ADAPTATION PROXY, NEVER A CORRECTNESS SIGNAL.** Latency may trigger a bounded retry; it does not change `answer_status`.
4. **EEG AND DERIVED FEATURES ARE CONTEXT, NOT COMMAND.** No EEG signal may cause a protocol decision.
5. **PERSIST EVENTS; DERIVE STATE, OUTCOMES, AND SUMMARIES.** No second source of truth.
6. **NO SECOND DSL.** Protocols are typed data consumed by existing code, not textual/interpreted languages.
7. **DO NOT ABSTRACT BEFORE EVIDENCE.** A shared runner or helper may only be extracted after concrete duplication is demonstrated by at least two protocols.
8. **CURRICULUM AND PROTOCOL DEFINITIONS ARE VERSIONED AND IMMUTABLE.** Fixture and program/protocol version ids are carried on events.
9. **KEEP DOMAIN SEMANTICS OUT OF THE MPE CORE.** MPE core (`Runtime`, `EventStore`, `Replay`, provider contracts) is domain-agnostic; protocol meaning lives in provider implementations and event-derived summaries.
10. **NO HIDDEN ADAPTATION.** Every adaptation is explicit, bounded, deterministic, event-recorded, and auditable.
11. **EVERY ADAPTATION MUST BE BOUNDED, EXPLICIT, DETERMINISTIC, EVENT-RECORDED, AND AUDITABLE.** The `trial_created` `repeat_count`/`adaptation_source`/`cap` fields satisfy this for Immediate Recall.
12. **A SECOND PROTOCOL IS EVIDENCE, NOT AN EXCUSE FOR A FRAMEWORK.** Recognition is used only to observe real duplication.
13. **REUSE EXISTING RUNTIME CONTRACTS BEFORE CREATING NEW EXECUTION INFRASTRUCTURE.** `Runtime`, `EventStore`, `Replay`, and provider `Protocol`s are sufficient.
14. **THE SMALLEST SUFFICIENT ABSTRACTION IS PREFERRED TO A GENERAL INTERPRETER.** Prefer ordinary functions and typed dataclasses over generic interpreters, registries, or rule engines.

---

## 4. Cloud-plan overreach audit

The original cloud plan proposed ten abstractions. Each is classified against the actual repository.

| # | Proposed abstraction | Actual repository symbol(s) | Current responsibility | Proposed responsibility | Evidence supporting extraction | Risk of premature abstraction | Final classification |
|---|---|---|---|---|---|---|---|
| 1 | Data-driven primitive interpreter | No matching contract exists. `InstructionType` is an enum; there is no primitive interpreter or state machine. | N/A | Execute steps from a closed primitive vocabulary (Play, Pause, Expect, Confirm, Repeat, Branch, Transition, Wait, Observe, Score, Record). | None in repository. Immediate Recall uses direct Python method calls in `ImmediateRecallRunner._execute_item_trial`. | A generic interpreter is a second DSL and a new execution engine. It duplicates `Runtime` responsibilities and would require a new grammar. | **D. PREMATURE_ABSTRACTION_REMOVE_FROM_PHASE_4C2** |
| 2 | Protocol registry | No registry exists. `ImmediateRecallFixture` is a single typed dataclass; `cli.py` dispatches to `cmd_run_immediate_recall`. | N/A | Map `protocol_id` → typed protocol definition and drive execution. | Only one protocol exists. A registry for one or two protocols is unnecessary indirection. | Becomes a broad framework element; encourages open-ended protocol taxonomy. | **D. PREMATURE_ABSTRACTION_REMOVE_FROM_PHASE_4C2** |
| 3 | Declarative bounded rule-set | `AdaptationRule` is a single two-field dataclass (`repeat_cap`, `latency_bound`) used by `ImmediateRecallRunner`. | Encodes Immediate Recall's bounded repeat policy. | General rule engine accepting arbitrary declarative rules (conditions, actions, caps). | One rule shape only (`repeat_cap` + `latency_bound`). No second rule shape yet. | A general rule-set is a DSL. Conditions/actions can encode protocol semantics and bypass explicit code. | **D. PREMATURE_ABSTRACTION_REMOVE_FROM_PHASE_4C2** |
| 4 | Generic executor | No generic executor exists. `ImmediateRecallRunner` is the only protocol runner. | N/A | Execute any protocol expressed as typed data. | Only one protocol exists. The `Runtime` already provides generic session/trial/event orchestration. | Generic executor presumes duplication before Recognition is built; likely a framework. | **C. SECOND_PROTOCOL_EVIDENCE_REQUIRED** |
| 5 | Protocol definition data model | `ImmediateRecallFixture` is the only protocol definition. `FixtureItem` includes Immediate-Recall-specific fields (`self_confirmation`, `latency`). | N/A | Generic protocol definition schema. | Only one protocol exists. The current model is intentionally Immediate-Recall-specific. | A generic model would force premature unification of unlike concepts. | **C. SECOND_PROTOCOL_EVIDENCE_REQUIRED** |
| 6 | Observation-shape abstraction | `ObservationProvider` Protocol and `ObservationType` enum already exist. `FixtureObservationProvider` is one implementation. | Generic contract: `start_listening`, `stop_listening`, `inject`, `poll` returning observations as dicts. | New abstraction over observation shapes. | The existing contract is already protocol-agnostic; only payload semantics differ. | Adding a new abstraction layer is unnecessary; providers already hide semantics. | **A. EXISTING_REPOSITORY_CONTRACT_REUSED_UNCHANGED** |
| 7 | Adaptation-rule representation | `AdaptationRule` (single dataclass). | Immediate Recall's bounded repeat rule. | General rule representation. | One rule only. | See row 3. | **C. SECOND_PROTOCOL_EVIDENCE_REQUIRED** |
| 8 | Summary generalization | `ProtocolSummary` / `ItemSummary` are Immediate-Recall-specific; `derive_protocol_summary` hard-codes self-confirmation/repeat/cap semantics. | Derive Immediate Recall summary from events. | Generic summary derivation for any protocol. | Only one summary shape exists. The event-derived pattern is generic, but the summary fields are protocol-specific. | Generic summary would force a lowest-common-denominator or schema-driven model. | **C. SECOND_PROTOCOL_EVIDENCE_REQUIRED** |
| 9 | Event additions | `SUPPORTED_EVENT_TYPES` / `PAYLOAD_SCHEMAS` already support the entire trial lifecycle. | Existing event vocabulary. | New generalized event vocabulary. | All required events already exist; only optional payload fields need to be added. | No new event types are needed. | **A. EXISTING_REPOSITORY_CONTRACT_REUSED_UNCHANGED** |
| 10 | CLI additions | `mpe.cli` flat subcommand pattern with `run-immediate-recall` and `show-protocol-summary`. | One protocol's CLI surface. | Generic `run-protocol` / `show-protocol-summary` commands, or per-protocol commands. | Existing pattern is per-protocol. A generic command requires a registry/interpreter (see row 2). | Generic CLI is a framework and a second DSL. | **A for per-protocol commands; D for generic CLI.** |

**Summary:** only two proven generic assets exist now: the existing `Runtime`/`EventStore`/`Replay`/provider contracts and the existing event vocabulary. Everything else must be deferred until Recognition is implemented and real duplication is measured.

---

## 5. No-second-DSL audit

A representation is a second DSL if it introduces a protocol-authoring language with its own interpreter semantics, branching grammar, or independent execution model beside the existing `Runtime` contracts.

| Proposed representation | Is it a DSL? | Reason | Phase 4C.2 disposition |
|---|---|---|---|
| Per-protocol typed fixture dataclasses (e.g., `ImmediateRecallFixture`) | No | Ordinary Python dataclasses consumed by ordinary Python code. No grammar, parser, or separate execution model. | Retain; create analogous `RecognitionFixture` if needed. |
| Typed `AdaptationRule` per protocol | No | A small dataclass with fixed fields used directly by the runner. No grammar or open-ended conditions. | Retain per protocol. |
| Generic primitive interpreter | Yes | Defines a primitive vocabulary, branching, and independent execution semantics. | Remove. |
| Protocol registry with generic lookup and dispatch | Yes | Introduces an indirection layer that is itself a minimal execution model (id → definition → runner). | Remove; explicit per-protocol CLI entry points only. |
| Declarative bounded rule-set engine | Yes | A condition/action language that can encode control flow outside Python. | Remove; keep per-protocol typed rules. |
| Generic protocol definition schema / generic `Protocol` model | Borderline / Yes if coupled to generic executor | If it only normalizes common metadata (version ids, block id, item list) it is typed config. If it drives a generic executor it becomes a schema language. | Allowed only as lightweight, non-executed typed metadata; must not drive a generic interpreter. |

**Conclusion:** Phase 4C.2 will use ordinary typed Python dataclasses and functions. It will not introduce a parser, expression evaluator, generic state machine, rule language, or open-ended primitive interpreter.

---

## 6. Immediate Recall responsibility decomposition

Based on `packages/mpe/src/mpe/protocol/immediate_recall.py` and its provider set:

| Responsibility | Generic / reusable | Protocol-specific | Repository evidence |
|---|---|---|---|
| Session lifecycle (`session_created` → `session_started` → `session_completed`) | Generic | — | `Runtime.create_session`, `start_session`, `complete_session`. Used identically by `run_mock_session` and `ImmediateRecallRunner`. |
| Block lifecycle (`block_started`, `block_completed`) | Generic | — | `Runtime.emit` with `block_id`; `aggregates.py` handlers. |
| Trial lifecycle (`trial_created` → feedback → next) | Generic skeleton | Protocol-specific ordering of steps inside a trial | `Runtime.emit` with `trial_id` is generic; the six-step sequence inside `_execute_item_trial` is Immediate-Recall-specific. |
| Item iteration and repeat insertion | Candidate helper after Recognition | Immediate Recall's specific repeat policy | `plan = list(self.fixture.items)` + `plan.insert(index+1, item)` driven by `AdaptationRule`. |
| Stimulus request/render (`stimulus_requested`, `stimulus_ready`) | Generic pattern | Asset roles (`prompt`, `confirmation`) are protocol semantics | `_emit_stimulus` emits the same events for both roles; the role is payload data. |
| Response window (`response_window_opened`) | Generic | Accepted response modes and window text are protocol-specific | `Runtime.emit` is generic; payload values differ. |
| Observation collection | Generic contract | Observation payload semantics (positive/negative) | `ObservationProvider.poll()` returns dict; `FixtureObservationProvider` encodes Immediate Recall semantics. |
| Response pipeline (`captured_response_created` → `response_interpreted` → `domain_response_normalized`) | Generic | Interpreter/normalizer payload shapes | `ImmediateRecallRunner` calls `providers.interpreter.interpret` and `normalizer.normalize`; both are passthrough for self-confirmation. |
| Evaluation | Generic contract | Correctness mapping | `Evaluator.evaluate` maps payload to `AnswerStatus`; `SelfConfirmationEvaluator` maps `positive`/`negative`. |
| Feedback (`feedback_started`, `feedback_completed`) | Generic event shape | Feedback category/type and content item id | `FeedbackCategory.KNOWLEDGE`, `FeedbackType.CORRECT_ANSWER` chosen by Immediate Recall. |
| Adaptation policy | Generic concept of bounded repeat | Rule shape and trigger (negative or slow) | `AdaptationRule` + `should_repeat` logic in `ImmediateRecallRunner`. |
| Outcome interpretation (`positive`/`negative`/`unresolved`) | — | Immediate Recall-specific | `ItemOutcome` and `_outcome_from` in `summary.py` hard-code self-confirmation semantics. |
| Summary derivation | Generic pattern (walk events) | Summary fields and outcome mapping | `derive_protocol_summary` is Immediate-Recall-specific. |
| CLI command | Generic pattern (subcommand) | Command name and summary formatting | `cmd_run_immediate_recall` / `cmd_show_protocol_summary` are specific. |

**Key insight:** the generic layer is already present in `Runtime`, `EventStore`, `Replay`, `ProviderSet`, and the closed event vocabulary. The Immediate Recall runner is a thin, protocol-specific orchestration layer above it.

---

## 7. Minimal Recognition comparative probe

### 7.1 Purpose

Recognition is the only second protocol allowed in Phase 4C.2. It serves as a comparative design probe to see whether real duplication justifies extracting any shared helper, and if so, what the smallest such helper is.

### 7.2 Domain-neutral fixture shape (tentative, typed)

A `RecognitionFixture` would contain items such as:

```python
@dataclass(frozen=True)
class RecognitionFixtureItem:
    content_item_id: str
    target_media_handle: str
    distractor_media_handles: list[str]
    correct_choice_index: int
    latency: float
    expected_relation: str
    assets: dict[str, FixtureAsset]

@dataclass(frozen=True)
class RecognitionFixture:
    fixture_id: str
    protocol_id: str
    protocol_version_id: str
    program_id: str
    program_version_id: str
    task_definition_id: str
    block_id: str
    block_type: str
    items: list[RecognitionFixtureItem]
```

This is **not** a new DSL. It is an ordinary typed dataclass analogous to `ImmediateRecallFixture`.

### 7.3 Trial sequence (Recognition-specific)

1. `trial_created` for the item.
2. `instruction_started` / `instruction_completed` — present the choice array.
3. `stimulus_requested` / `stimulus_ready` — render the target and distractor options (one or multiple `stimulus_ready` events, each with `asset_role="option_N"`).
4. `response_window_opened` — accept a `TOUCH` selection.
5. `observation_received` — the learner selects an option index. Payload is the selected integer.
6. `captured_response_created`, `response_interpreted`, `domain_response_normalized`.
7. `evaluation_completed` — compare selected index to `correct_choice_index`; produce `CORRECT`/`INCORRECT`.
8. `feedback_started` / `feedback_completed`.

This differs from Immediate Recall in the **stimulus presentation** (multiple options instead of cue-then-confirmation) and the **observation/evaluation semantics** (selected option vs self-confirmation).

### 7.4 Providers

A `RecognitionFixtureProviderSet` would implement the same `ProviderSet` contract:

- `Renderer`: returns one or more `stimulus_ready` events for the option assets.
- `ObservationProvider`: returns the fixture-selected index and latency.
- `ResponseInterpreter` / `DomainNormalizer`: passthrough, interpreting the selected index.
- `Evaluator`: maps selected index to `correct_choice_index`, producing `CORRECT`/`INCORRECT`.
- `Scheduler`: `NoOpScheduler` placeholder.

### 7.5 Bounded adaptation

The same `AdaptationRule` shape (`repeat_cap`, `latency_bound`) could apply if Recognition uses the same bounded-repeat policy (wrong or slow → repeat once). That is a design decision to be confirmed during Gate 1. If it differs, the rule remains protocol-specific.

### 7.6 Summary

`RecognitionSummary` would derive from events:

- per-item `selected_index`, `correct_index`, `correct` (bool), `repeats_used`;
- total `correct_count`, `repeats`;
- `outcome` based on correctness and repeat cap.

It is expected to share only the event-walking pattern with `derive_protocol_summary`; the field mapping is protocol-specific.

---

## 8. Duplication evidence matrix

This matrix records **predictions** to be validated after Gate 1. No extraction is authorized before Gate 2.

| Candidate shared component | Immediate Recall pattern (current) | Recognition predicted pattern | Predicted duplication | Gate 2 decision basis |
|---|---|---|---|---|
| Item iteration helper | `while index < len(plan)` + `plan.insert(index+1, item)` for bounded repeat | Likely identical if Recognition also uses bounded repeat. | High if repeat policy matches; low otherwise. | Extract a small typed helper only if the loop and repeat insertion are verbatim. |
| Trial creation helper | `runtime.emit("trial_created", ...)` with `content_item_ids`, `task_definition_id`, `repeat_count` | Same event, different `content_item_ids` and optional `repeat_count`. | High — event payload structure identical. | A helper that emits `trial_created` with provenance is likely justified. |
| Stimulus request/render helper | `_emit_stimulus` calls `runtime.emit("stimulus_requested")`, `providers.renderer.render`, `runtime.emit("stimulus_ready")` | Same sequence, multiple options. | High for the single-option case; option loop may be specific. | Extract a single-stimulus helper; keep option-array loop specific. |
| Response window helper | `runtime.emit("response_window_opened", ...)` | Same event. | High. | Likely a small helper can emit the window. |
| Observation collection helper | `observation.inject(...)` + `observation.poll()` + `runtime.emit("observation_received")` | Same contract; different inject/poll semantics. | High shape; low payload semantics. | Generic helper for the emit step only; provider-specific prep stays separate. |
| Response pipeline helper | `captured_response_created` → `response_interpreted` → `domain_response_normalized` | Same pipeline. | High. | A function that runs the three emits with a provider set is likely justified. |
| Evaluation emit helper | `providers.evaluator.evaluate(...)` + `runtime.emit("evaluation_completed")` | Same. | High. | Likely a small helper. |
| Feedback emit helper | `feedback_started` → `feedback_completed` | Same. | High. | Likely a small helper. |
| Adaptation rule | `AdaptationRule(repeat_cap, latency_bound)` with `negative or slow` trigger | May be `wrong or slow` trigger with same cap. | High if cap/latency shape reused; low if trigger differs. | Extract a tiny `should_repeat(outcome, rule, cap_reached)` predicate only if trigger logic is identical. |
| Summary event walker | `derive_protocol_summary` walks `trial_created`, `observation_received`, `evaluation_completed`, `feedback_completed` | Same event types, different field extraction. | High pattern; low field semantics. | A generic "read session events" utility already exists (`store.read`); do not create a schema-driven summary engine. |
| CLI command pattern | `cmd_run_immediate_recall`, `cmd_show_protocol_summary` | `cmd_run_recognition`, `cmd_show_recognition_summary`. | High boilerplate. | A helper that runs a runner and prints a summary is likely justified, but command registration stays per-protocol. |

**Acceptable Gate 2 outcomes:**

- `NO_SHARED_RUNNER_EXTRACTION_YET`: if Recognition is simple enough that copy/adapt is clearer.
- Extract a small `protocol_runner.py` module containing event-emitting helpers, but keep protocol-specific step ordering in `ImmediateRecallRunner` and `RecognitionRunner`.

---

## 9. Two-gate implementation sequence

### GATE 1 — Implement minimal Recognition slice with explicit duplication

1. Create `packages/mpe/src/mpe/protocol/fixture_recognition.py` with `RecognitionFixture`, `RecognitionFixtureItem`, `default_recognition_fixture()`.
2. Create `packages/mpe/src/mpe/protocol/providers_recognition.py` with `RecognitionRenderer`, `RecognitionObservationProvider`, `RecognitionResponseInterpreter`, `RecognitionNormalizer`, `RecognitionEvaluator`, and `RecognitionProviderSet`.
3. Create `packages/mpe/src/mpe/protocol/recognition.py` with `RecognitionRunner` that explicitly copies/adapts the Immediate Recall runner structure.
4. Create `packages/mpe/src/mpe/protocol/summary_recognition.py` with `RecognitionSummary` and `derive_recognition_summary`.
5. Add CLI commands `run-recognition` and `show-recognition-summary` in `cli.py` / `cli_helpers.py`.
6. Add `packages/mpe/tests/test_protocol_recognition.py`.
7. Run full test suite, ruff, mypy. Ensure no `schedule_decision` usage and no new event types.

During Gate 1, **do not** extract shared helpers. Tolerate limited duplication.

### GATE 2 — Minimal extraction decision

After Gate 1:

1. Compare `ImmediateRecallRunner` and `RecognitionRunner` line by line.
2. Identify verbatim duplicated sequences of event emissions.
3. Extract only the smallest helpers that remove real duplication:
   - candidate: `_emit_trial_created`;
   - candidate: `_emit_single_stimulus`;
   - candidate: `_emit_response_window`;
   - candidate: `_emit_observation`;
   - candidate: `_emit_response_pipeline`;
   - candidate: `_emit_evaluation`;
   - candidate: `_emit_feedback`.
4. If step ordering is the only difference, keep two separate `run_item_trial` methods.
5. If item iteration and bounded repeat are identical, extract a typed `BoundedItemIterator`.
6. If no substantial duplication exists, record `NO_SHARED_RUNNER_EXTRACTION_YET` and stop.

**Gate 2 must not begin until Gate 1 is complete and reviewed.**

---

## 10. NO_SHARED_RUNNER_EXTRACTION_YET outcome

This is an explicitly valid result of Phase 4C.2.

If Recognition shows that the only shared code is already provided by `Runtime`/`EventStore`/`Replay`/provider contracts, and that the two protocol runners differ in step ordering, observation semantics, evaluation mapping, and summary interpretation, then the correct decision is to keep two separate protocol-specific runners.

In that case, the phase still produces value:

- a second protocol (Recognition) is implemented and tested;
- the boundaries between generic Runtime and protocol-specific runner are confirmed;
- future extraction has concrete evidence to build from.

The final recommendation in that case is `APPROVE_PHASE_4C2_IMPLEMENTATION_WITH_CONDITIONS`, with the condition that extraction is deferred.

---

## 11. Events, persistence, replay, CLI, and tests impact analysis

### 11.1 Events

- No new event types are required.
- Existing events will be reused with additive payload fields:
  - `trial_created`: may carry `repeat_count`, `adaptation_source`, `cap` on repeats;
  - `stimulus_ready`: `asset_role` values may include `option_0`, `option_1`, etc.;
  - `observation_received`: payload will be the selected option index for Recognition;
  - `evaluation_completed`: `answer_status` will be `correct`/`incorrect` based on option comparison.
- All payload additions are optional and backward-compatible with `PAYLOAD_SCHEMAS`.

### 11.2 Persistence and replay

- `InMemoryEventStore` and `SQLiteEventStore` require no changes.
- `Replay` requires no changes.
- `RuntimeState` requires no changes.
- `Recognition` events replay through the existing `Runtime` without modification.

### 11.3 CLI

- Add `run-recognition` and `show-recognition-summary` subcommands mirroring the Immediate Recall pattern.
- Preserve existing exit codes and single-document JSON output.
- Do not add a generic `run-protocol` command or protocol registry.

### 11.4 Tests

- Add `packages/mpe/tests/test_protocol_recognition.py`.
- Cover: successful execution, correct/wrong responses, bounded repeat (if applicable), persistence round-trip, replay equality, summary derivation, asset version pins, no EEG/provider access, CLI success/exit codes.
- If Gate 2 extracts helpers, add unit tests for each helper.
- Existing `test_protocol_immediate_recall.py` must continue to pass unchanged.

---

## 12. Scope exclusions

Phase 4C.2 explicitly excludes:

- Implementation during this planning task.
- Any third protocol (no Silent Production, no Recognition Recall as a separate category, no Delayed Recall).
- A generic primitive interpreter.
- A broad protocol registry.
- An open-ended rule engine or declarative rule-set DSL.
- A scheduler component or `schedule_decision` usage.
- Spaced repetition.
- Hebrew or Piano adapters.
- Audio provider, live TTS, or `mpe_audio` integration.
- EEG, ASR, or physiological-signal dependencies.
- Protocol composition, taxonomy-wide coverage, or counterfactual replay.
- A textual or implicit protocol DSL.
- Modification of `PROJECT_STATE.md`, `NEXT_TASK.md`, canonical MPE docs, or canonical registries.
- Dependency installation.
- Git commit or push.

---

## 13. Disk implementation handoff checklist

Before implementation begins, the following must be true:

- [ ] Gate 1 plan is approved by the user.
- [ ] `docs/implementation/phase4c2/` contains the approved plan.
- [ ] No `PROVISIONAL_DESIGN_MAPPING` labels remain.
- [ ] `PROJECT_STATE.md` and `NEXT_TASK.md` are not modified during implementation.
- [ ] No changes to `docs/MPE_*.md`, `docs/specification/v1.1/*.md`, canonical registries, or `mpe/events.py` `SUPPORTED_EVENT_TYPES` without an ADR.
- [ ] `packages/mpe/src/mpe/protocol/` is the target package.
- [ ] `packages/mpe/tests/test_protocol_recognition.py` is the target test file.
- [ ] Full test suite, ruff, and mypy are run after every increment.

---

## 14. Acceptance criteria

The Phase 4C.2 plan is acceptable if and only if:

- it is based on actual repository inspection;
- all provisional mappings are resolved to real symbols;
- the MindTune Architectural Invariants are explicit;
- Recognition is the only candidate second protocol;
- no generic interpreter, broad registry, or rule engine is authorized;
- bounded duplication is explicitly allowed;
- abstraction follows evidence (two-gate sequence);
- a `NO_SHARED_RUNNER_EXTRACTION_YET` outcome remains valid;
- no source or test code is changed in this planning task;
- no second DSL is introduced.

---

## 15. Final recommendation

APPROVE_PHASE_4C2_IMPLEMENTATION_WITH_CONDITIONS

**Conditions:**

1. Implement Gate 1 (minimal Recognition) before any extraction.
2. Perform Gate 2 extraction only if concrete, verbatim duplication is demonstrated.
3. If no substantial duplication exists, record `NO_SHARED_RUNNER_EXTRACTION_YET`.
4. Do not introduce a generic interpreter, protocol registry, rule engine, or textual DSL.
5. Preserve all architectural invariants and existing runtime contracts.
