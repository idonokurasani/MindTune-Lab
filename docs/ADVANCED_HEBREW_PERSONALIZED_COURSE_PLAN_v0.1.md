# Advanced Hebrew Personalized Course Plan v0.1

Status: planning document, not implementation.

Purpose: define Andrea's personalized advanced Modern Hebrew course inside MindTune Lab.

Core principle:

> Every study session starts by estimating today's cognitive and physiological state, then selects the right Hebrew work for that state, records behavioral results, links them to EEG/context when available, and updates long-term performance memory.

## 1. Product Goal

This is not a generic Hebrew course.

It is a personalized re-entry and advancement system for Andrea, built from:

- prior study history, especially Citizen Cafe;
- stronger Hebrew authorities, especially the Academy of the Hebrew Language;
- real usage sources, especially Streetwise Hebrew;
- morphology support, especially Pealim-style verb/root data;
- future psycholinguistic profiling through HeLP;
- daily physiological context from Oura and other sensors;
- MindTune behavioral events and EEG context.

The course optimizes:

- reactivation of dormant Hebrew skills;
- advanced active production;
- long-term retention;
- fast recall under time pressure;
- contextual comprehension;
- verb/root fluency;
- efficiency: performance achieved per unit of fatigue/time.

## 2. Source Hierarchy

| Source | Role |
|---|---|
| Citizen Cafe | Andrea's personal re-entry corpus: what he likely studied before |
| Academy of the Hebrew Language | Normative authority for spelling, morphology, terminology, grammar |
| Streetwise Hebrew | Living usage, register, idiom, audio/context enrichment |
| Pealim-style cache | Practical verb/root/conjugation lookup, pending stronger validation |
| Ulpan/university curricula | Pedagogical benchmark for progression |
| HeLP | Future lexical/morphological difficulty and profiling layer |
| MindTune performance history | Personal truth: what Andrea actually recalls and produces |

No single source is the course authority.

The true course emerges from the intersection of:

1. prior exposure;
2. linguistic correctness;
3. real usage;
4. measured performance;
5. daily state.

## 3. Daily Session Structure

### Phase 0 - Preflight

Before study begins, MindTune reads or asks for:

- sleep duration;
- REM sleep;
- deep sleep;
- readiness;
- resting heart rate;
- HRV if available;
- stress / resilience indicators;
- previous day's activity load;
- today's caffeine in espresso cups and estimated mg;
- subjective energy;
- subjective stress;
- time available;
- whether EEG is available.

Output:

- `daily_state_summary`;
- `confidence_score`;
- suggested session dose.

### Phase 1 - Cognitive Activation / Calibration

Duration: 3-7 minutes.

This is not "brain training" as a claim. It is a short calibration battery to estimate today's response speed, inhibition, attention and motor readiness.

Recommended tasks:

| Task | Function |
|---|---|
| Simple reaction / target tap | baseline response speed |
| Simon direction | interference and stimulus-response mapping |
| Stroop color | inhibition / conflict monitoring |
| Go / No-Go | impulse control and response withholding |
| Short working-memory pulse | immediate retention and mental load |

Output:

- mean reaction time;
- reaction-time variability;
- accuracy;
- interference cost;
- lapse count;
- early fatigue signal.

These metrics are used to adjust the Hebrew plan for the day.

### Phase 2 - State Classification

MindTune classifies the day into one of four practical modes:

| Mode | Condition | Study Strategy |
|---|---|---|
| Green | good sleep, good readiness, stable activation | new material + production |
| Yellow | acceptable but not optimal | consolidation + controlled new items |
| Orange | fatigue, stress, slow activation | re-entry and easy retrieval |
| Red | very poor state or high fatigue | minimal dose, passive/contextual work only |

This classification must remain advisory. The user can override it.

### Phase 3 - Adaptive Hebrew Plan

The session is built from modules. MindTune chooses the dose and mix.

## 4. Hebrew Modules

### Module A - Re-entry Lexicon

Source: Citizen Cafe consolidated corpus.

Goal:

- recover dormant vocabulary;
- distinguish forgotten items from bad source material;
- update personal memory state.

Task types:

- Hebrew -> Italian recognition;
- Italian -> Hebrew recall;
- audio/context-assisted recall when available;
- delayed retest after session;
- re-entry test for old color decks.

Measured:

- accuracy;
- time to answer;
- hesitation;
- answer edits;
- confidence if provided;
- retention across 1 day, 7 days, 30 days.

### Module B - Hebrew Domino Production

Source: Pealim/Academy-validated verb set, later HeLP enriched.

