# MPE v1.1 Cross-Document Audit

## Scope and method

This audit reviews the complete MPE v1.1 documentation package as a connected system. It uses:

- `docs/MPE_ARCHITECTURE_V1_1.md`
- `docs/MPE_V1_0_CRITICAL_REVIEW.md`
- `docs/MPE_OBJECT_MODEL_V1_1.md`
- `docs/MPE_EVENT_MODEL_V1_1.md`
- `docs/MPE_PROVIDER_BOUNDARIES.md`
- `docs/MPE_ADAPTATION_CONTRACT.md`
- `docs/MPE_HEBREW_PROVIDER_CONTRACT.md`
- `docs/MPE_DSL_DECISION_RECORD.md`
- `docs/MPE_PHASE_4_IMPLEMENTATION_PLAN.md`
- `docs/MPE_RISK_REGISTER_V1_1.md`
- `docs/MPE_OPEN_DECISIONS.md`
- `docs/MPE_REVIEW_SUMMARY.md`
- `docs/research/mpe_ontology_audit_v1/*`
- `docs/MINDTUNE_PROTOCOL_ENGINE_ARCHITECTURE_v1.0.md`
- `data/hebrew/phase3/PHASE_3_FINAL_REPORT.md`

The review was performed with filesystem text searches (grep) across the `docs/` tree. No code, tests, runtime schemas, CI files, or Hebrew engine files were modified.

## Executive verdict

**REVISE_DOCUMENTATION**

The core v1.1 architecture is coherent: logical/executable identity separation, the layered response pipeline, provider boundaries, abstention/rollback, and Hebrew authority are sound. However, several documents have not kept pace with the object model and event model, leaving high- and medium-severity inconsistencies. These can be corrected without changing the architecture. Once the corrections in `docs/MPE_FINAL_CORRECTIONS_REQUIRED.md` are applied, the package will be ready for an `APPROVE_PHASE_4A` recommendation.

## 1. Object–event coverage

The object–event coverage matrix is in `docs/MPE_OBJECT_EVENT_COVERAGE_MATRIX.csv`.

### Objects with no corresponding event

| Object | Why it is missing an event | Risk | Recommended fix |
|---|---|---|---|
| `CapturedResponse` | `MPE_EVENT_MODEL_V1_1.md` jumps from `observation_received` to `response_normalized`, skipping the capture layer. | Replay cannot reconstruct the exact captured response; ASR/interpretation history is lost. | Add `captured_response_recorded` event, or embed `captured_response_id` in `observation_received` / `response_normalized`. |
| `ResponseInterpretation` | Same as above; no `response_interpreted` event. | ASR output cannot be replayed or audited independently. | Add `response_interpreted` event carrying `response_interpretation_id`, `interpreter_id`, `interpreted_payload`, `interpretation_confidence`. |
| `EvidenceRecord` | Referenced by `evaluation_completed`, `schedule_decision`, `adaptation_proposed` but never emitted as its own event. | Evidence cannot be reconstructed as a first-class object. | Add `evidence_record_created` event, or embed the full `EvidenceRecord` in each referencing event. |
| `Program` / `Protocol` | These are logical identities, not runtime objects. | None, if version events carry `program_version_id` / `protocol_version_id`. | Acceptable; no event required. |

### Events with no corresponding object

- `signal_quality_changed` — has no `SignalQuality` object in `MPE_OBJECT_MODEL_V1_1.md`. It should probably be an `Observation` with `observation_type == signal_quality`.
- `safety_instruction_started` / `safety_instruction_completed` — map to `SafetyInstruction` object; acceptable.

### Objects whose reconstruction rules are incomplete

- `StateEstimate` — `state_estimate_produced` event does not include `state_estimate_id`, so the object cannot be reconstructed by ID.
- `Outcome` — has no event; it is a computed view. Document the computation formula.
- `SensorObservation` — object model separates it, but event model treats it as `Observation` with `observation_type == sensor_feature`. Clarify subtype mapping.

### Duplicate or overlapping objects

