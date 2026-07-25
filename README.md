MindTune App

Adaptive cognitive protocols, EEG research, sleep-aware learning and audio-first training.

MindTune App is a local-first platform for designing, executing and analysing adaptive cognitive protocols.

The system combines:

* audio-first cognitive training;
* adaptive mantra protocols;
* behavioural measurement;
* EEG acquisition and analysis through BrainLab;
* FocusCalm FC-11 integration;
* sleep and recovery context from Oura;
* deterministic protocol execution through the MindTune Protocol Engine;
* language learning through Hebrew Lab;
* high-quality Hebrew audio generated through SpeechGen;
* event-sourced session history;
* reproducible research exports and dashboards.

MindTune is not a conventional learning application, meditation player or EEG dashboard.

Its central idea is that a cognitive session should be treated as a structured protocol: a sequence of stimuli, pauses, internal responses, recall attempts, confirmations and recovery periods that can adapt while preserving a complete explanation of what happened.

Status: active research and development.
MindTune is not a medical device and is not intended for diagnosis or treatment.

⸻

Vision

Most learning applications assume that the user learns while looking at a screen.

MindTune takes a different approach.

The active part of a MindTune session is designed to occur primarily through:

* listening;
* internal speech;
* anticipation;
* mental recall;
* spoken or manual confirmation;
* controlled pauses;
* reduced visual stimulation;
* optional eyes-closed execution.

The screen is used mainly for:

* choosing a protocol;
* configuring a session;
* checking sensor readiness;
* reviewing results;
* inspecting progress;
* reading explanations;
* analysing research data.

The protocol itself is normally audio-first.

MindTune therefore does not treat audio as decoration. Audio is the principal execution surface of the cognitive protocol.

⸻

System architecture

                           ┌─────────────────────┐
                           │    MindTune App     │
                           │ UI, session control │
                           └──────────┬──────────┘
                                      │
                   ┌──────────────────┼──────────────────┐
                   │                  │                  │
                   ▼                  ▼                  ▼
        ┌──────────────────┐ ┌────────────────┐ ┌─────────────────┐
        │ MindTune Protocol│ │    BrainLab    │ │ Context Engine  │
        │ Engine — MPE     │ │ EEG research   │ │ Oura, history,  │
        │ protocol runtime │ │ and FC-11 data │ │ self-report     │
        └─────────┬────────┘ └───────┬────────┘ └────────┬────────┘
                  │                  │                   │
                  └──────────────────┼───────────────────┘
                                     ▼
                          ┌─────────────────────┐
                          │ Evidence and state  │
                          │ estimation layer    │
                          └──────────┬──────────┘
                                     ▼
                          ┌─────────────────────┐
                          │ Bounded adaptation  │
                          │ or abstention       │
                          └──────────┬──────────┘
                                     ▼
                          ┌─────────────────────┐
                          │ Next executable     │
                          │ protocol action     │
                          └─────────────────────┘

MindTune separates five concerns:

1. MPE executes protocols.
2. BrainLab acquires and analyses EEG.
3. Oura provides longitudinal sleep and recovery context.
4. Domain adapters provide content and scoring semantics.
5. The Audio Asset Pipeline provides approved audio without exposing providers to MPE.

No component may silently take over the responsibilities of another.

⸻

MindTune Protocol Engine

The MindTune Protocol Engine, or MPE, is the deterministic runtime that executes cognitive protocols.

MPE controls:

* protocol state;
* step ordering;
* stimuli;
* pauses;
* anticipation windows;
* internal-response intervals;
* confirmations;
* repetitions;
* branching;
* progression;
* bounded adaptation;
* recovery;
* termination;
* persistence;
* replay.

MPE does not communicate directly with the FocusCalm headset, Oura or SpeechGen.

It receives normalized inputs through explicit interfaces.

This keeps the core independent of:

* EEG hardware;
* wearable brands;
* language;
* speech provider;
* curriculum;
* user interface;
* storage technology.

