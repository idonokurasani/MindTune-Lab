# MPE Protocol Library v1.0

**Document:** `docs/specification/v1.1/MPE_PROTOCOL_LIBRARY_v1.0.md`
**Status:** Canonical architecture reference (v1.0) — documentation only
**Scope:** Defines *what a protocol is* in the MindTune Protocol Engine (MPE): the protocol ontology, taxonomy, cognitive primitives, adaptation boundaries, EEG policy, lifecycle, object model, replay semantics, and metrics.

> **This is not a DSL specification, not an implementation plan, and not Hebrew-specific.** It defines the *meaning* of protocols. No production code is written here. No `mpe_audio` implementation is defined. No existing runtime contract is modified. No Git action is taken. Typed shapes below are **conceptual models expressed as pseudocode**, never implementation classes.

> **Relationship to sibling documents.** Audio assets referenced here are resolved exclusively through the **Audio Asset Pipeline** (`MPE_AUDIO_ASSET_PIPELINE_SPEECHGEN_HEBREW_v0.1.md` and `MPE_AUDIO_PIPELINE_PHASE_A_DECISION_RECORD.md`). Protocols in this document never name a provider and never know SpeechGen exists. The primitive names used in this document (`play`, `pause`, `expect`, `confirm`, `repeat`, `branch`, `transition`, etc.) are **semantic pseudocode**, not an approved textual DSL. Their concrete expression in the runtime is the MPE v1.1 typed model: `Instruction`, `StimulusRequest`, `ResponseWindow`, `ScheduleDecision`, `AdaptationDecision`, and `FeedbackEvent`. See `MPE_DSL_DECISION_RECORD.md` (no textual DSL in Phase 4) and the mapping in Appendix E.

---

## Table of contents

1. Executive summary
2. Foundational principle: MindTune is a cognitive-protocol framework
3. Protocol ontology
4. Domain neutrality and the domain-binding model
5. Protocol taxonomy (the eight categories)
6. Cognitive primitive catalog (semantics only)
7. Per-protocol specifications
   - 7.1 Encoding protocols
   - 7.2 Recall protocols
   - 7.3 Transformation protocols
   - 7.4 Recognition protocols
   - 7.5 Internal-speech protocols
   - 7.6 Listening protocols
   - 7.7 Consolidation protocols
   - 7.8 Recovery protocols
8. Adaptation model
9. EEG policy (permanent architectural rule)
10. Behavioral evidence model
11. Protocol lifecycle
12. Protocol object model (conceptual)
13. Interaction with MPE runtime
14. Interaction with the Audio Asset Pipeline
15. Replay: protocol replay vs event replay
16. Metrics and measurable outcomes
17. Future domains (Hebrew Lab, Piano Lab, general cognitive training, other languages)
18. Cross-cutting invariants and acceptance criteria
19. Unresolved questions
20. Implementation recommendations
21. Final recommendation

Appendix A — Primitive quick reference
Appendix B — Protocol summary matrix
Appendix C — Worked Hebrew examples (illustrative only)
Appendix D — Glossary

---

## 1. Executive summary

MindTune Lab is a framework for **adaptive cognitive protocols**, not an e-learning product. A *protocol* is a structured, time-based cognitive exercise that the MindTune Protocol Engine executes primarily through the auditory and internal-speech channels: the learner **listens, anticipates, produces internal speech, recalls, and confirms**, with the engine **adapting repetition, pacing, and progression** in response to evidence. The screen is for configuration, explanation, review, and progress visualization; the protocol itself is normally executable with **eyes closed**.

This document establishes the canonical reference for every protocol MindTune will ever run. It defines:

- a **protocol ontology** — the invariant vocabulary and relationships (protocol, step, objective, stimulus, response, observation, adaptation, outcome);
- a **taxonomy** of eight protocol categories (Encoding, Recall, Transformation, Recognition, Internal Speech, Listening, Consolidation, Recovery) and the protocols within each;
- a small, closed **catalog of cognitive primitives** defined by semantics, not syntax;
- an **adaptation model** that cleanly separates behavior-based, latency-based, history-based, and EEG-context adaptation, stating exactly what each may influence;
- a **permanent EEG policy**: EEG is contextual, never authoritative, never determines correctness, never rewrites learning state directly;
- a **protocol lifecycle** (Planning → Execution → Observation → Adaptation → Completion → Replay → Analysis);
- a conceptual **object model**;
- the distinction between **protocol replay** and **event replay**;
- **metrics** for protocol outcomes; and
- applicability to **future domains** (Hebrew Lab, Piano Lab, general cognitive training, additional languages).

**Central design commitments:**

1. **Domain neutrality.** Protocol definitions contain no Hebrew (or piano, or any-domain) assumptions. Domains bind to protocols through an explicit *domain adapter* that supplies items, asset roles, and scoring semantics. Hebrew appears only as illustrative examples.
2. **Provider invisibility.** Protocols reference audio by logical asset role and item identity; the Audio Asset Pipeline resolves these to approved local assets. Protocols never see providers.
3. **Evidence primacy.** Behavioral evidence is authoritative for correctness. EEG only modulates bounded pacing/repetition/progression decisions and always emits a reasoned, replayable adaptation event.
4. **Determinism where it matters.** Given a recorded execution and its inputs, adaptation decisions and outcomes are reconstructible; orderings (sessions, findings, steps) are deterministic.

**Recommendation:** `APPROVE_PROTOCOL_LIBRARY_ARCHITECTURE`, conditioned on resolving the open questions in §19 during the first implementation phase. See §21.

---

## 2. Foundational principle: MindTune is a cognitive-protocol framework

### 2.1 What MindTune is not

MindTune Lab is **not** an e-learning platform. It is not a courseware player, not a flashcard app, not a quiz engine, not a spaced-repetition scheduler with a UI. Those framings assume the *screen* is the site of learning and that content is consumed visually. MindTune rejects that assumption.

### 2.2 What MindTune is

MindTune is a **framework for adaptive cognitive protocols**. A protocol orchestrates a cognitive process over time. Learning is produced by the learner's *own cognitive activity* — attention, prediction, retrieval, articulation — scaffolded by precisely timed audio and silence, and shaped by adaptation.

Learning occurs primarily through:

- **listening** — receiving a stimulus through the auditory channel;
- **anticipation** — predicting what comes next before it arrives;
- **internal speech** — silently producing a target (word, form, phrase) in the mind;
- **recall** — retrieving a target from memory, cued or free;
- **confirmation** — hearing the correct target after an attempt, closing the loop;
- **adaptive repetition** — repeating with spacing and density adjusted to performance.

### 2.3 The role of the screen

The screen exists for:

- **configuration** — choosing a protocol, domain, session length, difficulty band;
- **explanation** — describing what a protocol does and how to engage with it;
- **review** — inspecting what happened after a session;
- **progress visualization** — trends, mastery, streaks, spacing schedules.

The screen is **not** required during protocol execution. A protocol must be designed so that its *execution phase* is fully expressible through audio and silence, and is **normally executable with eyes closed**. Any protocol that cannot be run eyes-closed during execution is, by definition, out of the MindTune protocol model (visual-only tasks belong to configuration/review, not execution).

### 2.4 Consequences of the principle

This principle has concrete architectural consequences that recur throughout the document:

- **Silence is a first-class construct.** Pauses are where anticipation, internal speech, and recall happen. Pause timing is a primary adaptation lever, not incidental.
- **Behavioral evidence is often *implicit*.** Because the learner may produce internal (unspoken) responses, the engine frequently cannot observe correctness directly. It observes *proxies* (response latency, self-reported confirmation, optional overt production) and treats them accordingly (§10).
- **Confirmation replaces grading in many protocols.** For internal-production protocols, the engine may never "mark" an answer; it *presents the correct target* and lets the learner self-assess, recording confirmation signals rather than machine-scored correctness.
- **Adaptation must be gentle and reversible.** Because evidence is often noisy/implicit, adaptation favors bounded, reversible adjustments over hard state changes.

---

## 3. Protocol ontology

The ontology is the invariant vocabulary. Every protocol, in every domain, is described using exactly these concepts. Categories and specific protocols are *instances/specializations*; the ontology itself does not change per domain.

### 3.1 Core entities

- **Protocol** — a named, reusable cognitive exercise definition. It declares an objective, a category, the primitive-based structure of its steps, its asset-role requirements, its behavioral measurements, its adaptation opportunities, and its success criteria. A protocol is a *type*; an execution is an *instance*.
- **ProtocolObjective** — the cognitive goal(s) a protocol serves (e.g. *form a durable association*, *strengthen retrieval*, *discriminate confusable items*). Objectives are drawn from a closed cognitive-goal vocabulary (§3.3).
- **ProtocolStep** — an ordered (possibly branching) unit of execution, expressed via cognitive primitives (§6). A step is the smallest addressable execution unit for observation and adaptation.
- **Stimulus** — a presented item, delivered as an audio asset (via the pipeline) resolved by *logical role* and *item identity*. Never a provider URL.
- **Response (expected)** — the cognitive act the learner is expected to perform (internal or overt), plus the *evidence* the engine may collect about it.
- **Observation** — a recorded measurement during execution (latency, overt response marker, confirmation signal, EEG-context reference). Observations are evidence, not verdicts.
- **AdaptationDecision** — a bounded, reasoned change to pacing, repetition, selection, or progression, derived from observations under an explicit policy rule.
- **Outcome / ExecutionResult** — the recorded result of an execution instance: what happened, what was observed, what was decided, and how objectives were met.

### 3.2 Relationships

```
Protocol ──has──▶ ProtocolObjective(1..n)
Protocol ──composed of──▶ ProtocolStep(1..n)   # via primitives; may branch
ProtocolStep ──presents──▶ Stimulus(0..n)      # resolved to audio assets by role+item
ProtocolStep ──expects──▶ Response(0..1)        # internal or overt
ProtocolStep ──produces──▶ Observation(0..n)
Observation ──feeds──▶ AdaptationDecision(0..n)
AdaptationDecision ──modifies──▶ future ProtocolStep pacing/selection/progression
Execution(Protocol) ──yields──▶ ExecutionResult ──summarized as──▶ ProtocolSummary
```

### 3.3 Cognitive-goal vocabulary (closed set)

Every `ProtocolObjective` maps to one or more of these canonical cognitive goals. This keeps objectives comparable across domains and categories:

- **Encode** — establish a new memory representation / association.
- **Retrieve** — strengthen retrieval of an existing representation.
- **Discriminate** — sharpen the boundary between confusable representations.
- **Transform** — apply a systematic rule to produce a derived form.
- **Produce** — generate a target through internal or overt articulation.
- **Comprehend** — extract meaning from connected input.
- **Consolidate** — stabilize and space existing representations over time.
- **Restore** — rebuild confidence / reduce load after difficulty.

Each category (§5) is characterized by which goals it primarily serves.

### 3.4 Ontological invariants

- A protocol's *category* is determined by its **primary cognitive goal**, not by surface structure (two protocols may share primitives but belong to different categories because their objective differs).
- A protocol is **domain-agnostic**: swapping the domain adapter must not change the protocol's ontology-level description.
- Every `Stimulus` is **asset-role addressed** (e.g. `prompt`, `confirmation`, `natural`, `pedagogical_slow`, `minimal_pair`, `sentence_context`); role vocabulary is shared with the Audio Asset Pipeline.
- Every `Observation` is **typed** and carries a provenance (which step, which primitive, which evidence kind).

---

## 4. Domain neutrality and the domain-binding model

### 4.1 Why neutrality is mandatory

Hebrew is the first domain, but the protocol library must serve Piano Lab, general cognitive training, and other languages without rewriting protocol definitions. Therefore **no Hebrew concept may appear in a protocol definition**. Concepts like "root", "binyan", or "niqqud" are *domain vocabulary*, not protocol vocabulary. Where this document uses them, it is strictly as **examples**, clearly marked.

### 4.2 The domain adapter

A **DomainAdapter** is the seam between the neutral protocol library and a concrete domain. It supplies:

- **Item universe** — the domain's learnable items and their identity (`item_id`), with domain metadata opaque to the protocol.
- **Item relations** — domain-specific relations the protocol references only abstractly (e.g. "derivation-of", "inflection-of", "confusable-with", "member-of-family"). Protocols request relations by *abstract relation name*; the adapter defines them.
- **Asset-role catalog** — which asset roles exist for this domain and how an (`item_id`, `role`) resolves via the Audio Asset Pipeline.
- **Scoring semantics** — how a domain interprets an overt/confirmed response as evidence (the protocol records evidence; the adapter interprets domain correctness where applicable).
- **Difficulty model** — how items map to difficulty bands the protocol can progress through.

