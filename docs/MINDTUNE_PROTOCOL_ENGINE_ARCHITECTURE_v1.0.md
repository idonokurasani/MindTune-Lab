# MindTune Protocol Engine
## Technical & Cognitive Architecture v1.0

**Status:** Blueprint / pre-implementation  
**Author:** MindTune Lab architecture team  
**Date:** 2026-07-23  
**Scope:** Defines a new software category — Adaptive Cognitive Protocols (ACP) — and the engine that executes them.

---

## 1. Vision

MindTune Lab is becoming the first platform dedicated to **Adaptive Cognitive Protocols**.

A learning application assumes that the user learns while looking at a screen. MindTune rejects that premise for the active learning session. The most effective learning state, we hypothesize, occurs with eyes closed, minimal visual stimulation, auditory guidance, internal speech, mental imagery, and a continuously regulated cognitive load. The learner is not "using an app"; the learner is undergoing a protocol.

Hebrew is the first domain. The Hebrew linguistic engine built in earlier phases becomes one provider inside a larger system. Future domains — music, memory, executive function, meditation, mental arithmetic, working memory, cognitive rehabilitation — will plug into the same engine.

The product is therefore not a Hebrew app, a TTS pipeline, or an EEG recorder. The product is the **MindTune Protocol Engine (MPE)**: a runtime that turns declarative cognitive protocols into adaptive audio sessions and continuously regulates them.

---

## 2. Philosophy

### 2.1 The screen is secondary

The screen is used for:
- choosing a protocol,
- configuring settings and learner preferences,
- reviewing progress and explanations,
- preparing and closing a session.

The active session should happen almost entirely without looking at the display.

### 2.2 A protocol is not audio

A protocol is not an audio file, a playlist, or a meditation. It is a **structured cognitive sequence** with:
- a clear objective,
- a cognitive target,
- a linguistic or domain target,
- timing,
- adaptation rules,
- progression rules,
- evaluation metrics.

The audio is generated dynamically from the protocol.

### 2.3 Learning is a regulated state

The goal is not maximum speed or maximum throughput. The goal is maintaining an **optimal cognitive learning state**: not boredom, not overload, but the narrow band in which effort is productive.

### 2.4 Internal speech as mechanism

Internal speech — hearing, predicting mentally, comparing, reinforcing — is central. The learner often does not need to speak aloud. The protocol asks for mental responses and uses external confirmation to close the feedback loop.

### 2.5 EEG is one signal among many

EEG is not a correctness detector, a lie detector, or a thought reader. It is one adaptive input. Other inputs include behavioral accuracy, retrieval latency, historical performance, fatigue estimates, and future physiological sensors. The protocol engine fuses these signals to regulate the session.

---

## 3. Scientific assumptions

The architecture is built on a set of explicit, falsifiable assumptions. They are stated here so they can be tested, not assumed.

1. **State-dependent learning.** Encoding and consolidation are modulated by arousal, attention, fatigue, and cognitive load.
2. **Prediction and error correction.** Generating a prediction before receiving feedback strengthens memory more than passive exposure.
3. **Internal rehearsal.** Sub-vocal or mental rehearsal of material improves retention and fluency.
4. **Desirable difficulty.** Slightly harder retrieval produces stronger learning than errorless study.
5. **Spaced and interleaved practice.** Distributed and mixed practice outperforms massed practice for long-term retention.
6. **Sensory reduction.** Reducing visual input during encoding/recall may deepen auditory and internally generated processing.
7. **EEG correlates, not decodes.** EEG can correlate with states such as engagement, drowsiness, or cognitive load, but it cannot read semantic content or determine correctness.
8. **Multimodal feedback regulation.** Adaptive timing, speech rate, and repetition density can keep the learner in a productive state.

These assumptions form the cognitive foundation. The system must remain agnostic enough to update them as evidence accumulates.

---

## 4. Cognitive model

### 4.1 The learning loop

A single learning cycle consists of four phases:

1. **Perceive.** An auditory stimulus is presented.
2. **Predict.** The learner generates an internal expectation, translation, or completion.
3. **Resolve.** The correct information is supplied.
4. **Reinforce.** The association between prediction and outcome is strengthened through timing, repetition, and feedback.

A protocol is a managed sequence of these cycles.

### 4.2 Cognitive state variables

The engine estimates a small, explicit state vector:

| Variable | Meaning | Example sources |
|---|---|---|
| `arousal` | Alertness / sleepiness | EEG alpha/theta ratio, blink rate, reaction time |
| `attention` | Focus on task | Behavioral accuracy, EEG frontal asymmetry, self-report |
| `cognitive_load` | Perceived effort | Response latency, error rate, EEG frontal theta/beta |
| `fatigue` | Declining performance capacity | Latency drift, accuracy decay, time-on-task, HRV |
| `engagement` | Willingness to continue | Session length, skip behavior, post-session rating |
| `fluency` | Automaticity of target material | Retrieval latency, error rate over reviews |

These variables are estimates, not ground truth. They are used to choose among safe, reversible adaptations (pause length, rate, repetition, difficulty).

### 4.3 Session phases

Every session moves through a well-defined sequence:

- **Setup.** Screen-based configuration.
- **Calibrate.** Baseline measurements and environment check.
- **Warm-up.** Low-stakes preview of target material.
- **Core loop.** Perceive-predict-resolve-reinforce cycles.
- **Cool-down.** Summary, consolidation cue, transition out.
- **Review.** Screen-based feedback and progress.

---

## 5. Protocol object model

The MPE manipulates a small set of conceptual objects. They are abstract; concrete implementations will come later.

### 5.1 Protocol

A `Protocol` is a declarative blueprint.

```text
Protocol
├── id
├── name
├── version
├── objective
├── cognitive_target
├── domain_target
├── estimated_duration
├── difficulty_profile
├── protocol_family       # e.g., language_encoding, working_memory, meditation
├── provider_requirements # e.g., hebrew, tts, eeg
├── state_graph           # Steps and transitions
├── adaptation_policy
├── progression_policy
├── success_metrics
└── safety_rules
```

### 5.2 Step

A `Step` is a node in the protocol state graph.

```text
Step
├── id
├── type                  # play, pause, expect, repeat, branch, adapt, loop, wait_for_state
├── parameters            # provider, stimulus, duration, cue, expected_response
├── transitions           # next step IDs + conditions
├── adaptation_scope      # which parameters may be modified at runtime
└── evaluation_rule       # how the step contributes to metrics
```

### 5.3 Session

A `Session` is an executed instance of a `Protocol`.

```text
Session
├── id
├── protocol_id
├── learner_id
├── start_time
├── end_time
├── state_history
├── event_stream
├── estimated_cognitive_state
├── applied_adaptations
├── provider_outputs
└── outcome_summary
```

### 5.4 Provider

A `Provider` supplies capabilities to the engine. Providers are strictly separated from the core.

```text
Provider
├── id
├── capability_list       # e.g., audio_stimulus, language_form, eeg_signal, recall_prompt
├── init(config)
├── render(step) -> media cue
├── observe() -> signal
├── evaluate(expected, observed) -> correctness / latency / confidence
└── metadata() -> version, quality, domain
```

### 5.5 Learner profile

```text
LearnerProfile
├── id
├── preferences           # voice, speed, pause style, visual settings
├── history               # prior sessions, retention curves
├── state_model           # per-learner parameters for the adaptive engine
├── goals
└── consent_flags         # data use, sensor permissions
```

---

## 6. Protocol DSL

The Protocol Domain-Specific Language is human-readable and declarative. It describes *what* should happen, not *how* the engine implements it.

### 6.1 Core primitives

| Primitive | Meaning |
|---|---|
| `play(stimulus, [provider])` | Render and play an auditory stimulus. |
| `pause(duration, [adaptive=true])` | Wait. Duration may be fixed or regulated. |
| `expect(kind, [duration])` | Ask the learner to produce an internal response. |
| `repeat(n, [step_id])` | Repeat a step or block. |
| `loop(block, [condition])` | Loop while a condition holds. |
| `branch(condition, if_true, if_false)` | Conditional transition. |
| `adapt(param, policy)` | Declare that a parameter may be regulated. |
| `review(item, [mode])` | Re-introduce material from the learner's history. |
| `wait_for_state(target, timeout)` | Block until a cognitive state is estimated or timeout. |
| `increase_difficulty()` / `decrease_difficulty()` | Shift difficulty within safe bounds. |
| `calibrate()` | Baseline measurement step. |

### 6.2 Example: Vocabulary Encoding

