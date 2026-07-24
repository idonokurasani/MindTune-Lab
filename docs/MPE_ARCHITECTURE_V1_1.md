# MindTune Protocol Engine
## Technical & Cognitive Architecture v1.1

**Status:** Revised blueprint / pre-implementation  
**Scope:** A behaviorally grounded, deterministic, staged architecture for Adaptive Cognitive Protocols.  
**Audit basis:** `docs/research/mpe_ontology_audit_v1/COGNITIVE_PROTOCOL_ONTOLOGY.md` (§Core entities, §Instruction, §Response processing layers, §Evaluation, §Feedback, §ScheduleDecision, §AdaptationDecision, §LatentEstimate, §Safety, §Outcome), `PROTOCOL_PRIMITIVES_CATALOG.md` (§Allowed/Prohibited primitives, §Trial role sequence examples), `SOURCE_CLAIM_AUDIT.md`/`.csv` (claims 1, 4–13 rejected; 14–28 accepted), `DOMAIN_INDEPENDENCE_MAP.md` (§What belongs in MPE core/outside, §Provider contract table), `OPEN_QUESTIONS_AND_DECISIONS.md` (closed decisions), `EXECUTIVE_SYNTHESIS.md` (§What must change, §Key risks), `METHODOLOGY_AND_LIMITATIONS.md` (§Methodology, §Limitations), `PROTOCOL_DECOMPOSITION_MATRIX.csv` (all rows), `docs/MPE_V1_0_CRITICAL_REVIEW.md`, `data/hebrew/phase3/PHASE_3_FINAL_REPORT.md`.

---

## 1. Vision

MindTune Lab explores the hypothesis that some learning is most effective with minimal visual stimulation, auditory guidance, internal speech, and regulated cognitive load. The active session should be eyes-free and audio-driven; the screen is used only for setup, selection, and review.

This is an experimental hypothesis, not a validated fact. It is quarantined in the **Product positioning hypotheses** section below.

### Product positioning hypotheses — not validated

- MindTune may become a platform for Adaptive Cognitive Protocols.
- It may be the first such platform in a particular segment.
- These are product and market hypotheses, not technical architecture axioms.

## 2. Philosophy

- **Screen is secondary.** The active session is audio-driven.
- **Protocol is a structured cognitive sequence.** It is not an audio file, playlist, or meditation.
- **Learning is a regulated state.** The system aims to help the learner maintain a productive cognitive state; whether a single optimal state exists is an experimental hypothesis, not an architecture axiom. Response speed is not the sole objective.
- **Internal speech is a mechanism, not an observable.** The system can instruct covert operations; it cannot observe them.
- **EEG is one signal among many.** It is never a correctness detector or thought reader.

## 3. Scientific assumptions (as hypotheses)

The following are explicit, falsifiable assumptions. They are stated to be tested, not assumed:

1. State-dependent learning: arousal, attention, fatigue, and load modulate encoding.
2. Prediction and error correction: generating a prediction before feedback may strengthen memory.
3. Internal rehearsal: sub-vocal or mental rehearsal may improve retention.
4. Desirable difficulty: slightly harder retrieval may produce stronger learning.
5. Spaced and interleaved practice may outperform massed practice.
6. Reduced visual input may deepen auditory/internal processing.
7. EEG can correlate with state but cannot decode semantic content or correctness.
8. Adaptive timing, rate, and repetition may help maintain a productive state.

Each protocol must record which assumptions it relies on and their validation status.

## 4. Cognitive model

### 4.1 Generic trial structure

The canonical trial structure is:

```text
Stimulus or Cue
-> Learner Operation
-> Response Window
-> Observation
-> CapturedResponse
-> ResponseInterpretation
-> DomainNormalizedResponse
-> Evaluation
-> Feedback
-> Scheduling or Adaptation Decision
-> Next Trial
```

### 4.2 Specializations

- **Language Prediction-Retrieval Loop:** present cue → instruct covert prediction → present correct answer → knowledge feedback.
- **Perceptual Discrimination:** present A and B → request same/different judgment → performance feedback.
- **Overt Recall:** present cue → request overt response → evaluate → knowledge feedback.
- **Morphology Generation:** present root + features → request inflected form → evaluate → performance + knowledge feedback.
- **Sequence / Working Memory:** present sequence → request recall → evaluate → performance feedback.

The prediction-retrieval loop is one valid specialization, not a universal model. See `docs/research/mpe_ontology_audit_v1/PROTOCOL_DECOMPOSITION_MATRIX.csv` for more.

### 4.3 Cognitive state as estimate

Cognitive states are not directly measured. `StateEstimate` (or `LatentEstimate`) objects carry:

