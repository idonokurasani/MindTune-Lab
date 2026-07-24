# Phase 4A.5 Walkthrough — Hebrew Vocabulary Recall

## 1. Scenario definition

- **Learner objective:** Recall the Hebrew infinitive for the English/Italian cue "to learn" / "imparare".
- **Protocol purpose:** `retrieval`.
- **Exact task:** The learner is presented with a cue ("imparare" in Italian, or "to learn" in English) and must type the Hebrew infinitive.
- **Concrete content item (expected answer):** Verb `A_4_למד` from `data/hebrew/phase3/automatic_gold_100.json`: infinitive `לִלְמוֹד`, plain `ללמוד`, root `למד`, binyan `PA'AL`, status `verified_consensus`.
- **Content item (cue):** `ci_italian_imparare` (surface "imparare", content_type "word", provider_id "multilingual_cue_provider").
- **Content item (feedback):** `ci_knowledge_lilmod` (surface "לִלְמוֹד means imparare").
- **Response requirement:** `required`.
- **Accepted response modes:** `[typed, voice]`. This walkthrough uses `typed`.
- **Assumptions:**
  - `ProtocolVersion` `prv_hebrew_recall_v1` is loaded and validated.
  - `ProgramVersion` `pv_hebrew_vocab_v1` references `prv_hebrew_recall_v1`.
  - `HebrewDomainProvider` returns `ContentItem` `ci_hebrew_lilmod` with `status == verified_consensus` and an `accepted_variants` list.
  - `HebrewEvaluator` is available and its version matches `ProtocolVersion.dependency_versions`.
- **Explicitly out-of-scope behavior:**
  - No EEG or sensor input.
  - No adaptation (Phase 5A+).
  - No speech response in this typed branch (voice would add `ResponseInterpreter` ASR but is not exercised here).

## 2. Object instantiation ledger

