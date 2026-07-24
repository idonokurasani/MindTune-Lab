# MPE v1.1 Review Summary

## Audit inputs and sections

This revision is based on:

- The newly created `docs/research/mpe_ontology_audit_v1/` package:
  - `COGNITIVE_PROTOCOL_ONTOLOGY.md` §Core entities, §Instruction, §Response processing layers, §Evaluation, §Feedback, §ScheduleDecision, §AdaptationDecision, §LatentEstimate, §Safety, §Outcome.
  - `PROTOCOL_PRIMITIVES_CATALOG.md` §Allowed primitives, §Prohibited primitives, §Trial role sequence examples, §Response requirement values.
  - `SOURCE_CLAIM_AUDIT.md` and `SOURCE_CLAIM_AUDIT.csv` — claims 1, 4–13 (D, rejected) and 14–28 (A, accepted).
  - `DOMAIN_INDEPENDENCE_MAP.md` §What belongs in MPE core, §Provider contract table, §MPE core must not contain.
  - `OPEN_QUESTIONS_AND_DECISIONS.md` — open questions 1–9 and closed decisions.
  - `EXECUTIVE_SYNTHESIS.md` §What must change, §What remains acceptable, §Readiness for Phase 4A, §Key risks.
  - `METHODOLOGY_AND_LIMITATIONS.md` §Methodology, §Limitations.
  - `PROTOCOL_DECOMPOSITION_MATRIX.csv` — all task-family rows.
- `docs/MINDTUNE_PROTOCOL_ENGINE_ARCHITECTURE_v1.0.md` (the document being corrected).
- `data/hebrew/phase3/PHASE_3_FINAL_REPORT.md` (Honest limitations and key metrics).

The requested audit inputs did not exist before this work; they were produced as audit artifacts and now serve as the binding inputs for v1.1. Each "What changed" item below cites the relevant audit section.

## What changed

### 1. Logical vs executable identity

`Program` and `Protocol` are now stable logical identities. `ProgramVersion` and `ProtocolVersion` are immutable executable definitions with checksums and dependency versions. `Session` references exact `ProgramVersion` and `ProtocolVersion` checksums. Executable fields such as sequences, provider requirements, safety configuration, and schema version live in the version objects.

Source: `COGNITIVE_PROTOCOL_ONTOLOGY.md` §Core entities (Program/ProgramVersion/Protocol/ProtocolVersion); correction to v1.0 5.1/5.3.

### 2. Trial response semantics

The mandatory `expected_response_mode` was replaced by `response_requirement` (`required` | `optional` | `none`) and an optional `accepted_response_modes` list. This supports exposure-only, encoding-only, feedback-only, covert-instruction, and delayed-probe designs.

Source: `COGNITIVE_PROTOCOL_ONTOLOGY.md` §Trial; `PROTOCOL_PRIMITIVES_CATALOG.md` §Allowed primitives, §Prohibited primitives, §Response requirement values.

### 3. Covert instruction semantics

A covert instruction now has `instruction_payload` (never null), `target_operation`, `allotted_duration`, and `observable_response_expected`. The system records the instruction and its time window, but never a covert answer or correctness result.

Source: `COGNITIVE_PROTOCOL_ONTOLOGY.md` Instruction; `SOURCE_CLAIM_AUDIT.md` claims 7, 4.

### 4. Response processing layers

The direct path `Observation` → `NormalizedResponse` → `Evaluation` was replaced with `Observation` → `CapturedResponse` → `ResponseInterpretation` → `DomainNormalizedResponse` → `Evaluation`. Speech-derived Hebrew output is processed by a Hebrew-specific `ResponseInterpreter` and `DomainNormalizer`, not a generic provider-agnostic step.

Source: `COGNITIVE_PROTOCOL_ONTOLOGY.md` §Response processing layers; `DOMAIN_INDEPENDENCE_MAP.md` §Provider contract table, §MPE core must not contain.

### 5. Quality model

Generic scalar `quality_score` was replaced by `quality_dimensions`, `quality_flags`, `quality_model_id`, `quality_model_version`, and optional `overall_quality`.

Source: `COGNITIVE_PROTOCOL_ONTOLOGY.md` Observation.

### 6. Answer and evaluation status separation

`Evaluation` now has `answer_status` (`correct`, `incorrect`, `acceptable_variant`, `partially_correct`, `unevaluable`) and `evaluation_status` (`completed`, `abstained`, `failed`, `out_of_scope`). `acceptable_variant` can receive full `correctness_credit`. Additional fields include `accepted_variant_id`, `evidence_group`, `scope_status`, `abstention_reason`, and `failure_reason`.

Source: `COGNITIVE_PROTOCOL_ONTOLOGY.md` Evaluation; `MPE_HEBREW_PROVIDER_CONTRACT.md`.

### 7. Reproducible ScheduleDecision

