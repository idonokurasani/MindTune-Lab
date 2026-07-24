# MPE Hebrew Provider Contract v1.1

## Audit basis

This contract implements `DOMAIN_INDEPENDENCE_MAP.md` (Hebrew outside core), `COGNITIVE_PROTOCOL_ONTOLOGY.md` §Response processing layers, §Evaluation, and `SOURCE_CLAIM_AUDIT.md` claims 14–28 (Phase 3 Hebrew engine as domain authority) plus claim 6 (EEG semantics removed from core).

## Scope

This contract defines the exact interface between the MindTune Protocol Engine and the completed Phase 3 Hebrew engine. MPE must consume Hebrew outputs; it must not duplicate Hebrew morphology, binyan logic, niqqud handling, or lexical evidence rules.

## Hebrew engine authority

The following remain inside the Hebrew engine:

- Root extraction and classification.
- Binyan pattern mapping.
- Normative unvocalized spelling (`hebrew/orthography.py`).
- Phonology and stress (`hebrew/phonology.py`).
- Verb selection and coverage (`hebrew/phase3/selection.py`).
- Evidence and confidence classification (`hebrew/phase3/confidence.py`).
- Differential and benchmark validation (`hebrew/phase3/differential.py`, `hebrew/phase3/benchmark.py`).
- Correctness and variant acceptance.

MPE core must not perform any of these operations.

## Provider roles

The Hebrew engine participates through three narrow interfaces:

1. `HebrewDomainProvider` — implements `DomainProvider`.
2. `HebrewRenderer` — implements `Renderer` (uses existing TTS/SSML pipeline).
3. `HebrewEvaluator` — implements `Evaluator`.

There is no single "Hebrew Provider".

---

## 1. HebrewDomainProvider

### Required outputs for each `ContentItem`

```text
ContentItem
├── content_item_id             (stable id)
├── provider_id                 = "hebrew"
├── provider_version            (engine version or git sha)
├── content_type                ("verb_form", "word", "phrase")
├── surface_form                (vocalized Hebrew, e.g., "לִלְמוֹד")
├── normalized_form             (canonical unvocalized from orthography, e.g., "ללמוד")
├── accepted_variants           (list of accepted surface/normalized forms, each with an id)
├── form_key                    (e.g., "past_first_mf_singular")
├── root                        (e.g., "למד")
├── binyan                      (e.g., "PA'AL")
├── grammatical_features        {person, gender, number, tense, ...}
├── pronunciation_metadata      (from phonology, advisory)
│     ├── phonemic
│     ├── practical
│     ├── lexical_stress
│     ├── unresolved            (boolean)
│     └── advisory_note
├── evidence_group              (e.g., "eran_tomer_derivative", "verb_inflector_fresh_pass", "corpus_attestation")
├── confidence                  (from confidence.py)
├── status                      ("verified_consensus", "high_confidence_candidate", "unresolved", "rejected")
├── abstention_status           (true/false)
├── scope                       ("phase3_100_verb_subset" or similar)
└── engine_version              (Phase 3 engine version)
```

### Content item lookup

```text
get_item_by_id(item_id) -> ContentItem
get_items_by_form(surface_or_normalized_form, content_type) -> list of ContentItem
get_items_by_root_and_form_key(root, binyan, form_key) -> ContentItem
get_prompt(item_id, mode) -> {prompt_text, prompt_content_item_id, prosody_hint}
```

`mode` may be `hear`, `recall_cue_native`, `recall_cue_target`, `morphology_cue`.

### Expected answer

For a recall trial, the Hebrew engine provides the expected answer:

```text
get_expected_answer(cue_item_id, target_form_key) ->
  {
    expected_content_item_id,
    surface_form,
    normalized_form,
    accepted_variants,
    evidence,
    confidence,
    status,
    abstention_status,
    scope
  }
```

MPE must not compute this itself.

---

## 2. HebrewRenderer

The Hebrew `Renderer` converts `ContentItem` or `prompt_text` into audio using the existing TTS pipeline (e.g., Azure, Piper, HebTTS, BlueTTS). It is provider-agnostic in principle but configured for Hebrew.