| Object type | Canonical identifier | Creation point | Immutable fields | Mutable derived state | Persistence class | Owning component | Source specification section |
|---|---|---|---|---|---|---|---|
| `Program` | `prog_hebrew_vocab` | Fixture | `program_id`, `name`, `transfer_claim_level` | — | persistent | author/registry | `MPE_OBJECT_MODEL_V1_1.md` §Program |
| `ProgramVersion` | `pv_hebrew_vocab_v1` | Fixture | `program_version_id`, `program_id`, `protocol_version_sequence`, `checksum` | — | persistent | author/registry | `MPE_OBJECT_MODEL_V1_1.md` §ProgramVersion |
| `Protocol` | `proto_hebrew_recall` | Fixture | `protocol_id`, `name`, `purpose` | — | persistent | author/registry | `MPE_OBJECT_MODEL_V1_1.md` §Protocol |
| `ProtocolVersion` | `prv_hebrew_recall_v1` | Fixture | `protocol_version_id`, `protocol_id`, `block_sequence`, `required_providers`, `checksum` | — | persistent | author/registry | `MPE_OBJECT_MODEL_V1_1.md` §ProtocolVersion |
| `TaskDefinition` | `td_overt_recall_v1` | Fixture | `task_definition_id`, `task_family`, `trial_role_sequence` | — | persistent | author/registry | `MPE_OBJECT_MODEL_V1_1.md` §TaskDefinition |
| `ContentItem` cue | `ci_italian_imparare` | `HebrewDomainProvider.get_prompt` / fixture | `content_item_id`, `provider_id`, `checksum`, `surface_form` | `status` (in provider) | persistent / cached | `HebrewDomainProvider` | `MPE_OBJECT_MODEL_V1_1.md` §ContentItem; `MPE_HEBREW_PROVIDER_CONTRACT.md` §HebrewDomainProvider |
| `ContentItem` expected | `ci_hebrew_lilmod` | `HebrewDomainProvider.get_expected_answer` | `content_item_id`, `provider_id`, `surface_form`, `normalized_form`, `accepted_variants`, `status` | `abstention_status` | persistent / cached | `HebrewDomainProvider` | `MPE_OBJECT_MODEL_V1_1.md` §ContentItem |
| `Session` | `sess_vocab_001` | `session_created` event | `session_id`, `program_version_id`, `protocol_version_id`, `learner_id` | `status`, `latest_event_sequence_number` | derived / stream-only | runtime | `MPE_OBJECT_MODEL_V1_1.md` §Session |
| `BlockExecution` | `block_assessment_001` | `block_started` event | `block_id`, `session_id`, `block_type` | `completed_at`, `completed_trial_count` | derived / stream-only | runtime | `MPE_OBJECT_MODEL_V1_1.md` §Block |
| `Trial` | `trial_vocab_001` | `trial_created` event | `trial_id`, `session_id`, `task_definition_id`, `content_item_ids`, `response_requirement` | `status` (derived) | derived / stream-only | runtime | `MPE_OBJECT_MODEL_V1_1.md` §Trial |
| `StimulusRequest` | `sr_cue_001` | `stimulus_requested` event | `stimulus_request_id`, `trial_id`, `content_item_id`, `renderer_id` | — | stream-only | runtime | `MPE_OBJECT_MODEL_V1_1.md` §StimulusRequest |
| `RenderedStimulus` | `rs_cue_001` | `stimulus_ready` event | `rendered_stimulus_id`, `stimulus_request_id`, `media_handle`, `duration` | — | persistent / stream-only | `HebrewRenderer` | `MPE_OBJECT_MODEL_V1_1.md` §RenderedStimulus |
| `Instruction` | `instr_request_001` | `instruction_started` event | `instruction_id`, `trial_id`, `instruction_type`, `instruction_payload`, `observable_response_expected` | `completed_at` | derived / stream-only | runtime | `MPE_OBJECT_MODEL_V1_1.md` §Instruction |
| `ResponseWindow` | `rw_001` | `response_window_opened` event | `response_window_id`, `trial_id`, `response_modes_accepted`, `opened_at` | — | stream-only | runtime | `MPE_OBJECT_MODEL_V1_1.md` §ResponseWindow |
| `Observation` | `obs_typed_001` | `observation_received` event | `observation_id`, `response_window_id`, `provider_id`, `observation_type`, `payload`, `quality_*` | — | persistent / stream-only | `KeyboardObservationProvider` | `MPE_OBJECT_MODEL_V1_1.md` §Observation |
| `CapturedResponse` | `cr_001` | `captured_response_created` event | `captured_response_id`, `response_window_id`, `observation_ids`, `response_mode`, `captured_payload` | — | persistent / stream-only | runtime | `MPE_OBJECT_MODEL_V1_1.md` §CapturedResponse |
| `ResponseInterpretation` | `ri_001` | `response_interpreted` event | `response_interpretation_id`, `captured_response_id`, `interpreter_id`, `interpreted_payload` | — | persistent / stream-only | `HebrewResponseInterpreter` / generic | `MPE_OBJECT_MODEL_V1_1.md` §ResponseInterpretation |
| `DomainNormalizedResponse` | `dnr_001` | `domain_response_normalized` event | `domain_normalized_response_id`, `response_interpretation_id`, `normalizer_id`, `normalized_payload` | — | persistent / stream-only | `HebrewDomainNormalizer` | `MPE_OBJECT_MODEL_V1_1.md` §DomainNormalizedResponse |
| `Evaluation` | `eval_001` | `evaluation_completed` event | `evaluation_id`, `trial_id`, `evaluator_id`, `answer_status`, `evaluation_status` | — | persistent / stream-only | `HebrewEvaluator` | `MPE_OBJECT_MODEL_V1_1.md` §Evaluation |
| `FeedbackEvent` | `fb_001` | `feedback_started` event | `feedback_event_id`, `trial_id`, `feedback_category`, `content_item_id` | `completed_at` | persistent / stream-only | runtime | `MPE_OBJECT_MODEL_V1_1.md` §FeedbackEvent |
| `ScheduleDecision` | `sd_001` | `schedule_decision` event | `schedule_decision_id`, `session_id`, `selected_item_ids`, `decision_type`, `decision_status`, `source_event_ids` | — | persistent / stream-only | `Scheduler` | `MPE_OBJECT_MODEL_V1_1.md` §ScheduleDecision |
| `EvidenceRecord` | `er_001` | `evidence_record_created` event | `evidence_record_id`, `decision_or_evaluation_id`, `source_event_ids` | — | persistent / stream-only | runtime / `HebrewEvaluator` | `MPE_OBJECT_MODEL_V1_1.md` §EvidenceRecord |
| `Outcome` | `outcome_vocab_001` | Computed after `session_completed` | `session_id`, `computation_version` | All aggregate fields | derived | runtime | `MPE_OBJECT_MODEL_V1_1.md` §Outcome |