- `KnowledgeFeedback`, `PerformanceFeedback`, `MetacognitivePrompt` are listed as expected objects in the audit brief, but the object model implements them as `FeedbackEvent.feedback_category` values plus one `SafetyInstruction` object. This is an acceptable design choice, not a duplicate. Document it explicitly.

## 2. Identifier inconsistencies

The canonical identifier registry is in `docs/MPE_CANONICAL_IDENTIFIER_REGISTRY.md`.

High-severity identifier mismatches:

1. **`session_created` event payload uses `program_id` instead of `program_version_id`.**
   - `MPE_OBJECT_MODEL_V1_1.md` Session requires `program_version_id`.
   - `MPE_EVENT_MODEL_V1_1.md` `session_created` payload lists `program_id`.
   - Correction: replace `program_id` with `program_version_id` in the event payload.

2. **`normalized_response_id` is ambiguous.**
   - The old `NormalizedResponse` object no longer exists; the pipeline now has `ResponseInterpretation` and `DomainNormalizedResponse`.
   - `MPE_OBJECT_MODEL_V1_1.md` `Evaluation` uses `normalized_response_id`.
   - `MPE_EVENT_MODEL_V1_1.md` `response_normalized` and `evaluation_completed` use `normalized_response_id`.
   - Correction: rename to `domain_normalized_response_id` everywhere.

3. **`CapturedResponse` primary field is `id`, but `ResponseInterpretation` references `captured_response_id`.**
   - Correction: rename `CapturedResponse.id` to `captured_response_id`.

4. **Missing `session_sequence_number`.**
   - `MPE_EVENT_MODEL_V1_1.md` common event fields do not include a sequence number.
   - UUID ordering cannot be canonical.
   - Correction: add `session_sequence_number` to every event.

## 3. Status and enum inconsistencies

The canonical enum registry is in `docs/MPE_CANONICAL_ENUM_REGISTRY.md`.

High-severity enum mismatches:

1. **`MPE_EVENT_MODEL_V1_1.md` `trial_created` payload uses `expected_response_mode` (obsolete).**
   - `MPE_OBJECT_MODEL_V1_1.md` Trial uses `response_requirement` (`required` | `optional` | `none`) and `accepted_response_modes`.
   - Correction: update the event payload.

2. **`MPE_HEBREW_PROVIDER_CONTRACT.md` uses old `verdict` enum.**
   - `MPE_OBJECT_MODEL_V1_1.md` and `MPE_EVENT_MODEL_V1_1.md` use `answer_status` and `evaluation_status`.
   - Correction: rewrite the Hebrew `Evaluator` input/output and handling categories.

3. **`MPE_OBJECT_MODEL_V1_1.md` `ContentItem` lacks `status` and `abstention_status`.**
   - `MPE_HEBREW_PROVIDER_CONTRACT.md` returns `status` and `abstention_status` in `ContentItem`.
   - Correction: add these fields to the object model.

4. **Quality model not consistently applied.**
   - `MPE_OBJECT_MODEL_V1_1.md` `Observation` uses `quality_dimensions`, `quality_flags`, `quality_model_id`, `quality_model_version`, optional `overall_quality`.
   - `MPE_EVENT_MODEL_V1_1.md` `observation_received`, `signal_quality_changed` use generic `quality_score`.
   - `MPE_PROVIDER_BOUNDARIES.md` `ObservationProvider` uses `quality_metrics`.
   - `MPE_ADAPTATION_CONTRACT.md` refers to `low quality_score`.
   - `MPE_OBJECT_MODEL_V1_1.md` `SensorObservation` uses `quality_score`.
   - Correction: align all to the quality model.

5. **`transfer_claim_level` spelling mismatch.**
   - Review brief uses `trained_task_performance` (underscores).
   - `MPE_OBJECT_MODEL_V1_1.md` uses `trained-task-performance` (hyphens).
   - Correction: choose one canonical spelling before schema implementation.

## 4. Response pipeline consistency

The conceptual sequence `Observation -> CapturedResponse -> ResponseInterpretation -> DomainNormalizedResponse -> Evaluation` is consistent in:

