# MPE v1.1 Provider API Specification

## Scope

This document defines the API contract for every provider interface in the MindTune Protocol Engine v1.1. It is derived directly from:

- `MPE_PROVIDER_BOUNDARIES.md`
- `MPE_OBJECT_MODEL_V1_1.md`
- `MPE_HEBREW_PROVIDER_CONTRACT.md`
- `MPE_EVENT_MODEL_V1_1.md`
- `MPE_CANONICAL_IDENTIFIER_REGISTRY.md`
- `MPE_CANONICAL_ENUM_REGISTRY.md`

No implementation language, protocol (REST/GraphQL/protobuf), or framework is specified. Each section defines the abstract operation, inputs, outputs, errors, timeouts, retries, ownership, and side effects.

## Legend

| Tag | Meaning |
|---|---|
| **Normative** | Required by MPE v1.1. |
| **Recommended** | Strongly advised for correctness, performance, or auditability. |
| **Optional** | May be omitted in a minimal implementation. |
| **Out of scope** | Not part of Phase 4A. |
| **Implementation note** | Engineering guidance, not an architectural rule. |

## 1. Shared concepts

### 1.1 Capabilities pattern

Every provider must expose a capabilities operation that returns identity, version, and supported features. The runtime uses capabilities to validate `ProtocolVersion.required_providers` at session start.

**Normative common capabilities fields:**

- `provider_id` / `renderer_id` / `interpreter_id` / `normalizer_id` / `evaluator_id` / `scheduler_id` / `model_id`
- `*_version`
- Supported input/output types or schemas
- Optional: `latency_estimate_ms`

### 1.2 Correlation ID

- **Normative:** Every provider invocation must accept a `correlation_id` and return it unchanged. The runtime uses it to link provider outputs to events.

### 1.3 Timeout and retry defaults

| Aspect | Default | Notes |
|---|---|---|
| Capability call timeout | 2s | Runtime may block briefly at session start. |
| Rendering timeout | 5s + media duration | Renderer may pre-render. |
| Observation poll timeout | 100ms | Polling must not block scheduler. |
| Interpretation timeout | 2s | ASR must stream. |
| Normalization timeout | 1s | Deterministic function. |
| Evaluation timeout | 2s | Domain engine call. |
| Scheduling timeout | 500ms | Deterministic function. |
| State estimate timeout | 5s | Shadow/offline only. |

**Recommended:** Timeouts must be configurable per `ProtocolVersion` and provider.
**Implementation note:** Retries should be idempotent; provider operations must not mutate MPE runtime state.

## 2. Renderer

### 2.1 Responsibility

Convert a `StimulusRequest` into playable media. The `Renderer` owns media generation and duration but no correctness logic.

### 2.2 Operations

#### `capabilities() -> RendererCapabilities`

- **Inputs:** None.
- **Outputs:**
  - `renderer_id` (string)
  - `renderer_version` (string)
  - `formats_supported` (list)
  - `voices_supported` (list)
  - `rate_range` (object `{min, max, default}`)
  - `latency_estimate_ms` (number)
  - `streaming_support` (boolean)
- **Side effects:** None.
- **Errors:**
  - `capability_unavailable`: cannot return capabilities.
- **Timeout:** 2s.
- **Retries:** 2 immediate retries, then fail.

#### `render(request: StimulusRequest) -> RenderedStimulus`

- **Inputs:** `StimulusRequest` object:
  - `stimulus_request_id`
  - `trial_id`
  - `content_item_id` or `prompt_text`
  - `voice_id` (optional)
  - `rate` (optional)
  - `prosody_hints` (optional)
- **Outputs:** `RenderedStimulus` object:
  - `rendered_stimulus_id`
  - `stimulus_request_id`
  - `renderer_id`
  - `renderer_version`
  - `media_handle`
  - `duration`
  - `rendered_at` (component timestamp)
  - `format` (optional)
  - `provenance` (optional)
