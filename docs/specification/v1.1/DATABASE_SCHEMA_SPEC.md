# MPE v1.1 Database Schema Specification

## Scope

This document defines the persistent entities for the MindTune Protocol Engine v1.1. It is derived directly from:

- `MPE_OBJECT_MODEL_V1_1.md`
- `MPE_CANONICAL_IDENTIFIER_REGISTRY.md`
- `MPE_CANONICAL_ENUM_REGISTRY.md`
- `MPE_OBJECT_EVENT_COVERAGE_MATRIX.csv`

No implementation language, SQL, or storage engine is chosen here. All identifiers, enums, and relationships must match the canonical registries. Fields introduced in this document are limited to implementation-required metadata (e.g., `created_at`, `updated_at` for registry entries) and do not change the architecture.

## Legend

| Tag | Meaning |
|---|---|
| **Normative** | Required by MPE v1.1. |
| **Recommended** | Strongly advised for correctness, performance, or auditability. |
| **Optional** | May be omitted in a minimal implementation. |
| **Out of scope** | Not part of Phase 4A. |
| **Implementation note** | Engineering guidance, not an architectural rule. |

## 1. Static content and protocol registry tables

These tables hold immutable, versioned fixtures authored before runtime. They are append-only and effectively immutable.

### 1.1 `program`

- **Purpose:** Stable logical identity for a family of protocols.
- **Source:** `MPE_OBJECT_MODEL_V1_1.md` §Program.
- **Classification:** Persistent, static, immutable content.

| Field | Type | Nullable | Unique | Index | FK | Immutable | Notes |
|---|---|---|---|---|---|---|---|
| `program_id` | UUID or slug | No | Primary key | Yes | — | Yes | Canonical identifier. |
| `name` | string | No | Yes | Yes | — | Yes | |
| `description` | string | Yes | No | No | — | Yes | |
| `transfer_claim_level` | enum | No | No | No | — | Yes | `trained_task_performance` default (canonical enum registry). |
| `target_population` | string | Yes | No | No | — | Yes | Optional. |
| `consent_category` | string | Yes | No | No | — | Yes | Optional. |
| `created_at` | timestamp | No | No | No | — | Yes | Implementation audit field. |

**Indexes:** Primary key on `program_id`; unique on `name`.

**Implementation note:** `program` contains no executable content; executable data lives in `program_version`.

### 1.2 `program_version`

- **Purpose:** Immutable executable definition of a `program`.
- **Source:** `MPE_OBJECT_MODEL_V1_1.md` §ProgramVersion.

| Field | Type | Nullable | Unique | Index | FK | Immutable | Notes |
|---|---|---|---|---|---|---|---|
| `program_version_id` | UUID | No | Primary key | Yes | — | Yes | Canonical identifier. |
| `program_id` | UUID/slug | No | No | Yes | `program.program_id` | Yes | Logical parent. |
| `version` | string | No | No | Yes | — | Yes | Human-readable version label. |
| `checksum` | string | No | Yes | Yes | — | Yes | Integrity of this version. |
| `protocol_version_sequence` | ordered list of UUIDs | No | No | No | `protocol_version.protocol_version_id` | Yes | Ordered list of protocol versions in this program. |
| `safety_profile_id` | UUID | No | No | Yes | — | Yes | References a safety profile fixture. |
| `consent_requirements` | JSON/map | No | No | No | — | Yes | Consent categories and retention rules. |
| `schema_version` | string | No | No | No | — | Yes | Schema version of this object. |
| `dependency_versions` | map | No | No | No | — | Yes | Provider/dependency checksums. |
| `schedule` | JSON | Yes | No | No | — | Yes | Optional high-level schedule constraints. |
| `learner_eligibility` | JSON | Yes | No | No | — | Yes | Optional. |
| `created_at` | timestamp | No | No | No | — | Yes | |

**Indexes:** Primary key on `program_version_id`; unique on `checksum`; index on `program_id`.

### 1.3 `protocol`

- **Purpose:** Stable logical identity for a session type.
- **Source:** `MPE_OBJECT_MODEL_V1_1.md` §Protocol.

| Field | Type | Nullable | Unique | Index | FK | Immutable | Notes |
|---|---|---|---|---|---|---|---|
| `protocol_id` | UUID or slug | No | Primary key | Yes | — | Yes | Canonical identifier. |
| `name` | string | No | Yes | Yes | — | Yes | |
| `description` | string | Yes | No | No | — | Yes | |
| `protocol_family` | string | No | No | Yes | — | Yes | E.g., language, memory, etc. |
| `purpose` | enum | No | No | No | — | Yes | `assessment` \| `acquisition` \| `retrieval` \| `consolidation` \| `generalization` \| `regulation` \| `rehabilitation` \| `mixed`. |
| `default_transfer_claim` | enum | Yes | No | No | — | Yes | Optional; defaults to `trained_task_performance`. |
| `created_at` | timestamp | No | No | No | — | Yes | |

**Indexes:** Primary key on `protocol_id`; unique on `name`.

### 1.4 `protocol_version`

- **Purpose:** Immutable executable definition of a `protocol`.
- **Source:** `MPE_OBJECT_MODEL_V1_1.md` §ProtocolVersion.

| Field | Type | Nullable | Unique | Index | FK | Immutable | Notes |
|---|---|---|---|---|---|---|---|
| `protocol_version_id` | UUID | No | Primary key | Yes | — | Yes | Canonical identifier. |
| `protocol_id` | UUID/slug | No | No | Yes | `protocol.protocol_id` | Yes | Logical parent. |
| `version` | string | No | No | Yes | — | Yes | |
| `checksum` | string | No | Yes | Yes | — | Yes | |
| `objective` | string | No | No | No | — | Yes | |
| `purpose` | enum | No | No | No | — | Yes | Same enum as `protocol.purpose`. |
| `primary_transfer_claim` | enum | No | No | No | — | Yes | `trained_task_performance` default. |
| `block_sequence` | JSON | Conditional | No | No | — | Yes | Required if `trial_sequence` absent. |
| `trial_sequence` | JSON | Conditional | No | No | — | Yes | Required if `block_sequence` absent. |
| `required_providers` | list | No | No | No | — | Yes | Provider IDs/versions required. |
| `safety_profile_id` | UUID | No | No | Yes | — | Yes | |
| `schema_version` | string | No | No | No | — | Yes | |
| `dependency_versions` | map | No | No | No | — | Yes | |
| `estimated_duration` | number | Yes | No | No | — | Yes | Optional. |
| `difficulty_dimensions` | JSON | Yes | No | No | — | Yes | Phase 5A+; optional for schema. |
| `created_at` | timestamp | No | No | No | — | Yes | |