- `MPE_OBJECT_MODEL_V1_1.md`
- `MPE_PROVIDER_BOUNDARIES.md`
- `MPE_ARCHITECTURE_V1_1.md`
- `MPE_V1_0_CRITICAL_REVIEW.md`

Violations:

- `MPE_HEBREW_PROVIDER_CONTRACT.md` takes `NormalizedResponse` (old single object) as input and returns a `verdict` (old single status). It does not use `DomainNormalizedResponse` or the `answer_status`/`evaluation_status` split.
- `MPE_EVENT_MODEL_V1_1.md` has no `captured_response_recorded` or `response_interpreted` events, collapsing the pipeline from `Observation` directly to `response_normalized`.
- `MPE_PHASE_4_IMPLEMENTATION_PLAN.md` stop conditions refer to `abstained verdicts are scored as incorrect` and `correct/incorrect/acceptable_variant/abstained` verdicts, contradicting the `answer_status`/`evaluation_status` separation.
- `MPE_OBJECT_MODEL_V1_1.md` `Evaluation` uses `normalized_response_id` rather than `domain_normalized_response_id`.

No document assigns correctness to `Observation` or `CapturedResponse`. Latency ownership is correctly assigned to the runtime.

## 5. Timestamp and ordering consistency

Correct aspects:

- Runtime owns authoritative `timestamp` in `MPE_EVENT_MODEL_V1_1.md`.
- Components may report non-authoritative `component_timestamp` inside payload.
- `wallclock_at` is optional and explicitly marked as may drift.

Undefined or inconsistent aspects:

- **Paused time and monotonic session clock** — not defined. Must decide whether paused time counts in `timestamp` and whether `scheduled_for` is shifted after resume.
- **Response latency and paused intervals** — not defined. Must clarify whether response latency excludes paused time.
- **Late provider event ordering** — `MPE_EVENT_MODEL_V1_1.md` says ordering is resolved by `event_id` tie-breaker for near-identical timestamps. This uses UUID ordering, which is prohibited as canonical. Must use `session_sequence_number`.
- **Capture start/end timestamps** — `response_detected`/`response_completed` payload uses `detected_at`/`completed_at`. These are provider-reported and should not be used directly for latency; runtime `timestamp` must be used.
- **Signal quality event timestamp** — `signal_quality_changed` payload uses `timestamp` instead of the common `timestamp` semantics and lacks `session_id`.
- **No `session_sequence_number`** — every event should carry one for canonical ordering.

## 6. Replay consistency

Classification of event families:

| Event family | Replay role |
|---|---|
| `session_created`, `session_started`, `block_started/completed`, `trial_created`, `instruction_started/completed`, `stimulus_requested`, `response_window_opened`, `schedule_decision` | Deterministically recomputed from `ProtocolVersion` and scheduler (given random seed and history). |
| `observation_received`, `response_detected`, `response_completed`, `session_paused`, `session_resumed`, `session_cancelled` | Recorded fact consumed during replay. |
| `stimulus_ready`, `evaluation_completed`, `evaluation_abstained` | External output requiring capture for exact replay; otherwise recomputed if provider deterministic. |
| `stimulus_started`, `stimulus_completed`, `feedback_completed`, `safety_instruction_completed` | Not replayed; regenerated during replay. |
| `state_estimate_produced` | Diagnostic only; not consumed in Phase 4 replay. |
| `adaptation_*` | Not used in Phase 4; replayed in Phase 5A+ if policy deterministic. |

Claims of "full replay" are only supported when:
- `ProtocolVersion` is fixed,
- random seed is fixed,
- observations and provider outputs are captured,
- wall-clock dependencies are excluded.

The `MPE_EVENT_MODEL_V1_1.md` "fully replay-deterministic" claim is therefore conditional and acceptable, but the missing `CapturedResponse`/`ResponseInterpretation` events weaken exact replay for ASR paths.

## 7. Provider boundary consistency

Provider responsibilities are correctly separated in `MPE_PROVIDER_BOUNDARIES.md` and `MPE_OBJECT_MODEL_V1_1.md`:

