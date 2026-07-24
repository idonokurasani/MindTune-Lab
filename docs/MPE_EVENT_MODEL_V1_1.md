# MPE Event Model v1.1

## Audit basis

This event model implements `COGNITIVE_PROTOCOL_ONTOLOGY.md` §TrialRole, §Instruction, §Response processing layers, §Evaluation, §Feedback, §Safety, §ScheduleDecision, §AdaptationDecision, §Outcome and `PROTOCOL_PRIMITIVES_CATALOG.md` §Allowed primitives, §Prohibited primitives. It enforces `DOMAIN_INDEPENDENCE_MAP.md` by keeping provider-specific semantics out of core event definitions.

## Principles

- The **event stream is the source of truth**. All mutable objects are derived views.
- Events are **immutable** and **append-only**.
- Every event has a **timestamp owned by the runtime** from a monotonic session clock, with device-time and estimated-latency metadata where relevant.
- Every event carries **provenance**: source component, component version, and a correlation ID linking it to a trial/session/block.
- Every event carries a **session_sequence_number** that defines canonical per-session ordering. UUID ordering is never used as canonical ordering.
- Events are **versioned**; old payload versions must remain parseable.
- **Sensitive data** (raw audio, raw EEG, free text) is flagged and subject to consent and retention policies.

## Event payload shape

Every event has the following common fields:

```text
Event
├── event_id              (UUID, immutable event identity)
├── event_type            (string from taxonomy)
├── schema_version        (event payload version)
├── session_id
├── session_sequence_number (strictly monotonic per session, canonical ordering)
├── protocol_version_id
├── trial_id              (if applicable)
├── block_id              (if applicable)
├── timestamp             (runtime-owned monotonic session time, seconds since active session start)
├── wallclock_at          (optional, device wall-clock, may drift)
├── component             (who emitted it: runtime, renderer, evaluator, observation_provider, safety_monitor, scheduler)
├── component_version
├── correlation_id        (links a request to its response/result)
├── provenance            (list of preceding event_ids that caused this event)
├── payload               (event-specific)
├── sensitive             (boolean: does this event contain raw physiological/audio/voice/free-text data?)
├── data_classification   (optional enum: `public` | `consent_gated` | `sensitive_phi` | `research_sensitive`; inferred from `sensitive` when omitted)
└── quality_flags         (optional: event-level device timing uncertainty, observation quality, etc.)
```

`timestamp` is always owned by the runtime. Components may report their own `component_timestamp` inside `payload`, but the runtime timestamp is authoritative. Latency is derived from runtime `timestamp` pairs, not from component timestamps.

## Session clock and pause semantics

- `timestamp` counts active session time. Paused time is **not** counted.
- `scheduled_for` and `deadline_at` are expressed in the same active-session timeline.
- When a session resumes, scheduled future events are **not** shifted unless a safety or recovery rule explicitly reschedules them.
- Response latency is `response_completed.timestamp - response_window_opened.timestamp` and excludes paused intervals.
- Late provider events are ordered by `session_sequence_number`, not by `event_id` or wall clock.

## Canonical event taxonomy

### session_created

- **When:** A `Session` object is instantiated but not yet started.
- **Payload:** `session_id`, `program_version_id`, `protocol_version_id`, `learner_id`.
- **Object created:** `Session`.
- **Replay-deterministic:** Yes.
- **Sensitive:** No.

### session_started

- **When:** The user confirms start and the runtime clock begins.
- **Payload:** `session_id`, `program_version_id`, `protocol_version_id`, `learner_id`, `random_seed`, `start_parameters`.
- **Object updated:** `Session`.
- **Replay-deterministic:** Yes.
- **Sensitive:** No.

### session_paused

- **When:** User or safety rule pauses the session.
- **Payload:** `session_id`, `reason` (`user`, `safety`, `device_error`), `paused_at` (runtime timestamp), `active_session_time_at_pause`.
- **Object updated:** `Session`.
- **Replay-deterministic:** No (depends on user/system trigger).
- **Sensitive:** No.

### session_resumed

