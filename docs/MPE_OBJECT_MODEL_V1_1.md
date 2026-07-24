# MPE Object Model v1.1

## Audit basis

This object model is revised from v1.0 using these audit files and sections:

- `COGNITIVE_PROTOCOL_ONTOLOGY.md` §Core entities (Program/ProgramVersion/Protocol/ProtocolVersion, Trial, Instruction, Evaluation, ScheduleDecision, AdaptationDecision, LatentEstimate, Safety, Outcome), §Response processing layers.
- `PROTOCOL_PRIMITIVES_CATALOG.md` §Allowed primitives, §Prohibited primitives, §Response requirement values.
- `SOURCE_CLAIM_AUDIT.md` / `.csv` claims 1, 4–13 (D, rejected), 14–28 (A, accepted).
- `DOMAIN_INDEPENDENCE_MAP.md` §What belongs in MPE core, §Provider contract table, §MPE core must not contain.
- `EXECUTIVE_SYNTHESIS.md` §What must change (points 1–10).
- `PROTOCOL_DECOMPOSITION_MATRIX.csv` — all task-family rows.
- `data/hebrew/phase3/PHASE_3_FINAL_REPORT.md` — Honest limitations and key metrics.

## Design principles

1. **Behavioral evidence is primary.** Every claim about the learner must be traceable to an observable event.
2. **Logical and executable identity are separated.** `Program` and `Protocol` are stable logical identities; `ProgramVersion` and `ProtocolVersion` are immutable executable definitions with checksums.
3. **Covert mental activity is not directly observable.** Instruction objects may request covert retrieval, rehearsal, or imagery, but they never store a covert answer, correctness, or semantic content.
4. **Cognitive states are estimates, not facts.** `StateEstimate` carries model version, uncertainty, validation status, and alternative explanations.
5. **Domain authority lives in providers.** MPE core never evaluates Hebrew correctness; it delegates to the Hebrew `Evaluator`.
6. **Response processing is layered.** `Observation` → `CapturedResponse` → `ResponseInterpretation` → `DomainNormalizedResponse` → `Evaluation`.
7. **Safety overrides everything.** Safety instructions are distinct from educational feedback.

## Core objects

### Program

- **Purpose:** A stable logical identity that groups protocols toward a learner goal.
- **Ownership:** Author / researcher / clinician.
- **Immutability:** Logical; no executable content.
- **Versioning:** `program_id`; versions are in `ProgramVersion`.
- **Required fields:**
  - `program_id`
  - `name`
  - `description`
  - `transfer_claim_level` (default: `trained_task_performance`)
- **Optional fields:**
  - `target_population`
  - `consent_category`
- **Prohibited responsibilities:**
  - Must not contain executable sequences, provider requirements, or safety configuration.
- **Relation to event stream:** A `session_created` event references a `ProgramVersion`, not a `Program`.
- **Traceability:** Correction to v1.0 5.1/5.3 conflation of identity and version; `COGNITIVE_PROTOCOL_ONTOLOGY.md` Program/ProgramVersion.

### ProgramVersion

- **Purpose:** An immutable executable definition of a `Program`.
- **Ownership:** Author / registry.
- **Immutability:** Immutable after creation.
- **Versioning:** `program_version_id`, `program_id` + `version` + `checksum`.
- **Required fields:**
  - `program_version_id`
  - `program_id`
  - `version`
  - `checksum`
  - `protocol_version_sequence`
  - `safety_profile_id`
  - `consent_requirements`
  - `schema_version`
  - `created_at`
  - `dependency_versions`
- **Optional fields:**
  - `schedule`
  - `learner_eligibility`
- **Prohibited responsibilities:**
  - Must not be mutated after release.
- **Relation to event stream:** `session_created` references `program_version_id`.
- **Traceability:** Correction 1; `COGNITIVE_PROTOCOL_ONTOLOGY.md`.

### Protocol

- **Purpose:** A stable logical identity for one session type.
- **Ownership:** Author / researcher.
- **Immutability:** Logical; no executable content.
- **Versioning:** `protocol_id`; versions are in `ProtocolVersion`.
- **Required fields:**
  - `protocol_id`
  - `name`
  - `description`
  - `protocol_family`
  - `purpose` (`assessment` | `acquisition` | `retrieval` | `consolidation` | `generalization` | `regulation` | `rehabilitation` | `mixed`)
