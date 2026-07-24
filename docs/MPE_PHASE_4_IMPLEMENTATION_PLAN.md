# MPE Phase 4 Implementation Plan v1.1

## Audit basis

This plan implements `EXECUTIVE_SYNTHESIS.md` point 7 (Staged Phase 4), `OPEN_QUESTIONS_AND_DECISIONS.md` closed decisions (Phase 4 split, no textual DSL, EEG exploratory), `PROTOCOL_PRIMITIVES_CATALOG.md` Phase 4 allowed primitives, and `SOURCE_CLAIM_AUDIT.md` claim 13 (rejected broad Phase 4).

## Scope

Phase 4 builds the first executable MPE runtime. It is split into three subphases:

- **4A — Protocol Schema:** Define logical and executable entities, JSON/YAML fixtures, validation, versioning.
- **4B — Deterministic Runtime:** Event scheduler, state machine, immutable event stream, replay, provider orchestration.
- **4C — Hebrew Behavioral Integration:** Hebrew `DomainProvider`, `HebrewDomainNormalizer`, `HebrewEvaluator`, `Renderer`, and fixed non-adaptive Hebrew protocols.

No EEG, no adaptation, no textual DSL parser, no sensor interpretation.

## Phase 4A — Protocol Schema

### Objectives

- Separate logical identity (`Program`, `Protocol`) from executable versions (`ProgramVersion`, `ProtocolVersion`).
- Define the schema for `Block`, `TaskDefinition`, `Trial`, `Instruction`, `StimulusRequest`, `ResponseWindow`, `Feedback`, `SafetyRule`.
- Choose JSON/YAML as the authoring format.
- Define schema versioning and migration rules.
- Define validation rules (required fields, prohibited combinations, provider requirements, safety profile references).
- Produce reference fixtures for at least three fixed Hebrew protocols.

### Deliverables

- JSON Schema files for `ProgramVersion` and `ProtocolVersion`.
- At least three validated `ProtocolVersion` fixtures:
  - Vocabulary encoding (no response).
  - Vocabulary recall with button fallback.
  - Morphology exposure.
- Schema validator test suite.
- Documentation of schema migration strategy.

### Exclusions

- No DSL parser.
- No runtime execution.
- No audio rendering.
- No Hebrew correctness logic.
- No adaptation.
- No EEG.

### Dependencies

- `MPE_OBJECT_MODEL_V1_1.md`
- `MPE_EVENT_MODEL_V1_1.md`
- `MPE_PROVIDER_BOUNDARIES.md`
- `MPE_DSL_DECISION_RECORD.md`

### Acceptance criteria

- Every fixture validates against the schema.
- `Program` and `Protocol` fixtures do not contain executable fields.
- `ProgramVersion` and `ProtocolVersion` contain checksums and dependency versions.
- Schema migration can add new optional fields without breaking old fixtures.

### Test strategy

- Schema validation tests.
- Fixture round-trip tests (serialize, deserialize, checksum stable).
- Negative tests for invalid fixtures.

### Stop conditions

- Schema cannot represent the three required protocol types.
- Identity and version separation is violated.
- Executable fields leak into `Program` or `Protocol`.

## Phase 4B — Deterministic Runtime

### Objectives

- Implement an event-driven scheduler with a monotonic session clock.
- Implement a state machine that walks a `ProtocolVersion`.
- Implement immutable event stream append-only storage.
- Implement deterministic replay with a fixed seed and captured observations.
- Implement provider orchestration for `Renderer`, `ObservationProvider`, `ResponseInterpreter`, `DomainNormalizer`, `Evaluator`.
- Implement safety rule execution that overrides all flow.
- Implement session pause/resume/cancel/terminate.

### Deliverables

- Runtime engine module.
- Event store with append-only semantics.
- Deterministic replay harness.
- Provider orchestration bus.
- Safety monitor.
- Unit tests for scheduler, state machine, event store, replay, safety.
- Mock providers for testing.

### Exclusions

- No EEG.
- No adaptation.
- No scheduling policy beyond fixed sequence.
- No textual DSL parser.
- No Hebrew engine integration (use mock `DomainProvider`/`Evaluator`).

### Dependencies

- Phase 4A schema.
- `MPE_OBJECT_MODEL_V1_1.md`
- `MPE_EVENT_MODEL_V1_1.md`
- `MPE_PROVIDER_BOUNDARIES.md`
- `MPE_HEBREW_PROVIDER_CONTRACT.md` (interface only, not implementation).

### Acceptance criteria

- A `ProtocolVersion` can be executed from start to end.
- Every event has a runtime-owned timestamp and provenance.
- Replay with the same seed and observations reproduces the same event sequence.
- Safety rule triggers immediately pause or terminate the session.
- Mock `Evaluator` returns `abstained` for ambiguous inputs and the runtime handles it.