- **When:** Session resumes from pause.
- **Payload:** `session_id`, `resumed_at` (runtime timestamp), `active_session_time_at_resume`.
- **Object updated:** `Session`.
- **Replay-deterministic:** No.
- **Sensitive:** No.

### session_cancelled

- **When:** The user explicitly cancels the session before normal completion.
- **Payload:** `session_id`, `reason` (`user`, `device_error`), `cancelled_at`.
- **Lifecycle note:** Distinct from `protocol_terminated`. This is a cancellation, not a safety termination.
- **Object updated:** `Session`.
- **Replay-deterministic:** No.
- **Sensitive:** No.

### session_completed

- **When:** Protocol graph reaches a terminal state normally.
- **Payload:** `session_id`, `completed_at`, `final_trial_index`.
- **Lifecycle note:** Distinct from `session_cancelled` and `protocol_terminated`.
- **Object updated:** `Session`.
- **Replay-deterministic:** Yes, given same observation stream and policy.
- **Sensitive:** No.

### block_started

- **When:** A block begins.
- **Payload:** `session_id`, `block_id`, `block_type`, `trial_count` (if known).
- **Object created:** `Block` execution record.
- **Replay-deterministic:** Yes.
- **Sensitive:** No.

### block_completed

- **When:** A block ends.
- **Payload:** `session_id`, `block_id`, `completed_trial_count`.
- **Object updated:** `Block`.
- **Replay-deterministic:** Yes.
- **Sensitive:** No.

### trial_created

- **When:** Runtime generates a trial plan from protocol and schedule decision.
- **Payload:** `trial_id`, `session_id`, `block_id`, `trial_index`, `task_definition_id`, `content_item_ids`, `difficulty_dimensions`, `response_requirement` (`required` | `optional` | `none`), `accepted_response_modes` (optional list).
- **Object created:** `Trial`.
- **Replay-deterministic:** Yes, given deterministic scheduler.
- **Sensitive:** No.

### instruction_started

- **When:** An instruction begins playback or display.
- **Payload:** `trial_id`, `instruction_id`, `instruction_type`, `instruction_payload`, `content_item_id` (if any), `target_operation`, `observable_response_expected`, `started_at`.
- **Object created:** `Instruction` execution record.
- **Replay-deterministic:** Yes.
- **Sensitive:** No.

### instruction_completed

- **When:** Instruction finishes or allotted time expires.
- **Payload:** `trial_id`, `instruction_id`, `completed_at`, `duration`.
- **Object updated:** `Instruction`.
- **Replay-deterministic:** Yes, for fixed duration; no for variable durations until `instruction_completed` is observed.
- **Sensitive:** No.

### stimulus_requested

- **When:** Runtime asks a `Renderer` to prepare media.
- **Payload:** `stimulus_request_id`, `trial_id`, `content_item_id`, `renderer_id`, `requested_at` (runtime timestamp), `scheduled_for`, `rate`, `voice_id`, `prosody_hints`.
- **Object created:** `StimulusRequest`.
- **Replay-deterministic:** Yes.
- **Sensitive:** No.

### stimulus_ready

- **When:** `Renderer` returns `RenderedStimulus`.
- **Payload:** `stimulus_request_id`, `rendered_stimulus_id`, `renderer_version`, `duration`, `rendered_at` (renderer component timestamp), `provenance`.
- **Object created:** `RenderedStimulus`.
- **Replay-deterministic:** Depends on renderer; same renderer/version with same config is deterministic; capture required for exact replay.
- **Sensitive:** No.

### stimulus_started

- **When:** Audio actually begins playing.
- **Payload:** `trial_id`, `stimulus_request_id`, `rendered_stimulus_id`, `started_at` (component timestamp).
- **Object updated:** `RenderedStimulus`.
- **Replay-deterministic:** No (device/audio latency).
- **Sensitive:** No.

### stimulus_completed

- **When:** Audio playback ends or is interrupted.
- **Payload:** `trial_id`, `stimulus_request_id`, `completed_at` (component timestamp), `duration_observed`.
- **Object updated:** `RenderedStimulus`.
- **Replay-deterministic:** No.
- **Sensitive:** No.