```dsl
protocol vocabulary_encoding {
  objective: "associate Hebrew word with Italian meaning"
  family: language_encoding

  step present_hebrew:
    play("לִלְמוֹד", hebrew)
    pause(1.5, adaptive=true)

  step present_meaning:
    play("imparare", tts)
    pause(2.0, adaptive=true)

  step repeat_pair:
    repeat(2, block=[present_hebrew, present_meaning])

  start: present_hebrew
}
```

### 6.3 Example: Vocabulary Recall

```dsl
protocol vocabulary_recall {
  objective: "recall Hebrew word from Italian cue"
  family: language_recall

  step cue:
    play("imparare", tts)
    expect(mental_hebrew, duration=4.0, adaptive=true)

  step feedback:
    play("לִלְמוֹד", hebrew)
    pause(2.0, adaptive=true)

  step evaluate:
    # Learner may press a button or speak; absence of data is acceptable.
    observe_response(kind=optional_button, label=correct/incorrect)

  transitions:
    cue -> feedback [after expect timeout]
    feedback -> evaluate [after play]
    evaluate -> cue [loop until protocol_end]
}
```

### 6.4 Example: Morphology Flow

```dsl
protocol morphology_flow {
  objective: "internalize person inflections"
  family: language_morphology

  step first:
    play("I studied", tts)
    pause(1.5)

  step second:
    play("you studied", tts)
    pause(1.5)

  step third:
    play("he/she studied", tts)
    pause(2.0)

  step predict:
    play("we ____", tts)
    expect(mental_completion, duration=5.0)

  step resolve:
    play("we studied", tts)
    pause(2.0, adaptive=true)
}
```

### 6.5 Example: Prediction Flow

```dsl
protocol prediction_flow {
  objective: "predict the next word in a sentence"
  family: language_prediction

  step stimulus:
    play("The cat sat on the...", tts)
    expect(mental_completion, duration=3.5, adaptive=true)

  step resolve:
    play("mat", tts)
    pause(2.0)
}
```

### 6.6 Example: Listening Immersion

```dsl
protocol listening_immersion {
  objective: "maintain comprehension under adaptive speech rate"
  family: language_immersion

  step stream:
    play(passage_001, hebrew, adaptive_rate=true)
    # Engine continuously modulates speech rate and insertions based on state.
    adapt(rate, policy=track_load)
    adapt(insert_review, policy=on_high_load)
}
```

---

## 7. Runtime execution engine

### 7.1 Responsibilities

The runtime is the heart of MPE. It:
- loads a `Protocol` and a `LearnerProfile`,
- initializes required providers,
- walks the protocol state graph,
- dispatches audio rendering,
- collects observations,
- invokes the adaptive engine,
- records every event immutably,
- enforces safety and pause rules.

### 7.2 Execution model

A session runs on an **audio clock**: discrete events are scheduled at absolute times relative to session start. The engine is event-driven, not audio-stream-driven, so adaptation can reschedule future events without re-rendering already-played audio.

```text
Scheduler
├── current_time
├── scheduled_events (priority queue)
├── state_machine
└── provider_bus

loop:
  pop next event
  execute event handler
  update cognitive state estimate
  possibly re-schedule future events
  log event
```

### 7.3 Determinism and reproducibility

A protocol run with the same `Protocol`, `LearnerProfile`, random seed, and observation stream must be reproducible. Reproducibility is essential for:
- debugging,
- A/B testing,
- clinical validation,
- regression testing.

To achieve this, all randomness is seeded, all adaptations are logged, and provider outputs are captured or mocked in test mode.

### 7.4 Concurrency and timing

Audio rendering may happen on a separate thread, but the scheduler is single-threaded. Provider observations are timestamped and merged asynchronously into the event stream. The engine never blocks on real-time EEG; it uses the most recent validated estimate.

---

## 8. Adaptive engine

### 8.1 Inputs

The adaptive engine consumes a normalized observation vector:

| Source | Observation | Latency |
|---|---|---|
| Behavioral | Button press, voice input, skip action | ~0 ms |
| Performance | Correctness, response latency, confidence | ~ms to seconds |
| EEG | Engagement, drowsiness, load features | ~1-5 seconds |
| Physiological | HRV, eye tracking, breathing (future) | ~seconds |
| Self-report | Fatigue, difficulty, engagement ratings | user-initiated |
| History | Forgetting curves, item difficulty | offline |