- **Optional fields:**
  - `default_transfer_claim`
- **Prohibited responsibilities:**
  - Must not contain sequences, dependencies, schema version, provider requirements, or safety configuration.
- **Traceability:** Correction 1; `COGNITIVE_PROTOCOL_ONTOLOGY.md` Protocol/ProtocolVersion.

### ProtocolVersion

- **Purpose:** An immutable executable definition of a `Protocol`.
- **Ownership:** Author / registry.
- **Immutability:** Immutable after creation.
- **Versioning:** `protocol_version_id`, `protocol_id` + `version` + `checksum`.
- **Required fields:**
  - `protocol_version_id`
  - `protocol_id`
  - `version`
  - `checksum`
  - `objective`
  - `purpose`
  - `primary_transfer_claim` (default: `trained_task_performance`)
  - `block_sequence` or `trial_sequence`
  - `required_providers`
  - `safety_profile_id`
  - `schema_version`
  - `dependency_versions`
  - `created_at`
- **Optional fields:**
  - `estimated_duration`
  - `difficulty_dimensions` that may be adapted (Phase 5A+)
- **Prohibited responsibilities:**
  - Must not be mutated after release.
  - Must not contain EEG feature semantics.
- **Relation to event stream:** `session_created` and `session_started` reference `protocol_version_id`.
- **Traceability:** Correction 1 and 14 (transfer claims); `COGNITIVE_PROTOCOL_ONTOLOGY.md`.

### Session

- **Purpose:** One execution of a `ProgramVersion` and `ProtocolVersion` by a learner.
- **Ownership:** MPE runtime.
- **Immutability:** Session state is event-derived; events are immutable.
- **Versioning:** `session_id`, `program_version_id`, `protocol_version_id`, `created_at`.
- **Required fields:**
  - `session_id`
  - `program_version_id`
  - `protocol_version_id`
  - `learner_id`
  - `created_at`
  - `status` (`created` | `started` | `paused` | `resumed` | `completed` | `cancelled` | `terminated`)
- **Optional fields:**
  - `ended_at`
  - `outcome_summary` (computed, read-only)
- **Prohibited responsibilities:**
  - Must not contain mutable cognitive-state fields.
  - Must not evaluate responses.
- **Relation to event stream:** Query over event stream.
- **Traceability:** Correction 1; `COGNITIVE_PROTOCOL_ONTOLOGY.md` Session.

### Block

- **Purpose:** A named sub-sequence of trials within a session.
- **Ownership:** Protocol author.
- **Immutability:** Block definitions are part of the immutable `ProtocolVersion`.
- **Versioning:** `block_id` (defined inside `ProtocolVersion`).
- **Required fields:**
  - `block_id`
  - `block_type` (`warmup` | `practice` | `review` | `assessment` | `cooldown` | `recovery` | `safety`)
  - `trial_sequence` or `trial_generator_ref`
- **Optional fields:**
  - `max_trials`
  - `exit_condition` (observable, e.g., `N_TRIALS_COMPLETED`)
- **Prohibited responsibilities:**
  - Must not depend on EEG state.
  - Must not block waiting for a state estimate.
- **Relation to event stream:** `block_started`, `block_completed`.

### TaskDefinition

- **Purpose:** A reusable template describing a cognitive task pattern.
- **Ownership:** Protocol author.
- **Immutability:** Immutable.
- **Versioning:** `task_definition_id` + `version`.
- **Required fields:**
  - `task_definition_id`
  - `version`
  - `task_family` (`language_prediction_retrieval` | `perceptual_discrimination` | `overt_recall` | `morphology_generation` | `working_memory_sequence` | `copying_exposure` | `metacognitive_prompt` | `safety_pause` | `item_exposure_no_response`)
  - `trial_role_sequence` (ordered list of `TrialRole` names)
- **Optional fields:**
  - `example_protocol_ids`
- **Prohibited responsibilities:**
  - Must not contain runtime state.
