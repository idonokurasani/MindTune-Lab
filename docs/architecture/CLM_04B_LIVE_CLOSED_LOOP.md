# CLM-04B: Live Closed Loop with FC11 and Giuseppe/Aaron Audio

## Scope

CLM-04B closes the live sensor-to-audio loop by combining:

- `mindtune_clm.live` (CLM-04) for FC11 sensor gateway frames,
- `mindtune_clm.loop` (CLM-01) for state estimation, policy, and actuation,
- `mindtune_clm.voice` (CLM-03B) for Giuseppe/Aaron routing and cache identity,
- `mindtune_clm.audio` for rendering and scheduling,
- `mpe` for provenance events and causal graph reconstruction.

The orchestrator runs a deterministic, speaker-free fast loop in tests, and provides a `MacOSPlaybackBackend` for manual real-speaker smoke tests only.

## Package Layout

```
packages/clm/src/mindtune_clm/live_loop/
├── __init__.py
├── orchestrator.py       # LiveClosedLoopOrchestrator
├── state.py              # LiveClosedLoopState, LiveCycleState
├── safety.py             # SafetyController
├── latency.py            # LatencyTracker
├── outcomes.py           # InterventionOutcome
├── control.py            # LiveControlPipeline
├── playback_backend.py   # PlaybackBackend, DeterministicPlaybackBackend, MacOSPlaybackBackend
├── receipts.py           # LiveLoopCycleReceipt
├── health.py             # LiveClosedLoopHealth
├── events.py             # LiveClosedLoopEventType
└── fixture_clm04b.py     # synthetic FC11 + Giuseppe/Aaron cache fixtures
```

## Components

### `LiveClosedLoopOrchestrator`

- Owns the gateway, control pipeline, voice cache, renderer, scheduler, playback backend, safety controller, latency tracker, health, and MPE `Runtime`.
- `start()` creates an MPE session and emits `live_closed_loop_started`.
- `run_step(frame)` executes one cycle:
  1. emit observation event,
  2. estimate cognitive state,
  3. apply `SafetyController` and emit safety events,
  4. actuate,
  5. resolve the `VoiceCache` (no SpeechGen),
  6. render,
  7. schedule playback only at `between_mantra_cycles` safe boundaries,
  8. emit `live_closed_loop_intervention_outcome` and health update.
- `pause`, `resume`, `stop`, `kill` are explicit lifecycle controls.

### `SafetyController`

- `start`, `pause`, `resume`, `stop`, `kill`, `freeze_policy`, `unfreeze_policy`, `force_baseline`, `release_force_baseline`.
- Enforces:
  - max decisions/minute,
  - max switches/minute,
  - minimum dwell time between switches,
  - consecutive degraded and missing window limits,
  - max playback/cache failures,
  - max pending commands,
  - max frame-to-render and render-to-playback latencies.
- Violations emit reason codes and fall back to baseline; hard sensor-loss threshold can request stop.

### `DeterministicPlaybackBackend`

- Validates WAV containers and returns deterministic `PlaybackReceipt` objects.
- Supports injected `success=False`, `cancelled=True`, and `failure_reason`.
- No wall-clock; used in CI/tests.

### `MacOSPlaybackBackend`

- Manual-only backend that launches `afplay` with a list of arguments (`["afplay", "/path/to.wav"]`).
- `stop()` terminates the `afplay` process and removes the temporary WAV file.
- Not used in CI.

### `LatencyTracker`

- Tracks per-frame `frame_to_render_ms` and `render_to_playback_ms`.
- Configurable thresholds: 200 ms and 50 ms by default.
- Emits `live_closed_loop_latency_exceeded` when violated.

### `VoiceCache` integration

The orchestrator resolves the current mantra asset from a pre-populated `VoiceCache` using the same `cache_key` that `SpeechGenClient` would compute:

```python
cache_key = cache_key(route, tts_text, SynthesisParameters())
```

If the key is missing, `live_closed_loop_cache_miss` is emitted and the render continues using the fallback registry asset. The fast loop never calls SpeechGen, Pealim, the Hebrew inflector, HeLP, or the network.

## Event Provenance

CLM-04B reuses existing MPE event types where possible (`observation_frame_created`, `cognitive_state_estimated`, `control_decision_made`, `actuation_applied`, `adapted_stimulus_rendered`, `playback_completed`, etc.) and adds the following MPE-registered event strings in `packages/mpe/src/mpe/events.py`:

- `live_closed_loop_started`
- `live_closed_loop_completed`
- `live_closed_loop_paused`
- `live_closed_loop_resumed`
- `live_closed_loop_stopped`
- `live_closed_loop_killed`
- `live_closed_loop_observation_frame_consumed`
- `live_closed_loop_control_decision_made`
- `live_closed_loop_actuation_applied`
- `live_closed_loop_safety_envelope_violated`
- `live_closed_loop_baseline_fallback_activated`
- `live_closed_loop_baseline_fallback_released`
- `live_closed_loop_policy_frozen`
- `live_closed_loop_policy_unfrozen`
- `live_closed_loop_render_failed`
- `live_closed_loop_playback_failed`
- `live_closed_loop_cache_miss`
- `live_closed_loop_latency_exceeded`
- `live_closed_loop_health_changed`
- `live_closed_loop_intervention_outcome`

Each event provenance chain is set so the causal graph can be reconstructed independent of event ordering.

## Test Scenarios

`packages/clm/tests/test_clm04b.py` covers:

A. stable baseline  
B. deterioration and bounded intervention  
C. escalation  
D. recovery/withdrawal  
E. sensor disconnect  
F. missing cache asset  
G. render failure  
H. playback failure  
I. kill switch  

All tests use synthetic FC11 data, seeded Giuseppe/Aaron `VoiceCache` assets, and the deterministic playback backend. No real speaker is required.

## Smoke Script

`scripts/smoke_clm04b.py` (optional) can be run manually with a macOS speaker to exercise `MacOSPlaybackBackend`.

## Versions

- Orchestrator: `clm04b-orchestrator.v1`
- Safety policy: `clm04b-safety.v1`
- Deterministic playback backend: `deterministic.v1`
- macOS playback backend: `macos.afplay.v1`

## Latency Thresholds

- `max_frame_to_render_ms`: 200 ms
- `max_render_to_playback_ms`: 50 ms

## Policies

- **Cache-miss policy**: emit `live_closed_loop_cache_miss` and continue with the fallback `AudioAssetRegistry`.
- **Sensor-loss policy**: count consecutive missing windows; after `max_consecutive_missing` fall back to baseline, and after a hard threshold stop the loop.
- **Render-failure policy**: emit `live_closed_loop_render_failed`, mark outcome unsuccessful, and degrade health.
- **Playback-failure policy**: emit `live_closed_loop_playback_failed`, count failures, and degrade health.