**Indexes:** Primary key on `protocol_version_id`; unique on `checksum`; index on `protocol_id`.

**Implementation note:** Validation must ensure exactly one of `block_sequence` or `trial_sequence` is present.

### 1.5 `task_definition`

- **Purpose:** Reusable template for a cognitive task pattern.
- **Source:** `MPE_OBJECT_MODEL_V1_1.md` §TaskDefinition.

| Field | Type | Nullable | Unique | Index | FK | Immutable | Notes |
|---|---|---|---|---|---|---|---|
| `task_definition_id` | UUID | No | Primary key | Yes | — | Yes | |
| `version` | string | No | No | Yes | — | Yes | |
| `task_family` | enum | No | No | Yes | — | Yes | Canonical `task_family` enum. |
| `trial_role_sequence` | ordered list of enum | No | No | No | — | Yes | From `TrialRole` values. |
| `example_protocol_ids` | list | Yes | No | No | `protocol.protocol_id` | Yes | Optional example protocols. |

**Indexes:** Primary key on `task_definition_id`; composite index on (`task_definition_id`, `version`).

### 1.6 `content_item`

- **Purpose:** Domain-neutral reference to learning material.
- **Source:** `MPE_OBJECT_MODEL_V1_1.md` §ContentItem; `MPE_HEBREW_PROVIDER_CONTRACT.md` §HebrewDomainProvider outputs.
- **Classification:** Persistent, domain-provided, immutable.

| Field | Type | Nullable | Unique | Index | FK | Immutable | Notes |
|---|---|---|---|---|---|---|---|
| `content_item_id` | UUID | No | Primary key | Yes | — | Yes | |
| `provider_id` | string | No | No | Yes | — | Yes | E.g., `hebrew`. |
| `provider_version` | string | No | No | Yes | — | Yes | |
| `content_type` | string | No | No | Yes | — | Yes | E.g., `verb_form`, `word`, `phrase`. |
| `checksum` | string | No | No | Yes | — | Yes | |
| `surface_form` | string | Yes | No | Yes | — | Yes | Vocalized or display form. |
| `normalized_form` | string | Yes | No | Yes | — | Yes | Canonical form. |
| `accepted_variants` | JSON | Yes | No | No | — | Yes | List of accepted forms with `variant_id`. |
| `form_key` | string | Yes | No | Yes | — | Yes | E.g., `past_first_mf_singular`. |
| `root` | string | Yes | No | Yes | — | Yes | Hebrew example. |
| `binyan` | string | Yes | No | Yes | — | Yes | Hebrew example. |
| `grammatical_features` | JSON | Yes | No | No | — | Yes | |
| `pronunciation_metadata` | JSON | Yes | No | No | — | Yes | Advisory. |
| `evidence_group` | string | Yes | No | Yes | — | Yes | |
| `confidence` | number | Yes | No | No | — | Yes | |
| `status` | enum | Yes | No | No | — | Yes | `verified_consensus` \| `high_confidence_candidate` \| `unresolved` \| `rejected`. |
| `abstention_status` | boolean | Yes | No | No | — | Yes | |
| `scope` | string | Yes | No | Yes | — | Yes | E.g., `phase3_100_verb_subset`. |
| `metadata` | JSON | Yes | No | No | — | Yes | Opaque to core. |
| `created_at` | timestamp | Yes | No | No | — | Yes | |

**Indexes:** Primary key on `content_item_id`; index on (`provider_id`, `provider_version`); index on `scope`; index on `status`.

**Implementation note:** Content items may be stored in a domain-provider database and cached in MPE storage. MPE core must not interpret domain-specific fields.

### 1.7 `safety_profile`

- **Purpose:** Collection of safety rules referenced by `ProgramVersion`/`ProtocolVersion`.
- **Source:** Implied by `safety_profile_id` in object model; not fully expanded in MPE v1.1. Phase 4A schema requires a fixture table.
- **Classification:** Persistent, static, immutable.

| Field | Type | Nullable | Unique | Index | FK | Immutable | Notes |
|---|---|---|---|---|---|---|---|
| `safety_profile_id` | UUID | No | Primary key | Yes | — | Yes | |
| `name` | string | No | Yes | Yes | — | Yes | |
| `rules` | JSON | No | No | No | — | Yes | List of safety rule definitions. |
| `schema_version` | string | No | No | No | — | Yes | |
| `created_at` | timestamp | No | No | No | — | Yes | |

**Implementation note:** Each safety rule must define trigger conditions, `severity`, and `action_taken`. Detailed rule schema is Phase 4A fixture work.

## 2. Session and runtime state tables

These tables are derived from the immutable event stream but are materialized for query performance.

### 2.1 `session`

- **Purpose:** One execution of a `program_version` and `protocol_version` by a learner.
- **Source:** `MPE_OBJECT_MODEL_V1_1.md` §Session; `MPE_EVENT_MODEL_V1_1.md` `session_created`, `session_started`, `session_paused`, `session_resumed`, `session_cancelled`, `session_completed`, `protocol_terminated`.
- **Classification:** Persistent, derived, mutable via events.

