# Phase 4A.5 Walkthrough — Exposure-Only Learning

## 1. Scenario definition

- **Learner objective:** Encode the association between the Hebrew infinitive `ללמוד` and its Italian meaning `imparare` through auditory/visual exposure.
- **Protocol purpose:** `acquisition`.
- **Exact task:** The learner is presented with `ללמוד` followed by `imparare` and a brief wait. No observable response is required.
- **Concrete content items:**
  - `ci_hebrew_lilmod` (`surface_vocalized: לִלְמוֹד`, `surface_plain: ללמוד`, `content_type: verb_form`, provider `hebrew`).
  - `ci_italian_imparare` (`surface: imparare`, `content_type: word`, provider `multilingual_cue`).
  - `ci_knowledge_lilmod_means` (`surface: "ללמוד means imparare"`, `content_type: phrase`, provider `hebrew`).
- **Response requirement:** `none`.
- **Accepted response modes:** `[]` (empty).
- **Assumptions:**
  - `ProtocolVersion` `prv_exposure_v1` and `ProgramVersion` `pv_exposure_program_v1` are validated.
  - `TaskDefinition` `td_language_prediction_exposure_v1` uses `task_family: language_prediction_retrieval` with `response_requirement: none`.
- **Explicitly out-of-scope behavior:**
  - No `ResponseWindow`, `CapturedResponse`, `ResponseInterpretation`, `DomainNormalizedResponse`, or `Evaluation` in the success path.
  - No covert mental activity is recorded as an `Observation`.
  - No correctness feedback (only knowledge feedback).
  - No EEG/adaptation.

## 2. Object instantiation ledger

