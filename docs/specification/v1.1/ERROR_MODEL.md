# MPE v1.1 Error Model Specification

## Scope

This document enumerates every recoverable and unrecoverable error class for the MindTune Protocol Engine v1.1. It is derived from:

- `MPE_EVENT_MODEL_V1_1.md`
- `MPE_OBJECT_MODEL_V1_1.md`
- `MPE_PROVIDER_BOUNDARIES.md`
- `MPE_HEBREW_PROVIDER_CONTRACT.md`
- `MPE_RISK_REGISTER_V1_1.md`
- `MPE_CANONICAL_ENUM_REGISTRY.md`

All error classifications use canonical enums and identifiers. No new error categories are introduced beyond those in the canonical `error_category` enum and the event taxonomy.

## Legend

| Tag | Meaning |
|---|---|
| **Normative** | Required by MPE v1.1. |
| **Recommended** | Strongly advised for correctness, performance, or auditability. |
| **Optional** | May be omitted in a minimal implementation. |
| **Out of scope** | Not part of Phase 4A. |
| **Implementation note** | Engineering guidance, not an architectural rule. |

## 1. Error classification dimensions

Every error is classified along four dimensions:

- **Severity:** `info`, `warning`, `critical`.
- **Recoverability:** `recoverable` (runtime continues), `degraded` (runtime continues with reduced functionality), `unrecoverable` (session must terminate or cancel).
- **Retry policy:** `none`, `immediate`, `exponential_backoff`, `deferred`.
- **Fallback:** what the runtime does if the error persists.

### Severity mapping

| Severity | Meaning | Generated event severity |
|---|---|---|
| `info` | Diagnostic only; no action required. | `info` |
| `warning` | Degraded experience; may require user notification. | `warning` |
| `critical` | Safety or integrity risk; flow must stop. | `critical` |

## 2. Runtime errors

### 2.1 Invalid fixture

- **Description:** `ProgramVersion` or `ProtocolVersion` does not validate against schema, checksum mismatch, or required provider missing.
- **Severity:** `critical`
- **Recoverability:** `unrecoverable`
- **Retry:** `none`
- **Fallback:** Reject session creation; emit `session_cancelled` or `protocol_terminated` with reason `provider_failure`.
- **Generated events:** `session_cancelled` / `protocol_terminated`.

### 2.2 Session sequence violation

- **Description:** Append attempted with non-monotonic `session_sequence_number` or duplicate (`session_id`, `session_sequence_number`).
- **Severity:** `critical`
- **Recoverability:** `unrecoverable`
- **Retry:** `none`
- **Fallback:** Reject append; runtime enters diagnostic mode.
- **Generated events:** `validation_failed` (optional diagnostic), `protocol_terminated` if corruption detected.

### 2.3 Timestamp violation

- **Description:** Event `timestamp` earlier than a provenance event's `timestamp`.
- **Severity:** `warning`
- **Recoverability:** `degraded`
- **Retry:** `none`
- **Fallback:** Append with corrected `timestamp` equal to provenance `timestamp`; log `warning`.
- **Generated events:** Event appended with `quality_flags` indicating timestamp correction.

### 2.4 State machine transition violation

- **Description:** Event type is not valid for current state (e.g., `response_completed` without `response_window_opened`).
- **Severity:** `warning`
- **Recoverability:** `recoverable`
- **Retry:** `none`
- **Fallback:** Reject invalid event; emit `validation_failed` or `safety_rule_triggered`.
- **Generated events:** `validation_failed`.

## 3. Provider errors

### 3.1 Provider not found

- **Description:** Required provider is not registered or does not respond to capabilities.
- **Severity:** `critical`
- **Recoverability:** `unrecoverable`
- **Retry:** `immediate` 2 times during session start.
- **Fallback:** If still unavailable, `protocol_terminated` with reason `provider_failure`.
- **Generated events:** `protocol_terminated`.

### 3.2 Provider version mismatch

