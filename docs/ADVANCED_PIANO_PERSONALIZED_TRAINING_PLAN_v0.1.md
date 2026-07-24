# Advanced Piano Personalized Training Plan v0.1

Status: planning document, not implementation.

Purpose: define Andrea's personalized piano performance and re-entry system inside MindTune Lab.

Core principle:

> Every piano session starts by estimating today's cognitive and physiological state, then selects the right musical work for that state, records behavioral and musical outcomes, links them to EEG/context when available, and updates long-term performance memory.

## 1. Product Goal

This is not a generic practice diary.

It is a personal piano performance laboratory for:

- recovering dormant repertoire and skills;
- improving sight-reading;
- strengthening memory;
- improving auditory prediction and inner hearing;
- refining motor precision;
- measuring fatigue and recovery;
- optimizing practice dose;
- relating musical performance to sleep, stress, sport and EEG context.

The piano system shares the same architecture as Hebrew:

```text
daily state -> activation -> adaptive task plan -> performance -> memory update
```

## 2. Core Outcomes

Primary outcomes:

- accuracy;
- tempo stability;
- rhythmic precision;
- continuity after errors;
- sight-reading quality;
- memory reliability;
- recovery speed for old repertoire;
- expressive control;
- efficiency: musical result per unit of fatigue/time.

Secondary context:

- sleep;
- readiness;
- HRV / resting heart rate;
- sport load;
- soreness;
- subjective energy;
- stress;
- caffeine;
- activation-task performance.

Biomarkers:

- EEG only as context;
- motion/artifact quality;
- headset contact;
- not as a replacement for musical performance.

## 3. Daily Session Structure

### Phase 0 - State Check

MindTune reads or asks for:

- Oura sleep duration;
- REM/deep sleep;
- readiness;
- resting HR / HRV;
- previous training load;
- hand/forearm soreness;
- subjective energy;
- subjective focus;
- available time;
- practice goal;
- EEG available or not.

Output:

- `daily_state_summary`;
- `practice_mode`;
- suggested practice dose.

### Phase 1 - Cognitive / Motor Activation

Duration: 3-8 minutes.

Tasks:

| Task | Function |
|---|---|
| Simple reaction | response speed |
| Simon direction | interference and motor mapping |
| Stroop color | inhibition and cognitive control |
| Finger tapping / alternation | motor readiness |
| Short auditory discrimination | listening readiness |
| Visual tracking / tachistoscope | reading speed and visual attention |

Output:

- reaction time;
- variability;
- error count;
- motor asymmetry;
- attention/fatigue warning.

### Phase 2 - Practice Mode

| Mode | Condition | Piano Strategy |
|---|---|---|
| Green | good sleep, good readiness, low fatigue | new repertoire, hard sight-reading, tempo work |
| Yellow | acceptable state | consolidation, moderate reading, memory checks |
| Orange | fatigue or stress | slow practice, old repertoire, low-risk technical work |
| Red | poor state | listening, mental imagery, very light hands |

## 4. Piano Modules

### Module A - Sight-Reading Lab

Goal:

- improve first-sight processing;
- measure reading accuracy and continuity.

Task types:

- unknown score, never heard;
- short excerpt at fixed tempo;
- melody-only reading;
- two-hand reduced texture;
- full texture;
- delayed second attempt.

Measured:

- wrong notes;
- rhythm errors;
- stops;
- recovery after error;
- tempo drift;
- perceived difficulty;
- first-to-second attempt improvement.

### Module B - Memory Lab

Goal:

- test and strengthen memorized repertoire.

Task types:

- start from beginning;
- random entry point;
- left hand only;
- right hand only;
- silent mental run-through;
- play after listening cue;
- play after score cue.

Measured:

- memory breaks;
- location of failure;
- recovery strategy;
- time to restart;
- motor vs harmonic vs auditory memory weakness.

### Module C - Repertoire Re-entry

Goal:

- recover pieces once known but now dormant.

Stages:

1. listen mentally without score;
2. inspect score silently;
3. play slowly;
4. isolate failure zones;
5. retest after 24h / 7d / 30d.

Measured:

- re-entry speed;
- number of exposed weak spots;
- improvement per minute;
- retention after delay.

### Module D - Motor Precision

Goal:

- improve control without mindless repetition.

Task types:

- finger independence;
- repeated-note control;
- leaps;
- polyrhythm;
- scales/arpeggios only when linked to musical need;
- slow-to-fast tempo ladder.

Measured:

- timing stability;
- evenness;
- error cluster;
- fatigue onset;
- tempo ceiling.

### Module E - Auditory Prediction

Goal:

- strengthen inner hearing and anticipatory listening.

Task types:

- predict next chord;
- sing bass/melody before playing;
- identify harmonic direction;
- listen to phrase then reproduce;
- play from memory after short audio cue.

Measured:

- prediction accuracy;
- response time;
- reproduction accuracy;
- auditory vs motor dependence.

### Module F - Mental Imagery / Silent Practice

Goal:

- practice when physical fatigue is high;
- separate score cognition from motor execution.

Task types:

- read score without playing;
- imagine fingering;
- imagine sound;
- tap rhythm only;
- mark structure;
- delayed physical test.

Measured:

- later performance gain;
- mental effort;
- confidence;
- transfer to actual playing.

### Module G - Interpretation / Expression

Goal:

- not reduce piano to accuracy.

Task types:

- phrase shaping;
- dynamic plan;
- voicing;
- articulation contrast;
- rubato control;
- compare two interpretations.

Measured:

- subjective musical quality;
- consistency across takes;
- expressive intention vs execution;
- tension/fatigue cost.

## 5. Practice Dose

