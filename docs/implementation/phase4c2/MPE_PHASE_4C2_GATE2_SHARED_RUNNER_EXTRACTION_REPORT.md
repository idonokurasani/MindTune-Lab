# MPE Phase 4C.2 — Gate 2 Shared Runner Extraction Report

## 1. Inspected repository state

- Root: `/Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console`
- Git HEAD: `8b131f818c9a196ab146d3bbe0ca9de5e99ea73e`
- Pre-extraction baseline: 132 tests OK, ruff clean, mypy clean (29 files).
- No commit, no push, no branch change.

## 2. Pre-extraction duplication map

See `MPE_PHASE_4C2_GATE2_PRE_EXTRACTION_ANALYSIS.md` (15-row duplication table).
Twelve duplicated mechanical blocks; three semantic areas explicitly kept protocol-specific.

## 3. Extraction boundary

Shared layer owns **invariant mechanics only**:

- block started/completed emission;
- `trial_created` canonical payload + repeat metadata;
- instruction started/completed pairs;
- stimulus requested/ready pairs, in input order;
- response window opening;
- observation poll and `observation_received`;
- captured → interpreted → normalized chain;
- `evaluation_completed` emission;
- `feedback_started`/`feedback_completed` pair;
- bounded repeat plan mechanics (count, cap, requeue, termination, adaptation-source propagation);
- generic event correlation for summaries;
- mechanically identical CLI store/format/parse/error handling.

Shared layer does **not** decide: stimulus meaning, choice count, correctness, self-confirmation
semantics, selected-vs-correct comparison, feedback type, summary projection, item scheduling,
or protocol selection.

## 4. Files added

- `packages/mpe/src/mpe/protocol/trial_pipeline.py` (542 lines)
- `packages/mpe/src/mpe/protocol/bounded_repeat.py` (97 lines)
- `packages/mpe/src/mpe/protocol/summary_walk.py` (143 lines)
- `packages/mpe/tests/test_shared_extraction.py` (30 tests)
- `docs/implementation/phase4c2/MPE_PHASE_4C2_GATE2_PRE_EXTRACTION_ANALYSIS.md`
- this report

## 5. Files modified

- `packages/mpe/src/mpe/protocol/immediate_recall.py` (596 → 327 lines)
- `packages/mpe/src/mpe/protocol/recognition.py` (≈600 → 324 lines)
- `packages/mpe/src/mpe/protocol/summary.py` (239 → 155 lines)
- `packages/mpe/src/mpe/protocol/summary_recognition.py` (walk reused; projection retained)
- `packages/mpe/src/mpe/cli.py` (two private helpers; four explicit commands retained)

## 6. Files intentionally unchanged

`runtime.py`, `events.py`, `validation.py`, `event_store.py`, `persistence/store.py`, `replay.py`,
`enums.py`, `types.py`, all fixtures and providers, `cli_helpers.py`, every existing test file,
`PROJECT_STATE.md`, `NEXT_TASK.md`, dependency manifests.

## 7. Shared orchestration API

```python
TrialPipeline(runtime, providers)
  .emit_block_started(block_id, block_type) / .emit_block_completed(block_id, count)
  .emit_trial_created(TrialIdentity, repeat: RepeatMetadata, response_requirement,
                      accepted_response_modes, extensions: PayloadExtension | None)
  .emit_instruction(trial_id, InstructionSpec)
  .emit_stimulus(trial_id, StimulusSpec) / .emit_stimuli(trial_id, [StimulusSpec])
  .open_response_window(trial_id, ResponseWindowSpec) -> ResponseWindowID
  .poll_observation(ObservationSpec) -> ObservationOutcome
  .emit_observation_received(trial_id, window_id, spec, observation, payload_value, received_at)
  .run_response_pipeline(...) -> normalized
  .emit_evaluation(trial_id, normalized, content_item, response_mode, protocol_version_id)
  .emit_feedback(trial_id, FeedbackSpec)

BoundedRepeatPlan(items, cap, key) -> iterator of BoundedRepeatStep
RepeatDecision(should_repeat, adaptation_source, reason_code)
RepeatMetadata(repeat_count, adaptation_source, cap)
walk_session(events) -> SessionWalk(items: list[TrialItemRecord])
```

All domain inputs are frozen typed dataclasses; there is no untyped dictionary domain API and no
protocol identifier anywhere in the signatures.

## 8. Protocol-specific responsibilities retained

- Immediate Recall: self-confirmation semantics, positive/negative mapping, fixed
  `CORRECT_ANSWER` feedback, prompt/confirmation stimulus roles, `ProtocolSummary` projection.
- Recognition: choice count, `choice_0…choice_n` roles, integer selection payload,
  selected-vs-`correct_choice_index` correctness, status-dependent feedback type,
  `correct_choice_index`/`choice_count` payload extensions, `RecognitionSummary` projection.
- Both: their own `_repeat_decision`, fixtures, providers, evaluators, CLI commands.

## 9. Bounded-repeat design