- **Side effects:** May generate or cache media; must not change `ContentItem`.
- **Errors:**
  - `render_failed`: unable to generate media.
  - `voice_unavailable`: requested voice not supported.
  - `content_unsupported`: content type cannot be rendered.
  - `fallback_used`: TTS engine ignored `pronunciation_metadata`.
- **Timeout:** 5s + expected duration.
- **Retries:** 1 retry with fallback voice; if persistent, runtime logs `renderer_fallback` and continues.
- **Ownership:** `Renderer` owns `RenderedStimulus.media_handle` and `duration`; runtime owns timestamps.

## 3. ObservationProvider

### 3.1 Responsibility

Capture raw learner or sensor input and report quality. It does not interpret responses.

### 3.2 Operations

#### `capabilities() -> ObservationCapabilities`

- **Inputs:** None.
- **Outputs:**
  - `provider_id`
  - `provider_version`
  - `observation_types_supported`
  - `device_id`
  - `quality_dimensions_supported`
  - `quality_flags_supported`
  - `quality_model_id`
  - `quality_model_version`
  - `latency_estimate_ms`
- **Side effects:** None.
- **Timeout:** 2s.

#### `start_listening(window: ResponseWindow) -> void`

- **Inputs:** `ResponseWindow` object.
- **Outputs:** Acknowledgment or `unsupported_response_mode` error.
- **Side effects:** Begins capturing input for the window.
- **Timeout:** 1s.
- **Retries:** 0; failure is a runtime error.

#### `stop_listening(window_id: UUID) -> void`

- **Inputs:** `response_window_id`.
- **Outputs:** Acknowledgment.
- **Side effects:** Stops capturing.
- **Timeout:** 1s.

#### `poll() -> list of Observation`

- **Inputs:** None.
- **Outputs:** List of `Observation` objects since last poll, each containing:
  - `observation_id`
  - `response_window_id` (if applicable)
  - `provider_id`
  - `provider_version`
  - `observation_type`
  - `received_at` (component timestamp)
  - `payload`
  - `quality_dimensions`
  - `quality_flags`
  - `quality_model_id`
  - `quality_model_version`
  - `overall_quality` (optional)
  - `artifact_flags` (optional)
  - `device_id` (optional)
- **Side effects:** Returns and clears local buffer; does not evaluate.
- **Errors:**
  - `device_error`: sensor disconnected or malfunction.
  - `buffer_overflow`: observations dropped.
- **Timeout:** 100ms per poll.
- **Retries:** Continuous polling; device error triggers `signal_quality_changed` or `safety_rule_triggered`.

#### `signal_quality() -> SignalQuality` (optional, push or poll)

- **Inputs:** None.
- **Outputs:** `quality_dimensions`, `quality_flags`, `quality_model_id`, `quality_model_version`, `overall_quality`, `artifact_flags`, `reported_at`.
- **Side effects:** May emit `signal_quality_changed` event.
- **Timeout:** N/A.

## 4. ResponseInterpreter

### 4.1 Responsibility

Transform a `CapturedResponse` into a domain-agnostic interpreted form.

### 4.2 Operations

#### `capabilities() -> InterpreterCapabilities`

- **Inputs:** None.
- **Outputs:**
  - `interpreter_id`
  - `interpreter_version`
  - `response_modes_supported`
  - `output_schema`
- **Timeout:** 2s.

#### `interpret(captured_response: CapturedResponse) -> ResponseInterpretation`

- **Inputs:** `CapturedResponse` object with `captured_response_id`, `response_mode`, `captured_payload`, `observation_ids`, `quality_flags`.
- **Outputs:** `ResponseInterpretation` object:
  - `response_interpretation_id`
  - `response_window_id`
  - `captured_response_id`
  - `interpreter_id`
  - `interpreter_version`
  - `interpreted_payload`
  - `interpretation_confidence`
  - `interpretation_type` (`asr_transcript` | `button_label` | `typed_text` | `selected_option`)