- **Description:** Running provider version does not match `ProtocolVersion.dependency_versions`.
- **Severity:** `critical`
- **Recoverability:** `unrecoverable`
- **Retry:** `none`
- **Fallback:** `protocol_terminated` or `evaluation_failed` depending on when detected.
- **Generated events:** `protocol_terminated` / `evaluation_failed`.

### 3.3 Provider timeout

- **Description:** Provider did not respond within configured timeout.
- **Severity:** `warning`
- **Recoverability:** `degraded`
- **Retry:** per provider policy (Renderer: 1; Evaluator: 0; Scheduler: 0).
- **Fallback:** Use provider-specific fallback (e.g., `renderer_fallback`, `evaluation_failed`, `response_timeout`).
- **Generated events:** `renderer_fallback`, `evaluation_failed`, `response_timeout`.

## 4. Network errors

### 4.1 Transient network failure

- **Description:** Short-lived network partition between runtime and remote provider.
- **Severity:** `warning`
- **Recoverability:** `recoverable`
- **Retry:** `exponential_backoff` up to 3 attempts.
- **Fallback:** If retries exhausted, treat as provider timeout.
- **Generated events:** `signal_quality_changed`, `provider_timeout` (diagnostic), then provider-specific fallback event.

### 4.2 Persistent network failure

- **Description:** Network unavailable for the duration of the session.
- **Severity:** `critical`
- **Recoverability:** `unrecoverable`
- **Retry:** `deferred` until user action.
- **Fallback:** `session_cancelled` with reason `device_error`.
- **Generated events:** `session_cancelled`.

## 5. Storage errors

### 5.1 Append failure

- **Description:** Event store cannot append event.
- **Severity:** `critical`
- **Recoverability:** `unrecoverable`
- **Retry:** `immediate` 2 times.
- **Fallback:** If persists, `protocol_terminated` with reason `unrecoverable_error`.
- **Generated events:** `protocol_terminated`.

### 5.2 Read failure

- **Description:** Event store cannot read events for replay or query.
- **Severity:** `critical`
- **Recoverability:** `unrecoverable` for replay; `degraded` for live queries.
- **Retry:** `immediate` 2 times.
- **Fallback:** For replay, abort replay. For live query, return stale snapshot if available.
- **Generated events:** `protocol_terminated` (replay), `validation_failed` (query).

### 5.3 Archival failure

- **Description:** Completed session cannot be archived.
- **Severity:** `warning`
- **Recoverability:** `degraded`
- **Retry:** `exponential_backoff` deferred.
- **Fallback:** Retain in hot storage; alert operations.
- **Generated events:** `validation_failed` (diagnostic).

## 6. Hebrew provider errors

### 6.1 Hebrew engine abstention

- **Description:** `HebrewEvaluator` deliberately declines to judge (unknown input, ambiguous form).
- **Severity:** `info`
- **Recoverability:** `recoverable`
- **Retry:** `none`
- **Fallback:** Runtime emits `evaluation_abstained`; does not score; continues with neutral feedback or re-prompt.
- **Generated events:** `evaluation_abstained`.

### 6.2 Hebrew engine failure

- **Description:** `HebrewEvaluator` engine exception, malformed output, or version mismatch.
- **Severity:** `warning`
- **Recoverability:** `degraded`
- **Retry:** `none`
- **Fallback:** Runtime emits `evaluation_failed`; continues gracefully; may terminate trial.
- **Generated events:** `evaluation_failed`.

### 6.3 Out-of-scope Hebrew form

- **Description:** Expected item is outside the validated subset or engine refuses to evaluate.
- **Severity:** `info`
- **Recoverability:** `recoverable`
- **Retry:** `none`
- **Fallback:** Runtime emits `evaluation_abstained` or `evaluation_failed` with `evaluation_status == out_of_scope`; does not present item as authoritative.
- **Generated events:** `evaluation_abstained` / `evaluation_failed`.

### 6.4 Normalization ambiguity

