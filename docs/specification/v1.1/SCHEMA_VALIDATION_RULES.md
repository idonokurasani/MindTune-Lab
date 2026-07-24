# MPE v1.1 Schema Validation Rules Specification

## Scope

This document enumerates the validation rules that must be applied to MPE v1.1 objects and events. It is derived from:

- `MPE_OBJECT_MODEL_V1_1.md`
- `MPE_EVENT_MODEL_V1_1.md`
- `MPE_CANONICAL_ENUM_REGISTRY.md`
- `MPE_CANONICAL_IDENTIFIER_REGISTRY.md`
- `MPE_PROVIDER_BOUNDARIES.md`
- `MPE_ADAPTATION_CONTRACT.md`
- `MPE_HEBREW_PROVIDER_CONTRACT.md`

No implementation language or validation library is specified.

## Legend

| Tag | Meaning |
|---|---|
| **Normative** | Required by MPE v1.1. |
| **Recommended** | Strongly advised for correctness, performance, or auditability. |
| **Optional** | May be omitted in a minimal implementation. |
| **Out of scope** | Not part of Phase 4A. |
| **Implementation note** | Engineering guidance, not an architectural rule. |

## 1. Identifier validation

### 1.1 Identifier uniqueness

- **Normative:** Every primary identifier field (`*_id`) must be unique within its owning table/event type.
- **Normative:** `event_id` must be globally unique across all events.
- **Normative:** `session_sequence_number` must be unique within a `session_id`.
- **Recommended:** Identifiers should be UUID v4 or ULID. Slugs are permitted for logical identities (`program_id`, `protocol_id`).

### 1.2 Identifier naming

- **Normative:** Primary identifiers must follow `<object>_id` naming from `MPE_CANONICAL_IDENTIFIER_REGISTRY.md`.
- **Normative:** References to an object must use the same canonical identifier name as the object's primary key.
- **Normative:** Generic `id` fields are prohibited as primary identifiers.

### 1.3 Foreign-key validity

- **Normative:** Every foreign-key reference must point to an existing record of the correct type.
- **Normative:** Event `provenance` entries must reference existing `event_id`s in the same `session_id`.
- **Recommended:** Event payloads should validate that referenced `trial_id`, `block_id`, `response_window_id`, etc., exist in the current session context.

### 1.4 Logical vs executable identity separation

- **Normative:** `Program` and `Protocol` must not contain executable fields (`protocol_version_sequence`, `block_sequence`, `trial_sequence`, `required_providers`, `safety_profile_id`, `schema_version`, `dependency_versions`).
- **Normative:** `ProgramVersion` must reference an existing `Program` via `program_id`.
- **Normative:** `ProtocolVersion` must reference an existing `Protocol` via `protocol_id`.

## 2. Enum validation

### 2.1 Canonical enum values

- **Normative:** Every enum field must contain a value listed in `MPE_CANONICAL_ENUM_REGISTRY.md`.
- **Normative:** Required enum fields must not be null.
- **Recommended:** Optional enum fields may be null or omitted; if present, must be valid.

### 2.2 Enum-specific rules

| Enum | Validation rule |
|---|---|
| `session_status` | Must follow allowed transitions from `MPE_CANONICAL_ENUM_REGISTRY.md`. |
| `response_requirement` | Must be `required`, `optional`, or `none`. |
| `answer_status` | Must be `correct`, `incorrect`, `acceptable_variant`, `partially_correct`, or `unevaluable`. |
| `evaluation_status` | Must be `completed`, `abstained`, `failed`, or `out_of_scope`. |
| `deployment_status` | Must be `exploratory_only`, `shadow_mode`, `limited_runtime`, or `production_approved`. |
| `adaptation_decision` | Must be `APPLY`, `NO_CHANGE_INSUFFICIENT_EVIDENCE`, `REVERSE`, or `ABSTAIN`. |
| `transfer_claim_level` | Must be `trained_task_performance`, `item_generalization`, `near_transfer`, `far_transfer`, or `clinical_outcome`. |
| `protocol_purpose` | Must be one of the eight canonical values. |
| `instruction_type` | Must be one of the eight canonical values. |
| `feedback_category` | Must be `KNOWLEDGE`, `PERFORMANCE`, or `METACOGNITIVE`. |
| `feedback_type` | Must be one of the six canonical values. |
| `observation_type` | Must be one of the seven canonical values. |
| `interpretation_type` | Must be `asr_transcript`, `button_label`, `typed_text`, or `selected_option`. |
| `response_mode` | Must be `button`, `voice`, `typed`, or `recognition`. |
| `error_category` | Must be one of the canonical values. |
| `scope_status` / `content_item_status` | Must be `verified_consensus`, `high_confidence_candidate`, `unresolved`, or `rejected`. |
| `block_type` | Must be one of the seven canonical values. |
| `safety_action_taken` | Must be `pause`, `terminate`, `volume_limit`, `offer_end`, or `insert_recovery`. |
| `severity` | Must be `info`, `warning`, or `critical`. |
| `decision_status` | Must be `made` or `abstained`. |
| `decision_type` (ScheduleDecision) | Must be `next_trial`, `next_block`, `session_end`, `insert_review`, or `offer_break`. |
| `task_family` | Must be one of the nine canonical values. |
| `data_classification` | Must be `public`, `consent_gated`, `sensitive_phi`, or `research_sensitive`. |