| Object type | Canonical identifier | Creation point | Immutable fields | Mutable derived state | Persistence class | Owning component | Source specification section |
|---|---|---|---|---|---|---|---|
| `Program` | `prog_exposure_program` | Fixture | `program_id`, `name`, `transfer_claim_level: trained_task_performance` | — | persistent | author/registry | `MPE_OBJECT_MODEL_V1_1.md` §Program |
| `ProgramVersion` | `pv_exposure_program_v1` | Fixture | `program_version_id`, `program_id`, `protocol_version_sequence`, `checksum` | — | persistent | author/registry | `MPE_OBJECT_MODEL_V1_1.md` §ProgramVersion |
| `Protocol` | `proto_exposure` | Fixture | `protocol_id`, `name`, `purpose: acquisition` | — | persistent | author/registry | `MPE_OBJECT_MODEL_V1_1.md` §Protocol |
| `ProtocolVersion` | `prv_exposure_v1` | Fixture | `protocol_version_id`, `protocol_id`, `trial_sequence`, `required_providers`, `checksum` | — | persistent | author/registry | `MPE_OBJECT_MODEL_V1_1.md` §ProtocolVersion |
| `TaskDefinition` | `td_language_prediction_exposure_v1` | Fixture | `task_definition_id`, `task_family: language_prediction_retrieval`, `trial_role_sequence` | — | persistent | author/registry | `MPE_OBJECT_MODEL_V1_1.md` §TaskDefinition |
| `ContentItem` Hebrew | `ci_hebrew_lilmod` | `HebrewDomainProvider` fixture | `content_item_id`, `provider_id`, `surface_form`, `normalized_form`, `status` | `abstention_status` | persistent / cached | `HebrewDomainProvider` | `MPE_OBJECT_MODEL_V1_1.md` §ContentItem |
| `ContentItem` Italian | `ci_italian_imparare` | cue fixture | `content_item_id`, `provider_id`, `surface_form` | — | persistent / cached | `DomainProvider` | `MPE_OBJECT_MODEL_V1_1.md` §ContentItem |
| `ContentItem` feedback | `ci_knowledge_lilmod_means` | feedback fixture | `content_item_id`, `provider_id`, `surface_form` | — | persistent / cached | `HebrewDomainProvider` | `MPE_OBJECT_MODEL_V1_1.md` §ContentItem |
| `Session` | `sess_exp_001` | `session_created` | `session_id`, `program_version_id`, `protocol_version_id`, `learner_id` | `status` | derived / stream-only | runtime | `MPE_OBJECT_MODEL_V1_1.md` §Session |
| `BlockExecution` | `block_exp_001` | `block_started` | `block_id`, `session_id`, `block_type: practice` | `completed_at`, `completed_trial_count` | derived / stream-only | runtime | `MPE_OBJECT_MODEL_V1_1.md` §Block |
| `Trial` | `trial_exp_001` | `trial_created` | `trial_id`, `session_id`, `task_definition_id: td_language_prediction_exposure_v1`, `content_item_ids: [ci_hebrew_lilmod, ci_italian_imparare, ci_knowledge_lilmod_means]`, `response_requirement: none`, `accepted_response_modes: []` | `status` | derived / stream-only | runtime | `MPE_OBJECT_MODEL_V1_1.md` §Trial |
| `StimulusRequest` | `sr_hebrew_001`, `sr_italian_001`, `sr_feedback_001` | `stimulus_requested` events | `stimulus_request_id`, `trial_id`, `content_item_id`, `renderer_id` | — | stream-only | runtime | `MPE_OBJECT_MODEL_V1_1.md` §StimulusRequest |
| `RenderedStimulus` | `rs_hebrew_001`, `rs_italian_001`, `rs_feedback_001` | `stimulus_ready` events | `rendered_stimulus_id`, `stimulus_request_id`, `media_handle`, `duration` | — | persistent / stream-only | `HebrewRenderer` | `MPE_OBJECT_MODEL_V1_1.md` §RenderedStimulus |
| `Instruction` | `instr_covert_001` | `instruction_started` | `instruction_id`, `trial_id`, `instruction_type: INSTRUCT_COVERT_RETRIEVAL`, `instruction_payload`, `observable_response_expected: false` | `completed_at` | derived / stream-only | runtime | `MPE_OBJECT_MODEL_V1_1.md` §Instruction |
| `FeedbackEvent` | `fb_exp_001` | `feedback_started` | `feedback_event_id`, `trial_id`, `feedback_category: KNOWLEDGE`, `feedback_type: elaboration`, `content_item_id: ci_knowledge_lilmod_means` | `completed_at` | persistent / stream-only | runtime | `MPE_OBJECT_MODEL_V1_1.md` §FeedbackEvent |
| `ScheduleDecision` | `sd_exp_001`, `sd_exp_002` | `schedule_decision` events | `schedule_decision_id`, `session_id`, `selected_item_ids`, `decision_type`, `decision_status`, `source_event_ids` | — | persistent / stream-only | `Scheduler` | `MPE_OBJECT_MODEL_V1_1.md` §ScheduleDecision |
| `Outcome` | `outcome_exp_001` | computed after terminal event | `session_id`, `computation_version` | exposure count, dropout, early_termination, protocol_adherence | derived | runtime | `MPE_OBJECT_MODEL_V1_1.md` §Outcome |

## 3. Event-by-event execution trace (successful completion with pause/resume)