### response_window_opened

- **When:** The window for an observable response opens.
- **Payload:** `response_window_id`, `trial_id`, `response_modes_accepted`, `opened_at` (runtime timestamp), `deadline_at`, `timeout_policy`.
- **Object created:** `ResponseWindow`.
- **Replay-deterministic:** Yes.
- **Sensitive:** No.

### response_detected

- **When:** An `ObservationProvider` reports a possible response onset (e.g., button press, voice onset, first keystroke).
- **Payload:** `response_window_id`, `observation_id`, `provider_id`, `detected_at` (component timestamp, non-authoritative), `response_mode`.
- **Object updated:** `Observation`.
- **Replay-deterministic:** No.
- **Sensitive:** Depends on provider (voice onset may be derived from raw audio; flag as sensitive if raw audio is retained).

### response_completed

- **When:** The response is finalized (button release, voice end, final keystroke).
- **Payload:** `response_window_id`, `observation_id`, `completed_at` (component timestamp, non-authoritative), `response_mode`.
- **Object updated:** `Observation`; references `CapturedResponse` that will be created by `captured_response_created`.
- **Replay-deterministic:** No.
- **Sensitive:** Depends on provider.

### response_timeout

- **When:** The response window closes without a finalized response.
- **Payload:** `response_window_id`, `trial_id`, `timeout_at` (runtime timestamp).
- **Object updated:** `ResponseWindow`.
- **Replay-deterministic:** Yes.
- **Sensitive:** No.

### observation_received

- **When:** Any `Observation` is received from an `ObservationProvider`.
- **Payload:** `observation_id`, `response_window_id` (if any), `provider_id`, `provider_version`, `observation_type`, `received_at` (component timestamp, non-authoritative), `payload`, `quality_dimensions`, `quality_flags`, `quality_model_id`, `quality_model_version`, `overall_quality` (optional), `artifact_flags`.
- **Object created:** `Observation` (and `SensorObservation` when `observation_type == sensor_feature`).
- **Replay-deterministic:** No.
- **Sensitive:** Yes if raw audio, raw EEG, or free-text self-report.

### captured_response_created

- **When:** The runtime assembles a technical capture from one or more observations and the response window.
- **Payload:** `captured_response_id`, `response_window_id`, `observation_ids`, `response_mode`, `captured_payload`, `captured_at` (component timestamp, non-authoritative), `device_provenance`, `quality_flags`.
- **Object created:** `CapturedResponse`.
- **Causal input:** `response_window_opened`, `observation_received`, `response_completed`.
- **Replay-deterministic:** Yes, given same observations and response window.
- **Sensitive:** Depends on provider.

### response_interpreted

- **When:** A `ResponseInterpreter` produces a domain-agnostic interpretation of a `CapturedResponse`.
- **Payload:** `response_interpretation_id`, `response_window_id`, `captured_response_id`, `interpreter_id`, `interpreter_version`, `interpreted_payload`, `interpretation_confidence`, `interpretation_type` (`asr_transcript` | `button_label` | `typed_text` | `selected_option`), `component_timestamp`.
- **Object created:** `ResponseInterpretation`.
- **Causal input:** `captured_response_created`.
- **Replay-deterministic:** Yes for deterministic interpreters; capture required for exact ASR replay.
- **Sensitive:** Yes if it contains transcribed speech or typed text.

### domain_response_normalized

- **When:** A `DomainNormalizer` produces a `DomainNormalizedResponse` from a `ResponseInterpretation`.
- **Payload:** `domain_normalized_response_id`, `response_window_id`, `response_interpretation_id`, `response_mode`, `normalizer_id`, `normalizer_version`, `normalized_payload`, `extracted_at` (component timestamp, non-authoritative), `uncertainty`.
- **Object created:** `DomainNormalizedResponse`.
- **Causal input:** `response_interpreted`.
- **Replay-deterministic:** Yes for deterministic normalizers.
- **Sensitive:** Yes if it contains transcribed speech or typed text.

### evaluation_completed