### Test strategy

- Deterministic replay tests.
- Safety override tests.
- Timeout and omission tests.
- Provider failure fallback tests.
- Event stream integrity tests.

### Stop conditions

- Runtime is not deterministic.
- Timestamps are not owned by the runtime.
- Safety rules do not override instruction/feedback flow.
- Replay fails for a simple mock protocol.

## Phase 4C — Hebrew Behavioral Integration

### Objectives

- Wrap the completed Phase 3 Hebrew engine as `HebrewDomainProvider`.
- Implement `HebrewDomainNormalizer` using `hebrew.normalization` and `hebrew.orthography`.
- Implement `HebrewEvaluator` using `hebrew.phase3` confidence and evidence.
- Integrate a TTS or recorded-audio `Renderer`.
- Implement fixed Hebrew protocols for vocabulary encoding, recall, and morphology exposure.
- Support button, typed, and optional speech responses with button fallback.
- Implement delayed recall probe fixtures.

### Deliverables

- `HebrewDomainProvider` module.
- `HebrewDomainNormalizer` module.
- `HebrewEvaluator` module.
- `Renderer` integration (Azure, Piper, or HebTTS/BlueTTS adapter).
- Fixed Hebrew protocol fixtures.
- Integration tests with the 100-verb subset.
- CI regression tests for Hebrew integration.

### Exclusions

- No EEG.
- No adaptation.
- No new Hebrew morphology logic.
- No generic `increase_difficulty`.
- No textual DSL parser.
- No imperatives or weak-root verbs outside the validated 100-verb subset.

### Dependencies

- Phase 4B runtime.
- `hebrew/` engine (Phase 3).
- `MPE_HEBREW_PROVIDER_CONTRACT.md`.
- `data/hebrew/phase3/automatic_gold_100.json`.

### Acceptance criteria

- Hebrew recall trials evaluate responses with `answer_status` (`correct`/`incorrect`/`acceptable_variant`/`partially_correct`/`unevaluable`) and `evaluation_status` (`completed`/`abstained`/`failed`/`out_of_scope`).
- `HebrewEvaluator` returns `evaluation_status` `abstained` or `out_of_scope` for out-of-scope or low-confidence items.
- Runtime handles `abstained` and `failed` evaluations without crashing or fabricating scores.
- Speech responses flow through `CapturedResponse` -> `ResponseInterpretation` -> `DomainNormalizedResponse` before evaluation.
- Pronunciation metadata is advisory and does not affect correctness.
- All 100-verb `verified_consensus` items can be presented and evaluated.

### Test strategy

- Hebrew `Evaluator` unit tests using the 100-verb subset.
- End-to-end Hebrew recall tests with mock and real TTS.
- Abstention handling tests.
- Variant acceptance tests.
- Out-of-scope rejection tests.

### Stop conditions

- Hebrew engine correctness logic leaks into MPE core.
- Latency is computed by `HebrewEvaluator`.
- `abstained` or `failed` evaluations are scored as incorrect.
- Unvalidated imperatives or weak-root forms are presented as authoritative.

## Cross-phase acceptance

Phase 4 is complete when:

1. `Program`/`ProgramVersion` and `Protocol`/`ProtocolVersion` separation is implemented and tested.
2. The runtime executes fixed protocols deterministically and reproducibly.
3. Hebrew responses are evaluated by the Hebrew engine, not MPE core.
4. No EEG, adaptation, or textual DSL parser is present.
5. All tests pass and a simple Hebrew recall session can run end-to-end.

## What comes after Phase 4

- Phase 5A: Behavioral adaptation (spaced retrieval, response-window adjustment, review insertion).
- Phase 5B: Sensor research layer (EEG acquisition, quality gating, feature registry, offline analysis).
- Phase 5C: Experimental sensor-informed policies (only after offline validation).
- Phase 6: Protocol library, longitudinal learning, A/B testing.

## Traceability

This plan implements `EXECUTIVE_SYNTHESIS.md` point 7 (Staged Phase 4) and `OPEN_QUESTIONS_AND_DECISIONS.md` closed decisions (Phase 4 split, no textual DSL, EEG `exploratory_only`). It uses `PROTOCOL_PRIMITIVES_CATALOG.md` §Allowed primitives to define Phase 4 scope and reflects `SOURCE_CLAIM_AUDIT.md` claim 13 (rejected broad Phase 4). Phase 4A scope aligns with `MPE_DSL_DECISION_RECORD.md`; Phase 4C scope aligns with `MPE_HEBREW_PROVIDER_CONTRACT.md`.
