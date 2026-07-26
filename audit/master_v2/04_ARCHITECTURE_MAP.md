# 04 — Architecture Map

## 1. Layer Model

```
┌─────────────────────────────────────────────────────────────┐
│  Presentation / UI                                          │
│  index.html / app.js / styles.css  +  server.py routes      │
├─────────────────────────────────────────────────────────────┤
│  Orchestration                                               │
│  server.py (RPi bridge, EEG jobs, Oura, Hebrew MLF)         │
├─────────────────────────────────────────────────────────────┤
│  Protocol Engine (MPE)                                       │
│  packages/mpe/src/mpe/                                       │
│  Runtime → Event Store → Replay → Protocol Runners          │
├─────────────────────────────────────────────────────────────┤
│  Domain Adapters                                             │
│  packages/mpe/src/mpe/domains/hebrew/                        │
│  hebrew/ + mantra/phase1/                                    │
├─────────────────────────────────────────────────────────────┤
│  Sensor / EEG / Wearables                                    │
│  mindtune_capture/ (FC11 BLE), oura_api.py, help_profiler.py │
├─────────────────────────────────────────────────────────────┤
│  Data & Persistence                                          │
│  data/, output/, SQLite (mpe/persistence/, event store),     │
│  CSV (mindtune_capture), .oura_token                         │
└─────────────────────────────────────────────────────────────┘
```

## 2. Core Package Boundaries (`packages/mpe/`)

| Module | Responsibility | Inputs | Outputs | Ownership |
|---|---|---|---|---|
| `runtime.py` | Session/trial event emission, clock, `RuntimeState` | `EventStore`, `ProviderSet`, `Clock` | `Event` stream, `RuntimeState` | Runtime owns event ordering and session lifecycle |
| `events.py` | Canonical event envelope and payload schemas | Event type + payload | `Event` dataclass | Event type/payload author |
| `event_store.py` | Append-only in-memory store contract + `InMemoryEventStore` | `Event`, expected_version | persisted `Event` stream | Event store owns `session_sequence_number` uniqueness |
| `replay.py` | Deterministic reconstruction of `RuntimeState` | `EventStore` + `session_id` | `RuntimeState` | Replay is pure function over events |
| `aggregates.py` | State machine handlers for every canonical event | `Event` | updated `RuntimeState` | Aggregate owns runtime projections |
| `providers.py` | Provider protocols (Renderer, Observation, Evaluator, EEG, Scheduler) and mocks | provider-specific inputs | capability/dict outputs | Provider owns side effects; runtime owns calls |
| `protocol/trial_pipeline.py` | Domain-agnostic trial event flow | `InstructionSpec`, `StimulusSpec`, `ResponseWindowSpec`, `ObservationSpec` | `Event` stream | Shared layer owns canonical trial fields |
| `protocol/immediate_recall.py` | Immediate Recall runner with closed-loop adaptation | fixture, adaptation rule, store | `ImmediateRecallResult` (events + outcomes) | Protocol runner owns stimulus/response semantics |
| `protocol/cognitive_state.py` | Behavioral-authoritative cognitive load estimator | correctness, latency, EEG features | `CognitiveStateUpdate` | Estimator owns state, but behavioral evidence is authoritative |
| `protocol/adaptation_policy.py` | Bounded response-deadline adaptation | `CognitiveStateUpdate`, current deadline | `AdaptationDecision`, next deadline | Policy owns adaptation semantics |
| `domains/hebrew/adapter.py` | Hebrew immediate-recall domain adapter | Hebrew content, typed/self response | `ContentItem`, `BehavioralEvidence` | Domain adapter owns Hebrew semantics |
| `domains/hebrew/help/` | HeLP norm loader/repository/profiler | CSV/JSON HeLP data | `HeLPFormEvidence`, difficulty priors | HeLP is read-only source |

## 3. Runtime Sequence (Immediate Recall)

1. `ImmediateRecallRunner.run_session()` creates `Runtime` + `EventStore`.
2. `runtime.create_session()` → emits `session_created`.
3. `runtime.start_session()` → emits `session_started` with `random_seed`.
4. `pipeline.emit_block_started()` → `block_started`.
5. `BoundedRepeatPlan` iterates fixture items.
6. `_execute_item_trial()`:
   - `poll_eeg()` (before overt response) → `observation_received` if EEG present.
   - `emit_instruction(PRESENT_STIMULUS)` → `instruction_started`/`instruction_completed`.
   - `emit_stimulus()` → `stimulus_requested` / `stimulus_ready`.
   - `open_response_window()` → `response_window_opened`.
   - `poll_observation()` → `observation_received`.
   - `run_response_pipeline()` → `captured_response_created` → `response_interpreted` → `domain_response_normalized`.
   - `emit_evaluation()` → `evaluation_completed`.
   - `emit_feedback()` → `feedback_started`/`feedback_completed`.
   - `_apply_adaptation()` → `CognitiveStateEstimator.update()` → `AdaptationPolicy.decide()` → `adaptation_decision` and new `response_deadline` for next trial.
7. `BoundedRepeatPlan` requeues or advances.
8. `runtime.complete_session()` → `session_completed`.
9. `Replay` can reconstruct `RuntimeState` from the stored event stream.

## 4. Sensor / EEG Pipeline (`mindtune_capture/`)

```
FC11 BLE (bleak/CoreBluetooth)
    → fc11_mac_capture.py (protobuf framing, raw samples)
    → fc11_capture_pipeline.py (bounded queues, CSV writers)
    → scientific_qc.py (window-level QC)
    → scientific_spectral.py (PSD, band powers)
    → lsl_bridge.py (optional Lab Streaming Layer outlet)
    → brainlab_features.csv / scientific_spectral.json
```

## 5. Data Flows and Ownership

- **Authoritative session record:** the `Event` stream in `EventStore`.
- **Derived objects:** `RuntimeState`, `Session`, `Trial`, `BlockExecution`.
- **Persistent media:** `RenderedStimulus.media_handle` stored outside the event store (e.g., `output/mantra_global_tts_cache/`).
- **Sensor raw data:** `mindtune_capture/` CSV/JSON per session.
- **Wearable data:** `.oura_token` + fetched daily JSON.
- **Behavioral event DB:** `packages/mpe/persistence/store.py` experiments with SQLite.

## 6. Coupling Notes

- **Low coupling:** MPE protocol layer is domain-agnostic; Hebrew logic is isolated in `mpe/domains/hebrew/` and `hebrew/`.
- **Medium coupling:** `mantra/phase1/` depends on `hebrew/` for phonology and conjugation.
- **High coupling:** `server.py` couples HTTP API, RPi bridge, FC11 subprocess, Oura, Hebrew MLF, and UI; `app.js` is a 6,896-line monolith.