```
Protocol (neutral)  ──uses abstract──▶  { item_id, abstract_relation, asset_role, difficulty_band }
                                             │
                                   DomainAdapter binds
                                             ▼
Domain (Hebrew | Piano | ...)  ──supplies──▶ concrete items, relations, assets, scoring
```

### 4.3 Neutral relation vocabulary

Protocols reference item relations only through this abstract set (domains map them concretely):

- `associate(a, b)` — a↔b meaning/label association (e.g. word↔translation; note↔fingering).
- `derive(base → derived)` — rule-based derivation (e.g. root→word; scale→chord).
- `inflect(base → variant, dimension)` — systematic variation along a dimension (e.g. verb tense; dynamics).
- `contrast(a, b)` — minimally different, confusable pair.
- `family(root, members)` — a set sharing a generator.
- `sequence(a → b → …)` — an ordered progression.
- `contains(whole, parts)` — compositional structure (e.g. sentence↔words; phrase↔notes).

Any protocol expressible in these relations is automatically portable across domains.

---

## 5. Protocol taxonomy (the eight categories)

The taxonomy is organized by **primary cognitive goal**. A protocol belongs to exactly one category (its primary goal); it may serve secondary goals. Categories are ordered roughly along a learning arc — from establishing representations to stabilizing and protecting them — but MPE composes across categories freely within a session.

| # | Category | Primary goal(s) | Core question it answers | Typical evidence |
|---|---|---|---|---|
| 1 | **Encoding** | Encode | "Can a new representation be formed?" | latency-to-confirm, repetition demand |
| 2 | **Recall** | Retrieve | "Can it be retrieved, and how easily?" | retrieval latency, confirmation, success rate |
| 3 | **Transformation** | Transform, Produce | "Can a rule be applied to produce a derived form?" | production latency, correctness (overt), error type |
| 4 | **Recognition** | Discriminate | "Can confusable items be told apart?" | choice correctness, discrimination latency |
| 5 | **Internal Speech** | Produce | "Can the target be produced internally/overtly on cue?" | timing alignment, self-confirmation, optional overt |
| 6 | **Listening** | Comprehend | "Can meaning/structure be extracted from connected input?" | sustained attention proxies, comprehension checks |
| 7 | **Consolidation** | Consolidate | "Are representations stable and well-spaced over time?" | spaced success, retention curves |
| 8 | **Recovery** | Restore | "Can confidence and load be restored after difficulty?" | recovered success rate, reduced-load performance |

### 5.1 Category summaries

**1. Encoding** — Establishes new representations and associations. Members: *Vocabulary Encoding, Morphology Encoding, Root Encoding, Pattern Encoding, Sentence Encoding*. Heavy on `play → pause → confirm` loops with generous, adaptive pauses; low retrieval demand initially.

**2. Recall** — Strengthens retrieval of existing representations under varying support. Members: *Immediate Recall, Delayed Recall, Free Recall, Recognition Recall*. Emphasizes `expect internal response` before `confirm`; the anticipation pause is the active ingredient.

**3. Transformation** — Trains systematic rule application to produce derived forms. Members: *Inflection, Conjugation, Number, Gender, Person, Tense, Voice, Derivation*. A cue specifies the transformation dimension; the learner produces the transformed form; confirmation follows.

**4. Recognition** — Sharpens discrimination between confusable items. Members: *Minimal Pairs, Root Recognition, Pattern Recognition, Error Detection*. Presents contrasts and asks for a discrimination judgment (internal or overt).

**5. Internal Speech** — Trains internal (and optionally overt) production on cue. Members: *Silent production, Silent repetition, Mental completion, Mental anticipation*. Purely production-focused; correctness is self-confirmed, not machine-graded, unless an overt variant is enabled.

**6. Listening** — Builds comprehension and structural perception from connected input. Members: *Immersion, Focused listening, Comparative listening*. Longer, lower-interaction; adaptation acts on density and pause insertion, not on per-item grading.

**7. Consolidation** — Stabilizes and spaces existing representations. Members: *Adaptive review, Spaced reinforcement, Mixed review*. Draws items from history/spacing state; interleaves categories.

**8. Recovery** — Restores confidence and reduces cognitive load after difficulty. Members: *Reduced-load mode, Confidence rebuilding, Reinforcement cycles*. Triggered by sustained struggle or EEG-context signals (as a modulator only); deliberately easy, high-confirmation.

### 5.2 Category relationships

```
        Encode              Retrieve            Transform/Produce
   ┌───────────────┐   ┌───────────────┐   ┌────────────────────┐
   │  1 Encoding   │──▶│  2 Recall     │──▶│ 3 Transformation    │
   └───────────────┘   └───────────────┘   └────────────────────┘
           │                   │                     │
           ▼                   ▼                     ▼
   ┌───────────────┐   ┌───────────────┐   ┌────────────────────┐
   │ 5 Internal    │   │ 4 Recognition │   │ 6 Listening        │
   │   Speech      │   │ (Discriminate)│   │  (Comprehend)      │
   └───────────────┘   └───────────────┘   └────────────────────┘
                    ╲          │          ╱
                     ▼         ▼         ▼
                  ┌───────────────────────────┐
                  │     7 Consolidation        │  (spacing, mixing)
                  └───────────────────────────┘
                               │  (on sustained difficulty)
                               ▼
                  ┌───────────────────────────┐
                  │       8 Recovery           │  (restore load/confidence)
                  └───────────────────────────┘
```

Internal Speech (5) is *cross-cutting*: most Encoding/Recall/Transformation protocols embed internal-speech primitives. It is also a category in its own right when internal production is the *primary* goal.

---

## 6. Cognitive primitive catalog (semantics only)

Primitives are the smallest reusable protocol building blocks. This section defines **semantics, not syntax**. Their concrete expression is the MPE v1.1 typed model (`Instruction`, `StimulusRequest`, `ResponseWindow`, `ScheduleDecision`, `AdaptationDecision`, `FeedbackEvent`) and the event taxonomy in `MPE_EVENT_MODEL_V1_1.md`. Here we define *what each primitive means cognitively*, what it observes, and how it participates in adaptation. A mapping to MPE contracts is given in Appendix E.

The catalog is a **closed set**. New protocols are built by composing primitives, not by inventing new ones. Adding a primitive is an architecture-level change requiring revision of this document.

### 6.1 Primitive list

| Primitive | One-line semantics | Produces observation? | Adaptation touchpoint |
|---|---|---|---|
| **Play stimulus** | Present an item as audio (resolved by role+item) | onset/offset timestamps | playback rate (bounded), which variant/role |
| **Pause** | Insert silence for processing/recall/anticipation | pause duration (chosen) | pause duration (primary lever) |
| **Expect internal response** | Open a window in which the learner produces internally | latency proxy, optional overt marker | window length; whether to repeat |
| **Confirm** | Present the correct target to close the loop | confirmation-shown timestamp; self-confirm signal | whether/when to confirm; repetition after |
| **Repeat** | Re-present a step or group | repeat index | repeat count (bounded) |
| **Branch** | Choose a path from evidence/context | chosen branch + reason | selection/progression |
| **Transition** | Move to another protocol state/block | transition reason | progression, recovery/consolidation entry |
| **Wait** | Idle for a fixed/bounded interval unrelated to response | elapsed | rarely adapted |
| **Observe** | Explicitly sample behavioral/EEG-context evidence | the sampled evidence | feeds all adaptation |
| **Score** | Interpret collected evidence into a domain outcome (via adapter) | derived score/verdict | history-based adaptation |
| **Record** | Emit a durable execution event | the event itself | none (audit/replay) |
| **Explain** | Provide non-execution explanatory content (config/review) | n/a (not during eyes-closed execution) | none |

### 6.2 Primitive semantics in detail

**Play stimulus.** Presents a single item through the auditory channel. The item is addressed as (`item_id`, `asset_role`, `voice_profile_family`); resolution to an approved local asset is the Audio Asset Pipeline's responsibility. `Play` may apply a **bounded** `runtime_playback_rate`; if a required rate falls outside validated phonetic bounds, the protocol must request a *separately synthesized pedagogical variant* rather than time-stretch (consistent with the audio pipeline's principle B). `Play` observes onset/offset only; it never grades.

**Pause.** Inserts silence. Semantically, a pause is a **cognitive workspace**: anticipation before a reveal, internal production, or memory retrieval. Pause duration is derived at runtime from a *duration policy* (bounds + adaptation inputs), never a fixed provider setting. Pause is the **primary adaptation lever** and the main reason MindTune protocols are eyes-closable.

**Expect internal response.** Opens a response window during which the learner produces the target *internally* (default) or *overtly* (if the protocol enables overt capture). Because internal responses are unobservable, `Expect` primarily records a **latency proxy** (time until the learner signals readiness, or a fixed window) and, when enabled, an **overt marker** (a spoken repetition captured only as timing/energy, not recognized — recognition is out of scope). `Expect` never fabricates correctness.

**Confirm.** Presents the correct target after an attempt, closing the anticipation/recall loop. In internal-production protocols, `Confirm` is how the learner self-assesses; the engine records a **self-confirmation signal** (e.g. a "got it / missed it" marker) as evidence, not as machine-graded truth. `Confirm` may be *conditional* (only shown on request, or after a threshold).

**Repeat.** Re-presents a step or group. Repetition count is bounded and adaptive (more repeats on struggle, fewer on fluency). Repeat is distinct from `Consolidation` protocols: repeat is *within-execution*, consolidation is *across-time*.

**Branch.** Chooses among alternative continuations based on observations and/or EEG context. The chosen branch and its **reason** are always recorded. Branch is the primitive through which difficulty progression, recovery entry, and item selection are expressed.

**Transition.** Moves execution to another protocol state or block (e.g. from a main block to a consolidation block, or into recovery). Transition records its reason and preserves replayability.

**Wait.** A fixed/bounded idle unrelated to a specific expected response (e.g. inter-trial interval, settling time). Distinguished from `Pause` (which is *for* a cognitive act) and rarely adapted.

**Observe.** Explicitly samples evidence: behavioral (latency, overt-response markers, confirmation signals) and/or an EEG-context reference (a pointer to a context window, never raw signal, never a verdict). `Observe` is the single point where evidence enters the adaptation system.

**Score.** Interprets accumulated evidence into a domain outcome **via the domain adapter**. In many internal-speech protocols there is no machine `Score` at all — only recorded self-confirmation. `Score` never runs on EEG alone (§9).

**Record.** Emits a durable execution event (see §12, §15). Every semantically meaningful moment (`Play`, `Pause` chosen, `Expect` window, `Confirm`, adaptation decision, `Transition`) is recorded for replay/audit.

**Explain.** Provides explanatory/instructional content. **`Explain` is a configuration/review-phase primitive** — it must not be required during eyes-closed execution. It exists so protocols can carry their own onboarding/debrief text without polluting the execution stream.

### 6.3 Primitive composition rules

- Every observation-bearing step must be reachable by `Record` so the execution is fully replayable.
- `Expect` should be followed (eventually) by `Confirm` unless the protocol is explicitly production-only with deferred confirmation.
- `Branch`/`Transition` decisions must cite the observations/policy that produced them.
- No primitive may call a TTS provider directly; only `Play` touches audio, and only via the pipeline over **approved local assets** (never synchronous provider calls in execution).
- Adaptation may only adjust the *bounded parameters* enumerated in §8; it may not invent new primitives or restructure a protocol's objective mid-execution.

### 6.4 Primitive-to-MPE contract mapping (reconciliation)