Basic formula:

```text
piano_dose =
  minutes
  x technical_difficulty
  x cognitive_load
  x tempo_pressure
  x novelty
  x physical_fatigue_modifier
```

Dose modes:

| Mode | Duration | Intensity | Main Work |
|---|---:|---:|---|
| Green | 60-120 min | high | new music, hard reading, tempo, memory |
| Yellow | 40-75 min | medium | consolidation, moderate reading |
| Orange | 20-50 min | low | slow re-entry, repair, mental practice |
| Red | 5-25 min | very low | listening, score study, imagery |

## 6. Session Templates

### Green Day

1. State check.
2. Activation battery.
3. Sight-reading excerpt.
4. Main repertoire work.
5. Motor precision block.
6. Memory/random entry test.
7. Short expressive run.
8. Summary and next retest scheduling.

### Yellow Day

1. State check.
2. Short activation.
3. Repertoire consolidation.
4. Medium sight-reading.
5. One memory check.
6. Stop before fatigue contaminates technique.

### Orange Day

1. State check.
2. Minimal activation.
3. Slow practice / repair only.
4. Mental imagery.
5. Optional listening.

### Red Day

1. No heavy playing.
2. Listen, score-read, annotate.
3. One very easy motor warm-up if useful.
4. No negative performance interpretation.

## 7. Memory Model

For every trial/block:

- session_id;
- piece_id;
- composer;
- movement/section;
- measure range;
- task type;
- tempo target;
- tempo actual;
- source: score/audio/memory;
- first attempt or retest;
- errors;
- stops;
- recovery time;
- perceived difficulty;
- physical fatigue;
- mental effort;
- Oura context;
- EEG session reference if active;
- notes.

Derived per piece/section:

- current status;
- last practiced;
- retention interval;
- weak measures;
- error type distribution;
- memory confidence;
- tempo stability;
- re-entry index;
- next_due_at;
- personal difficulty.

## 8. Re-entry Status

| Status | Meaning |
|---|---|
| `new` | never studied or effectively unknown |
| `known_active` | currently playable |
| `fragile` | playable but unstable |
| `dormant` | once known, now unreliable |
| `re_entry` | currently being recovered |
| `recovered` | restored after dormancy |
| `maintenance` | low-dose periodic recall |

## 9. Sport Interaction

Training context matters.

Powerlifting:

- may increase systemic fatigue;
- may affect fine motor control if forearms/back/neck are loaded;
- avoid maximal precision work after heavy sessions if fatigue is high.

Running:

- easy aerobic work may support focus;
- hard intervals may reduce high-load cognitive work later.

Resistance training:

- track soreness and grip/forearm fatigue.

Rules:

- heavy fatigue -> mental practice or listening;
- good recovery -> sight-reading and production;
- deload week -> test re-entry and performance peak;
- poor sleep plus hard training -> no harsh judgment.

## 10. EEG and Sensors

Every piano task must work with or without EEG.

When EEG is active:

- the EEG session must include piano task events;
- task labels must be accurate;
- no zero-sample task-only session may be treated as EEG;
- EEG quality/contact must be reported;
- performance remains the primary outcome.

Useful comparisons:

- sight-reading unknown music;
- playing from memory;
- listening without playing;
- mental imagery from score;
- technical repetition;
- expressive run-through.

## 11. Weekly Review

Weekly dashboard:

- total piano dose;
- sight-reading trend;
- memory failures;
- recovered sections;
- fatigue resistance;
- best state predictors;
- sport/practice interaction;
- pieces requiring re-entry;
- next week's plan.

## 12. Implementation Order

### Step 1 - Piece / Section Catalog

Define pieces, sections, measure ranges and status.

### Step 2 - Session Event Logging

Log piano tasks as behavioral events independent from EEG.

### Step 3 - Sight-Reading Lab

Build first because it has clean outcome metrics.

### Step 4 - Repertoire Re-entry

Add dormant/active/recovered tracking.

### Step 5 - Memory Lab

Add random-entry, hand-separate and mental run-through tests.

### Step 6 - Sensor Context

Attach Oura/sport/caffeine/fatigue context.

### Step 7 - EEG Binding

Embed task events into EEG-linked sessions.

### Step 8 - Adaptive Scheduler

Select what to practice based on state, due retests and performance history.

## 13. Hard Rules

1. Musical performance is the primary outcome.
2. EEG contextualizes; it does not judge the music.
3. No task is valid unless it records what piece/section it refers to.
4. Do not compare sight-reading with memorized playing as if they were the same skill.
5. Do not interpret fatigue-day failures as loss of ability.
6. Always separate cognitive load from motor fatigue.
7. Always preserve raw notes and structured metrics.
8. Always record whether EEG was active.
9. Always schedule retests for re-entry material.
10. Always distinguish new learning from recovery of old skill.

## 14. First Practical Pilot

Pilot name: `Piano Re-entry A`

Duration: 14 days.

Daily target:

- 3-5 min activation;
- 20-90 min piano depending on state;
- one sight-reading or memory measurement;
- one repertoire re-entry target;
- automatic summary.

Success criteria:

- at least 8 sessions completed;
- each session has state/context;
- each task has piece/section metadata;
- at least 3 dormant sections tracked;
- at least 2 delayed retests completed;
- performance trend visible;
- no EEG/session label confusion.

## 15. Final Direction

This should become a personal piano performance laboratory.

The important outcome is not "practice more".

The important outcome is knowing:

- which skills are active;
- which are dormant;
- how fast they return;
- under which conditions reading, memory and expression work best;
- how sport, sleep and stress shape musical performance;
- what practice dose gives the best return without fatigue.
