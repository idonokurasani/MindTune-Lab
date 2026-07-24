# Phase 4A.5 Vertical-Slice Comparison

## 1. Summary of slices

| Slice | Task family | Protocol purpose | Response requirement | Observable response | Key objects exercised | Key Hebrew engine feature |
|---|---|---|---|---|---|---|
| Hebrew vocabulary recall | `overt_recall` | `retrieval` | `required` | `typed` (also `voice` supported but not exercised) | Full response pipeline (`Observation`, `CapturedResponse`, `ResponseInterpretation`, `DomainNormalizedResponse`, `Evaluation`) | Hebrew infinitive canonicalization and variant acceptance |
| Hebrew morphology recognition | `perceptual_discrimination` | `assessment` | `required` | `typed` label | Full response pipeline plus `partially_correct` and `acceptable_variant` | Binyan label matching and partial credit |
| Exposure-only learning | `language_prediction_retrieval` | `acquisition` | `none` | none | No response pipeline; `Instruction` with `INSTRUCT_COVERT_RETRIEVAL`; `session_paused`/`session_resumed` | Content item retrieval and rendering only; no evaluation |

## 2. Object-instantiation matrix

| Object | Vocab recall | Morphology | Exposure | Notes |
|---|---|---|---|---|
| `Program` / `ProgramVersion` / `Protocol` / `ProtocolVersion` | X | X | X | Same lifecycle for all slices. |
| `TaskDefinition` | `td_overt_recall_v1` | `td_morphology_binyan_v1` | `td_language_prediction_exposure_v1` | Different `task_family`; each uses canonical `trial_role_sequence`. |
| `BlockExecution` | `block_assessment_001` (`assessment`) | `block_assess_001` (`assessment`) | `block_exp_001` (`practice`) | `block_type` chosen per protocol purpose. |
| `Trial` | `response_requirement: required` | `response_requirement: required` | `response_requirement: none` | Drives whether `ResponseWindow` is opened. |
| `StimulusRequest` / `RenderedStimulus` | cue `ci_italian_imparare` | form `ci_hifil_form_haavarti` | Hebrew + Italian + feedback | Renderer contract identical. |
| `Instruction` | `REQUEST_OVERT_RESPONSE` | `REQUEST_OVERT_RESPONSE` | `INSTRUCT_COVERT_RETRIEVAL` | Exposure uses `observable_response_expected: false`. |
| `ResponseWindow` | X | X | — | Not created when `response_requirement: none`. |
| `Observation` | X | X | — | Exposure does not fabricate observations. |
| `CapturedResponse` | X | X | — | |
| `ResponseInterpretation` | X | X | — | |
| `DomainNormalizedResponse` | X | X | — | |
| `Evaluation` | X | X | — | No correctness evaluation in exposure. |
| `EvidenceRecord` | X | X | — | |
| `FeedbackEvent` | `KNOWLEDGE` / `correct_answer` | `PERFORMANCE` / `correct_answer` | `KNOWLEDGE` / `elaboration` | Category/type reflect intent, not presence of evaluation. |
| `ScheduleDecision` | X | X | X | Required for every session; `decision_status` and `source_event_ids` always present. |
| `Outcome` | X | X | X | Computed from event stream; accuracy only where `Evaluation` exists. |

## 3. Event-pipeline comparison

| Event sequence | Vocab recall | Morphology | Exposure |
|---|---|---|---|
| `session_created` -> `session_started` | X | X | X |
| `block_started` | X | X | X |
| `schedule_decision` (`next_trial`) | X | X | X |
| `trial_created` | X | X | X |
| `stimulus_requested` -> `stimulus_ready` -> `stimulus_started` -> `stimulus_completed` | cue | form | Hebrew, then Italian |
| `instruction_started` -> `instruction_completed` | `REQUEST_OVERT_RESPONSE` | `REQUEST_OVERT_RESPONSE` | `INSTRUCT_COVERT_RETRIEVAL` |
| `response_window_opened` | X | X | — |
| `observation_received` | typed "ללמוד" | typed "HIF'IL" | — |
| `captured_response_created` | X | X | — |
| `response_interpreted` | X | X | — |
| `domain_response_normalized` | X | X | — |
| `evaluation_completed` / `abstained` / `failed` | X | X | — |
| `evidence_record_created` | X | X | — |
| `feedback_started` -> `feedback_completed` | X | X | elaboration |
| `session_paused` / `session_resumed` | — | — | X (illustrative) |
| `schedule_decision` (`session_end`) | X | X | X |
| `block_completed` -> `session_completed` | X | X | X |

## 4. Provider-call comparison

