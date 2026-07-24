# Phase 4A.5 Walkthrough — Hebrew Morphology Recognition

## 1. Scenario definition

- **Learner objective:** Identify the binyan (verbal pattern) of a presented Hebrew verb form.
- **Protocol purpose:** `assessment`.
- **Exact task:** The learner is shown/hears the Hebrew form `העברתי` and must type the binyan label (e.g., `HIF'IL` or `הפעיל`).
- **Concrete content item (stimulus):** Verb `F_5_העביר` from `data/hebrew/phase3/automatic_gold_100.json`, form `past_first_mf_singular` (`form_key: past_first_mf_singular`, `surface_plain: העברתי`, `surface_vocalized: הֶעֱבַרְתִּי`, `canonical_unvocalized: העברתי`, `root: העביר`, `binyan: HIF'IL`, `status: verified_consensus`).
- **Concrete content item (expected answer):** `ci_binyan_hifil` (surface `HIF'IL`, normalized `HIF'IL`, `accepted_variants` include `HIF'IL`, `הפעיל`, and a partial-credit variant `HIFIL`).
- **Response requirement:** `required`.
- **Accepted response modes:** `[typed]`.
- **Assumptions:**
  - `ProtocolVersion` `prv_morphology_assess_v1` and `ProgramVersion` `pv_morphology_program_v1` are validated.
  - `TaskDefinition` `td_morphology_binyan_v1` uses `task_family: perceptual_discrimination`.
  - `HebrewDomainProvider` exposes a `ContentItem` for the binyan label with `accepted_variants`.
- **Explicitly out-of-scope behavior:**
  - No root extraction by MPE core; root/binyan information is in the domain `ContentItem`.
  - No adaptation or EEG.

## 2. Object instantiation ledger

