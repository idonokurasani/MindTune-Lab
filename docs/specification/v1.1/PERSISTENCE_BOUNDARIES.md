# MPE v1.1 Persistence Boundaries Specification

## Scope

This document classifies every object in the MPE v1.1 object model according to its persistence boundary and explains how each object is reconstructed. It is derived from:

- `MPE_OBJECT_MODEL_V1_1.md`
- `MPE_EVENT_MODEL_V1_1.md`
- `MPE_OBJECT_EVENT_COVERAGE_MATRIX.csv`
- `MPE_CANONICAL_IDENTIFIER_REGISTRY.md`

## Legend

| Classification | Meaning | Durability |
|---|---|---|
| `persistent` | Must be durably stored before the operation that produced it is considered complete. | Durable. |
| `derived` | Computed from persisted data; may be cached or materialized. | Reconstructable. |
| `cached` | Copy of persistent or derived data kept for performance; safe to discard. | Reconstructable. |
| `ephemeral` | Exists only during active processing; not durable. | Not reconstructable. |
| `stream-only` | Stored only as events; object view is a projection. | Reconstructable from event stream. |

## 1. Static registry objects

These fixtures are authored before runtime and loaded at session start.

| Object | Classification | Reconstruction | Notes |
|---|---|---|---|
| `Program` | persistent | Loaded from registry. | Logical identity only. |
| `ProgramVersion` | persistent | Loaded from registry by `program_version_id`. | Immutable executable definition. |
| `Protocol` | persistent | Loaded from registry. | Logical identity only. |
| `ProtocolVersion` | persistent | Loaded from registry by `protocol_version_id`. | Immutable executable definition. |
| `TaskDefinition` | persistent | Loaded from registry. | Reusable trial template. |
| `ContentItem` | persistent / cached | Loaded from `DomainProvider`; may be cached in MPE storage. | Domain provider is authoritative. |
| `SafetyProfile` | persistent | Loaded from registry by `safety_profile_id`. | Static fixture. |

## 2. Session and block objects

| Object | Classification | Reconstruction | Notes |
|---|---|---|---|
| `Session` | derived / stream-only | Reconstructed by querying events with `session_id`. | `session_created`, `session_started`, etc. |
| `Block` (definition) | persistent | Embedded in `ProtocolVersion`. | Immutable. |
| `BlockExecution` | derived / stream-only | `block_started` and `block_completed` events. | Runtime materialization. |

## 3. Trial objects

| Object | Classification | Reconstruction | Notes |
|---|---|---|---|
| `Trial` | derived / stream-only | `trial_created` event. | Immutable plan; runtime state derived. |
| `Instruction` | derived / stream-only | `instruction_started` and `instruction_completed` events. | |
| `StimulusRequest` | stream-only | `stimulus_requested` event. | |
| `RenderedStimulus` | persistent | `stimulus_ready` event; media handle may reference durable media store. | Capture required for exact replay. |
| `ResponseWindow` | stream-only | `response_window_opened`, `response_timeout` events. | |

## 4. Response pipeline objects

| Object | Classification | Reconstruction | Notes |
|---|---|---|---|
| `Observation` | persistent | `observation_received` event. | Raw input; must be durable. |
| `SensorObservation` | persistent | `observation_received` with `observation_type == sensor_feature`. | |
| `CapturedResponse` | persistent | `captured_response_created` event. | |
| `ResponseInterpretation` | persistent | `response_interpreted` event. | Capture required for ASR replay. |
| `DomainNormalizedResponse` | persistent | `domain_response_normalized` event. | |
| `Evaluation` | persistent | `evaluation_completed`, `evaluation_abstained`, `evaluation_failed` events. | |

## 5. Feedback and safety objects

| Object | Classification | Reconstruction | Notes |
|---|---|---|---|
| `FeedbackEvent` | persistent | `feedback_started`, `feedback_completed` events. | |
| `SafetyInstruction` | persistent | `safety_instruction_started`, `safety_instruction_completed` events. | |
| `SafetyEvent` | persistent | `safety_rule_triggered`, `recovery_inserted`, `protocol_terminated` events. | |

