# MPE Provider Boundaries v1.1

## Audit basis

This document implements `DOMAIN_INDEPENDENCE_MAP.md` (§What belongs in MPE core, §What belongs outside MPE core, §Provider contract table, §MPE core must not contain), `COGNITIVE_PROTOCOL_ONTOLOGY.md` §Response processing layers, and the rejection of v1.0 claims 6 (EEG semantics in core) and 9 (single Provider) in `SOURCE_CLAIM_AUDIT.md`.

## Principle

No single provider may render, observe, and evaluate. Each interface has a single, narrow responsibility. The MPE core orchestrates them and owns all timestamps, scheduling, and session lifecycle.

## Summary table

| Interface | Owns | Never owns | Produces | Consumes |
|---|---|---|---|---|
| `DomainProvider` | Domain content identity and metadata | Timing, correctness logic in core | `ContentItem`, domain-grounded expected answers | `item_id`, `content_type` requests |
| `Renderer` | Media generation | Content semantics, evaluation | `RenderedStimulus` | `StimulusRequest` |
| `ObservationProvider` | Raw input capture and quality flags | Response interpretation | `Observation` | Device/sensor inputs |
| `ResponseInterpreter` | Domain-agnostic extraction (ASR, button mapping, text) | Domain canonicalization or correctness | `ResponseInterpretation` | `CapturedResponse` |
| `DomainNormalizer` | Domain-specific canonicalization | Correctness verdict | `DomainNormalizedResponse` | `ResponseInterpretation` |
| `Evaluator` | Correctness verdict and evidence | Latency, scheduling | `Evaluation` | `DomainNormalizedResponse` + expected answer |
| `Scheduler` / `ItemPolicy` | Item selection and ordering | Content generation, evaluation | `ScheduleDecision` | `Evaluation` history, protocol rules |
| `StateInferenceModel` | Uncertain state estimates | Runtime control | `StateEstimate` | `Observation`, `SensorObservation` (offline or shadow) |

---

## 1. DomainProvider

### Responsibility

Supply domain-grounded learning material and expected answers. The MPE core treats this material as opaque references with metadata.

### Required operations

```text
domain_capabilities() ->
  {
    provider_id,
    provider_version,
    content_types_supported,
    metadata_schema_version,
    confidence_labels_supported,
    evaluation_modes_supported
  }

get_item(item_id) ->
  {
    content_item_id,
    provider_id,
    provider_version,
    content_type,
    checksum,
    surface_form,
    normalized_form,
    metadata,
    scope,
    confidence,
    abstention_status
  }

get_expected_answer(trial_context) ->
  {
    expected_content_item_id,
    accepted_variants,
    evidence_record,
    abstention_status
  }

get_prompt_for_mode(item_id, mode) ->
  {
    prompt_text,
    prompt_content_item_id,
    prosody_hint
  }
```

### Prohibited

- Must not compute latency.
- Must not access session history directly.
- Must not render audio.
- Must not emit cognitive-state claims.

### Hebrew example

The Hebrew `DomainProvider` returns:
- `surface_form` (vocalized Hebrew),
- `normalized_form` (strip-niqqud or canonical unvocalized),
- `form_key` (e.g., `past_first_mf_singular`),
- `root`, `binyan`, grammatical features,
- `accepted_variants` from `hebrew/orthography.py`,
- `evidence` from `hebrew/phase3/confidence.py`,
- `confidence`, `abstention_status`.

---

## 2. Renderer

### Responsibility

Convert a `StimulusRequest` into playable media. The Renderer knows how to call a TTS engine or load recorded audio, but knows nothing about Hebrew morphology or correctness.

### Required operations

```text
renderer_capabilities() ->
  {
    renderer_id,
    renderer_version,
    formats_supported,
    voices_supported,
    rate_range,
    latency_estimate_ms,
    streaming_support
  }

render(request: StimulusRequest) -> RenderedStimulus
```

### Prohibited

- Must not evaluate responses.
- Must not modify content semantics.
- Must not change `ContentItem` identity.
- Must not decide what to render next.

### Latency note