| Object type | Canonical identifier | Creation point | Immutable fields | Mutable derived state | Persistence class | Owning component | Source specification section |
|---|---|---|---|---|---|---|---|
| `Program` | `prog_morphology_program` | Fixture | `program_id`, `name`, `transfer_claim_level` | — | persistent | author/registry | `MPE_OBJECT_MODEL_V1_1.md` §Program |
| `ProgramVersion` | `pv_morphology_program_v1` | Fixture | `program_version_id`, `program_id`, `protocol_version_sequence`, `checksum` | — | persistent | author/registry | `MPE_OBJECT_MODEL_V1_1.md` §ProgramVersion |
| `Protocol` | `proto_morphology_assess` | Fixture | `protocol_id`, `name`, `purpose: assessment` | — | persistent | author/registry | `MPE_OBJECT_MODEL_V1_1.md` §Protocol |
| `ProtocolVersion` | `prv_morphology_assess_v1` | Fixture | `protocol_version_id`, `protocol_id`, `block_sequence`, `required_providers`, `checksum` | — | persistent | author/registry | `MPE_OBJECT_MODEL_V1_1.md` §ProtocolVersion |
| `TaskDefinition` | `td_morphology_binyan_v1` | Fixture | `task_definition_id`, `task_family: perceptual_discrimination`, `trial_role_sequence` | — | persistent | author/registry | `MPE_OBJECT_MODEL_V1_1.md` §TaskDefinition |
| `ContentItem` stimulus | `ci_hifil_form_haavarti` | `HebrewDomainProvider.get_item` | `content_item_id`, `provider_id`, `surface_form`, `normalized_form`, `root`, `binyan`, `status` | `abstention_status` | persistent / cached | `HebrewDomainProvider` | `MPE_OBJECT_MODEL_V1_1.md` §ContentItem |
| `ContentItem` expected | `ci_binyan_hifil` | `HebrewDomainProvider.get_expected_answer` | `content_item_id`, `provider_id`, `surface_form`, `normalized_form`, `accepted_variants`, `status`, `scope_status` | `abstention_status` | persistent / cached | `HebrewDomainProvider` | `MPE_OBJECT_MODEL_V1_1.md` §ContentItem |
| `Session` | `sess_morph_001` | `session_created` | `session_id`, `program_version_id`, `protocol_version_id`, `learner_id` | `status` | derived / stream-only | runtime | `MPE_OBJECT_MODEL_V1_1.md` §Session |
| `BlockExecution` | `block_assess_001` | `block_started` | `block_id`, `session_id`, `block_type: assessment` | `completed_at`, `completed_trial_count` | derived / stream-only | runtime | `MPE_OBJECT_MODEL_V1_1.md` §Block |
| `Trial` | `trial_morph_001` | `trial_created` | `trial_id`, `session_id`, `task_definition_id: td_morphology_binyan_v1`, `content_item_ids: [ci_hifil_form_haavarti, ci_binyan_hifil]`, `response_requirement: required` | `status` | derived / stream-only | runtime | `MPE_OBJECT_MODEL_V1_1.md` §Trial |
| `StimulusRequest` | `sr_form_001` | `stimulus_requested` | `stimulus_request_id`, `trial_id`, `content_item_id: ci_hifil_form_haavarti` | — | stream-only | runtime | `MPE_OBJECT_MODEL_V1_1.md` §StimulusRequest |
| `RenderedStimulus` | `rs_form_001` | `stimulus_ready` | `rendered_stimulus_id`, `stimulus_request_id`, `media_handle`, `duration` | — | persistent / stream-only | `HebrewRenderer` | `MPE_OBJECT_MODEL_V1_1.md` §RenderedStimulus |
| `Instruction` | `instr_morph_001` | `instruction_started` | `instruction_id`, `trial_id`, `instruction_type: REQUEST_OVERT_RESPONSE`, `instruction_payload`, `observable_response_expected: true` | `completed_at` | derived / stream-only | runtime | `MPE_OBJECT_MODEL_V1_1.md` §Instruction |
| `ResponseWindow` | `rw_morph_001` | `response_window_opened` | `response_window_id`, `trial_id`, `response_modes_accepted: [typed]`, `opened_at`, `deadline_at` | — | stream-only | runtime | `MPE_OBJECT_MODEL_V1_1.md` §ResponseWindow |
| `Observation` | `obs_morph_001` | `observation_received` | `observation_id`, `response_window_id`, `observation_type: typed_input`, `payload`, `quality_*` | — | persistent / stream-only | `KeyboardObservationProvider` | `MPE_OBJECT_MODEL_V1_1.md` §Observation |
| `CapturedResponse` | `cr_morph_001` | `captured_response_created` | `captured_response_id`, `response_window_id`, `observation_ids`, `response_mode: typed`, `captured_payload` | — | persistent / stream-only | runtime | `MPE_OBJECT_MODEL_V1_1.md` §CapturedResponse |
| `ResponseInterpretation` | `ri_morph_001` | `response_interpreted` | `response_interpretation_id`, `captured_response_id`, `interpreter_id`, `interpreted_payload`, `interpretation_type: typed_text` | — | persistent / stream-only | `ResponseInterpreter` | `MPE_OBJECT_MODEL_V1_1.md` §ResponseInterpretation |
| `DomainNormalizedResponse` | `dnr_morph_001` | `domain_response_normalized` | `domain_normalized_response_id`, `response_interpretation_id`, `normalizer_id`, `normalized_payload` | — | persistent / stream-only | `HebrewDomainNormalizer` | `MPE_OBJECT_MODEL_V1_1.md` §DomainNormalizedResponse |
| `Evaluation` | `eval_morph_001` | `evaluation_completed` / `abstained` / `failed` | `evaluation_id`, `trial_id`, `evaluator_id`, `answer_status`, `evaluation_status` | — | persistent / stream-only | `HebrewEvaluator` | `MPE_OBJECT_MODEL_V1_1.md` §Evaluation |
| `FeedbackEvent` | `fb_morph_001` | `feedback_started` | `feedback_event_id`, `trial_id`, `evaluation_id`, `feedback_category`, `feedback_type`, `content_item_id` | `completed_at` | persistent / stream-only | runtime | `MPE_OBJECT_MODEL_V1_1.md` §FeedbackEvent |
| `ScheduleDecision` | `sd_morph_001` | `schedule_decision` | `schedule_decision_id`, `session_id`, `selected_item_ids`, `decision_type`, `decision_status`, `source_event_ids` | — | persistent / stream-only | `Scheduler` | `MPE_OBJECT_MODEL_V1_1.md` §ScheduleDecision |
| `EvidenceRecord` | `er_morph_001` | `evidence_record_created` | `evidence_record_id`, `decision_or_evaluation_id`, `source_event_ids`, `evidence_type` | — | persistent / stream-only | runtime / `HebrewEvaluator` | `MPE_OBJECT_MODEL_V1_1.md` §EvidenceRecord |
| `Outcome` | `outcome_morph_001` | computed after terminal event | `session_id`, `computation_version` | aggregate metrics | derived | runtime | `MPE_OBJECT_MODEL_V1_1.md` §Outcome |

