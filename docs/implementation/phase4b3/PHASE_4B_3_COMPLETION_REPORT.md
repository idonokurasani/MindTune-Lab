# Phase 4B.3 Completion Report

**Date:** 2026-07-24  
**Recommendation:** `APPROVE_PHASE_4B_3_CLOSURE`

## 1. Scope Implemented

Phase 4B.3 adds a minimal, `argparse`-based CLI over the Phase 4B.1 MPE runtime and the Phase 4B.2 SQLite persistence layer. The implemented scope matches the approved `docs/specification/v1.1/PHASE_4B_3_SCOPE_PROPOSAL.md`.

### New commands

- `mpe run-mock-session` — execute and persist the reference mock session.
- `mpe replay <session-id>` — replay a persisted session and print terminal state.
- `mpe list-sessions` — list sessions in a store.
- `mpe validate-store` — validate the structural integrity of the persisted event log.

### New source files

- `packages/mpe/src/mpe/cli.py`
- `packages/mpe/src/mpe/cli_helpers.py`
- `packages/mpe/src/mpe/__main__.py`
- `packages/mpe/tests/test_cli.py`

### Modified source/config files

- `packages/mpe/src/mpe/event_store.py` — added `SessionSummary` and `EventStore.list_sessions()`.
- `packages/mpe/src/mpe/persistence/store.py` — implemented `SQLiteEventStore.list_sessions()`.
- `packages/mpe/tests/test_event_store.py` — added `test_list_sessions` contract test.
- `packages/mpe/pyproject.toml` — added `[project.scripts]` `mpe = "mpe.cli:main"`.
- `requirements.txt` — removed unused `click==8.4.2` entry.

## 2. Test Results

### Authoritative discovery command

```bash
python -m unittest discover -s packages/mpe/tests -p 'test_*.py' -v
```

**Result:** `Ran 89 tests in 0.808s — OK`

- Phase 4B.1 baseline: 42 tests, all pass.
- Phase 4B.2 persistence tests: 17 tests, all pass.
- Phase 4B.2 shared event-store contract tests: 9 original + 1 new (`test_list_sessions`) = 10, run for both `InMemoryEventStore` and `SQLiteEventStore`.
- Phase 4B.3 CLI tests: 19 tests, all pass.

### Static analysis

- `ruff check packages/mpe/src packages/mpe/tests` → All checks passed!
- `mypy packages/mpe/src/mpe` → Success: no issues found in 20 source files

## 3. Docker Verification

- `docker build -t mpe:phase4b3 .` → success.
- `docker run --rm mpe:phase4b3 mpe --help` → exit `0`.
- `docker run --rm mpe:phase4b3 python -m mpe --help` → exit `0`.
- Two-container CLI demo on a named volume succeeded:
  - Container 1: `mpe run-mock-session --format json` persisted 22 events.
  - Container 2: `mpe list-sessions --format json`, `mpe replay <session-id> --format json`, and `mpe validate-store --format json` all returned expected JSON.
- `docker compose -f compose/testing.yaml up --build` → success (89 tests pass and `mpe.demo` completes).

## 4. Contract Verification

### Exit-code matrix

| Code | Verified by |
|---|---|
| `0` | All success-path tests |
| `1` | `test_unexpected_error_maps_to_exit_one` |
| `2` | `test_invalid_session_id_exits_usage`, `test_directory_path_exits_usage` |
| `3` | `test_replay_missing_session_fails`, `test_read_only_commands_do_not_create_store` |
| `4` | `test_validate_store_fails_on_corrupt_row` |
| `5` | `test_concurrency_error_maps_to_exit_five` |
| `6` | `test_provider_failure_maps_to_exit_six` |

### Stdout/stderr contract

- `test_verbose_writes_to_stderr_not_stdout` confirms diagnostic output is on stderr and stdout is pure JSON.
- Failure-path tests confirm stdout is empty and errors are written to stderr.

### Human and JSON output

- `test_format_json_for_all_commands` parses JSON for `replay`, `list-sessions`, and `validate-store`.
- `test_human_list_sessions_format` verifies human-readable `list-sessions` output.

### EventStore contract extension

- `test_list_sessions` verifies `list_sessions()` for both `InMemoryEventStore` and `SQLiteEventStore`.
- `SQLiteEventStore.list_sessions()` uses a single `GROUP BY` query with `ORDER BY session_id`.
- `InMemoryEventStore.list_sessions()` iterates `_streams` and returns summaries sorted by `session_id`.

### Validation

- `mpe validate-store` uses `store.list_sessions()` and `Replay(store).replay(session_id)` for each session.
- `test_validate_store_passes` and `test_validate_store_fails_on_corrupt_row` confirm correct behavior.

### Replay-live state equality

- `test_run_and_replay_match` runs the CLI, replays the persisted session, compares the JSON output to an independent in-memory `RuntimeState` reference, and asserts equality after an ID-agnostic projection (`normalize_state_dict`).

### Read-only no-creation semantics

- `test_read_only_commands_do_not_create_store` confirms that `list-sessions`, `replay`, and `validate-store` on a missing path exit `3` and leave no file behind.

### Deterministic ordering

- `test_list_sessions` asserts `session_id` values are returned in ascending lexicographic order.
- `test_validate_store_passes` verifies `validate-store` output is deterministic and sorted.

### Invocation paths

- `test_python_mpe_invocation` verifies `python -m mpe ...` in a subprocess.
- `test_installed_console_entry_point` verifies the installed `mpe` console script.
- `test_cross_process_replay` verifies cross-process replay via `python -m mpe`.

## 5. Exclusions Audit

No Hebrew Engine logic, EEG, learner model, `StateInferenceModel`, adaptation, REST API, web UI, cloud deployment, additional persistence backend, event compaction, snapshotting, backup/restore, or fixture/provider overrides were introduced. MPE v1.1 event envelopes, payload schemas, and runtime state-machine rules were not modified.

## 6. Residual Risks

| Risk | Status |
|---|---|
| `RuntimeState.as_dict()` may change in a future phase, affecting `--format json` output | Documented in CLI design; future changes require MPE v1.1 change control. |
| Partial `run-mock-session` runs may leave incomplete sessions in the store | Acceptable because the event log is append-only and `validate-store` reports failures. |

## 7. Recommendation

`APPROVE_PHASE_4B_3_CLOSURE`

All acceptance criteria from the revised Phase 4B.3 scope proposal are satisfied. The CLI is a thin, stdlib-only infrastructure layer on top of the verified runtime and persistence foundation. The 89-test suite, static analysis, local CLI verification, and Docker/Compose verification all pass.
