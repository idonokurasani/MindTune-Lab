# MPE Canonical Enum Registry v1.1 (corrected)

## Status

This registry captures every enum used across the MPE v1.1 documentation package after the blocking correction pass. Values in **bold** are the canonical forms intended for schema design. Mismatches identified in the first audit have been resolved.

## Registry

### session_status

- **Values:** `created`, `started`, `paused`, `resumed`, `completed`, `cancelled`, `terminated`
- **Owner:** `MPE_OBJECT_MODEL_V1_1.md` Session
- **Permitted transitions:**
  - `created` -> `started`
  - `started` -> `paused` | `completed` | `cancelled` | `terminated`
  - `paused` -> `resumed` | `cancelled` | `terminated`
  - `resumed` -> `paused` | `completed` | `cancelled` | `terminated`

### response_requirement

- **Values:** `required`, `optional`, `none`
- **Owner:** `MPE_OBJECT_MODEL_V1_1.md` Trial
- **Notes:** Consistent across `MPE_OBJECT_MODEL_V1_1.md` and `MPE_EVENT_MODEL_V1_1.md` `trial_created`.

### answer_status

- **Values:** `correct`, `incorrect`, `acceptable_variant`, `partially_correct`, `unevaluable`
- **Owner:** `MPE_OBJECT_MODEL_V1_1.md` Evaluation
- **Notes:** Consistent across object model, event model, provider boundaries, and Hebrew contract.

### evaluation_status

- **Values:** `completed`, `abstained`, `failed`, `out_of_scope`
- **Owner:** `MPE_OBJECT_MODEL_V1_1.md` Evaluation
- **Notes:** Consistent across object model, event model, provider boundaries, and Hebrew contract.

### deployment_status

- **Values:** `exploratory_only`, `shadow_mode`, `limited_runtime`, `production_approved`
- **Owner:** `MPE_OBJECT_MODEL_V1_1.md` StateEstimate, `MPE_ADAPTATION_CONTRACT.md` AdaptationDecision
- **Semantics:**
  - `exploratory_only` — offline analysis only; no runtime effect.
  - `shadow_mode` — may generate hypothetical decisions but must never change runtime behavior; `adaptation_applied` is prohibited.
  - `limited_runtime` — may apply changes only inside an approved, consented, logged experiment.
  - `production_approved` — may apply changes under normal protocol guardrails.

### adaptation_decision

- **Values:** `APPLY`, `NO_CHANGE_INSUFFICIENT_EVIDENCE`, `REVERSE`, `ABSTAIN`
- **Owner:** `MPE_OBJECT_MODEL_V1_1.md` AdaptationDecision

### transfer_claim_level

- **Values:** `trained_task_performance`, `item_generalization`, `near_transfer`, `far_transfer`, `clinical_outcome`
- **Owner:** `MPE_OBJECT_MODEL_V1_1.md` Program (`transfer_claim_level`), ProtocolVersion (`primary_transfer_claim`)
- **Notes:** Hyphenated form `trained-task-performance` was replaced by underscore form `trained_task_performance` across all documents.

### protocol_purpose

- **Values:** `assessment`, `acquisition`, `retrieval`, `consolidation`, `generalization`, `regulation`, `rehabilitation`, `mixed`
- **Owner:** `MPE_OBJECT_MODEL_V1_1.md` Program/Protocol/ProtocolVersion

### instruction_type

- **Values:** `PRESENT_STIMULUS`, `INSTRUCT_COVERT_RETRIEVAL`, `INSTRUCT_COVERT_REHEARSAL`, `INSTRUCT_IMAGERY`, `REQUEST_OVERT_RESPONSE`, `REQUEST_CONFIDENCE_RATING`, `REQUEST_SELF_REPORT`, `DELIVER_SAFETY_INSTRUCTION`
- **Owner:** `MPE_OBJECT_MODEL_V1_1.md` Instruction

### feedback_category

- **Values:** `KNOWLEDGE`, `PERFORMANCE`, `METACOGNITIVE`
- **Owner:** `MPE_OBJECT_MODEL_V1_1.md` FeedbackEvent

### feedback_type

- **Values:** `correct_answer`, `incorrect_indicator`, `elaboration`, `encouragement`, `confidence_prompt`, `strategy_suggestion`
- **Owner:** `MPE_OBJECT_MODEL_V1_1.md` FeedbackEvent

### observation_type

- **Values:** `button_press`, `voice_sample`, `typed_input`, `self_report`, `sensor_feature`, `microphone_status`, `signal_quality`
- **Owner:** `MPE_OBJECT_MODEL_V1_1.md` Observation

### interpretation_type

