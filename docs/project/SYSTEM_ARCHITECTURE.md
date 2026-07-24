# MindTune Lab — System Architecture

## 1. Purpose

This document describes the complete MindTune Lab ecosystem. It treats the **MindTune Protocol Engine (MPE)** and the **Hebrew Engine** as approved subsystems and defines how all other components are organized around them.

This is a design and planning document. It does not contain implementation code, Dockerfiles, or compose files.

## 2. Design principles

1. **Subsystem boundaries are respected.** MPE and the Hebrew Engine are not redesigned here.
2. **Deterministic reproducibility.** Any developer or AI agent can check out the repository and understand where each responsibility lives.
3. **Domain isolation.** Language-specific logic is isolated in domain engines; core MPE logic is domain-agnostic.
4. **Event-driven truth.** Runtime state is derived from an immutable event stream.
5. **Progressive expansion.** The architecture supports future engines (piano, additional languages), sensors, analytics, and UI without re-architecting core MPE.

## 3. Ecosystem layers

```text
┌─────────────────────────────────────────────────────────────┐
│                    Applications                             │
│   CLI    Dashboard    Future Mobile / Web UI               │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    Core Platform                            │
│   MPE Runtime    Event Store    Persistence    Scheduler   │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    Provider Layer                           │
│   Observation providers    Renderers    Domain normalizers │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    Domain Engines                           │
│   Hebrew Engine    Future Piano Engine    Future Lang...   │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    Analytics & Research                     │
│   BrainLab    Experiment registry    Analysis notebooks    │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    Infrastructure                           │
│   Docker    Compose    Volumes    Networks    Secrets      │
└─────────────────────────────────────────────────────────────┘
```

## 4. Infrastructure layer

### 4.1 Docker

Docker provides reproducible runtime environments for:

- MPE runtime and API
- Event store
- Persistence services
- Hebrew engine
- Provider adapters
- Development and test containers

`DOCKER_ARCHITECTURE.md` specifies the layout. No Dockerfiles or compose files are part of this phase.

### 4.2 Compose

Compose is the primary local orchestration mechanism. Future compose files will group services by environment:

- `compose/development.yaml`
- `compose/testing.yaml`
- `compose/production.yaml` (future)

### 4.3 Volumes

Named volumes are used for:

- Event-store data
- Persistence backups
- Rendered media cache
- Provider model caches
- Research artifacts

### 4.4 Networks

Services communicate over isolated Docker networks:

- `mpe-core` for MPE runtime, event store, and persistence
- `mpe-providers` for observation providers and renderers
- `mpe-domain` for domain engines (Hebrew, piano, etc.)
- `mpe-research` for analytics and BrainLab (future)

## 5. Core Platform layer

### 5.1 MPE (MindTune Protocol Engine)

MPE is the approved cognitive-protocol execution runtime. It is defined in:

- `docs/MPE_ARCHITECTURE_V1_1.md`
- `docs/MPE_OBJECT_MODEL_V1_1.md`
- `docs/MPE_EVENT_MODEL_V1_1.md`
- `docs/MPE_PROVIDER_BOUNDARIES.md`
- `docs/MPE_HEBREW_PROVIDER_CONTRACT.md`
- `docs/MPE_ADAPTATION_CONTRACT.md`
- `docs/specification/v1.1/*.md`

Responsibilities:

- Parse `ProgramVersion` and `ProtocolVersion`.
- Execute trials according to `TaskDefinition` role sequences.
- Manage `Session`, `Block`, `Trial`, `Instruction`, `ResponseWindow`, and `FeedbackEvent` lifecycle.
- Emit events to the event store.
- Route provider calls.
- Compute `Outcome` from events.

MPE does **not** contain language-specific correctness logic.

### 5.2 Event Store

The event store is the single source of truth for runtime state. It stores every `MPE_EVENT_MODEL_V1_1.md` event in append-only order, keyed by `session_id` and `session_sequence_number`.

Responsibilities:

- Append-only writes.
- Monotonic sequence guarantees per session.
- Event schema validation.
- Replay by session.

### 5.3 Persistence

Persistence includes:

- Event-store storage
- Object snapshots for fast replay
- `ContentItem` and fixture registries
- Provider caches
- `Outcome` summaries

Responsibilities:

- Classify objects as persistent/derived/cached/ephemeral per `PERSISTENCE_BOUNDARIES.md`.
- Maintain referential integrity between snapshots and events.
- Support reconstruction of any session from the event stream.

### 5.4 Scheduler

The scheduler consumes `ScheduleDecision` events and produces the next `ScheduleDecision`. It is policy-driven and uses fixed random seeds for deterministic reproducibility.