- **Side effects:** None.
- **Errors:**
  - `interpretation_failed`: could not extract usable signal.
  - `unsupported_response_mode`: interpreter cannot handle this mode.
  - `low_confidence`: extraction succeeded but confidence below threshold.
- **Timeout:** 2s.
- **Retries:** 0; low-confidence result is returned, not retried.
- **Ownership:** `ResponseInterpreter` owns `interpreted_payload` and `interpretation_type`; runtime owns timestamps and event emission.

## 5. DomainNormalizer

### 5.1 Responsibility

Canonicalize an interpreted response into a domain-specific normalized form.

### 5.2 Operations

#### `capabilities() -> NormalizerCapabilities`

- **Inputs:** None.
- **Outputs:**
  - `normalizer_id`
  - `normalizer_version`
  - `normalization_rules_version`
  - `content_types_supported`
- **Timeout:** 2s.

#### `normalize(response_interpretation: ResponseInterpretation) -> DomainNormalizedResponse`

- **Inputs:** `ResponseInterpretation` object.
- **Outputs:** `DomainNormalizedResponse` object:
  - `domain_normalized_response_id`
  - `response_window_id`
  - `response_interpretation_id`
  - `normalizer_id`
  - `normalizer_version`
  - `response_mode`
  - `normalized_payload`
  - `extracted_at` (component timestamp)
  - `uncertainty`
  - `input_observation_ids` (optional)
- **Side effects:** None.
- **Errors:**
  - `normalization_failed`: could not canonicalize.
  - `out_of_scope`: input outside supported domain subset.
- **Timeout:** 1s.
- **Retries:** 0; normalization is deterministic.
- **Ownership:** `DomainNormalizer` owns `normalized_payload`; runtime owns timestamps and events.

## 6. Evaluator

### 6.1 Responsibility

Compare a `DomainNormalizedResponse` against a domain-grounded expected answer and return an `Evaluation`.

### 6.2 Operations

#### `capabilities() -> EvaluatorCapabilities`

- **Inputs:** None.
- **Outputs:**
  - `evaluator_id`
  - `evaluator_version`
  - `response_modes_supported`
  - `answer_status_values`
  - `evaluation_status_values`
  - `error_categories_supported`
  - `abstention_reasons_supported`
- **Timeout:** 2s.

#### `evaluate(domain_normalized_response: DomainNormalizedResponse, expected_answer: ContentItem, context: TrialContext) -> Evaluation`

- **Inputs:**
  - `DomainNormalizedResponse` object
  - `ContentItem` expected answer (or `get_expected_answer` result)
  - `TrialContext`:
    - `trial_id`
    - `session_id`
    - `response_mode`
    - `protocol_version_id`
- **Outputs:** `Evaluation` object:
  - `evaluation_id`
  - `trial_id`
  - `evaluator_id`
  - `evaluator_version`
  - `domain_normalized_response_id`
  - `expected_content_item_id`
  - `answer_status`
  - `evaluation_status`
  - `correctness_credit` (optional)
  - `accepted_variant_id` (optional)
  - `evidence_group` (optional)
  - `scope_status` (optional)
  - `abstention_reason` (optional)
  - `failure_reason` (optional)
  - `error_category` (optional)
  - `evidence` (optional)
  - `confidence` (optional)
- **Side effects:** None.
- **Errors:**
  - `evaluation_failed`: engine exception, malformed output, version mismatch.
  - `abstained`: deliberate refusal to evaluate.
  - `out_of_scope`: expected item outside evaluator authority.
- **Timeout:** 2s.
- **Retries:** 0; engine failures must not be silently retried. Version mismatch triggers `protocol_terminated` or `evaluation_failed` depending on severity.
- **Ownership:** `Evaluator` owns `answer_status`, `evaluation_status`, `evidence`, `error_category`; runtime owns `evaluation_id` and timestamps.