| Field | Type | Nullable | Unique | Index | FK | Immutable | Notes |
|---|---|---|---|---|---|---|---|
| `session_id` | UUID | No | Primary key | Yes | — | Yes | Event-derived. |
| `program_version_id` | UUID | No | No | Yes | `program_version.program_version_id` | Yes | From `session_created`. |
| `protocol_version_id` | UUID | No | No | Yes | `protocol_version.protocol_version_id` | Yes | From `session_created`. |
| `learner_id` | string/UUID | No | No | Yes | — | Yes | From `session_created`. |
| `created_at` | timestamp | No | No | Yes | — | Yes | Event timestamp. |
| `status` | enum | No | No | Yes | — | No | `created` \| `started` \| `paused` \| `resumed` \| `completed` \| `cancelled` \| `terminated`. |
| `ended_at` | timestamp | Yes | No | No | — | No | Derived from terminal event. |
| `outcome_summary` | JSON | Yes | No | No | — | No | Derived from `Outcome` computation. |
| `latest_event_sequence_number` | integer | No | No | No | — | No | Materialized from last event. |

**Indexes:** Primary key on `session_id`; indexes on `learner_id`, `program_version_id`, `protocol_version_id`, `status`.

**Derived fields:** `status`, `ended_at`, `outcome_summary`, `latest_event_sequence_number` are recomputed from events and may be cached.

### 2.2 `block_execution`

- **Purpose:** Runtime execution record of a `Block` within a `Session`.
- **Source:** `MPE_OBJECT_MODEL_V1_1.md` §Block; `MPE_EVENT_MODEL_V1_1.md` `block_started`, `block_completed`.

| Field | Type | Nullable | Unique | Index | FK | Immutable | Notes |
|---|---|---|---|---|---|---|---|
| `block_id` | UUID | No | Primary key | Yes | — | Yes | Defined by `ProtocolVersion`. |
| `session_id` | UUID | No | No | Yes | `session.session_id` | Yes | |
| `block_type` | enum | No | No | No | — | Yes | From `block_started`. |
| `started_at` | timestamp | No | No | Yes | — | Yes | From `block_started`. |
| `completed_at` | timestamp | Yes | No | No | — | No | From `block_completed`. |
| `completed_trial_count` | integer | Yes | No | No | — | No | From `block_completed`. |
| `trial_count` | integer | Yes | No | No | — | Yes | From `block_started` if known. |

**Indexes:** Primary key on (`block_id`, `session_id`); index on `session_id`.

### 2.3 `trial`

- **Purpose:** Atomic unit of a session.
- **Source:** `MPE_OBJECT_MODEL_V1_1.md` §Trial; `MPE_EVENT_MODEL_V1_1.md` `trial_created`.

| Field | Type | Nullable | Unique | Index | FK | Immutable | Notes |
|---|---|---|---|---|---|---|---|
| `trial_id` | UUID | No | Primary key | Yes | — | Yes | |
| `session_id` | UUID | No | No | Yes | `session.session_id` | Yes | |
| `block_id` | UUID | Yes | No | Yes | `block_execution.block_id` | Yes | If in a block. |
| `trial_index` | integer | No | No | Yes | — | Yes | Per-session index. |
| `task_definition_id` | UUID | No | No | Yes | `task_definition.task_definition_id` | Yes | |
| `content_item_ids` | list of UUIDs | No | No | No | `content_item.content_item_id` | Yes | Ordered list. |
| `response_requirement` | enum | No | No | No | — | Yes | `required` \| `optional` \| `none`. |
| `accepted_response_modes` | list of enum | Yes | No | No | — | Yes | From `trial_created`. |
| `difficulty_dimensions` | JSON | Yes | No | No | — | Yes | At trial start. |
| `scheduled_start_time` | number | Yes | No | No | — | Yes | Active-session timestamp. |
| `status` | enum | Yes | No | Yes | — | No | `created` \| `in_progress` \| `completed` \| `timeout` \| `aborted`. Implementation-derived. |

**Indexes:** Primary key on `trial_id`; composite index on (`session_id`, `trial_index`); index on `block_id`.

**Implementation note:** `status` is not a MPE object-model field; it is a derived materialization for runtime convenience.

## 3. Response processing tables

All objects in this section are immutable and created by explicit events.

### 3.1 `observation`

- **Purpose:** Raw input from an `ObservationProvider`.
- **Source:** `MPE_OBJECT_MODEL_V1_1.md` §Observation; `MPE_EVENT_MODEL_V1_1.md` `observation_received`.

| Field | Type | Nullable | Unique | Index | FK | Immutable | Notes |
|---|---|---|---|---|---|---|---|
| `observation_id` | UUID | No | Primary key | Yes | — | Yes | |
| `response_window_id` | UUID | Yes | No | Yes | `response_window.response_window_id` | Yes | Null when not in a window. |
| `provider_id` | string | No | No | Yes | — | Yes | |
| `provider_version` | string | No | No | Yes | — | Yes | |
| `observation_type` | enum | No | No | Yes | — | Yes | Canonical `observation_type` enum. |
| `received_at` | number | No | No | Yes | — | Yes | Component timestamp. |
| `payload` | JSON/binary | No | No | No | — | Yes | Raw observation payload. |
| `quality_dimensions` | map | No | No | No | — | Yes | |
| `quality_flags` | list | No | No | No | — | Yes | |
| `quality_model_id` | string | No | No | No | — | Yes | |
| `quality_model_version` | string | No | No | No | — | Yes | |
| `overall_quality` | number | Yes | No | No | — | Yes | Optional. |
| `artifact_flags` | list | Yes | No | No | — | Yes | Optional. |
| `device_id` | string | Yes | No | Yes | — | Yes | Optional. |

**Indexes:** Primary key on `observation_id`; index on (`response_window_id`, `received_at`); index on `observation_type`.

### 3.2 `captured_response`

- **Purpose:** Technical capture assembled from observations.
- **Source:** `MPE_OBJECT_MODEL_V1_1.md` §CapturedResponse; `MPE_EVENT_MODEL_V1_1.md` `captured_response_created`.

