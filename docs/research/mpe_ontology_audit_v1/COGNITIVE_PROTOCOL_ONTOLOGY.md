# Cognitive Protocol Ontology v1

## Purpose

This document defines the conceptual entities of the MindTune Protocol Engine. It is implementation-neutral. Every claim uses operational definitions so that it can be validated or falsified.

## Core entities

### Program

A stable logical identity that groups protocols toward a learner goal. A Program does not contain executable content.

- **Fields:** `id`, `name`, `description`, `transfer_claim_level`.
- **Not executable.**

### ProgramVersion

An immutable executable definition of a Program at a point in time. Contains the sequence of ProtocolVersions, schedule, safety profile, consent requirements, and dependencies.

- **Fields:** `program_id`, `version`, `checksum`, `protocol_version_sequence`, `safety_profile_id`, `consent_requirements`, `schema_version`, `created_at`.

### Protocol

A stable logical identity for one session type. A Protocol does not contain executable content.

- **Fields:** `id`, `name`, `description`, `protocol_family`, `purpose`.

### ProtocolVersion

An immutable executable definition of a Protocol. Contains the trial/block sequence, required providers, safety profile, schema version, and versioned dependencies.

- **Fields:** `protocol_id`, `version`, `checksum`, `objective`, `purpose`, `primary_transfer_claim`, `block_sequence` or `trial_sequence`, `required_providers`, `safety_profile_id`, `schema_version`, `dependency_versions`, `created_at`.

### Session

One execution of a ProgramVersion / ProtocolVersion by a learner. The runtime owns all session state; the Session object is a query over the event stream.

- **References:** `program_version_id`, `protocol_version_id`, `learner_id`.

### Block

A named sub-sequence of trials (e.g., warm-up, assessment, core). Blocks are part of the immutable ProtocolVersion.

- **Fields:** `id`, `block_type`, `trial_sequence`, `exit_condition`.

### Trial

The atomic unit of a protocol. A trial is one complete exposure/instruction/response-window/observation/interpretation/normalization/evaluation/feedback cycle. A trial does not require an observable response.

- **Fields:** `id`, `trial_index`, `task_definition_id`, `content_item_ids`, `response_requirement` (`required` | `optional` | `none`), `accepted_response_modes` (optional list), `difficulty_dimensions`.

### TaskDefinition

A reusable template that defines the role sequence for a cognitive task pattern. Examples: `language_prediction_retrieval`, `perceptual_discrimination`, `overt_recall`, `morphology_generation`, `working_memory_sequence`.

- **Fields:** `id`, `version`, `task_family`, `trial_role_sequence`.

### TrialRole

A named stage within a trial, such as:

- `STIMULUS` — present an auditory or other cue.
- `COVERT_INSTRUCTION` — instruct the learner to think, rehearse, or imagine without observable scoring.
- `RESPONSE_WINDOW` — interval during which an observable response may be collected.
- `FEEDBACK` — provide knowledge, performance, or metacognitive feedback.
- `SAFETY_INSTRUCTION` — override flow for safety (not educational feedback).

## Instruction

An Instruction is a deliberate communication to the learner. It has:

- `instruction_payload` — what is said or played (text/media reference, never null).
- `target_operation` — the requested learner operation (e.g., `listen`, `rehearse_mentally`, `predict_silently`, `speak_aloud`, `type`).
- `allotted_duration` — how long the learner has for the operation.
- `observable_response_expected` — whether an observable probe follows.

A covert instruction still has `instruction_payload`. It may instruct "predict the Hebrew word silently". The system records that the instruction was given and its time window. It never records the covert answer, correctness, or semantic content.

## Stimulus and rendered media

- `StimulusRequest` — runtime request to produce media for a content item or instruction.
- `RenderedStimulus` — the output of a `Renderer` (e.g., audio file, stream handle) with duration and provenance.

## Response processing layers

The response path is strictly layered:

1. `Observation` — raw input from an `ObservationProvider` (button, voice sample, keystroke, sensor feature).
2. `CapturedResponse` — technical capture with device timestamps, provenance, and quality flags.
3. `ResponseInterpretation` — domain-agnostic transformation (ASR, button label mapping, text extraction, confidence).
4. `DomainNormalizedResponse` — domain-specific canonicalization (e.g., strip niqqud, normalize Hebrew spelling).
5. `Evaluation` — comparison against a domain-grounded expected answer by an `Evaluator`.

Speech-derived Hebrew output is not provider-agnostic. It must be processed by the Hebrew `ResponseInterpreter` and `DomainNormalizer`.

## Evaluation

An Evaluation has two orthogonal statuses:

- `answer_status`: `correct`, `incorrect`, `acceptable_variant`, `partially_correct`, `unevaluable`.
- `evaluation_status`: `completed`, `abstained`, `failed`, `out_of_scope`.

Additional fields:

- `correctness_credit` (0.0–1.0, e.g., 1.0 for correct, 0.5 for acceptable_variant).
- `accepted_variant_id`.
- `evidence_group` (from Hebrew engine).
- `scope_status` (e.g., `verified_consensus`, `high_confidence_candidate`, `unresolved`).
- `abstention_reason`.
- `failure_reason`.

## Feedback

Feedback is separated into:

- `KnowledgeFeedback` — correct answer, elaboration, example.
- `PerformanceFeedback` — correct/incorrect indicator, error category.
- `MetacognitivePrompt` — confidence request, strategy suggestion.
- `SafetyInstruction` — runtime safety command (separate from educational feedback).

## ScheduleDecision

A `ScheduleDecision` selects the next item, block, or session action. It must be fully reproducible:

- `policy_id` and `policy_version`.
- `source_event_ids`.
- `item_history_snapshot_id`.
- `candidate_item_ids`.
- `excluded_candidates` with reasons.
- `selection_rule` and `tie_break_rule`.
- `random_seed` where applicable.
- `selected_item_ids`.
- `decision_status` (`made` | `abstained`).
- `abstention_reason`.

## AdaptationDecision

A contractual, reversible decision to change one controllable parameter. Events reference the decision; the decision does not reference an audit event.

- `deployment_status`: `exploratory_only` (offline only), `shadow_mode` (hypothetical only), `limited_runtime` (approved experiment only), `production_approved`.
- No model in `shadow_mode` may apply a runtime change.

## LatentEstimate

A `LatentEstimate` (or `StateEstimate`) is an uncertain inference about a cognitive state. It must include:

- `model_id` and `model_version`.
- `target_estimate_name` (narrow, e.g., `estimated_drowsiness_risk`).
- `operational_definition`.
- `input_observations`.
- `time_window`.
- `value` and `uncertainty`.
- `validation_status`.
- `deployment_status` (default `exploratory_only`).
- `alternative_explanations`.
- `fallback_behavior_when_uncertain`.

A latent estimate is never treated as a direct measurement and never used as a blocking condition.

## Safety

Safety is separate from adaptation and feedback. Safety rules:

- Always-on user stop command.
- Emergency pause.
- Maximum approved session duration.
- No silent session extension.
- Hearing-volume constraints.
- Headphone and environment warnings.
- Eyes-closed environment check.
- Motion/travel prohibition where relevant.
- Fatigue self-report.
- Repeated-error frustration threshold.
- Signal loss fallback.
- Microphone failure fallback.
- Provider timeout.
- Degraded mode.
- Session termination rules.

Safety rules override adaptation, instruction, and feedback.

## Outcome

A computed read-only summary of a session. Latency metrics must be stratified by `task_definition`, `response_mode`, `trial_role`, and `item_class`. Prefer medians, quantiles, omission counts, and timeout counts over a single global mean.
