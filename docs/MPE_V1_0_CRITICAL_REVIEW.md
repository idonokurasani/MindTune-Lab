# MPE v1.0 Critical Review v1.1

## Scope

This document critiques `docs/MINDTUNE_PROTOCOL_ENGINE_ARCHITECTURE_v1.0.md` using the audit package in `docs/research/mpe_ontology_audit_v1/` and the Phase 3 final report. It records which claims were rejected, which were retained, and how v1.1 resolves them.

## Audit documents and sections referenced

- `COGNITIVE_PROTOCOL_ONTOLOGY.md` §Core entities, §Instruction, §Response processing layers, §Evaluation, §Feedback, §ScheduleDecision, §AdaptationDecision, §LatentEstimate, §Safety, §Outcome.
- `PROTOCOL_PRIMITIVES_CATALOG.md` §Allowed primitives, §Prohibited primitives, §Trial role sequence examples, §Response requirement values.
- `SOURCE_CLAIM_AUDIT.md` and `SOURCE_CLAIM_AUDIT.csv` — claims 1, 4–13 (D, rejected) and 14–28 (A, accepted).
- `DOMAIN_INDEPENDENCE_MAP.md` §What belongs in MPE core, §Provider contract table.
- `OPEN_QUESTIONS_AND_DECISIONS.md` — closed decisions list.
- `EXECUTIVE_SYNTHESIS.md` §What must change, §Key risks.
- `METHODOLOGY_AND_LIMITATIONS.md` §Methodology, §Limitations.
- `PROTOCOL_DECOMPOSITION_MATRIX.csv` — all task-family rows.
- `data/hebrew/phase3/PHASE_3_FINAL_REPORT.md` — Honest limitations and key metrics.

## Traceability note

Every row in the section-by-section critique below cites the specific audit source that drives the correction. "Resolved in v1.1 object model" links to `MPE_OBJECT_MODEL_V1_1.md`.

## High-level verdict

v1.0 is a useful vision document but it over-commits on cognitive-state claims, provider abstraction, DSL, EEG semantics, and implementation pacing. v1.1 corrects these by separating logical from executable identity, making covert operations unobservable, decomposing providers, and staging implementation. See `EXECUTIVE_SYNTHESIS.md` for the condensed conclusion.

## Section-by-section critique and corrections