- **Values:** `asr_transcript`, `button_label`, `typed_text`, `selected_option`
- **Owner:** `MPE_OBJECT_MODEL_V1_1.md` ResponseInterpretation

### response_mode

- **Values:** `button`, `voice`, `typed`, `recognition`
- **Owner:** `MPE_OBJECT_MODEL_V1_1.md` ResponseWindow, CapturedResponse, DomainNormalizedResponse

### error_category

- **Values:** `tense`, `person`, `gender`, `number`, `spelling`, `binyan`, `out_of_scope`, `engine_error`, `version_mismatch`
- **Owner:** `MPE_OBJECT_MODEL_V1_1.md` Evaluation

### scope_status / content_item_status

- **Values:** `verified_consensus`, `high_confidence_candidate`, `unresolved`, `rejected`
- **Owner:** `MPE_OBJECT_MODEL_V1_1.md` Evaluation (`scope_status`), ContentItem (`status`)
- **Notes:** `ContentItem` now defines `status` and `abstention_status`.

### block_type

- **Values:** `warmup`, `practice`, `review`, `assessment`, `cooldown`, `recovery`, `safety`
- **Owner:** `MPE_OBJECT_MODEL_V1_1.md` Block

### safety_action_taken

- **Values:** `pause`, `terminate`, `volume_limit`, `offer_end`, `insert_recovery`
- **Owner:** `MPE_OBJECT_MODEL_V1_1.md` SafetyEvent

### severity

- **Values:** `info`, `warning`, `critical`
- **Owner:** `MPE_OBJECT_MODEL_V1_1.md` SafetyEvent

### decision_status

- **Values:** `made`, `abstained`
- **Owner:** `MPE_OBJECT_MODEL_V1_1.md` ScheduleDecision

### decision_type (ScheduleDecision)

- **Values:** `next_trial`, `next_block`, `session_end`, `insert_review`, `offer_break`
- **Owner:** `MPE_OBJECT_MODEL_V1_1.md` ScheduleDecision

### task_family

- **Values:** `language_prediction_retrieval`, `perceptual_discrimination`, `overt_recall`, `morphology_generation`, `working_memory_sequence`, `copying_exposure`, `metacognitive_prompt`, `safety_pause`, `item_exposure_no_response`
- **Owner:** `MPE_OBJECT_MODEL_V1_1.md` TaskDefinition

### quality_model

- **Fields:** `quality_dimensions` (dict), `quality_flags` (list), `quality_model_id`, `quality_model_version`, optional `overall_quality` (scalar)
- **Owner:** `MPE_OBJECT_MODEL_V1_1.md` Observation, `MPE_PROVIDER_BOUNDARIES.md` ObservationProvider
- **Notes:** Generic `quality_score` was replaced by the quality model across the object model, event model, and provider boundaries.

### data_classification

- **Values:** `public`, `consent_gated`, `sensitive_phi`, `research_sensitive`
- **Owner:** `MPE_EVENT_MODEL_V1_1.md` common event fields
- **Notes:** Added as a structured classification to complement the `sensitive` boolean. `sensitive_phi` events require encryption at rest and consent gating.

## Mismatches resolved

| Enum | Original conflict | Resolution |
|---|---|---|
| `response_requirement` vs `expected_response_mode` | `MPE_OBJECT_MODEL_V1_1.md` vs `MPE_EVENT_MODEL_V1_1.md` `trial_created` | `MPE_EVENT_MODEL_V1_1.md` updated to `response_requirement` and `accepted_response_modes`. |
| `answer_status` / `evaluation_status` vs `verdict` | `MPE_OBJECT_MODEL_V1_1.md` / `MPE_EVENT_MODEL_V1_1.md` vs `MPE_HEBREW_PROVIDER_CONTRACT.md` | `MPE_HEBREW_PROVIDER_CONTRACT.md` rewritten to use `answer_status`/`evaluation_status`. |
| `ContentItem.status` | `MPE_HEBREW_PROVIDER_CONTRACT.md` required it; `MPE_OBJECT_MODEL_V1_1.md` omitted it | Added `status` and `abstention_status` to `ContentItem`. |
| Quality model | `MPE_OBJECT_MODEL_V1_1.md` vs `MPE_EVENT_MODEL_V1_1.md` / `MPE_PROVIDER_BOUNDARIES.md` / `MPE_ADAPTATION_CONTRACT.md` | Replaced generic `quality_score` with `quality_dimensions`, `quality_flags`, `quality_model_id`, `quality_model_version`, optional `overall_quality`. |
| `transfer_claim_level` spelling | Review brief (underscore) vs `MPE_OBJECT_MODEL_V1_1.md` (hyphen) | Canonicalized to `trained_task_performance` (underscore) across all documents. |