| Field | Type | Nullable | Unique | Index | FK | Immutable | Notes |
|---|---|---|---|---|---|---|---|
| `captured_response_id` | UUID | No | Primary key | Yes | — | Yes | |
| `response_window_id` | UUID | No | No | Yes | `response_window.response_window_id` | Yes | |
| `observation_ids` | list of UUIDs | No | No | No | `observation.observation_id` | Yes | |
| `response_mode` | enum | No | No | No | — | Yes | `button` \| `voice` \| `typed` \| `recognition`. |
| `captured_payload` | JSON/binary | No | No | No | — | Yes | Raw but captured. |
| `captured_at` | number | No | No | Yes | — | Yes | Component timestamp. |
| `device_provenance` | JSON | No | No | No | — | Yes | |
| `quality_flags` | list | No | No | No | — | Yes | |

**Indexes:** Primary key on `captured_response_id`; index on `response_window_id`.

### 3.3 `response_interpretation`

- **Purpose:** Domain-agnostic interpreted form.
- **Source:** `MPE_OBJECT_MODEL_V1_1.md` §ResponseInterpretation; `MPE_EVENT_MODEL_V1_1.md` `response_interpreted`.

| Field | Type | Nullable | Unique | Index | FK | Immutable | Notes |
|---|---|---|---|---|---|---|---|
| `response_interpretation_id` | UUID | No | Primary key | Yes | — | Yes | |
| `response_window_id` | UUID | No | No | Yes | `response_window.response_window_id` | Yes | |
| `captured_response_id` | UUID | No | No | Yes | `captured_response.captured_response_id` | Yes | |
| `interpreter_id` | string | No | No | Yes | — | Yes | |
| `interpreter_version` | string | No | No | Yes | — | Yes | |
| `interpreted_payload` | string/JSON | No | No | No | — | Yes | |
| `interpretation_confidence` | number | No | No | No | — | Yes | |
| `interpretation_type` | enum | No | No | No | — | Yes | `asr_transcript` \| `button_label` \| `typed_text` \| `selected_option`. |

**Indexes:** Primary key on `response_interpretation_id`; index on `captured_response_id`.

### 3.4 `domain_normalized_response`

- **Purpose:** Domain-specific canonicalization.
- **Source:** `MPE_OBJECT_MODEL_V1_1.md` §DomainNormalizedResponse; `MPE_EVENT_MODEL_V1_1.md` `domain_response_normalized`.

| Field | Type | Nullable | Unique | Index | FK | Immutable | Notes |
|---|---|---|---|---|---|---|---|
| `domain_normalized_response_id` | UUID | No | Primary key | Yes | — | Yes | |
| `response_window_id` | UUID | No | No | Yes | `response_window.response_window_id` | Yes | |
| `response_interpretation_id` | UUID | No | No | Yes | `response_interpretation.response_interpretation_id` | Yes | |
| `normalizer_id` | string | No | No | Yes | — | Yes | |
| `normalizer_version` | string | No | No | Yes | — | Yes | |
| `response_mode` | enum | No | No | No | — | Yes | `button` \| `voice` \| `typed` \| `recognition`. |
| `normalized_payload` | string/JSON | No | No | No | — | Yes | |
| `extracted_at` | number | No | No | No | — | Yes | Component timestamp. |
| `uncertainty` | number | No | No | No | — | Yes | |
| `input_observation_ids` | list | Yes | No | No | `observation.observation_id` | Yes | Optional. |

**Indexes:** Primary key on `domain_normalized_response_id`; index on `response_interpretation_id`.

### 3.5 `evaluation`

- **Purpose:** Correctness result from an `Evaluator`.
- **Source:** `MPE_OBJECT_MODEL_V1_1.md` §Evaluation; `MPE_EVENT_MODEL_V1_1.md` `evaluation_completed`, `evaluation_abstained`, `evaluation_failed`.

| Field | Type | Nullable | Unique | Index | FK | Immutable | Notes |
|---|---|---|---|---|---|---|---|
| `evaluation_id` | UUID | No | Primary key | Yes | — | Yes | |
| `trial_id` | UUID | No | No | Yes | `trial.trial_id` | Yes | |
| `evaluator_id` | string | No | No | Yes | — | Yes | |
| `evaluator_version` | string | No | No | Yes | — | Yes | |
| `domain_normalized_response_id` | UUID | Yes | No | Yes | `domain_normalized_response.domain_normalized_response_id` | Yes | May be null for `abstained`/`failed`. |
| `expected_content_item_id` | UUID | No | No | Yes | `content_item.content_item_id` | Yes | |
| `answer_status` | enum | No | No | No | — | Yes | Canonical `answer_status` enum. |
| `evaluation_status` | enum | No | No | No | — | Yes | Canonical `evaluation_status` enum. |
| `correctness_credit` | number | Yes | No | No | — | Yes | 0.0–1.0. |
| `accepted_variant_id` | UUID | Yes | No | Yes | — | Yes | Optional. |
| `evidence_group` | string | Yes | No | Yes | — | Yes | |
| `scope_status` | enum | Yes | No | No | — | Yes | `verified_consensus` \| `high_confidence_candidate` \| `unresolved` \| `rejected`. |
| `abstention_reason` | string | Yes | No | No | — | Yes | If `evaluation_status == abstained`. |
| `failure_reason` | string | Yes | No | No | — | Yes | If `evaluation_status == failed`. |
| `error_category` | enum | Yes | No | No | — | Yes | Canonical `error_category` enum. |
| `evidence` | JSON | Yes | No | No | — | Yes | Domain-specific evidence. |
| `confidence` | number | Yes | No | No | — | Yes | |

**Indexes:** Primary key on `evaluation_id`; index on (`trial_id`, `evaluator_id`); index on `answer_status`.

## 4. Instruction, stimulus, and feedback tables

### 4.1 `instruction`

- **Purpose:** Cue delivered to the learner.
- **Source:** `MPE_OBJECT_MODEL_V1_1.md` §Instruction; `MPE_EVENT_MODEL_V1_1.md` `instruction_started`.

