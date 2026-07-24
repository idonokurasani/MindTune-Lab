# MPE v1.1 Final Corrections Required

## Summary

This document lists all unresolved corrections identified during the cross-document audit. Each correction includes severity, affected documents, the exact change required, whether it blocks Phase 4A, and an acceptance test.

Severities:

- **High** — contradicts the architecture or would lead to an inconsistent Phase 4A schema.
- **Medium** — creates ambiguity, stale terminology, or audit/replay gaps.
- **Low** — editorial or optional clarification.

---

### C-001: `session_created` event payload uses wrong program identifier

- **Severity:** High
- **Affected documents:** `MPE_EVENT_MODEL_V1_1.md` §`session_created`
- **Exact correction:** Change payload from `session_id, protocol_version_id, learner_id, program_id` to `session_id, program_version_id, protocol_version_id, learner_id`. Remove `program_id`; the event must reference the immutable executable `ProgramVersion`, not the logical `Program`.
- **Blocking status:** Blocks Phase 4A (schema cannot be canonical if the event references a non-existent Session field).
- **Acceptance test:** Grep `MPE_EVENT_MODEL_V1_1.md` for `session_created` payload and confirm it contains `program_version_id` and not `program_id`; confirm `MPE_OBJECT_MODEL_V1_1.md` Session matches.

---

### C-002: `trial_created` event payload uses obsolete `expected_response_mode`

- **Severity:** High
- **Affected documents:** `MPE_EVENT_MODEL_V1_1.md` §`trial_created`
- **Exact correction:** Replace `expected_response_mode` with `response_requirement` (`required` | `optional` | `none`) and add optional `accepted_response_modes` list, matching `MPE_OBJECT_MODEL_V1_1.md` Trial.
- **Blocking status:** Blocks Phase 4A (schema mismatch between object and event model).
- **Acceptance test:** Grep `MPE_EVENT_MODEL_V1_1.md` for `trial_created` payload and confirm it contains `response_requirement` and `accepted_response_modes`; confirm no occurrence of `expected_response_mode` outside historical review text.

---

### C-003: `MPE_HEBREW_PROVIDER_CONTRACT.md` still uses old `NormalizedResponse` and `verdict` semantics

- **Severity:** High
- **Affected documents:** `MPE_HEBREW_PROVIDER_CONTRACT.md` §3 HebrewEvaluator, §Verdict semantics, §MPE handling categories
- **Exact correction:**
  1. Rename input object from `NormalizedResponse` to `DomainNormalizedResponse` and use its field names (`domain_normalized_response_id`, `response_mode`, `normalized_payload`, `extracted_at`, `uncertainty`).
  2. Replace `verdict` with `answer_status` and `evaluation_status`.
  3. Replace `accepted_variant` with `accepted_variant_id`.
  4. Add `correctness_credit`, `scope_status`, `evidence_group`, `failure_reason`.
  5. Update the handling categories to reference `answer_status`, `evaluation_status`, `accepted_variant_id`, and `scope_status`.
- **Blocking status:** Blocks Phase 4A (the Hebrew provider contract is a Phase 4C dependency and must match the object/event model).
- **Acceptance test:** Grep `MPE_HEBREW_PROVIDER_CONTRACT.md` and confirm no occurrences of `NormalizedResponse` (as input object), `verdict`, `accepted_variant` (without `_id`), or `partial`; confirm `answer_status` and `evaluation_status` appear in the output definition and handling categories.

---

### C-004: `MPE_ADAPTATION_CONTRACT.md` still contains removed `audit_event_id`

- **Severity:** High
- **Affected documents:** `MPE_ADAPTATION_CONTRACT.md` §AdaptationDecision schema
- **Exact correction:** Remove `audit_event_id` from the `AdaptationDecision` ASCII diagram and any prose. Document that events reference `adaptation_decision_id`, not the reverse.
- **Blocking status:** Blocks Phase 4A (circular reference reintroduced).
- **Acceptance test:** Grep `MPE_ADAPTATION_CONTRACT.md` for `audit_event_id`; confirm zero matches outside historical references. Confirm `MPE_OBJECT_MODEL_V1_1.md`, `MPE_EVENT_MODEL_V1_1.md`, and `MPE_V1_0_CRITICAL_REVIEW.md` are mutually consistent.

---

### C-005: `MPE_EVENT_MODEL_V1_1.md` missing `session_sequence_number`