- **Description:** `HebrewDomainNormalizer` cannot uniquely canonicalize the response.
- **Severity:** `warning`
- **Recoverability:** `recoverable`
- **Retry:** `none`
- **Fallback:** Emit `domain_response_normalized` with high `uncertainty`; evaluator may abstain.
- **Generated events:** `domain_response_normalized`, `evaluation_abstained`.

## 7. Renderer errors

### 7.1 Render failure

- **Description:** `Renderer` cannot generate media for `StimulusRequest`.
- **Severity:** `warning`
- **Recoverability:** `degraded`
- **Retry:** 1 retry with fallback voice/format.
- **Fallback:** If persistent, emit `renderer_fallback` and use text fallback or skip stimulus.
- **Generated events:** `renderer_fallback` (diagnostic), `stimulus_ready` with fallback, `feedback_started` with fallback.

### 7.2 Voice unavailable

- **Description:** Requested `voice_id` not supported.
- **Severity:** `warning`
- **Recoverability:** `recoverable`
- **Retry:** `none`
- **Fallback:** Use default voice.
- **Generated events:** `stimulus_ready` with default voice; `renderer_fallback` optional.

### 7.3 Pronunciation metadata unsupported

- **Description:** TTS engine cannot use `pronunciation_metadata`.
- **Severity:** `info`
- **Recoverability:** `recoverable`
- **Retry:** `none`
- **Fallback:** Render `surface_form`; log `renderer_fallback`.
- **Generated events:** `renderer_fallback`.

## 8. Observation errors

### 8.1 Device disconnected

- **Description:** `ObservationProvider` reports sensor/microphone disconnected.
- **Severity:** `warning`
- **Recoverability:** `degraded`
- **Retry:** `exponential_backoff` up to 3 attempts.
- **Fallback:** If persistent, trigger `safety_rule_triggered` with action `offer_end` or fallback to button response mode.
- **Generated events:** `signal_quality_changed`, `safety_rule_triggered`.

### 8.2 Buffer overflow

- **Description:** Provider dropped observations due to buffer limits.
- **Severity:** `warning`
- **Recoverability:** `degraded`
- **Retry:** `none`
- **Fallback:** Continue with available observations; record `quality_flags`.
- **Generated events:** `observation_received` with `quality_flags` indicating drop.

### 8.3 Raw signal quality critical

- **Description:** Signal quality fell below usable threshold.
- **Severity:** `warning` or `critical` depending on rule.
- **Recoverability:** `degraded` or `unrecoverable`.
- **Retry:** `none`
- **Fallback:** `signal_quality_changed` event; safety rule may pause or terminate.
- **Generated events:** `signal_quality_changed`, `safety_rule_triggered`.

### 8.4 Unsupported response mode

- **Description:** Provider cannot support requested `response_mode` for a trial.
- **Severity:** `warning`
- **Recoverability:** `degraded`
- **Retry:** `none`
- **Fallback:** Use another `accepted_response_mode` or emit `response_timeout`.
- **Generated events:** `response_timeout`.

## 9. Evaluation errors

### 9.1 Evaluator timeout

- **Description:** `Evaluator` did not return within timeout.
- **Severity:** `warning`
- **Recoverability:** `degraded`
- **Retry:** `none`
- **Fallback:** Emit `evaluation_failed`; continue with neutral scheduling.
- **Generated events:** `evaluation_failed`.

### 9.2 Evaluator version mismatch

- **Description:** `Evaluator` version does not match protocol dependency.
- **Severity:** `critical`
- **Recoverability:** `unrecoverable`
- **Retry:** `none`
- **Fallback:** `evaluation_failed` for current trial; if detected at session start, `protocol_terminated`.
- **Generated events:** `evaluation_failed` / `protocol_terminated`.

### 9.3 Empty or invalid normalized payload

- **Description:** `DomainNormalizedResponse.normalized_payload` is empty or not valid for evaluator.
- **Severity:** `warning`
- **Recoverability:** `recoverable`
- **Retry:** `none`
- **Fallback:** Emit `evaluation_abstained` or `evaluation_failed`.
- **Generated events:** `evaluation_abstained` / `evaluation_failed`.

## 10. Adaptation errors