| Field | Type | Nullable | Unique | Index | FK | Immutable | Notes |
|---|---|---|---|---|---|---|---|
| `instruction_id` | UUID | No | Primary key | Yes | — | Yes | |
| `trial_id` | UUID | No | No | Yes | `trial.trial_id` | Yes | |
| `instruction_type` | enum | No | No | No | — | Yes | Canonical `instruction_type` enum. |
| `instruction_payload` | string/JSON | No | No | No | — | Yes | Never null. |
| `target_operation` | string | No | No | No | — | Yes | |
| `allotted_duration` | number | Yes | No | No | — | Yes | |
| `open_until_response` | boolean | Yes | No | No | — | Yes | |
| `observable_response_expected` | boolean | No | No | No | — | Yes | |
| `content_item_id` | UUID | Yes | No | Yes | `content_item.content_item_id` | Yes | Optional. |
| `started_at` | number | No | No | Yes | — | Yes | Runtime timestamp. |
| `completed_at` | number | Yes | No | No | — | No | From `instruction_completed`. |
| `duration` | number | Yes | No | No | — | No | Derived. |

**Indexes:** Primary key on `instruction_id`; index on `trial_id`.

### 4.2 `stimulus_request`

- **Purpose:** Request to a `Renderer`.
- **Source:** `MPE_OBJECT_MODEL_V1_1.md` §StimulusRequest; `MPE_EVENT_MODEL_V1_1.md` `stimulus_requested`.

| Field | Type | Nullable | Unique | Index | FK | Immutable | Notes |
|---|---|---|---|---|---|---|---|
| `stimulus_request_id` | UUID | No | Primary key | Yes | — | Yes | |
| `trial_id` | UUID | No | No | Yes | `trial.trial_id` | Yes | |
| `content_item_id` | UUID | No | No | Yes | `content_item.content_item_id` | Yes | |
| `renderer_id` | string | No | No | Yes | — | Yes | |
| `requested_at` | number | No | No | Yes | — | Yes | Runtime timestamp. |
| `scheduled_for` | number | Yes | No | No | — | Yes | |
| `rate` | number | Yes | No | No | — | Yes | |
| `voice_id` | string | Yes | No | No | — | Yes | |
| `prosody_hints` | JSON | Yes | No | No | — | Yes | |
| `fallback_policy` | JSON | Yes | No | No | — | Yes | Optional. |

**Indexes:** Primary key on `stimulus_request_id`; index on `trial_id`.

### 4.3 `rendered_stimulus`

- **Purpose:** Playable media output.
- **Source:** `MPE_OBJECT_MODEL_V1_1.md` §RenderedStimulus; `MPE_EVENT_MODEL_V1_1.md` `stimulus_ready`.

| Field | Type | Nullable | Unique | Index | FK | Immutable | Notes |
|---|---|---|---|---|---|---|---|
| `rendered_stimulus_id` | UUID | No | Primary key | Yes | — | Yes | |
| `stimulus_request_id` | UUID | No | No | Yes | `stimulus_request.stimulus_request_id` | Yes | |
| `renderer_id` | string | No | No | Yes | — | Yes | |
| `renderer_version` | string | No | No | Yes | — | Yes | |
| `media_handle` | string | No | No | No | — | Yes | Reference to media, not binary data. |
| `duration` | number | No | No | No | — | Yes | |
| `rendered_at` | number | No | No | Yes | — | Yes | Component timestamp. |
| `format` | string | Yes | No | No | — | Yes | |
| `provenance` | JSON | Yes | No | No | — | Yes | |

**Indexes:** Primary key on `rendered_stimulus_id`; index on `stimulus_request_id`.

### 4.4 `response_window`

- **Purpose:** Interval for observable response collection.
- **Source:** `MPE_OBJECT_MODEL_V1_1.md` §ResponseWindow; `MPE_EVENT_MODEL_V1_1.md` `response_window_opened`.

| Field | Type | Nullable | Unique | Index | FK | Immutable | Notes |
|---|---|---|---|---|---|---|---|
| `response_window_id` | UUID | No | Primary key | Yes | — | Yes | |
| `trial_id` | UUID | No | No | Yes | `trial.trial_id` | Yes | |
| `response_modes_accepted` | list of enum | No | No | No | — | Yes | Canonical `response_mode` values. |
| `opened_at` | number | No | No | Yes | — | Yes | Runtime timestamp. |
| `deadline_at` | number | Yes | No | No | — | Yes | |
| `timeout_policy` | JSON | No | No | No | — | Yes | |
| `min_response_duration` | number | Yes | No | No | — | Yes | |
| `max_response_duration` | number | Yes | No | No | — | Yes | |

**Indexes:** Primary key on `response_window_id`; index on `trial_id`.

### 4.5 `feedback_event`

- **Purpose:** Delivery of educational feedback.
- **Source:** `MPE_OBJECT_MODEL_V1_1.md` §FeedbackEvent; `MPE_EVENT_MODEL_V1_1.md` `feedback_started`, `feedback_completed`.

| Field | Type | Nullable | Unique | Index | FK | Immutable | Notes |
|---|---|---|---|---|---|---|---|
| `feedback_event_id` | UUID | No | Primary key | Yes | — | Yes | |
| `trial_id` | UUID | No | No | Yes | `trial.trial_id` | Yes | |
| `evaluation_id` | UUID | Yes | No | Yes | `evaluation.evaluation_id` | Yes | Optional. |
| `feedback_category` | enum | No | No | No | — | Yes | `KNOWLEDGE` \| `PERFORMANCE` \| `METACOGNITIVE`. |
| `feedback_type` | enum | No | No | No | — | Yes | Canonical `feedback_type` enum. |
| `content_item_id` | UUID | Yes | No | Yes | `content_item.content_item_id` | Yes | XOR with `rendered_media_id`. |
| `rendered_media_id` | UUID | Yes | No | Yes | `rendered_stimulus.rendered_stimulus_id` | Yes | XOR with `content_item_id`. |
| `started_at` | number | No | No | Yes | — | Yes | |
| `completed_at` | number | Yes | No | No | — | No | From `feedback_completed`. |
| `duration` | number | Yes | No | No | — | No | Derived. |
| `prosody_hint` | JSON | Yes | No | No | — | Yes | |