- **Severity:** High
- **Affected documents:** `MPE_EVENT_MODEL_V1_1.md` §Event payload shape
- **Exact correction:** Add `session_sequence_number` (strictly monotonic per session integer) to the common event fields. Document that UUID ordering is never used as canonical ordering; ties on `timestamp` are resolved by `session_sequence_number`.
- **Blocking status:** Blocks Phase 4A (replay and ordering semantics undefined without it).
- **Acceptance test:** Grep `MPE_EVENT_MODEL_V1_1.md` common event fields for `session_sequence_number`; confirm `event_id` is not described as a tie-breaker.

---

### C-006: Response pipeline objects missing events

- **Severity:** High
- **Affected documents:** `MPE_EVENT_MODEL_V1_1.md` §Canonical event taxonomy
- **Exact correction:** Add `captured_response_recorded` and `response_interpreted` events with payloads matching `MPE_OBJECT_MODEL_V1_1.md` `CapturedResponse` and `ResponseInterpretation`. If these are intentionally collapsed, explicitly state that they are embedded in `observation_received` and `response_normalized` and show the embedded fields.
- **Blocking status:** Blocks Phase 4A (response pipeline cannot be replayed or audited without explicit events for all layers).
- **Acceptance test:** Confirm events for `CapturedResponse` and `ResponseInterpretation` exist or are explicitly embedded with `captured_response_id` and `response_interpretation_id` in other event payloads.

---

### C-007: `MPE_HEBREW_PROVIDER_CONTRACT.md` / `MPE_OBJECT_MODEL_V1_1.md` `ContentItem` field mismatch

- **Severity:** High
- **Affected documents:** `MPE_OBJECT_MODEL_V1_1.md` §ContentItem, `MPE_HEBREW_PROVIDER_CONTRACT.md` §ContentItem fields
- **Exact correction:** Add `status` and `abstention_status` to `MPE_OBJECT_MODEL_V1_1.md` `ContentItem` required/optional fields (values `verified_consensus` | `high_confidence_candidate` | `unresolved` | `rejected`). Align `status` with `Evaluation.scope_status` and `ContentItem.scope`.
- **Blocking status:** Blocks Phase 4A (Hebrew contract relies on fields the object model does not define).
- **Acceptance test:** Confirm `MPE_OBJECT_MODEL_V1_1.md` ContentItem defines `status` and `abstention_status`; confirm `MPE_HEBREW_PROVIDER_CONTRACT.md` ContentItem matches.

---

### C-008: Ambiguous `normalized_response_id` identifier

- **Severity:** Medium
- **Affected documents:** `MPE_OBJECT_MODEL_V1_1.md` §Evaluation, `MPE_EVENT_MODEL_V1_1.md` §`response_normalized`, §`evaluation_completed`
- **Exact correction:** Rename `normalized_response_id` to `domain_normalized_response_id` in all three locations. Rename `DomainNormalizedResponse` primary field from `id` to `domain_normalized_response_id`.
- **Blocking status:** Non-blocking but required for schema clarity before Phase 4A implementation.
- **Acceptance test:** Grep `docs/` for `normalized_response_id`; confirm only `domain_normalized_response_id` remains.

---

### C-009: `Observation` / `SensorObservation` quality model not consistently applied

- **Severity:** Medium
- **Affected documents:** `MPE_EVENT_MODEL_V1_1.md` §`observation_received`, §`signal_quality_changed`; `MPE_PROVIDER_BOUNDARIES.md` §`ObservationProvider`; `MPE_ADAPTATION_CONTRACT.md` §Abstention reasons; `MPE_OBJECT_MODEL_V1_1.md` §`SensorObservation`
- **Exact correction:** Replace generic `quality_score`/`quality_metrics` with `quality_dimensions`, `quality_flags`, `quality_model_id`, `quality_model_version`, and optional `overall_quality` in all of the above.
- **Blocking status:** Non-blocking for Phase 4A schema (can be optional field set) but must be resolved before Phase 4B.
- **Acceptance test:** Grep `docs/` for `quality_score` outside historical review text and `MINDTUNE_PROTOCOL_ENGINE_ARCHITECTURE_v1.0.md`; confirm zero matches or only in context of "replaced by quality model".

---

### C-010: `signal_quality_changed` event is malformed

