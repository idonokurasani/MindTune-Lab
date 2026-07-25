# MPE Phase 4C.2 — Gate 2 Pre-Extraction Analysis

## 1. Inspected repository state

- Repository root: `/Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console`
- Git HEAD at inspection: `8b131f818c9a196ab146d3bbe0ca9de5e99ea73e`
- Working tree: Gate 1 Recognition work present and uncommitted (untracked Recognition modules, modified `cli.py`, `cli_helpers.py`); unrelated pre-existing artifacts (`output/`, `mantra/`, `data/hebrew/`) left untouched.
- Test baseline before extraction: `Ran 132 tests … OK`; `ruff` clean; `mypy` clean (29 source files).

## 2. Implementation files inspected

Immediate Recall:

- `packages/mpe/src/mpe/protocol/immediate_recall.py` (596 lines at HEAD)
- `packages/mpe/src/mpe/protocol/fixture_minimal.py`
- `packages/mpe/src/mpe/protocol/providers.py`
- `packages/mpe/src/mpe/protocol/summary.py` (239 lines at HEAD)

Recognition (Gate 1, untracked):

- `packages/mpe/src/mpe/protocol/recognition.py` (≈600 lines pre-extraction)
- `packages/mpe/src/mpe/protocol/fixture_recognition.py`
- `packages/mpe/src/mpe/protocol/providers_recognition.py`
- `packages/mpe/src/mpe/protocol/summary_recognition.py`

Shared surfaces:

- `packages/mpe/src/mpe/runtime.py`, `events.py`, `validation.py`, `event_store.py`
- `packages/mpe/src/mpe/cli.py`, `cli_helpers.py`

## 3. Current event sequences (pre-extraction, unchanged by Gate 2)

Immediate Recall trial:

```
trial_created
instruction_started / instruction_completed        (present cue)
stimulus_requested / stimulus_ready                (prompt)
instruction_started / instruction_completed        (request self-confirmation)
response_window_opened
observation_received
captured_response_created
response_interpreted
domain_response_normalized
evaluation_completed
instruction_started / instruction_completed        (present target)
stimulus_requested / stimulus_ready                (confirmation)
feedback_started / feedback_completed
```

Recognition trial: identical skeleton, except one instruction for the prompt, N ordered
`stimulus_requested / stimulus_ready` pairs (`choice_0 … choice_{n-1}`), an integer observation
payload, and a feedback type that depends on `answer_status`.

Replay: `replay_session` reproduces live state for both protocols (existing tests).
CLI: `run-immediate-recall`, `show-protocol-summary`, `run-recognition`, `show-recognition-summary`
all produce text and JSON output; verified unchanged after extraction.

## 4. Duplication table

| # | Immediate Recall source | Recognition source | Similarity | Semantic difference | Decision |
|---|---|---|---|---|---|
| 1 | `_emit_block_started` / `_emit_block_completed` | same-named methods | identical | none | **Extract** (`TrialPipeline.emit_block_started/completed`) |
| 2 | `trial_created` payload assembly | same, plus `correct_choice_index`, `choice_count` | ~90% | two protocol-owned fields | **Extract with typed extension boundary** |
| 3 | `_emit_instruction` (started+completed pair) | identical method | identical | instruction text/target only | **Extract** (`InstructionSpec`) |
| 4 | `_emit_stimulus` (requested+ready pair) | identical method, called in a loop | identical | 1 stimulus vs N ordered stimuli | **Extract** (`StimulusSpec`, `emit_stimuli`) |
| 5 | `response_window_opened` emission | identical | identical | none | **Extract** (`ResponseWindowSpec`) |
| 6 | observation inject/poll + `observation_received` | identical except provider id and payload type | ~95% | payload `str` vs `int` | **Extract** (`ObservationSpec`, typed payload value) |
| 7 | captured → interpreted → normalized chain | identical | identical | captured payload string only | **Extract** (`run_response_pipeline`) |
| 8 | `evaluation_completed` emission | identical | identical | none | **Extract** (`emit_evaluation`) |
| 9 | `feedback_started` / `feedback_completed` | identical | feedback type is fixed vs status-dependent | ~95% | **Extract** (`FeedbackSpec`; type chosen by protocol) |
| 10 | bounded repeat while-loop + insert | identical loop | repeat condition differs (self-confirmation vs answer status) | ~85% | **Extract mechanics only** (`BoundedRepeatPlan`); decision stays protocol-specific (`RepeatDecision`) |
| 11 | summary event walk in `summary.py` | same walk in `summary_recognition.py` | ~80% | projection and result types differ | **Extract traversal only** (`walk_session`); projections stay separate |
| 12 | CLI run/show command bodies | same bodies | ~95% | runner/loader/formatter | **Extract mechanics** into two private helpers; commands stay explicit |
| 13 | correctness determination | `self_confirmation == "positive"` | `selected == correct_choice_index` | different semantics | **Keep protocol-specific** |
| 14 | fixtures, providers, evaluators | protocol-specific | protocol-specific | domain shape differs | **Keep protocol-specific** |
| 15 | summary result models | `ProtocolSummary` | `RecognitionSummary` | different fields | **Keep separate** (no merged optional-field model) |

## 5. Conclusion

Rows 1–12 constitute concrete, measured duplication of *mechanics*; rows 13–15 are semantics and must
remain protocol-owned. This justifies exactly one small typed shared layer
(`trial_pipeline.py`, `bounded_repeat.py`, `summary_walk.py`) reused by the two existing protocols —
no registry, no interpreter, no DSL, no protocol-ID dispatch.