- No provider owns runtime timestamps.
- No provider evaluates covert activity.
- Hebrew morphology is confined to Hebrew providers.
- Rendering, observation, and evaluation are not combined.
- EEG semantics are not in core.

Inconsistencies:

- `MPE_PROVIDER_BOUNDARIES.md` `ObservationProvider` `observation_capabilities()` still returns `quality_metrics` instead of the quality model fields.
- `MPE_HEBREW_PROVIDER_CONTRACT.md` mixes old `verdict` semantics, violating the `Evaluator` boundary contract.
- `MPE_PROVIDER_BOUNDARIES.md` `ResponseInterpreter` correctly says it does not canonicalize, but `MPE_EVENT_MODEL_V1_1.md` has no event for its output.

## 8. Hebrew contract consistency

`MPE_HEBREW_PROVIDER_CONTRACT.md` is the most out-of-sync document. It still uses:

- `NormalizedResponse` input instead of `DomainNormalizedResponse`.
- `verdict` (`correct`/`incorrect`/`partial`/`abstained`) output instead of `answer_status`/`evaluation_status`.
- `accepted_variant` (object) instead of `accepted_variant_id`.
- `Evaluation.verdict` in handling categories.

The required handling categories (verified result, acceptable variant, advisory pronunciation, unknown result, out-of-scope verb, low-confidence result, abstention, engine failure, version mismatch, 100-verb scope) are all present in intent, but their field names are stale.

MPE never independently decides Hebrew correctness; this principle is intact in `MPE_OBJECT_MODEL_V1_1.md` and `MPE_PROVIDER_BOUNDARIES.md`.

## 9. Safety consistency

Safety is consistently represented as:

- Separate from feedback in `MPE_OBJECT_MODEL_V1_1.md` (FeedbackEvent vs SafetyInstruction) and `MPE_EVENT_MODEL_V1_1.md` (feedback vs safety_instruction events).
- Override of adaptation in `MPE_ADAPTATION_CONTRACT.md`.
- Pause/terminate actions in `MPE_OBJECT_MODEL_V1_1.md` SafetyEvent and `MPE_EVENT_MODEL_V1_1.md` `safety_rule_triggered`.
- No silent session extension in safety rules.
- Provider timeout, degraded mode, microphone/sensor fallback implied but not fully detailed.

The `MPE_PHASE_4_IMPLEMENTATION_PLAN.md` includes safety fallback and degraded mode testing.

## 10. Phase consistency

Phase 4A scope in `MPE_PHASE_4_IMPLEMENTATION_PLAN.md` is correctly limited to documentation/schema design:

- No production runtime.
- No textual DSL parser.
- No adaptation.
- No EEG.
- No real-time cognitive-state inference.
- No Hebrew engine modification.
- No production TTS integration.
- No product UI.

However, the plan's stop conditions for Phase 4C still use obsolete `verdict` language (`abstained verdicts are scored as incorrect`, `correct/incorrect/acceptable_variant/abstained`). These need to be aligned with `answer_status`/`evaluation_status`.

Phase 4B and 4C dependencies do not leak into Phase 4A acceptance criteria.

## 11. Claim consistency

Residual scientific/positioning phrases found:

| Phrase | Location | Classification | Required action |
|---|---|---|---|
| "The goal is an optimal cognitive state, not maximum speed." | `MPE_ARCHITECTURE_V1_1.md` §2 Philosophy | Experimental hypothesis, but not explicitly labeled | Reword to "The goal is to help the learner maintain a productive cognitive state; this is an experimental hypothesis, not a validated optimum." |
| "first platform" / "new software category" | `MINDTUNE_PROTOCOL_ENGINE_ARCHITECTURE_v1.0.md` (rejected); `MPE_REVIEW_SUMMARY.md` and `MPE_V1_0_CRITICAL_REVIEW.md` quarantine them as product-positioning hypotheses. | Removed/quarantined | None; correctly handled. |
| "validated safe ranges" | Not present as phrase; `MPE_ADAPTATION_CONTRACT.md` correctly labels "provisional configurable bounds". | Removed | None. |
| "EEG correctness detection" | Not present in v1.1 docs. | Removed | None. |
| "far transfer" / "clinical efficacy" | Only mentioned as risks or as claims requiring separate validation. | Correctly treated as unsupported | None. |
| "proven closed-eyes superiority" | Not present. | Removed | None. |