Goal:

- active conjugation fluency;
- transfer between person, gender, number and tense;
- continuous production without isolated memorization.

Example flow:

1. "How do you say: he eats?"
2. If `hu ohel hayom`, then: "hi mahar...?"
3. If `hi tochal mahar`, then: "hem etmol...?"
4. Continue as a chain.

Rules:

- one answer becomes the seed for the next prompt;
- pronoun, tense and time adverb change each step;
- difficulty rises when responses are fast and correct;
- difficulty falls when errors cluster.

Measured:

- correctness;
- latency;
- edit distance from target;
- repeated error type;
- tense/person/gender weakness;
- chain length before failure;
- recovery after feedback.

### Module C - Streetwise Context

Source: Streetwise enrichment metadata, links, short excerpts and audio references.

Goal:

- connect known words to living Hebrew;
- identify register and idiom;
- train comprehension of phrases rather than isolated cards.

Task types:

- identify known word in context;
- choose meaning from context;
- register judgment;
- listen-and-recall;
- phrase completion.

Streetwise does not overwrite the canonical corpus. It enriches it.

### Module D - Academy Normalization

Source: Academy of the Hebrew Language.

Goal:

- clean spelling, roots, morphology and formal correctness.

Task types:

- choose correct spelling;
- root/binyan recognition;
- infinitive/present/past/future mapping;
- identify colloquial vs normative form;
- resolve disputed Citizen Cafe fragments.

This module is especially useful when a card is marked `reconstructed_pending_review`.

### Module E - Reading and Listening

Goal:

- move from card recall to real comprehension.

Task types:

- short text reading;
- timed gist extraction;
- sentence reconstruction;
- audio clip comprehension;
- shadowing / repeat-after-audio;
- phrase-level dictation.

Measured:

- comprehension accuracy;
- reading time;
- listening replay count;
- unknown-word density;
- summary quality.

### Module F - Active Output

Goal:

- produce Hebrew, not merely recognize it.

Task types:

- sentence production;
- micro-dialogue;
- paraphrase;
- one-minute speaking prompt;
- written response;
- translation from Italian to Hebrew.

Measured:

- lexical retrieval;
- grammar errors;
- morphology errors;
- fluency;
- self-correction;
- response time.

## 5. Daily Dose Rules

The system should control cognitive dose like physical training.

Basic formula:

```text
cognitive_dose =
  minutes
  x task_difficulty
  x response_pressure
  x novelty
  x fatigue_modifier
```

Dose targets:

| Mode | Duration | New Items | Main Work |
|---|---:|---:|---|
| Green | 45-75 min | high | production + new material + retest |
| Yellow | 30-50 min | moderate | consolidation + limited production |
| Orange | 15-35 min | low | re-entry + easy recall |
| Red | 5-20 min | none | passive context, light review |

## 6. Session Templates

### Green Day

1. Oura/state check.
2. 5 min activation battery.
3. 10 min re-entry lexicon.
4. 20 min Hebrew Domino Production.
5. 15 min Streetwise context/listening.
6. 10 min active output.
7. Short delayed retest.
8. Session summary.

### Yellow Day

1. Oura/state check.
2. 4 min activation battery.
3. 15 min re-entry lexicon.
4. 10 min conjugation domino.
5. 10 min reading/listening.
6. Stop before fatigue rises.

### Orange Day

1. Oura/state check.
2. 2-3 min simple activation.
3. 10-20 min old material recall.
4. No aggressive new production.
5. Mark fatigue and recovery.

### Red Day

1. No heavy testing.
2. Optional passive listening.
3. 5 min easy recognition.
4. No negative judgment from poor performance.

## 7. Adaptive Selection Logic

For each candidate item, MindTune computes:

- personal mastery;
- recency;
- forgetting risk;
- re-entry value;
- error history;
- difficulty;
- today's state compatibility;
- source reliability;
- review status.

Priority should favor:

1. due retests;
2. high-value dormant items;
3. items with repeated errors;
4. items linked to current module;
5. new items only if daily state permits.

Blocked items:

- quarantined source fragments;
- unreviewed reconstructed forms;
- cards with broken Hebrew or broken Italian;
- items requiring morphology not yet validated.

## 8. Memory Model

MindTune must remember performance over time.

For every trial, store:

- session_id;
- timestamp;
- module;
- task type;
- item IDs;
- source/corpus version;
- prompt;
- response raw;
- response normalized;
- score;
- latency;
- feedback;
- error type;
- Oura/day context;
- EEG session reference if available;
- confidence score for data quality.