## 3. Event-by-event execution trace (successful canonical response)

| seq | event_type | event_id | causation_event_ids | correlation_id | object/fact introduced | canonical payload fields | owning component | replay classification | data_classification | state before | state after |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `session_created` | `ev_s1_001` | — | `corr_sess_001` | `Session` `sess_vocab_001` | `session_id`, `program_version_id`, `protocol_version_id`, `learner_id` | runtime | deterministic | public | none | `created` |
| 2 | `session_started` | `ev_s1_002` | `ev_s1_001` | `corr_sess_001` | session clock begins | `session_id`, `random_seed`, `start_parameters` | runtime | deterministic | public | `created` | `started` |
| 3 | `block_started` | `ev_s1_003` | `ev_s1_002` | `corr_block_001` | `BlockExecution` `block_assessment_001` | `session_id`, `block_id`, `block_type: assessment` | runtime | deterministic | public | none | `in_progress` |
| 4 | `schedule_decision` | `ev_s1_004` | `ev_s1_002` | `corr_sched_001` | `ScheduleDecision` `sd_001` | `schedule_decision_id`, `session_id`, `source_event_ids: [ev_s1_002]`, `selected_item_ids: [ci_hebrew_lilmod]`, `decision_type: next_trial`, `decision_status: made` | `Scheduler` | deterministic | public | — | trial planned |
| 5 | `trial_created` | `ev_s1_005` | `ev_s1_004` | `corr_trial_001` | `Trial` `trial_vocab_001` | `trial_id`, `session_id`, `block_id`, `task_definition_id: td_overt_recall_v1`, `content_item_ids: [ci_hebrew_lilmod]`, `response_requirement: required`, `accepted_response_modes: [typed, voice]` | runtime | deterministic | public | none | `planned` |
| 6 | `instruction_started` | `ev_s1_006` | `ev_s1_005` | `corr_trial_001` | `Instruction` `instr_request_001` | `trial_id`, `instruction_id`, `instruction_type: REQUEST_OVERT_RESPONSE`, `instruction_payload: "Type or say the Hebrew for imparare"`, `target_operation: type_hebrew_infinitive`, `allotted_duration: 30.0`, `observable_response_expected: true` | runtime | deterministic | public | planned | `awaiting_response` |
| 7 | `stimulus_requested` | `ev_s1_007` | `ev_s1_005` | `corr_render_001` | `StimulusRequest` `sr_cue_001` | `stimulus_request_id`, `trial_id`, `content_item_id: ci_italian_imparare`, `renderer_id: hebrew_tts`, `requested_at`, `scheduled_for` | runtime | deterministic | public | planned | rendering |
| 8 | `stimulus_ready` | `ev_s1_008` | `ev_s1_007` | `corr_render_001` | `RenderedStimulus` `rs_cue_001` | `stimulus_request_id`, `rendered_stimulus_id`, `renderer_id`, `renderer_version: 1.2.0`, `rendered_at`, `media_handle`, `duration` | `HebrewRenderer` | depends on renderer | public | rendering | ready |
| 9 | `stimulus_started` | `ev_s1_009` | `ev_s1_008` | `corr_render_001` | playback begins | `trial_id`, `stimulus_request_id`, `rendered_stimulus_id`, `started_at` | `HebrewRenderer` | no | public | ready | playing |
| 10 | `stimulus_completed` | `ev_s1_010` | `ev_s1_009` | `corr_render_001` | playback ends | `trial_id`, `stimulus_request_id`, `completed_at`, `duration_observed` | `HebrewRenderer` | no | public | playing | awaiting response |
| 11 | `response_window_opened` | `ev_s1_011` | `ev_s1_010` | `corr_trial_001` | `ResponseWindow` `rw_001` | `response_window_id`, `trial_id`, `response_modes_accepted: [typed]`, `opened_at`, `deadline_at`, `timeout_policy: hard_deadline` | runtime | deterministic | public | awaiting response | listening |
| 12 | `observation_received` | `ev_s1_012` | `ev_s1_011` | `corr_resp_001` | `Observation` `obs_typed_001` | `observation_id`, `response_window_id`, `provider_id: keyboard_v1`, `provider_version: 1.0.0`, `observation_type: typed_input`, `payload: "ללמוד"`, `received_at`, `quality_dimensions`, `quality_flags`, `quality_model_id: typed_quality_v1`, `quality_model_version: 1.0.1` | `KeyboardObservationProvider` | no (input captured) | consent_gated | listening | captured |
| 13 | `captured_response_created` | `ev_s1_013` | `ev_s1_012` | `corr_resp_001` | `CapturedResponse` `cr_001` | `captured_response_id`, `response_window_id`, `observation_ids: [obs_typed_001]`, `response_mode: typed`, `captured_payload: "ללמוד"`, `captured_at`, `device_provenance: {keyboard_id: kb_001}`, `quality_flags: []` | runtime | deterministic | consent_gated | captured | interpreted |
| 14 | `response_interpreted` | `ev_s1_014` | `ev_s1_013` | `corr_resp_001` | `ResponseInterpretation` `ri_001` | `response_interpretation_id`, `response_window_id: rw_001`, `captured_response_id`, `interpreter_id: typed_text_v1`, `interpreter_version: 1.0.0`, `interpreted_payload: "ללמוד"`, `interpretation_type: typed_text`, `interpretation_confidence: 0.99` | `ResponseInterpreter` | deterministic (typed) | consent_gated | interpreted | normalized |
| 15 | `domain_response_normalized` | `ev_s1_015` | `ev_s1_014` | `corr_resp_001` | `DomainNormalizedResponse` `dnr_001` | `domain_normalized_response_id`, `response_window_id: rw_001`, `response_interpretation_id`, `normalizer_id: hebrew_norm_v1`, `normalizer_version: 1.0.0`, `response_mode: typed`, `normalized_payload: "ללמוד"`, `extracted_at`, `uncertainty: 0.01` | `HebrewDomainNormalizer` | deterministic | consent_gated | normalized | evaluated |
| 16 | `evaluation_completed` | `ev_s1_016` | `ev_s1_015` | `corr_eval_001` | `Evaluation` `eval_001` | `evaluation_id`, `trial_id`, `evaluator_id: hebrew_eval_v1`, `evaluator_version: 1.0.1`, `domain_normalized_response_id`, `expected_content_item_id: ci_hebrew_lilmod`, `answer_status: correct`, `evaluation_status: completed`, `correctness_credit: 1.0`, `accepted_variant_id: av_lilmod_full`, `evidence_group: eran_tomer_derivative`, `scope_status: verified_consensus`, `confidence: 0.99` | `HebrewEvaluator` | deterministic | public | evaluated | feedback |
| 17 | `evidence_record_created` | `ev_s1_017` | `ev_s1_016` | `corr_eval_001` | `EvidenceRecord` `er_001` | `evidence_record_id`, `decision_or_evaluation_id: eval_001`, `source_event_ids: [ev_s1_015, ev_s1_016]`, `evidence_type: domain_evaluation`, `summary` | runtime / `HebrewEvaluator` | deterministic | public | feedback | feedback |
| 18 | `feedback_started` | `ev_s1_018` | `ev_s1_016` | `corr_trial_001` | `FeedbackEvent` `fb_001` | `feedback_event_id`, `trial_id`, `evaluation_id: eval_001`, `feedback_category: KNOWLEDGE`, `feedback_type: correct_answer`, `content_item_id: ci_knowledge_lilmod`, `started_at` | runtime | deterministic | public | feedback | feedback playing |
| 19 | `feedback_completed` | `ev_s1_019` | `ev_s1_018` | `corr_trial_001` | feedback ends | `feedback_event_id`, `completed_at`, `duration_observed` | `HebrewRenderer` | no | public | playing | scheduling |
| 20 | `schedule_decision` | `ev_s1_020` | `ev_s1_019` | `corr_sched_002` | `ScheduleDecision` `sd_002` | `schedule_decision_id`, `session_id`, `source_event_ids: [ev_s1_019]`, `selected_item_ids: []`, `decision_type: session_end`, `decision_status: made` | `Scheduler` | deterministic | public | scheduling | terminal planned |
| 21 | `block_completed` | `ev_s1_021` | `ev_s1_020` | `corr_block_001` | `BlockExecution` complete | `session_id`, `block_id`, `completed_trial_count: 1` | runtime | deterministic | public | in_progress | completed |
| 22 | `session_completed` | `ev_s1_022` | `ev_s1_021` | `corr_sess_001` | session terminal | `session_id`, `completed_at`, `final_trial_index: 1` | runtime | deterministic | public | in_progress | completed |