- **Severity:** Medium
- **Affected documents:** `MPE_EVENT_MODEL_V1_1.md` §`signal_quality_changed`
- **Exact correction:** Add `session_id` to payload; rename payload `timestamp` to `observed_at` or `component_timestamp`; use the common `timestamp` field for runtime-owned time; replace `quality_score` with quality model fields.
- **Blocking status:** Non-blocking for Phase 4A but required for correct event taxonomy.
- **Acceptance test:** Confirm payload contains `session_id` and does not shadow the common `timestamp` field.

---

### C-011: `MPE_ARCHITECTURE_V1_1.md` philosophy statement implies validated optimal state

- **Severity:** Medium
- **Affected documents:** `MPE_ARCHITECTURE_V1_1.md` §2 Philosophy
- **Exact correction:** Reword "The goal is an optimal cognitive state, not maximum speed." to "The system aims to help the learner maintain a productive cognitive state; whether a single optimal state exists is an experimental hypothesis, not an architecture axiom."
- **Blocking status:** Non-blocking but required before scientific claim consistency can be certified.
- **Acceptance test:** Grep `MPE_ARCHITECTURE_V1_1.md` for "optimal cognitive state"; confirm it is qualified as experimental/hypothetical or removed.

---

### C-012: Pause/resume and monotonic clock semantics undefined

- **Severity:** Medium
- **Affected documents:** `MPE_EVENT_MODEL_V1_1.md` §Event ordering guarantees, §`session_paused`, §`session_resumed`; `MPE_ARCHITECTURE_V1_1.md`
- **Exact correction:** Document:
  1. Whether paused time counts in `timestamp`.
  2. Whether scheduled stimuli `scheduled_for` are shifted after resume.
  3. Whether response latency excludes paused intervals.
  4. How late provider events are ordered relative to `session_sequence_number`.
- **Blocking status:** Non-blocking for Phase 4A schema design, but blocks Phase 4B runtime specification.
- **Acceptance test:** Confirm the event model or architecture document contains explicit answers to all four questions.

---

### C-013: `MPE_PHASE_4_IMPLEMENTATION_PLAN.md` uses obsolete verdict language

- **Severity:** Medium
- **Affected documents:** `MPE_PHASE_4_IMPLEMENTATION_PLAN.md` §What Phase 4C must not do
- **Exact correction:** Replace "Hebrew recall trials evaluate responses with `correct`/`incorrect`/`acceptable_variant`/`abstained` verdicts" and "`abstained` verdicts are scored as incorrect" with the `answer_status`/`evaluation_status` model. `abstained`/`unevaluable` must not be scored as incorrect; `partially_correct` and `acceptable_variant` must be separate.
- **Blocking status:** Non-blocking for Phase 4A but blocks Phase 4C acceptance criteria.
- **Acceptance test:** Confirm plan uses only `answer_status` and `evaluation_status` values and does not equate abstention with incorrect.

---

### C-014: `CapturedResponse` primary identifier not canonical

- **Severity:** Medium
- **Affected documents:** `MPE_OBJECT_MODEL_V1_1.md` §`CapturedResponse`
- **Exact correction:** Rename primary field `id` to `captured_response_id` so that references in `ResponseInterpretation` and events are unambiguous.
- **Blocking status:** Non-blocking but required for schema consistency.
- **Acceptance test:** Confirm `MPE_OBJECT_MODEL_V1_1.md` `CapturedResponse` lists `captured_response_id` as a required field.

---

### C-015: `state_estimate_produced` event lacks `state_estimate_id`

- **Severity:** Low
- **Affected documents:** `MPE_EVENT_MODEL_V1_1.md` §`state_estimate_produced`
- **Exact correction:** Add `state_estimate_id` to the payload.
- **Blocking status:** Non-blocking.
- **Acceptance test:** Confirm payload contains `state_estimate_id`.

---

### C-016: `Outcome` latency summary structure undefined

- **Severity:** Low
- **Affected documents:** `MPE_OBJECT_MODEL_V1_1.md` §`Outcome`
- **Exact correction:** Define the shape of `latency_summaries` (stratified by `task_definition`, `response_mode`, `trial_role`, `item_class`) including median/quantile/distribution summary fields.
- **Blocking status:** Non-blocking for Phase 4A.
- **Acceptance test:** Confirm `Outcome` defines a nested structure for `latency_summaries`.

---

### C-017: `instruction_started` event payload does not match `Instruction` object