## 6. Decision and evidence objects

| Object | Classification | Reconstruction | Notes |
|---|---|---|---|
| `ScheduleDecision` | persistent | `schedule_decision` event. | |
| `AdaptationDecision` | persistent | `adaptation_proposed`, `adaptation_abstained`, `adaptation_applied`, `adaptation_reversed` events. | Phase 5A+. |
| `EvidenceRecord` | persistent | `evidence_record_created` event. | |

## 7. State and outcome objects

| Object | Classification | Reconstruction | Notes |
|---|---|---|---|
| `StateEstimate` | derived / diagnostic | `state_estimate_produced` event. | Phase 5B+; not used for runtime control. |
| `Outcome` | derived | Computed from all session events. | Read-only summary. |

## 8. Event store

| Object | Classification | Reconstruction | Notes |
|---|---|---|---|
| `Event` | persistent | Stored append-only in event store. | Source of truth. |

## 9. Reconstruction rules

### 9.1 Event stream as source of truth

- **Normative:** All `stream-only` and `derived` objects must be reconstructable from the `Event` stream in canonical order.
- **Normative:** The `Event` store is append-only and immutable.

### 9.2 Materialized views

- **Recommended:** The runtime may maintain materialized views of `Session`, `Trial`, `BlockExecution`, `Outcome` for query performance.
- **Normative:** Materialized views are not authoritative; they must be invalidated and rebuilt if the underlying event stream changes.

### 9.3 Provider caches

- **Recommended:** `ContentItem` and provider capability responses may be cached.
- **Normative:** Cached data must be validated against provider `checksum`/`provider_version` before use.

### 9.4 Media storage

- **Recommended:** `RenderedStimulus.media_handle` may reference a durable media store (file, object storage).
- **Normative:** The event store stores the `RenderedStimulus` metadata, not the binary media, unless the media is small enough to embed.

### 9.5 Sensitive data

- **Normative:** `Observation` payloads with raw audio/EEG and `CapturedResponse` payloads with raw voice samples must be encrypted at rest and consent-gated.
- **Recommended:** Sensitive payloads may be stored in a separate encrypted object store linked by `observation_id`/`captured_response_id`.

## 10. Summary table

| Object | Persistent | Derived | Cached | Ephemeral | Stream-only |
|---|---|---|---|---|---|
| `Program` | X | | | | |
| `ProgramVersion` | X | | | | |
| `Protocol` | X | | | | |
| `ProtocolVersion` | X | | | | |
| `TaskDefinition` | X | | | | |
| `ContentItem` | X | | X | | |
| `SafetyProfile` | X | | | | |
| `Session` | | X | X | | X |
| `BlockExecution` | | X | X | | X |
| `Trial` | | X | X | | X |
| `Instruction` | | X | X | | X |
| `StimulusRequest` | | | | | X |
| `RenderedStimulus` | X | | | | X |
| `ResponseWindow` | | | | | X |
| `Observation` | X | | | | X |
| `SensorObservation` | X | | | | X |
| `CapturedResponse` | X | | | | X |
| `ResponseInterpretation` | X | | | | X |
| `DomainNormalizedResponse` | X | | | | X |
| `Evaluation` | X | | | | X |
| `FeedbackEvent` | X | | | | X |
| `SafetyInstruction` | X | | | | X |
| `SafetyEvent` | X | | | | X |
| `ScheduleDecision` | X | | | | X |
| `AdaptationDecision` | X | | | | X |
| `EvidenceRecord` | X | | | | X |
| `StateEstimate` | | X | | | X |
| `Outcome` | | X | X | | |
| `Event` | X | | | | |

## 11. Phase 4A scope note

This specification is complete for Phase 4A. It does not define:

- Storage engine selection.
- Cache invalidation strategy.
- Encryption implementation.
- Media storage backend.
- Materialized view refresh scheduling.

These are implementation decisions reserved for Phase 4B.