| v1.0 section | Original concept | Risk / problem | Severity | Conservative source | Required correction | Resolved in v1.1 object model |
|---|---|---|---|---|---|---|
| 1. Vision | "MindTune Lab is becoming the first platform dedicated to Adaptive Cognitive Protocols" | Unvalidated product-positioning claim presented as fact. | Medium | `SOURCE_CLAIM_AUDIT.md` claim 1 | Quarantine as positioning hypothesis; do not build architecture on it. | Yes; v1.1 removes or labels such claims. |
| 2.2 A protocol is not audio | Protocol with timing, adaptation, progression, metrics | Too abstract; lacks trial observability. | Low | `COGNITIVE_PROTOCOL_ONTOLOGY.md` | Add explicit transfer-claim level, purpose classification, and trial roles. | Yes; `ProtocolVersion` and `ProgramVersion` carry `purpose` and `primary_transfer_claim`. |
| 3. Scientific assumptions | 8 assumptions | Several unvalidated for this system. | Medium | `METHODOLOGY_AND_LIMITATIONS.md` | Reclassify as experimental hypotheses; require validation status per protocol. | Yes; assumptions are now hypotheses in v1.1 architecture. |
| 4.1 The learning loop | Perceive → Predict → Resolve → Reinforce as universal | Over-generalizes one language-retrieval specialization. | High | `PROTOCOL_PRIMITIVES_CATALOG.md`, `COGNITIVE_PROTOCOL_ONTOLOGY.md` | Reclassify as Language Prediction-Retrieval Loop; define generic trial structure and other specializations. | Yes; `TaskDefinition` carries `task_family` and `trial_role_sequence`; decomposition matrix shows four other specializations. |
| 4.2 Cognitive state variables | `arousal`, `attention`, `cognitive_load`, `fatigue`, `engagement`, `fluency` as direct state vector | States reified as scalars without operational definitions or validation. | High | `COGNITIVE_PROTOCOL_ONTOLOGY.md` LatentEstimate | Replace with `LatentEstimate` / risk-style estimates with provenance and `exploratory_only` status. | Yes; `StateEstimate` now requires model_id, version, validation_status, alternative_explanations, fallback. |
| 4.2 table | EEG features assigned semantic meanings | MPE core contains EEG semantics. | High | `DOMAIN_INDEPENDENCE_MAP.md`, `SOURCE_CLAIM_AUDIT.md` claims 5-6 | Remove EEG semantics from core; use generic `SensorObservation` and versioned `StateInferenceModel`. | Yes; `SensorObservation` is opaque to core; `StateInferenceModel` carries `exploratory_only` status. |
| 5.1/5.3 Protocol/Session | Protocol and Session conflate logical identity with executable version | Cannot reproduce exact execution. | High | `COGNITIVE_PROTOCOL_ONTOLOGY.md` Program/ProgramVersion/Protocol/ProtocolVersion | Split into `Program`/`ProgramVersion` and `Protocol`/`ProtocolVersion`; Session references exact checksums. | Yes; `MPE_OBJECT_MODEL_V1_1.md` defines the four identity/version objects. |
| 5.2 Step | `expect` and `wait_for_state` step types | Covert response treated as observable; state estimate as blocking condition. | High | `PROTOCOL_PRIMITIVES_CATALOG.md` prohibited primitives | Replace `expect` with `INSTRUCT_COVERT_RETRIEVAL`/`REHEARSAL`/`IMAGERY`; remove `wait_for_state`; add `WAIT_DURATION`, `WAIT_FOR_RESPONSE`, `CHECK_CONTINUATION_CONDITION`, `INSERT_RECOVERY`, `OFFER_SESSION_END`. | Yes; `Instruction` and trial role catalog updated. |
| 5.2 Step | `expected_response_mode` mandatory | Forces every trial to have an observable response. | Medium | `COGNITIVE_PROTOCOL_ONTOLOGY.md` Trial | Replace with `response_requirement` (`required`/`optional`/`none`) and optional `accepted_response_modes`; support exposure/encoding/covert/delayed-probe designs. | Yes; `Trial` corrected. |
| 5.4 Provider | Single `Provider` renders, observes, evaluates | God object; mixes concerns. | High | `DOMAIN_INDEPENDENCE_MAP.md` | Decompose into `DomainProvider`, `Renderer`, `ObservationProvider`, `ResponseInterpreter`, `DomainNormalizer`, `Evaluator`, `Scheduler`, `StateInferenceModel`. | Yes; `MPE_PROVIDER_BOUNDARIES.md` and object model updated. |
| 6.1 Core primitives | `play`, `pause`, `expect`, `wait_for_state`, `increase_difficulty`, `decrease_difficulty` | Premature/unsafe primitives. | High | `PROTOCOL_PRIMITIVES_CATALOG.md` | Remove `expect`/`wait_for_state`; replace generic difficulty with typed dimensions; add `AdaptationDecision` contract. | Yes; `MPE_ADAPTATION_CONTRACT.md` and catalog. |
| 6.3 Recall example | `expect(mental_hebrew)` then optional button | Suggests mental answer timed but correctness optional. | High | `COGNITIVE_PROTOCOL_ONTOLOGY.md` Instruction, `SOURCE_CLAIM_AUDIT.md` claim 7 | Separate covert instruction (`instruction_payload` + `target_operation` + `allotted_duration` + `observable_response_expected`) from observable probe. | Yes; `Instruction` object updated. |
| 6.4 Morphology / 6.5 Prediction | `expect(mental_completion)` | Same covert-response problem. | High | `PROTOCOL_PRIMITIVES_CATALOG.md` | Same as above. | Yes. |
| 7.2 Execution model | Scheduler updates cognitive state estimate | Over-weights latent estimates in main loop. | Medium | `COGNITIVE_PROTOCOL_ONTOLOGY.md` LatentEstimate | Core scheduler processes timestamped events; state estimates feed non-blocking advisory policy. | Yes; `StateEstimate` is diagnostic, non-blocking. |
| 8.2 State estimator | Fuses inputs into state vector | Treats state as confidently estimable. | High | `COGNITIVE_PROTOCOL_ONTOLOGY.md` | Reclassify as `StateInferenceModel` with `exploratory_only` default; estimates advisory. | Yes. |
| 8.3 Safe ranges | `0.5–8.0s`, `0.7x–1.3x`, `0–50%` as safe | Presented as validated ranges without evidence. | Medium | `SOURCE_CLAIM_AUDIT.md` claim 11 | Reclassify as provisional configurable bounds with evidence grade and validation requirement. | Yes; `AdaptationDecision` includes `allowed_bounds` with status and evidence grade. |
| 8.4 Adaptation policy | DSL maps `load > high` to `decrease difficulty` + multi-param changes | Reified thresholds and generic difficulty; multi-dimension changes not declared. | High | `MPE_ADAPTATION_CONTRACT.md` | Single dimension per policy unless compound; full `AdaptationDecision` with provenance, bounds, rollback, abstention; `NO_CHANGE_INSUFFICIENT_EVIDENCE`; `audit_event_id` removed from decision (events reference decision). | Yes; `AdaptationDecision` updated; deployment_status corrected (`shadow_mode` cannot apply changes). |
| 9.1 Provider model / 10.1 Hebrew | `evaluate_response(item, response) -> latency, correctness, confidence` | Latency owned by provider. | High | `DOMAIN_INDEPENDENCE_MAP.md`, `COGNITIVE_PROTOCOL_ONTOLOGY.md` response layers | Decompose response into `CapturedResponse` -> `ResponseInterpretation` -> `DomainNormalizedResponse` -> `Evaluation`; runtime owns timestamps; `Evaluator` returns `answer_status` + `evaluation_status` + `correctness_credit` + `accepted_variant_id`. | Yes; object model updated. |
| 10.1 Hebrew | Single `evaluate_response` returning latency | Latency leakage. | High | `MPE_PROVIDER_BOUNDARIES.md` | `HebrewEvaluator` does not compute latency; runtime computes from `response_window_opened` and `response_completed`. | Yes. |
| 11.2 Signal path | EEG feature vector → MPE adaptive engine | No interpretation layer. | High | `DOMAIN_INDEPENDENCE_MAP.md`, `COGNITIVE_PROTOCOL_ONTOLOGY.md` | Generic `SensorObservation` + `StateInferenceModel` outside core. | Yes. |
| 11.4 Feature extraction | Specific EEG-band meanings | Core architecture assigns semantics. | High | `SOURCE_CLAIM_AUDIT.md` claims 5-6 | Removed from core; moved to experimental model with `exploratory_only` status and alternative explanations. | Yes. |
| 12.1 Session metrics | `time_in_target_state` core KPI | Depends on reified optimal state. | Medium | `SOURCE_CLAIM_AUDIT.md` claim 12 | Removed from Phase 4/5A KPIs; experimental diagnostic only. | Yes; `Outcome` latency metrics stratified by task/response_mode/trial_role. |
| 12.3 Learner-level | `optimal state profile` | Reifies unvalidated model. | Medium | `COGNITIVE_PROTOCOL_ONTOLOGY.md` | Replaced by observed behavioral profile, item retention, latency history. | Yes. |
| 13.1 Event model | `Event` with `event_type`, `payload`, `version` | Lacks full canonical taxonomy and replay semantics. | Medium | `MPE_EVENT_MODEL_V1_1.md` | Expanded taxonomy with timestamp ownership, provenance, replay-deterministic flags, sensitive data flags. | Yes. |
| 14.1 Provider API | Single `provider_render/observe/evaluate` | God object. | High | `DOMAIN_INDEPENDENCE_MAP.md` | Six narrow interfaces; no single provider may render, observe, and evaluate. | Yes. |
| 19. Phase 4 | Core + Hebrew + audio + DSL parser + runtime in one phase | Too broad. | High | `EXECUTIVE_SYNTHESIS.md`, `OPEN_QUESTIONS_AND_DECISIONS.md` | Split into 4A schema, 4B deterministic runtime, 4C Hebrew behavioral integration. | Yes; `MPE_PHASE_4_IMPLEMENTATION_PLAN.md`. |
| 19. Phase 5 | Adaptive Engine + Optional EEG in one phase | EEG acquisition and control mixed. | High | `EXECUTIVE_SYNTHESIS.md` | Split into 5A behavioral adaptation, 5B sensor research, 5C experimental sensor-informed policies. | Yes. |