- `model_id` and `model_version`
- `target_estimate_name` (narrow, e.g., `estimated_drowsiness_risk`)
- `operational_definition`
- `input_observations`
- `time_window`
- `value` and `uncertainty`
- `validation_status`
- `deployment_status` (`exploratory_only` default)
- `alternative_explanations`
- `fallback_behavior_when_uncertain`

They are never blocking conditions. See `MPE_OBJECT_MODEL_V1_1.md` and `COGNITIVE_PROTOCOL_ONTOLOGY.md`.

## 5. Protocol object model

The object model is fully defined in `MPE_OBJECT_MODEL_V1_1.md`. Key points:

- `Program` and `Protocol` are logical identities.
- `ProgramVersion` and `ProtocolVersion` are immutable executable definitions.
- `Session` references exact `ProgramVersion` and `ProtocolVersion` checksums.
- `Trial` has `response_requirement` (`required` | `optional` | `none`) and optional `accepted_response_modes`.
- `Instruction` has `instruction_payload` (never null), `target_operation`, `allotted_duration`, `observable_response_expected`.
- Response processing is layered: `Observation` → `CapturedResponse` → `ResponseInterpretation` → `DomainNormalizedResponse` → `Evaluation`.
- `Evaluation` separates `answer_status` and `evaluation_status`.
- `AdaptationDecision` is contractual and reversible; `audit_event_id` removed.
- `ScheduleDecision` is fully reproducible with policy, candidates, selection rule, tie-break, random seed, and excluded candidates.
- `Outcome` latency metrics are stratified, not aggregated into a global mean.
- Safety instructions are separate from `FeedbackEvent`.

## 6. Protocol primitives

The primitives catalog is in `docs/research/mpe_ontology_audit_v1/PROTOCOL_PRIMITIVES_CATALOG.md`.

### 6.1 Allowed core primitives

- `PRESENT_STIMULUS`
- `INSTRUCT_COVERT_RETRIEVAL` / `REHEARSAL` / `IMAGERY`
- `REQUEST_OVERT_RESPONSE`
- `REQUEST_CONFIDENCE_RATING`
- `REQUEST_SELF_REPORT`
- `OPEN_RESPONSE_WINDOW`
- `WAIT_DURATION`
- `WAIT_FOR_RESPONSE`
- `WAIT_FOR_SIGNAL_QUALITY`
- `CHECK_CONTINUATION_CONDITION`
- `INSERT_RECOVERY`
- `OFFER_SESSION_END`
- `DELIVER_KNOWLEDGE_FEEDBACK` / `PERFORMANCE_FEEDBACK` / `METACOGNITIVE_PROMPT`
- `DELIVER_SAFETY_INSTRUCTION`
- `SELECT_NEXT_ITEM`
- `NO_CHANGE_INSUFFICIENT_EVIDENCE` (Phase 5A+)

### 6.2 Prohibited primitives

- `expect(mental_*)`
- `wait_for_state(target, timeout)`
- `increase_difficulty()` / `decrease_difficulty()` (replaced by typed dimensions)
- any EEG-semantic primitive in core

### 6.3 Example: Vocabulary encoding (no response)

```yaml
trials:
  - task_family: language_prediction_retrieval
    response_requirement: none
    roles:
      - PRESENT_STIMULUS: "לִלְמוֹד"
      - INSTRUCT_COVERT_RETRIEVAL:
          instruction_payload: "Think of the Italian meaning"
          target_operation: retrieve_italian_meaning
          allotted_duration: 3.0
          observable_response_expected: false
      - WAIT_DURATION: 1.5
      - PRESENT_STIMULUS: "imparare"
      - DELIVER_KNOWLEDGE_FEEDBACK: "לִלְמוֹד means imparare"
```

### 6.4 Example: Vocabulary recall with observable probe

```yaml
trials:
  - task_family: overt_recall
    response_requirement: required
    accepted_response_modes: [button, voice, typed]
    roles:
      - PRESENT_STIMULUS: "imparare"
      - REQUEST_OVERT_RESPONSE: "Say or type the Hebrew word"
      - OPEN_RESPONSE_WINDOW:
          deadline: 5.0
      - WAIT_FOR_RESPONSE
      - DELIVER_KNOWLEDGE_FEEDBACK: "לִלְמוֹד"
```

## 7. Runtime execution engine

The runtime is defined by `MPE_EVENT_MODEL_V1_1.md` and `MPE_PHASE_4_IMPLEMENTATION_PLAN.md`.