- **When:** An `Evaluator` returns a correctness verdict.
- **Payload:** `evaluation_id`, `trial_id`, `evaluator_id`, `evaluator_version`, `domain_normalized_response_id`, `expected_content_item_id`, `answer_status`, `evaluation_status`, `correctness_credit`, `accepted_variant_id`, `evidence_group`, `scope_status`, `evidence`, `error_category`, `confidence`.
- **Object created:** `Evaluation`.
- **Causal input:** `domain_response_normalized`.
- **Replay-deterministic:** Yes for deterministic evaluators.
- **Sensitive:** No.

### evaluation_abstained

- **When:** An `Evaluator` cannot determine correctness and deliberately abstains.
- **Payload:** `evaluation_id`, `trial_id`, `evaluator_id`, `evaluator_version`, `domain_normalized_response_id` (if available), `expected_content_item_id`, `answer_status` (`unevaluable`), `evaluation_status` (`abstained`), `abstention_reason`, `failure_reason`, `scope_status`, `error_category`.
- **Object created:** `Evaluation`.
- **Causal input:** `domain_response_normalized` or `response_interpreted`.
- **Replay-deterministic:** Yes.
- **Sensitive:** No.

### evaluation_failed

- **When:** An `Evaluator` fails to complete evaluation (e.g., engine exception, malformed output, version mismatch).
- **Payload:** `evaluation_id`, `trial_id`, `evaluator_id`, `evaluator_version`, `domain_normalized_response_id` (if available), `expected_content_item_id`, `answer_status` (`unevaluable`), `evaluation_status` (`failed`), `failure_reason`, `error_category` (`engine_error` or `version_mismatch`), `evidence_record_id`.
- **Object created:** `Evaluation`.
- **Causal input:** `domain_response_normalized` or `response_interpreted`.
- **Replay-deterministic:** Yes for deterministic failure handling.
- **Sensitive:** No.

### feedback_started

- **When:** Educational feedback playback or display begins.
- **Payload:** `feedback_event_id`, `trial_id`, `evaluation_id` (if applicable), `feedback_category` (`KNOWLEDGE` | `PERFORMANCE` | `METACOGNITIVE`), `feedback_type`, `content_item_id` or `rendered_stimulus_id`, `started_at`.
- **Object created:** `FeedbackEvent`.
- **Causal input:** `evaluation_completed`.
- **Replay-deterministic:** Yes.
- **Sensitive:** No.

### feedback_completed

- **When:** Educational feedback playback or display ends.
- **Payload:** `feedback_event_id`, `trial_id`, `completed_at`, `duration_observed`.
- **Object updated:** `FeedbackEvent`.
- **Replay-deterministic:** No.
- **Sensitive:** No.

### safety_instruction_started

- **When:** A runtime safety instruction begins.
- **Payload:** `safety_instruction_id`, `session_id`, `safety_rule_id`, `instruction_payload`, `started_at`.
- **Object created:** `SafetyInstruction`.
- **Causal input:** `safety_rule_triggered` or `recovery_inserted`.
- **Replay-deterministic:** Depends on safety rule trigger.
- **Sensitive:** No.

### safety_instruction_completed

- **When:** A runtime safety instruction ends or is acknowledged.
- **Payload:** `safety_instruction_id`, `session_id`, `completed_at`, `user_acknowledged_at`.
- **Object updated:** `SafetyInstruction`.
- **Replay-deterministic:** No.
- **Sensitive:** No.

### schedule_decision

- **When:** The scheduler selects the next trial/block/item.
- **Payload:** `schedule_decision_id`, `session_id`, `scheduler_id`, `scheduler_version`, `policy_id`, `policy_version`, `source_event_ids`, `item_history_snapshot_id`, `candidate_item_ids`, `excluded_candidates` with reasons, `selection_rule`, `tie_break_rule`, `random_seed`, `selected_item_ids`, `decision_type`, `decision_status` (`made` | `abstained`), `abstention_reason`, `expected_difficulty_dimensions`.
- **Object created:** `ScheduleDecision`.
- **Causal input:** `evaluation_completed`, `evaluation_abstained`, `session_started`.
- **Replay-deterministic:** Yes for deterministic schedulers.
- **Sensitive:** No.