**Indexes:** Primary key on `feedback_event_id`; index on `trial_id`; index on `evaluation_id`.

## 5. Safety, scheduling, and adaptation tables

### 5.1 `safety_instruction`

- **Purpose:** Runtime safety command.
- **Source:** `MPE_OBJECT_MODEL_V1_1.md` §SafetyInstruction; `MPE_EVENT_MODEL_V1_1.md` `safety_instruction_started`, `safety_instruction_completed`.

| Field | Type | Nullable | Unique | Index | FK | Immutable | Notes |
|---|---|---|---|---|---|---|---|
| `safety_instruction_id` | UUID | No | Primary key | Yes | — | Yes | |
| `session_id` | UUID | No | No | Yes | `session.session_id` | Yes | |
| `safety_rule_id` | string | No | No | Yes | — | Yes | |
| `instruction_payload` | string/JSON | No | No | No | — | Yes | |
| `severity` | enum | No | No | No | — | Yes | `info` \| `warning` \| `critical`. |
| `started_at` | number | No | No | Yes | — | Yes | |
| `completed_at` | number | Yes | No | No | — | No | From `safety_instruction_completed`. |
| `user_acknowledged_at` | number | Yes | No | No | — | No | |

**Indexes:** Primary key on `safety_instruction_id`; index on `session_id`.

### 5.2 `safety_event`

- **Purpose:** Safety rule activation or degradation.
- **Source:** `MPE_OBJECT_MODEL_V1_1.md` §SafetyEvent; `MPE_EVENT_MODEL_V1_1.md` `safety_rule_triggered`, `recovery_inserted`, `protocol_terminated`.

| Field | Type | Nullable | Unique | Index | FK | Immutable | Notes |
|---|---|---|---|---|---|---|---|
| `safety_event_id` | UUID | No | Primary key | Yes | — | Yes | |
| `session_id` | UUID | No | No | Yes | `session.session_id` | Yes | |
| `safety_rule_id` | string | No | No | Yes | — | Yes | |
| `triggered_at` | number | No | No | Yes | — | Yes | Runtime timestamp. |
| `severity` | enum | No | No | No | — | Yes | `info` \| `warning` \| `critical`. |
| `action_taken` | enum | No | No | No | — | Yes | `pause` \| `terminate` \| `volume_limit` \| `offer_end` \| `insert_recovery`. |
| `trigger_observation_id` | UUID | Yes | No | Yes | `observation.observation_id` | Yes | Optional. |
| `user_acknowledged_at` | number | Yes | No | No | — | No | |

**Indexes:** Primary key on `safety_event_id`; index on `session_id`; index on `triggered_at`.

### 5.3 `schedule_decision`

- **Purpose:** Next item/block/session action.
- **Source:** `MPE_OBJECT_MODEL_V1_1.md` §ScheduleDecision; `MPE_EVENT_MODEL_V1_1.md` `schedule_decision`.

| Field | Type | Nullable | Unique | Index | FK | Immutable | Notes |
|---|---|---|---|---|---|---|---|
| `schedule_decision_id` | UUID | No | Primary key | Yes | — | Yes | |
| `session_id` | UUID | No | No | Yes | `session.session_id` | Yes | |
| `scheduler_id` | string | No | No | Yes | — | Yes | |
| `scheduler_version` | string | No | No | Yes | — | Yes | |
| `policy_id` | string | No | No | Yes | — | Yes | |
| `policy_version` | string | No | No | Yes | — | Yes | |
| `source_event_ids` | list of UUIDs | No | No | No | `event.event_id` | Yes | |
| `item_history_snapshot_id` | UUID | No | No | Yes | — | Yes | |
| `candidate_item_ids` | list of UUIDs | No | No | No | `content_item.content_item_id` | Yes | |
| `excluded_candidates` | JSON | No | No | No | — | Yes | Reasons. |
| `selection_rule` | string | No | No | No | — | Yes | |
| `tie_break_rule` | string | No | No | No | — | Yes | |
| `random_seed` | string/integer | Yes | No | No | — | Yes | |
| `selected_item_ids` | list of UUIDs | No | No | No | `content_item.content_item_id` | Yes | |
| `decision_type` | enum | No | No | No | — | Yes | `next_trial` \| `next_block` \| `session_end` \| `insert_review` \| `offer_break`. |
| `decision_status` | enum | No | No | No | — | Yes | `made` \| `abstained`. |
| `abstention_reason` | string | Yes | No | No | — | Yes | |
| `expected_difficulty_dimensions` | JSON | Yes | No | No | — | Yes | Optional. |

**Indexes:** Primary key on `schedule_decision_id`; index on `session_id`; index on `policy_id`.

### 5.4 `adaptation_decision`

- **Purpose:** Contractual reversible decision to change a controllable parameter.
- **Source:** `MPE_OBJECT_MODEL_V1_1.md` §AdaptationDecision; `MPE_EVENT_MODEL_V1_1.md` `adaptation_*`.
- **Phase applicability:** Phase 5A+. Stored in schema for completeness but not created during Phase 4.

