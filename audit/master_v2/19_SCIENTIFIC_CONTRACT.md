# 19 — Scientific Contract

## 1. Behavior-Primary Principle

Behavior is the primary evidence for cognitive-state estimation. Sensor data (EEG, HRV, etc.) is contextual.

Evidence:

- `mpe/protocol/cognitive_state.py:65-72` — if `behavioral_load == 0.0`, EEG is ignored.
- `mpe/protocol/cognitive_state.py:71` — `combined_load = max(behavioral_load, eeg_load)` only when behavioral load is non-zero.

## 2. Adaptation Must Change Execution

An adaptation must change an actual next runtime parameter, not only metadata.

Evidence:

- `mpe/protocol/immediate_recall.py:420-434` — `AdaptationPolicy.decide()` returns a new `response_deadline` that is used in `ResponseWindowSpec` of the next trial.

## 3. Every Session Auditable

All trial-level, response-level, and adaptation-level decisions are events in the append-only `EventStore` with provenance.

Evidence:

- `mpe/event_store.py` — append-only, optimistic concurrency, provenance validation.
- `mpe/events.py` — 27 canonical event types including `adaptation_decision`.

## 4. Deterministic Replay

A session can be reconstructed from its event stream given the same `ProtocolVersion` and random seed.

Evidence:

- `mpe/replay.py` — replays events into `RuntimeState`.
- `mpe/aggregates.py` — event handlers rebuild state.
- `mpe/runtime.py` — `Clock` and `random_seed` are deterministic.

## 5. Domain Adapters Are Not Core Architecture

Hebrew, piano, or any content domain must reach the runtime only through adapters.

Evidence:

- `packages/mpe/src/mpe/domains/hebrew/adapter.py` — Hebrew-specific logic isolated.
- `HELP_INTEGRATION.md:51-54` — HeLP evidence never leaks into generic runtime; only `BehavioralEvidence` crosses.

## 6. Conclusion

The `packages/mpe/` implementation satisfies the scientific contract at the library level. V2 must preserve and productionize it, with explicit empirical validation of cognitive-state thresholds and adaptation effects.