## 3. Event-by-event execution trace (successful canonical response)

| seq | event_type | event_id | causation_event_ids | correlation_id | object/fact introduced | canonical payload fields | owning component | replay classification | data_classification | state before | state after |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `session_created` | `ev_m1_001` | — | `corr_morph_001` | `Session` `sess_morph_001` | `session_id`, `program_version_id`, `protocol_version_id`, `learner_id` | runtime | deterministic | public | none | `created` |
| 2 | `session_started` | `ev_m1_002` | `ev_m1_001` | `corr_morph_001` | clock begins | `session_id`, `random_seed` | runtime | deterministic | public | `created` | `started` |
| 3 | `block_started` | `ev_m1_003` | `ev_m1_002` | `corr_block_m001` | `BlockExecution` `block_assess_001` | `session_id`, `block_id`, `block_type: assessment` | runtime | deterministic | public | none | `in_progress` |
| 4 | `schedule_decision` | `ev_m1_004` | `ev_m1_002` | `corr_sched_m001` | `ScheduleDecision` `sd_morph_001` | `schedule_decision_id`, `session_id`, `source_event_ids: [ev_m1_002]`, `selected_item_ids: [ci_hifil_form_haavarti]`, `decision_type: next_trial`, `decision_status: made` | `Scheduler` | deterministic | public | — | trial planned |
| 5 | `trial_created` | `ev_m1_005` | `ev_m1_004` | `corr_trial_m001` | `Trial` `trial_morph_001` | `trial_id`, `session_id`, `block_id`, `task_definition_id: td_morphology_binyan_v1`, `content_item_ids: [ci_hifil_form_haavarti, ci_binyan_hifil]`, `response_requirement: required`, `accepted_response_modes: [typed]` | runtime | deterministic | public | none | `planned` |
| 6 | `stimulus_requested` | `ev_m1_006` | `ev_m1_005` | `corr_render_m001` | `StimulusRequest` `sr_form_001` | `stimulus_request_id`, `trial_id`, `content_item_id: ci_hifil_form_haavarti`, `renderer_id: hebrew_tts`, `requested_at`, `scheduled_for` | runtime | deterministic | public | planned | rendering |
| 7 | `stimulus_ready` | `ev_m1_007` | `ev_m1_006` | `corr_render_m001` | `RenderedStimulus` `rs_form_001` | `stimulus_request_id`, `rendered_stimulus_id`, `renderer_id`, `renderer_version: 1.2.0`, `rendered_at`, `media_handle`, `duration` | `HebrewRenderer` | depends on renderer | public | rendering | ready |
| 8 | `stimulus_started` | `ev_m1_008` | `ev_m1_007` | `corr_render_m001` | playback begins | `trial_id`, `stimulus_request_id`, `rendered_stimulus_id`, `started_at` | `HebrewRenderer` | no | public | ready | playing |
| 9 | `stimulus_completed` | `ev_m1_009` | `ev_m1_008` | `corr_render_m001` | playback ends | `trial_id`, `stimulus_request_id`, `completed_at` | `HebrewRenderer` | no | public | playing | awaiting response |
| 10 | `instruction_started` | `ev_m1_010` | `ev_m1_009` | `corr_trial_m001` | `Instruction` `instr_morph_001` | `trial_id`, `instruction_id`, `instruction_type: REQUEST_OVERT_RESPONSE`, `instruction_payload: "Type the binyan of this form"`, `target_operation: identify_binyan`, `allotted_duration: 30.0`, `observable_response_expected: true` | runtime | deterministic | public | awaiting response | listening |
| 11 | `response_window_opened` | `ev_m1_011` | `ev_m1_010` | `corr_trial_m001` | `ResponseWindow` `rw_morph_001` | `response_window_id`, `trial_id`, `response_modes_accepted: [typed]`, `opened_at`, `deadline_at`, `timeout_policy: hard_deadline` | runtime | deterministic | public | listening | listening |
| 12 | `observation_received` | `ev_m1_012` | `ev_m1_011` | `corr_resp_m001` | `Observation` `obs_morph_001` | `observation_id`, `response_window_id`, `provider_id: keyboard_v1`, `provider_version: 1.0.0`, `observation_type: typed_input`, `payload: "HIF'IL"`, `received_at`, `quality_dimensions`, `quality_flags`, `quality_model_id: typed_quality_v1`, `quality_model_version: 1.0.1` | `KeyboardObservationProvider` | no | consent_gated | listening | captured |
| 13 | `captured_response_created` | `ev_m1_013` | `ev_m1_012` | `corr_resp_m001` | `CapturedResponse` `cr_morph_001` | `captured_response_id`, `response_window_id`, `observation_ids: [obs_morph_001]`, `response_mode: typed`, `captured_payload: "HIF'IL"`, `captured_at`, `device_provenance: {keyboard_id: kb_001}`, `quality_flags: []` | runtime | deterministic | consent_gated | captured | interpreted |
| 14 | `response_interpreted` | `ev_m1_014` | `ev_m1_013` | `corr_resp_m001` | `ResponseInterpretation` `ri_morph_001` | `response_interpretation_id`, `response_window_id: rw_morph_001`, `captured_response_id`, `interpreter_id: typed_text_v1`, `interpreter_version: 1.0.0`, `interpreted_payload: "HIF'IL"`, `interpretation_type: typed_text`, `interpretation_confidence: 0.99` | `ResponseInterpreter` | deterministic | consent_gated | interpreted | normalized |
| 15 | `domain_response_normalized` | `ev_m1_015` | `ev_m1_014` | `corr_resp_m001` | `DomainNormalizedResponse` `dnr_morph_001` | `domain_normalized_response_id`, `response_window_id: rw_morph_001`, `response_interpretation_id`, `normalizer_id: hebrew_norm_v1`, `normalizer_version: 1.0.0`, `response_mode: typed`, `normalized_payload: "HIF'IL"`, `extracted_at`, `uncertainty: 0.01` | `HebrewDomainNormalizer` | deterministic | consent_gated | normalized | evaluated |
| 16 | `evaluation_completed` | `ev_m1_016` | `ev_m1_015` | `corr_eval_m001` | `Evaluation` `eval_morph_001` | `evaluation_id`, `trial_id`, `evaluator_id: hebrew_eval_v1`, `evaluator_version: 1.0.1`, `domain_normalized_response_id`, `expected_content_item_id: ci_binyan_hifil`, `answer_status: correct`, `evaluation_status: completed`, `correctness_credit: 1.0`, `accepted_variant_id: av_hifil_full`, `evidence_group: eran_tomer_derivative`, `scope_status: verified_consensus`, `confidence: 0.99` | `HebrewEvaluator` | deterministic | public | evaluated | feedback |
| 17 | `evidence_record_created` | `ev_m1_017` | `ev_m1_016` | `corr_eval_m001` | `EvidenceRecord` `er_morph_001` | `evidence_record_id`, `decision_or_evaluation_id: eval_morph_001`, `source_event_ids: [ev_m1_015, ev_m1_016]`, `evidence_type: domain_evaluation`, `summary` | runtime / `HebrewEvaluator` | deterministic | public | feedback | feedback |
| 18 | `feedback_started` | `ev_m1_018` | `ev_m1_016` | `corr_trial_m001` | `FeedbackEvent` `fb_morph_001` | `feedback_event_id`, `trial_id`, `evaluation_id: eval_morph_001`, `feedback_category: PERFORMANCE`, `feedback_type: correct_answer`, `content_item_id: ci_binyan_hifil`, `started_at` | runtime | deterministic | public | feedback | feedback playing |
| 19 | `feedback_completed` | `ev_m1_019` | `ev_m1_018` | `corr_trial_m001` | feedback ends | `feedback_event_id`, `completed_at`, `duration_observed` | `HebrewRenderer` | no | public | playing | scheduling |
| 20 | `schedule_decision` | `ev_m1_020` | `ev_m1_019` | `corr_sched_m002` | `ScheduleDecision` `sd_morph_002` | `schedule_decision_id`, `session_id`, `source_event_ids: [ev_m1_019]`, `selected_item_ids: []`, `decision_type: session_end`, `decision_status: made` | `Scheduler` | deterministic | public | scheduling | terminal planned |
| 21 | `block_completed` | `ev_m1_021` | `ev_m1_020` | `corr_block_m001` | block complete | `session_id`, `block_id`, `completed_trial_count: 1` | runtime | deterministic | public | in_progress | completed |
| 22 | `session_completed` | `ev_m1_022` | `ev_m1_021` | `corr_morph_001` | session terminal | `session_id`, `completed_at`, `final_trial_index: 1` | runtime | deterministic | public | in_progress | completed |

