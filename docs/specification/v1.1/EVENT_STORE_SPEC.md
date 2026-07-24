# MPE v1.1 Event Store Specification

## Scope

This document specifies the event store for the MindTune Protocol Engine v1.1. It is derived from:

- `MPE_EVENT_MODEL_V1_1.md`
- `MPE_OBJECT_MODEL_V1_1.md`
- `MPE_CANONICAL_IDENTIFIER_REGISTRY.md`
- `MPE_CANONICAL_ENUM_REGISTRY.md`

It is implementation-language agnostic and does not prescribe a storage engine, serialization library, or API.

## Legend

| Tag | Meaning |
|---|---|
| **Normative** | Required by MPE v1.1. |
| **Recommended** | Strongly advised for correctness, performance, or auditability. |
| **Optional** | May be omitted in a minimal implementation. |
| **Out of scope** | Not part of Phase 4A. |
| **Implementation note** | Engineering guidance, not an architectural rule. |

## 1. Event envelope

Every event stored in the event store is an immutable record with the following envelope. The envelope is **normative**. Payloads are event-specific and defined in `MPE_EVENT_MODEL_V1_1.md`.

```text
Event
├── event_id              (UUID, immutable event identity)
├── event_type            (string from canonical event taxonomy)
├── schema_version        (string, payload version)
├── session_id            (UUID)
├── session_sequence_number (integer, strictly monotonic per session)
├── protocol_version_id   (UUID)
├── trial_id              (UUID, optional)
├── block_id              (UUID, optional)
├── timestamp             (number, runtime-owned monotonic session time)
├── wallclock_at          (number, optional device wall-clock)
├── component             (string, who emitted it)
├── component_version     (string)
├── correlation_id        (UUID, optional, links request to result)
├── provenance            (list of event_id, causal predecessors)
├── payload               (event-specific object)
├── sensitive             (boolean)
├── data_classification   (enum: public | consent_gated | sensitive_phi | research_sensitive, optional)
└── quality_flags         (list, optional)
```

### 1.1 Field ownership

| Field | Owner | Mutable after append? | Source |
|---|---|---|---|
| `event_id` | Runtime / event store | No | Runtime assigns on append. |
| `event_type` | Emitting component | No | Must be a canonical event type. |
| `schema_version` | Emitting component | No | Declares payload schema version. |
| `session_id` | Runtime | No | From `session_created`. |
| `session_sequence_number` | Event store / runtime | No | Assigned at append. |
| `protocol_version_id` | Runtime | No | From `session_created`. |
| `trial_id` | Runtime | No | Current trial context, if any. |
| `block_id` | Runtime | No | Current block context, if any. |
| `timestamp` | Runtime | No | Runtime monotonic session clock. |
| `wallclock_at` | Component | No | Optional device wall-clock; not authoritative. |
| `component` | Emitting component | No | E.g., `runtime`, `renderer`, `evaluator`. |
| `component_version` | Emitting component | No | Version string. |
| `correlation_id` | Runtime | No | Optional link. |
| `provenance` | Emitting component | No | List of `event_id`s that caused this event. |
| `payload` | Emitting component | No | Event-specific; must conform to `schema_version`. |
| `sensitive` | Emitting component / runtime | No | Boolean flag. |
| `data_classification` | Emitting component / runtime | No | Optional classification; inferred from `sensitive` if omitted. |
| `quality_flags` | Emitting component / runtime | No | Optional event-level quality flags. |

## 2. Append rules

### 2.1 Append-only

- **Normative:** Events are append-only. No event may be deleted, updated, or reordered after append.
- **Normative:** If an erroneous event is appended, a compensating event must be appended; the original event remains.

### 2.2 Monotonic `session_sequence_number`

- **Normative:** Within a `session_id`, `session_sequence_number` must be strictly monotonically increasing without gaps.
- **Normative:** The event store may assign `session_sequence_number`, or the runtime may assign it under the store's validation.
- **Normative:** `session_sequence_number` is the canonical ordering key for events within a session. `event_id` and `timestamp` are not used for ordering.

### 2.3 Monotonic `timestamp`

- **Normative:** `timestamp` counts active session time and must be non-decreasing within a session.
- **Recommended:** `timestamp` should increase for every causal event. Concurrent observation events may share the same `timestamp`; ordering is then resolved by `session_sequence_number`.
- **Implementation note:** Paused time is not counted in `timestamp`. Component timestamps inside `payload` (`rendered_at`, `received_at`, `completed_at`, etc.) are non-authoritative for ordering.

### 2.4 Valid payload

- **Normative:** Before append, the event store must validate the payload against the declared `schema_version` and `event_type`.
- **Normative:** Validation failures must result in a `validation_failed` diagnostic event or an immediate append rejection; the runtime must not silently drop events.
- **Recommended:** Validation should check required fields, enum values against `MPE_CANONICAL_ENUM_REGISTRY.md`, identifier formats, and foreign-key references to already-appended events.