| Provider | Vocab recall | Morphology | Exposure |
|---|---|---|---|
| `HebrewDomainProvider.get_item` / `get_expected_answer` | cue + expected answer | form + expected binyan label | Hebrew + Italian content |
| `HebrewRenderer` | cue render | form render | two stimulus renders + feedback |
| `KeyboardObservationProvider` | start/poll/stop | start/poll/stop | not called |
| `ResponseInterpreter` (typed) | typed text extraction | typed text extraction | not called |
| `HebrewDomainNormalizer` | Hebrew canonicalization | label normalization | not called |
| `HebrewEvaluator` | infinitive evaluation | binyan evaluation | not called |
| `Scheduler` | next trial / session end | next trial / session end | session end (no response history) |

## 5. State-machine differences

| State machine | Vocab recall | Morphology | Exposure |
|---|---|---|---|
| Session | `created` -> `started` -> `completed` | `created` -> `started` -> `completed` | `created` -> `started` -> `paused` -> `resumed` -> `completed` |
| Block | `in_progress` -> `completed` | `in_progress` -> `completed` | `in_progress` -> `completed` |
| Trial | `planned` -> `started` -> `evaluated` -> complete | `planned` -> `started` -> `evaluated` -> complete | `planned` -> `started` -> complete (no response) |
| Response | full pipeline | full pipeline | N/A |
| Safety | idle | idle | idle in success; branch covers activation |
| Adaptation | inactive | inactive | inactive |

## 6. Data-classification comparison

| Data-classification | Vocab recall | Morphology | Exposure |
|---|---|---|---|
| `public` | session, block, schedule, instruction, stimulus, feedback, evaluation | session, block, schedule, instruction, stimulus, feedback, evaluation | session, block, schedule, instruction, stimulus, feedback |
| `consent_gated` | observation, captured response, interpretation, normalized response | observation, captured response, interpretation, normalized response | none |

## 7. Branch coverage comparison

| Branch | Vocab recall | Morphology | Exposure |
|---|---|---|---|
| correct canonical | X | X | N/A |
| acceptable variant | X | X | N/A |
| partially correct | — | X | N/A |
| incorrect | X | X | N/A |
| timeout | X | X | N/A |
| low-confidence interpretation | X | X | N/A |
| Hebrew engine abstention | X | X | N/A |
| provider failure | X | X | X (renderer timeout, scheduling failure) |
| pause/resume | — | — | X |
| cancellation | — | — | X |
| safety interruption | — | — | X |

## 8. Architecture-unity analysis

The three slices demonstrate that the MPE v1.1 object and event model is unified by a small set of primitives and parameterized by `TaskDefinition` fields (`task_family`, `response_requirement`, `accepted_response_modes`) and `Instruction` fields (`instruction_type`, `observable_response_expected`).

- **Single pipeline, optional activation:** The `Observation` -> `CapturedResponse` -> `ResponseInterpretation` -> `DomainNormalizedResponse` -> `Evaluation` pipeline exists in all slices as a potential path but is only activated when `response_requirement != none` and a `ResponseWindow` is opened. Exposure shows the pipeline can be correctly omitted.
- **No hidden decisions:** Whether to open a response window, whether to create an `Evaluation`, and whether to classify feedback as `KNOWLEDGE` or `PERFORMANCE` are all explicit in the object/event payload.
- **Provider boundaries preserved:** The `HebrewRenderer` never evaluates; the `HebrewEvaluator` never renders; the `HebrewDomainNormalizer` never compares to expected answers. This holds across all three slices.
- **Replay consistency:** Every slice is reconstructible from the event stream because derived objects (`Session`, `Block`, `Trial`, `Outcome`) are rebuilt from immutable events.
- **Data-classification consistency:** Typed/observed inputs are always `consent_gated`; evaluative outcomes and scheduling decisions are `public`.

## 9. Cross-slice findings

| Finding | Severity | Slice(s) | Note |
|---|---|---|---|
| No missing object or event required by any slice | — | all | Architecture covers all three vertical slices. |
| `block_type` must be chosen from canonical enum; `acquisition` is not a valid `block_type` | Low | exposure | Corrected to `practice` in the walkthrough. |
| `ScheduleDecision` requires `decision_status` and `source_event_ids` | Low | all | Added to all slices. |
| `Instruction` requires `allotted_duration` or `open_until_response` in addition to `observable_response_expected` | Low | vocab, morphology | Added to both overt-response slices. |
| `StimulusRequest`, `RenderedStimulus`, `Observation`, `CapturedResponse`, `ResponseInterpretation`, `DomainNormalizedResponse`, and `Evaluation` each have required version/timestamp fields that must be present in event payloads | Low | all | Added to all relevant event rows. |

No architecture change is required; the corrections above are payload-completeness details within the existing specification.