## 4. Provider-call ledger

| Provider | Operation | Input object / identifier | Output object / identifier | Timeout | Retry | Error mapping | Side effects | Deterministic | Exact output must be captured for replay |
|---|---|---|---|---|---|---|---|---|---|
| `HebrewDomainProvider` | `get_item(ci_italian_imparare)` | `ci_italian_imparare` | `ContentItem` `ci_italian_imparare` | 2s | 2 | `provider_not_found` -> `protocol_terminated` | none | yes (fixture-backed) | no |
| `HebrewDomainProvider` | `get_expected_answer(trial_context)` | cue `ci_italian_imparare`, target `past_first_mf_singular` or `infinitive` | `ContentItem` `ci_hebrew_lilmod` with `accepted_variants` | 2s | 2 | `out_of_scope` -> `evaluation_abstained` | none | yes | no |
| `HebrewDomainProvider` | `get_prompt(item_id, mode)` | `ci_knowledge_lilmod`, `mode: hear` | `{prompt_text, prompt_content_item_id, prosody_hint}` | 2s | 2 | `content_unsupported` -> `renderer_fallback` | none | yes | no |
| `HebrewRenderer` | `render(sr_cue_001)` | `StimulusRequest` `sr_cue_001` | `RenderedStimulus` `rs_cue_001` | 5s+duration | 1 | `render_failed` -> `renderer_fallback` event; `voice_unavailable` -> default voice | may cache media | no (latency varies) | yes (duration/handle) |
| `KeyboardObservationProvider` | `start_listening(rw_001)` | `ResponseWindow` `rw_001` | ack | 1s | 0 | `unsupported_response_mode` -> `response_timeout` | begins capture | n/a | n/a |
| `KeyboardObservationProvider` | `poll()` | — | `Observation` `obs_typed_001` | 100ms | continuous | `device_error` -> `signal_quality_changed` / `safety_rule_triggered` | returns buffer | no | yes (typed payload) |
| `KeyboardObservationProvider` | `stop_listening(rw_001)` | `rw_001` | ack | 1s | 0 | — | stops capture | n/a | n/a |
| `ResponseInterpreter` (typed) | `interpret(cr_001)` | `CapturedResponse` `cr_001` | `ResponseInterpretation` `ri_001` | 2s | 0 | `interpretation_failed` -> `response_interpreted` with low confidence + `evaluation_abstained` | none | yes (typed) | no |
| `HebrewDomainNormalizer` | `normalize(ri_001)` | `ResponseInterpretation` `ri_001` | `DomainNormalizedResponse` `dnr_001` | 1s | 0 | `normalization_failed` / `out_of_scope` -> `domain_response_normalized` with high uncertainty + `evaluation_abstained`/`evaluation_failed` | none | yes | no |
| `HebrewEvaluator` | `evaluate(dnr_001, ci_hebrew_lilmod, trial_context)` | `DomainNormalizedResponse` `dnr_001`, `ContentItem` `ci_hebrew_lilmod` | `Evaluation` `eval_001` | 2s | 0 | `evaluation_failed` -> `evaluation_failed` event; `abstained` -> `evaluation_abstained`; `out_of_scope` -> `evaluation_abstained` | none | yes (for deterministic engine) | yes |
| `Scheduler` | `select_next(scheduling_context)` | context with session history | `ScheduleDecision` `sd_001`, `sd_002` | 500ms | 0 | `scheduling_failed` -> `protocol_terminated` | none | yes (fixed seed) | no |

