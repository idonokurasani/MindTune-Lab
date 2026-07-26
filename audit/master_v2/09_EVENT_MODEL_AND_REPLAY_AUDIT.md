# 09 — Event Model and Replay Audit

## 1. Event Envelope

`mpe/events.py` defines `Event` as a frozen dataclass with:

- `event_id`, `event_type`, `schema_version`
- `session_id`, `session_sequence_number` (strictly monotonic)
- `protocol_version_id`
- `timestamp` (runtime monotonic), `wallclock_at` (optional)
- `component`, `component_version`
- `correlation_id`, `provenance` (causal predecessors)
- `payload` (read-only `MappingProxyType`)
- `sensitive`, `data_classification`, `quality_flags`
- `trial_id`, `block_id`

## 2. Supported Event Types

27 canonical event types in `events.py:31-59`:

`session_created`, `session_started`, `session_completed`, `session_cancelled`, `block_started`, `block_completed`, `trial_created`, `instruction_started`, `instruction_completed`, `stimulus_requested`, `stimulus_ready`, `response_window_opened`, `response_timeout`, `observation_received`, `captured_response_created`, `response_interpreted`, `domain_response_normalized`, `evaluation_completed`, `evaluation_abstained`, `evaluation_failed`, `feedback_started`, `feedback_completed`, `schedule_decision`, `adaptation_decision`, `protocol_terminated`.

## 3. Append Rules

`mpe/event_store.py`:

- Only `Event` instances can be appended.
- `event_type` must be in `SUPPORTED_EVENT_TYPES`.
- `validate_event(event)` is called.
- `expected_version` must equal current stream length (optimistic concurrency).
- `session_sequence_number` must be strictly increasing.
- `timestamp` must be non-decreasing.
- All `provenance` event IDs must already exist in the session.

## 4. Replay

`mpe/replay.py`:

```python
class Replay:
    def replay(self, session_id: SessionID) -> RuntimeState:
        events = self.store.read(session_id)
        state = RuntimeState()
        for event in events:
            state.apply(event)
        return state
```

`RuntimeState.apply()` dispatches to `_EVENT_HANDLERS` (`aggregates.py`). This makes replay deterministic given the same event stream and initial state.

## 5. Conformance to Spec

`docs/specification/v1.1/EVENT_STORE_SPEC.md`:

- Append-only: yes.
- Monotonic `session_sequence_number`: yes.
- Monotonic `timestamp`: yes.
- Provenance validation: yes.
- Optimistic concurrency: yes.
- Causal ordering: yes (provenance events must precede).

## 6. Disposition

**KEEP** — event model and replay are production-ready and should form the V2 core.
