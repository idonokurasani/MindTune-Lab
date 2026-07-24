# MPE Adaptation Contract v1.1

## Audit basis

This contract implements `COGNITIVE_PROTOCOL_ONTOLOGY.md` §AdaptationDecision, `PROTOCOL_PRIMITIVES_CATALOG.md` §Prohibited primitives (`increase_difficulty` / `decrease_difficulty`, `adapt` without contract), `SOURCE_CLAIM_AUDIT.md` claims 10 (generic difficulty) and 11 (safe ranges), and `EXECUTIVE_SYNTHESIS.md` point 9 (adaptation is contractual and reversible).

## Principle

Every adaptation must be a contractual, reversible decision based on observable evidence. No adaptation is better than an unjustified adaptation.

## Permitted target dimensions in Phase 4A–4C

None. Phase 4 contains no adaptation. The runtime executes fixed protocols.

## Permitted target dimensions in Phase 5A (behavioral adaptation)

The following dimensions may be adapted, one at a time, by an explicit policy:

| Dimension | Type | Initial bounds | Evidence source |
|---|---|---|---|
| `pause_duration` | continuous seconds | 0.5–8.0 | response latency, omission rate, self-report |
| `speech_rate` | continuous multiplier | 0.7x–1.3x | self-report, completion latency |
| `response_deadline` | continuous seconds | 2.0–10.0 | response latency, omission rate |
| `new_item_rate` | continuous ratio | 0–0.5 | accuracy, item history |
| `review_insertion` | boolean or count | 0–3 extra reviews | accuracy, item history |
| `cue_specificity` | categorical | high/medium/low | accuracy, evaluator evidence |
| `response_mode` | categorical | button/voice/typed/recognition | device capability, accuracy per mode |

Bounds are **provisional configurable bounds**, not validated safe ranges. Each bound must carry:
- default value,
- min and max,
- status (`simulation_default` / `expert_reviewed` / `validated`),
- evidence grade,
- validation requirement,
- protocol override policy,
- user override policy.

## Prohibited dimensions in Phase 5A

- Any EEG-derived or sensor-derived dimension.
- Any `StateEstimate` as a target.
- Generic `difficulty_level`.
- Multi-dimension changes unless declared as a compound policy and evaluated separately.

## AdaptationDecision schema

Every adaptation decision must be an object with the following fields:

```text
AdaptationDecision
├── id
├── session_id
├── policy_id
├── policy_version
├── deployment_status            (exploratory_only / shadow_mode / limited_runtime / production_approved)
├── target_dimension             (typed dimension name)
├── current_value
├── proposed_value
├── allowed_bounds               { min, max, default, status, evidence_grade }
├── source_event_ids             (list of event ids that fed the decision)
├── evidence_record_ids          (optional list of EvidenceRecord ids)
├── aggregation_window           (time or trial count)
├── minimum_evidence             (boolean: was minimum evidence met?)
├── uncertainty_threshold        (boolean: was uncertainty threshold met?)
├── confidence                   (policy-internal confidence, 0.0–1.0)
├── cooldown                     (seconds or trials remaining before this policy can act again)
├── hysteresis                   (minimum change required to act)
├── maximum_step_size            (max single-step change)
├── rollback_rule                (condition under which the change is reversed)
├── abstention_rule              (condition under which policy returns NO_CHANGE)
├── decision                     (APPLY / NO_CHANGE_INSUFFICIENT_EVIDENCE / REVERSE / ABSTAIN)
├── reason                       (human-readable justification)
├── applied_at                   (if APPLY)
├── reversed_at                  (if REVERSE)
└── outcome_event_refs           (references for later efficacy analysis)
```

## Valid decisions

- `APPLY`: the change is within bounds, evidence and uncertainty thresholds are met, cooldown is satisfied, and the step size is acceptable.
- `NO_CHANGE_INSUFFICIENT_EVIDENCE`: evidence or uncertainty threshold not met; runtime continues unchanged.
- `REVERSE`: a previous change is rolled back because a rollback rule fired or because the change violated a bound or safety rule.
- `ABSTAIN`: the policy deliberately chooses not to act for a non-evidence reason (e.g., safety override, user preference, session phase).