⸻

Cognitive primitives

MindTune protocols are composed from a small set of reusable cognitive operations.

Typical primitives include:

play
pause
anticipate
expect
confirm
repeat
review
branch
transition
calibrate
adapt

Their purpose is semantic rather than visual.

For example:

* play presents an approved audio asset;
* anticipate creates a prediction window;
* expect gives the learner time to produce an internal or external response;
* confirm presents the target answer;
* repeat schedules bounded rehearsal;
* adapt permits a defined parameter to change;
* calibrate establishes a session baseline.

⸻

Adaptive mantra

The adaptive mantra is one of MindTune’s first complete closed-loop protocols.

It is not a fixed recording, playlist or generic relaxation exercise.

A mantra is represented as a versioned protocol made of executable actions:

phrase
pause
internal repetition
phrase
recovery interval
confirmation

The protocol can regulate:

* cadence;
* silence duration;
* verbal density;
* repetition count;
* block length;
* recovery interval;
* transition speed;
* return-to-baseline rate.

⸻

Baseline execution

A simple baseline sequence may be:

phrase
2-second pause
phrase
2-second pause
phrase

When sustained deterioration is detected, the next executable actions may become:

phrase
4-second pause
repeat phrase
5-second recovery interval
phrase

When the user recovers, the baseline is restored gradually:

5-second pause
→ 4-second pause
→ 3-second pause
→ baseline cadence

The adaptation must modify the protocol that is actually running.

Calculating a recommendation, logging an event or changing a label on the screen is not sufficient.

A genuine adaptation requires:

new evidence
→ cognitive-state update
→ adaptation decision
→ protocol-state modification
→ different next executable action
→ event recording
→ deterministic replay

⸻

Cognitive-state model

A typical MindTune state model includes:

STABLE
   ↓
POSSIBLE_DRIFT
   ↓
RECOVERY_REQUIRED
   ↓
RECOVERING
   ↓
STABLE

Stable

Behavioural execution and valid contextual evidence remain within the expected range.

The baseline protocol continues.

Possible drift

Early deterioration is visible, but the evidence is not yet sufficient for intervention.

The system may continue observing without changing anything.

Recovery required

Sustained evidence indicates that the current pacing or load is no longer appropriate.

The protocol modifies its next actions within predefined limits.

Recovering

Performance has begun to improve.

The adaptation is withdrawn gradually rather than removed immediately.

⸻

Hysteresis and anti-flapping

MindTune must not react to every isolated sample.

State transitions therefore use:

* evidence windows;
* consecutive observations;
* confidence thresholds;
* separate entry and exit thresholds;
* minimum dwell times;
* cooldown periods;
* maximum adaptation steps;
* gradual restoration;
* explicit abstention.

When evidence is uncertain, the correct action may be to make no change.

⸻

BrainLab

BrainLab is MindTune’s EEG acquisition, signal-processing and research engine.

The FocusCalm FC-11 is the current EEG device.

BrainLab is the system that turns the FC-11 stream into:

* preserved raw measurements;
* packet-integrity records;
* signal-quality information;
* validated EEG windows;
* spectral features;
* temporal features;
* artefact indicators;
* session reports;
* longitudinal comparisons;
* context for MPE.

BrainLab does not decide whether a linguistic answer is correct and does not directly rewrite learning state.

Its EEG outputs are evidence, not ground truth.

⸻

BrainLab data path

FocusCalm FC-11
        ↓ Bluetooth Low Energy
FC-11 acquisition driver
        ↓
Raw packet queue
        ↓
Immutable sample and packet recording
        ↓
Integrity and timing reconstruction
        ↓
Contact, lead-off and artefact checks
        ↓
Valid EEG windows
        ↓
Spectral and temporal analysis
        ↓
BrainLab feature stream
        ↓
Session alignment and research reports
        ↓
Optional bounded input to MPE

The acquisition callback is kept lightweight.