| Field | Type | Nullable | Unique | Index | FK | Immutable | Notes |
|---|---|---|---|---|---|---|---|
| `adaptation_decision_id` | UUID | No | Primary key | Yes | — | Yes | |
| `session_id` | UUID | No | No | Yes | `session.session_id` | Yes | |
| `policy_id` | string | No | No | Yes | — | Yes | |
| `policy_version` | string | No | No | Yes | — | Yes | |
| `deployment_status` | enum | No | No | No | — | Yes | `exploratory_only` \| `shadow_mode` \| `limited_runtime` \| `production_approved`. |
| `target_dimension` | string | No | No | Yes | — | Yes | Typed dimension name. |
| `current_value` | any | No | No | No | — | Yes | |
| `proposed_value` | any | No | No | No | — | Yes | |
| `allowed_bounds` | JSON | No | No | No | — | Yes | `{min, max, default, status, evidence_grade}`. |
| `source_event_ids` | list of UUIDs | No | No | No | `event.event_id` | Yes | |
| `evidence_record_ids` | list of UUIDs | Yes | No | No | `evidence_record.evidence_record_id` | Yes | Optional. |
| `aggregation_window` | string/JSON | No | No | No | — | Yes | |
| `minimum_evidence` | boolean | No | No | No | — | Yes | |
| `uncertainty_threshold` | boolean | No | No | No | — | Yes | |
| `confidence` | number | No | No | No | — | Yes | |
| `cooldown` | number | No | No | No | — | Yes | |
| `hysteresis` | number | No | No | No | — | Yes | |
| `maximum_step_size` | number | No | No | No | — | Yes | |
| `rollback_rule` | JSON | No | No | No | — | Yes | |
| `abstention_rule` | JSON | No | No | No | — | Yes | |
| `decision` | enum | No | No | No | — | Yes | `APPLY` \| `NO_CHANGE_INSUFFICIENT_EVIDENCE` \| `REVERSE` \| `ABSTAIN`. |
| `reason` | string | No | No | No | — | Yes | |
| `applied_at` | number | Yes | No | No | — | No | From `adaptation_applied`. |
| `reversed_at` | number | Yes | No | No | — | No | From `adaptation_reversed`. |
| `outcome_event_refs` | list | Yes | No | No | `event.event_id` | Yes | Optional. |

**Indexes:** Primary key on `adaptation_decision_id`; index on `session_id`; index on `policy_id`.

## 6. Evidence, state estimate, and outcome tables

### 6.1 `evidence_record`

- **Purpose:** Evidence backing an `Evaluation`, `ScheduleDecision`, or `AdaptationDecision`.
- **Source:** `MPE_OBJECT_MODEL_V1_1.md` §EvidenceRecord; `MPE_EVENT_MODEL_V1_1.md` `evidence_record_created`.

| Field | Type | Nullable | Unique | Index | FK | Immutable | Notes |
|---|---|---|---|---|---|---|---|
| `evidence_record_id` | UUID | No | Primary key | Yes | — | Yes | |
| `decision_or_evaluation_id` | UUID | No | No | Yes | — | Yes | Generic reference to source decision/evaluation. |
| `source_event_ids` | list of UUIDs | No | No | No | `event.event_id` | Yes | |
| `evidence_type` | enum | No | No | No | — | Yes | `domain_evaluation` \| `item_history` \| `behavioral_observation` \| `self_report` \| `sensor_observation`. |
| `summary` | string | No | No | No | — | Yes | |
| `domain_provider_evidence` | JSON | Yes | No | No | — | Yes | Optional. |
| `created_at` | number | No | No | Yes | — | Yes | |

**Indexes:** Primary key on `evidence_record_id`; index on `decision_or_evaluation_id`; index on `evidence_type`.

### 6.2 `state_estimate`

- **Purpose:** Uncertain estimate produced by a `StateInferenceModel`.
- **Source:** `MPE_OBJECT_MODEL_V1_1.md` §StateEstimate; `MPE_EVENT_MODEL_V1_1.md` `state_estimate_produced`.
- **Phase applicability:** Phase 5B+; schema defined for diagnostic storage.

| Field | Type | Nullable | Unique | Index | FK | Immutable | Notes |
|---|---|---|---|---|---|---|---|
| `state_estimate_id` | UUID | No | Primary key | Yes | — | Yes | |
| `model_id` | string | No | No | Yes | — | Yes | |
| `model_version` | string | No | No | Yes | — | Yes | |
| `target_estimate_name` | string | No | No | Yes | — | Yes | |
| `operational_definition` | string | No | No | No | — | Yes | |
| `input_observation_ids` | list of UUIDs | No | No | No | `observation.observation_id` | Yes | |
| `time_window` | JSON | No | No | No | — | Yes | |
| `value` | any | No | No | No | — | Yes | |
| `uncertainty` | number | No | No | No | — | Yes | |
| `validation_status` | string | No | No | No | — | Yes | |
| `deployment_status` | enum | No | No | No | — | Yes | `exploratory_only` default. |
| `alternative_explanations` | list | No | No | No | — | Yes | |
| `fallback_behavior_when_uncertain` | string | No | No | No | — | Yes | |
| `calibration_population` | string | Yes | No | No | — | Yes | |
| `known_confounds` | list | Yes | No | No | — | Yes | |
| `produced_at` | number | No | No | Yes | — | Yes | |

**Indexes:** Primary key on `state_estimate_id`; index on `model_id`; index on `input_observation_ids`.

### 6.3 `sensor_observation`

- **Purpose:** Generic sensor/device observation.
- **Source:** `MPE_OBJECT_MODEL_V1_1.md` §SensorObservation.

| Field | Type | Nullable | Unique | Index | FK | Immutable | Notes |
|---|---|---|---|---|---|---|---|
| `sensor_observation_id` | UUID | No | Primary key | Yes | — | Yes | |
| `provider_id` | string | No | No | Yes | — | Yes | |
| `provider_version` | string | No | No | Yes | — | Yes | |
| `device_id` | string | No | No | Yes | — | Yes | |
| `sensor_configuration_id` | string | No | No | Yes | — | Yes | |
| `preprocessing_version` | string | No | No | Yes | — | Yes | |
| `feature_name` | string | No | No | Yes | — | Yes | Opaque to core. |
| `raw_or_derived` | string | No | No | No | — | Yes | |
| `feature_window` | JSON | No | No | No | — | Yes | |
| `observed_at` | number | No | No | Yes | — | Yes | Component timestamp. |
| `quality_dimensions` | map | No | No | No | — | Yes | |
| `quality_flags` | list | No | No | No | — | Yes | |
| `quality_model_id` | string | No | No | No | — | Yes | |
| `quality_model_version` | string | No | No | No | — | Yes | |
| `artifact_flags` | list | No | No | No | — | Yes | |
| `numeric_value` | number | Conditional | No | No | — | Yes | Required if no `categorical_value`. |
| `categorical_value` | string | Conditional | No | No | — | Yes | Required if no `numeric_value`. |
| `uncertainty` | number | No | No | No | — | Yes | |
| `experimental_status` | string | No | No | No | — | Yes | |
| `provenance` | list | No | No | No | — | Yes | |
| `units` | string | Yes | No | No | — | Yes | |