- **Relation to event stream:** Referenced in `trial_created`.
- **Traceability:** Correction A (reclassify universal loop); `COGNITIVE_PROTOCOL_ONTOLOGY.md` TaskDefinition; `PROTOCOL_DECOMPOSITION_MATRIX.csv`.

### Trial

- **Purpose:** The atomic unit of a session: one complete cycle through trial roles.
- **Ownership:** Runtime generates from `ProtocolVersion` and `ScheduleDecision`.
- **Immutability:** Trial plan is immutable; runtime events record execution.
- **Versioning:** `trial_id`, `session_id`, `trial_index`, `task_definition_id`, `content_item_ids`.
- **Required fields:**
  - `trial_id`
  - `session_id`
  - `trial_index`
  - `task_definition_id`
  - `content_item_ids`
  - `response_requirement` (`required` | `optional` | `none`)
- **Optional fields:**
  - `accepted_response_modes` (list, e.g., `button`, `voice`, `typed`, `recognition`)
  - `scheduled_start_time`
  - `difficulty_dimensions` at trial start
- **Prohibited responsibilities:**
  - Must not store latency; latency is derived from events.
  - Must not store evaluation result.
  - Must not store covert response content.
- **Relation to event stream:** `trial_created`, plus instruction/stimulus/response/evaluation/feedback events.
- **Traceability:** Correction 2; `COGNITIVE_PROTOCOL_ONTOLOGY.md` Trial.

### TrialRole

- **Purpose:** A named stage within a trial.
- **Values:** `STIMULUS`, `COVERT_INSTRUCTION`, `OVERT_INSTRUCTION`, `RESPONSE_WINDOW`, `KNOWLEDGE_FEEDBACK`, `PERFORMANCE_FEEDBACK`, `METACOGNITIVE_PROMPT`, `SAFETY_INSTRUCTION`.
- **Traceability:** `PROTOCOL_PRIMITIVES_CATALOG.md` trial role sequence examples.

### ContentItem

- **Purpose:** A domain-neutral reference to learning material.
- **Ownership:** Domain provider.
- **Immutability:** Immutable.
- **Versioning:** `content_item_id`, `provider_id`, `provider_version`, `checksum`.
- **Required fields:**
  - `content_item_id`
  - `provider_id`
  - `provider_version`
  - `content_type`
  - `checksum`
- **Optional fields:**
  - `metadata` (opaque to MPE core; may contain Hebrew engine evidence)
  - `scope` (e.g., `phase3_100_verb_subset`)
  - `status` (`verified_consensus` | `high_confidence_candidate` | `unresolved` | `rejected`)
  - `abstention_status` (boolean; true when the domain provider deliberately declines to vouch for the item)
  - `confidence`
- **Prohibited responsibilities:**
  - Must not contain MPE runtime state.
  - MPE core must not interpret domain-specific fields.
- **Relation to event stream:** Referenced by `stimulus_requested`, `stimulus_ready`, `feedback_*`.

### StimulusRequest

- **Purpose:** A request to a `Renderer` to produce playable media.
- **Ownership:** Runtime.
- **Immutability:** Immutable.
- **Versioning:** `stimulus_request_id`, `trial_id`, `requested_at`.
- **Required fields:**
  - `stimulus_request_id`
  - `trial_id`
  - `content_item_id`
  - `renderer_id`
  - `requested_at`
  - `scheduled_for`
- **Optional fields:**
  - `rate`
  - `voice_id`
  - `prosody_hints`
  - `fallback_policy`
- **Prohibited responsibilities:**
  - Must not contain rendered audio data.
  - Must not evaluate correctness.

### RenderedStimulus

- **Purpose:** The output of a `Renderer`.
- **Ownership:** Renderer.
- **Immutability:** Immutable.
- **Versioning:** `rendered_stimulus_id`, `stimulus_request_id`, `renderer_version`.
- **Required fields:**
  - `rendered_stimulus_id`
  - `stimulus_request_id`
  - `renderer_id`
  - `renderer_version`
  - `media_handle`
  - `duration`
  - `rendered_at`
- **Optional fields:**
  - `format`
  - `provenance`