`RenderedStimulus.duration` is the media duration. Rendering latency is reported in `RenderedStimulus.rendered_at` minus `StimulusRequest.requested_at` but is not used for learner response latency.

---

## 3. ObservationProvider

### Responsibility

Capture raw learner or sensor input and report quality. It does not interpret responses.

### Required operations

```text
observation_capabilities() ->
  {
    provider_id,
    provider_version,
    observation_types_supported,
    device_id,
    quality_dimensions_supported,
    quality_flags_supported,
    quality_model_id,
    quality_model_version,
    latency_estimate_ms
  }

start_listening(window: ResponseWindow) -> void
stop_listening(window_id) -> void
poll() -> list of Observation
```

### Prohibited

- Must not compare input against expected answers.
- Must not emit `correct`/`incorrect`.
- Must not interpret mental activity.
- Must not block the runtime.

### Examples

- `ButtonObservationProvider`: button press/release.
- `MicrophoneObservationProvider`: audio onset/offset and optional voice activity detection.
- `KeyboardObservationProvider`: typed keystrokes.
- `EEGObservationProvider`: raw or preprocessed EEG samples with quality flags.

---

## 4. ResponseInterpreter

### Responsibility

Transform a `CapturedResponse` into a domain-agnostic interpreted form, such as an ASR transcript, a button label, or extracted typed text. It does not canonicalize domain spelling or judge correctness.

### Required operations

```text
response_interpreter_capabilities() ->
  {
    interpreter_id,
    interpreter_version,
    response_modes_supported,
    output_schema
  }

interpret(captured_response: CapturedResponse) -> ResponseInterpretation
```

### Prohibited

- Must not canonicalize to domain form.
- Must not compare against expected answers.
- Must not emit cognitive-state estimates.

### Hebrew example

A `HebrewResponseInterpreter` runs ASR on a voice sample and returns a transcript string. It does not strip niqqud, normalize spelling, or compare to the expected answer. That is the responsibility of the `HebrewDomainNormalizer` and `HebrewEvaluator`.

---

## 5. DomainNormalizer

### Responsibility

Canonicalize an interpreted response into a domain-specific normalized form. For Hebrew, this means stripping niqqud and applying `hebrew/orthography.py` rules. The normalizer is domain-specific, not provider-agnostic.

### Required operations

```text
domain_normalizer_capabilities() ->
  {
    normalizer_id,
    normalizer_version,
    normalization_rules_version,
    content_types_supported
  }

normalize(response_interpretation: ResponseInterpretation) -> DomainNormalizedResponse
```

### Prohibited

- Must not compare against expected answers.
- Must not emit cognitive-state estimates.
- Must not handle domain-agnostic extraction (that is `ResponseInterpreter`).

### Hebrew example

The `HebrewDomainNormalizer` takes an ASR transcript and returns a `DomainNormalizedResponse` with `normalized_payload` computed by `hebrew.normalization` and `hebrew.orthography`.

---

## 6. Evaluator

### Responsibility

Compare a `DomainNormalizedResponse` against a domain-grounded expected answer and return a verdict, evidence, and abstention.

### Required operations

```text
evaluator_capabilities() ->
  {
    evaluator_id,
    evaluator_version,
    response_modes_supported,
    answer_status_values,
    evaluation_status_values,
    error_categories_supported,
    abstention_reasons_supported
  }

evaluate(domain_normalized_response: DomainNormalizedResponse,
         expected_answer: ContentItem,
         context: TrialContext) -> Evaluation
```

### Prohibited

- Must not compute latency (runtime owns timestamps).
- Must not schedule future items.
- Must not access session state beyond the provided context.
- Must not emit cognitive-state estimates.
- Must not own response interpretation or domain normalization.

### Hebrew example

