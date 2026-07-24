# MPE v1.1 Runtime State Machine Specification

## Scope

This document defines the runtime state machines for the MindTune Protocol Engine v1.1. It is derived from:

- `MPE_EVENT_MODEL_V1_1.md`
- `MPE_OBJECT_MODEL_V1_1.md`
- `MPE_CANONICAL_ENUM_REGISTRY.md`
- `MPE_OBJECT_EVENT_COVERAGE_MATRIX.csv`
- `MPE_RISK_REGISTER_V1_1.md`

All states, transitions, generated events, and failure handling are limited to what is specified in the architecture. No new states or transitions are introduced.

## Legend

| Tag | Meaning |
|---|---|
| **Normative** | Required by MPE v1.1. |
| **Recommended** | Strongly advised for correctness, performance, or auditability. |
| **Optional** | May be omitted in a minimal implementation. |
| **Out of scope** | Not part of Phase 4A. |
| **Implementation note** | Engineering guidance, not an architectural rule. |

## 1. Session lifecycle

### 1.1 Session states

```text
created
  |
  v
started <----> paused
  |              |
  |              v
  |           resumed
  |
  +--(cancel)--> cancelled
  |
  +--(complete)--> completed
  |
  +--(terminate)--> terminated
```

### 1.2 `created` -> `started`

- **Entry condition:** `Session` object instantiated; learner confirmed start; `ProgramVersion` and `ProtocolVersion` validated.
- **Generated events:**
  1. `session_created` (if not already emitted)
  2. `session_started`
- **Exit condition:** `session_started` appended; runtime clock begins.
- **Failure handling:** If `ProgramVersion`/`ProtocolVersion` checksum or dependency mismatch, append `session_cancelled` or `protocol_terminated` with reason `provider_failure`.

### 1.3 `started` -> `paused`

- **Entry condition:** User action, safety rule, or device error triggers pause.
- **Generated event:** `session_paused`
- **Exit condition:** Runtime stops active session clock; records `active_session_time_at_pause`.
- **Failure handling:** If pause fails to persist, append `session_paused` with reason `device_error`; runtime enters degraded mode.

### 1.4 `paused` -> `resumed`

- **Entry condition:** Pause condition cleared and user/runtime confirms resume.
- **Generated event:** `session_resumed`
- **Exit condition:** Runtime clock resumes from `active_session_time_at_resume`; scheduled events are not shifted.
- **Failure handling:** If resume fails, append `session_resumed` with `active_session_time_at_resume` unchanged; safety monitor may terminate.

### 1.5 `started` -> `completed`

- **Entry condition:** Protocol graph reaches terminal state; no safety rule active.
- **Generated event:** `session_completed`
- **Exit condition:** Terminal event appended; `Outcome` may be computed.
- **Failure handling:** If completion validation fails (unexpected active trials), append `protocol_terminated` with reason `unrecoverable_error`.

### 1.6 `started` or `paused` -> `cancelled`

- **Entry condition:** User explicitly cancels before normal completion.
- **Generated event:** `session_cancelled` (reason `user` or `device_error`)
- **Exit condition:** Terminal event appended.
- **Failure handling:** If cancellation races with safety termination, safety wins; append `protocol_terminated` instead or after.

### 1.7 `started` or `paused` -> `terminated`

- **Entry condition:** Safety rule, user emergency stop, unrecoverable error, or provider failure.
- **Generated event:** `protocol_terminated` (reason `safety`, `user_emergency`, `unrecoverable_error`, `provider_failure`)
- **Exit condition:** Terminal safety event appended; all active flow stops.
- **Failure handling:** Termination is the failure handler of last resort. If termination fails, runtime exits as safely as possible and logs to a diagnostic channel outside the event store.

## 2. Block lifecycle

### 2.1 Block states

```text
not_started
  |
  v
in_progress
  |
  v
completed
```

### 2.2 `not_started` -> `in_progress`

- **Entry condition:** Scheduler selects a block from `ProtocolVersion.block_sequence`; previous block completed or this is the first block.
- **Generated event:** `block_started`
- **Exit condition:** `block_started` appended.
- **Failure handling:** If block definition is missing or invalid, append `protocol_terminated` with reason `unrecoverable_error`.

### 2.3 `in_progress` -> `completed`

- **Entry condition:** Block exit condition satisfied (e.g., `N_TRIALS_COMPLETED`) or safety recovery inserted.
- **Generated event:** `block_completed`
- **Exit condition:** `block_completed` appended.
- **Failure handling:** If exit condition is never satisfiable, scheduler may append `protocol_terminated` or `session_cancelled` depending on cause.

## 3. Trial lifecycle

### 3.1 Trial states

```text
planned
  |
  v
started
  |
  +--(instruction/stimulus flow)--> awaiting_response
  |
  +--(timeout)--> timeout
  |
  +--(evaluation complete)--> evaluated
  |
  +--(safety)--> aborted
```