## 5. State-machine trace

### Session

| Transition | Entry condition | Exit condition | Generated events |
|---|---|---|---|
| `created` -> `started` | `session_created` appended; fixture validated; learner confirms | `session_started` appended; clock begins | `session_created`, `session_started` |
| `started` -> `completed` | Protocol reaches terminal state (`schedule_decision` with `decision_type: session_end`) | `session_completed` appended | `session_completed` |

### Block

| Transition | Entry condition | Exit condition | Generated events |
|---|---|---|---|
| `not_started` -> `in_progress` | `session_started`; first block selected | `block_started` appended | `block_started` |
| `in_progress` -> `completed` | All trials in block completed; exit condition satisfied | `block_completed` appended | `block_completed` |

### Trial

| Transition | Entry condition | Exit condition | Generated events |
|---|---|---|---|
| `planned` -> `started` | `trial_created` appended | `response_window_opened` (or `response_requirement: none`) | `trial_created`, `instruction_started`, `stimulus_*`, `response_window_opened` |
| `started` -> `awaiting_response` | `response_window_opened` | Provider begins listening | `response_window_opened` |
| `awaiting_response` -> `evaluated` | Observation captured, interpreted, normalized, evaluated | `evaluation_completed` appended | `observation_received`, `captured_response_created`, `response_interpreted`, `domain_response_normalized`, `evaluation_completed` |
| `evaluated` -> complete | `feedback_completed` and `schedule_decision` appended | `schedule_decision` appended | `feedback_started`, `feedback_completed`, `schedule_decision` |