### evidence_record_created

- **When:** The runtime or a provider bundles evidence for an `Evaluation`, `ScheduleDecision`, or `AdaptationDecision`.
- **Payload:** `evidence_record_id`, `decision_or_evaluation_id`, `source_event_ids`, `evidence_type` (`domain_evaluation` | `item_history` | `behavioral_observation` | `self_report` | `sensor_observation`), `summary`, `domain_provider_evidence` (optional).
- **Object created:** `EvidenceRecord`.
- **Causal input:** `evaluation_completed`, `schedule_decision`, `adaptation_proposed`.
- **Replay-deterministic:** Yes (derived from source events).
- **Sensitive:** No.

### adaptation_proposed

- **When:** An adaptation policy computes a proposed parameter change.
- **Payload:** `adaptation_decision_id`, `session_id`, `policy_id`, `policy_version`, `deployment_status`, `target_dimension`, `current_value`, `proposed_value`, `allowed_bounds`, `source_event_ids`, `evidence_record_ids` (optional), `aggregation_window`, `minimum_evidence`, `uncertainty_threshold`, `confidence`, `cooldown`, `hysteresis`, `maximum_step_size`, `rollback_rule`, `abstention_rule`, `decision`, `reason`.
- **Object created:** `AdaptationDecision`.
- **Causal input:** `evaluation_completed`, `schedule_decision`.
- **Replay-deterministic:** Yes.
- **Sensitive:** No.

### adaptation_abstained

- **When:** An adaptation policy chooses `NO_CHANGE_INSUFFICIENT_EVIDENCE` or `ABSTAIN`.
- **Payload:** `adaptation_decision_id`, `session_id`, `policy_id`, `policy_version`, `deployment_status`, `target_dimension`, `decision`, `reason`.
- **Object updated:** `AdaptationDecision`.
- **Replay-deterministic:** Yes.
- **Sensitive:** No.

### adaptation_applied

- **When:** A proposed adaptation is actually applied.
- **Payload:** `adaptation_decision_id`, `session_id`, `applied_at` (runtime timestamp), `new_value`, `deployment_status`.
- **Object updated:** `AdaptationDecision`.
- **Replay-deterministic:** Yes.
- **Sensitive:** No.

- **Constraint:** A model in `shadow_mode` or `exploratory_only` must never produce `adaptation_applied`.

### adaptation_reversed

- **When:** An applied adaptation is rolled back.
- **Payload:** `adaptation_decision_id`, `session_id`, `reversed_at` (runtime timestamp), `previous_value`, `reason`.
- **Object updated:** `AdaptationDecision`.
- **Replay-deterministic:** Yes, given reversal rule.
- **Sensitive:** No.

### signal_quality_changed

- **When:** An `ObservationProvider` reports a change in signal quality.
- **Payload:** `session_id`, `provider_id`, `device_id`, `quality_dimensions`, `quality_flags`, `quality_model_id`, `quality_model_version`, `overall_quality` (optional), `artifact_flags`, `reported_at` (component timestamp, non-authoritative).
- **Classification:** Provider/runtime diagnostic fact. Does **not** create a persistent domain object; it is either recorded as an `Observation` with `observation_type == signal_quality` or used as an event-level quality flag. The common `timestamp` field is authoritative.
- **Replay-deterministic:** No.
- **Sensitive:** No (unless it includes raw samples).

### safety_rule_triggered

- **When:** A safety rule is activated.
- **Payload:** `safety_event_id`, `safety_rule_id`, `session_id`, `severity`, `trigger_observation_id`, `action_taken`, `triggered_at` (runtime timestamp).
- **Object created:** `SafetyEvent`.
- **Causal input:** `observation_received`, `signal_quality_changed`.
- **Replay-deterministic:** Depends on rule; deterministic rules replay if observations replay.
- **Sensitive:** No.

### recovery_inserted