### 2.5 Provenance

- **Normative:** `provenance` must contain only `event_id`s that already exist in the same `session_id`.
- **Recommended:** Every event should include at least one provenance reference unless it is a session-level event (`session_created`, `session_started`).
- **Implementation note:** The runtime may automatically populate `provenance` from the current causal context.

### 2.6 Multi-session isolation

- **Normative:** `session_sequence_number` and `timestamp` monotonicity are enforced per `session_id` only. Different sessions are independent.

## 3. Optimistic concurrency

### 3.1 Append conflict detection

- **Normative:** The event store must reject an append that would violate (`session_id`, `session_sequence_number`) uniqueness.
- **Normative:** The event store must reject an append whose `provenance` references a `session_sequence_number` greater than its own.
- **Recommended:** The event store should reject an append whose `timestamp` is earlier than the `timestamp` of any event in its `provenance`.

### 3.2 Concurrent append model

- **Recommended:** The runtime should use a single writer per `session_id` to guarantee `session_sequence_number` ordering. Multiple readers and asynchronous providers may produce events, but final append serialization is the runtime's responsibility.
- **Implementation note:** If distributed appenders are used, the store must implement a compare-and-swap or conditional append on `session_sequence_number`.

### 3.3 Append transaction boundary

- **Recommended:** An append operation should be atomic with respect to a single event.
- **Out of scope:** Multi-event transactions are not required for Phase 4A.

## 4. Ordering

### 4.1 Canonical ordering

- **Normative:** Events within a session are ordered by (`session_id`, `session_sequence_number`) ascending.
- **Normative:** Ties on `session_sequence_number` are impossible by the append rules.
- **Recommended:** Queries may secondarily order by `timestamp` for human readability, but `session_sequence_number` is authoritative.

### 4.2 Causal ordering

- **Normative:** If event B lists event A in `provenance`, A must appear before B in canonical ordering.
- **Recommended:** The runtime should ensure that causal chains have increasing `session_sequence_number`s. This is guaranteed if `provenance` is validated and `session_sequence_number` is monotonic.

### 4.3 Trial-relative ordering

- **Recommended:** Queries may filter by (`session_id`, `trial_id`) to reconstruct a trial's event subsequence. Trial-relative ordering still uses `session_sequence_number`.

## 5. Replay

### 5.1 Replay definition

- **Normative:** Replay is the deterministic reconstruction of a session's event sequence from the event store given the same `ProtocolVersion`, random seed, and captured observations.

### 5.2 Full replay-determinism

A session is fully replay-deterministic if:

- `ProtocolVersion` is fixed.
- Random seed is fixed.
- All `Observation` inputs are captured.
- All provider outputs (`RenderedStimulus`, `Evaluation`) are captured or the providers are deterministic.
- No external wall-clock dependencies affect the runtime.

### 5.3 Partial replay-determinism

- **Normative:** Phase 4B/4C targets partial replay-determinism: deterministic protocol execution and scheduling with captured observations. Provider timing may vary.

### 5.4 Replay procedure

- **Normative:** Replay reads events in canonical order.
- **Normative:** Replay must restore runtime state from events, not from derived materialized tables.
- **Recommended:** Replay may skip or recompute derived events (`Outcome`, `state_estimate_produced`) if the computation is deterministic and the source events are present.
- **Implementation note:** A replay harness should accept a `session_id`, load all events, and feed them to a deterministic runtime interpreter.

### 5.5 Replay validation

- **Recommended:** A replay should produce a checksum of the emitted event sequence. Comparing two replays of the same inputs should yield identical canonical outputs except for `event_id`, `wallclock_at`, and `session_sequence_number` offsets if re-appended.

## 6. Snapshots

### 6.1 Definition

- **Normative:** A snapshot is a read-only, derived materialization of runtime state at a point in time. It is not a source of truth.

### 6.2 Snapshot types

| Snapshot | Source | Purpose | Refresh trigger |
|---|---|---|---|
| `session` state | `session_created` … terminal event | Query current session status. | On each new session event. |
| `trial` state | `trial_created` … `evaluation_*`/`feedback_completed` | Query trial progress. | On trial events. |
| `outcome` | All session events | Summary statistics. | After `session_completed`/`session_cancelled`/`protocol_terminated`. |
| `provider capability cache` | Provider capability responses | Avoid repeated capability calls. | On provider version change. |

### 6.3 Snapshot invalidation

- **Normative:** Snapshots must be invalidated and recomputed if the underlying event stream changes (e.g., appended events, schema version migration). Event store is source of truth.

## 7. Event versioning

### 7.1 `schema_version`

- **Normative:** Every event payload has a `schema_version`. The envelope `schema_version` refers to the payload, not the envelope itself.
- **Normative:** New payload versions must be additive (new optional fields) unless a formal migration is defined.
- **Normative:** The event store must be able to store and return events with different `schema_version`s within the same session.

