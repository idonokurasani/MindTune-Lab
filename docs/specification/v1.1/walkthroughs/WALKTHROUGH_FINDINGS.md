# Phase 4A.5 Walkthrough Findings

## 1. Executive summary

Three vertical-slice walkthroughs were executed against the approved MPE v1.1 architecture and Phase 4A implementation specification:

1. Hebrew vocabulary recall (`overt_recall`, `response_requirement: required`, typed response).
2. Hebrew morphology recognition (`perceptual_discrimination`, `response_requirement: required`, typed label response).
3. Exposure-only learning (`language_prediction_retrieval`, `response_requirement: none`, no observable response).

No approved-specification conflict or implementation impossibility was found. All slices can be expressed using existing objects, events, enums, provider contracts, and state machines. Minor payload-completeness issues were identified and corrected during the walkthrough; none require an ADR.

## 2. Findings by architecture-stress category

| Category | Finding | Severity | Status |
|---|---|---|---|
| Missing object | None. All required objects exist for all three slices. | — | — |
| Missing event | None. All required events exist; exposure correctly omits response-pipeline events because `response_requirement: none` implies no `ResponseWindow`. | — | — |
| Undefined identifier | None. All identifiers used are in `MPE_CANONICAL_IDENTIFIER_REGISTRY.md`. | — | — |
| Ambiguous enum | None. All enum values are canonical and unambiguous. | — | — |
| Illegal state transition | None. All transitions are consistent with `RUNTIME_STATE_MACHINE.md` and `MPE_CANONICAL_ENUM_REGISTRY.md`. | — | — |
| Provider-boundary violation | None. `HebrewRenderer` only renders; `HebrewDomainNormalizer` only normalizes; `HebrewEvaluator` only evaluates. MPE core never computes Hebrew correctness. | — | — |
| Replay gap | None. Every object is either an event or derived from events. `Outcome` is recomputed from the event stream. | — | — |
| Persistence ambiguity | None. `PERSISTENCE_BOUNDARIES.md` classifications are consistent across slices. Objects that are not created (e.g., `CapturedResponse` in exposure) are not persisted. | — | — |
| Safety ambiguity | None. Safety rules can trigger at any time and override flow; safety transitions are defined. | — | — |
| Hebrew authority leakage | None. All Hebrew-specific correctness decisions are delegated to `HebrewEvaluator` and derived from `ContentItem` metadata. | — | — |
| Hidden implementation decision | None. The decision to open or skip a `ResponseWindow` is explicit in `Trial.response_requirement` and `Instruction.observable_response_expected`. | — | — |

## 3. Payload-completeness corrections made

During the walkthrough, the following specification-compliant but previously omitted fields were added to event payloads:

| Field | Reason | Where added |
|---|---|---|
| `Instruction.allotted_duration` (or `open_until_response`) | Required by `MPE_OBJECT_MODEL_V1_1.md` §Instruction for `REQUEST_OVERT_RESPONSE` instructions. | Vocab recall, morphology recognition |
| `Instruction.target_operation` | Required by `MPE_OBJECT_MODEL_V1_1.md` §Instruction. | Vocab recall, morphology recognition, exposure |
| `StimulusRequest.requested_at`, `scheduled_for` | Required by `MPE_OBJECT_MODEL_V1_1.md` §StimulusRequest. | All three slices |
| `RenderedStimulus.renderer_version`, `rendered_at` | Required by `MPE_OBJECT_MODEL_V1_1.md` §RenderedStimulus. | All three slices |
| `ResponseWindow.timeout_policy` | Required by `MPE_OBJECT_MODEL_V1_1.md` §ResponseWindow. | Vocab recall, morphology recognition |
| `Observation.provider_id`, `provider_version`, `quality_model_id`, `quality_model_version` | Required by `MPE_OBJECT_MODEL_V1_1.md` §Observation. | Vocab recall, morphology recognition |
| `CapturedResponse.device_provenance`, `quality_flags` | Required by `MPE_OBJECT_MODEL_V1_1.md` §CapturedResponse. | Vocab recall, morphology recognition |
| `ResponseInterpretation.response_window_id`, `interpreter_version` | Required by `MPE_OBJECT_MODEL_V1_1.md` §ResponseInterpretation. | Vocab recall, morphology recognition |
| `DomainNormalizedResponse.response_window_id`, `normalizer_version`, `response_mode` | Required by `MPE_OBJECT_MODEL_V1_1.md` §DomainNormalizedResponse. | Vocab recall, morphology recognition |
| `Evaluation.evaluator_version` | Required by `MPE_OBJECT_MODEL_V1_1.md` §Evaluation. | Vocab recall, morphology recognition |
| `ScheduleDecision.decision_status`, `source_event_ids` | Required by `MPE_OBJECT_MODEL_V1_1.md` §ScheduleDecision. | All three slices |
| `BlockExecution.block_type` for exposure | `acquisition` is not a valid `block_type` enum value; `practice` is. | Exposure-only |

These are documentation corrections within the approved specification, not architectural changes.

## 4. ADR proposals

No ADR is proposed.

Per the Phase 4A.5 instructions, an ADR is only required for a genuine approved-specification conflict or implementation impossibility. The walkthroughs revealed no such conflict. All issues were payload-completeness or enum-value mistakes in the walkthrough drafts, not in the underlying architecture or Phase 4A specification.

## 5. Residual questions

None. The three vertical slices demonstrate sufficient coverage for Phase 4B to begin for the Hebrew recall, morphology recognition, and exposure-only use cases.

## 6. Recommendations

- Proceed to Phase 4B implementation for the three walked-through use cases.
- Ensure that Phase 4B event validation enforces the required payload fields identified above.
- Re-run these walkthroughs (or a generated test suite based on them) after the first Phase 4B build to confirm runtime behavior matches the architecture.