| seq | event_type | event_id | causation_event_ids | correlation_id | object/fact introduced | canonical payload fields | owning component | replay classification | data_classification | state before | state after |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `session_created` | `ev_e1_001` | — | `corr_exp_001` | `Session` `sess_exp_001` | `session_id`, `program_version_id`, `protocol_version_id`, `learner_id` | runtime | deterministic | public | none | `created` |
| 2 | `session_started` | `ev_e1_002` | `ev_e1_001` | `corr_exp_001` | clock begins | `session_id`, `random_seed` | runtime | deterministic | public | `created` | `started` |
| 3 | `block_started` | `ev_e1_003` | `ev_e1_002` | `corr_block_e001` | `BlockExecution` `block_exp_001` | `session_id`, `block_id`, `block_type: practice` | runtime | deterministic | public | none | `in_progress` |
| 4 | `schedule_decision` | `ev_e1_004` | `ev_e1_002` | `corr_sched_e001` | `ScheduleDecision` `sd_exp_001` | `schedule_decision_id`, `session_id`, `source_event_ids: [ev_e1_002]`, `selected_item_ids: [ci_hebrew_lilmod, ci_italian_imparare, ci_knowledge_lilmod_means]`, `decision_type: next_trial`, `decision_status: made` | `Scheduler` | deterministic | public | — | trial planned |
| 5 | `trial_created` | `ev_e1_005` | `ev_e1_004` | `corr_trial_e001` | `Trial` `trial_exp_001` | `trial_id`, `session_id`, `block_id`, `task_definition_id`, `content_item_ids`, `response_requirement: none`, `accepted_response_modes: []` | runtime | deterministic | public | none | `planned` |
| 6 | `stimulus_requested` | `ev_e1_006` | `ev_e1_005` | `corr_render_e001` | `StimulusRequest` `sr_hebrew_001` | `stimulus_request_id`, `trial_id`, `content_item_id: ci_hebrew_lilmod`, `renderer_id: hebrew_tts`, `requested_at`, `scheduled_for` | runtime | deterministic | public | planned | rendering |
| 7 | `stimulus_ready` | `ev_e1_007` | `ev_e1_006` | `corr_render_e001` | `RenderedStimulus` `rs_hebrew_001` | `stimulus_request_id`, `rendered_stimulus_id`, `renderer_id`, `renderer_version: 1.2.0`, `rendered_at`, `media_handle`, `duration` | `HebrewRenderer` | depends | public | rendering | ready |
| 8 | `stimulus_started` | `ev_e1_008` | `ev_e1_007` | `corr_render_e001` | playback begins | `trial_id`, `stimulus_request_id`, `rendered_stimulus_id`, `started_at` | `HebrewRenderer` | no | public | ready | playing |
| 9 | `stimulus_completed` | `ev_e1_009` | `ev_e1_008` | `corr_render_e001` | playback ends | `trial_id`, `stimulus_request_id`, `completed_at` | `HebrewRenderer` | no | public | playing | next instruction |
| 10 | `instruction_started` | `ev_e1_010` | `ev_e1_009` | `corr_trial_e001` | `Instruction` `instr_covert_001` | `trial_id`, `instruction_id`, `instruction_type: INSTRUCT_COVERT_RETRIEVAL`, `instruction_payload: "Think of the Italian meaning"`, `target_operation: retrieve_italian_meaning`, `allotted_duration: 3.0`, `observable_response_expected: false` | runtime | deterministic | public | next instruction | covert retrieval active |
| 11 | `instruction_completed` | `ev_e1_011` | `ev_e1_010` | `corr_trial_e001` | instruction ends | `trial_id`, `instruction_id`, `completed_at`, `duration: 3.0` | runtime | deterministic | public | covert retrieval active | wait |
| 12 | `stimulus_requested` | `ev_e1_012` | `ev_e1_011` | `corr_render_e002` | `StimulusRequest` `sr_italian_001` | `stimulus_request_id`, `trial_id`, `content_item_id: ci_italian_imparare`, `renderer_id: hebrew_tts`, `requested_at`, `scheduled_for` | runtime | deterministic | public | wait | rendering |
| 13 | `stimulus_ready` | `ev_e1_013` | `ev_e1_012` | `corr_render_e002` | `RenderedStimulus` `rs_italian_001` | `stimulus_request_id`, `rendered_stimulus_id`, `renderer_id`, `renderer_version: 1.2.0`, `rendered_at`, `media_handle`, `duration` | `HebrewRenderer` | depends | public | rendering | ready |
| 14 | `stimulus_started` | `ev_e1_014` | `ev_e1_013` | `corr_render_e002` | playback begins | `trial_id`, `stimulus_request_id`, `started_at` | `HebrewRenderer` | no | public | ready | playing |
| 15 | `stimulus_completed` | `ev_e1_015` | `ev_e1_014` | `corr_render_e002` | playback ends | `trial_id`, `stimulus_request_id`, `completed_at` | `HebrewRenderer` | no | public | playing | feedback |
| 16 | `session_paused` | `ev_e1_016` | `ev_e1_015` | `corr_exp_001` | pause | `session_id`, `reason: user`, `paused_at`, `active_session_time_at_pause` | runtime | deterministic | public | feedback | `paused` |
| 17 | `session_resumed` | `ev_e1_017` | `ev_e1_016` | `corr_exp_001` | resume | `session_id`, `resumed_at`, `active_session_time_at_resume` | runtime | deterministic | public | `paused` | `resumed` |
| 18 | `feedback_started` | `ev_e1_018` | `ev_e1_017` | `corr_trial_e001` | `FeedbackEvent` `fb_exp_001` | `feedback_event_id`, `trial_id`, `feedback_category: KNOWLEDGE`, `feedback_type: elaboration`, `content_item_id: ci_knowledge_lilmod_means`, `started_at` | runtime | deterministic | public | resumed | feedback playing |
| 19 | `feedback_completed` | `ev_e1_019` | `ev_e1_018` | `corr_trial_e001` | feedback ends | `feedback_event_id`, `completed_at` | `HebrewRenderer` | no | public | feedback playing | scheduling |
| 20 | `schedule_decision` | `ev_e1_020` | `ev_e1_019` | `corr_sched_e002` | `ScheduleDecision` `sd_exp_002` | `schedule_decision_id`, `session_id`, `source_event_ids: [ev_e1_019]`, `selected_item_ids: []`, `decision_type: session_end`, `decision_status: made` | `Scheduler` | deterministic | public | scheduling | terminal planned |
| 21 | `block_completed` | `ev_e1_021` | `ev_e1_020` | `corr_block_e001` | block complete | `session_id`, `block_id`, `completed_trial_count: 1` | runtime | deterministic | public | in_progress | completed |
| 22 | `session_completed` | `ev_e1_022` | `ev_e1_021` | `corr_exp_001` | session terminal | `session_id`, `completed_at`, `final_trial_index: 1` | runtime | deterministic | public | in_progress | `completed` |