- **When:** The runtime inserts a recovery step (e.g., repeat last trial, offer break).
- **Payload:** `safety_event_id`, `session_id`, `trial_id`, `recovery_type`, `reason`, `inserted_at` (runtime timestamp).
- **Object created:** `SafetyEvent`.
- **Replay-deterministic:** Depends on policy.
- **Sensitive:** No.

### protocol_terminated

- **When:** The protocol is terminated by safety, user, or unrecoverable error. This is a terminal safety action, not a normal completion or a user cancellation.
- **Payload:** `safety_event_id`, `session_id`, `reason` (`safety`, `user_emergency`, `unrecoverable_error`, `provider_failure`), `terminated_at` (runtime timestamp), `final_event_id`.
- **Object created:** `SafetyEvent`.
- **Lifecycle note:** Distinct from `session_cancelled` (user cancellation) and `session_completed` (normal protocol end).
- **Replay-deterministic:** No.
- **Sensitive:** No.

### state_estimate_produced (diagnostic, Phase 5B+)

- **When:** A `StateInferenceModel` produces an estimate.
- **Payload:** `state_estimate_id`, `model_id`, `model_version`, `target_estimate_name`, `validation_status`, `deployment_status`, `value`, `uncertainty`, `input_observation_ids`, `alternative_explanations`.
- **Object created:** `StateEstimate`.
- **Replay-deterministic:** Yes for deterministic models.
- **Sensitive:** No.

## Replay semantics

A session is **fully replay-deterministic** if:
- the `ProtocolVersion` is fixed,
- the random seed is fixed,
- all `Observation` inputs are captured,
- all provider outputs (`RenderedStimulus`, `Evaluation`) are captured,
- no external wall-clock dependencies affect the runtime.

A session is **partially replay-deterministic** if only the protocol graph and deterministic schedule are captured; observation timing is allowed to vary.

For Phase 4A/4B, the goal is **partial replay-determinism** with deterministic protocol execution. Full replay with captured observations is a Phase 4B acceptance criterion.

## Event ordering guarantees

- Events within a single trial are causally ordered by `provenance` and then by `session_sequence_number`.
- The runtime guarantees monotonic `timestamp` and monotonic `session_sequence_number` within a session.
- Concurrent observation providers may produce events with near-identical timestamps; ordering is resolved by `session_sequence_number`, never by `event_id`.

## Sensitive data handling

| Event type | Sensitive | Data classification | Reason |
|---|---|---|---|
| `observation_received` (voice) | Yes | `sensitive_phi` | May contain raw audio. |
| `observation_received` (EEG) | Yes | `sensitive_phi` | May contain raw samples. |
| `observation_received` (self-report free text) | Yes | `consent_gated` | Free text. |
| `response_interpreted` (voice/typed) | Yes | `consent_gated` | May contain transcribed content. |
| `domain_response_normalized` (voice/typed) | Yes | `consent_gated` | May contain transcribed content. |
| `evaluation_completed` | No | `public` | Verdict and evidence only. |
| `evaluation_abstained` | No | `public` | Verdict and reason only. |
| `evaluation_failed` | No | `public` | Failure reason only. |
| `stimulus_ready` | No | `public` | Media handle, not content. |
| `state_estimate_produced` | No | `research_sensitive` (default) | Aggregate estimate; classification may vary by consent. |

Sensitive and `sensitive_phi` events are encrypted at rest, consent-gated, and subject to retention policies.

## Traceability

This event taxonomy implements `COGNITIVE_PROTOCOL_ONTOLOGY.md` §TrialRole (instruction, response window, feedback, safety instruction), §Response processing layers (`observation_received` → `captured_response_created` → `response_interpreted` → `domain_response_normalized` → `evaluation_completed`/`evaluation_abstained`/`evaluation_failed`), §Evaluation (answer/evaluation status separation), §Feedback (Knowledge/Performance/Metacognitive categories), §Safety, §ScheduleDecision (reproducible fields), §AdaptationDecision (deployment status constraint, no circular audit event reference), and §EvidenceRecord. It also reflects `PROTOCOL_PRIMITIVES_CATALOG.md` §Allowed primitives and §Prohibited primitives (no `wait_for_state`, no EEG-semantic primitives).
