# 21 — V2 Target Architecture

## 1. Repository Strategy

V2 is developed incrementally inside the current `mindtune_console` repository. Use a strangler architecture:

- Preserve `packages/mpe/` as the event-sourced protocol runtime.
- Add a domain-neutral `packages/clm/` (Closed-Loop Mantra) cognitive-control package.
- Move new functionality behind typed interfaces.
- Gradually bypass `server.py` and `app.js` as replacement paths are tested.
- Retain compatibility until replacements are fully validated.

## 2. Package Boundaries (Revised)

```
mindtune_console/
├── packages/
│   ├── mpe/                   # Event-sourced protocol runtime (preserved)
│   ├── clm/                   # Closed-loop control kernel (new)
│   │   ├── observation.py     # ObservationFrame, quality gating
│   │   ├── estimator.py       # CognitiveStateEstimate with uncertainty
│   │   ├── decision.py        # ControlDecision (apply/maintain/withdraw/abstain/stop)
│   │   ├── control_state.py   # MantraControlState
│   │   ├── actuator.py        # Deterministic in-memory actuator
│   │   ├── renderer.py        # AdaptedStimulus renderer contract
│   │   ├── outcome.py         # InterventionOutcome evaluation
│   │   └── events.py          # CLM event schemas and provenance
│   ├── mpe-adapters/          # Domain adapters (hebrew, piano, ...)
│   ├── mpe-sensors/           # Sensor gateways (simulated, FC11, LSL, replay, RPi optional)
│   └── mpe-analysis/          # Replay, export, dashboards
├── api/                       # FastAPI (CLM-05)
├── web/                       # Web UI; PyWebView optional thin container
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
└── tests/
```

## 3. CLM Control Cycle

1. `SensorGateway` emits `ObservationFrame` (multimodal evidence + quality).
2. `EvidenceQualityGate` drops or flags low-quality observations.
3. `CognitiveStateEstimator` produces `CognitiveStateEstimate` with uncertainty.
4. `DecisionEngine` produces `ControlDecision`:
   - `APPLY` — change control state.
   - `MAINTAIN` — keep current state.
   - `WITHDRAW` — gradually reduce assistance.
   - `ABSTAIN` — insufficient or conflicting evidence.
   - `STOP` — safety/emergency.
5. `MantraControlState` is updated with bounded, safe parameters.
6. `MantraActuator` applies control state and returns `ActuationReceipt`.
7. `AdaptedStimulusRenderer` produces the next stimulus from the receipt.
8. `InterventionOutcome` is evaluated.
9. Every step appends an event to `EventStore`.
10. `Replay` reproduces `MantraControlState` and adapted stimulus deterministically.

## 4. Data Ownership

- `EventStore` is authoritative for all control, protocol, and outcome events.
- `SQLite` for local/test; `PostgreSQL` deferred to later platform phase.
- `RenderedStimulus` media stored as immutable files; events store `media_handle` and parameters.
- Sensor raw data stored as immutable files (EDF/CSV/BDF) with `session_id` linkage.

## 5. Adapter Contracts

- `SensorGateway` → `stream()` / `poll()` → `ObservationFrame`
- `EvidenceQualityGate` → `validate(frame) -> ValidatedFrame`
- `CognitiveStateEstimator` → `estimate(validated) -> CognitiveStateEstimate`
- `DecisionEngine` → `decide(estimate, current_control_state) -> ControlDecision`
- `MantraActuator` → `apply(control_decision, current_state) -> (MantraControlState, ActuationReceipt)`
- `AdaptedStimulusRenderer` → `render(control_state, segment_plan) -> AdaptedStimulus`
- `InterventionOutcomeEvaluator` → `evaluate(expected, observed) -> InterventionOutcome`
- `Renderer` (legacy/TTS) → `render(StimulusRequest) -> RenderedStimulus`
- `ObservationProvider` (legacy) → `start/stop/poll` → `Observation`

## 6. TTS / Voice Contract

- `VoiceRenderProvider` is provider-agnostic.
- Local/offline rendering is required for low-latency closed-loop actuation.
- Remote TTS (SpeechGen) is allowed for high-quality asset generation but is **not** an architectural dependency of `DecisionEngine` or `MantraActuator`.

## 7. Raspberry Pi Bridge

- Represented as an optional `SensorGateway` implementing the same contract as simulated, direct-FC11, LSL, and replay gateways.
- The cognitive control system operates without a Raspberry Pi.

## 8. UI Strategy

- Web-first architecture.
- PyWebView may remain as an optional thin desktop container.
- The web app and PyWebView shell host the same UI and use the same API contracts.

## 9. Testing Strategy

- Unit tests for `clm/` estimation, decision, actuator, and safety boundaries.
- Property-based tests for event-store monotonicity and replay determinism.
- The non-negotiable CLM-01 test: a control decision changes mantra parameters and the next rendered stimulus uses those exact parameters.
- Integration tests with `SimulatedSensorGateway`, `MantraActuator`, and `MockRenderer`.

## 10. Versioning

- `ProtocolVersion` / `ProgramVersion` remain immutable and UUID-tagged.
- CLM event schemas versioned independently.
- API versioned via `/v1/` prefix (CLM-05).