- **Prohibited responsibilities:**
  - Must not contain learner response data.

### Instruction

- **Purpose:** A cue delivered to the learner.
- **Ownership:** Protocol author; runtime executes.
- **Immutability:** Definition is immutable; execution events immutable.
- **Versioning:** `instruction_id`, `trial_id`, `instruction_type`.
- **Required fields:**
  - `instruction_id`
  - `trial_id`
  - `instruction_type` (`PRESENT_STIMULUS` | `INSTRUCT_COVERT_RETRIEVAL` | `INSTRUCT_COVERT_REHEARSAL` | `INSTRUCT_IMAGERY` | `REQUEST_OVERT_RESPONSE` | `REQUEST_CONFIDENCE_RATING` | `REQUEST_SELF_REPORT` | `DELIVER_SAFETY_INSTRUCTION`)
  - `instruction_payload` (text or media reference; never null)
  - `target_operation` (what the learner should do)
  - `allotted_duration` or `open_until_response`
  - `observable_response_expected` (boolean)
- **Optional fields:**
  - `voice_id`
  - `rate`
- **Prohibited responsibilities:**
  - Must not record correctness.
  - Must not record semantic content of covert operations.
  - Must not score mental activity directly.
  - `instruction_payload` must not be null for covert instructions.
- **Relation to event stream:** `instruction_started`, `instruction_completed`.
- **Traceability:** Correction 3; `COGNITIVE_PROTOCOL_ONTOLOGY.md` Instruction.

### ResponseWindow

- **Purpose:** The interval during which an observable response may be collected.
- **Ownership:** Runtime.
- **Immutability:** Immutable plan; execution events record timing.
- **Versioning:** `response_window_id`, `trial_id`, `opened_at`.
- **Required fields:**
  - `response_window_id`
  - `trial_id`
  - `response_modes_accepted`
  - `opened_at`
  - `deadline_at` (or `null`)
  - `timeout_policy`
- **Optional fields:**
  - `min_response_duration`
  - `max_response_duration`
- **Prohibited responsibilities:**
  - Must not interpret responses.
  - Must not block on EEG or state estimate.
- **Relation to event stream:** `response_window_opened`, `response_detected`, `response_completed`, `response_timeout`.

### Observation

- **Purpose:** A raw input from an `ObservationProvider`.
- **Ownership:** ObservationProvider.
- **Immutability:** Immutable.
- **Versioning:** `observation_id`, `provider_id`, `provider_version`, `received_at`.
- **Required fields:**
  - `observation_id`
  - `response_window_id` (if applicable)
  - `provider_id`
  - `provider_version`
  - `observation_type` (`button_press` | `voice_sample` | `typed_input` | `self_report` | `sensor_feature` | `microphone_status` | `signal_quality`)
  - `received_at`
  - `payload`
  - `quality_dimensions` (dict)
  - `quality_flags` (list)
  - `quality_model_id`
  - `quality_model_version`
- **Optional fields:**
  - `overall_quality` (scalar, optional)
  - `artifact_flags`
  - `device_id`
- **Prohibited responsibilities:**
  - Must not contain a correctness verdict.
  - Must not contain semantic interpretation.
- **Relation to event stream:** `observation_received`.
- **Traceability:** Correction 5; `COGNITIVE_PROTOCOL_ONTOLOGY.md` Observation.

### CapturedResponse

- **Purpose:** Technical capture of a learner response with device timestamps and provenance.
- **Ownership:** Runtime or observation adapter.
- **Immutability:** Immutable.
- **Versioning:** `captured_response_id`, `response_window_id`, `captured_at`.
- **Required fields:**
  - `captured_response_id`
  - `response_window_id`
  - `observation_ids`
  - `response_mode`
  - `captured_payload` (raw but captured, e.g., audio buffer, keystroke sequence)
  - `captured_at`
  - `device_provenance`
  - `quality_flags`
- **Prohibited responsibilities:**
  - Must not interpret content (ASR, button label mapping, text extraction).
- **Relation to event stream:** Created by `captured_response_created`; referenced by `response_interpreted`.
- **Traceability:** Correction 4; `COGNITIVE_PROTOCOL_ONTOLOGY.md` response layers.