## Major rejected concepts

1. Universal Perceive-Predict-Resolve-Reinforce loop → reclassified as Language Prediction-Retrieval Loop. (`PROTOCOL_PRIMITIVES_CATALOG.md`, `COGNITIVE_PROTOCOL_ONTOLOGY.md`)
2. `expect(mental_*)` primitive → replaced by explicit covert instruction + observable probe separation. (`PROTOCOL_PRIMITIVES_CATALOG.md`)
3. `wait_for_state(target, timeout)` → removed. (`PROTOCOL_PRIMITIVES_CATALOG.md`)
4. Reified cognitive-state vector → replaced by `LatentEstimate` / `StateEstimate`. (`COGNITIVE_PROTOCOL_ONTOLOGY.md`)
5. EEG semantics in MPE core → removed; `SensorObservation` + `StateInferenceModel`. (`DOMAIN_INDEPENDENCE_MAP.md`)
6. Single `Provider` god object → decomposed into six narrow interfaces. (`DOMAIN_INDEPENDENCE_MAP.md`)
7. Generic `increase_difficulty()`/`decrease_difficulty()` → replaced by typed dimensions and `AdaptationDecision`. (`MPE_ADAPTATION_CONTRACT.md`)
8. "Safe ranges" without evidence → reclassified as provisional configurable bounds. (`SOURCE_CLAIM_AUDIT.md` claim 11, `MPE_ADAPTATION_CONTRACT.md`)
9. `time_in_target_state` as core KPI → removed from Phase 4/5A; experimental diagnostic only. (`SOURCE_CLAIM_AUDIT.md` claim 12)
10. Textual DSL from the start → schema-first; optional textual syntax later. (`MPE_DSL_DECISION_RECORD.md`)
11. "First platform" / "new software category" claims → quarantined as product-positioning hypotheses. (`SOURCE_CLAIM_AUDIT.md` claim 1)
12. Phase 4 as single broad implementation → split into 4A/4B/4C. (`MPE_PHASE_4_IMPLEMENTATION_PLAN.md`)
13. Provider-owned latency / single response path → runtime owns timestamps; response layered into `CapturedResponse` -> `ResponseInterpretation` -> `DomainNormalizedResponse` -> `Evaluation`. (`COGNITIVE_PROTOCOL_ONTOLOGY.md`)
14. `safety_cue` inside `FeedbackEvent` → separated into `SafetyInstruction` category. (`COGNITIVE_PROTOCOL_ONTOLOGY.md`)

