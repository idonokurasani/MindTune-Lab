# 22 — V2 Implementation Plan

## Architecture Principles (Revised)

- Develop incrementally in the current `mindtune_console` repository.
- Use a strangler architecture: preserve `packages/mpe/`; add new cognitive-control packages behind typed interfaces.
- No big-bang rewrite; progressively bypass `server.py` and `app.js` as replacement paths are tested.
- Web-first UI; PyWebView may remain as an optional thin desktop container.
- The cognitive control system must operate without a Raspberry Pi; the Pi bridge is an optional sensor gateway implementing the same provider contract as simulated sensors, direct FC11 adapters, LSL streams, and replay providers.
- Voice rendering is provider-agnostic; remote TTS may generate high-quality assets, but no remote TTS is an architectural dependency of the Decision Engine or Mantra Actuator.
- Do not merge `mindtune-learning-framework` into MPE during CLM-01; keep typed boundaries between learning objectives, domain actions, control decisions, and protocol execution.

## CLM-01 — Closed-Loop Mantra Control Kernel

Goal: prove the causal chain

```
ObservationFrame
→ CognitiveStateEstimate
→ ControlDecision (apply / maintain / withdraw / abstain / stop)
→ MantraControlState
→ ActuationReceipt
→ AdaptedStimulus
→ InterventionOutcome
```

Deliverables:

1. **Domain-neutral observation frames** (`ObservationFrame` dataclass/Pydantic model) carrying multimodal evidence and quality flags.
2. **Multimodal evidence quality handling** — artifact/bad-signal gating, confidence, and uncertainty propagation.
3. **Cognitive state estimates with uncertainty** — estimate + confidence interval; not a hard state transition.
4. **Explicit control decisions** — `apply`, `maintain`, `withdraw`, `abstain`, `stop`.
5. **Parameterized `MantraControlState`** — rate, pause duration, segment selection, playback mode, and any other actuator-safe parameter.
6. **Deterministic in-memory actuator** — applies `MantraControlState` to a `MantraSegment` timeline and returns `ActuationReceipt`.
7. **Safe application boundaries** — no decision can produce an unsafe parameter value (clamping, rate limits, emergency stop).
8. **Actuation receipts** — immutable record of what was actuated, with provenance and timestamp.
9. **Adapted-stimulus records** — record of the rendered/selected stimulus parameters.
10. **Outcome evaluation** — compare expected vs. observed outcome after the adapted stimulus.
11. **Event provenance** — every step emits an event with causal `provenance`.
12. **Hysteresis and gradual assistance withdrawal** — avoid oscillation; withdraw assistance gradually.

**Not required for CLM-01:** real EEG, TTS, FastAPI, PostgreSQL, or full UI.

### Non-Negotiable Acceptance Test for CLM-01

An automated test must prove:

```
control decision at cycle N
→ successful actuation receipt
→ changed mantra control parameters
→ next rendered stimulus uses those exact applied parameters
```

Without this proof, the implementation is not yet MindTune Lab V2.

## CLM-02 — Sensor Replay

- Integrate recorded FC11 evidence through deterministic replay.
- Add quality gating so artifact windows are ignored by the Decision Engine.
- Validate that replay produces the same control decisions as the original recorded session.

## CLM-03 — Audio Actuation

- Implement the first controllable mantra renderer (local/offline-capable).
- The renderer consumes `MantraControlState` and produces an `AdaptedStimulus`.
- SpeechGen may be used for high-quality asset generation, but the Decision Engine and Actuator do not depend on it.

## CLM-04 — Live Experimental Loop

- Connect live sensor acquisition to the Decision Engine and Mantra Actuator.
- Operate under explicit safety constraints (clamped parameters, human stop, degraded-mode fallback).
- Use the FC11 progression: simulated → recorded replay → validated native-buffer/LSL → live deployment.

## CLM-05 — API and Web Interface

- Add FastAPI and a minimal web interface **only after** the control kernel and actuator path have been proven.
- The web app and any PyWebView shell must host the same UI and use the same API contracts.

## First Executable Vertical Slice (Revised)

The first vertical slice is **CLM-01**: a single control cycle that proves the causal chain.

Scenario:

1. A simulated `ObservationFrame` carries a high-load indicator and good quality.
2. `DecisionEngine` produces `ControlDecision.APPLY` with a `MantraControlState` (e.g., slower rate, longer pause, different segment selection).
3. `MantraActuator` applies the control state to a fixture `MantraSegment` timeline and returns an `ActuationReceipt`.
4. `AdaptedStimulusRenderer` produces the next stimulus using the exact applied parameters.
5. `OutcomeEvaluator` records the result.
6. Every step is an event in the append-only `EventStore`.
7. `Replay` reproduces the same `MantraControlState` and stimulus parameters from the events.

### Acceptance Criteria

1. `ObservationFrame` → `CognitiveStateEstimate` with uncertainty.
2. `CognitiveStateEstimate` → `ControlDecision` (one of `apply`, `maintain`, `withdraw`, `abstain`, `stop`).
3. `ControlDecision` → `MantraControlState` with changed parameters.
4. `MantraControlState` → `ActuationReceipt` from the deterministic actuator.
5. `ActuationReceipt` → `AdaptedStimulus` whose parameters match the applied control state.
6. All of the above are events with `provenance` in `EventStore`.
7. `Replay` of the event stream reproduces the same `MantraControlState` and adapted stimulus.
8. Artifact-quality `ObservationFrame` leads to `ControlDecision.ABSTAIN` or `MAINTAIN`, not `APPLY`.
9. Unsafe control parameters are clamped or rejected by the actuator safety boundary.

## Milestones

| Milestone | Acceptance Criteria |
|---|---|
| CLM-01 | Control-kernel test passes: a decision changes mantra parameters and the next rendered stimulus uses those exact parameters |
| CLM-02 | Replay of recorded FC11 evidence reproduces CLM-01 decisions |
| CLM-03 | Local/offline mantra renderer produces adapted audio from `MantraControlState` |
| CLM-04 | Live sensor data drives the control kernel under safety constraints |
| CLM-05 | FastAPI + web UI expose the same proven session/replay API and control the kernel |