```text
render(request: StimulusRequest) -> RenderedStimulus
```

`StimulusRequest` may include:
- `content_item_id` (preferred),
- or `prompt_text` (for non-item prompts like instructions),
- `voice_id`,
- `rate`,
- `prosody_hint`.

The renderer must respect the `pronunciation_metadata` only if the TTS engine supports it. If not, it must fall back to `surface_form` and log a `renderer_fallback` event.

---

## 3. HebrewEvaluator

### Inputs

```text
DomainNormalizedResponse
├── domain_normalized_response_id
├── response_mode       (button / voice / typed / recognition)
├── normalized_payload  (button label, transcribed text, typed text, selected option)
├── extracted_at        (component timestamp, non-authoritative)
└── uncertainty

ExpectedAnswer
├── expected_content_item_id
├── surface_form
├── normalized_form
├── accepted_variants   (list of {variant_id, surface_form, normalized_form, evidence})
├── evidence
├── status
├── abstention_status
└── scope
```

The `HebrewEvaluator` does **not** own latency. Latency is derived by the runtime from `response_window_opened.timestamp` and `response_completed.timestamp`.

### Outputs

```text
Evaluation
├── evaluation_id
├── answer_status       (correct / incorrect / acceptable_variant / partially_correct / unevaluable)
├── evaluation_status   (completed / abstained / failed / out_of_scope)
├── correctness_credit  (0.0–1.0)
├── accepted_variant_id (if answer_status == acceptable_variant and a variant was accepted with full credit)
├── evidence_group      (Hebrew engine evidence classification)
├── scope_status        (verified_consensus / high_confidence_candidate / unresolved / rejected)
├── evidence            (domain-specific evidence record)
├── confidence          (evaluation confidence, not learner state)
├── abstention_reason   (if evaluation_status == abstained)
├── failure_reason      (if evaluation_status == failed)
└── error_category      (optional: tense, person, gender, number, spelling, binyan, out_of_scope, engine_error, version_mismatch)
```

### Answer status semantics

| `answer_status` | Meaning | `evaluation_status` | MPE action |
|---|---|---|---|
| `correct` | The response matches the expected answer or an accepted variant with full correctness credit. | `completed` | Deliver confirmatory feedback or continue. |
| `incorrect` | The response is a known Hebrew form but not the expected one, or is clearly wrong. | `completed` | Deliver correct-answer feedback. |
| `acceptable_variant` | The response matches an accepted variant; `accepted_variant_id` is non-null and `correctness_credit` is 1.0 unless the policy gives partial credit. | `completed` | Treat as `correct` for scoring but record the variant. |
| `partially_correct` | The response matches a related variant but not the target; `correctness_credit` is between 0.0 and 1.0. | `completed` | Deliver feedback with variant information. |
| `unevaluable` | The Hebrew engine cannot determine correctness. | `abstained` or `failed` | MPE must not fabricate a correctness score. |

### Evaluation status semantics

| `evaluation_status` | Meaning | MPE action |
|---|---|---|
| `completed` | The `Evaluator` returned a non-abstained `answer_status`. | Use `answer_status` and `correctness_credit` for feedback and scheduling. |
| `abstained` | The `Evaluator` deliberately declined to judge (e.g., unknown input, ambiguous form). | Do not score; log the event and continue with neutral feedback or re-prompt. |
| `failed` | The `Evaluator` encountered an engine error or version mismatch. | Log `evaluation_failed`; terminate the trial gracefully if the error is unrecoverable. |
| `out_of_scope` | The expected item is outside the Phase 3 100-verb subset or the engine refuses to evaluate. | Do not score; do not present the item as authoritative without human review. |

### MPE handling categories

MPE must handle each `Evaluation` and `ContentItem` state as follows:

#### verified result

- `ContentItem.status == verified_consensus` and `ContentItem.abstention_status == false`.
- `Evaluation.evaluation_status == completed` and `Evaluation.answer_status` is `correct`, `incorrect`, `acceptable_variant`, or `partially_correct`.
- MPE may treat `correct` and `acceptable_variant` (with full `correctness_credit`) as authoritative for scoring.
- Pronunciation metadata is advisory.