### 8.2 State estimator

The state estimator fuses inputs into the cognitive state vector. It is explicitly probabilistic: every estimate carries a confidence interval. When confidence is low, the engine falls back to conservative defaults rather than over-adapting.

### 8.3 Controllable parameters

| Parameter | Effect | Safe range |
|---|---|---|
| `pause_duration` | Time between stimuli | 0.5s – 8.0s |
| `speech_rate` | Words per minute | 0.7x – 1.3x base |
| `repetition_density` | Probability of repeating an item | 0% – 100% |
| `difficulty_level` | Item complexity / novelty | bounded by protocol |
| `new_item_rate` | Ratio of new vs. review items | 0% – 50% |
| `session_length` | Remaining planned duration | min/max bounds |

### 8.4 Adaptation policy

An `AdaptationPolicy` is a declarative mapping from state to parameter changes:

```dsl
adaptation_policy default {
  if load > high and attention < low:
    decrease difficulty
    increase pause_duration by 0.5s
    decrease speech_rate by 0.1x
  elif load < low and engagement < low:
    increase difficulty
    decrease pause_duration by 0.3s
  elif fatigue > high:
    insert_review
    offer_session_end
}
```

Policies are authored in the DSL, versioned, and evaluated against historical sessions before deployment.

### 8.5 Guardrails

- A parameter can never change by more than its safe step size within one transition.
- Difficulty cannot increase after three consecutive errors.
- Session length cannot be silently extended beyond the user-approved maximum.
- Every adaptation is logged and reversible.
- If state estimation confidence is below threshold, the engine holds the current parameters.

---

## 9. Audio generation

### 9.1 Provider model

Audio is generated by providers, not by the engine. The engine sends `RenderRequest` objects and receives `AudioCue` objects.

```text
RenderRequest
├── text / stimulus identifier
├── provider
├── rate
├── voice
├── prosody_hint       # e.g., question, emphasis, calm
└── metadata

AudioCue
├── uri / stream_handle
├── duration
├── waveform_metadata
└── provider_version
```

### 9.2 Speed and prosody

Speech rate is controllable per step and per item. Prosody hints allow the provider to emphasize a prompt, soften a review, or mark a question. The engine remains provider-agnostic; the actual TTS engine (Hebrew TTS, Azure, Coqui, Piper, etc.) implements the rendering.

### 9.3 Dynamic generation

Because the protocol is declarative, audio is generated on demand. This enables:
- real-time adaptation,
- personalized content insertion,
- new protocols without pre-recording audio,
- A/B testing of prosody and timing.

Caching is a provider concern. The engine may cache `RenderRequest` hashes but does not require it.

---

## 10. Hebrew integration

The existing Hebrew linguistic engine becomes a **domain provider**. MPE knows nothing about binyanim, niqqud, or stress. It asks the provider for stimuli and metadata.

### 10.1 Hebrew provider capabilities

- `render_word(surface, form_key)` → audio cue
- `render_form(root, binyan, form_key)` → audio cue
- `get_item(item_id)` → lexical metadata
- `generate_recall_cue(item)` → cue in target or native language
- `evaluate_response(item, response)` → latency, correctness, confidence

### 10.2 Decoupling

No Hebrew-specific code lives in MPE core. The core only understands generic primitives: `play`, `expect`, `pause`, `adapt`. All Hebrew content is injected through the provider interface.

### 10.3 Reuse of Phase 3 work

The normative orthography, phonology/stress, verb selection, verified-consensus expansion, confidence calibration, benchmark partitions, and differential tests remain valid. They become the quality layer inside the Hebrew provider. MPE consumes their outputs as provider metadata.

---

## 11. EEG integration

### 11.1 Role

EEG is an optional adaptive input. It is treated as a **noisy, delayed correlate** of cognitive state. It is never used to determine correctness or read semantic content.

### 11.2 Signal path

```text
EEG hardware
  -> acquisition driver
  -> quality gate
  -> feature extraction
  -> state feature vector
  -> MPE adaptive engine
```

### 11.3 Quality gate

If signal quality is poor (impedance, motion artifact, disconnection), the engine ignores EEG and falls back to behavioral/historical signals. A session can proceed without EEG.

### 11.4 Feature extraction