| Primitive | MPE typed-model / event expression |
|---|---|
| `Play stimulus` | `Instruction(instruction_type=PRESENT_STIMULUS)` → `StimulusRequest` → `RenderedStimulus` → `stimulus_started` / `stimulus_completed` |
| `Pause` | `WAIT_DURATION` or inter-`Instruction` silence; duration chosen by `AdaptationDecision.target_dimension=pause_duration` |
| `Expect internal response` | `Instruction(instruction_type=INSTRUCT_COVERT_RETRIEVAL)` + optional `ResponseWindow` for an overt marker |
| `Expect overt response` | `Instruction(instruction_type=REQUEST_OVERT_RESPONSE)` + `ResponseWindow` + evaluation pipeline |
| `Confirm` | `PRESENT_STIMULUS` of a `confirmation` asset, optionally followed by `FeedbackEvent(feedback_category=KNOWLEDGE)` |
| `Repeat` | `ScheduleDecision` to re-select a `Trial`/`Block`, or `Block.exit_condition` loop |
| `Branch` | `ScheduleDecision` + `AdaptationDecision` with `source_event_ids` and `reason` |
| `Transition` | `ScheduleDecision.decision_type` (`next_block`, `insert_review`, `offer_break`, `session_end`) or `recovery_inserted` |
| `Wait` | `WAIT_DURATION` (rarely adapted) |
| `Observe` | `OPEN_RESPONSE_WINDOW` + `observation_received` |
| `Score` | `captured_response_created` → `response_interpreted` → `domain_response_normalized` → `evaluation_completed` / `abstained` / `failed` |
| `Record` | Implicit; every semantically meaningful moment emits an `Event` with `session_sequence_number` and `provenance` |
| `Explain` | `Program`/`Protocol`/`ProtocolVersion` metadata or onboarding content; not an in-session `Instruction` during eyes-closed execution |

---

## 7. Per-protocol specifications

Each protocol is specified with the **thirteen mandatory fields**: Purpose · Expected cognitive process · Inputs · Outputs · Required assets · Behavioral measurements · Optional EEG influence · Adaptation opportunities · Typical duration · Typical difficulty progression · Replay requirements · Failure modes · Success criteria.

**Conventions used throughout §7:**

- *Inputs/Outputs* are conceptual, not schemas (see §12).
- *Required assets* are stated as **asset roles** over abstract items (`prompt`, `confirmation`, `natural`, `pedagogical_slow`, `minimal_pair`, `sentence_context`, `instruction`), resolved by the Audio Asset Pipeline. No provider appears.
- *Optional EEG influence* is always bounded and non-authoritative (§9).
- Hebrew examples are **illustrative only** and never part of the definition.
- *Replay requirements* distinguish **event replay** (reconstruct what happened) from **protocol replay** (re-run the protocol logic against recorded inputs) — see §15.

### Protocol specification template (reference)

```
Protocol: <name>          Category: <category>          Primary goal: <goal>
Purpose:                  <why it exists>
Cognitive process:        <what the learner's mind does>
Inputs:                   <items, relations, prior state, config>
Outputs:                  <observations, outcomes, state deltas>
Required assets:          <asset roles over items>
Behavioral measurements:  <what is observed>
Optional EEG influence:   <bounded modulation only>
Adaptation opportunities: <pacing/repetition/selection/progression levers>
Typical duration:         <per-item and per-session>
Difficulty progression:   <how difficulty increases>
Replay requirements:      <event vs protocol replay guarantees>
Failure modes:            <what can go wrong>
Success criteria:         <when the objective is met>
```

---

### 7.1 Encoding protocols

Encoding protocols establish new representations/associations. They are pause-generous and confirmation-heavy, with low initial retrieval demand.

#### 7.1.1 Vocabulary Encoding

- **Purpose.** Form a durable association between an item and its meaning/label.
- **Cognitive process.** Attentive listening → brief anticipation → confirmation; the learner binds form↔meaning. (Example: hear an Italian prompt, anticipate, hear the Hebrew word.)
- **Inputs.** Item set with `associate(a,b)` relation; voice profile family; session length; difficulty band.
- **Outputs.** Per-item exposure records; latency-to-confirm proxies; repetition demand; encoding-strength estimate delta (via history).
- **Required assets.** `prompt` (label/meaning side), `confirmation` (target side), optionally `natural` for the target.
- **Behavioral measurements.** Latency to self-confirm; requested repeats; optional overt-response markers.
- **Optional EEG influence.** May lengthen the pre-confirmation pause or increase repetition probability under low-engagement context; never marks the association learned.
- **Adaptation opportunities.** Pause duration; repetition count; item interleaving; introduction rate of new items.
- **Typical duration.** 4–10 s/item; 5–15 min/session.
- **Difficulty progression.** Fewer repetitions; shorter pauses; more new items per block; interleave confusable items later.
- **Replay requirements.** Event replay reconstructs exact stimuli/pauses/confirmations; protocol replay reproduces selection/adaptation given recorded observations.
- **Failure modes.** Over-repetition (boredom); too-fast introduction (no encoding); asset missing (fallback variant or skip+log).
- **Success criteria.** Declining repetition demand and latency across exposures; positive transfer to Recall protocols.

#### 7.1.2 Morphology Encoding

- **Purpose.** Encode a base form together with the *dimension* along which it varies (so later Transformation is possible).
- **Cognitive process.** Hear base → hear a marked variant → notice the systematic change → confirm the mapping. (Example: lemma → a single inflected form, attention drawn to the changed morpheme.)
- **Inputs.** Items with `inflect(base→variant, dimension)`; the dimension label (abstract); difficulty band.
- **Outputs.** Exposure records tagged by dimension; latency; repetition demand.
- **Required assets.** `prompt` (base), `confirmation` (variant), optional `pedagogical_slow` variant to expose the morphological contrast.
- **Behavioral measurements.** Latency; repeats; optional overt marker.
- **Optional EEG influence.** Bounded pause extension under low-engagement; never labels the dimension "understood".
- **Adaptation opportunities.** Pause; repetition; number of dimensions introduced per block; slow-variant usage.
- **Typical duration.** 5–12 s/item; 6–15 min/session.
- **Difficulty progression.** Add dimensions; reduce slow-variant scaffolding; interleave dimensions.
- **Replay requirements.** As 7.1.1, plus dimension tags recorded.
- **Failure modes.** Learner mishears the contrast (mitigate with `pedagogical_slow`); dimension ambiguity (adapter must disambiguate).
- **Success criteria.** Reduced latency; readiness to attempt Transformation on that dimension.

#### 7.1.3 Root Encoding

- **Purpose.** Encode a generator ("root") and its role as a family source. (Domain example: a triconsonantal Hebrew root.)
- **Cognitive process.** Hear generator → hear a derivative → bind generator↔family membership.
- **Inputs.** `family(root, members)`; `derive(root→member)`; difficulty band.
- **Outputs.** Root-exposure records; derivative associations; latency.
- **Required assets.** `prompt` (root, possibly abstracted as a spoken pattern), `confirmation` (derivative), optional `natural` derivative.
- **Behavioral measurements.** Latency; repeats; family-coverage progress.
- **Optional EEG influence.** Bounded pause/repetition modulation only.
- **Adaptation opportunities.** Number of derivatives per root; pause; interleaving of roots.
- **Typical duration.** 5–12 s/item; 6–15 min.
- **Difficulty progression.** More derivatives per root; interleave multiple roots; move toward Root Recognition.
- **Replay requirements.** Record root/derivative identities and family linkage.
- **Failure modes.** Root not perceivable in isolation (domain-dependent; adapter may present via a canonical carrier); missing derivative assets.
- **Success criteria.** Learner anticipates further derivatives; transfer to Root Recognition.

#### 7.1.4 Pattern Encoding

- **Purpose.** Encode an abstract pattern/template that generates many surface items (domain example: a morphological *mishkal*/vowel pattern; in Piano Lab, a scale/chord shape).
- **Cognitive process.** Hear multiple instances of one pattern → abstract the invariant → confirm the pattern identity.
- **Inputs.** `derive(pattern→instance)`; a set of instances sharing the pattern; difficulty band.
- **Outputs.** Pattern-exposure records; abstraction-progress proxies.
- **Required assets.** `prompt` (instance or pattern cue), `confirmation` (instances), optional `pedagogical_slow`.
- **Behavioral measurements.** Latency; repeats; cross-instance consistency.
- **Optional EEG influence.** Bounded pause/repetition only.
- **Adaptation opportunities.** Instance variety; pause; introduction rate.
- **Typical duration.** 6–12 s/item; 6–15 min.
- **Difficulty progression.** More diverse instances; interleave patterns; move to Pattern Recognition.
- **Replay requirements.** Record pattern id and instance ids.
- **Failure modes.** Instances too similar (no abstraction) or too diverse (no pattern); adapter tunes instance set.
- **Success criteria.** Learner predicts new instances of the pattern.

#### 7.1.5 Sentence Encoding

- **Purpose.** Encode short connected utterances as wholes (chunking), bridging vocabulary and comprehension.
- **Cognitive process.** Hear a short sentence → optional segmented replay → hold the whole → confirm meaning. (`contains(sentence, words)`.)
- **Inputs.** Short sentences; component items; difficulty band.
- **Outputs.** Sentence-exposure records; segmentation events; latency.
- **Required assets.** `sentence_context` (whole sentence), optional per-word `confirmation`, optional `pedagogical_slow` sentence.
- **Behavioral measurements.** Latency; requested segment replays; repeats.
- **Optional EEG influence.** Bounded pause and segmentation-density modulation.
- **Adaptation opportunities.** Segment vs whole; pause between segments; sentence length; slow-variant usage.
- **Typical duration.** 8–20 s/item; 6–15 min.
- **Difficulty progression.** Longer sentences; fewer segments; faster delivery within bounds.
- **Replay requirements.** Record whole/segment structure and which was played.
- **Failure modes.** Sentence too long for working memory (segment); missing sentence asset.
- **Success criteria.** Learner holds/repeats the sentence; transfer to Listening.

---

### 7.2 Recall protocols

Recall protocols strengthen retrieval. The **anticipation pause before confirmation** is the active ingredient; retrieval effort (not exposure) drives gains.

#### 7.2.1 Immediate Recall

- **Purpose.** Strengthen retrieval immediately after encoding (short lag).
- **Cognitive process.** Cue → *retrieve internally now* → confirm. (Example: Italian prompt → recall Hebrew → hear Hebrew.)
- **Inputs.** Recently encoded items; `associate`; difficulty band.
- **Outputs.** Retrieval-latency proxies; self-confirmation; success-proxy deltas.
- **Required assets.** `prompt`, `confirmation`.
- **Behavioral measurements.** Anticipation-window latency; self-confirm (got/missed); optional overt marker.
- **Optional EEG influence.** Bounded anticipation-window extension; repetition probability; never scores got/missed.
- **Adaptation opportunities.** Anticipation-window length; repetition; interleaving; drop-to-Encoding on repeated miss.
- **Typical duration.** 4–8 s/item; 5–12 min.
- **Difficulty progression.** Shorter windows; less cueing; more items; longer lag → Delayed Recall.
- **Replay requirements.** Record cue, window length chosen, confirmation, self-confirm signal.
- **Failure modes.** Window too short (no retrieval attempt) or too long (disengagement); adapt window.
- **Success criteria.** Increasing self-confirmed success at shorter windows.

#### 7.2.2 Delayed Recall

- **Purpose.** Strengthen retrieval after a delay/interference (later in session or across sessions).
- **Cognitive process.** As Immediate Recall, but with intervening material or time.
- **Inputs.** Previously encoded items with elapsed lag; spacing/history state.
- **Outputs.** Retrieval success at lag; latency; spacing-state deltas.
- **Required assets.** `prompt`, `confirmation`.
- **Behavioral measurements.** Latency; self-confirm; lag since last success.
- **Optional EEG influence.** Bounded window/repetition modulation.
- **Adaptation opportunities.** Which items are due (history-based); window; repetition; route failures to Recovery/Consolidation.
- **Typical duration.** 4–8 s/item; 5–15 min.
- **Difficulty progression.** Longer lags; more interference; less cueing.
- **Replay requirements.** Record lag, due-selection reason, outcome.
- **Failure modes.** Excessive forgetting (route to re-encode); scheduling errors (history integrity).
- **Success criteria.** Retention at increasing lags; stable spacing schedule.

#### 7.2.3 Free Recall

- **Purpose.** Retrieve multiple items from a set without item-specific cues.
- **Cognitive process.** Given a category/context cue → internally enumerate members → confirm against the set.
- **Inputs.** A `family`/category; membership; difficulty band.
- **Outputs.** Count/coverage proxies; order; latency between productions.
- **Required assets.** `instruction`/context cue; `confirmation` for each member (on reveal).
- **Behavioral measurements.** Number of self-confirmed productions; inter-production latency; coverage of the set.
- **Optional EEG influence.** Bounded pause/enumeration-window modulation; never counts items for the learner.
- **Adaptation opportunities.** Set size; enumeration-window length; cueing strength.
- **Typical duration.** 15–45 s/set; 6–15 min.
- **Difficulty progression.** Larger sets; weaker cues; longer lag.
- **Replay requirements.** Record cue, window, reveal order, self-confirm markers.
- **Failure modes.** No overt signal to count productions (rely on self-confirm + optional overt markers); set too large.
- **Success criteria.** Increasing self-reported coverage; faster enumeration.