The Hebrew `Evaluator` uses `hebrew/phase3/confidence.py` and the validated forms from `data/hebrew/phase3/automatic_gold_100.json` to return:
- `answer_status`: `correct`, `incorrect`, `acceptable_variant`, `partially_correct`, `unevaluable`;
- `evaluation_status`: `completed`, `abstained`, `failed`, `out_of_scope`;
- `accepted_variant_id`: if a spelling variant is accepted with full correctness credit;
- `correctness_credit`: e.g., `1.0` for `correct`, `1.0` for `acceptable_variant`, `0.5` for `partially_correct`;
- `evidence_group`: reference to evidence groups;
- `error_category`: e.g., `tense`, `person`, `gender`, `spelling`;
- `confidence`: evaluation confidence;
- `abstention_reason`: if the input or expected answer is ambiguous.

---

## 7. Scheduler / ItemPolicy

### Responsibility

Select and order trials/items based on protocol rules, item history, and evaluations. It does not generate content or evaluate responses.

### Required operations

```text
scheduler_capabilities() ->
  {
    scheduler_id,
    scheduler_version,
    scheduling_strategies_supported,
    difficulty_dimensions_supported
  }

select_next(scheduling_context: SchedulingContext) -> ScheduleDecision
```

`SchedulingContext` includes:
- `protocol_version_id`,
- `current_block_id`,
- `trial_index`,
- `item_history` (outcomes, latencies, timestamps),
- `protocol_policy` (e.g., spacing rules, difficulty bounds),
- `session_duration_remaining`.

### Prohibited

- Must not interpret sensor features.
- Must not use EEG state estimates in Phase 4.
- Must not block waiting for observations.
- Must not render media.

### Note

The `Scheduler` may be informed by `AdaptationDecision` objects (e.g., a decision to `insert_review`), but the `Scheduler` decides which specific item to review.

---

## 8. StateInferenceModel

### Responsibility

Consume `Observation` and `SensorObservation` data and produce uncertain `StateEstimate`s. It is optional, versioned, and never controls the runtime.

### Required operations

```text
model_capabilities() ->
  {
    model_id,
    model_version,
    input_features,
    target_estimate_name,
    validation_status,
    deployment_status,
    calibration_population,
    uncertainty_method,
    known_confounds
  }

estimate(observations: list of Observation/SensorObservation) -> StateEstimate
```

### Deployment status rules

- `exploratory_only`: may run offline or in shadow; no runtime use.
- `shadow_mode`: may produce estimates in real time but they are logged, not acted upon.
- `limited_runtime`: may inform adaptation under explicit protocol policy and study protocol.
- `production_approved`: may inform adaptation broadly; requires documented evidence.

For v1.1, all `StateInferenceModel`s default to `exploratory_only` and must be reviewed before `shadow_mode`.

### Prohibited

- Must not determine correctness.
- Must not decide session flow.
- Must not block waiting for state.
- Must not assign semantic meaning to covert mental activity.
- Must not be used as a hard synchronization condition.

### EEG-specific rule

An EEG `StateInferenceModel` must not claim that a specific EEG feature means `attention`, `arousal`, `load`, etc. The model must define its `target_estimate_name` as a narrow risk-style estimate (e.g., `estimated_drowsiness_risk`) with explicit operational definition and alternative explanations.

---

## Boundary enforcement

- The runtime validates that each provider implements only its assigned interface.
- A `Renderer` cannot call an `Evaluator`.
- An `ObservationProvider` cannot call a `ResponseInterpreter`, `DomainNormalizer`, or `Evaluator`.
- A `ResponseInterpreter` cannot call a `DomainNormalizer` or `Evaluator`.
- A `DomainNormalizer` cannot call an `Evaluator`.
- An `Evaluator` cannot call a `StateInferenceModel` or `Scheduler`.
- A `Scheduler` cannot call an `ObservationProvider`.
- Crossing boundaries requires explicit event logging and is allowed only for diagnostic tooling, not runtime control.

## Traceability

This provider decomposition implements `DOMAIN_INDEPENDENCE_MAP.md` §What belongs in MPE core, §What belongs outside MPE core, and §Provider contract table. It also implements `COGNITIVE_PROTOCOL_ONTOLOGY.md` §Response processing layers (`Observation` → `CapturedResponse` → `ResponseInterpretation` → `DomainNormalizedResponse` → `Evaluation`) and `SOURCE_CLAIM_AUDIT.md` claim 9 (single Provider rejected) and claim 6 (EEG semantics removed from core).