**Indexes:** Primary key on `sensor_observation_id`; index on `device_id`; index on `feature_name`.

### 6.4 `outcome`

- **Purpose:** Read-only computed session summary.
- **Source:** `MPE_OBJECT_MODEL_V1_1.md` §Outcome.
- **Classification:** Derived, read-only.

| Field | Type | Nullable | Unique | Index | FK | Immutable | Notes |
|---|---|---|---|---|---|---|---|
| `session_id` | UUID | No | Primary key | Yes | `session.session_id` | No | Recomputed. |
| `computation_version` | string | No | No | Yes | — | No | |
| `status` | string | No | No | No | — | No | Derived from `session.status`. |
| `trial_count` | integer | No | No | No | — | No | Derived. |
| `completed_trial_count` | integer | No | No | No | — | No | Derived. |
| `accuracy` | number | Yes | No | No | — | No | Derived where applicable. |
| `omission_rate` | number | No | No | No | — | No | Derived. |
| `coverage` | number | No | No | No | — | No | Derived. |
| `dropout` | number | No | No | No | — | No | Derived. |
| `early_termination` | boolean | No | No | No | — | No | Derived. |
| `protocol_adherence` | number | No | No | No | — | No | Derived. |
| `latency_summaries` | JSON | Yes | No | No | — | No | Stratified. |
| `retention_proxy` | JSON | Yes | No | No | — | No | Optional. |
| `diagnostics` | JSON | Yes | No | No | — | No | Experimental only. |

**Indexes:** Primary key on `session_id`.

**Implementation note:** `outcome` is a materialized view over the event stream. It must be recomputed if the computation version or event stream changes.

## 7. Event store table

The event store is the source of truth. It is defined in detail in `EVENT_STORE_SPEC.md`. This section lists the event-store table schema for completeness.

### 7.1 `event`

- **Purpose:** Immutable, append-only record of everything that happened in a session.
- **Source:** `MPE_EVENT_MODEL_V1_1.md` §Event payload shape.

| Field | Type | Nullable | Unique | Index | FK | Immutable | Notes |
|---|---|---|---|---|---|---|---|
| `event_id` | UUID | No | Primary key | Yes | — | Yes | |
| `event_type` | string | No | No | Yes | — | Yes | From canonical event taxonomy. |
| `schema_version` | string | No | No | Yes | — | Yes | Payload version. |
| `session_id` | UUID | No | No | Yes | `session.session_id` | Yes | |
| `session_sequence_number` | integer | No | No | Yes | — | Yes | Canonical per-session ordering. |
| `protocol_version_id` | UUID | No | No | Yes | `protocol_version.protocol_version_id` | Yes | |
| `trial_id` | UUID | Yes | No | Yes | `trial.trial_id` | Yes | If applicable. |
| `block_id` | UUID | Yes | No | Yes | `block_execution.block_id` | Yes | If applicable. |
| `timestamp` | number | No | No | Yes | — | Yes | Runtime-owned monotonic session time. |
| `wallclock_at` | number | Yes | No | No | — | Yes | Optional wall-clock. |
| `component` | string | No | No | Yes | — | Yes | Who emitted it. |
| `component_version` | string | No | No | Yes | — | Yes | |
| `correlation_id` | UUID | Yes | No | Yes | — | Yes | Links request/response. |
| `provenance` | list of UUIDs | No | No | No | `event.event_id` | Yes | Causal predecessors. |
| `payload` | JSON | No | No | No | — | Yes | Event-specific payload. |
| `sensitive` | boolean | No | No | Yes | — | Yes | |
| `data_classification` | enum | Yes | No | Yes | — | Yes | `public` \| `consent_gated` \| `sensitive_phi` \| `research_sensitive`. |
| `quality_flags` | list | Yes | No | No | — | Yes | |

**Indexes:** Primary key on `event_id`; composite unique on (`session_id`, `session_sequence_number`); composite index on (`session_id`, `event_type`); index on `correlation_id`.

**Constraints:** `session_sequence_number` must be strictly monotonic per `session_id`. `timestamp` must be monotonic within a session except for component-timestamp events where it still counts active session time.

## 8. Summary of cross-table integrity

- `program` -> `program_version` (1:N).
- `protocol` -> `protocol_version` (1:N).
- `program_version` -> `protocol_version` via `protocol_version_sequence` (ordered N:M reference list).
- `session` -> `program_version`, `protocol_version` (N:1).
- `session` -> `block_execution` (1:N), `trial` (1:N), `safety_event` (1:N), `safety_instruction` (1:N), `schedule_decision` (1:N).
- `trial` -> `instruction`, `stimulus_request`, `response_window`, `feedback_event`, `evaluation`, `schedule_decision` (1:N each).
- `response_window` -> `observation` (1:N), `captured_response` (1:1), `response_interpretation` (1:1 if produced), `domain_normalized_response` (1:1 if produced).
- `domain_normalized_response` -> `evaluation` (1:1 or 1:0 if abstained/failed).
- `evaluation` -> `feedback_event` (1:N optional), `evidence_record` (1:1 optional), `schedule_decision` (via source events).
- `event` is the source of truth; all other runtime tables are materializations.

## 9. Phase 4A scope note

This schema specification is complete for Phase 4A. It does not define:

- SQL DDL or migration scripts.
- Storage engine selection.
- Caching strategy.
- Encryption at rest implementation details.
- Sharding/partitioning.

These are implementation decisions reserved for Phase 4B.