## 4. Provider-call ledger

| Provider | Operation | Input object / identifier | Output object / identifier | Timeout | Retry | Error mapping | Side effects | Deterministic | Exact output must be captured for replay |
|---|---|---|---|---|---|---|---|---|---|
| `HebrewDomainProvider` | `get_item(ci_hifil_form_haavarti)` | `ci_hifil_form_haavarti` | `ContentItem` with `root`, `binyan`, `status` | 2s | 2 | `out_of_scope` -> `evaluation_abstained` | none | yes | no |
| `HebrewDomainProvider` | `get_expected_answer(cue, target)` | form `ci_hifil_form_haavarti`, label `binyan` | `ContentItem` `ci_binyan_hifil` with `accepted_variants` | 2s | 2 | `out_of_scope` -> `evaluation_abstained` | none | yes | no |
| `HebrewRenderer` | `render(sr_form_001)` | `StimulusRequest` `sr_form_001` | `RenderedStimulus` `rs_form_001` | 5s+duration | 1 | `render_failed` -> `renderer_fallback` | may cache media | no | yes (duration/handle) |
| `KeyboardObservationProvider` | `start_listening` / `poll` / `stop_listening` | `rw_morph_001` | `Observation` `obs_morph_001` | 100ms poll | continuous | `device_error` -> `signal_quality_changed` / `safety_rule_triggered` | captures input | no | yes (payload) |
| `ResponseInterpreter` | `interpret(cr_morph_001)` | `CapturedResponse` `cr_morph_001` | `ResponseInterpretation` `ri_morph_001` | 2s | 0 | `interpretation_failed` -> low-confidence `response_interpreted` + `evaluation_abstained` | none | yes (typed) | no |
| `HebrewDomainNormalizer` | `normalize(ri_morph_001)` | `ResponseInterpretation` `ri_morph_001` | `DomainNormalizedResponse` `dnr_morph_001` | 1s | 0 | `normalization_failed` / `out_of_scope` -> high-uncertainty `dnr` + `evaluation_abstained`/`failed` | none | yes | no |
| `HebrewEvaluator` | `evaluate(dnr_morph_001, ci_binyan_hifil, trial_context)` | `DomainNormalizedResponse`, expected `ContentItem` | `Evaluation` `eval_morph_001` | 2s | 0 | `abstained` -> `evaluation_abstained`; `failed` -> `evaluation_failed`; `out_of_scope` -> `evaluation_abstained` | none | yes | yes |
| `Scheduler` | `select_next(context)` | session history | `ScheduleDecision` | 500ms | 0 | `scheduling_failed` -> `protocol_terminated` | none | yes | no |

