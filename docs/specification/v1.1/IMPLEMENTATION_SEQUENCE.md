# MPE v1.1 Phase 4A Implementation Sequence

## Scope

This document breaks Phase 4A (Protocol Schema) into small, independently testable milestones with explicit dependencies. It is derived from:

- `MPE_PHASE_4_IMPLEMENTATION_PLAN.md`
- `MPE_OBJECT_MODEL_V1_1.md`
- `MPE_EVENT_MODEL_V1_1.md`
- `MPE_PROVIDER_BOUNDARIES.md`
- `MPE_DSL_DECISION_RECORD.md`

Phase 4A produces executable technical specifications and validated fixtures. It does not include runtime code, database code, SQL migrations, APIs, UI, EEG, adaptation, DSL parser, or Hebrew engine changes.

## Legend

| Tag | Meaning |
|---|---|
| **Normative** | Required by MPE v1.1. |
| **Recommended** | Strongly advised for correctness, performance, or auditability. |
| **Optional** | May be omitted in a minimal implementation. |
| **Out of scope** | Not part of Phase 4A. |
| **Implementation note** | Engineering guidance, not an architectural rule. |

## 1. Phase 4A milestones

### Milestone 1: Canonical schema vocabulary

- **Objective:** Publish machine-readable schema definitions for all canonical enums and identifiers used in Phase 4A.
- **Deliverables:**
  - JSON Schema or equivalent enum registry artifact.
  - Identifier format definitions (UUID/slug, naming conventions).
- **Dependencies:** None.
- **Acceptance criteria:**
  - Every enum in `MPE_CANONICAL_ENUM_REGISTRY.md` is represented.
  - Every identifier in `MPE_CANONICAL_IDENTIFIER_REGISTRY.md` has a name and type.
- **Testability:** Static lint against registry; no runtime needed.

### Milestone 2: Static fixture schema (`Program`, `ProgramVersion`, `Protocol`, `ProtocolVersion`)

- **Objective:** Define JSON/YAML schema for logical and executable identities.
- **Deliverables:**
  - Schema for `Program` and `Protocol` (logical, no executable fields).
  - Schema for `ProgramVersion` and `ProtocolVersion` (immutable, checksum, dependency versions, `protocol_version_sequence`, `block_sequence`/`trial_sequence`).
- **Dependencies:** Milestone 1.
- **Acceptance criteria:**
  - A fixture can be serialized and deserialized round-trip.
  - `Program`/`Protocol` fixtures reject executable fields.
  - `ProgramVersion`/`ProtocolVersion` fixtures contain checksums and dependency versions.
- **Testability:** Schema validation tests (positive and negative).

### Milestone 3: `TaskDefinition` and `Block` fixture schema

- **Objective:** Define schema for reusable task templates and block definitions.
- **Deliverables:**
  - `TaskDefinition` schema (`task_family`, `trial_role_sequence`, `version`).
  - `Block` schema embedded in `ProtocolVersion` (`block_type`, `trial_sequence`/`trial_generator_ref`, `max_trials`, `exit_condition`).
- **Dependencies:** Milestone 2.
- **Acceptance criteria:**
  - `task_family` and `TrialRole` values validate against canonical enums.
  - `block_type` validates against canonical enum.
  - `block_sequence` and `trial_sequence` are mutually exclusive at the `ProtocolVersion` level.
- **Testability:** Fixture round-trip and negative tests.

### Milestone 4: `ContentItem` and `SafetyProfile` fixture schema

- **Objective:** Define schema for domain content and safety rules.
- **Deliverables:**
  - `ContentItem` schema (`content_item_id`, `provider_id`, `provider_version`, `status`, `abstention_status`, `scope`, `accepted_variants`, etc.).
  - `SafetyProfile` schema (`safety_profile_id`, `rules` list with `safety_rule_id`, `trigger_condition`, `severity`, `action_taken`).
- **Dependencies:** Milestone 1.
- **Acceptance criteria:**
  - `ContentItem.status` and `abstention_status` validate correctly.
  - `SafetyProfile` rules reference valid `action_taken` values.
- **Testability:** Schema validation and fixture tests.

### Milestone 5: Event envelope schema

- **Objective:** Define the common event envelope and event type registry.
- **Deliverables:**
  - JSON Schema for common `Event` envelope (`event_id`, `event_type`, `schema_version`, `session_id`, `session_sequence_number`, `protocol_version_id`, `timestamp`, `component`, `provenance`, `sensitive`, `data_classification`, `quality_flags`).
  - Registry of allowed `event_type` values and payload schema versions.
- **Dependencies:** Milestone 1.
- **Acceptance criteria:**
  - `session_sequence_number` is integer and monotonic per session.
  - `timestamp` is non-negative number.
  - `data_classification` validates against canonical enum.
- **Testability:** Envelope validation tests; negative tests for missing fields.

### Milestone 6: Event payload schemas

- **Objective:** Define JSON Schema for every event payload in the canonical taxonomy.
- **Deliverables:**
  - Payload schemas for session lifecycle, block, trial, instruction, stimulus, response pipeline, feedback, safety, schedule, evaluation, evidence, adaptation, and signal-quality events.
- **Dependencies:** Milestone 5, Milestone 2 (for `trial_created` references).
- **Acceptance criteria:**
  - Every canonical event type in `MPE_EVENT_MODEL_V1_1.md` has a payload schema.
  - Payloads reference canonical identifiers and enums.
  - Causal field presence validated (e.g., `captured_response_id` in `response_interpreted`).
- **Testability:** Positive/negative payload tests for each event type.

### Milestone 7: Provider interface schema stubs