- Event-driven scheduler with monotonic session clock.
- Runtime owns all timestamps.
- Immutable event stream is source of truth.
- Deterministic replay with fixed seed and captured observations.
- Single-threaded scheduler; providers run asynchronously.
- Safety rules override all flow.
- No blocking on EEG or state estimates.

## 8. Adaptive engine

### 8.1 Inputs

Primary inputs are behavioral:

- explicit learner responses,
- response latency,
- completion latency,
- item history,
- self-report,
- time-on-task,
- technical signal quality.

### 8.2 State inference

Sensor observations are generic `SensorObservation` objects. Interpretation is done by versioned `StateInferenceModel`s that default to `exploratory_only`. MPE core does not know what an EEG feature means.

### 8.3 Controllable parameters

Parameters are typed dimensions such as `pause_duration`, `speech_rate`, `response_deadline`, `new_item_rate`, `review_insertion`, `cue_specificity`, `response_mode`. Each has provisional configurable bounds with evidence grade and validation requirement.

### 8.4 Adaptation contract

Every adaptation is an `AdaptationDecision` with:

- policy id/version,
- deployment status,
- target dimension,
- current and proposed value,
- allowed bounds,
- evidence inputs,
- minimum evidence and uncertainty thresholds,
- cooldown, hysteresis, max step size,
- rollback and abstention rules,
- decision (`APPLY` | `NO_CHANGE_INSUFFICIENT_EVIDENCE` | `REVERSE` | `ABSTAIN`).

Shadow-mode models may not apply runtime changes. See `MPE_ADAPTATION_CONTRACT.md`.

## 9. Audio generation

Audio is generated by `Renderer` providers. MPE sends `StimulusRequest` objects and receives `RenderedStimulus` objects with duration and provenance. The engine is provider-agnostic.

## 10. Hebrew integration

The completed Phase 3 Hebrew engine is wrapped as:

- `HebrewDomainProvider` for content and expected answers,
- `HebrewResponseInterpreter` for ASR/transcript extraction (if used),
- `HebrewDomainNormalizer` for spelling/orthographic canonicalization,
- `HebrewEvaluator` for correctness, evidence, and abstention.

MPE core does not evaluate Hebrew correctness. See `MPE_HEBREW_PROVIDER_CONTRACT.md`.

## 11. EEG integration

- EEG is optional.
- Raw EEG is stored only with consent.
- `EEGObservationProvider` produces generic `SensorObservation` objects.
- `StateInferenceModel`s consume these offline (Phase 5B) or in shadow mode.
- No real-time control by EEG in Phase 4 or 5A.
- No EEG semantics in MPE core.

## 12. Performance metrics

Phase 4 and 5A metrics prioritize:

- accuracy,
- response latency,
- completion latency,
- omission rate,
- timeout count,
- hint use,
- confidence calibration,
- item retention (delayed recall),
- item stability,
- coverage,
- dropout,
- early termination,
- perceived difficulty/fatigue (self-report),
- technical signal quality,
- protocol adherence,
- adaptation count and reversal count.

`time_in_target_state` is an experimental diagnostic only. Latency metrics are stratified by task, response mode, trial role, and item class. See `MPE_OBJECT_MODEL_V1_1.md` Outcome.

## 13. Data model

All runtime facts are immutable events. Derived objects (`Session`, `Outcome`) are queries over the event stream. Sensitive events (raw audio, EEG, free-text self-report) are flagged, encrypted, and consent-gated.

## 14. Extensibility

Domains are added by implementing the provider interfaces. MPE core remains unchanged. New `StateInferenceModel`s can be added without altering the runtime. New protocol families are added as `TaskDefinition`s and `ProtocolVersion`s.

## 15. Future protocol families

Anticipated families include language, music, memory, executive function, meditation, mental arithmetic, working memory, and cognitive rehabilitation. Each family requires its own domain providers and evidence base. Claims beyond `trained_task_performance` require separate validation.

## 16. Risks

Key risks are in `MPE_RISK_REGISTER_V1_1.md`:

- over-adaptation,
- false confidence in EEG/sensors,
- covert activity treated as observable,
- generic difficulty masking causes,
- provisional bounds treated as validated,
- Hebrew logic leaking into core,
- timestamp ownership errors,
- event stream irreproducibility,
- DSL scope creep,
- safety failure.

## 17. Validation methodology

- Simulation with synthetic learners.
- Replay of historical sessions.
- Component tests for each provider and the runtime.
- Expert review by cognitive scientists, linguists, and HCI designers.
- Controlled A/B studies.
- Pre-registered hypotheses and blinded analysis.

## 18. Research roadmap