#### 7.2.4 Recognition Recall

- **Purpose.** Retrieve via recognition (easier than free recall); useful early or in Recovery.
- **Cognitive process.** Hear a target among/with alternatives → recognize → confirm.
- **Inputs.** Target + distractors (`contrast`); difficulty band.
- **Outputs.** Recognition correctness (overt if enabled); latency.
- **Required assets.** `prompt` (question), `natural`/`confirmation` for options.
- **Behavioral measurements.** Choice (if overt), latency, self-confirm.
- **Optional EEG influence.** Bounded pacing modulation; never sets the choice.
- **Adaptation opportunities.** Distractor similarity; number of options; pacing.
- **Typical duration.** 5–10 s/item; 5–12 min.
- **Difficulty progression.** More/closer distractors; move to Free Recall.
- **Replay requirements.** Record options presented, choice/self-confirm, outcome.
- **Failure modes.** Distractors too easy/hard; overt capture unavailable (fall back to self-confirm).
- **Success criteria.** High recognition accuracy → progress to harder recall.

---

### 7.3 Transformation protocols

Transformation protocols train systematic rule application to *produce* a derived form. A cue names the transformation dimension; the learner produces; confirmation follows. These are the most "generative" protocols.

**Shared template for 7.3.x.** Because Inflection, Conjugation, Number, Gender, Person, Tense, Voice, and Derivation share structure, they are specified once as a family and then differentiated. Each is a distinct protocol (distinct dimension), but shares the fields below except where noted.

- **Purpose (family).** Train application of a transformation rule along one dimension to produce the derived form from a base.
- **Cognitive process (family).** Hear base + dimension cue → internally (or overtly) produce the transformed form → confirm against the correct form → note error type on mismatch.
- **Inputs (family).** `inflect(base→variant, dimension)` or `derive(base→derived)`; the dimension; difficulty band; prior error history.
- **Outputs (family).** Production attempts (self-confirm/overt); error typing (via adapter `Score`); latency; per-dimension mastery deltas.
- **Required assets (family).** `prompt` (base + dimension cue, possibly `instruction`), `confirmation` (correct derived form), optional `pedagogical_slow`.
- **Behavioral measurements (family).** Production latency; self-confirm or overt correctness; error category (from adapter).
- **Optional EEG influence (family).** Bounded production-window extension; repetition probability; hold difficulty; never determines correctness or error type.
- **Adaptation opportunities (family).** Production-window length; repetition; dimension selection; difficulty band; route persistent errors to Encoding/Recovery.
- **Typical duration (family).** 5–10 s/item; 6–15 min.
- **Difficulty progression (family).** Multiple simultaneous dimensions; irregular forms; less cueing; faster pacing (bounded).
- **Replay requirements (family).** Record base, dimension cue, window, confirmation, self-confirm/overt outcome, error type.
- **Failure modes (family).** Ambiguous cue (dimension not clear from audio → use `instruction`); irregulars miscategorized (adapter responsibility); missing asset.
- **Success criteria (family).** Rising self-confirmed/overt production accuracy per dimension; transfer to combined dimensions.

**Differentiation:**