Derived memory per item:

- first_seen;
- last_seen;
- attempts;
- correct_count;
- error_count;
- mean_latency;
- latency_trend;
- retention_interval;
- re-entry_status;
- strongest_skill;
- weakest_skill;
- next_due_at;
- personal_difficulty;
- source_quality_status.

## 9. Performance Metrics

Primary outcomes:

- accuracy;
- response time;
- retention;
- production fluency;
- transfer across forms;
- re-entry speed.

Secondary state/context:

- sleep;
- readiness;
- HRV/resting HR;
- activity load;
- stress;
- caffeine;
- activation-task metrics.

Biomarkers:

- EEG quality;
- EEG bands and ratios only as context;
- motion/artifact;
- headset contact.

Principle:

> Behavioral performance beats biomarkers. EEG and Oura explain performance; they do not replace it.

## 10. Longitudinal Dashboard

Weekly:

- study dose;
- accuracy trend;
- latency trend;
- retention trend;
- new vs re-entry balance;
- fatigue resistance;
- best/worst state predictors.

Monthly:

- re-entry index;
- dormant-skill recovery;
- verb production fluency;
- vocabulary active/passive split;
- source-quality repairs completed;
- efficiency score.

Key questions:

- Which sleep profile predicts best Hebrew performance?
- Does powerlifting or running affect recall differently?
- Which modules improve fastest?
- Which old Citizen Cafe material is genuinely recovered?
- Which errors are linguistic, memory-based or source-caused?

## 11. Integration With Sport

MindTune should not ignore physical training.

Training context:

- running;
- resistance work;
- powerlifting;
- rest day;
- soreness/fatigue.

Rules:

- after heavy powerlifting: avoid maximal production tests if fatigue is high;
- after easy aerobic work: allow consolidation and listening;
- after poor sleep plus hard training: reduce dose;
- after good sleep plus low stress: schedule production and new material;
- track whether cognitive performance rebounds after deload days.

## 12. Implementation Order

### Step 1 - Session Orchestrator

Create a daily session flow:

```text
state check -> activation -> adaptive Hebrew plan -> results -> memory update
```

### Step 2 - Stable Item Memory

Persist item-level performance for flashcards, domino verbs and context tasks.

### Step 3 - Citizen Cafe Re-entry

Use only consolidated, non-quarantined Citizen Cafe items.

### Step 4 - Hebrew Domino

Build the verb chain module with verified Pealim/Academy forms.

### Step 5 - Streetwise Enrichment

Attach reviewed Streetwise contexts to known items.

### Step 6 - Oura Adaptive Dose

Make sleep/readiness/activity influence dose and task selection.

### Step 7 - EEG Binding

Ensure every study task can run with or without EEG, but when EEG is active:

- task events are embedded in the EEG session;
- session labels are accurate;
- no fake zero-sample task-only session is treated as EEG.

### Step 8 - HeLP Profiler

HeLP is active as a read-only profiler. It exposes exact stimulus norms immediately, reconstructs personal performance from recorded events, and unlocks adaptive priorities only after the evidence gate is met.

## 13. Hard Rules

1. Never let a broken source card become a production exercise.
2. Never let EEG score override behavioral performance.
3. Never punish a red-state day as "bad learning".
4. Never mix source truth with personal memory state.
5. Never let Hebrew-specific logic enter MLF Core.
6. Always preserve raw response and normalized response.
7. Always keep source/corpus version in lineage.
8. Always record whether a session had EEG or not.
9. Always separate task-only sessions from EEG-linked sessions.
10. Always update memory from events, not from UI assumptions.

## 14. First Practical Pilot

Pilot name: `Hebrew Advanced Re-entry A`

Duration: 14 days.

Daily target:

- 3-5 min activation;
- 20-45 min Hebrew work depending on state;
- 1 short delayed retest;
- automatic summary.

Modules:

- Citizen Cafe re-entry lexicon;
- Hebrew Domino Production;
- one short Streetwise context when available;
- no new unverified corpus.

Success criteria:

- at least 10 sessions completed;
- no quarantined items shown;
- all responses stored with latency;
- daily state attached;
- item memory updated;
- weekly trend report generated;
- visible distinction between learned, dormant, recovered and problematic-source items.

## 15. Final Direction

This course should become a personal Hebrew performance laboratory.

The important outcome is not "finire un corso".

The important outcome is knowing:

- what Andrea knows;
- what Andrea once knew;
- what has gone dormant;
- what returns quickly;
- what requires rebuilding;
- under which physical and mental conditions Hebrew performance is strongest.