## 4. Provider-call ledger

| Provider | Operation | Input object / identifier | Output object / identifier | Timeout | Retry | Error mapping | Side effects | Deterministic | Exact output must be captured for replay |
|---|---|---|---|---|---|---|---|---|---|
| `HebrewDomainProvider` | `get_item(ci_hebrew_lilmod)` / `get_prompt(...)` | `ci_hebrew_lilmod` | `ContentItem` with `surface_form`, `normalized_form`, `pronunciation_metadata` | 2s | 2 | `out_of_scope` -> skip content | none | yes | no |
| `HebrewDomainProvider` | `get_item(ci_italian_imparare)` | `ci_italian_imparare` | `ContentItem` | 2s | 2 | `out_of_scope` -> skip content | none | yes | no |
| `HebrewRenderer` | `render(sr_hebrew_001)`, `render(sr_italian_001)`, `render(sr_feedback_001)` | `StimulusRequest` | `RenderedStimulus` | 5s+duration | 1 | `render_failed` -> `renderer_fallback` event; `voice_unavailable` -> default voice | may cache media | no | yes (duration/handle) |
| `Scheduler` | `select_next(context)` | session history (empty/no evaluations) | `ScheduleDecision` | 500ms | 0 | `scheduling_failed` -> `protocol_terminated` | none | yes | no |

`ObservationProvider`, `ResponseInterpreter`, `DomainNormalizer`, and `Evaluator` are **not called** in the exposure-only success path because `response_requirement == none` and no `ResponseWindow` is opened.

## 5. State-machine trace

### Session

