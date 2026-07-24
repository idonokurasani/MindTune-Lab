# Protocol Primitives Catalog v1

## Allowed primitives

| Primitive | Category | Meaning | Allowed in Phase 4 | Allowed in Phase 5A |
|---|---|---|---|---|
| `PRESENT_STIMULUS` | instruction | Play an auditory or other stimulus. | Yes | Yes |
| `INSTRUCT_COVERT_RETRIEVAL` | instruction | Instruct the learner to retrieve an answer internally. | Yes | Yes |
| `INSTRUCT_COVERT_REHEARSAL` | instruction | Instruct the learner to rehearse mentally. | Yes | Yes |
| `INSTRUCT_IMAGERY` | instruction | Instruct the learner to use mental imagery. | Yes | Yes |
| `REQUEST_OVERT_RESPONSE` | instruction | Instruct the learner to respond via button, voice, typing, or selection. | Yes | Yes |
| `REQUEST_CONFIDENCE_RATING` | instruction | Instruct the learner to report confidence. | Yes | Yes |
| `REQUEST_SELF_REPORT` | instruction | Instruct the learner to report fatigue, difficulty, etc. | Yes | Yes |
| `OPEN_RESPONSE_WINDOW` | runtime | Start the interval for observable response collection. | Yes | Yes |
| `CLOSE_RESPONSE_WINDOW` | runtime | End the response window. | Yes | Yes |
| `WAIT_DURATION` | runtime | Wait a fixed or configured duration. | Yes | Yes |
| `WAIT_FOR_RESPONSE` | runtime | Wait until response window closes or response is finalized. | Yes | Yes |
| `WAIT_FOR_SIGNAL_QUALITY` | runtime | Wait for an observation provider to report acceptable signal quality before proceeding (e.g., microphone check). | Yes | Yes |
| `CHECK_CONTINUATION_CONDITION` | runtime | Evaluate an observable condition (e.g., N trials completed) to decide continuation. | Yes | Yes |
| `INSERT_RECOVERY` | runtime | Insert a recovery trial or block based on an observable rule. | Yes | Yes |
| `OFFER_SESSION_END` | runtime | Offer the learner the option to end the session. | Yes | Yes |
| `DELIVER_KNOWLEDGE_FEEDBACK` | feedback | Provide the correct answer or elaboration. | Yes | Yes |
| `DELIVER_PERFORMANCE_FEEDBACK` | feedback | Indicate correctness or error category. | Yes | Yes |
| `DELIVER_METACOGNITIVE_PROMPT` | feedback | Prompt confidence or strategy reflection. | Yes | Yes |
| `DELIVER_SAFETY_INSTRUCTION` | safety | Deliver a safety command. | Yes | Yes |
| `SELECT_NEXT_ITEM` | scheduling | Schedule the next item/trial/block. | Yes (fixed) | Yes (adaptive) |
| `NO_CHANGE_INSUFFICIENT_EVIDENCE` | adaptation | Explicitly abstain from adaptation. | No | Yes |

## Prohibited primitives

| Primitive | Why prohibited | Replacement |
|---|---|---|
| `expect(mental_*)` | Implies the system can observe a mental answer. | `INSTRUCT_COVERT_RETRIEVAL` + optional later `REQUEST_OVERT_RESPONSE`. |
| `wait_for_state(target, timeout)` | Blocks on an inferred cognitive state. | `WAIT_DURATION`, `WAIT_FOR_RESPONSE`, `CHECK_CONTINUATION_CONDITION`, `INSERT_RECOVERY`, `OFFER_SESSION_END`. |
| `increase_difficulty()` / `decrease_difficulty()` | Generic scalar difficulty is underspecified. | Typed dimension-specific adaptation decisions (e.g., `change_response_deadline`, `change_new_item_rate`). |
| `adapt(param, policy)` without contract | Missing provenance, bounds, rollback, abstention. | Full `AdaptationDecision` with contractual fields. |
| Any primitive using EEG semantics | MPE core must not know what an EEG feature means. | Generic `SensorObservation` consumed by versioned `StateInferenceModel` outside core. |

## Trial role sequence examples

### Language Prediction-Retrieval Loop

```text
PRESENT_STIMULUS (cue)
INSTRUCT_COVERT_RETRIEVAL
WAIT_DURATION
PRESENT_STIMULUS (correct answer)
DELIVER_KNOWLEDGE_FEEDBACK
```

The system never observes the covert retrieval directly. A later trial may add `REQUEST_OVERT_RESPONSE` for an observable probe.

### Perceptual Discrimination

```text
PRESENT_STIMULUS (A)
PRESENT_STIMULUS (B)
REQUEST_OVERT_RESPONSE (same/different)
DELIVER_PERFORMANCE_FEEDBACK
```

### Overt Recall

```text
PRESENT_STIMULUS (cue)
REQUEST_OVERT_RESPONSE
OPEN_RESPONSE_WINDOW
WAIT_FOR_RESPONSE
CLOSE_RESPONSE_WINDOW
DELIVER_KNOWLEDGE_FEEDBACK
```

### Morphology Generation

```text
PRESENT_STIMULUS (root + person/gender/number cue)
REQUEST_OVERT_RESPONSE (produce inflected form)
DELIVER_PERFORMANCE_FEEDBACK + DELIVER_KNOWLEDGE_FEEDBACK
```

### Sequence / Working Memory

```text
PRESENT_STIMULUS (sequence item 1)
PRESENT_STIMULUS (sequence item 2)
...
REQUEST_OVERT_RESPONSE (recall sequence)
DELIVER_PERFORMANCE_FEEDBACK
```

### Exposure / Encoding Only

```text
PRESENT_STIMULUS
WAIT_DURATION
# No response window.
```

### Delayed Probe

```text
# Encoding phase earlier in session
PRESENT_STIMULUS
WAIT_DURATION

# Later probe trial
PRESENT_STIMULUS (cue)
REQUEST_OVERT_RESPONSE
DELIVER_KNOWLEDGE_FEEDBACK
```

## Response requirement values

- `required` — an observable response is expected; omission is a timeout.
- `optional` — a response may be collected but timeout is not an error.
- `none` — no response is expected; trial is exposure/encoding/feedback only.