- **Objective:** Define input/output schema stubs for each provider operation.
- **Deliverables:**
  - `RendererCapabilities`, `Renderer.render` input/output.
  - `ObservationCapabilities`, `Observation` output.
  - `ResponseInterpreter` capabilities and `interpret` output.
  - `DomainNormalizer` capabilities and `normalize` output.
  - `Evaluator` capabilities and `evaluate` output.
  - `Scheduler` capabilities and `select_next` output.
  - `StateInferenceModel` capabilities and `estimate` output.
- **Dependencies:** Milestones 1, 4, 6.
- **Acceptance criteria:**
  - Every provider input/output matches object model fields.
  - `HebrewEvaluator` input is `DomainNormalizedResponse`, output uses `answer_status`/`evaluation_status`.
- **Testability:** Mock payload validation; no implementation.

### Milestone 8: Response-pipeline fixture validation

- **Objective:** Validate a complete response pipeline through fixtures.
- **Deliverables:**
  - A set of fixtures representing `observation_received` -> `captured_response_created` -> `response_interpreted` -> `domain_response_normalized` -> `evaluation_completed`.
- **Dependencies:** Milestone 6.
- **Acceptance criteria:**
  - Each event's payload schema validates.
  - Identifier references are consistent across the chain.
  - `answer_status`/`evaluation_status` are valid.
- **Testability:** Chain validation test.

### Milestone 9: Three reference protocol fixtures

- **Objective:** Produce and validate three fixed Hebrew protocol fixtures.
- **Deliverables:**
  - Vocabulary encoding (no response).
  - Vocabulary recall with button fallback.
  - Morphology exposure.
- **Dependencies:** Milestones 2, 3, 4, 6.
- **Acceptance criteria:**
  - Each fixture validates against `ProtocolVersion` schema.
  - Each fixture contains valid `TaskDefinition` references.
  - Each fixture declares `required_providers` and `dependency_versions`.
  - No adaptation or EEG fields are present.
- **Testability:** Fixture round-trip and negative tests.

### Milestone 10: Schema migration rules

- **Objective:** Define how schemas can evolve without breaking old fixtures.
- **Deliverables:**
  - Migration policy: additive optional fields only for v1.x.
  - `schema_version` compatibility matrix.
  - Fixture upgrade/downgrade rules.
- **Dependencies:** Milestones 2, 6.
- **Acceptance criteria:**
  - A fixture with an older `schema_version` still validates under the current schema if only optional fields were added.
  - A fixture with a removed required field is rejected.
- **Testability:** Migration test cases.

### Milestone 11: Validation rule suite

- **Objective:** Encode the validation rules from `SCHEMA_VALIDATION_RULES.md` as runnable checks.
- **Deliverables:**
  - Validation suite covering identifier uniqueness, enum validation, foreign-key validity, timestamp ordering, protocol compatibility, provider compatibility, checksum validation, version compatibility.
- **Dependencies:** Milestones 2, 4, 6, 7, 9.
- **Acceptance criteria:**
  - Positive fixtures pass all checks.
  - Negative fixtures fail with specific rule violations.
- **Testability:** Validation suite is itself the test.

### Milestone 12: Traceability and documentation package

- **Objective:** Ensure the specification package is internally consistent and traceable.
- **Deliverables:**
  - Cross-reference table mapping each spec document to object model, event model, provider boundaries, and canonical registries.
  - Updated `docs/specification/v1.1/README.md` listing all documents.
- **Dependencies:** All previous milestones.
- **Acceptance criteria:**
  - Every identifier in specs references canonical registry.
  - Every enum in specs references canonical registry.
  - Every provider references `MPE_PROVIDER_BOUNDARIES.md` or `MPE_HEBREW_PROVIDER_CONTRACT.md`.
  - Every event references `MPE_EVENT_MODEL_V1_1.md`.
  - Every persistent entity references `MPE_OBJECT_MODEL_V1_1.md`.
- **Testability:** Automated cross-reference check.

## 2. Dependency graph

```text
Milestone 1: Canonical vocabulary
  |
  +--> Milestone 2: Static fixture schema (Program/Protocol)
  |      |
  |      +--> Milestone 3: TaskDefinition/Block schema
  |      |
  |      +--> Milestone 4: ContentItem/SafetyProfile schema
  |             |
  |             +--> Milestone 9: Reference protocol fixtures
  |
  +--> Milestone 5: Event envelope schema
         |
         +--> Milestone 6: Event payload schemas
                |
                +--> Milestone 7: Provider interface stubs
                |
                +--> Milestone 8: Response-pipeline fixture validation
                |
                +--> Milestone 10: Schema migration rules
                |
                +--> Milestone 11: Validation rule suite
                       |
                       +--> Milestone 12: Traceability package
```

## 3. Exit criteria for Phase 4A

Phase 4A is complete when:

1. All 12 milestones are completed and their acceptance tests pass.
2. The three reference protocol fixtures validate against the schemas.
3. Identity and version separation is preserved (`Program`/`Protocol` contain no executable fields).
4. No adaptation, EEG, DSL parser, runtime, database, or API code exists.
5. All spec documents reference the canonical registries and contracts.

## 4. What comes next (not in Phase 4A)

- Phase 4B: deterministic runtime, event store, replay, provider orchestration.
- Phase 4C: Hebrew behavioral integration.
- Phase 5A: behavioral adaptation.
- Phase 5B: sensor research layer.
- Phase 5C: experimental sensor-informed policies.

## 5. Implementation notes

- **Recommended:** Each milestone should be a separate pull/merge request with tests.
- **Recommended:** Schema files should be versioned alongside the documents they describe.
- **Recommended:** Negative tests should be at least as numerous as positive tests.
- **Out of scope:** Writing production code, choosing a storage engine, implementing providers, or implementing the runtime.