| Transition | Entry condition | Exit condition | Generated events |
|---|---|---|---|
| `created` -> `started` | `session_created` validated | `session_started` | `session_created`, `session_started` |
| `started` -> `paused` | User pauses | `session_paused` | `session_paused` |
| `paused` -> `resumed` | User resumes | `session_resumed` | `session_resumed` |
| `resumed` -> `completed` | Protocol reaches terminal state | `session_completed` | `session_completed` |

### Block

| Transition | Entry condition | Exit condition | Generated events |
|---|---|---|---|
| `not_started` -> `in_progress` | session started | `block_started` | `block_started` |
| `in_progress` -> `completed` | trial and feedback completed | `block_completed` | `block_completed` |

### Trial

| Transition | Entry condition | Exit condition | Generated events |
|---|---|---|---|
| `planned` -> `started` | `trial_created` | `response_requirement == none`, so no `ResponseWindow` | `trial_created`, `stimulus_*`, `instruction_started/completed`, `feedback_*` |
| `started` -> complete | feedback completed and `schedule_decision` emitted | `schedule_decision` | `feedback_started`, `feedback_completed`, `schedule_decision` |

### Response

- Not instantiated because `response_requirement == none`.
- State remains `window_closed` / N/A.

### Safety

| Transition | Entry condition | Exit condition | Generated events |
|---|---|---|---|
| `idle` -> `active` | Safety rule triggered (e.g., environment check fails) | `safety_rule_triggered` | `safety_rule_triggered`, `safety_instruction_started`, `session_paused` or `protocol_terminated` |
| `active` -> `terminated` | Unrecoverable safety condition | `protocol_terminated` | `protocol_terminated` |

### Adaptation

- Inactive in Phase 4A. No `AdaptationDecision` created.

## 6. Persistence and reconstruction trace

| Object / event | persistent | derived | cached | ephemeral | stream-only | Reconstruction source | Snapshot eligibility |
|---|---|---|---|---|---|---|---|
| `Program`/`ProgramVersion`/`Protocol`/`ProtocolVersion`/`TaskDefinition` | X | | X | | | fixtures / registry | yes |
| `ContentItem` | X | | X | | | `HebrewDomainProvider` fixtures | yes |
| `Session` | | X | X | | X | session events | yes |
| `BlockExecution` | | X | X | | X | `block_started` / `block_completed` | yes |
| `Trial` | | X | X | | X | `trial_created` and trial events | yes |
| `StimulusRequest` | | | | | X | `stimulus_requested` | no |
| `RenderedStimulus` | X | | | | X | `stimulus_ready` + media store | yes |
| `Instruction` | | X | X | | X | `instruction_started` / `instruction_completed` | yes |
| `FeedbackEvent` | X | | | | X | `feedback_started` / `feedback_completed` | yes |
| `ScheduleDecision` | X | | | | X | `schedule_decision` | no |
| `Outcome` | | X | X | | | all session events; no response pipeline | yes |
| `Event` | X | | | | | event store | n/a |

### Replay procedure

1. Load `ProtocolVersion` `prv_exposure_v1` and `ProgramVersion` `pv_exposure_program_v1`.
2. Read events for `sess_exp_001` in canonical order.
3. Apply `session_created` and `session_started`.
4. Apply `block_started` and `schedule_decision` to plan trial.
5. Apply `trial_created`; note `response_requirement: none` means no `ResponseWindow` is expected.
6. Apply `stimulus_*` events, `instruction_started/completed`, `session_paused`/`session_resumed`, `feedback_*`.
7. Apply `schedule_decision` (`session_end`), `block_completed`, `session_completed`.
8. Recompute `Outcome` from events; `Outcome.accuracy` and `omission_rate` are not applicable, but `coverage` and `protocol_adherence` reflect completed exposures.

No `ResponseWindow`, `CapturedResponse`, `ResponseInterpretation`, `DomainNormalizedResponse`, or `Evaluation` events are required for replay.

## 7. Validation checklist