### ResponseInterpretation

- **Purpose:** Domain-agnostic transformation of a `CapturedResponse` into an interpretable form (ASR, button label mapping, text extraction).
- **Ownership:** Response interpreter (provider-specific or generic).
- **Immutability:** Immutable.
- **Versioning:** `response_interpretation_id`, `response_window_id`, `interpreter_id`, `interpreter_version`.
- **Required fields:**
  - `response_interpretation_id`
  - `response_window_id`
  - `captured_response_id`
  - `interpreter_id`
  - `interpreter_version`
  - `interpreted_payload`
  - `interpretation_confidence`
  - `interpretation_type` (`asr_transcript` | `button_label` | `typed_text` | `selected_option`)
- **Prohibited responsibilities:**
  - Must not canonicalize to domain form.
  - Must not compare against expected answers.
- **Relation to event stream:** Created by `response_interpreted`; referenced by `domain_response_normalized`.
- **Traceability:** Correction 4; `COGNITIVE_PROTOCOL_ONTOLOGY.md`.

### DomainNormalizedResponse

- **Purpose:** Domain-specific canonicalization of an interpreted response.
- **Ownership:** Domain normalizer (e.g., Hebrew `DomainNormalizer`).
- **Immutability:** Immutable.
- **Versioning:** `domain_normalized_response_id`, `response_window_id`, `normalizer_id`, `normalizer_version`.
- **Required fields:**
  - `domain_normalized_response_id`
  - `response_window_id`
  - `response_interpretation_id`
  - `normalizer_id`
  - `normalizer_version`
  - `response_mode`
  - `normalized_payload`
  - `extracted_at`
  - `uncertainty`
- **Optional fields:**
  - `input_observation_ids`
- **Prohibited responsibilities:**
  - Must not compare against expected answers.
  - Speech-derived Hebrew output is not provider-agnostic; it must pass through this domain-specific normalizer.
- **Relation to event stream:** Created by `domain_response_normalized`; referenced by `evaluation_completed`, `evaluation_abstained`, `evaluation_failed`.
- **Traceability:** Correction 4; `COGNITIVE_PROTOCOL_ONTOLOGY.md`.

### Evaluation

- **Purpose:** The result of comparing a `DomainNormalizedResponse` against a domain-grounded expected answer.
- **Ownership:** `Evaluator` (e.g., Hebrew Evaluator).
- **Immutability:** Immutable.
- **Versioning:** `evaluation_id`, `trial_id`, `evaluator_id`, `evaluator_version`.
- **Required fields:**
  - `evaluation_id`
  - `trial_id`
  - `evaluator_id`
  - `evaluator_version`
  - `domain_normalized_response_id`
  - `expected_content_item_id`
  - `answer_status` (`correct` | `incorrect` | `acceptable_variant` | `partially_correct` | `unevaluable`)
  - `evaluation_status` (`completed` | `abstained` | `failed` | `out_of_scope`)
- **Optional fields:**
  - `correctness_credit` (0.0–1.0)
  - `accepted_variant_id`
  - `evidence_group` (from Hebrew engine)
  - `scope_status` (`verified_consensus` | `high_confidence_candidate` | `unresolved` | `rejected`)
  - `abstention_reason`
  - `failure_reason`
  - `error_category` (`tense` | `person` | `gender` | `number` | `spelling` | `binyan` | `out_of_scope` | `engine_error` | `version_mismatch`)
  - `evidence` (domain-specific)
  - `confidence` (evaluation confidence, not learner state)
- **Prohibited responsibilities:**
  - Must not compute latency.
  - Must not emit learner cognitive-state estimates.
- **Relation to event stream:** `evaluation_completed`, `evaluation_abstained`, or `evaluation_failed`.
- **Traceability:** Correction 6; `COGNITIVE_PROTOCOL_ONTOLOGY.md` Evaluation; `MPE_HEBREW_PROVIDER_CONTRACT.md`.

### FeedbackEvent (revised)