#### acceptable variant with full credit

- `Evaluation.answer_status == acceptable_variant` and `Evaluation.correctness_credit == 1.0`.
- `Evaluation.accepted_variant_id` is non-null.
- MPE treats as `correct` for scoring and records the variant id.
- Feedback may mention the target form.

#### acceptable variant with partial credit

- `Evaluation.answer_status == partially_correct` and `0.0 < Evaluation.correctness_credit < 1.0`.
- `Evaluation.accepted_variant_id` may be null.
- MPE uses `correctness_credit` for scoring and provides feedback that distinguishes the partial match.

#### advisory pronunciation

- `ContentItem.pronunciation_metadata.unresolved == true` or `Evaluation.evidence` flags pronunciation as advisory.
- MPE must not reject a `correct` response based on pronunciation.
- MPE may present the advisory pronunciation as a learning note.

#### unknown response

- `Evaluation.answer_status == unevaluable` and `Evaluation.evaluation_status == abstained` and `Evaluation.abstention_reason == unknown_input`.
- MPE must not score. It may ask the learner to repeat or provide neutral feedback.

#### out-of-scope verb

- `ContentItem.scope != "phase3_100_verb_subset"` or `ContentItem.status == unresolved`/`rejected` or `Evaluation.evaluation_status == out_of_scope`.
- MPE must not present the item as authoritative without human review.
- Phase 4C must be restricted to the 100-verb subset.

#### low-confidence result

- `ContentItem.status == high_confidence_candidate` or `Evaluation.confidence < threshold`.
- MPE may present but must flag the item and `Evaluation` as provisional and avoid using it as a hard benchmark.

#### normalization ambiguity

- The `ResponseInterpreter` or `DomainNormalizer` cannot produce a single normalized form.
- MPE must log a `domain_response_normalized` event with high `uncertainty` and may ask the learner to repeat.

#### engine abstention

- `Evaluation.evaluation_status == abstained`.
- MPE must not fabricate a correctness score.
- MPE may log the event and continue with a neutral prompt.

#### engine failure

- Hebrew provider raises an exception or returns malformed output.
- `Evaluation.evaluation_status == failed` and `Evaluation.error_category == engine_error`.
- MPE must log an `evaluation_failed` event and, if unrecoverable, a `safety_rule_triggered` or `protocol_terminated` event, gracefully terminate the trial or session, and never crash.

#### version mismatch

- `ContentItem.engine_version` does not match the registered `HebrewEvaluator` version.
- `Evaluation.evaluation_status == failed` and `Evaluation.error_category == version_mismatch`.
- MPE must refuse to evaluate and log a `protocol_terminated` or `session_cancelled` event.

#### unsupported grammatical form

- The learner produces a form that the Phase 3 engine does not cover (e.g., weak/hollow roots not yet tested, imperative not validated).
- `Evaluation.evaluation_status == abstained` or `out_of_scope`.
- MPE must not treat the unsupported form as incorrect without domain review.

## Scope restriction

Phase 4C must only use items from the 100-verb subset (`data/hebrew/phase3/automatic_gold_100.json`) with `status == verified_consensus` or `high_confidence_candidate`. Items marked `unresolved` or `rejected` must be excluded from production protocols.

## Traceability

This contract implements `DOMAIN_INDEPENDENCE_MAP.md` (Hebrew outside MPE core), `COGNITIVE_PROTOCOL_ONTOLOGY.md` §Response processing layers and §Evaluation (answer/evaluation status separation, `acceptable_variant`, `partially_correct`), and `SOURCE_CLAIM_AUDIT.md` claims 14–28 (Phase 3 Hebrew engine as domain authority). It operationalizes `OPEN_QUESTIONS_AND_DECISIONS.md` #4 and #6 (Hebrew error categories, variant scoring) as provisional defaults pending further evidence.

All Hebrew outputs consumed by MPE must include `engine_version`, `provider_version`, and `evidence_group` so that every `Evaluation` can be traced back to the Phase 3 engine and its confidence classification.