Features are state indicators, not decoders:
- frontal theta / beta ratio as a correlate of cognitive load,
- alpha asymmetry / power as a correlate of engagement or drowsiness,
- blink and muscle artifact rejection,
- heart-rate variability if available.

### 11.5 Privacy and safety

Raw EEG is stored only if the learner consents. Features are pseudonymized. The system never makes medical claims or diagnoses. Closed-eyes protocols include an explicit safety rule to reopen eyes on demand.

---

## 12. Performance metrics

### 12.1 Session-level metrics

- `time_in_target_state` — fraction of session with estimated optimal load,
- `accuracy` — behavioral correctness when measurable,
- `latency` — response or prediction latency,
- `coverage` — fraction of target items presented,
- `adaptation_count` — number of parameter changes,
- `engagement_proxy` — absence of skips, early termination, self-reports.

### 12.2 Protocol-level metrics

- retention curve per item,
- forgetting rate,
- transfer to untrained items,
- time to criterion,
- state stability across sessions.

### 12.3 Learner-level metrics

- cumulative progress per protocol family,
- learning velocity,
- optimal state profile,
- long-term retention,
- cross-domain transfer if applicable.

### 12.4 Diagnostic metrics

- adaptation efficacy (did the change improve the state?),
- state estimator accuracy (against labeled validation sessions),
- provider latency and reliability,
- protocol adherence (did the session follow the state graph?).

---

## 13. Data model

### 13.1 Event stream as source of truth

All runtime facts are recorded as immutable events:

```text
Event
├── session_id
├── timestamp
├── event_type          # play_started, play_ended, observation, adaptation, state_estimate
├── step_id
├── provider_id
├── payload
├── version
└── provenance
```

Derived views (session summaries, learner progress, retention curves) are computed from the event stream. This makes the system auditable and reproducible.

### 13.2 Entities

- `Protocol` — versioned blueprint.
- `Session` — executed instance.
- `LearnerProfile` — per-user model and preferences.
- `Item` — domain entity managed by a provider.
- `Observation` — sensor or behavioral input.
- `Adaptation` — a recorded parameter change.
- `Outcome` — computed summary of a session.

### 13.3 Privacy

- Raw physiological data is encrypted at rest and consent-gated.
- Learner-facing reports are pseudonymized for research sharing.
- Data retention policies are explicit per protocol family.
- The learner can export or delete their event stream.

---

## 14. Extensibility

### 14.1 Provider API

A provider implements a small interface:

```text
provider_init(config)
provider_capabilities()
provider_render(request) -> cue
provider_observe() -> observations
provider_evaluate(expected, observed) -> metrics
provider_shutdown()
```

### 14.2 Protocol family plugins

A protocol family is a package that:
- defines domain-specific step types,
- provides default protocols,
- contributes metrics,
- contributes adaptation policies,
- registers providers.

### 14.3 New domains

To add a new domain (e.g., music ear training):
1. implement a provider that can render audio and evaluate responses,
2. define a protocol family plugin,
3. author protocols in the DSL,
4. add evaluation metrics,
5. validate through simulation and small studies.

No changes to MPE core are required.

---

## 15. Future protocol families

The architecture is intentionally domain-neutral. Anticipated families include:

| Family | Description |
|---|---|
| `language_*` | Vocabulary, morphology, listening, speaking, grammar. |
| `music_*` | Ear training, interval recognition, rhythm, sight-singing. |
| `memory_*` | Spatial memory, paired associates, narrative recall. |
| `executive_function_*` | Inhibition, switching, updating, planning. |
| `meditation_*` | Breath focus, open awareness, body scan, compassion. |
| `mental_arithmetic_*` | Facts, estimation, strategy fluency. |
| `working_memory_*` | N-back, span, complex span. |
| `cognitive_rehabilitation_*` | Stroke, ADHD, aging, attention training. |

---

## 16. Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| **Over-adaptation** | Medium | High | Conservative adaptation policies, guardrails, logging, A/B testing. |
| **False confidence in EEG** | High | High | EEG is never the sole signal; uncertainty is explicit; fallback modes. |
| **Cognitive overload** | Medium | High | Difficulty bounds, pause floors, learner override, safe exit. |
| **Closed-eyes safety** | Medium | Medium | Always-on audio stop cue, proximity to display optional, emergency pause. |
| **Provider lock-in** | Medium | Medium | Provider API and render/abstract interface. |
| **TTS latency breaks pacing** | Medium | Medium | Pre-fetch, caching, streaming, asynchronous providers. |
| **Confirmation bias** | Medium | High | Outcome metrics include retention and transfer, not just session completion. |
| **Privacy / consent** | Medium | High | Consent flags, encryption, export/delete, pseudonymization. |
| **Domain-specific shortcuts** | Medium | Medium | Strict separation between MPE core and providers; no domain code in core. |