- **7.3.1 Inflection** — general systematic variation of a base along a grammatical dimension (superset framing for number/gender/person/tense/voice in inflecting domains).
- **7.3.2 Conjugation** — verb-specific inflection across a paradigm (example: Hebrew binyan/tense/person paradigms). Dimension = paradigm slot.
- **7.3.3 Number** — singular↔plural (and dual, where the domain has it). Dimension = number.
- **7.3.4 Gender** — masculine↔feminine (or the domain's gender system). Dimension = gender.
- **7.3.5 Person** — 1st/2nd/3rd (and the domain's person distinctions). Dimension = person.
- **7.3.6 Tense** — past/present/future (and aspect where relevant). Dimension = tense/aspect.
- **7.3.7 Voice** — active/passive/reflexive etc. Dimension = voice.
- **7.3.8 Derivation** — produce a *new lexeme* from a base/root via a derivational rule (distinct from inflection: changes lexical identity, not just grammatical marking). Example: root → agent noun. Additional failure mode: derivation may be non-productive/lexicalized (adapter flags exceptions).

---

### 7.4 Recognition protocols

Recognition protocols sharpen **discrimination** between confusable items. They present contrasts and elicit a discrimination judgment (internal or overt).

#### 7.4.1 Minimal Pairs

- **Purpose.** Discriminate items differing minimally (phonetic/morphological). (Example: two Hebrew words differing by one vowel or a guttural.)
- **Cognitive process.** Hear A and B (or A then a target) → detect the distinguishing feature → judge same/different or identify.
- **Inputs.** `contrast(a,b)` pairs; the contrast dimension; difficulty band.
- **Outputs.** Discrimination correctness; latency; confusion matrix deltas.
- **Required assets.** `minimal_pair` assets (both members), `prompt`/`instruction`.
- **Behavioral measurements.** Judgment (overt) or self-confirm; latency.
- **Optional EEG influence.** Bounded pacing; never sets the judgment.
- **Adaptation opportunities.** Pair difficulty (feature salience); pacing; which contrasts are drilled (history).
- **Typical duration.** 4–8 s/pair; 5–12 min.
- **Difficulty progression.** Less salient contrasts; faster pacing; embed in `sentence_context`.
- **Replay requirements.** Record both members, judgment, outcome.
- **Failure modes.** Assets not truly minimal (adapter/pipeline responsibility); playback-rate distortion of the contrast (use natural variants).
- **Success criteria.** Rising discrimination accuracy on low-salience contrasts.

#### 7.4.2 Root Recognition

- **Purpose.** Identify the shared generator across surface-different items.
- **Cognitive process.** Hear a derivative → identify its root/family (internally or by choosing).
- **Inputs.** `family(root, members)`; distractor roots; difficulty band.
- **Outputs.** Identification correctness; latency; family-coverage.
- **Required assets.** `prompt` (derivative), `confirmation` (root/family), option assets.
- **Behavioral measurements.** Choice/self-confirm; latency.
- **Optional EEG influence.** Bounded pacing only.
- **Adaptation opportunities.** Distractor closeness; number of families; pacing.
- **Typical duration.** 5–10 s/item; 5–12 min.
- **Difficulty progression.** Closer distractor roots; less transparent derivatives.
- **Replay requirements.** Record derivative, options, outcome.
- **Failure modes.** Opaque derivations (adapter flags); missing assets.
- **Success criteria.** Accurate root attribution across opaque derivatives.

#### 7.4.3 Pattern Recognition

- **Purpose.** Identify the abstract pattern shared by surface-different instances.
- **Cognitive process.** Hear an instance → identify its pattern (internally or by choosing).
- **Inputs.** `derive(pattern→instance)`; distractor patterns; difficulty band.
- **Outputs.** Pattern-identification correctness; latency.
- **Required assets.** `prompt` (instance), `confirmation` (pattern), option assets.
- **Behavioral measurements.** Choice/self-confirm; latency.
- **Optional EEG influence.** Bounded pacing only.
- **Adaptation opportunities.** Pattern similarity; number of patterns; pacing.
- **Typical duration.** 5–10 s/item; 5–12 min.
- **Difficulty progression.** More/closer patterns; novel instances.
- **Replay requirements.** Record instance, options, outcome.
- **Failure modes.** Instances ambiguous across patterns; adapter tunes set.
- **Success criteria.** Accurate pattern attribution to novel instances.

#### 7.4.4 Error Detection

- **Purpose.** Detect that a presented form is *incorrect* (and optionally identify the error). Trains an internal correctness model.
- **Cognitive process.** Hear a form (sometimes wrong) → judge correct/incorrect → optionally locate the error → confirm.
- **Inputs.** Correct forms and adapter-generated plausible errors; difficulty band.
- **Outputs.** Detection accuracy; false-alarm/miss rates; latency.
- **Required assets.** `prompt` (possibly-erroneous form), `confirmation` (correct form + verdict).
- **Behavioral measurements.** Correct/incorrect judgment (overt or self-confirm); latency; error-localization (optional).
- **Optional EEG influence.** Bounded pacing; never sets the verdict.
- **Adaptation opportunities.** Error subtlety; base rate of errors; pacing.
- **Typical duration.** 5–10 s/item; 5–12 min.
- **Difficulty progression.** Subtler errors; lower error base rate (more vigilance).
- **Replay requirements.** Record the (possibly erroneous) stimulus, verdict, outcome.
- **Failure modes.** Error not perceivable audibly; adapter must ensure errors are auditory-detectable.
- **Success criteria.** High detection with low false alarms on subtle errors.

---

### 7.5 Internal-speech protocols

Internal-speech protocols train **production on cue**. Correctness is **self-confirmed**, not machine-graded, unless an overt variant is explicitly enabled (and even then only timing/energy is captured — no recognition). These are the purest expression of the eyes-closed principle.

#### 7.5.1 Silent production

- **Purpose.** Produce a target internally on cue (no audio output by the learner).
- **Cognitive process.** Cue → internally articulate the full target → confirm.
- **Inputs.** Items; cue type; difficulty band.
- **Outputs.** Production-window timing; self-confirm; optional overt marker.
- **Required assets.** `prompt` (cue), `confirmation` (target).
- **Behavioral measurements.** Window latency; self-confirm; optional overt onset timing.
- **Optional EEG influence.** Bounded window extension; repetition; never asserts the target was produced.
- **Adaptation opportunities.** Window length; repetition; cue strength.
- **Typical duration.** 4–8 s/item; 5–12 min.
- **Difficulty progression.** Weaker cues; shorter windows; longer targets.
- **Replay requirements.** Record cue, window, confirmation, self-confirm.
- **Failure modes.** No observable production (inherent — rely on self-confirm); window mis-set.
- **Success criteria.** Faster self-confirmed production; transfer to Transformation/Recall.

#### 7.5.2 Silent repetition

- **Purpose.** Internally rehearse a just-heard target (subvocal repetition) to strengthen the trace.
- **Cognitive process.** Hear target → internally repeat N times → confirm.
- **Inputs.** Items; repetition count policy; difficulty band.
- **Outputs.** Rehearsal-window timing; repetition count; self-confirm.
- **Required assets.** `natural`/`confirmation` (target).
- **Behavioral measurements.** Window timing; requested extra repeats.
- **Optional EEG influence.** Bounded repetition-count and window modulation.
- **Adaptation opportunities.** Repetition count; window; spacing.
- **Typical duration.** 4–10 s/item; 5–12 min.
- **Difficulty progression.** Fewer external repeats; longer targets; sentence-level.
- **Replay requirements.** Record target, repetition policy applied.
- **Failure modes.** Rote without engagement (interleave with Recall).
- **Success criteria.** Reduced external repetition demand; improved downstream recall.

#### 7.5.3 Mental completion

- **Purpose.** Complete a partially presented item/sequence internally (cloze via audio).
- **Cognitive process.** Hear the start → internally complete → confirm the full form.
- **Inputs.** Items/sequences with a defined truncation point; difficulty band.
- **Outputs.** Completion-window timing; self-confirm; optional overt.
- **Required assets.** `prompt` (partial), `confirmation` (full).
- **Behavioral measurements.** Window latency; self-confirm.
- **Optional EEG influence.** Bounded window/repetition modulation.
- **Adaptation opportunities.** Truncation depth; window; cueing.
- **Typical duration.** 5–10 s/item; 5–12 min.
- **Difficulty progression.** Earlier truncation (more to complete); less context.
- **Replay requirements.** Record truncation point, completion window, outcome.
- **Failure modes.** Truncation point ambiguous; multiple valid completions (adapter constrains).
- **Success criteria.** Faster/accurate completion at deeper truncation.

#### 7.5.4 Mental anticipation

- **Purpose.** Predict the *next* item before it is presented (pure anticipation).
- **Cognitive process.** In a known sequence/pattern, before the next stimulus, internally predict it → hear it → confirm prediction.
- **Inputs.** `sequence`/`pattern` with predictable continuation; difficulty band.
- **Outputs.** Anticipation-window timing; self-confirm of prediction; latency.
- **Required assets.** `natural`/`confirmation` (the anticipated item).
- **Behavioral measurements.** Window latency; self-confirm (predicted correctly?).
- **Optional EEG influence.** Bounded anticipation-window modulation; **notably**, EEG anticipation/expectation context may adjust the pre-stimulus pause — still never scores the prediction.
- **Adaptation opportunities.** Anticipation-window length; sequence predictability; pacing.
- **Typical duration.** 3–7 s/item; 5–12 min.
- **Difficulty progression.** Less predictable sequences; shorter windows.
- **Replay requirements.** Record sequence position, window, anticipated vs presented, self-confirm.
- **Failure modes.** Sequence not actually predictable (no basis for anticipation); adapter ensures predictability gradient.
- **Success criteria.** Rising self-confirmed prediction accuracy; the hallmark MindTune "flow" state.

---

### 7.6 Listening protocols

Listening protocols build **comprehension and structural perception** from connected input. They are longer and lower-interaction; adaptation acts on **density and pause insertion**, not per-item grading.

#### 7.6.1 Immersion

- **Purpose.** Sustained exposure to connected input to build comprehension and prosody familiarity.
- **Cognitive process.** Continuous/segmented listening with light internal tracking; eyes closed.
- **Inputs.** Connected passages; difficulty band; segmentation policy.
- **Outputs.** Attention proxies; segment-replay requests; optional comprehension-check outcomes.
- **Required assets.** `sentence_context`/passage assets, optional `pedagogical_slow`.
- **Behavioral measurements.** Segment-replay requests; sustained-listening duration; optional comprehension checks (light `Expect`/`Confirm`).
- **Optional EEG influence.** Bounded **density** modulation (insert more pauses / slow segmentation under low-engagement or high-load context); may trigger `Transition` to Recovery.
- **Adaptation opportunities.** Segmentation density; pause insertion; passage difficulty; slow-variant usage.
- **Typical duration.** 3–15 min continuous; session-length driven.
- **Difficulty progression.** Longer passages; fewer pauses; faster natural speech; less familiar content.
- **Replay requirements.** Record passage id, segmentation applied, pauses inserted; protocol replay reproduces density decisions.
- **Failure modes.** Overload (insert pauses / slow / recover); disengagement (adapt density).
- **Success criteria.** Longer sustained comprehension at higher density.

#### 7.6.2 Focused listening

- **Purpose.** Attend to a specific feature within connected input (e.g. detect every occurrence of a target form).
- **Cognitive process.** Listen with a set target → internally flag occurrences → confirm.
- **Inputs.** Passage + a target feature; difficulty band.
- **Outputs.** Detection proxies; latency; occurrence coverage.
- **Required assets.** `instruction` (the target to attend to), passage assets, `confirmation`.
- **Behavioral measurements.** Occurrence detections (overt markers/self-confirm); latency.
- **Optional EEG influence.** Bounded density/pause modulation; never counts occurrences.
- **Adaptation opportunities.** Target frequency; passage speed; pauses at occurrences.
- **Typical duration.** 3–10 min.
- **Difficulty progression.** Rarer targets; faster speech; multiple simultaneous targets.
- **Replay requirements.** Record passage, target, occurrences, detections.
- **Failure modes.** Target imperceptible at speed (slow variant); ambiguous occurrences.
- **Success criteria.** Accurate detection at natural speed.

#### 7.6.3 Comparative listening

- **Purpose.** Compare two connected inputs to perceive a systematic difference (register, tense, speaker, variant).
- **Cognitive process.** Hear A then B → perceive the systematic difference → confirm.
- **Inputs.** Paired passages differing along one dimension; difficulty band.
- **Outputs.** Difference-identification correctness; latency.
- **Required assets.** Two `sentence_context`/passage assets; `confirmation`.
- **Behavioral measurements.** Judgment/self-confirm; latency.
- **Optional EEG influence.** Bounded pacing/pause modulation.
- **Adaptation opportunities.** Difference salience; passage length; pause between A/B.
- **Typical duration.** 20–60 s/pair; 5–12 min.
- **Difficulty progression.** Subtler differences; longer passages.
- **Replay requirements.** Record both passages, judgment, outcome.
- **Failure modes.** Difference not audible; assets not truly minimal at passage level.
- **Success criteria.** Reliable perception of subtle systematic differences.

---

### 7.7 Consolidation protocols

Consolidation protocols **stabilize and space** existing representations across time. They draw items from **history/spacing state** and interleave categories. They are primarily *scheduling-driven*.

#### 7.7.1 Adaptive review

- **Purpose.** Review items whose retention is estimated to be decaying, prioritized by need.
- **Cognitive process.** Retrieve/confirm due items (mostly Recall-like steps) selected by history.
- **Inputs.** Spacing/history state; due-item queue; difficulty band.
- **Outputs.** Updated retention estimates; spacing-state deltas.
- **Required assets.** `prompt`, `confirmation` per item (roles depend on embedded step type).
- **Behavioral measurements.** Retrieval success/latency per due item.
- **Optional EEG influence.** Bounded pacing/repetition; may trigger Recovery on sustained struggle.
- **Adaptation opportunities.** Item selection (history-based, primary); pacing; repetition; next-review scheduling.
- **Typical duration.** 5–15 min.
- **Difficulty progression.** Longer intervals as retention stabilizes.
- **Replay requirements.** Record due-selection reasons, outcomes, schedule updates.
- **Failure modes.** Scheduling drift (history integrity); over-review (respect spacing).
- **Success criteria.** Flattening forgetting curves; lengthening stable intervals.

#### 7.7.2 Spaced reinforcement

- **Purpose.** Apply expanding-interval reinforcement to items nearing mastery.
- **Cognitive process.** Brief retrieval at increasing spacing.
- **Inputs.** Near-mastered items; spacing schedule.
- **Outputs.** Confirmations at expanding intervals; mastery-state deltas.
- **Required assets.** `prompt`, `confirmation`.
- **Behavioral measurements.** Success at each interval; latency.
- **Optional EEG influence.** Bounded pacing only.
- **Adaptation opportunities.** Interval expansion rate; pacing.
- **Typical duration.** Short touches spread across sessions.
- **Difficulty progression.** Increasing intervals; eventual retirement to maintenance.
- **Replay requirements.** Record interval, outcome, schedule delta.
- **Failure modes.** Interval expansion too aggressive (lapses) — adapt schedule.
- **Success criteria.** Sustained success at long intervals.

#### 7.7.3 Mixed review

- **Purpose.** Interleave items/categories to promote discrimination and durable, flexible retrieval.
- **Cognitive process.** Rapid switching across item types/protocols (interleaving effect).
- **Inputs.** Mixed pool across categories; difficulty band.
- **Outputs.** Cross-category retrieval outcomes; interleaving-cost proxies.
- **Required assets.** Roles as required by embedded step types.
- **Behavioral measurements.** Success/latency across switches.
- **Optional EEG influence.** Bounded pacing; may reduce switching under high load.
- **Adaptation opportunities.** Switch rate; mix composition; pacing.
- **Typical duration.** 6–15 min.
- **Difficulty progression.** More switching; more categories; less blocking.
- **Replay requirements.** Record mix composition and switch sequence.
- **Failure modes.** Excessive switching cost (reduce switching, recover).
- **Success criteria.** Maintained accuracy under high interleaving.

---

### 7.8 Recovery protocols

Recovery protocols **restore confidence and reduce load** after sustained difficulty. They are deliberately easy and high-confirmation, and are typically *entered by adaptation* (behavioral struggle and/or EEG-context, as a modulator only), not chosen directly.

#### 7.8.1 Reduced-load mode

- **Purpose.** Lower cognitive load immediately after detected struggle/overload.
- **Cognitive process.** Easy, well-known items; generous pauses; heavy confirmation; minimal retrieval demand.
- **Inputs.** Well-mastered items; current struggle signals; difficulty floor.
- **Outputs.** Recovered success proxies; load-reduction confirmation.
- **Required assets.** `natural`/`confirmation` (familiar items), `instruction` (reassurance/framing).
- **Behavioral measurements.** Success rate at low load; latency normalization.
- **Optional EEG influence.** May *trigger entry* and modulate how long reduced-load persists (bounded); exit still requires behavioral recovery, not EEG alone.
- **Adaptation opportunities.** Load level; duration; pause length; when to exit.
- **Typical duration.** 1–5 min, adaptive.
- **Difficulty progression.** Gradual re-escalation to prior band once recovered.
- **Replay requirements.** Record entry reason (behavioral + optional EEG context), duration, exit reason.
- **Failure modes.** Premature exit (relapse); over-long recovery (boredom) — bound duration.
- **Success criteria.** Restored success/latency; smooth return to prior difficulty.

#### 7.8.2 Confidence rebuilding

- **Purpose.** Rebuild self-efficacy through a run of achievable successes.
- **Cognitive process.** Sequence of high-probability-success items with clear confirmation.
- **Inputs.** Items with high recent success; difficulty floor.
- **Outputs.** Success streak; confidence proxies (self-confirm positivity).
- **Required assets.** `prompt`, `confirmation` (easy items), `instruction`.
- **Behavioral measurements.** Success streak length; self-confirm positivity; latency.
- **Optional EEG influence.** Bounded pacing/duration; may inform exit readiness (with behavioral corroboration).
- **Adaptation opportunities.** Success-probability targeting; streak length; pacing.
- **Typical duration.** 1–4 min.
- **Difficulty progression.** Slowly raise difficulty as streak holds.
- **Replay requirements.** Record item difficulty selection, streak, outcomes.
- **Failure modes.** Too easy (no confidence value); mis-estimated success probability.
- **Success criteria.** Sustained success streak; positive self-confirmation; readiness to re-engage.

#### 7.8.3 Reinforcement cycles

- **Purpose.** Short, repeated reinforcement loops to re-stabilize shaky items before returning to main flow.
- **Cognitive process.** Tight `play → pause → expect → confirm → repeat` cycles on a small shaky set.
- **Inputs.** Recently failed/shaky items; difficulty floor.
- **Outputs.** Re-stabilization proxies; per-item recovery.
- **Required assets.** `prompt`, `confirmation`, optional `pedagogical_slow`.
- **Behavioral measurements.** Within-cycle success trend; latency.
- **Optional EEG influence.** Bounded repetition/pacing; may extend cycles under sustained low-engagement (bounded).
- **Adaptation opportunities.** Cycle count; set size; pacing; exit threshold.
- **Typical duration.** 1–5 min.
- **Difficulty progression.** Exit to Consolidation/Recall once stable.
- **Replay requirements.** Record cycle structure, per-cycle outcomes, exit reason.
- **Failure modes.** Endless cycling (bound cycles; escalate to re-encode); set too large.
- **Success criteria.** Shaky items re-stabilized; clean exit to main flow.

---

## 8. Adaptation model

Adaptation is how MPE personalizes execution in real time. This section defines the **four adaptation sources** and, for each, **exactly what it may influence**. The core discipline: sources are separated, each has a bounded scope, and every adaptation is a recorded, reasoned decision.

### 8.1 The four adaptation sources

| Source | Signal | Authority | May influence |
|---|---|---|---|
| **Behavior-based** | Overt/self-confirmed correctness, confirmation signals, choices | **Authoritative** for correctness | Everything below + item selection, progression, error routing |
| **Latency-based** | Response/production/anticipation timing | Strong proxy (not correctness) | Pause/window length, repetition, pacing, difficulty pacing |
| **History-based** | Prior outcomes, spacing state, mastery estimates | Authoritative for scheduling | Item selection, due scheduling, difficulty band, consolidation entry |
| **EEG-context** | Engagement/load/attention context windows | **Contextual only, never authoritative** | *Bounded* pause adjustment, repetition probability, temporary difficulty hold, consolidation/recovery entry, presentation density |

### 8.2 What each source may influence — precisely

**Behavior-based adaptation.** The only source that may establish or change **correctness / mastery outcomes**. Drives: marking an item correct/incorrect (where a domain `Score` exists), routing persistent errors to Encoding/Recovery, advancing difficulty on sustained success, and updating history. Behavior overrides all other sources when they conflict.

**Latency-based adaptation.** Latency is a **proxy for effort/fluency**, not correctness. It may adjust: anticipation/production **window length**, **pause** duration, **repetition** count, and **pacing** (within bounds). It may *suggest* difficulty changes but may not, by itself, mark mastery. Long latency never means "wrong"; it means "give more time / more support".

**History-based adaptation.** Governs **selection and scheduling**: which items are due, spacing intervals, difficulty band, when to enter Consolidation, and retirement to maintenance. It is authoritative for *what to present*, not for *what happened this trial*.

**EEG-context adaptation.** A **modulator layered on top** of the other three. It may only make the **bounded** adjustments in the table and always with behavioral corroboration for anything consequential. See §9 for the full policy. Every EEG-influenced change emits an `AdaptationDecision` with input context reference, policy rule, bounds, previous and new value.

### 8.3 Bounded-parameter set (the only things adaptation may change)

Adaptation may adjust **only** these runtime parameters, each within validated bounds declared by the protocol/voice profile:

1. **Pause / window duration** (per step).
2. **Runtime playback rate** (within validated phonetic bounds; otherwise select a pedagogical variant — never time-stretch beyond bounds).
3. **Repetition count** (bounded).
4. **Item selection** (from the due/eligible pool).
5. **Difficulty band / progression step** (bounded increments).
6. **Category/mode transitions** (to Consolidation or Recovery).
7. **Presentation density** (for Listening).

Adaptation may **not**: invent primitives, change a protocol's objective, alter recorded outcomes retroactively, or make irreversible learning-state changes without behavioral corroboration.

### 8.4 Adaptation resolution order

When multiple sources apply to the same parameter, resolve in this order (higher wins on conflict):

```
1. Behavior-based        (authoritative for correctness/mastery)
2. History-based         (authoritative for selection/scheduling)
3. Latency-based         (proxy: pacing/support)
4. EEG-context           (bounded modulation only)
```

EEG can *nudge* within bounds but is always the lowest-priority source and can never contradict a behavioral verdict.

### 8.5 Reversibility

All EEG- and latency-driven changes are **reversible** (pacing, pauses, temporary holds). Only behavior/history may produce **durable** state changes (mastery, scheduling). A temporary difficulty hold triggered by EEG must auto-release once behavioral evidence resumes, even absent further EEG input.

---

## 9. EEG policy (permanent architectural rule)

> **This section is a permanent architectural rule. It applies to every protocol, current and future, in every domain. It may not be weakened by any protocol definition, domain adapter, or implementation.**

### 9.1 The rule

**EEG is contextual. EEG is never authoritative. EEG never determines correctness. EEG never rewrites learning state directly.**

### 9.2 EEG MAY

- Adjust **pause/window duration** within bounded ranges.
- Adjust **repetition probability** within bounds.
- Trigger a **temporary difficulty hold** (bounded, auto-releasing).
- Trigger **transition to Consolidation or Recovery**.
- Adjust **presentation density** (Listening).
- Inform **exit readiness** from Recovery/holds — but only *together with* behavioral corroboration.

### 9.3 EEG MUST NOT

- **Mark a response correct or incorrect.**
- **Invent user performance** (fabricate that a target was produced/recalled).
- **Override explicit behavioral evidence.**
- **Directly rewrite curriculum / mastery / scheduling state.**
- **Make irreversible learning-state changes without behavioral corroboration.**

### 9.4 Mandatory reasoned event

Every EEG-influenced adaptation **must** emit a reasoned `AdaptationDecision` containing:

- **input context reference** — a pointer to the EEG context window (never raw signal in the protocol/event stream);
- **policy rule id** — which EEG policy rule fired;
- **bounded adjustment** — the parameter and its bounds;
- **previous value** and **new value**.

Absent all four fields, the adaptation is invalid and must not be applied. This makes every EEG influence auditable and replayable, and makes it trivial to *disable EEG entirely* by dropping EEG-sourced decisions during protocol replay (§15) — the session must still be coherent without them.

### 9.5 Rationale

EEG signals are noisy, individually variable, and non-diagnostic of linguistic/cognitive correctness. Treating EEG as authoritative would fabricate performance and corrupt the learning state. By confining EEG to bounded, reversible, corroborated modulation with mandatory reasoning, MindTune gains EEG's benefits (engagement/load-sensitive pacing) without ever letting it substitute for evidence.

---

## 10. Behavioral evidence model

Because much production is internal, MindTune distinguishes **evidence kinds** by how directly they bear on correctness.

| Evidence kind | Source primitive | Bears on correctness? | Notes |
|---|---|---|---|
| **Overt response correctness** | `Expect`(overt)+`Score` | Yes (when domain scores it) | Highest-confidence behavioral evidence |
| **Self-confirmation signal** | `Confirm` | Yes (learner-judged) | Primary for internal-speech protocols; learner asserts got/missed |
| **Choice / selection** | `Expect`(overt, discrete) | Yes | Recognition/discrimination protocols |
| **Response latency** | `Expect`/`Pause` timing | Proxy only | Effort/fluency, not correctness |
| **Overt production marker** | `Expect`(overt, non-recognized) | Weak proxy | Timing/energy only; no speech recognition (out of scope) |
| **Engagement/load context** | `Observe`(EEG) | No | Context only (§9) |

**Principles.** (1) The engine prefers the most direct evidence available but never fabricates it. (2) When only proxies exist, decisions are limited to pacing/support (§8.2). (3) Self-confirmation is trusted as the learner's own assessment for internal protocols and recorded as such — distinct from machine `Score`. (4) Absence of evidence is recorded as absence, never inferred as success or failure.

---

## 11. Protocol lifecycle

A protocol execution proceeds through seven lifecycle phases. Planning and Analysis bracket the eyes-closed core (Execution/Observation/Adaptation).

```
Planning ─▶ Execution ⇄ Observation ⇄ Adaptation ─▶ Completion ─▶ Replay ─▶ Analysis
             └──────────── in-session loop ────────────┘        (post-session, offline)
```

### 11.1 Planning

Before execution: select protocol + domain adapter; build an **ExecutionPlan** (item pool via history, initial difficulty band, session length, asset-role requirements). **Prefetch and validate all required audio assets** from the Audio Asset Pipeline (approved local assets only). If a required asset is unavailable, resolve a fallback variant or exclude the item — **never** synthesize inline. Planning is the only phase that may touch the provider path (via prefetch), and even then outside time-critical execution.

### 11.2 Execution

The eyes-closed core. MPE runs the protocol's primitive-based steps: `Play`, `Pause`, `Expect`, `Confirm`, `Repeat`, etc., over approved local assets. No provider calls occur here (hard rule).

### 11.3 Observation

Interleaved with Execution. `Observe`/`Expect`/`Confirm` collect behavioral evidence and EEG-context references. Observations are recorded immediately (`Record`).

### 11.4 Adaptation

Interleaved with Execution/Observation. Under §8's model and §9's EEG policy, MPE makes bounded, reasoned `AdaptationDecision`s and applies them to subsequent steps. Every decision is recorded.

### 11.5 Completion

Execution ends (session length reached, objective met, or explicit stop). MPE finalizes the `ExecutionResult`, updates durable learning/history state **only from behavioral/history evidence**, and computes a `ProtocolSummary`.

### 11.6 Replay

Offline. The recorded execution can be **event-replayed** (reconstruct exactly what happened) and **protocol-replayed** (re-run protocol logic against recorded inputs), including with EEG influence disabled. See §15.

### 11.7 Analysis

Offline. Metrics (§16) are computed across executions: mastery trends, retention curves, adaptation efficacy, EEG-context correlations (descriptive only — EEG never becomes authoritative retroactively).

---

## 12. Protocol object model (conceptual)

**Conceptual models only — not implementation classes.** These describe the *shape* of the domain, not its code. Field names are indicative.

```
Protocol:                         # a type/definition
    protocol_id
    name
    category                      # one of the 8
    primary_goal                  # cognitive-goal vocabulary
    objectives: [ProtocolObjective]
    step_template: [ProtocolStep] # primitive composition (may branch)
    required_asset_roles: [AssetRole]
    behavioral_measurements: [EvidenceKind]
    adaptation_opportunities: [BoundedParameter]
    success_criteria
    difficulty_model_ref          # abstract; bound by domain adapter

ProtocolObjective:
    objective_id
    cognitive_goal                # Encode/Retrieve/Discriminate/...
    description

ProtocolStep:
    step_id
    primitive                     # semantic primitive from §6 (Play/Pause/Expect/Confirm/Repeat/Branch/Transition/Wait/Observe/Score/Record/Explain)
                                  # Concrete expression: one or more MPE Instruction / StimulusRequest / ResponseWindow / ScheduleDecision / AdaptationDecision / FeedbackEvent.
    stimulus_ref?                 # (item_id, asset_role, voice_profile_family) — never a provider URL; maps to StimulusRequest
    duration_policy?              # bounds + adaptation inputs (for Pause/Expect/Wait); maps to AdaptationDecision allowed_bounds and chosen value
    expected_response?            # internal | overt; evidence kinds; maps to Instruction.observable_response_expected and ResponseWindow
    branch_spec?                  # condition → next step(s); maps to ScheduleDecision or future protocol-graph extension (see §6.4)

Observation:
    observation_id
    step_id                       # references the ProtocolStep that produced this evidence
    evidence_kind                 # see §10
    value                         # latency, marker, choice, self-confirm, context-ref
    provenance                    # which primitive, which evidence source
    timestamp
    # Note: The authoritative MPE object is Observation (raw provider input) plus
    # CapturedResponse / ResponseInterpretation / DomainNormalizedResponse / Evaluation
    # for layered response processing. See MPE_OBJECT_MODEL_V1_1.md and MPE_EVENT_MODEL_V1_1.md.

AdaptationDecision:
    # This is the conceptual, minimal view. The authoritative MPE schema is
    # MPE_ADAPTATION_CONTRACT.md and MPE_OBJECT_MODEL_V1_1.md §AdaptationDecision.
    adaptation_decision_id
    session_id
    policy_id
    policy_version
    deployment_status               # exploratory_only | shadow_mode | limited_runtime | production_approved
    target_dimension                # typed dimension name (pause_duration, speech_rate, response_deadline, new_item_rate, review_insertion, cue_specificity, response_mode)
    current_value
    proposed_value
    allowed_bounds                  # { min, max, default, status, evidence_grade }
    source                          # behavior | latency | history | eeg-context
    source_event_ids                # list of event ids that fed the decision
    evidence_record_ids             # optional list of EvidenceRecord ids
    aggregation_window              # time or trial count
    minimum_evidence                # was minimum evidence met?
    uncertainty_threshold           # was uncertainty threshold met?
    confidence                      # policy-internal confidence, 0.0–1.0
    cooldown                        # seconds or trials remaining before this policy can act again
    hysteresis                      # minimum change required to act
    maximum_step_size               # max single-step change
    rollback_rule                   # condition under which the change is reversed
    abstention_rule                 # condition under which the policy returns NO_CHANGE
    decision                        # APPLY | NO_CHANGE_INSUFFICIENT_EVIDENCE | REVERSE | ABSTAIN
    reason                          # human-readable justification
    behavioral_evidence_ref?        # pointer to behavioral evidence
    eeg_context_ref?                # pointer only, never raw signal
    applied_at?                     # if APPLY
    reversed_at?                    # if REVERSE
    timestamp

ExecutionPlan:
    # Runtime-derived planning artifact, not a formal MPE core object.
    # Equivalent data lives in Session.start_parameters, ProtocolVersion, and ScheduleDecision.
    plan_id
    protocol_id / protocol_version_id
    domain_adapter_ref            # required provider set
    item_pool                     # selected via history; maps to ScheduleDecision.candidate_item_ids
    initial_difficulty_band       # maps to Trial.difficulty_dimensions
    session_length
    required_assets_resolved      # approved local asset refs (prefetched); maps to StimulusRequest / RenderedStimulus

ExecutionResult:
    # Runtime-derived outcome artifact; authoritative MPE object is Outcome + event stream.
    result_id
    plan_id
    session_id
    started_at, ended_at
    steps_executed: [step outcomes]
    observations: [Observation]
    adaptation_decisions: [AdaptationDecision]
    state_deltas                  # durable changes (behavior/history only)
    completion_reason

ProtocolSummary:
    # Derived analytics view, not a formal MPE core object.
    summary_id
    result_id
    session_id
    protocol_id, category
    duration
    items_touched, items_advanced
    behavioral_outcome_summary    # success/latency aggregates
    adaptation_summary            # counts by source, incl. eeg-influenced
    objective_attainment          # per objective
    notes
```

**Separation of concerns:** `Protocol`/`ProtocolStep`/`ProtocolObjective` = **definition** (neutral); `ExecutionPlan` = **intended run**; `Observation`/`AdaptationDecision` = **what was seen/decided**; `ExecutionResult` = **what happened**; `ProtocolSummary` = **analyzed outcome**. Durable learning-state changes live in `state_deltas` and derive only from behavioral/history evidence.

---

## 13. Interaction with MPE runtime

MPE is the executor; the protocol library is the definitional layer. Responsibilities:

- **MPE owns timing and adaptation.** Protocols declare *policies and bounds*; MPE derives concrete pauses, windows, repetitions, selections, and transitions at runtime under §8/§9.
- **MPE never calls a provider during execution.** It plays approved local assets resolved by the registry.
- **MPE emits the event stream.** Every `Record`-worthy moment becomes a durable event supporting replay (§15).
- **MPE enforces boundaries.** It rejects adaptation outside the bounded-parameter set, EEG decisions lacking the mandatory reasoned fields, and any attempt to change objectives mid-execution.
- **Protocols are provider- and domain-blind.** They reference items/roles/relations abstractly; the domain adapter and asset pipeline resolve concretes.

This preserves the existing MPE runtime contracts (unchanged by this document): the library sits *above* the event store / persistence / CLI surface delivered in prior phases and *below* nothing — it is the semantic definition those layers execute and record.

---

## 14. Interaction with the Audio Asset Pipeline

- Protocols reference audio only as **(`item_id`, `asset_role`, `voice_profile_family`)**. Resolution to an approved, validated, human-reviewed local asset is entirely the pipeline's responsibility.
- **Protocols never know providers**, never see SpeechGen, never hold provider URLs or voice names.
- **Asset roles** (`natural`, `pedagogical_slow`, `prompt`, `confirmation`, `instruction`, `minimal_pair`, `sentence_context`) are the shared vocabulary between this library and the pipeline.
- **Playback-rate discipline** matches the pipeline's principle B: runtime rate stays within validated phonetic bounds; outside them, protocols request a `pedagogical_slow` (or otherwise pre-synthesized) variant rather than time-stretching.
- **Prefetch at Planning; play locally at Execution.** No synchronous synthesis in the adaptive loop, ever.
- **Missing-asset behavior** is a protocol failure mode handled at Planning (fallback variant or item exclusion), never by inline generation.

---

## 15. Replay: protocol replay vs event replay

These are two distinct, complementary capabilities. Conflating them is a common design error; MindTune keeps them separate.

### 15.1 Event replay — "what happened"

**Definition.** Reconstruct the exact sequence of what the learner experienced and what the engine did, by replaying the recorded **event stream** against the **immutable, versioned assets**.

- Deterministic reconstruction of stimuli (exact asset id + version), pauses/windows actually used, confirmations, observations, and adaptation decisions with their reasons.
- **Does not re-run protocol logic.** It faithfully re-presents recorded facts.
- Guarantee: given the event stream + immutable asset store, the exact asset **version** and playback parameters are recoverable and re-playable (consistent with the Audio Asset Pipeline's replay guarantee).
- Uses: audit, debugging, "play back my session", verifying no provider secret leaked.

### 15.2 Protocol replay — "what the logic would decide"

**Definition.** Re-run the **protocol's decision logic** (selection, adaptation, branching) against **recorded inputs** (observations, evidence, optionally EEG context), to reproduce or analyze the engine's decisions.

- Re-executes `Branch`/`Adaptation`/selection given the recorded observation stream.
- **Reference state is produced independently**, not by trusting the recorded outputs — protocol replay recomputes decisions from inputs so it can *verify* the original decisions (or test alternative policies).
- Supports **counterfactuals**: replay with **EEG influence disabled** (drop EEG-sourced decisions) must yield a coherent session — proving EEG was never authoritative (§9). Replay with a modified policy shows what *would* have happened.
- Uses: policy validation, regression testing of adaptation, verifying determinism, ablating EEG.

### 15.3 Why both are required

Event replay proves **fidelity** (we recorded reality). Protocol replay proves **soundness** (our decisions follow from evidence and policy, and EEG is dispensable). Together they make MindTune auditable *and* verifiable. A protocol's *Replay requirements* field (§7) specifies what each protocol must record so both replays are possible.

### 15.4 Determinism requirements

For protocol replay to be meaningful, decision logic must be deterministic given inputs: stable orderings (sessions, findings, steps, options), explicit tie-breaks, and no dependence on wall-clock or unstable iteration order. Any stochastic policy (e.g. repetition *probability*) must record its seed/draw so replay is reproducible.

---

## 16. Metrics and measurable outcomes

Metrics are computed in Analysis (§11.7) and power progress visualization (screen) without ever making the screen part of execution.

### 16.1 Learning-outcome metrics

- **Retention curve** — success probability vs lag (per item/family); flattening = durable learning.
- **Retrieval fluency** — latency distribution for successful retrievals; decreasing = automatization.
- **Mastery coverage** — fraction of an item set/family at each mastery band.
- **Transfer** — performance on a category using items first seen in a prior category (e.g. Transformation success on items only Encoded).
- **Discrimination accuracy** — Recognition-category accuracy on low-salience contrasts; false-alarm/miss rates for Error Detection.
- **Production readiness** — self-confirmed/overt production accuracy and latency (Internal Speech / Transformation).

### 16.2 Process / adaptation metrics

- **Adaptation frequency by source** — counts of behavior/latency/history/EEG decisions.
- **EEG-influence share** — proportion of adaptations that were EEG-influenced (should be modest; a spike warrants review).
- **Recovery incidence & efficacy** — how often Recovery is entered and whether success/latency restored afterward.
- **Pause/window efficacy** — relationship between chosen window length and subsequent success (validates duration policies).
- **Density tolerance** (Listening) — sustained comprehension vs presentation density.

### 16.3 Integrity / safety metrics

- **Evidence provenance completeness** — fraction of outcomes backed by direct behavioral evidence vs proxy.
- **EEG-ablation coherence** — that protocol replay with EEG disabled remains coherent (a hard check, not just a metric).
- **Determinism** — protocol replay reproduces recorded decisions (regression gate).
- **No-provider-in-execution** — zero provider calls during execution (hard check).

### 16.4 Metric hygiene

Metrics are **descriptive**. In particular, EEG-context correlations may be reported in Analysis but must never feed back as authoritative correctness or retroactively alter learning state (§9). Self-confirmation-based outcomes are labeled as such and not conflated with machine-scored correctness.

---

## 17. Future domains

The library is domain-neutral (§4). Applicability is demonstrated by binding a domain adapter; protocol definitions are unchanged.

### 17.1 Hebrew Lab (first domain)

- **Items:** words, roots, patterns, inflected/derived forms, sentences.
- **Relations:** `derive` (root→word), `inflect` (tense/gender/number/person/voice), `contrast` (minimal pairs), `family` (root families), `contains` (sentence↔words).
- **Asset roles:** `natural`, `pedagogical_slow` (for niqqud-critical/isolated items), `prompt`, `confirmation`, `minimal_pair`, `sentence_context`.
- **Illustrative mappings:** Root Encoding/Recognition ← triconsonantal roots; Pattern Encoding ← *mishkalim*; Transformation ← binyan/tense/gender/number paradigms; Minimal Pairs ← guttural/vowel contrasts. **(Examples only — not part of any protocol definition.)**

### 17.2 Piano Lab

- **Items:** notes, intervals, chords, scales, phrases, fingerings.
- **Relations:** `associate` (note↔fingering; chord↔name), `derive` (scale→chord; key→scale), `inflect` (dynamics/articulation as dimensions), `contrast` (confusable intervals/chords), `sequence` (phrase progressions), `contains` (phrase↔notes).
- **Asset roles:** `natural`, `pedagogical_slow`, `prompt` (name/context), `confirmation` (played target), `minimal_pair` (confusable intervals), `sentence_context` (phrases).
- **Illustrative mappings:** Encoding ← interval/chord recognition by ear; Transformation ← transpose/derive chord from scale; Recognition ← distinguish major/minor thirds; Internal Speech ← audiate a phrase before hearing it (Mental anticipation); Listening ← comparative listening across articulations. Eyes-closed audiation is a natural fit for MindTune.

### 17.3 General cognitive training

- **Items:** arbitrary paired/sequenced/patterned stimuli (facts, associations, sequences).
- **Relations:** `associate`, `sequence`, `family`, `contrast`.
- **Use:** memory training, attention/vigilance (Error Detection, Focused listening), retrieval practice (Recall), spacing (Consolidation). Domain adapter supplies items and (optional) scoring; the same protocols apply.

### 17.4 Other languages

- Any inflecting/derivational language binds directly (Transformation dimensions, root/pattern families where applicable). Non-Semitic languages simply omit `family(root,…)`/pattern relations they lack; the remaining protocols (Vocabulary/Sentence Encoding, Recall, Recognition, Listening, Consolidation, Recovery) apply unchanged. Niqqud-style disambiguation generalizes to any orthography-vs-pronunciation gap via `pedagogical_slow`/`expected_reading` at the asset layer.

**Portability test (acceptance):** a protocol is well-formed iff it can be fully specified using only the neutral relation vocabulary (§4.3), asset roles, cognitive-goal vocabulary, and primitives — with zero domain terms. Every §7 protocol passes this test.

---

## 18. Cross-cutting invariants and acceptance criteria

1. **Eyes-closed execution.** Every protocol's *execution* phase is fully expressible via audio + silence; `Explain` and any visual content are confined to Planning/Review.
2. **Domain neutrality.** No protocol definition contains domain terms; all pass the §17 portability test.
3. **Provider invisibility.** No protocol/step references a provider, URL, or voice name; audio is (item, role, voice-profile-family) only.
4. **No synchronous synthesis in execution.** Providers are touched only at Planning (prefetch); execution uses approved local assets.
5. **Evidence primacy.** Behavioral evidence is authoritative for correctness; proxies drive only pacing/support; absence of evidence is recorded as absence.
6. **EEG policy (permanent).** EEG is contextual, bounded, reversible, corroborated, and always emits a reasoned decision; disabling EEG in protocol replay leaves a coherent session.
7. **Bounded adaptation.** Adaptation changes only the §8.3 parameter set, within declared bounds; objectives are never altered mid-execution.
8. **Dual replay.** Both event replay (fidelity) and protocol replay (soundness, incl. EEG ablation) are supported; decision logic is deterministic given inputs.
9. **Recorded reasoning.** Every `AdaptationDecision`/`Branch`/`Transition` cites its source, policy, bounds, and previous/new values.
10. **Closed primitive/goal/relation vocabularies.** Extending any of these three vocabularies is an architecture-level change requiring revision of this document.

---

## 19. Unresolved questions

1. **Self-confirmation capture mechanism.** How does an eyes-closed learner emit a "got it / missed it" signal (single-button, breath, minimal voice marker, EEG-assisted-but-not-authoritative)? Affects evidence quality for all Internal-Speech/Recall protocols.
2. **Overt-response capture scope.** How much overt production do we capture (timing/energy only vs future ASR)? ASR is explicitly out of scope for v1.0, but the evidence model must leave room.
3. **Difficulty model ownership.** Is the difficulty band model neutral (in the library) or domain-owned (in the adapter)? Proposed: neutral bands, domain-supplied item→band mapping — confirm.
4. **Spacing/history engine boundary.** Does Consolidation scheduling live in the library, in MPE runtime, or a separate scheduler service? Affects Consolidation protocol specs.
5. **EEG context representation.** Exact shape of the "EEG context window" reference and the closed set of EEG policy rules (§9.4) — to be co-designed with the EEG subsystem, staying non-authoritative.
6. **Stochastic policy determinism.** Standard for recording seeds/draws for probabilistic adaptation so protocol replay is reproducible.
7. **Self-confirmation vs machine score reconciliation.** How metrics treat items where self-confirmation and (later) machine score disagree.
8. **Protocol composition.** Whether sessions are single-protocol or MPE composes multiple protocols per session (this doc assumes free composition; confirm the session model).
9. **Minimal-pair / error asset generation authority.** Whether plausible-error and minimal-pair assets are authored, adapter-generated, or pipeline-generated — and how their linguistic validity is reviewed.
10. **Protocol graph expressiveness.** Whether `ProtocolVersion`/`Block` fixtures need a richer per-step branching graph to support `ProtocolStep.branch_spec` directly, or whether `Branch`/`Transition`/`Repeat` are fully expressible through `ScheduleDecision` + `Block.exit_condition`.

---

## 20. Implementation recommendations

1. **Implement the neutral core first.** Ship the primitive semantics, ontology, object model, and the adaptation/EEG enforcement *before* any domain content. Domain adapters (Hebrew first) come after.
2. **Enforce boundaries in the runtime, not by convention.** MPE should *reject* out-of-bounds adaptation, EEG decisions missing reasoned fields, provider references in steps, and objective mutation — with tests asserting each rejection.
3. **Make EEG optional and ablatable from day one.** Build protocol replay with an "EEG off" mode as a first-class, tested capability (an acceptance gate, §16.3).
4. **Start with a small protocol subset.** Recommended MVP: Vocabulary Encoding, Immediate Recall, one Transformation (e.g. Number), Minimal Pairs, Silent production/Mental anticipation, Adaptive review, Reduced-load Recovery — enough to exercise all eight categories' machinery end-to-end.
5. **Co-design the self-confirmation channel early** (§19.1); it gates evidence quality for most protocols.
6. **Keep the three vocabularies closed and versioned.** Primitives, cognitive goals, and neutral relations are the stable ABI of the library; changes require doc revision and a version bump.
7. **Instrument metrics from the start** (§16), including the integrity/safety checks as CI-style gates (no-provider-in-execution, EEG-ablation coherence, determinism).
8. **Align asset roles with the pipeline** (single shared vocabulary) to avoid drift between this library and `mpe_audio`.
9. **Sequence relative to Audio Asset Pipeline.** This library's Planning phase depends on the pipeline's approved-asset registry; land the registry/asset-role contract (pipeline Phase A/D) before protocol Execution integration.
10. **Do not begin domain-specific or Phase 4B.4 work under this document.** This is definitional; implementation is a separate, later authorization.

---

## 21. Final recommendation

The architecture defines a domain-neutral protocol ontology, a complete eight-category taxonomy with fully specified protocols, a closed primitive catalog defined by semantics, a disciplined four-source adaptation model, a permanent and enforceable EEG policy, a clean lifecycle and object model, a rigorous distinction between event and protocol replay, and measurable outcomes — all consistent with the Audio Asset Pipeline design and without touching existing MPE runtime contracts. Reconciliation with the MPE v1.1 typed model is documented in §6.4 and Appendix E; the few unresolved questions in §19 are design refinements that require ADRs before implementation but do not block the architecture.

**Recommendation:**

```
APPROVE_PROTOCOL_LIBRARY_ARCHITECTURE_WITH_CONDITIONS
```

**Conditions:**

1. Primitive names in this document are semantic pseudocode; concrete runtime expression is the MPE v1.1 typed model (`Instruction`, `StimulusRequest`, `ResponseWindow`, `ScheduleDecision`, `AdaptationDecision`, `FeedbackEvent`) per `MPE_DSL_DECISION_RECORD.md`.
2. `AdaptationDecision` implementation must use the full schema from `MPE_ADAPTATION_CONTRACT.md` and `MPE_OBJECT_MODEL_V1_1.md`.
3. `ExecutionPlan`, `ExecutionResult`, and `ProtocolSummary` are runtime-derived artifacts / `Outcome` + derived analytics, not new core objects, until elevated by ADR.
4. The self-confirmation capture mechanism (§19.1) and the protocol graph / `branch_spec` question (§19.10 / §6.4) must be resolved through ADRs before full end-to-end implementation.

---

## Appendix A — Primitive quick reference

| Primitive | Cognitive meaning | Observes | Adapts |
|---|---|---|---|
| Play stimulus | present item (audio, by role+item) | onset/offset | rate (bounded), variant |
| Pause | silence for anticipation/recall/processing | chosen duration | duration (primary) |
| Expect internal response | open internal/overt production window | latency, optional overt marker | window length, repeat |
| Confirm | present correct target; close loop | self-confirm signal | whether/when; repeat after |
| Repeat | re-present step/group | repeat index | count (bounded) |
| Branch | choose path from evidence/context | branch + reason | selection/progression |
| Transition | move to another state/block | reason | progression, recovery/consolidation |
| Wait | fixed/bounded idle | elapsed | rarely |
| Observe | sample behavioral/EEG-context evidence | the evidence | feeds all |
| Score | interpret evidence → domain outcome (adapter) | score/verdict | history-based |
| Record | emit durable event | the event | none |
| Explain | explanatory content (config/review only) | n/a | none |

## Appendix B — Protocol summary matrix

| Category | Protocols | Primary goal | Signature loop |
|---|---|---|---|
| Encoding | Vocabulary, Morphology, Root, Pattern, Sentence | Encode | play → pause → confirm |
| Recall | Immediate, Delayed, Free, Recognition | Retrieve | cue → expect → confirm |
| Transformation | Inflection, Conjugation, Number, Gender, Person, Tense, Voice, Derivation | Transform/Produce | base+dim → produce → confirm |
| Recognition | Minimal Pairs, Root, Pattern, Error Detection | Discriminate | contrast → judge → confirm |
| Internal Speech | Silent production, Silent repetition, Mental completion, Mental anticipation | Produce | cue → internal produce → confirm |
| Listening | Immersion, Focused, Comparative | Comprehend | (segmented) play → (light) confirm |
| Consolidation | Adaptive review, Spaced reinforcement, Mixed review | Consolidate | history-selected retrieval |
| Recovery | Reduced-load, Confidence rebuilding, Reinforcement cycles | Restore | easy → confirm → restabilize |

## Appendix C — Worked Hebrew examples (illustrative only)

> **These are examples to make the neutral protocols concrete. No Hebrew concept below is part of any protocol definition.**

**C.1 Vocabulary Recall (Immediate Recall).**
`play(prompt=IT "casa")` → `pause(anticipation)` → *internal Hebrew recall of בַּיִת* → `expect(latency)` → `play(confirmation=HE natural "bayit")` → `branch(if missed: repeat; else: next)`.

**C.2 Morphology Flow (Transformation: Number).**
`play(prompt=HE "sefer" + dim=plural, instruction)` → `pause(production)` → *internal production of "sfarim"* → `expect` → `play(confirmation=HE "sfarim")` → `branch(on error type → reinforcement)`.

**C.3 Root Recognition.**
`play(prompt=HE derivative "miktav")` → `pause` → *identify root כ־ת־ב* → `expect(choice/self-confirm)` → `play(confirmation=root/family)` → `branch(performance → next derivative or harder distractors)`.

**C.4 Listening Only (Immersion).**
segmented `play(sentence_context passage)` with adaptive `pause` density; EEG-context may increase pause density under high load (bounded, recorded); no per-item grading.

**C.5 Shadowing (Internal/overt Silent repetition).**
`play(HE natural)` → immediate overt repetition (timing captured, not recognized) → `observe(latency/energy)` → optional `confirm`.

Each example labels: **cached assets** (`play`/`confirm` targets), **runtime timing** (`pause`/window), **behavioral observation** (`expect`/`observe`), **EEG context** (density/pause nudge only), **transitions** (`branch`/`transition`).

## Appendix D — Glossary

- **Protocol** — a named cognitive exercise definition (a type).
- **Primitive** — smallest reusable protocol building block (semantic, not syntactic).
- **Cognitive goal** — one of the closed set (Encode/Retrieve/Discriminate/Transform/Produce/Comprehend/Consolidate/Restore).
- **Domain adapter** — the seam binding neutral protocols to a concrete domain.
- **Asset role** — logical audio role (natural, pedagogical_slow, prompt, confirmation, instruction, minimal_pair, sentence_context).
- **Behavioral evidence** — observations bearing on correctness; authoritative.
- **EEG context** — non-authoritative engagement/load context; bounded modulator only.
- **Event replay** — reconstruct what happened from the event stream + immutable assets.
- **Protocol replay** — re-run decision logic against recorded inputs (independently), incl. EEG-ablated.
- **Self-confirmation** — the learner's own got/missed assessment, recorded as evidence, distinct from machine score.

---

## Appendix E — Phase A reconciliation with MPE v1.1 contracts

This appendix records the changes made to align `MPE_PROTOCOL_LIBRARY_v1.0.md` with the existing MPE v1.1 repository after Phase A review.

### E.1 DSL / typed-model reconciliation

- The primitive names in this document (`play`, `pause`, `expect`, `confirm`, `repeat`, `branch`, `transition`, `wait`, `observe`, `score`, `record`, `explain`) are **semantic pseudocode**, not an approved textual DSL. `MPE_DSL_DECISION_RECORD.md` requires a schema-first typed model for Phase 4; any textual DSL is deferred.
- The concrete runtime expression of every primitive is one or more MPE typed-model entities: `Instruction`, `StimulusRequest`, `ResponseWindow`, `ScheduleDecision`, `AdaptationDecision`, `FeedbackEvent`. See §6.4.

### E.2 Object-model reconciliation

- `ProtocolStep` is a conceptual primitive composition. It maps to `Instruction` + `StimulusRequest` + `ResponseWindow` + `FeedbackEvent` + `ScheduleDecision`/`AdaptationDecision`.
- `ProtocolStep.branch_spec` is a condition → next step(s) graph. The current MPE `ProtocolVersion` uses `block_sequence` or `trial_sequence` with `Block.exit_condition`; richer per-step branching is unresolved (§19.10) and requires an ADR if elevated to the fixture schema.
- `Observation` in this document is a conceptual evidence record. The authoritative MPE path is `Observation` → `CapturedResponse` → `ResponseInterpretation` → `DomainNormalizedResponse` → `Evaluation`.
- `AdaptationDecision` in this document is a minimal conceptual view. Implementation must use the full `MPE_ADAPTATION_CONTRACT.md` / `MPE_OBJECT_MODEL_V1_1.md` schema, including `deployment_status`, `allowed_bounds`, `source_event_ids`, `evidence_record_ids`, `aggregation_window`, `minimum_evidence`, `uncertainty_threshold`, `confidence`, `cooldown`, `hysteresis`, `maximum_step_size`, `rollback_rule`, `abstention_rule`, and `decision`.
- `ExecutionPlan`, `ExecutionResult`, and `ProtocolSummary` are **runtime-derived artifacts** or analytics views, not new core objects. Equivalent data lives in `Session.start_parameters`, `Outcome`, and derived metrics.

### E.3 Adaptation mapping

| Library source | MPE contract |
|---|---|
| Behavior-based | `AdaptationDecision`/`ScheduleDecision` driven by `evaluation_completed`, learner observations |
| Latency-based | `AdaptationDecision.target_dimension` = `pause_duration`, `response_deadline`, `speech_rate` |
| History-based | `ScheduleDecision` with `item_history_snapshot_id` |
| EEG-context | `SensorObservation`/`state_estimate_produced` → `AdaptationDecision` with `eeg_context_ref` and `deployment_status` |

### E.4 Audio boundary mapping

- Audio is addressed only as (`item_id`, `asset_role`, `voice_profile_family`).
- These map to `StimulusRequest.content_item_id` + renderer hints (`voice_id`, `prosody_hints`, `rate`).
- Asset roles are a shared vocabulary with `mpe_audio`: `natural`, `pedagogical_slow`, `prompt`, `confirmation`, `instruction`, `minimal_pair`, `sentence_context`.
- The `instruction` asset role supplies media for `Instruction.instruction_payload`; it is distinct from `InstructionType`.

### E.5 Lifecycle mapping

| Library phase | MPE runtime contract |
|---|---|
| Planning | `session_created` / `session_started` + `ScheduleDecision` + asset prefetch via `StimulusRequest`/`RenderedStimulus` |
| Execution | `Instruction`/`StimulusRequest`/`ResponseWindow`/`FeedbackEvent` events over approved local assets |
| Observation | `observation_received` + `response_*` + `captured_response_created` events |
| Adaptation | `adaptation_*` + `schedule_decision` events |
| Completion | `session_completed` + `Outcome` |
| Replay | `Replay` over `EventStore` (event replay); future `ProtocolReplay` harness (protocol replay) |
| Analysis | Derived metrics from `Outcome` and event stream |

### E.6 Key unresolved ADRs

- §19.1: Self-confirmation capture mechanism (blocker for Internal Speech/Recall execution).
- §19.10: Protocol graph expressiveness (`branch_spec` vs `ScheduleDecision` + `Block.exit_condition`).

All other unresolved items in §19 are non-blockers for Phase A architecture acceptance.