- **Purpose:** Delivery of feedback to the learner.
- **Ownership:** Runtime, using content from domain provider.
- **Immutability:** Immutable.
- **Versioning:** `feedback_event_id`, `trial_id`, `feedback_type`.
- **Required fields:**
  - `feedback_event_id`
  - `trial_id`
  - `feedback_category` (`KNOWLEDGE` | `PERFORMANCE` | `METACOGNITIVE`)
  - `feedback_type` (`correct_answer` | `incorrect_indicator` | `elaboration` | `encouragement` | `confidence_prompt` | `strategy_suggestion`)
  - `content_item_id` or `rendered_media_id`
  - `started_at`
- **Optional fields:**
  - `evaluation_id` (links feedback to a specific `Evaluation`)
  - `duration`
  - `prosody_hint`
- **Prohibited responsibilities:**
  - Must not evaluate.
  - Must not contain `safety_cue` (safety is a separate `SafetyInstruction`).
  - Must not make unvalidated cognitive-state claims.
- **Relation to event stream:** `feedback_started`, `feedback_completed`.
- **Traceability:** Correction 11; `COGNITIVE_PROTOCOL_ONTOLOGY.md` feedback categories.

### SafetyInstruction

- **Purpose:** A runtime safety command delivered to the learner.
- **Ownership:** Runtime safety subsystem.
- **Immutability:** Immutable.
- **Versioning:** `safety_instruction_id`, `session_id`, `safety_rule_id`.
- **Required fields:**
  - `safety_instruction_id`
  - `session_id`
  - `safety_rule_id`
  - `instruction_payload`
  - `started_at`
  - `severity`
- **Prohibited responsibilities:**
  - Must not be confused with educational feedback.
  - Overrides all instructional flow.
- **Relation to event stream:** `safety_rule_triggered`, `recovery_inserted`, `protocol_terminated`.

### AdaptationDecision

- **Purpose:** A contractual, reversible decision to change one controllable parameter.
- **Ownership:** Adaptation policy.
- **Immutability:** Immutable.
- **Versioning:** `adaptation_decision_id`, `policy_id`, `policy_version`.
- **Required fields:**
  - `adaptation_decision_id`
  - `session_id`
  - `policy_id`
  - `policy_version`
  - `deployment_status` (`exploratory_only` | `shadow_mode` | `limited_runtime` | `production_approved`)
  - `target_dimension` (typed difficulty dimension)
  - `current_value`
  - `proposed_value`
  - `allowed_bounds`
  - `source_event_ids`
  - `evidence_record_ids` (optional)
  - `aggregation_window`
  - `minimum_evidence`
  - `uncertainty_threshold`
  - `confidence`
  - `cooldown`
  - `hysteresis`
  - `maximum_step_size`
  - `rollback_rule`
  - `abstention_rule`
  - `decision` (`APPLY` | `NO_CHANGE_INSUFFICIENT_EVIDENCE` | `REVERSE` | `ABSTAIN`)
  - `reason`
- **Optional fields:**
  - `applied_at`
  - `reversed_at`
  - `outcome_event_refs`
- **Prohibited responsibilities:**
  - `audit_event_id` removed; events reference the decision ID.
  - Must not change more than one dimension unless declared as compound policy.
  - `shadow_mode` models may never apply runtime changes.
- **Relation to event stream:** `adaptation_proposed`, `adaptation_abstained`, `adaptation_applied`, `adaptation_reversed`.
- **Traceability:** Corrections 7, 8, 9; `MPE_ADAPTATION_CONTRACT.md`; `COGNITIVE_PROTOCOL_ONTOLOGY.md` AdaptationDecision.

### ScheduleDecision

- **Purpose:** Determines the next item, block, or session action.
- **Ownership:** Scheduler / item policy.
- **Immutability:** Immutable.
- **Versioning:** `schedule_decision_id`, `scheduler_id`, `scheduler_version`.
- **Required fields:**
  - `schedule_decision_id`
  - `session_id`
  - `scheduler_id`
  - `scheduler_version`
  - `policy_id`
  - `policy_version`
  - `source_event_ids`
  - `item_history_snapshot_id`
  - `candidate_item_ids`
  - `excluded_candidates` (with reasons)
  - `selection_rule`
  - `tie_break_rule`
  - `random_seed` (where applicable)
  - `selected_item_ids`
  - `decision_type` (`next_trial` | `next_block` | `session_end` | `insert_review` | `offer_break`)
  - `decision_status` (`made` | `abstained`)