## 12. Traceability consistency

Every material correction in `MPE_V1_0_CRITICAL_REVIEW.md` maps to:

- `MPE_OBJECT_MODEL_V1_1.md` object/section,
- `docs/research/mpe_ontology_audit_v1/` file and section,
- `data/hebrew/phase3/PHASE_3_FINAL_REPORT.md` where applicable.

However, the following documents were found to contradict the critical review, meaning the traceability claim is not fully realized:

- `MPE_HEBREW_PROVIDER_CONTRACT.md` still uses `verdict`/`NormalizedResponse` even though `MPE_V1_0_CRITICAL_REVIEW.md` row 9.1/10.1 says the object model was updated.
- `MPE_ADAPTATION_CONTRACT.md` still contains `audit_event_id` even though `MPE_V1_0_CRITICAL_REVIEW.md` row 8.4 and `MPE_OBJECT_MODEL_V1_1.md` state it was removed.

These are not traceability gaps; they are implementation gaps in the documentation itself.

## 13. Required corrections summary

All unresolved corrections are listed in `docs/MPE_FINAL_CORRECTIONS_REQUIRED.md`.

## 14. Final recommendation (first pass)

**REVISE_DOCUMENTATION.**

The architecture is coherent, but the documentation package contained stale content in `MPE_HEBREW_PROVIDER_CONTRACT.md`, `MPE_EVENT_MODEL_V1_1.md`, `MPE_ADAPTATION_CONTRACT.md`, and minor issues elsewhere. A second correction pass was executed; results are below.

---

# Second-pass audit

## Scope and method

This second pass re-examined the same documentation package after the blocking corrections C-001 through C-007 were applied. It used the same grep-based filesystem inspection.

## Executive verdict (second pass)

**APPROVE_PHASE_4A**

All blocking corrections are resolved. The object model, event model, provider boundaries, Hebrew contract, and adaptation contract are now internally consistent. Phase 4A remains documentation/schema-only. No high-severity inconsistency remains.

## 1. Object–event coverage (second pass)

The updated object–event coverage matrix is in `docs/MPE_OBJECT_EVENT_COVERAGE_MATRIX.csv`.

- `CapturedResponse` is created by `captured_response_created`.
- `ResponseInterpretation` is created by `response_interpreted`.
- `DomainNormalizedResponse` is created by `domain_response_normalized`.
- `Evaluation` is created by `evaluation_completed`, `evaluation_abstained`, or `evaluation_failed`.
- `EvidenceRecord` is created by `evidence_record_created`.
- `signal_quality_changed` is explicitly classified as a provider/runtime diagnostic fact that does not create a persistent domain object.

No object/event gaps remain.

## 2. Identifier consistency (second pass)

The updated canonical identifier registry is in `docs/MPE_CANONICAL_IDENTIFIER_REGISTRY.md`.

- `session_created` uses `program_version_id`.
- All response-pipeline identifiers are canonically named: `observation_id`, `captured_response_id`, `response_interpretation_id`, `domain_normalized_response_id`, `evaluation_id`.
- `ProgramVersion` and `ProtocolVersion` explicitly define `program_version_id` and `protocol_version_id`.
- `session_sequence_number` is in the common event fields.
- `state_estimate_id` is in the `state_estimate_produced` payload.
- `evidence_record_id` is in the `evidence_record_created` payload.
- `safety_event_id` is in safety event payloads.

No identifier mismatches remain.

## 3. Enum consistency (second pass)

The updated canonical enum registry is in `docs/MPE_CANONICAL_ENUM_REGISTRY.md`.