- **Severity:** Low
- **Affected documents:** `MPE_EVENT_MODEL_V1_1.md` §`instruction_started`
- **Exact correction:** Add `instruction_payload`, `target_operation`, and `observable_response_expected` to the payload (or document that these are derived from `instruction_id`). Ensure `content_item_id` is optional and does not duplicate `instruction_payload`.
- **Blocking status:** Non-blocking for Phase 4A.
- **Acceptance test:** Confirm `instruction_started` payload includes `instruction_payload` or a clear note that it is fetched by `instruction_id`.

---

### C-018: `transfer_claim_level` spelling inconsistent

- **Severity:** Low
- **Affected documents:** `MPE_OBJECT_MODEL_V1_1.md` §Program, §ProtocolVersion; `MPE_CANONICAL_ENUM_REGISTRY.md`
- **Exact correction:** Choose either `trained-task-performance` (hyphenated) or `trained_task_performance` (underscore) and apply consistently across all documents. The audit registries currently prefer `trained_task_performance`.
- **Blocking status:** Non-blocking.
- **Acceptance test:** Grep `docs/` for both forms; confirm only the canonical form remains.

---

## Correction pass closure

All blocking corrections (C-001 through C-007) and all medium/low issues (C-008 through C-018) have been applied. The second-pass cross-document audit found no remaining high-severity inconsistency.