`ScheduleDecision` now includes `policy_id`, `policy_version`, `source_event_ids`, `item_history_snapshot_id`, `candidate_item_ids`, `excluded_candidates` with reasons, `selection_rule`, `tie_break_rule`, `random_seed`, `selected_item_ids`, `decision_status`, and `abstention_reason`.

Source: `COGNITIVE_PROTOCOL_ONTOLOGY.md` ScheduleDecision.

### 8. Circular audit reference removed

`audit_event_id` was removed from `AdaptationDecision`. Events now reference the decision ID. `AdaptationDecision` includes all contractual fields needed for independent validation.

Source: `MPE_OBJECT_MODEL_V1_1.md` AdaptationDecision; `MPE_ADAPTATION_CONTRACT.md`.

### 9. Deployment semantics corrected

Deployment status is now:

- `exploratory_only` — offline analysis only.
- `shadow_mode` — hypothetical decisions only; never changes runtime behavior.
- `limited_runtime` — changes only inside an approved, consented, logged experiment.
- `production_approved` — changes under normal protocol guardrails.

No model in `shadow_mode` may apply an adaptation.

Source: `MPE_ADAPTATION_CONTRACT.md`; `MPE_PROVIDER_BOUNDARIES.md` `StateInferenceModel`.

### 10. Outcome latency metrics stratified

Global mean response latency was removed. `Outcome` latency metrics are stratified by `task_definition`, `response_mode`, `trial_role`, and `item_class`. Prefer medians, quantiles, distribution summaries, omission count, and timeout count.

Source: `COGNITIVE_PROTOCOL_ONTOLOGY.md` Outcome.

### 11. Safety separated from feedback

`safety_cue` was removed from `FeedbackEvent`. Safety instructions are a separate event category and subsystem. Educational feedback is split into `KnowledgeFeedback`, `PerformanceFeedback`, and `MetacognitivePrompt`.

Source: `COGNITIVE_PROTOCOL_ONTOLOGY.md` SafetyInstruction and feedback categories; `MPE_EVENT_MODEL_V1_1.md`.

### 12. Provider decomposition

The single `Provider` abstraction was replaced by eight narrow interfaces: `DomainProvider`, `Renderer`, `ObservationProvider`, `ResponseInterpreter`, `DomainNormalizer`, `Evaluator`, `Scheduler`/`ItemPolicy`, and `StateInferenceModel`.

Source: `MPE_PROVIDER_BOUNDARIES.md`; `DOMAIN_INDEPENDENCE_MAP.md` §What belongs in MPE core, §Provider contract table, §MPE core must not contain.

### 13. Cognitive-state estimates made explicit

Reified state variables were replaced by `StateEstimate`/`LatentEstimate` objects with operational definitions, model version, uncertainty, validation status, `exploratory_only` deployment status, alternative explanations, and fallback behavior.

Source: `COGNITIVE_PROTOCOL_ONTOLOGY.md` LatentEstimate; `SOURCE_CLAIM_AUDIT.md` claims 5-6.

### 14. EEG semantics removed from core

All EEG-band semantic claims were removed from MPE core. EEG data is handled as generic `SensorObservation` consumed by versioned `StateInferenceModel`s that begin in `exploratory_only` status.

Source: `DOMAIN_INDEPENDENCE_MAP.md`; `MPE_PROVIDER_BOUNDARIES.md`; `SOURCE_CLAIM_AUDIT.md` claim 6.

### 15. Universal learning loop reclassified

`Perceive → Predict → Resolve → Reinforce` was reclassified as the `language_prediction_retrieval` task family. A generic trial structure (`Stimulus/Cue → Learner Operation → Response Window → Observation → Evaluation → Feedback → Scheduling`) was defined, with at least four other specializations: `perceptual_discrimination`, `overt_recall`, `morphology_generation`, `working_memory_sequence`.

Source: `PROTOCOL_PRIMITIVES_CATALOG.md` §Allowed primitives, §Prohibited primitives, §Trial role sequence examples; `PROTOCOL_DECOMPOSITION_MATRIX.csv` all rows.

### 16. Generic difficulty removed

`increase_difficulty()` / `decrease_difficulty()` were replaced by typed difficulty dimensions and dimension-specific `AdaptationDecision` objects.

Source: `MPE_ADAPTATION_CONTRACT.md`.

### 17. Provisional bounds

"Safe ranges" were relabeled as `provisional configurable bounds` with default, min, max, status, evidence grade, validation requirement, and override policies.

Source: `MPE_ADAPTATION_CONTRACT.md`; `SOURCE_CLAIM_AUDIT.md` claim 11.

### 18. `time_in_target_state` removed from Phase 4/5A KPIs

It remains only as an experimental diagnostic. Core metrics are accuracy, latency, omission, coverage, dropout, protocol adherence, and stratified latency summaries.

Source: `COGNITIVE_PROTOCOL_ONTOLOGY.md` Outcome; `SOURCE_CLAIM_AUDIT.md` claim 12.

### 19. Textual DSL deferred