## Major retained concepts

1. Screen as secondary, session as auditory/cognitive. (`COGNITIVE_PROTOCOL_ONTOLOGY.md` Instruction, TrialRole)
2. Protocol as declarative structured sequence. (`COGNITIVE_PROTOCOL_ONTOLOGY.md` ProtocolVersion)
3. Event stream as source of truth. (`MPE_EVENT_MODEL_V1_1.md`)
4. Determinism and reproducibility. (`MPE_EVENT_MODEL_V1_1.md` replay semantics)
5. Abstention and explicit uncertainty. (`MPE_ADAPTATION_CONTRACT.md`, `COGNITIVE_PROTOCOL_ONTOLOGY.md` LatentEstimate)
6. Domain independence through providers. (`DOMAIN_INDEPENDENCE_MAP.md`)
7. Hebrew engine as domain authority. (`MPE_HEBREW_PROVIDER_CONTRACT.md`)
8. Safety rules override adaptation. (`COGNITIVE_PROTOCOL_ONTOLOGY.md` Safety)
9. EEG optional and not a correctness detector. (`DOMAIN_INDEPENDENCE_MAP.md`, `MPE_PROVIDER_BOUNDARIES.md`)
10. Staged implementation. (`MPE_PHASE_4_IMPLEMENTATION_PLAN.md`)