---

## 17. Validation methodology

Validation must be layered and skeptical.

### 17.1 Simulation

- Synthetic learners with known forgetting curves.
- Replay historical sessions with modified policies.
- Monte-Carlo simulation of adaptation policies.

### 17.2 Component tests

- Provider unit tests (already in place for Hebrew).
- State estimator tests on labeled data.
- DSL parser and runtime tests.
- Round-trip reproducibility tests.

### 17.3 Expert review

- Cognitive scientists review protocol designs.
- Domain experts (linguists, musicians, clinicians) review content.
- HCI experts review screen flow and safety.

### 17.4 Controlled studies

- A/B tests of adaptation policies against fixed protocols.
- Pre/post retention tests.
- Dose-response studies (session length, frequency).
- Cross-domain transfer studies.

### 17.5 Psychometric standards

- Pre-registered hypotheses.
- Blinded analysis where possible.
- Public benchmark datasets.
- Replication across populations.

---

## 18. Research roadmap

### 18.1 Near-term (0–12 months)

- Does real-time pause adaptation improve immediate performance?
- Can simple EEG features (engagement, drowsiness) be fused with latency to predict optimal difficulty?
- What is the effect of closed-eyes vs. eyes-open vocabulary encoding?
- How should internal-speech protocols be designed to maximize prediction-based learning?

### 18.2 Medium-term (1–3 years)

- Long-term retention curves for adaptive protocols vs. fixed schedules.
- Cross-domain transfer: does Hebrew protocol experience improve working-memory protocol outcomes?
- Personalized state models: per-learner EEG/behavior feature weights.
- Robust EEG signal processing across consumer and research headsets.

### 18.3 Long-term (3+ years)

- Closed-loop, multi-day learning programs with automated spacing.
- Clinical validation of cognitive rehabilitation protocols.
- Real-world deployment with ecological momentary assessment.
- Open protocol marketplace and researcher-contributed families.

---

## 19. Implementation roadmap

### Phase 4 — Core MPE + Hebrew + Audio (no EEG)

- Define the DSL grammar and parser.
- Implement the runtime scheduler and state machine.
- Implement the provider interface.
- Wrap the existing Hebrew engine as a provider.
- Integrate TTS and dynamic audio rendering.
- Build a minimal screen UI for protocol selection and review.
- Implement event logging and session replay.
- Create a core test suite.

### Phase 5 — Adaptive Engine + Optional EEG

- Implement the state estimator with behavioral inputs.
- Add EEG acquisition and quality gating.
- Implement adaptation policies and guardrails.
- Add closed-eyes safety rules.
- Validate against simulation and small user studies.

### Phase 6 — Protocol Library and Progression

- Expand Hebrew protocol families (encoding, recall, morphology, prediction, immersion).
- Implement spaced repetition and review scheduling.
- Build learner profile and progress visualization.
- Implement protocol versioning and A/B testing.

### Phase 7 — Cross-Domain SDK

- Document the provider API and DSL.
- Release a music ear-training protocol family as the second domain.
- Add provider packaging and marketplace conventions.

### Phase 8 — Research Platform

- Support multi-session studies, export, and reproducible analysis.
- Integrate with institutional review workflows.
- Open-source core MPE and selected providers.

---

## Glossary

- **Adaptive Cognitive Protocol (ACP):** A structured, dynamically regulated sequence of cognitive exercises.
- **Protocol:** A declarative blueprint for a session.
- **Provider:** A pluggable domain or sensor capability.
- **Session:** One runtime execution of a protocol.
- **State estimator:** Component that infers cognitive state from multiple inputs.
- **Adaptation policy:** Rules that map state estimates to controllable parameter changes.
- **Internal speech:** Sub-vocal or mental rehearsal without audible output.

---

## Status and next step

This document is the architecture blueprint. **No production code should be written until the design is reviewed.** The next action is a review of assumptions, the DSL surface, and the provider interface. Implementation begins with Phase 4 once the blueprint is approved.