- `response_requirement` (`required` | `optional` | `none`) is used in `trial_created`.
- `answer_status` and `evaluation_status` are used in the Hebrew contract and event model.
- `ContentItem.status` and `abstention_status` are defined in the object model.
- Generic `quality_score` is replaced by the quality model in event model, provider boundaries, and adaptation contract.
- `transfer_claim_level` is canonically `trained_task_performance` (underscore) across all documents.
- `data_classification` enum is defined in the common event shape.

No enum mismatches remain.

## 4. Response pipeline consistency (second pass)

The canonical pipeline `Observation -> CapturedResponse -> ResponseInterpretation -> DomainNormalizedResponse -> Evaluation` is now represented by distinct events:

- `observation_received`
- `captured_response_created`
- `response_interpreted`
- `domain_response_normalized`
- `evaluation_completed` / `evaluation_abstained` / `evaluation_failed`

No document uses the obsolete `NormalizedResponse` or `verdict` model. Latency remains runtime-owned.

## 5. Timestamp and ordering consistency (second pass)

- `session_sequence_number` defines canonical ordering; UUID ordering is no longer used.
- Runtime `timestamp` is authoritative; component timestamps are non-authoritative.
- Pause semantics are defined: paused time is not counted in `timestamp`; scheduled events are not shifted on resume; response latency excludes paused intervals.
- `signal_quality_changed` uses `reported_at` for component timestamp and does not shadow the common `timestamp` field.
- `data_classification` enum (`public` | `consent_gated` | `sensitive_phi` | `research_sensitive`) is added to the common event shape alongside the `sensitive` boolean.

## 6. Replay consistency (second pass)

All response-processing layers have explicit events and identifiers. `Evaluation`, `ScheduleDecision`, and `AdaptationDecision` can be reconstructed. `StateEstimate` remains diagnostic and does not affect Phase 4 replay.

## 7. Provider boundary consistency (second pass)

`MPE_PROVIDER_BOUNDARIES.md` uses the quality model fields in `ObservationProvider.observation_capabilities()`. The Hebrew contract no longer returns latency or old `verdict` semantics.

## 8. Hebrew contract consistency (second pass)

`MPE_HEBREW_PROVIDER_CONTRACT.md` now uses `DomainNormalizedResponse` as input and `answer_status` / `evaluation_status` as output, with `accepted_variant_id`, `correctness_credit`, `scope_status`, `evidence_group`, `abstention_reason`, `failure_reason`, and `error_category`.

Handling categories cover verified result, acceptable variant (full and partial credit), advisory pronunciation, unknown response, out-of-scope verb, low-confidence result, normalization ambiguity, engine abstention, engine failure, version mismatch, and unsupported grammatical form.

MPE never independently decides Hebrew correctness.

## 9. Safety consistency (second pass)

Safety remains separate from feedback, overrides adaptation, and has explicit `safety_rule_triggered`, `recovery_inserted`, and `protocol_terminated` events. Lifecycle overlap is resolved:

- `session_cancelled` = user cancellation.
- `protocol_terminated` = safety or unrecoverable error.
- `session_completed` = normal protocol graph completion.

## 10. Phase consistency (second pass)

Phase 4A remains documentation/schema design only. No production runtime, DSL parser, adaptation, EEG, real-time inference, Hebrew engine modification, production TTS/microphone, product UI, or deployment infrastructure is included. Phase 4B/4C criteria do not leak into Phase 4A.

## 11. Claim consistency (second pass)

The `MPE_ARCHITECTURE_V1_1.md` "optimal cognitive state" statement is now qualified as an experimental hypothesis. No unsupported scientific or positioning claims remain in the v1.1 architecture.

## 12. Traceability consistency (second pass)

`MPE_V1_0_CRITICAL_REVIEW.md` claims are now consistent with `MPE_HEBREW_PROVIDER_CONTRACT.md` and `MPE_ADAPTATION_CONTRACT.md`. `audit_event_id` no longer appears in `AdaptationDecision`; the Hebrew contract uses the response pipeline and `answer_status`/`evaluation_status`.

## 13. Final recommendation (second pass)

**APPROVE_PHASE_4A.**

The documentation package is internally coherent enough to authorize Phase 4A protocol-schema design.