## 5. State-machine trace

Same canonical states as Slice 1; only the `TaskDefinition` and `content_item_ids` differ. Transitions are identical at the session/block/trial/response/safety/adaptation level. The key distinction is in `Trial` content and `Evaluation` answer semantics.

| Level | Transition | Entry condition | Exit condition | Generated events |
|---|---|---|---|---|
| Session | `created` -> `started` | `session_created` validated | `session_started` | `session_created`, `session_started` |
| Session | `started` -> `completed` | `schedule_decision` emits `session_end` | `session_completed` | `session_completed` |
| Block | `not_started` -> `in_progress` | session started | `block_started` | `block_started` |
| Block | `in_progress` -> `completed` | all trials completed | `block_completed` | `block_completed` |
| Trial | `planned` -> `started` | `trial_created` | `response_window_opened` | `trial_created`, `stimulus_*`, `instruction_started`, `response_window_opened` |
| Trial | `started` -> `evaluated` | evaluation returned | `evaluation_completed` | `observation_received`, `captured_response_created`, `response_interpreted`, `domain_response_normalized`, `evaluation_completed` |
| Trial | `evaluated` -> complete | `feedback_completed` + `schedule_decision` | `schedule_decision` | `feedback_started`, `feedback_completed`, `schedule_decision` |
| Response | `listening` -> `captured` -> `interpreted` -> `normalized` -> `evaluated` | typed input processed through pipeline | `evaluation_completed` | response-pipeline events |
| Safety | `idle` | no safety rule triggered | — | none |
| Adaptation | inactive | Phase 5A+ only | — | none |