The textual DSL is not finalized. Phase 4 uses a typed internal model serialized as JSON/YAML. A textual authoring syntax may be added later.

Source: `MPE_DSL_DECISION_RECORD.md` (decision and traceability sections); `MPE_PHASE_4_IMPLEMENTATION_PLAN.md` §Scope and §Traceability.

### 20. Phase 4 split

Phase 4 is now `4A` (schema), `4B` (deterministic runtime), `4C` (Hebrew behavioral integration). Phase 5 is split into `5A` (behavioral adaptation), `5B` (sensor research), `5C` (experimental sensor-informed policies).

Source: `MPE_PHASE_4_IMPLEMENTATION_PLAN.md` §Scope and §Traceability; `SOURCE_CLAIM_AUDIT.md` claim 13.

## What was rejected

- "First platform" / "new software category" claims as architecture facts. (`SOURCE_CLAIM_AUDIT.md` claim 1)
- `expect(mental_*)` as a primitive. (`SOURCE_CLAIM_AUDIT.md` claim 7)
- `wait_for_state(target, timeout)`. (`SOURCE_CLAIM_AUDIT.md` claim 8)
- Single `Provider` abstraction. (`SOURCE_CLAIM_AUDIT.md` claim 9)
- Generic `increase_difficulty()` / `decrease_difficulty()`. (`SOURCE_CLAIM_AUDIT.md` claim 10)
- EEG semantics inside MPE core. (`SOURCE_CLAIM_AUDIT.md` claims 5-6)
- `time_in_target_state` as a production KPI. (`SOURCE_CLAIM_AUDIT.md` claim 12)
- Latency ownership by the Hebrew `Evaluator`. (`COGNITIVE_PROTOCOL_ONTOLOGY.md` §Response processing layers)
- `safety_cue` as a feedback type. (`COGNITIVE_PROTOCOL_ONTOLOGY.md` §Feedback)

## What remains uncertain

- The exact authoring syntax if a textual DSL is introduced later (`MPE_OPEN_DECISIONS.md` #1).
- Which voice and TTS pipeline will be canonical for Phase 4C (`MPE_OPEN_DECISIONS.md` #7, #8).
- ASR accuracy on Hebrew verb forms and whether voice can be a primary response mode (`MPE_OPEN_DECISIONS.md` #3).
- The final set of Hebrew `error_category` values (`MPE_OPEN_DECISIONS.md` #5).
- Whether `acceptable_variant` should receive full or partial correctness credit long-term (`MPE_OPEN_DECISIONS.md` #6).
- How delayed recall will be structured (in-scheduler vs separate program) (`MPE_OPEN_DECISIONS.md` #4).

## Unresolved conflicts

None. All audit findings have been incorporated into the v1.1 object model, event model, provider boundaries, adaptation contract, Hebrew contract, DSL decision, Phase 4 plan, risk register, and review summary.

## Final correction pass

The first cross-document audit identified 7 blocking corrections (C-001–C-007) and 11 lower-severity items (C-008–C-018). The second-pass audit verified that all were applied and that no high-severity inconsistency remains:

- `session_created` references `program_version_id` and `protocol_version_id`.
- `trial_created` uses `response_requirement` and `accepted_response_modes`.
- `MPE_HEBREW_PROVIDER_CONTRACT.md` uses `DomainNormalizedResponse` input and `answer_status` / `evaluation_status` output.
- `audit_event_id` was removed from `AdaptationDecision`; events reference `adaptation_decision_id`.
- `session_sequence_number` was added to common event fields.
- `captured_response_created`, `response_interpreted`, `domain_response_normalized`, `evaluation_failed`, and `evidence_record_created` events were added.
- `ContentItem.status` and `abstention_status` were defined in the object model.
- Response-pipeline identifiers were canonicalized: `observation_id`, `captured_response_id`, `response_interpretation_id`, `domain_normalized_response_id`, `evaluation_id`.
- The quality model (`quality_dimensions`, `quality_flags`, `quality_model_id`, `quality_model_version`, optional `overall_quality`) replaced scalar `quality_score`.
- `signal_quality_changed` is classified as a provider/runtime diagnostic and uses `reported_at`.
- `transfer_claim_level` is canonically `trained_task_performance` (underscore) across all documents.
- `Outcome.latency_summaries` structure is defined per stratum.
- `data_classification` enum was added to common event fields.
- The canonical identifier registry, enum registry, and object-event coverage matrix were updated.
- `MPE_V1_1_CROSS_DOCUMENT_AUDIT.md` contains a second-pass section with the final `APPROVE_PHASE_4A` verdict.

## Recommendation

**APPROVE_PHASE_4A**

Phase 4A may begin. It has a clear scope (schema definition), no dependencies on EEG or adaptation, and explicit acceptance criteria. Phase 4B and 4C are blocked until Phase 4A is complete and accepted. Phase 5A, 5B, and 5C remain blocked until Phase 4 is complete.