- **Phase applicability:** Phase 5A+. Not applicable to Phase 4.

### 10.1 Policy bounds violation

- **Description:** `AdaptationDecision.proposed_value` outside `allowed_bounds`.
- **Severity:** `warning`
- **Recoverability:** `recoverable`
- **Retry:** `none`
- **Fallback:** Change decision to `REVERSE` or `ABSTAIN`; emit `adaptation_abstained`/`adaptation_reversed`.
- **Generated events:** `adaptation_abstained` / `adaptation_reversed`.

### 10.2 Insufficient evidence

- **Description:** Policy does not meet `minimum_evidence`.
- **Severity:** `info`
- **Recoverability:** `recoverable`
- **Retry:** `deferred` until next window.
- **Fallback:** Emit `adaptation_abstained`.
- **Generated events:** `adaptation_abstained`.

### 10.3 Shadow mode apply attempt

- **Description:** Policy in `shadow_mode` or `exploratory_only` attempts to apply an adaptation.
- **Severity:** `critical`
- **Recoverability:** `unrecoverable`
- **Retry:** `none`
- **Fallback:** Reject apply; emit `adaptation_abstained`; escalate to `safety_rule_triggered` if repeated.
- **Generated events:** `adaptation_abstained`, `safety_rule_triggered` (if repeated).

## 11. Safety errors

### 11.1 Safety rule trigger

- **Description:** Safety rule condition matched.
- **Severity:** `warning` or `critical` depending on rule.
- **Recoverability:** `degraded` or `unrecoverable`.
- **Retry:** `none`
- **Fallback:** Execute `action_taken`: `pause`, `terminate`, `volume_limit`, `offer_end`, `insert_recovery`.
- **Generated events:** `safety_rule_triggered`, `safety_instruction_started`, `session_paused`, `protocol_terminated`, `recovery_inserted`.

### 11.2 Safety action failure

- **Description:** Safety action could not be executed (e.g., pause command not delivered).
- **Severity:** `critical`
- **Recoverability:** `unrecoverable`
- **Retry:** 1 immediate retry.
- **Fallback:** Escalate to `protocol_terminated`.
- **Generated events:** `protocol_terminated`.

### 11.3 Maximum session duration exceeded

- **Description:** Session ran longer than protocol-defined maximum.
- **Severity:** `warning`
- **Recoverability:** `recoverable`
- **Retry:** `none`
- **Fallback:** `safety_rule_triggered` with `action_taken == offer_end`; if ignored, `protocol_terminated`.
- **Generated events:** `safety_rule_triggered`, `protocol_terminated`.

## 12. Error-to-event mapping summary

| Error | Primary generated event | Escalation event |
|---|---|---|
| Invalid fixture | `session_cancelled` / `protocol_terminated` | — |
| Sequence/timestamp violation | `validation_failed` | `protocol_terminated` |
| Provider not found / version mismatch | `protocol_terminated` / `evaluation_failed` | — |
| Provider timeout | `renderer_fallback`, `evaluation_failed`, `response_timeout` | `protocol_terminated` if systemic |
| Network transient | `signal_quality_changed` | provider timeout fallback |
| Network persistent | `session_cancelled` | — |
| Storage append failure | `protocol_terminated` | — |
| Hebrew engine abstention | `evaluation_abstained` | — |
| Hebrew engine failure | `evaluation_failed` | — |
| Render failure | `renderer_fallback` | `safety_rule_triggered` if persistent |
| Device disconnected | `signal_quality_changed` | `safety_rule_triggered` |
| Safety rule trigger | `safety_rule_triggered` | `protocol_terminated` if action fails |
| Adaptation bounds/shadow violation | `adaptation_abstained` / `adaptation_reversed` | `safety_rule_triggered` if repeated |

## 13. Phase 4A scope note

This error model is complete for Phase 4A. It does not define:

- Concrete exception types or error codes for a specific language.
- Logging framework.
- Alerting/operations integration.
- Circuit-breaker implementation.

These are implementation decisions reserved for Phase 4B.