Saving, live analysis and optional external streaming use independent workers or queues so that a slow analysis step does not compromise the original recording.

⸻

FocusCalm FC-11

MindTune connects directly to the FocusCalm FC-11 through Bluetooth Low Energy.

The verified lifecycle is represented conceptually as:

BLE discovery
→ GATT connection
→ application pairing or validation
→ stream configuration
→ START
→ EEG packet acquisition
→ STOP
→ disconnection

The implementation records information such as:

* packet sequence number;
* raw signed ADC values;
* sample index;
* packet-arrival time;
* reconstructed sample time;
* packet gaps;
* contact state;
* lead-off state;
* motion and orientation;
* queue overflow;
* integrity warnings;
* software and processing version.

The observed stream operates at approximately 247–250 samples per second, depending on the representation and timing layer used.

Timing is reconstructed from the ordered sample stream and must not rely only on repeated or low-resolution packet timestamps.

⸻

Raw preservation

BrainLab preserves the original acquisition evidence before applying transformations.

The raw layer may include:

* raw_s24 ADC counts;
* packet identifiers;
* frequency code;
* timing metadata;
* contact state;
* acquisition events;
* experimental markers;
* integrity statistics.

A derived microvolt representation may also be stored, but it must remain clearly labelled as derived and tied to its conversion assumptions.

Raw, transformed and interpreted values must remain distinguishable.

⸻

EEG processing

BrainLab processes EEG in quality-controlled windows.

Quality checks

A window may be rejected or downgraded because of:

* contact loss;
* lead-off;
* missing packets;
* queue overflow;
* excessive movement;
* flatline;
* clipping;
* saturation;
* implausible amplitude;
* abrupt discontinuity;
* probable blink or muscle artefact;
* excessive electrical interference;
* insufficient valid samples.

Poor-quality EEG must not trigger adaptation.

The behavioural protocol may continue even when EEG is unavailable.

⸻

Spectral features

BrainLab supports features such as:

* power spectral density;
* delta power;
* theta power;
* alpha power;
* low-beta power;
* high-beta power;
* gamma power where meaningful;
* absolute band power;
* relative band power;
* peak alpha frequency;
* normalized trends;
* alpha-to-theta ratio;
* theta-to-beta ratio;
* spectrograms.

Temporal and statistical features

* root mean square amplitude;
* peak-to-peak amplitude;
* variance;
* window range;
* stability;
* discontinuity rate;
* packet-loss rate.

Complexity features

* spectral entropy;
* Hjorth activity;
* Hjorth mobility;
* Hjorth complexity.

Quality outputs

* contact state;
* artefact flags;
* missing-packet count;
* packet-gap ratio;
* motion contamination;
* valid-sample ratio;
* overall quality score.

⸻

Native and independent features

MindTune may preserve both:

* native FocusCalm or BrainCo-derived outputs;
* independently calculated BrainLab features.

These are not interchangeable.

Examples of native outputs may include:

* attention-related values;
* meditation-related values;
* native EEG statistics;
* moving-average outputs.

Examples of independent BrainLab outputs include:

* band powers;
* entropy;
* Hjorth parameters;
* packet-integrity metrics;
* independently computed trends.

Every feature must identify:

* source;
* processing version;
* time window;
* quality status;
* derivation method.

⸻

Oura integration

Oura is MindTune’s primary sleep, recovery and readiness context source.

Oura is not a live EEG device and does not directly control the current protocol.

It provides longitudinal information about the physiological conditions under which a session takes place.

Relevant Oura context may include:

* sleep duration;
* sleep timing;
* sleep efficiency;
* sleep stages;
* sleep score;
* readiness score;
* resting heart rate;
* heart-rate variability;
* respiratory rate;
* body-temperature deviation;
* previous-day activity;
* recovery trends;
* bedtime regularity.

⸻

Role of Oura

Oura allows MindTune to investigate questions such as:

* Does recall decline after short or fragmented sleep?
* Is the user more vulnerable to cognitive drift on low-readiness days?
* Does EEG quality or spectral structure change with sleep debt?
* Are recovery interventions more effective after good sleep?
* Does mantra pacing need to begin more conservatively after poor recovery?
* Are response latency and confidence related to HRV or resting heart rate?
* Which protocols produce stable performance across different recovery states?

Oura is contextual evidence.

It must not:

* determine correctness;
* rewrite learning history;
* diagnose fatigue;
* force an adaptation from one score;
* be treated as an exact measure of cognitive capacity.

⸻

Oura data flow

Oura API or local export
        ↓
Timestamp normalization
        ↓
Daily sleep and recovery record
        ↓
Session-date and pre-session alignment
        ↓
Context snapshot
        ↓
Longitudinal analysis

A protocol session should record which Oura context was available at its start.

That context remains attached to the session for later research even when it is not used in live adaptation.

⸻

Evidence hierarchy

MindTune does not treat all evidence as equal.

Primary behavioural evidence

Behavioural evidence is authoritative for task performance:

* correctness;
* response latency;
* confidence;
* omission;
* error type;
* repetition history;
* retention;
* transfer;
* interruption;
* recovery performance.

Real-time contextual evidence

* quality-controlled EEG;
* contact state;
* motion;
* session fatigue reports;
* live interaction stability.

Longitudinal contextual evidence

* Oura sleep and readiness;
* previous sessions;
* forgetting history;
* item difficulty;
* time since last exposure;
* training load.

EEG and Oura may modulate bounded pacing, repetition or recovery decisions.

They do not determine whether knowledge exists.

⸻

Audio Asset Pipeline

MindTune uses an Audio Asset Pipeline rather than allowing protocols to call speech providers directly.

The current approved Hebrew speech-generation pipeline is based on SpeechGen.

Azure is not part of the canonical MindTune audio architecture.

MPE never names SpeechGen directly.

A protocol asks for a logical asset:

item identity
+ language
+ asset role
+ voice profile
+ rate profile
+ prosody requirements

The pipeline resolves that request to an approved audio asset.

⸻

Audio flow

Protocol requests logical audio role
        ↓
Audio Asset Pipeline
        ↓
Hebrew text normalization
        ↓
Niqqud and pronunciation preparation
        ↓
SpeechGen rendering
        ↓
Automated technical validation
        ↓
Linguistic and pronunciation review
        ↓
Approved local audio asset
        ↓
MPE playback

The result is cached and versioned so that a replayed protocol can use the same approved audio.

⸻

Why SpeechGen

The objective is not merely to produce understandable speech.

Hebrew learning requires attention to:

* modern Israeli pronunciation;
* stress;
* vowel realization;
* niqqud;
* homographs;
* clitics;
* verb forms;
* masculine and feminine forms;
* natural prosody;
* phrase boundaries.

Speech generation must therefore be followed by linguistic validation.

No TTS provider is treated as linguistically infallible.

⸻

Provider invisibility

Protocols reference:

* asset role;
* item identifier;
* language;
* approved version.

Protocols do not reference:

* SpeechGen API details;
* account credentials;
* provider-specific URLs;
* temporary render identifiers.

This allows the pipeline to evolve without rewriting MPE.

⸻

Hebrew Lab

Hebrew Lab is the first major learning domain built on MindTune.

It supports modern Israeli Hebrew through structured cognitive protocols rather than a simple flashcard interface.

Hebrew Lab may represent and measure:

* vocabulary;
* expressions;
* roots;
* binyanim;
* morphology;
* conjugation;
* clitics;
* pronunciation;
* listening;
* recognition;
* immediate recall;
* delayed recall;
* internal production;
* contextual use;
* error correction;
* transfer;
* re-entry after interruption.

⸻

Hebrew content pipeline

Source material
        ↓
Provenance preservation
        ↓
Linguistic audit
        ↓
Canonical Hebrew representation
        ↓
Pronunciation and stress specification
        ↓
SpeechGen asset generation
        ↓