| Rule category | Check | Result |
|---|---|---|
| Identifiers | All `*_id` canonical. | Pass |
| Enums | `response_requirement: none`, `block_type: practice`, `feedback_category: KNOWLEDGE`, `decision_type: session_end`, `decision_status: made`, `session_status` transitions valid. | Pass |
| Foreign references | `content_item_ids` exist in fixtures; `stimulus_request` -> `rendered_stimulus` links valid. | Pass |
| Version compatibility | `ProtocolVersion` dependencies match renderer/provider versions. | Pass (assumed) |
| Provider compatibility | `HebrewRenderer` renders `StimulusRequest`; no `Evaluator` called because no response. | Pass |
| Checksums | Fixture checksums validate. | Pass |
| Event ordering | `session_paused` before `session_resumed`; `feedback_started` before `feedback_completed`; `stimulus_started` before `stimulus_completed`. | Pass |
| Response requirement | `trial_exp_001.response_requirement == none`; no `ResponseWindow` opened. | Pass |
| Payload completeness | `instruction_started` payload includes `allotted_duration`, `observable_response_expected: false`. | Pass |
| Data classification | Stimulus/feedback events `public`; no sensitive observation events. | Pass |
| Lifecycle legality | `created -> started -> paused -> resumed -> completed` legal. | Pass |

## 8. Failure and recovery branches

| Triggering condition | Error classification | Event emitted | Retry / fallback | User-visible effect | State-machine transition | Terminal / recoverable |
|---|---|---|---|---|---|---|
| `HebrewRenderer` fails to render `ci_hebrew_lilmod` within timeout | provider timeout / render failure | `renderer_fallback` + `stimulus_ready` with fallback media | 1 retry with default voice | cue may be presented as text or skipped | trial continues | recoverable |
| Learner pauses session | user action | `session_paused` | none | audio pauses | `started` -> `paused` | recoverable |
| Learner resumes session | user action | `session_resumed` | none | audio resumes | `paused` -> `resumed` | recoverable |
| Learner cancels session | user action | `session_cancelled` (reason `user`) | none | session ends | `started`/`paused`/`resumed` -> `cancelled` | terminal |
| Safety rule triggered (e.g., maximum duration exceeded) | safety | `safety_rule_triggered` + `safety_instruction_started` + `protocol_terminated` or `session_paused` | none | safety action executes | `started` -> `active` -> `terminated`/`paused` | terminal if terminate |
| Stimulus sequence completes and `schedule_decision` emits `session_end` | success | `session_completed` | none | session ends normally | `resumed` -> `completed` | terminal |

## 9. Architecture stress findings

| Check | Finding | Severity |
|---|---|---|
| Missing object | None. `Instruction` supports `INSTRUCT_COVERT_RETRIEVAL` with `observable_response_expected: false`. | — |
| Missing event | None. `response_requirement: none` means no response-pipeline events are required. | — |
| Undefined identifier | None. | — |
| Ambiguous enum | None. `response_requirement` values explicitly include `none`. | — |
| Illegal transition | None. `Session` transitions include `paused` and `resumed`. | — |
| Provider-boundary violation | None. `ObservationProvider` is not invoked because no `ResponseWindow` is opened. | — |
| Replay gap | None. `Outcome` can be computed from session, stimulus, instruction, and feedback events without response pipeline. | — |
| Persistence ambiguity | None. `CapturedResponse`/`ResponseInterpretation`/`DomainNormalizedResponse`/`Evaluation` are not created; `PERSISTENCE_BOUNDARIES.md` classifies them as persistent only when their creation events occur. | — |
| Safety ambiguity | None. Safety rules can trigger at any time and override flow. | — |
| Hebrew authority leakage | None. No evaluation of Hebrew occurs in exposure-only path. | — |
| Hidden implementation decision | None. The decision to skip `ResponseWindow` is explicit from `response_requirement: none` in `Trial`. | — |

**Conclusion for this slice:** The architecture supports exposure-only protocols without fabricating responses or evaluations.