Mechanics (shared): plan order, requeue immediately after the executed item, per-item execution
count, `cap` enforcement (`repeats_used < cap`), termination guarantee, adaptation-source
propagation onto the next `trial_created`, repeat metadata (`repeat_count`, `adaptation_source`,
`cap`).

Decision (protocol): each runner returns `RepeatDecision`. Both currently implement
behavior-first, latency-second:

```python
if incorrect/negative:            RepeatDecision(True, "behavior", …)
elif latency > latency_bound:     RepeatDecision(True, "latency", …)
else:                             RepeatDecision.none()
```

Latency never affects correctness; it can only trigger a bounded repeat.

## 10. Payload-extension design

`emit_trial_created` accepts `extensions: Mapping[str, str | int | float | bool | None]`.
Canonical fields are explicit and frozen (`canonical_trial_fields()`); an extension that collides
with a canonical field raises `ValueError`. Extensions pass through the unchanged event schema and
validation path, so canonical required fields are still enforced (test:
`test_canonical_required_fields_are_still_validated`). No `metadata: dict[str, Any]` escape hatch
was introduced.

## 11. Summary extraction decision

Extracted: event correlation only (`walk_session` → `SessionWalk` / `TrialItemRecord`), i.e.
session start/completion, `trial_created`, `observation_received`, `evaluation_completed`,
`feedback_completed`, deterministic item ordering, and protocol extensions carried as
`trial_extensions`. Result types and projections remain two separate models; no merged
optional-field summary.

## 12. CLI extraction decision

Extracted only `_run_protocol_session(args, runner, formatter)` and
`_show_protocol_session_summary(args, loader, formatter)` — store opening, session-ID parsing,
output formatting, error mapping. The four commands remain explicitly registered and explicitly
implemented. No `run-protocol --protocol-id` and no dispatch table (test:
`test_cli_keeps_explicit_protocol_commands`).

## 13. Compatibility evidence

- All 132 pre-existing tests pass unmodified — no assertion was weakened, no expected sequence
  relaxed. This alone pins event order, payload fields, bounded-repeat behavior, summaries, replay
  equivalence and CLI output for both protocols.
- Added regression coverage: instruction/stimulus pair ordering, multi-stimulus input order,
  response-pipeline order, monotonic `session_sequence_number`, repeat counts
  `[(alpha,0),(beta,0),(beta,1)]`, extension survival, replay/summary derivation from events only,
  and cross-run normalized payload equality (IDs excluded as intentionally volatile).

## 14. Test results

```
PYTHONPATH=packages/mpe/src .venv/bin/python -m unittest discover -s packages/mpe/tests -p "test_*.py"
Ran 162 tests in 1.441s
OK
```

## 15. Ruff result

```
.venv/bin/ruff check packages/mpe/src packages/mpe/tests
All checks passed!
```

## 16. Mypy result

```
PYTHONPATH=packages/mpe/src .venv/bin/mypy packages/mpe/src
Success: no issues found in 32 source files
```

## 17. Duplication metrics

| Metric | Before | After |
|---|---|---|
| Duplicated mechanical blocks across the two runners | 12 | 0 |
| Duplicated runner lines (approx.) | ~470 | ~15 (protocol-specific decision methods) |
| Immediate Recall runner | 596 lines | 327 lines |
| Recognition runner | ≈600 lines | 324 lines |
| `summary.py` | 239 lines | 155 lines |
| Shared layer size | — | 782 lines (542 + 97 + 143) |
| Protocol-ID branches inside shared layer | — | 0 |
| New event types / schemas | — | 0 |
| New public protocol APIs | — | 0 (runner and session-function signatures unchanged) |
| Existing assertions changed | — | 0 |
| New `Any` occurrences in shared code | — | 12 annotations, all on provider-boundary dicts that already were `dict[str, Any]` in `providers.py`; zero new untyped *domain* models |
| New abstractions | — | 3 modules / 10 frozen dataclasses / 1 iterator |

## 18. Rejected abstractions

Explicitly not built: protocol registry; protocol-ID dispatch; generic primitive interpreter;
declarative rule engine; protocol DSL; unified `Protocol` base class with template method
`execute()`; merged summary model with optional fields; `run-protocol --protocol-id` CLI;
`metadata: dict[str, Any]` payload escape hatch; shared correctness/feedback policy; scheduler or
curriculum hooks.

## 19. Remaining duplication

- Each runner still has its own ~8-line `_repeat_decision`; the bodies are similar today but encode
  different semantics (self-confirmation vs selected choice) and must stay separate.
- Each runner builds its own `ContentItem` (4 differing fields).
- Two summary projections iterate `walk.items` similarly but produce different models.

All three are semantic, not mechanical; extracting them would move domain meaning into the core.

## 20. Recommendation for next gate

Evidence supports **stopping after two protocols**. The mechanical duplication that two protocols
proved is now removed by a small typed layer with zero protocol branching; the residual duplication
is semantic and must not be abstracted. A third protocol should be added only when a real product
requirement demands it — not to justify further abstraction.

Verdict: `GATE2_SHARED_RUNNER_EXTRACTION_COMPLETE`