Audio validation
        ↓
Versioned curriculum
        ↓
Domain adapter
        ↓
MPE protocol execution

Hebrew-specific knowledge remains inside the Hebrew domain.

MPE does not contain:

* binyan logic;
* root logic;
* niqqud rules;
* transliteration rules;
* Hebrew scoring rules.

⸻

Protocol families

MindTune’s protocol library includes or anticipates eight broad families:

1. Encoding
2. Recall
3. Transformation
4. Recognition
5. Internal Speech
6. Listening
7. Consolidation
8. Recovery

Examples include:

* vocabulary encoding;
* immediate recall;
* delayed recall;
* cued recall;
* recognition;
* morphology transformation;
* anticipation and confirmation;
* listening immersion;
* internal repetition;
* re-entry after interruption;
* adaptive mantra;
* recovery pacing.

⸻

Example Hebrew protocol

Objective:
Recall the Hebrew target from an Italian cue.
1. Play the Italian cue.
2. Open an internal-recall interval.
3. Record latency or optional confirmation.
4. Play the approved SpeechGen Hebrew asset.
5. Compare internally.
6. Record confidence.
7. Repeat, advance or schedule review.
8. Adapt only within protocol bounds.

The learner may complete most of this sequence with eyes closed.

⸻

Event-sourced execution

MindTune records meaningful operations as immutable events.

Possible events include:

session_started
context_snapshot_recorded
oura_context_attached
device_connected
eeg_stream_started
eeg_packet_received
signal_quality_changed
protocol_started
stimulus_prepared
audio_asset_resolved
audio_presented
response_window_opened
response_received
response_evaluated
cognitive_state_updated
adaptation_decision_recorded
next_action_modified
recovery_started
baseline_restored
protocol_completed
eeg_stream_stopped
session_closed

The event stream should allow reconstruction of:

* what was presented;
* which approved audio version was used;
* what the participant did;
* which EEG evidence was valid;
* which Oura context was attached;
* why an adaptation occurred;
* what changed;
* what was actually executed;
* whether replay reproduces the same result.

⸻

Session data model

A complete session may include:

session/
├── metadata.json
├── events.jsonl
├── protocol_snapshot.json
├── context/
│   ├── oura_snapshot.json
│   └── self_report.json
├── eeg/
│   ├── packets.parquet
│   ├── samples.parquet
│   ├── quality_events.jsonl
│   ├── imu.parquet
│   ├── native_features.parquet
│   └── brainlab_features.parquet
├── behavior/
│   ├── responses.parquet
│   └── trial_summary.parquet
├── audio/
│   └── asset_manifest.json
└── reports/
    ├── protocol_summary.json
    └── session_report.html

The exact schema may evolve.

Every derived record should preserve enough information to trace it back to:

* session;
* participant or pseudonymous identity;
* device;
* packet or sample range;
* protocol version;
* content version;
* audio asset version;
* BrainLab version;
* adaptation-policy version;
* software commit.

⸻

Local-first infrastructure

MindTune is designed to operate locally.

A typical architecture may include:

FocusCalm FC-11
        ↓ BLE
MindTune App on macOS or Linux
        ↓
Local session storage
        ↓
Raspberry Pi research infrastructure
        ↓
BrainLab processing, database and dashboards
        ↓
Longitudinal integration with Oura and other context

Local-first operation supports:

* ownership of EEG data;
* offline sessions;
* inspectable processing;
* reproducible local environments;
* explicit export;
* Raspberry Pi integration;
* reduced cloud dependency.

SpeechGen is used to produce approved audio assets, but protocol execution can use cached local assets.

A live cognitive session should not depend on generating new cloud audio at the moment of playback.

⸻

Research dashboard

MindTune can expose read-only analytical views including:

* session history;
* protocol timelines;
* EEG quality;
* packet integrity;
* band-power trends;
* cognitive-state transitions;
* adaptation events;
* response accuracy;
* response latency;
* confidence;
* item difficulty;
* retention;
* forgetting;
* sleep-context comparisons;
* readiness-context comparisons;
* Oura and performance correlations;
* eyes-open and eyes-closed comparisons;
* protocol summaries;
* CSV and JSON export.

Dashboard calculations are derived views.

They do not rewrite original events.

⸻

Reproducibility

A session should be reproducible from:

* preserved raw acquisition;
* behavioural events;
* quality events;
* protocol definition;
* adaptation-policy version;
* approved audio asset manifest;
* Oura context snapshot;
* BrainLab processing version;
* software commit;
* configuration.

Reprocessing the same data through the same versioned pipeline should generate equivalent results within documented numerical tolerances.

⸻

Repository structure

The target repository structure is:

mindtune_console/
├── app/
│   ├── ui/
│   ├── sessions/
│   └── dashboards/
│
├── packages/
│   ├── mpe/
│   │   ├── src/mpe/
│   │   │   ├── protocol/
│   │   │   ├── events/
│   │   │   ├── persistence/
│   │   │   └── replay/
│   │   └── tests/
│   │
│   ├── brainlab/
│   │   ├── src/brainlab/
│   │   │   ├── acquisition/
│   │   │   ├── signal/
│   │   │   ├── quality/
│   │   │   ├── features/
│   │   │   ├── storage/
│   │   │   └── reports/
│   │   └── tests/
│   │
│   ├── devices/
│   │   └── fc11/
│   │       ├── transport.py
│   │       ├── protocol.py
│   │       ├── packets.py
│   │       ├── adapter.py
│   │       └── tests/
│   │
│   ├── wearables/
│   │   └── oura/
│   │       ├── importer.py
│   │       ├── context.py
│   │       └── tests/
│   │
│   └── audio/
│       ├── assets/
│       ├── speechgen/
│       ├── validation/
│       └── tests/
│
├── domains/
│   ├── mantra/
│   ├── hebrew/
│   └── piano/
│
├── docs/
│   ├── architecture/
│   ├── eeg/
│   ├── wearables/
│   ├── audio/
│   ├── protocols/
│   ├── research/
│   └── safety/
│
├── tests/
├── compose/
├── Dockerfile
└── README.md

⸻

Current implementation

MindTune already has working or recovered implementations for substantial parts of:

* direct FocusCalm FC-11 acquisition;
* BLE stream startup and capture;
* raw packet recording;
* queue-isolated acquisition;
* timing reconstruction;
* packet-integrity analysis;
* signal-quality checks;
* EEG spectral analysis;
* BrainLab feature extraction;
* session reports;
* validated EEG recordings;
* native-parity research;
* Oura data ingestion;
* longitudinal health database integration;
* MPE event and protocol foundations;
* Immediate Recall;
* Recognition;
* Hebrew domain work;
* SpeechGen Hebrew audio-pipeline specification;
* adaptive-protocol architecture;
* research dashboards;
* Raspberry Pi processing.

Some components originated in previous MindTune Lab application bundles and research directories and are being consolidated into the canonical repository.

⸻

Verification

Verification must cover more than whether the interface opens.

Required test areas include:

* BLE connection lifecycle;
* FC-11 packet parsing;
* packet continuity;
* timing reconstruction;
* raw preservation;
* signal-quality rejection;
* feature reproducibility;
* Oura timestamp alignment;
* audio-asset identity;
* SpeechGen output validation;
* Hebrew pronunciation approval;
* protocol-state transitions;
* adaptation bounds;
* abstention;
* event-schema validity;
* deterministic replay;
* interrupted-session recovery.

⸻

Safety and scientific limits

MindTune is experimental software.

It is not:

* a medical device;
* a diagnostic system;
* a treatment;
* a clinical monitor;
* a validated neuropsychological test;
* a measure of intelligence;
* a substitute for medical care.

Consumer EEG can be affected by:

* electrode contact;
* movement;
* muscle activity;
* eye movement;
* electrical interference;
* proprietary processing;
* limited sensor placement.