### 3.2 `planned` -> `started`

- **Entry condition:** Scheduler produces `ScheduleDecision` with `decision_type == next_trial` and selects `content_item_ids`.
- **Generated event:** `trial_created`
- **Exit condition:** `trial_created` appended; trial plan is immutable.
- **Failure handling:** If `content_item_ids` are invalid or provider unreachable, append `trial_created` with `response_requirement: none` or abort trial.

### 3.3 `started` -> `awaiting_response`

- **Entry condition:** Instruction/stimulus flow completes and `response_window_opened` is emitted.
- **Generated event:** `response_window_opened`
- **Exit condition:** `ResponseWindow` is active; observation providers are listening.
- **Failure handling:** If no response mode is supported, append `response_timeout` and proceed to scheduling.

### 3.4 `awaiting_response` -> `timeout`

- **Entry condition:** Response window deadline reached without finalized response.
- **Generated event:** `response_timeout`
- **Exit condition:** `response_timeout` appended.
- **Failure handling:** Timeout is normal; scheduler decides next action. Repeated timeouts may trigger adaptation or safety rule in later phases.

### 3.5 `awaiting_response` -> `evaluated`

- **Entry condition:** `Observation` received, `CapturedResponse` created, `ResponseInterpretation` produced, `DomainNormalizedResponse` produced, and `Evaluator` returns `Evaluation`.
- **Generated events:** `captured_response_created`, `response_interpreted`, `domain_response_normalized`, `evaluation_completed`/`evaluation_abstained`/`evaluation_failed`
- **Exit condition:** `Evaluation` appended.
- **Failure handling:**
  - If interpreter fails: append `response_interpreted` with `interpretation_confidence == 0` and `evaluation_abstained`/`evaluation_failed`.
  - If normalizer fails: append `domain_response_normalized` with `uncertainty` high and `evaluation_abstained`/`evaluation_failed`.
  - If evaluator fails: append `evaluation_failed` and continue.

### 3.6 `evaluated` -> completed

- **Entry condition:** `FeedbackEvent` delivered (if any) and `ScheduleDecision` emitted.
- **Generated events:** `feedback_started`, `feedback_completed`, `schedule_decision`
- **Exit condition:** `schedule_decision` appended.
- **Failure handling:** If feedback cannot be rendered, append `feedback_started` with `rendered_media_id` null and continue.

### 3.7 Any trial state -> `aborted`

- **Entry condition:** Safety rule triggered during trial.
- **Generated events:** `safety_rule_triggered` (or `protocol_terminated`)
- **Exit condition:** Safety action completes; trial does not proceed to evaluation.
- **Failure handling:** Safety overrides all flow.

## 4. Response lifecycle

The response lifecycle is a nested state machine within a trial.

### 4.1 Response states

```text
window_closed
  |
  v
listening
  |
  +--(button/typed)--> captured
  |
  +--(voice sample complete)--> captured
  |
  +--(deadline)--> timeout
```

### 4.2 `window_closed` -> `listening`

- **Entry condition:** `response_window_opened` emitted.
- **Generated event:** `response_window_opened`
- **Exit condition:** Observation provider(s) begin listening.

### 4.3 `listening` -> `captured`

- **Entry condition:** Provider reports response onset and completion.
- **Generated events:** `response_detected`, `response_completed`, `observation_received`, `captured_response_created`
- **Exit condition:** `captured_response_created` appended.
- **Failure handling:** If response is incomplete, append `response_detected` without `response_completed`; on timeout append `response_timeout`.

### 4.4 `captured` -> `interpreted`

- **Entry condition:** `ResponseInterpreter` processes `CapturedResponse`.
- **Generated event:** `response_interpreted`
- **Exit condition:** `response_interpreted` appended.
- **Failure handling:** If interpretation fails, append `response_interpreted` with `interpretation_type` and low confidence; continue to `evaluation_abstained`/`evaluation_failed`.

### 4.5 `interpreted` -> `normalized`

- **Entry condition:** `DomainNormalizer` processes `ResponseInterpretation`.
- **Generated event:** `domain_response_normalized`
- **Exit condition:** `domain_response_normalized` appended.
- **Failure handling:** If normalization fails, append `domain_response_normalized` with high `uncertainty`; continue to `evaluation_abstained`/`evaluation_failed`.

### 4.6 `normalized` -> `evaluated`

- **Entry condition:** `Evaluator` compares `DomainNormalizedResponse` to expected answer.
- **Generated event:** `evaluation_completed`, `evaluation_abstained`, or `evaluation_failed`
- **Exit condition:** Evaluation event appended.
- **Failure handling:** If evaluator fails, `evaluation_failed` is the failure event.

### 4.7 `listening` -> `timeout`

- **Entry condition:** Response window deadline reached.
- **Generated event:** `response_timeout`
- **Exit condition:** No `CapturedResponse` created; scheduler decides next trial.