## Evidence requirements

A policy may act only if it has:
- at least one relevant observable event,
- a minimum number of trials or time window (defined per policy),
- no unresolved `abstention` or `evaluation_abstained` events within the window unless the policy explicitly handles them.

## Uncertainty requirements

A policy must abstain if:
- the variance in the evidence is high,
- the relevant observations have low `overall_quality` or quality flags indicating high artifact/uncertainty,
- the `StateInferenceModel` (if used in later phases) has a confidence interval that crosses the action threshold,
- the learner has not completed enough trials to establish a baseline.

## Rollback rules

Every applied adaptation must have an automatic rollback rule:
- if the change causes worse outcomes over the next N trials,
- if a safety rule is triggered,
- if the learner manually overrides,
- if the session is paused or terminated.

## Hysteresis and cooldown

- `hysteresis`: a policy must not oscillate around a threshold. Proposed changes smaller than the hysteresis band must be ignored.
- `cooldown`: after a policy acts, it must wait at least the specified duration or trial count before acting again on the same dimension.

## Compound policies

A compound policy may change more than one dimension simultaneously. It must:
- declare all target dimensions explicitly,
- be versioned separately from single-dimension policies,
- be evaluated in `shadow_mode` before `limited_runtime` or `production_approved`,
- have its own rollback rule,
- have evidence that it outperforms the equivalent sequence of single-dimension policies.

## Sensor-informed policies (Phase 5C only)

A policy may use `StateEstimate` inputs only if:
- the `StateInferenceModel` is at least in `shadow_mode`,
- the model has shown, in offline validation, that it improves prediction of an actionable outcome (e.g., timeout or error) over behavioral/historical features alone,
- the policy still abstains when model uncertainty is high,
- the policy has a pure-behavioral fallback,
- the learner has consented to sensor use.

## Event logging

Every adaptation must produce at least one of:
- `adaptation_proposed`
- `adaptation_abstained`
- `adaptation_applied`
- `adaptation_reversed`

The event payload must include the full `AdaptationDecision` object or a checksum of it.

## Safety override

Safety rules always override adaptation policies. If a safety rule triggers, any pending adaptation is cancelled and the runtime executes the safety action.

## Example single-dimension policy (Phase 5A)

```text
Policy: extend_response_deadline_on_omissions
  target_dimension: response_deadline
  deployment_status: shadow_mode (initially)
  aggregation_window: 5 trials
  minimum_evidence: at least 3 non-timeout trials and 2 timeout trials in window
  uncertainty_threshold: false if response_deadline was already extended within last 3 trials
  current_value: 3.0s
  proposed_value: current + 0.5s
  allowed_bounds: {min: 2.0, max: 10.0, default: 3.0, status: simulation_default}
  hysteresis: 0.2s
  cooldown: 3 trials
  maximum_step_size: 0.5s
  rollback_rule: if accuracy does not improve over next 5 trials or safety rule fires
  decision: APPLY | NO_CHANGE_INSUFFICIENT_EVIDENCE
  reason: "omit timeout rate > 40% in window and no recent extension"
```

## Future EEG policy example (Phase 5C, exploratory)

```text
Policy: insert_review_if_drowsiness_risk_high
  target_dimension: review_insertion
  deployment_status: exploratory_only
  input_features: [sensor_observation.eeg_alpha_power, response_latency_trend]
  state_inference_model_id: drowsiness_risk_v0.1
  state_inference_deployment_status: exploratory_only
  decision: ABSTAIN (until model reaches shadow_mode and shows added predictive value)
```

This policy may not be activated in Phase 5A or 5B.

## Traceability

This contract implements `COGNITIVE_PROTOCOL_ONTOLOGY.md` §AdaptationDecision (contractual, reversible, no circular audit event reference, deployment statuses), `PROTOCOL_PRIMITIVES_CATALOG.md` §Prohibited primitives (rejection of generic `increase_difficulty` and `adapt` without contract), `SOURCE_CLAIM_AUDIT.md` claim 10 (generic difficulty rejected) and claim 11 ("safe ranges" reclassified as provisional bounds), and `EXECUTIVE_SYNTHESIS.md` point 9 (adaptation is contractual and reversible).