### 7.2 Backward compatibility

- **Recommended:** A consumer reading an older `schema_version` should ignore unknown fields and use defaults for missing optional fields.
- **Recommended:** A producer must not emit a `schema_version` newer than the consumer understands unless the consumer is updated.
- **Implementation note:** A schema registry may track valid `schema_version`s per `event_type`.

### 7.3 Migration

- **Out of scope:** Migration of historical event payloads to a new schema is not required for Phase 4A. Consumers must be able to read historical payloads.

## 8. Serialization

### 8.1 Serialization format

- **Recommended:** Events should be serialized as JSON or YAML for Phase 4A/4B fixtures and tests.
- **Recommended:** Binary serialization may be used for storage efficiency in production, but it must be round-trippable and schema-version aware.
- **Normative:** The canonical serialization must preserve all envelope fields and payload fields exactly; no lossy transformation of identifiers, enums, or numbers.

### 8.2 Sensitive data

- **Normative:** Events with `sensitive == true` or `data_classification == sensitive_phi` must be encrypted at rest.
- **Recommended:** Sensitive payloads should be encrypted separately from non-sensitive envelope metadata to allow querying by `event_type`, `session_id`, and `session_sequence_number` without decrypting content.
- **Implementation note:** Key management and consent gating are implementation concerns, but the classification tags in the envelope are required.

### 8.3 Checksums

- **Recommended:** Each stored event should have a content checksum (e.g., over `event_id`, `session_sequence_number`, `timestamp`, `payload`) to detect tampering or storage corruption.
- **Implementation note:** Checksum algorithm is an implementation decision.

## 9. Archival

### 9.1 Archival trigger

- **Recommended:** Completed sessions (status `completed`, `cancelled`, or `terminated`) should be eligible for archival after a configurable retention period.
- **Recommended:** Active sessions should not be archived.

### 9.2 Archival target

- **Recommended:** Archived events should be moved to cold storage with lower retrieval cost and higher durability.
- **Recommended:** Archival should preserve event ordering, provenance, and encryption.
- **Implementation note:** Archival may be implemented as object storage, tape, or another long-term medium.

### 9.3 Archival metadata

- **Recommended:** Each archived session should have an archival record containing `session_id`, `archived_at`, `archive_location`, `event_count`, `checksum`, and `retention_class`.

## 10. Retention

### 10.1 Retention classes

| Class | Definition | Retention guidance |
|---|---|---|
| `public` | Aggregates and correctness results | Long-term, consent-permitting. |
| `consent_gated` | Transcriptions, typed text, self-report | Retention defined by learner consent and study IRB. |
| `sensitive_phi` | Raw audio, raw EEG, biometric data | Minimal retention; encrypted; deleted when consent withdrawn or study ends. |
| `research_sensitive` | State estimates, experimental sensor data | Retention for research; must be consent-gated. |

### 10.2 Retention by event type

- **Normative:** `observation_received` with raw audio or EEG (`sensitive == true`, `data_classification == sensitive_phi`) must be subject to the shortest retention and strongest encryption.
- **Normative:** `response_interpreted` and `domain_response_normalized` with transcribed speech or typed text (`data_classification == consent_gated`) must be retained according to consent.
- **Normative:** `evaluation_completed`/`evaluation_abstained`/`evaluation_failed` (`data_classification == public`) may be retained long-term.
- **Recommended:** `event` records themselves (envelope) may be retained longer than their encrypted payloads.

### 10.3 Deletion

- **Normative:** Deletion of sensitive data must be append-only: an explicit `data_purged` event may be appended to mark that a prior payload is no longer available. The original event envelope remains for audit.
- **Recommended:** Physical deletion of encrypted payload objects may occur after the `data_purged` event is appended.

## 11. Event store operations

### 11.1 Required operations

| Operation | Signature | Description |
|---|---|---|
| `append` | `append(event) -> session_sequence_number` | Validate and append an event. |
| `read_by_session` | `read(session_id, from_seq?, to_seq?) -> list of events` | Return events in canonical order. |
| `read_by_trial` | `read_trial(session_id, trial_id) -> list of events` | Return events for a trial. |
| `get_last_sequence` | `get_last_sequence(session_id) -> integer` | Return highest `session_sequence_number` for a session. |
| `exists` | `exists(event_id) -> boolean` | Check existence. |

### 11.2 Optional operations

| Operation | Description |
|---|---|
| `subscribe` | Stream events for a session. |
| `snapshot` | Materialize derived state. |
| `archive` | Move completed session to cold storage. |

## 12. Phase 4A scope note

This specification is complete for Phase 4A. It does not define:

- Storage engine (database, file system, object store).
- Serialization library.
- Encryption algorithms or key management.
- Distributed consensus protocol.
- Query language or API.

These are implementation decisions reserved for Phase 4B.