## Traceability summary

| Correction area | Audit source | MPE v1.1 document |
|---|---|---|
| Logical/executable identity, Instruction, Trial, Evaluation, ScheduleDecision, AdaptationDecision, Outcome | `COGNITIVE_PROTOCOL_ONTOLOGY.md` §Core entities, §Instruction, §Response processing layers, §Evaluation, §Feedback, §ScheduleDecision, §AdaptationDecision, §LatentEstimate, §Safety, §Outcome | `MPE_OBJECT_MODEL_V1_1.md` |
| Allowed/prohibited primitives, response requirement values | `PROTOCOL_PRIMITIVES_CATALOG.md` §Allowed primitives, §Prohibited primitives, §Response requirement values | `MPE_OBJECT_MODEL_V1_1.md`, `MPE_ARCHITECTURE_V1_1.md` §6 |
| v1.0 claims rejected/accepted (1, 4–13, 14–28) | `SOURCE_CLAIM_AUDIT.md` / `.csv` | `MPE_OBJECT_MODEL_V1_1.md`, `MPE_ARCHITECTURE_V1_1.md` |
| Provider decomposition, EEG outside core | `DOMAIN_INDEPENDENCE_MAP.md` §What belongs in MPE core, §Provider contract table, §MPE core must not contain | `MPE_PROVIDER_BOUNDARIES.md`, `MPE_HEBREW_PROVIDER_CONTRACT.md` |
| Phase 4 split, no DSL, EEG exploratory | `EXECUTIVE_SYNTHESIS.md` §What must change points 6–7, `OPEN_QUESTIONS_AND_DECISIONS.md` closed decisions | `MPE_PHASE_4_IMPLEMENTATION_PLAN.md`, `MPE_DSL_DECISION_RECORD.md` |
| Adaptation contract, bounds, rollback | `COGNITIVE_PROTOCOL_ONTOLOGY.md` §AdaptationDecision, `SOURCE_CLAIM_AUDIT.md` claims 10–11 | `MPE_ADAPTATION_CONTRACT.md` |
| Hebrew authority, variants, pronunciation advisory, scope restriction | `SOURCE_CLAIM_AUDIT.md` claims 14–28 | `MPE_HEBREW_PROVIDER_CONTRACT.md` |
| Trial/task decomposition examples | `PROTOCOL_DECOMPOSITION_MATRIX.csv` all rows | `MPE_ARCHITECTURE_V1_1.md` §4.2 |
| Audit methodology and limitations | `METHODOLOGY_AND_LIMITATIONS.md` §Methodology, §Limitations | `MPE_REVIEW_SUMMARY.md` |
| Phase 3 constraints | `data/hebrew/phase3/PHASE_3_FINAL_REPORT.md` | `MPE_HEBREW_PROVIDER_CONTRACT.md`, `MPE_PHASE_4_IMPLEMENTATION_PLAN.md` Phase 4C |