Responsibilities:

- Item selection.
- Block transitions.
- Session termination.
- Exclusion lists with reasons.

## 6. Provider layer

Providers are adapters that MPE invokes through documented contracts.

### 6.1 Observation providers

- `KeyboardObservationProvider`
- `MicrophoneObservationProvider` (future)
- `EEGObservationProvider` / `SensorObservationProvider` (future BrainLab)

Responsibilities: produce `Observation` objects; never score correctness.

### 6.2 Renderers

- `HebrewRenderer` (text-to-speech, media generation)
- `AudioRenderer` (generic audio playback)
- `VisualRenderer` (future; screen is secondary by design)

Responsibilities: turn `StimulusRequest` into `RenderedStimulus`; never evaluate.

### 6.3 Response interpreters

- `TypedTextInterpreter`
- `ASRInterpreter` (future)
- `ButtonInterpreter`

Responsibilities: turn `CapturedResponse` into `ResponseInterpretation`; never canonicalize to domain form.

### 6.4 Domain normalizers

- `HebrewDomainNormalizer`
- Future normalizers for other languages or domains

Responsibilities: turn `ResponseInterpretation` into `DomainNormalizedResponse`; never compare to expected answers.

## 7. Domain Engines layer

### 7.1 Hebrew Engine

The Hebrew Engine is an approved subsystem. It owns:

- `data/hebrew/phase3/`
- `hebrew/` (existing top-level directory)
- `docs/MPE_HEBREW_PROVIDER_CONTRACT.md`

Responsibilities:

- Provide `ContentItem` metadata (root, binyan, form, status).
- Normalize Hebrew responses.
- Evaluate Hebrew responses against expected answers.
- Declare accepted variants, scope status, and evidence groups.

MPE core delegates all Hebrew correctness decisions to this engine.

### 7.2 Future Piano Engine

A future domain engine for piano/auditory skill learning. It will mirror the Hebrew Engine pattern:

- Provide `ContentItem` for pitches, rhythms, phrases.
- Normalize observed performances (e.g., MIDI or audio).
- Evaluate performance against target phrase.

### 7.3 Future Language Engines

Additional language engines (e.g., Italian, Arabic) will follow the same provider contract pattern. Each will own its own `data/<language>/` directory and domain provider package.

## 8. Analytics & Research layer

### 8.1 BrainLab

BrainLab is the future EEG and sensor-research subsystem. It is quarantined from runtime decision-making in Phase 4.

Responsibilities:

- Collect and preprocess sensor observations.
- Produce diagnostic `StateEstimate` objects.
- Run offline analyses.
- Feed validated models back as optional, non-blocking signals.

### 8.2 Research registry

`docs/research/` contains ontology audits, decomposition matrices, and critical reviews. These documents are immutable historical artifacts unless a new ADR supersedes them.

### 8.3 Analysis artifacts

Future notebooks, scripts, and reports live under `research/` and `notebooks/`. They are read-only with respect to runtime state.

## 9. Applications layer

### 9.1 CLI

The CLI is the primary interface during Phase 4B and beyond. Responsibilities:

- Start sessions.
- Run protocol fixtures.
- Replay sessions.
- Run diagnostics.
- Administer registries.

### 9.2 Future UI

A future web or mobile UI may provide setup, selection, and review. It must not replace the CLI as the source of truth for protocol execution. Existing `app.js`, `index.html`, `server.py` files are legacy prototypes and not part of the approved Phase 4B architecture.

### 9.3 Dashboard

A future analytics dashboard for reviewing `Outcome` summaries, session histories, and research metrics. It is read-only and optional.

## 10. Boundaries and rules

| Rule | Rationale |
|---|---|
| MPE core is domain-agnostic. | Hebrew/language-specific logic must live in domain engines. |
| Events are append-only and immutable. | Reconstruction, replay, and audit depend on this. |
| Provider contracts are versioned. | Each provider declares `*_version` and matches `ProtocolVersion.dependency_versions`. |
| Safety overrides everything. | `SafetyInstruction` and `SafetyEvent` take precedence over protocol flow. |
| Research signals are diagnostic only in Phase 4. | EEG/state estimates must not block or override protocol execution. |

## 11. Future evolution

| Phase | Likely addition |
|---|---|
| 4B | MPE runtime, event store, persistence, CLI, Hebrew provider integration |
| 5A | Adaptation policies and `AdaptationDecision` |
| 5B | BrainLab sensor ingestion and offline `StateEstimate` production |
| 6 | UI/Dashboard, multi-language engines, Piano Engine |
| 7+ | Production orchestration, scalable event-store backends, cloud deployments |