## 3. Timestamp and ordering validation

### 3.1 Runtime timestamp monotonicity

- **Normative:** `timestamp` in the event envelope must be non-decreasing within a `session_id`.
- **Normative:** `timestamp` must count active session time; paused intervals must not be counted.
- **Recommended:** `timestamp` should be strictly increasing except for concurrent observation events.

### 3.2 Component timestamp validity

- **Normative:** Component timestamps inside `payload` (`rendered_at`, `received_at`, `captured_at`, `completed_at`, `extracted_at`, `reported_at`) are non-authoritative and may drift but must be non-negative.
- **Recommended:** Component timestamps should not be earlier than `session_started.timestamp`.

### 3.3 Session sequence ordering

- **Normative:** `session_sequence_number` must be strictly monotonic per `session_id` with no gaps.
- **Normative:** If event B references event A in `provenance`, `session_sequence_number(B) > session_sequence_number(A)`.

### 3.4 Causal ordering

- **Normative:** `captured_response_created` must not occur before `response_window_opened` in the same trial.
- **Normative:** `response_interpreted` must not occur before `captured_response_created` for the same `response_window_id`.
- **Normative:** `domain_response_normalized` must not occur before `response_interpreted` for the same `response_window_id`.
- **Normative:** `evaluation_completed`/`abstained`/`failed` must not occur before `domain_response_normalized` or `response_interpreted` for the same `response_window_id`.
- **Normative:** `feedback_started` must not occur before `evaluation_completed` for the same `trial_id`.

## 4. Protocol compatibility

### 4.1 Program/Protocol version compatibility

- **Normative:** `Session.program_version_id` must match `Session.protocol_version_id` through `program_version.protocol_version_sequence`.
- **Normative:** `ProtocolVersion.required_providers` must all be available at session start.
- **Normative:** `ProtocolVersion.dependency_versions` must match the actual provider versions in use.
- **Normative:** `ProtocolVersion.schema_version` must be supported by the runtime.

### 4.2 Block and trial sequence validation

- **Normative:** `ProtocolVersion` must contain exactly one of `block_sequence` or `trial_sequence`.
- **Normative:** Every `block_id` and `task_definition_id` referenced must exist.
- **Normative:** Every `content_item_id` referenced in a `ProtocolVersion` trial plan must exist in the domain provider or fixture set.

### 4.3 Transfer claim compatibility

- **Normative:** `ProtocolVersion.primary_transfer_claim` must be equal to or more conservative than `Program.transfer_claim_level`. It must not be less validated than the program allows.
- **Recommended:** A protocol with `far_transfer` or `clinical_outcome` must reference a program that permits it.

## 5. Provider compatibility

### 5.1 Provider capability matching

- **Normative:** At session start, the runtime must call `capabilities()` for every `ProtocolVersion.required_providers` entry.
- **Normative:** Provider `*_version` must match `ProtocolVersion.dependency_versions` for that provider.
- **Normative:** Provider-supported response modes, content types, and observation types must cover the protocol's requirements.

### 5.2 Response mode compatibility

- **Normative:** `Trial.accepted_response_modes` must be a subset of the `ObservationProvider` capabilities.
- **Normative:** `ResponseWindow.response_modes_accepted` must be compatible with `Trial.accepted_response_modes`.
- **Normative:** `CapturedResponse.response_mode` must be in `ResponseWindow.response_modes_accepted`.

### 5.3 Hebrew provider contract