### Response

| Transition | Entry condition | Exit condition | Generated events |
|---|---|---|---|
| `window_closed` -> `listening` | `response_window_opened` | Provider starts listening | `response_window_opened` |
| `listening` -> `captured` | Typed keystrokes finalized | `captured_response_created` appended | `observation_received`, `response_completed` (optional), `captured_response_created` |
| `captured` -> `interpreted` | `ResponseInterpreter` processes | `response_interpreted` appended | `response_interpreted` |
| `interpreted` -> `normalized` | `HebrewDomainNormalizer` processes | `domain_response_normalized` appended | `domain_response_normalized` |
| `normalized` -> `evaluated` | `HebrewEvaluator` returns | `evaluation_completed` appended | `evaluation_completed` |

### Safety

| Transition | Entry condition | Exit condition | Generated events |
|---|---|---|---|
| `idle` -> `active` | No safety rule triggered in this slice | — | none |
| `active` -> `paused` | N/A in success path | N/A | N/A |
| `active` -> `terminated` | N/A in success path | N/A | N/A |

### Adaptation

- Phase 5A+ only. In this slice `AdaptationDecision` is never created; state remains inactive. `decision` would be `NO_CHANGE_INSUFFICIENT_EVIDENCE` if a policy existed, but no `adaptation_*` event is emitted.

## 6. Persistence and reconstruction trace

| Object / event | persistent | derived | cached | ephemeral | stream-only | Reconstruction source | Snapshot eligibility |
|---|---|---|---|---|---|---|---|
| `Program` / `ProgramVersion` | X | | X | | | Fixture / registry | yes (capability cache) |
| `Protocol` / `ProtocolVersion` | X | | X | | | Fixture / registry | yes |
| `TaskDefinition` | X | | | | | Fixture | yes |
| `ContentItem` | X | | X | | | `HebrewDomainProvider` or fixture | yes |
| `Session` | | X | X | | X | `session_created` through terminal event | yes |
| `BlockExecution` | | X | X | | X | `block_started` / `block_completed` | yes |
| `Trial` | | X | X | | X | `trial_created` + trial events | yes |
| `StimulusRequest` | | | | | X | `stimulus_requested` | no |
| `RenderedStimulus` | X | | | | X | `stimulus_ready` + media store | yes (media cache) |
| `Instruction` | | X | X | | X | `instruction_started` / `instruction_completed` | yes |
| `ResponseWindow` | | | | | X | `response_window_opened` / `response_timeout` | no |
| `Observation` | X | | | | X | `observation_received` | no |
| `CapturedResponse` | X | | | | X | `captured_response_created` | no |
| `ResponseInterpretation` | X | | | | X | `response_interpreted` | no |
| `DomainNormalizedResponse` | X | | | | X | `domain_response_normalized` | no |
| `Evaluation` | X | | | | X | `evaluation_completed` | no |
| `FeedbackEvent` | X | | | | X | `feedback_started` / `feedback_completed` | yes |
| `ScheduleDecision` | X | | | | X | `schedule_decision` | no |
| `EvidenceRecord` | X | | | | X | `evidence_record_created` | no |
| `Outcome` | | X | X | | | all session events | yes (computed after terminal) |
| `Event` | X | | | | | event store | n/a |