| Issue | Original severity | Status | Blocking status | Correction applied | Exact sections changed | Acceptance evidence |
|---|---|---|---|---|---|---|
| C-001 | High | **RESOLVED** | No longer blocking | `session_created` payload changed from `program_id` to `program_version_id`; `session_started` also carries `program_version_id`. | `MPE_EVENT_MODEL_V1_1.md` §`session_created`, §`session_started`; `MPE_OBJECT_MODEL_V1_1.md` §Session | Grep confirms `session_created` payload contains `program_version_id` and no `program_id`. |
| C-002 | High | **RESOLVED** | No longer blocking | `trial_created` payload uses `response_requirement` and `accepted_response_modes`; removed `expected_response_mode`. | `MPE_EVENT_MODEL_V1_1.md` §`trial_created` | Grep confirms `trial_created` contains `response_requirement` and `accepted_response_modes`. |
| C-003 | High | **RESOLVED** | No longer blocking | Hebrew contract uses `DomainNormalizedResponse` input, `answer_status`/`evaluation_status` output, `accepted_variant_id`, `correctness_credit`, `scope_status`, `evidence_group`, `failure_reason`; handling categories rewritten. | `MPE_HEBREW_PROVIDER_CONTRACT.md` §3 HebrewEvaluator, §Answer status semantics, §Evaluation status semantics, §MPE handling categories | Grep confirms no `verdict` or `accepted_variant` (without `_id`) or `NormalizedResponse` (as input). |
| C-004 | High | **RESOLVED** | No longer blocking | Removed `audit_event_id` from `AdaptationDecision` schema; `source_event_ids` and `evidence_record_ids` used. | `MPE_ADAPTATION_CONTRACT.md` §AdaptationDecision schema; `MPE_OBJECT_MODEL_V1_1.md` §AdaptationDecision | Grep confirms `audit_event_id` absent. |
| C-005 | High | **RESOLVED** | No longer blocking | Added `session_sequence_number` to common event fields; replaced `event_id` tie-breaker with `session_sequence_number`. | `MPE_EVENT_MODEL_V1_1.md` §Event payload shape, §Event ordering guarantees, §Session clock and pause semantics | Grep confirms `session_sequence_number` in common fields. |
| C-006 | High | **RESOLVED** | No longer blocking | Added `captured_response_created`, `response_interpreted`, `domain_response_normalized`, `evaluation_failed`, `evidence_record_created` events; updated object/event relations. | `MPE_EVENT_MODEL_V1_1.md` §Canonical event taxonomy; `MPE_OBJECT_MODEL_V1_1.md` §CapturedResponse, §ResponseInterpretation, §DomainNormalizedResponse, §EvidenceRecord, §Evaluation | Grep confirms event names present and object relation updated. |
| C-007 | High | **RESOLVED** | No longer blocking | Added `status` and `abstention_status` to `ContentItem` object model. | `MPE_OBJECT_MODEL_V1_1.md` §ContentItem | Grep confirms `status` and `abstention_status` in ContentItem. |
| C-008 | Medium | **RESOLVED** | No longer blocking | Renamed `normalized_response_id` to `domain_normalized_response_id` everywhere; renamed `DomainNormalizedResponse` primary identifier. | `MPE_OBJECT_MODEL_V1_1.md` §Evaluation, §DomainNormalizedResponse; `MPE_EVENT_MODEL_V1_1.md` §`domain_response_normalized`, §`evaluation_completed` | Grep confirms `domain_normalized_response_id` present and no `normalized_response_id` outside historical references. |
| C-009 | Medium | **RESOLVED** | No longer blocking | Replaced generic `quality_score`/`quality_metrics` with `quality_dimensions`, `quality_flags`, `quality_model_id`, `quality_model_version`, optional `overall_quality`. | `MPE_EVENT_MODEL_V1_1.md` §`observation_received`, §`signal_quality_changed`; `MPE_PROVIDER_BOUNDARIES.md` §`ObservationProvider`; `MPE_ADAPTATION_CONTRACT.md` §Uncertainty requirements; `MPE_OBJECT_MODEL_V1_1.md` §`SensorObservation` | Grep confirms `quality_score` absent outside historical references. |
| C-010 | Medium | **RESOLVED** | No longer blocking | `signal_quality_changed` payload includes `session_id`, `reported_at`, quality model fields; classified as diagnostic. | `MPE_EVENT_MODEL_V1_1.md` §`signal_quality_changed` | Grep confirms payload structure. |
| C-011 | Medium | **RESOLVED** | No longer blocking | Rewrote `MPE_ARCHITECTURE_V1_1.md` philosophy statement to qualify optimal state as experimental hypothesis. | `MPE_ARCHITECTURE_V1_1.md` §2 Philosophy | Grep confirms reworded. |
| C-012 | Medium | **RESOLVED** | No longer blocking | Documented pause/clock semantics: paused time excluded from timestamp; scheduled events not shifted; response latency excludes paused time; late events ordered by `session_sequence_number`. | `MPE_EVENT_MODEL_V1_1.md` §Session clock and pause semantics, §Event ordering guarantees | Grep confirms all four rules stated. |
| C-013 | Medium | **RESOLVED** | No longer blocking | `MPE_PHASE_4_IMPLEMENTATION_PLAN.md` acceptance/stop criteria now use `answer_status`/`evaluation_status`. | `MPE_PHASE_4_IMPLEMENTATION_PLAN.md` §Phase 4C acceptance criteria, §Stop conditions | Grep confirms `abstained` not scored as incorrect. |
| C-014 | Medium | **RESOLVED** | No longer blocking | `CapturedResponse` primary identifier renamed to `captured_response_id`. | `MPE_OBJECT_MODEL_V1_1.md` §`CapturedResponse` | Grep confirms `captured_response_id` as required field. |
| C-015 | Low | **RESOLVED** | No longer blocking | `state_estimate_produced` payload includes `state_estimate_id`; `StateEstimate` object model defines `state_estimate_id`. | `MPE_EVENT_MODEL_V1_1.md` §`state_estimate_produced`; `MPE_OBJECT_MODEL_V1_1.md` §`StateEstimate` | Grep confirms `state_estimate_id` present. |
| C-016 | Low | **RESOLVED** | No longer blocking | `Outcome` `latency_summaries` now defines a per-stratum structure (`median_ms`, `quantiles`, `distribution_summary`, `omission_count`, `timeout_count`). | `MPE_OBJECT_MODEL_V1_1.md` §`Outcome` | Grep confirms `latency_summaries` structure present. |
| C-017 | Low | **RESOLVED** | No longer blocking | `instruction_started` payload includes `instruction_payload`, `target_operation`, `observable_response_expected`. | `MPE_EVENT_MODEL_V1_1.md` §`instruction_started` | Grep confirms payload. |
| C-018 | Low | **RESOLVED** | No longer blocking | Canonicalized `transfer_claim_level` to `trained_task_performance` (underscore) across all documents. | `MPE_OBJECT_MODEL_V1_1.md` §Program, §ProtocolVersion; `MPE_ARCHITECTURE_V1_1.md`; `MPE_RISK_REGISTER_V1_1.md`; `MPE_CANONICAL_ENUM_REGISTRY.md` | Grep confirms only `trained_task_performance` remains outside historical references. |

## Blocking count after correction pass

| Severity | Count |
|---|---|
| High (blocking Phase 4A) | 0 |
| Medium | 0 |
| Low | 0 |
| **Total** | **0** |

## Evidence that these are resolved

All listed items were re-verified by direct grep of the corrected `docs/` tree. No non-documentation changes were detected by the stated filesystem check. The workspace is not a Git repository, so these findings are based on the current file contents and not on version-control diffs.