- **Near-term:** Does pause adaptation improve immediate performance? Can EEG features add predictive value beyond behavioral data? Closed-eyes vs. eyes-open encoding.
- **Medium-term:** Long-term retention curves; cross-domain transfer; personalized state models.
- **Long-term:** Multi-day closed-loop programs; clinical validation; open protocol marketplace.

## 19. Implementation roadmap

### Phase 4A — Protocol Schema

Define `Program`/`ProgramVersion`, `Protocol`/`ProtocolVersion`, schema, validation, versioning, JSON/YAML fixtures. No runtime, no DSL parser, no adaptation, no EEG.

### Phase 4B — Deterministic Runtime

Event scheduler, state machine, immutable event stream, deterministic replay, provider orchestration, safety monitor. No EEG, no adaptation.

### Phase 4C — Hebrew Behavioral Integration

Hebrew `DomainProvider`, `ResponseInterpreter`, `DomainNormalizer`, `Evaluator`, `Renderer`, fixed non-adaptive Hebrew protocols. No EEG, no adaptation.

### Phase 5A — Conservative Behavioral Adaptation

Spaced retrieval, response-window adjustment, cue specificity, new-item/review ratio. One-dimension-at-a-time. Abstention and rollback.

### Phase 5B — Sensor Research Layer

EEG acquisition, quality gating, feature registry, offline analysis. No real-time control.

### Phase 5C — Experimental Sensor-Informed Policies

Only after offline validation shows added predictive value. Begins in shadow mode.

### Phase 6 — Protocol Library and Longitudinal Learning

Expand Hebrew protocols, spaced repetition, A/B testing, learner history.

### Phase 7+ — Cross-Domain SDK and Research Platform

Other domains, marketplace, multi-session studies, IR workflows.

---

## Status and next step

This is the revised v1.1 architecture blueprint. **No production code should be written until the blueprint is reviewed.** The next action is approval of Phase 4A. Phase 4B and later phases are blocked until Phase 4A acceptance criteria are met.

## Traceability

This blueprint applies the audit package as follows:

| v1.1 section | Audit source |
|---|---|
| 1. Vision (product hypotheses quarantined) | `SOURCE_CLAIM_AUDIT.md` claim 1; `METHODOLOGY_AND_LIMITATIONS.md` §Limitations. |
| 3. Scientific assumptions | `METHODOLOGY_AND_LIMITATIONS.md` §Methodology (evidence grades). |
| 4. Cognitive model | `COGNITIVE_PROTOCOL_ONTOLOGY.md` §TrialRole, `PROTOCOL_DECOMPOSITION_MATRIX.csv`, `SOURCE_CLAIM_AUDIT.md` claim 4. |
| 4.3 State as estimate | `COGNITIVE_PROTOCOL_ONTOLOGY.md` §LatentEstimate, `SOURCE_CLAIM_AUDIT.md` claims 5–6. |
| 5. Object model | `MPE_OBJECT_MODEL_V1_1.md`; `COGNITIVE_PROTOCOL_ONTOLOGY.md` all core-entity sections. |
| 6. Primitives | `PROTOCOL_PRIMITIVES_CATALOG.md`; `SOURCE_CLAIM_AUDIT.md` claims 7–10. |
| 7. Runtime | `MPE_EVENT_MODEL_V1_1.md`; `DOMAIN_INDEPENDENCE_MAP.md` §What belongs in MPE core. |
| 8. Adaptive engine | `MPE_ADAPTATION_CONTRACT.md`; `COGNITIVE_PROTOCOL_ONTOLOGY.md` §AdaptationDecision, §LatentEstimate; `SOURCE_CLAIM_AUDIT.md` claims 10–11. |
| 10. Hebrew | `MPE_HEBREW_PROVIDER_CONTRACT.md`; `DOMAIN_INDEPENDENCE_MAP.md`; `SOURCE_CLAIM_AUDIT.md` claims 14–28. |
| 11. EEG | `DOMAIN_INDEPENDENCE_MAP.md`; `COGNITIVE_PROTOCOL_ONTOLOGY.md` §LatentEstimate; `SOURCE_CLAIM_AUDIT.md` claim 6. |
| 12. Metrics | `COGNITIVE_PROTOCOL_ONTOLOGY.md` §Outcome, `SOURCE_CLAIM_AUDIT.md` claim 12. |
| 19. Roadmap | `MPE_PHASE_4_IMPLEMENTATION_PLAN.md`; `EXECUTIVE_SYNTHESIS.md` point 7; `SOURCE_CLAIM_AUDIT.md` claim 13. |

Detailed claim-by-claim corrections are in `MPE_V1_0_CRITICAL_REVIEW.md`. The v1.0 section-to-audit mapping is in `docs/MPE_AUDIT_TRACEABILITY_TABLE.md`.