- **Optional fields:**
  - `expected_difficulty_dimensions`
  - `abstention_reason`
- **Prohibited responsibilities:**
  - Must not use unvalidated EEG state estimates in Phase 4.
  - Must not block on state.
  - Must not render media.
- **Relation to event stream:** `schedule_decision`.
- **Traceability:** Correction 7; `COGNITIVE_PROTOCOL_ONTOLOGY.md` ScheduleDecision.

### StateEstimate

- **Purpose:** An uncertain estimate produced by a versioned `StateInferenceModel`.
- **Ownership:** `StateInferenceModel`.
- **Immutability:** Immutable.
- **Versioning:** `state_estimate_id`, `model_id`, `model_version`, `produced_at`.
- **Required fields:**
  - `state_estimate_id`
  - `model_id`
  - `model_version`
  - `target_estimate_name` (narrow, e.g., `estimated_drowsiness_risk`)
  - `operational_definition`
  - `input_observation_ids`
  - `time_window`
  - `value`
  - `uncertainty`
  - `validation_status`
  - `deployment_status` (`exploratory_only` default)
  - `alternative_explanations`
  - `fallback_behavior_when_uncertain`
- **Optional fields:**
  - `calibration_population`
  - `known_confounds`
- **Prohibited responsibilities:**
  - Must not be used as a blocking condition.
  - Must not be treated as a direct measurement.
- **Relation to event stream:** `state_estimate_produced` (diagnostic only).

### SensorObservation

- **Purpose:** A generic, uninterpreted sensor or device observation.
- **Ownership:** `ObservationProvider`.
- **Immutability:** Immutable.
- **Versioning:** `sensor_observation_id`, `provider_id`, `provider_version`, `preprocessing_version`.
- **Required fields:**
  - `sensor_observation_id`
  - `provider_id`
  - `provider_version`
  - `device_id`
  - `sensor_configuration_id`
  - `preprocessing_version`
  - `feature_name`
  - `raw_or_derived`
  - `feature_window`
  - `observed_at` (component timestamp, non-authoritative)
  - `quality_dimensions`
  - `quality_flags`
  - `quality_model_id`
  - `quality_model_version`
  - `artifact_flags`
  - `numeric_value` or `categorical_value`
  - `uncertainty`
  - `experimental_status`
  - `provenance`
- **Optional fields:**
  - `units`
- **Prohibited responsibilities:**
  - MPE core must not assign meaning to `feature_name`.
- **Relation to event stream:** `observation_received`.

### SafetyEvent

- **Purpose:** Any safety rule activation, user override, or degradation.
- **Ownership:** Runtime safety monitor.
- **Immutability:** Immutable.
- **Versioning:** `safety_event_id`, `safety_rule_id`, `triggered_at`.
- **Required fields:**
  - `safety_event_id`
  - `session_id`
  - `safety_rule_id`
  - `triggered_at`
  - `severity` (`info` | `warning` | `critical`)
  - `action_taken` (`pause` | `terminate` | `volume_limit` | `offer_end` | `insert_recovery`)
- **Optional fields:**
  - `trigger_observation_id`
  - `user_acknowledged_at`
- **Prohibited responsibilities:**
  - Must not be suppressed by adaptation policies.
- **Relation to event stream:** `safety_rule_triggered`, `recovery_inserted`, `protocol_terminated`.

### Outcome

- **Purpose:** A read-only, computed summary of a completed session.
- **Ownership:** Derived from event stream.
- **Immutability:** Immutable once computed.
- **Versioning:** `session_id`, `computation_version`.
- **Required fields:**
  - `session_id`
  - `computation_version`
  - `status`
  - `trial_count`
  - `completed_trial_count`
  - `accuracy` (observed, where applicable)
  - `omission_rate`
  - `coverage`
  - `dropout`
  - `early_termination`
  - `protocol_adherence`