## 6. Persistence and reconstruction trace

Same classification table as Slice 1 with these additions:

| Object / event | persistent | derived | cached | ephemeral | stream-only | Reconstruction source | Snapshot eligibility |
|---|---|---|---|---|---|---|---|
| `ContentItem` `ci_hifil_form_haavarti` | X | | X | | | `HebrewDomainProvider` fixture | yes |
| `ContentItem` `ci_binyan_hifil` | X | | X | | | `HebrewDomainProvider` fixture | yes |
| `TaskDefinition` `td_morphology_binyan_v1` | X | | | | | fixture | yes |
| `Evaluation` `eval_morph_001` | X | | | | X | `evaluation_completed` | no |
| `Outcome` `outcome_morph_001` | | X | X | | | all session events; stratified by `task_definition_id` and `response_mode` | yes |

### Replay procedure

Identical to Slice 1: read events in `session_sequence_number` order, instantiate objects, and recompute `Outcome`. The `Outcome` computation uses `task_definition_id: td_morphology_binyan_v1` and `response_mode: typed` as strata.

## 7. Validation checklist

| Rule category | Check | Result |
|---|---|---|
| Identifiers | Canonical `<object>_id` names used. | Pass |
| Enums | `task_family: perceptual_discrimination`, `response_requirement: required`, `answer_status`, `evaluation_status`, `feedback_category: PERFORMANCE`, `feedback_type`, `observation_type`, `interpretation_type`, `response_mode` all valid. | Pass |
| Foreign references | `expected_content_item_id` references `ci_binyan_hifil`; `domain_normalized_response_id` references `dnr_morph_001`. | Pass |
| Provider compatibility | `HebrewEvaluator` receives `DomainNormalizedResponse`; `HebrewDomainProvider` provides expected answer with `accepted_variants`. | Pass |
| Version compatibility | `ProtocolVersion.dependency_versions` matches provider versions. | Pass (assumed) |
| Event ordering | Response pipeline events in correct causal order. | Pass |
| Payload completeness | All required event fields present. | Pass |
| Data classification | Typed input events `consent_gated`; `evaluation_completed` `public`. | Pass |
| Lifecycle legality | Session and trial reach terminal states legally. | Pass |
| Outcome stratification | `Outcome.latency_summaries` can be keyed by `task_definition_id` and `response_mode`. | Pass |