### Replay procedure

1. Load `ProtocolVersion` `prv_hebrew_recall_v1` and `ProgramVersion` `pv_hebrew_vocab_v1` by reference.
2. Read all events for `sess_vocab_001` in `session_sequence_number` order.
3. Apply `session_created` -> `session_started` to initialize session state and clock.
4. Apply `block_started` -> `schedule_decision` -> `trial_created` to instantiate trial plan.
5. Apply instruction/stimulus events; replay may re-render or use captured `RenderedStimulus` if exact replay is required.
6. Apply `response_window_opened` -> `observation_received` -> `captured_response_created` -> `response_interpreted` -> `domain_response_normalized` -> `evaluation_completed`.
7. Apply `feedback_started` -> `feedback_completed`.
8. Apply `schedule_decision` with `session_end`.
9. Apply `block_completed` -> `session_completed`.
10. Recompute `Outcome` from the event stream.

The terminal state is fully reconstructable because every object is either an event or derived from events.

## 7. Validation checklist

| Rule category | Check | Result |
|---|---|---|
| Identifiers | All `*_id` fields use canonical names from `MPE_CANONICAL_IDENTIFIER_REGISTRY.md`. | Pass |
| Identifiers | `session_sequence_number` monotonic per `session_id`. | Pass (1–22) |
| Enums | `response_requirement`, `answer_status`, `evaluation_status`, `feedback_category`, `feedback_type`, `observation_type`, `interpretation_type`, `response_mode`, `block_type`, `decision_type`, `data_classification` all valid. | Pass |
| Foreign references | `provenance` entries reference prior events in same session. | Pass |
| Foreign references | `evaluation_completed.domain_normalized_response_id` references `dnr_001`. | Pass |
| Version compatibility | `ProtocolVersion.dependency_versions` matches `HebrewRenderer`, `HebrewEvaluator`, `HebrewDomainNormalizer` versions. | Pass (assumed) |
| Provider compatibility | `ResponseWindow.response_modes_accepted` subset of provider capabilities; `CapturedResponse.response_mode` in accepted list. | Pass (typed) |
| Provider compatibility | `HebrewEvaluator` input is `DomainNormalizedResponse`, not raw interpretation. | Pass |
| Checksums | `ProgramVersion.checksum` and `ProtocolVersion.checksum` validate. | Pass (fixture) |
| Event ordering | `captured_response_created` after `observation_received`; `response_interpreted` after `captured_response_created`; `domain_response_normalized` after `response_interpreted`; `evaluation_completed` after `domain_response_normalized`. | Pass |
| Response requirement | `trial_vocab_001.response_requirement = required`; `ResponseWindow` opened; `CapturedResponse` created. | Pass |
| Payload completeness | Every event payload contains required fields per `MPE_EVENT_MODEL_V1_1.md`. | Pass |
| Data classification | `observation_received`, `captured_response_created`, `response_interpreted`, `domain_response_normalized` flagged `consent_gated`; `evaluation_completed` and later `public`. | Pass |
| Lifecycle legality | `session` transitions `created -> started -> completed`; `trial` reaches `evaluated` and schedule emits `session_end`. | Pass |

## 8. Failure and recovery branches