- **Normative:** `HebrewEvaluator.evaluate` must receive a `DomainNormalizedResponse`, not a raw `ResponseInterpretation`.
- **Normative:** `HebrewEvaluator` output must include `answer_status` and `evaluation_status`; `verdict` is prohibited.
- **Normative:** `ContentItem.status` and `abstention_status` must be validated before presentation.

## 6. Checksum validation

### 6.1 Version checksums

- **Normative:** `ProgramVersion.checksum` and `ProtocolVersion.checksum` must be recomputed and validated on load.
- **Normative:** If computed checksum does not match stored checksum, the version is invalid and must not be used.

### 6.2 Content checksums

- **Normative:** `ContentItem.checksum` must be validated when loaded from cache.
- **Recommended:** `RenderedStimulus` may carry a checksum of the rendered media.

### 6.3 Event integrity

- **Recommended:** Each stored `Event` should have a content checksum to detect tampering.
- **Recommended:** `provenance` should be validated to form an acyclic graph.

## 7. Version compatibility

### 7.1 Schema version compatibility

- **Normative:** The runtime must accept all `schema_version`s it declares support for.
- **Normative:** A newer `schema_version` must not remove required fields; it may add optional fields.
- **Recommended:** The runtime should reject `schema_version`s it does not understand.

### 7.2 Dependency version compatibility

- **Normative:** `ProtocolVersion.dependency_versions` must be satisfied exactly by the running providers.
- **Recommended:** Exact-match semantics are preferred over semver ranges to ensure reproducibility.

### 7.3 Event payload versioning

- **Normative:** Old event payloads must remain parseable by new consumers.
- **Recommended:** Producers should not emit payloads with a `schema_version` newer than the consumer understands.

## 8. Object-specific validation rules

### 8.1 `Trial`

- **Normative:** `response_requirement` must be `required`, `optional`, or `none`.
- **Normative:** If `response_requirement == none`, `accepted_response_modes` must be absent or empty.
- **Normative:** `content_item_ids` must not be empty.

### 8.2 `Instruction`

- **Normative:** `instruction_payload` must not be null.
- **Normative:** For covert instruction types (`INSTRUCT_COVERT_RETRIEVAL`, `INSTRUCT_COVERT_REHEARSAL`, `INSTRUCT_IMAGERY`), `observable_response_expected` must be `false`.
- **Normative:** Exactly one of `allotted_duration` or `open_until_response` must be present.

### 8.3 `AdaptationDecision`

- **Normative:** `decision == APPLY` is prohibited when `deployment_status` is `exploratory_only` or `shadow_mode`.
- **Normative:** `proposed_value` must be within `allowed_bounds`.
- **Normative:** `current_value` and `proposed_value` must be for the same `target_dimension`.

### 8.4 `ScheduleDecision`

- **Normative:** `selected_item_ids` must be a subset of `candidate_item_ids`.
- **Normative:** `excluded_candidates` must reference only items in `candidate_item_ids`.

### 8.5 `Evaluation`

- **Normative:** `answer_status == unevaluable` is allowed only when `evaluation_status` is `abstained` or `failed`.
- **Normative:** `correctness_credit` must be between 0.0 and 1.0 inclusive.
- **Normative:** `accepted_variant_id` must be non-null when `answer_status == acceptable_variant` unless evaluator explicitly abstains.

### 8.6 `ContentItem`

- **Normative:** If `abstention_status == true`, the item must not be presented as authoritative.
- **Normative:** `status == rejected` items must not be used in any trial.

### 8.7 `SafetyEvent`

- **Normative:** `action_taken` must match the severity and rule definition.
- **Normative:** A `critical` safety event must result in `protocol_terminated` or `session_paused`.

## 9. Validation enforcement points

| Enforcement point | Rules applied |
|---|---|
| Fixture ingest | Identifier uniqueness, logical/executable separation, enum validation, checksum validation, provider compatibility. |
| Session start | Protocol version compatibility, provider capability matching, required_providers presence, dependency version matching. |
| Event append | Envelope validation, schema version, enum validation, provenance validity, timestamp/sequence monotonicity, causal ordering. |
| Snapshot refresh | Derived field consistency, foreign-key validity. |
| Replay load | Event integrity, provenance acyclicity, monotonic ordering. |

## 10. Phase 4A scope note

This validation rule set is complete for Phase 4A. It does not define:

- Validation library or framework.
- Error message format.
- Validation performance budgets.
- Schema migration code.

These are implementation decisions reserved for Phase 4B.