## 7. Scheduler / ItemPolicy

### 7.1 Responsibility

Select and order trials/items based on protocol rules, item history, and evaluations.

### 7.2 Operations

#### `capabilities() -> SchedulerCapabilities`

- **Inputs:** None.
- **Outputs:**
  - `scheduler_id`
  - `scheduler_version`
  - `scheduling_strategies_supported`
  - `difficulty_dimensions_supported`
- **Timeout:** 2s.

#### `select_next(scheduling_context: SchedulingContext) -> ScheduleDecision`

- **Inputs:** `SchedulingContext`:
  - `protocol_version_id`
  - `current_block_id` (optional)
  - `trial_index`
  - `item_history` (list of outcomes, latencies, timestamps)
  - `protocol_policy` (spacing rules, difficulty bounds)
  - `session_duration_remaining` (optional)
  - `random_seed` (optional)
- **Outputs:** `ScheduleDecision` object:
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
  - `random_seed`
  - `selected_item_ids`
  - `decision_type`
  - `decision_status`
  - `abstention_reason` (optional)
  - `expected_difficulty_dimensions` (optional)
- **Side effects:** None.
- **Errors:**
  - `scheduling_failed`: cannot select next item.
  - `insufficient_history`: not enough evidence for requested policy.
- **Timeout:** 500ms.
- **Retries:** 0; deterministic.
- **Ownership:** `Scheduler` owns selection logic and `selected_item_ids`; runtime owns timestamps.

## 8. StateInferenceModel

### 8.1 Responsibility

Consume `Observation` and `SensorObservation` data and produce uncertain `StateEstimate`s. Optional and non-blocking.

### 8.2 Operations

#### `capabilities() -> ModelCapabilities`

- **Inputs:** None.
- **Outputs:**
  - `model_id`
  - `model_version`
  - `input_features`
  - `target_estimate_name`
  - `validation_status`
  - `deployment_status`
  - `calibration_population`
  - `uncertainty_method`
  - `known_confounds`
- **Timeout:** 2s.

#### `estimate(observations: list of Observation/SensorObservation) -> StateEstimate`

- **Inputs:** List of observations relevant to the model.
- **Outputs:** `StateEstimate` object:
  - `state_estimate_id`
  - `model_id`
  - `model_version`
  - `target_estimate_name`
  - `operational_definition`
  - `input_observation_ids`
  - `time_window`
  - `value`
  - `uncertainty`
  - `validation_status`
  - `deployment_status` (`exploratory_only` default)
  - `alternative_explanations`
  - `fallback_behavior_when_uncertain`
  - `calibration_population` (optional)
  - `known_confounds` (optional)
- **Side effects:** May emit `state_estimate_produced` event; must not change runtime state.
- **Errors:**
  - `model_failed`: could not produce estimate.
  - `insufficient_data`: not enough observations.
- **Timeout:** 5s.
- **Retries:** 0; failures logged but not retried in real time.
- **Ownership:** `StateInferenceModel` owns `value`, `uncertainty`, `alternative_explanations`; runtime owns event emission.

## 9. Boundary enforcement

- **Normative:** The runtime must reject a provider invocation that crosses boundaries (e.g., `Renderer` calling `Evaluator`).
- **Normative:** Provider operations must be idempotent where retries are allowed.
- **Normative:** Provider operations must not mutate the MPE runtime state; they return objects that the runtime appends as events.
- **Recommended:** Provider errors must be translated into events (`evaluation_failed`, `renderer_fallback`, `signal_quality_changed`, `safety_rule_triggered`) by the runtime.

## 10. Phase 4A scope note

This specification is complete for Phase 4A. It does not define:

- Concrete API protocol (REST, gRPC, in-process, etc.).
- Authentication or authorization between runtime and providers.
- Provider discovery/registry mechanism.
- Concrete media storage.

These are implementation decisions reserved for Phase 4B/4C.