## 5. Adaptation lifecycle

- **Phase applicability:** Phase 5A+. No adaptation in Phase 4.
- **Source:** `MPE_ADAPTATION_CONTRACT.md`; `MPE_EVENT_MODEL_V1_1.md` `adaptation_*`.

### 5.1 Adaptation states

```text
candidate
  |
  +--(insufficient evidence)--> abstained
  |
  +--(proposed)--> proposed
        |
        +--(applied)--> applied
        |     |
        |     +--(rollback)--> reversed
        |
        +--(not applied)--> no_change
```

### 5.2 `candidate` -> `proposed`

- **Entry condition:** Policy has enough evidence, uncertainty below threshold, cooldown satisfied, step within bounds.
- **Generated event:** `adaptation_proposed`
- **Exit condition:** `AdaptationDecision` appended.

### 5.3 `proposed` -> `applied`

- **Entry condition:** `decision == APPLY`, `deployment_status` not `exploratory_only` or `shadow_mode`, safety rules allow.
- **Generated event:** `adaptation_applied`
- **Exit condition:** `applied_at` set; runtime parameter updated.
- **Failure handling:** If apply violates bounds, append `adaptation_reversed` immediately.

### 5.4 `applied` -> `reversed`

- **Entry condition:** Rollback rule fires, safety rule triggers, or user override.
- **Generated event:** `adaptation_reversed`
- **Exit condition:** `reversed_at` set; parameter restored.

### 5.5 `candidate` -> `abstained`

- **Entry condition:** Evidence or uncertainty threshold not met; policy deliberately abstains.
- **Generated event:** `adaptation_abstained`
- **Exit condition:** `AdaptationDecision` appended.

## 6. Safety lifecycle

### 6.1 Safety states

```text
idle
  |
  +--(rule triggered)--> active
        |
        +--(pause)--> paused
        |
        +--(recovery)--> recovery
        |
        +--(terminate)--> terminated
```

### 6.2 `idle` -> `active`

- **Entry condition:** Observation or state matches a safety rule condition.
- **Generated event:** `safety_rule_triggered`
- **Exit condition:** Severity and action determined; all active flow paused.

### 6.3 `active` -> `paused`

- **Entry condition:** `action_taken == pause` or `volume_limit`.
- **Generated events:** `safety_instruction_started`, `session_paused` (if pause)
- **Exit condition:** Safety action executed.
- **Failure handling:** If pause cannot be applied, escalate to `protocol_terminated`.

### 6.4 `active` -> `recovery`

- **Entry condition:** `action_taken == insert_recovery`.
- **Generated event:** `recovery_inserted`
- **Exit condition:** Recovery trial/block inserted.

### 6.5 `active` -> `terminated`

- **Entry condition:** `action_taken == terminate` or unrecoverable failure.
- **Generated event:** `protocol_terminated`
- **Exit condition:** Session terminated; no further events appended except terminal diagnostics.

## 7. Failure handling summary

| Failure point | Recovery event | Escalation |
|---|---|---|
| Invalid `ProgramVersion`/`ProtocolVersion` | `session_cancelled` or `protocol_terminated` | Cannot start session. |
| Missing block definition | `protocol_terminated` | Cannot recover mid-session. |
| Unsupported response mode | `response_timeout` | Trial ends without response. |
| Response capture incomplete | `response_timeout` | Trial ends without response. |
| Interpreter failure | `response_interpreted` (low confidence) + `evaluation_abstained`/`evaluation_failed` | Continue. |
| Normalizer failure | `domain_response_normalized` (high uncertainty) + `evaluation_abstained`/`evaluation_failed` | Continue. |
| Evaluator failure | `evaluation_failed` | Continue with neutral scheduling. |
| Renderer failure | `stimulus_ready`/`feedback_started` with fallback | Continue with degraded media. |
| Provider version mismatch | `protocol_terminated` or `evaluation_failed` | Stop or abort trial. |
| Safety rule trigger | `safety_rule_triggered` | Pause/recover/terminate. |
| Pause/resume failure | `session_paused`/`session_resumed` with error reason | Safety monitor may terminate. |

## 8. State machine composition rules

- **Normative:** Safety transitions override all other transitions at any level.
- **Normative:** Session-level transitions (`paused`, `cancelled`, `terminated`) interrupt trial/response lifecycles.
- **Normative:** Trial lifecycle events are nested within a `session_id`; their ordering is defined by `session_sequence_number`.
- **Recommended:** State machine implementation should be a single scheduler loop that processes one event at a time in canonical order.
- **Implementation note:** Concurrent providers may produce events; the runtime serializes final append and state updates.

## 9. Phase 4A scope note

This specification is complete for Phase 4A. It does not define:

- Implementation language or state machine framework.
- Threading model.
- Provider adapter code.
- Specific safety rule conditions.

These are implementation decisions reserved for Phase 4B.