| Triggering condition | Error classification | Event emitted | Retry / fallback | User-visible effect | State-machine transition | Terminal / recoverable |
|---|---|---|---|---|---|---|
| Learner types exact canonical `ללמוד` | success | `evaluation_completed` (`answer_status: correct`, `correctness_credit: 1.0`) | none | correct-answer feedback | `evaluated` -> scheduling | recoverable |
| Learner types an accepted variant surface that normalizes to `ללמוד` | success | `evaluation_completed` (`answer_status: acceptable_variant`, `accepted_variant_id: av_...`, `correctness_credit: 1.0`) | none | confirmatory feedback | `evaluated` -> scheduling | recoverable |
| Learner types `למדתי` (wrong form) or `לכתוב` (wrong root) | success | `evaluation_completed` (`answer_status: incorrect`, `correctness_credit: 0.0`) | none | correct-answer feedback | `evaluated` -> scheduling | recoverable |
| Response window deadline reached with no input | timeout | `response_timeout` | none | skip or neutral prompt | `awaiting_response` -> `timeout` -> scheduling | recoverable |
| `ResponseInterpreter` returns `interpretation_confidence` below threshold | low confidence | `response_interpreted` (low confidence) + `evaluation_abstained` (`evaluation_status: abstained`) | 0 retries | neutral feedback; continue | `evaluated` (abstained) -> scheduling | recoverable |
| `HebrewEvaluator` cannot determine correctness (ambiguous input or missing form) | abstention | `evaluation_abstained` (`answer_status: unevaluable`, `evaluation_status: abstained`) | none | neutral feedback / re-prompt | `evaluated` (abstained) -> scheduling | recoverable |
| Input outside 100-verb subset or unsupported form | out-of-scope | `evaluation_abstained` or `evaluation_failed` (`evaluation_status: out_of_scope`) | none | skip or neutral prompt | `evaluated` (out_of_scope) -> scheduling | recoverable |
| `HebrewEvaluator` engine exception or version mismatch | provider failure | `evaluation_failed` (`evaluation_status: failed`, `error_category: engine_error` or `version_mismatch`) | 0 retries | neutral feedback; log; possibly terminate | `evaluated` (failed) -> scheduling or safety | recoverable if isolated; terminal if systemic |
| `Renderer` fails to produce cue audio | provider failure | `renderer_fallback` + `stimulus_ready` with fallback | 1 retry with default voice | cue may be text-only | trial continues | recoverable |

## 9. Architecture stress findings

| Check | Finding | Severity |
|---|---|---|
| Missing object | None. All required objects (`Session`, `BlockExecution`, `Trial`, `ResponseWindow`, `Observation`, `CapturedResponse`, `ResponseInterpretation`, `DomainNormalizedResponse`, `Evaluation`, `FeedbackEvent`, `ScheduleDecision`, `EvidenceRecord`, `Outcome`) can be instantiated. | — |
| Missing event | None. All required events exist in `MPE_EVENT_MODEL_V1_1.md`. | — |
| Undefined identifier | None. All identifiers are in `MPE_CANONICAL_IDENTIFIER_REGISTRY.md`. | — |
| Ambiguous enum | None. All enums used are canonical. | — |
| Illegal state transition | None. Transitions follow `MPE_CANONICAL_ENUM_REGISTRY.md` `session_status` transitions and `RUNTIME_STATE_MACHINE.md`. | — |
| Provider-boundary violation | None. `Renderer` does not evaluate; `Evaluator` does not normalize; `Normalizer` does not interpret. | — |
| Replay gap | None. Every object has an event or derivation. `ResponseInterpretation` and `DomainNormalizedResponse` events exist. | — |
| Persistence ambiguity | None. `PERSISTENCE_BOUNDARIES.md` classification is consistent. | — |
| Safety ambiguity | None. Safety is not triggered in success path; safety transitions are defined and override flow. | — |
| Hebrew authority leakage | None. MPE core never computes Hebrew correctness; it delegates to `HebrewEvaluator`. | — |
| Hidden implementation decision | None. All decisions are explicit in object model, event model, or provider contracts. | — |

**Conclusion for this slice:** The approved architecture supports Hebrew vocabulary recall end-to-end without modification.