Oura measurements are estimates derived from a consumer wearable.

Speech synthesis can contain pronunciation or prosody errors.

MindTune must therefore:

* preserve provenance;
* record quality;
* distinguish observation from interpretation;
* allow abstention;
* avoid clinical claims;
* keep behavioural evidence primary;
* require linguistic review of Hebrew audio;
* keep raw, native and derived data separate.

⸻

Privacy

The public repository must not include:

* personal EEG recordings;
* Oura exports;
* health databases;
* participant identities;
* credentials;
* API keys;
* proprietary APK files;
* vendor native libraries;
* proprietary machine-learning models;
* copied decompiled vendor source;
* private audio assets whose licence prohibits redistribution.

Local datasets should be protected through:

* filesystem permissions;
* encrypted storage;
* backups;
* access control;
* pseudonymous identifiers;
* explicit export procedures.

⸻

Roadmap

BrainLab

* consolidate the recovered EEG engine;
* preserve raw acquisition behaviour;
* formalize packet and sample schemas;
* version the signal-processing pipeline;
* improve artefact detection;
* add deterministic reprocessing tests;
* unify live and offline features;
* strengthen longitudinal analysis.

FocusCalm FC-11

* document the verified BLE protocol;
* isolate device-specific transport;
* formalize pairing and reconnection;
* improve diagnostics;
* preserve raw data during analysis failures;
* validate timing against an external reference.

Oura

* formalize the Oura context adapter;
* snapshot relevant daily metrics at session start;
* align sleep episodes and protocol sessions;
* analyse sleep, HRV, readiness and performance;
* keep Oura contextual rather than authoritative.

Audio and SpeechGen

* consolidate the approved SpeechGen Hebrew pipeline;
* eliminate obsolete Azure references;
* version voice and rendering profiles;
* validate stress and pronunciation;
* cache approved assets locally;
* add regression tests for audio identity;
* support controlled regeneration when content changes.

Adaptive mantra

* formalize mantra units;
* version cadence profiles;
* implement bounded adaptation;
* validate recovery transitions;
* compare behavioural-only and EEG-informed modes;
* incorporate Oura only as pre-session context;
* add full event replay.

Hebrew Lab

* complete the domain adapter;
* migrate reviewed curriculum;
* implement recall, production, context and transfer;
* integrate SpeechGen assets;
* support re-entry after interruption;
* measure delayed retention.

Additional domains

* Piano Lab;
* music-reading protocols;
* auditory discrimination;
* memory training;
* additional languages;
* motor-timing protocols.

⸻

Engineering invariants

MindTune should preserve these rules:

* events are append-only;
* events are validated before persistence;
* replay does not depend on hidden mutable state;
* MPE remains hardware-independent;
* BrainLab preserves raw evidence;
* invalid EEG cannot force adaptation;
* Oura cannot determine correctness;
* SpeechGen remains behind the Audio Asset Pipeline;
* Azure is not part of the approved architecture;
* Hebrew pronunciation is reviewed;
* adaptation changes actual execution;
* protocol changes are bounded;
* recovery is gradual;
* uncertainty permits abstention;
* personal data is not committed;
* proprietary vendor artefacts are not committed.

⸻

Licence

No licence should be assumed unless a LICENSE file is present.

FocusCalm, BrainCo, Oura and SpeechGen names and technologies remain the property of their respective owners.

MindTune is an independent research project and is not affiliated with or endorsed by those companies.

⸻

Acknowledgements

MindTune draws on research and engineering practices from:

* cognitive psychology;
* retrieval practice;
* adaptive training;
* EEG signal processing;
* sleep and recovery research;
* psycholinguistics;
* second-language acquisition;
* music cognition;
* event-sourced systems;
* reproducible research;
* human-in-the-loop validation.

⸻

Contact

MindTune Lab

For technical discussion, research collaboration or development enquiries, use the contact information published in this repository.