## 8. Failure and recovery branches

| Triggering condition | Error classification | Event emitted | Retry / fallback | User-visible effect | State-machine transition | Terminal / recoverable |
|---|---|---|---|---|---|---|
| Learner types `HIF'IL` | success | `evaluation_completed` (`answer_status: correct`, `correctness_credit: 1.0`, `accepted_variant_id: av_hifil_full`) | none | confirmatory feedback | `evaluated` -> scheduling | recoverable |
| Learner types `הפעיל` | success | `evaluation_completed` (`answer_status: acceptable_variant`, `accepted_variant_id: av_hifil_hebrew`, `correctness_credit: 1.0`) | none | confirmatory feedback | `evaluated` -> scheduling | recoverable |
| Learner types `HIFIL` (missing aleph glottal stop) | success | `evaluation_completed` (`answer_status: partially_correct`, `correctness_credit: 0.5`) | none | feedback with correct form | `evaluated` -> scheduling | recoverable |
| Learner types `PA'AL` | success | `evaluation_completed` (`answer_status: incorrect`, `correctness_credit: 0.0`, `error_category: binyan`) | none | correct-answer feedback | `evaluated` -> scheduling | recoverable |
| Form is outside 100-verb subset or unknown binyan | out_of_scope | `evaluation_abstained` (`evaluation_status: out_of_scope`) | none | skip / neutral prompt | `evaluated` (abstained) -> scheduling | recoverable |
| `HebrewEvaluator` cannot decide among binyan candidates | abstention | `evaluation_abstained` (`answer_status: unevaluable`, `evaluation_status: abstained`) | none | neutral feedback / re-prompt | `evaluated` (abstained) -> scheduling | recoverable |
| `HebrewDomainNormalizer` cannot normalize typed label (e.g., mixed scripts) | normalization ambiguity | `domain_response_normalized` (`uncertainty: 1.0`) + `evaluation_abstained` | none | neutral feedback | `evaluated` (abstained) -> scheduling | recoverable |
| `HebrewEvaluator` engine exception | provider failure | `evaluation_failed` (`evaluation_status: failed`, `error_category: engine_error` or `version_mismatch`) | 0 retries | neutral feedback; log | `evaluated` (failed) -> scheduling or safety | recoverable if isolated |

## 9. Architecture stress findings

| Check | Finding | Severity |
|---|---|---|
| Missing object | None. `ContentItem` can represent a non-lexical label (binyan) with `accepted_variants`. | — |
| Missing event | None. `evaluation_completed` supports `acceptable_variant` and `partially_correct`. | — |
| Undefined identifier | None. | — |
| Ambiguous enum | None. `answer_status` includes `partially_correct` and `acceptable_variant` for this case. | — |
| Illegal transition | None. | — |
| Provider-boundary violation | None. `HebrewEvaluator` compares normalized label to expected label; MPE core does not know binyan rules. | — |
| Replay gap | None. | — |
| Persistence ambiguity | None. `Outcome` stratification fields support `task_definition` and `response_mode`. | — |
| Safety ambiguity | None. | — |
| Hebrew authority leakage | None. Binyan identification is delegated to `HebrewEvaluator` using `ContentItem` metadata. | — |
| Hidden implementation decision | None. `TaskDefinition` selection and `ContentItem` accepted-variants semantics are explicit. | — |

**Conclusion for this slice:** The architecture supports morphology recognition, including partial correctness and multiple acceptable answers, without MPE core changes.