- **Optional fields:**
  - `latency_summaries` (stratified by `task_definition`, `response_mode`, `trial_role`, `item_class`; each stratum contains `median_ms`, `quantiles`, `distribution_summary`, `omission_count`, `timeout_count`)
  - `retention_proxy` (if delayed recall data available)
  - `diagnostics` (state estimate summaries, experimental only)
- **Latency metrics:**
  - Must not aggregate all modalities and task families into one mean.
  - Prefer medians, quantiles, distribution summaries, omission count, timeout count.
- **Prohibited responsibilities:**
  - Must not contain unvalidated state claims.
  - Must not be the source of truth; events are.
- **Relation to event stream:** Computed from `session_started` through `session_completed`.
- **Traceability:** Correction 10; `COGNITIVE_PROTOCOL_ONTOLOGY.md` Outcome.

### EvidenceRecord

- **Purpose:** Captures the evidence backing an `Evaluation`, `ScheduleDecision`, or `AdaptationDecision`.
- **Ownership:** Runtime or provider.
- **Immutability:** Immutable.
- **Versioning:** `evidence_record_id`, `source_event_ids`, `created_at`.
- **Required fields:**
  - `evidence_record_id`
  - `decision_or_evaluation_id`
  - `source_event_ids`
  - `evidence_type` (`domain_evaluation` | `item_history` | `behavioral_observation` | `self_report` | `sensor_observation`)
  - `summary`
- **Optional fields:**
  - `domain_provider_evidence`
- **Prohibited responsibilities:**
  - Must not infer covert mental content.
- **Relation to event stream:** Created by `evidence_record_created`; referenced by `evaluation_completed`, `schedule_decision`, `adaptation_proposed`.

## Relationship summary

```text
Program
  └── ProgramVersion
        └── Session
              ├── Block (optional)
              │     └── Trial
              └── Trial (outside blocks)
                    ├── Instruction(s)
                    ├── StimulusRequest -> RenderedStimulus
                    ├── ResponseWindow
                    │     └── Observation(s)
                    │           └── CapturedResponse
                    │                 └── ResponseInterpretation
                    │                       └── DomainNormalizedResponse
                    │                             └── Evaluation
                    ├── FeedbackEvent (or SafetyInstruction)
                    ├── ScheduleDecision
                    ├── AdaptationDecision (optional, Phase 5A+)
                    ├── SafetyEvent (if triggered)
                    └── EvidenceRecord(s)

StateInferenceModel consumes SensorObservation offline (Phase 5B)
  └── StateEstimate (diagnostic, non-blocking, optional)

DomainProvider provides ContentItem + metadata
Renderer turns ContentItem into RenderedStimulus
ObservationProvider produces Observation
ResponseInterpreter produces ResponseInterpretation
DomainNormalizer produces DomainNormalizedResponse
Evaluator compares DomainNormalizedResponse to expected ContentItem
Scheduler / ItemPolicy produces ScheduleDecision
```

## Key ownership boundaries

- **Runtime** owns timestamps, scheduling, response windows, session lifecycle, safety.
- **DomainProvider** owns content identity and domain metadata.
- **Renderer** owns media generation and duration.
- **ObservationProvider** owns raw input capture and quality flags.
- **ResponseInterpreter** owns domain-agnostic extraction (ASR, button mapping, text).
- **DomainNormalizer** owns domain-specific canonicalization (e.g., Hebrew spelling).
- **Evaluator** owns correctness verdicts, evidence, and abstention.
- **Scheduler / ItemPolicy** owns item selection and spacing.
- **StateInferenceModel** owns uncertain state estimates; MPE core does not interpret features.

## Traceability

Each object definition above includes a "Traceability" note citing the audit file and section that drives its shape. In aggregate, the object model implements `COGNITIVE_PROTOCOL_ONTOLOGY.md` all core-entity sections, `DOMAIN_INDEPENDENCE_MAP.md` provider contract table, `PROTOCOL_PRIMITIVES_CATALOG.md` §Allowed/Prohibited primitives and §Response requirement values, and `SOURCE_CLAIM_AUDIT.md` claims 1, 4–13 (rejected) and 14–28 (accepted).
