# Phase 4B.3 — Minimal MPE CLI Scope Proposal (Revised)

**Phase:** 4B.3  
**Objective:** Add a minimal, infrastructure-focused command-line interface (CLI) that exercises the Phase 4B.1 runtime and the Phase 4B.2 SQLite persistence foundation.  
**Date:** 2026-07-24  
**Status:** Revised scope proposal — ready for review  
**Review basis:** `docs/specification/v1.1/PHASE_4B_3_SCOPE_REVIEW.md`

## 1. Executive Summary

Phase 4B.3 exposes the MPE runtime, replay engine, and persistent event store through a small `argparse`-based CLI. It is the smallest infrastructure layer on top of the persistence foundation: it turns the existing `Runtime`/`Replay`/`SQLiteEventStore` machinery into a runnable, inspectable tool without introducing domain-specific logic, network services, graphical interfaces, or new runtime dependencies.

The CLI will provide exactly four commands:

- `run-mock-session` — execute and persist the reference mock session.
- `replay <session-id>` — replay a persisted session and print its terminal state.
- `list-sessions` — list sessions in a store.
- `validate-store` — validate the structural integrity of the persisted event log.

This phase makes one controlled extension to the `EventStore` contract — adding `list_sessions()` — and keeps all other MPE v1.1 contracts unchanged. It does not introduce Hebrew, EEG, adaptation, REST, cloud, UI, or multi-node functionality. It uses Python stdlib `argparse`; the `click` entry in `requirements.txt` is an unexplained artifact and will not be adopted.

## 2. Current Baseline

Phase 4B.1 provides:

- `packages/mpe/src/mpe/runtime.py` — `Runtime` orchestrator with `run_mock_session()` and `Clock`.
- `packages/mpe/src/mpe/replay.py` — `Replay` class reconstructing `RuntimeState` from a store.
- `packages/mpe/src/mpe/event_store.py` — `InMemoryEventStore` and the shared `EventStore` protocol.
- `packages/mpe/src/mpe/demo.py` — `mpe.demo` live/replay demonstration.
- `packages/mpe/src/mpe/fixtures.py` — `make_mock_fixtures()`.
- 42 unit/contract/replay tests.

Phase 4B.2 provides:

- `packages/mpe/src/mpe/persistence/store.py` — `SQLiteEventStore` with WAL, `BEGIN IMMEDIATE`, `busy_timeout=5000`, and `PRAGMA user_version`.
- `packages/mpe/src/mpe/persistence/serializer.py` — canonical `to_row`/`from_row` round-trip.
- `packages/mpe/src/mpe/persistence/restart_demo.py` — idempotent cross-process restart/replay verification.
- `packages/mpe/tests/persistence/` — 17 persistence-specific tests.
- `Dockerfile` with `/data/mpe` and `chown` to `mpe`.
- `compose/testing.yaml` and `compose/persistence.yaml`.
- 68 total tests passing; Docker build, compose, and two-container restart demo verified.

`packages/mpe/pyproject.toml` declares `pydantic>=2.0` and `typing-extensions>=4.5`. `requirements.txt` contains a pinned `click==8.4.2`, but no source file in `packages/mpe/src` or in the root-level legacy modules imports or uses `click`. A repository search (`grep -R "import click"` / `from click`) confirms `click` is dead weight in the current approved source tree. The CLI will therefore use stdlib `argparse` and `requirements.txt` should be regenerated or manually cleaned to remove the unused `click` entry as part of this phase's closure.

## 3. Problem Statement

After Phase 4B.2, the MPE runtime is only accessible through Python imports (`mpe.demo`, `mpe.persistence.restart_demo`) or test runners. There is no stable, documented way for a developer or CI pipeline to:

- Create a persisted mock session from the command line.
- Inspect or replay an existing persisted session.
- Discover which sessions live in a given SQLite event store.
- Validate the structural integrity of an event-store file.

A minimal CLI closes this gap and provides the canonical integration surface for subsequent phases (provider loading, real protocol execution, operations tooling) while remaining strictly infrastructure.

## 4. Relationship to Phases 4B.1 and 4B.2

- The CLI reuses the existing `Runtime.run_mock_session()` and `Replay` classes unchanged.
- The CLI uses the `EventStore` protocol; `SQLiteEventStore` is the default backend for normal CLI use, with `InMemoryEventStore` remaining available for tests.
- The CLI adds exactly one new `EventStore` protocol method, `list_sessions()`, implemented trivially for `InMemoryEventStore` and via a single `GROUP BY` query for `SQLiteEventStore`.
- The CLI does not change any MPE v1.1 event envelope, payload schema, or runtime state-machine rule.
- The CLI can eventually subsume the ad-hoc `mpe.persistence.restart_demo` and `mpe.demo` entry points, but those modules are **not** removed in Phase 4B.3.

## 5. Proposed Components and Contract Changes

### 5.1 New source files

- `packages/mpe/src/mpe/cli.py` — the CLI implementation, using stdlib `argparse`. Contains only argument parsing and command dispatch.
- `packages/mpe/src/mpe/__main__.py` — enables `python -m mpe <command>`.
- `packages/mpe/src/mpe/cli_helpers.py` — required shared utilities: `resolve_store_path()`, `open_store()`, `format_output()`, `build_mock_providers()`, `build_mock_runtime()`, and `run_mock_session_in_runtime()`. `cli.py` delegates all non-trivial logic to this module.
- `packages/mpe/tests/test_cli.py` — CLI tests.

### 5.2 Modified source/config files

- `packages/mpe/src/mpe/event_store.py` — add `SessionSummary` dataclass and `list_sessions()` to the `EventStore` protocol; implement it on `InMemoryEventStore`.
- `packages/mpe/src/mpe/persistence/store.py` — implement `list_sessions()` on `SQLiteEventStore`.
- `packages/mpe/pyproject.toml` — add the console entry point `mpe = "mpe.cli:main"`. No new runtime dependencies are added.
- `requirements.txt` — remove the unused `click==8.4.2` line (or regenerate the lock file from `pyproject.toml`); optional but recommended for clarity.
- `Dockerfile` — no change required.

### 5.3 Public CLI contract

Invocation forms:

```text
mpe [-h] [--version] [-v] [--store-path PATH] <command> ...
python -m mpe [-h] [--version] [-v] [--store-path PATH] <command> ...
```

Global options:

- `-h`, `--help` — show help and exit `0`.
- `--version` — print package version and exit `0`.
- `-v`, `--verbose` — emit additional diagnostic lines to stderr.
- `--store-path PATH` — SQLite event-store path. Resolution order: this option, then `MPE_EVENT_STORE_PATH` env var, then `/data/mpe/events.db`.

Subcommands:

| Command | Arguments | Options |
|---|---|---|
| `run-mock-session` | (none) | `--session-id ID`, `--learner-id ID`, `--random-seed SEED`, `--format {human,json}` |
| `replay` | `SESSION_ID` | `--format {human,json}` |
| `list-sessions` | (none) | `--format {human,json}` |
| `validate-store` | (none) | `--format {human,json}` |

`--format` defaults to `human` for every command. `json` emits a single JSON document on stdout and no human commentary.

### 5.4 `run-mock-session` command

```text
mpe run-mock-session [--session-id ID] [--learner-id ID] [--random-seed SEED] [--format {human,json}]
```

- Uses `make_mock_fixtures()` for program, protocol, task, block, and content item.
- Defaults: `learner_id="learner_001"`, `random_seed="seed_0"`.
- If `--session-id` is supplied, it is passed to `Runtime.run_mock_session(session_id=...)`. Otherwise `Runtime` generates a random `SessionID`.
- The command always uses the runtime's normal production identifier generation (`make_id` / `uuid.uuid4`). No deterministic-ID mode is exposed.
- Opens `SQLiteEventStore` with `with SQLiteEventStore(path) as store:`, runs `Runtime`, and closes the store on exit.
- On success, prints the generated `session_id` and event count.
- JSON output schema:

```json
{
  "session_id": "<string>",
  "event_count": 22,
  "status": "completed",
  "terminal": true
}
```

- Exits `0` on success; see §8 for failure codes.

### 5.5 `replay` command

```text
mpe replay [--format {human,json}] SESSION_ID
```

- Reads all events for `SESSION_ID` from the store using `store.read(session_id)`.
- Reconstructs `RuntimeState` using `Replay(store).replay(session_id)`.
- Human output: a short summary (session ID, status, terminal, trial count, block count, event count).
- JSON output: `state.as_dict()` rendered as a single JSON document.
- Exits `0` on success; exits `3` if the session is not found; exits `4` if replay fails due to store corruption or invalid events.

### 5.6 `list-sessions` command

```text
mpe list-sessions [--format {human,json}]
```

- Calls `store.list_sessions()` and prints one entry per session.
- Human output (one line per session, columns separated by two spaces):

```text
<session_id>  <event_count>  <last_sequence>
```

- JSON output schema:

```json
[
  {"session_id": "<string>", "event_count": 22, "last_sequence": 22}
]
```

- Deterministic ordering: ascending lexicographic order of `session_id` string.
- Exits `0` if the command completes; exits `3` if the store file does not exist (read-only commands do not create new databases).

### 5.7 `validate-store` command

```text
mpe validate-store [--format {human,json}]
```

Architecture: `validate-store` is a generic CLI-level operation composed from the `EventStore` contract:

1. Call `store.list_sessions()` to obtain all session identifiers in deterministic order.
2. For each session, call `Replay(store).replay(session_id)`. This exercises `store.read(session_id)`, which for `SQLiteEventStore` already validates every row via `validate_event(event, previous_events=events)` and raises a typed error on the first bad row, and then applies the events to a fresh `RuntimeState`.
3. If every session replays successfully, the store is valid.

This design avoids relying on `EventStore.all_events()` for validation, because `all_events()` returns a global ordering (`session_id, session_sequence_number`) and `validate_event` is sequence-relative within a session; cross-session sequence resets would produce false ordering errors if validated as a single stream.

Human output on success:

```text
store valid: <event_count> events, <session_count> sessions
```

JSON output schema:

```json
{
  "valid": true,
  "event_count": 22,
  "session_count": 1,
  "sessions": [
    {"session_id": "<string>", "event_count": 22, "last_sequence": 22}
  ],
  "error": null
}
```

On failure, human output:

```text
store invalid: <error message>
```

JSON output on failure:

```json
{
  "valid": false,
  "event_count": 0,
  "session_count": 0,
  "sessions": [],
  "error": "<error message>"
}
```

- Exits `0` if valid; exits `4` if invalid or corrupted.

### 5.8 JSON output serialization rules

All `--format json` output is produced by `json.dumps` on a plain Python structure. The CLI guarantees:

- **Identifiers** (`SessionID`, `EventID`, `TrialID`, etc.) are rendered as their string `value` before serialization; no `Identifier` object is passed to `json.dumps`.
- **Enums** (`SessionStatus`, `AnswerStatus`, etc.) are rendered with their `.value` string before serialization.
- **Timestamps** are persisted and output as ISO 8601 strings? No — the runtime uses monotonic `float` timestamps (`Clock`), not wall-clock datetimes. JSON output preserves the original `float` values for `timestamp`, `wallclock_at`, and `completed_at` fields. No date-time formatting is applied.
- **Booleans** use JSON native `true`/`false`.
- **Lists and dicts** preserve their original structure.
- Each successful `--format json` command emits **exactly one** JSON document and no trailing text on stdout.
- The key names and value types in the documented JSON schemas (§5.4–§5.7) are stable for Phase 4B.3. Any future change requires an approved ADR.

## 6. Event-Store Contract Extension

### 6.1 `SessionSummary`

A new frozen dataclass in `mpe.event_store`:

```python
from dataclasses import dataclass
from mpe.types import SessionID

@dataclass(frozen=True)
class SessionSummary:
    session_id: SessionID
    event_count: int
    last_sequence: int
```

`last_sequence` is the maximum `session_sequence_number` for the session. Status is intentionally **not** included, because status is a `RuntimeState` concern, not a store concern. If the CLI `list-sessions` output wants status, it must replay the session separately.

### 6.2 `EventStore.list_sessions()`

Add to the protocol:

```python
def list_sessions(self) -> list[SessionSummary]: ...
```

`InMemoryEventStore.list_sessions()` iterates `self._streams`, returning one summary per session sorted by `str(session_id)`.

`SQLiteEventStore.list_sessions()` executes:

```sql
SELECT session_id,
       COUNT(*) AS event_count,
       MAX(session_sequence_number) AS last_sequence
FROM events
GROUP BY session_id
ORDER BY session_id
```

and constructs `SessionSummary` objects from the rows.

### 6.3 `validate-store` is not a protocol method

No `validate()` method is added to `EventStore`. Validation is a CLI-level composition of `list_sessions()` and `Replay`, keeping the store boundary minimal and avoiding a new capability that only one command needs.

## 7. Event-Flow Implications

- Only `run-mock-session` appends events. It does so through the existing `EventStore.append()` path.
- `run-mock-session` emits events incrementally as `Runtime` runs. Each `append()` in `SQLiteEventStore` is a separate `BEGIN IMMEDIATE ... COMMIT` transaction. A crash mid-run may leave a partially persisted session; this is acceptable because the event log is append-only and the store remains valid up to the last committed event.
- No command performs `UPDATE` or `DELETE` on event rows; the append-only invariant is preserved.
- `replay`, `list-sessions`, and `validate-store` are read-only. They do not create new databases (see §11.5).

## 8. Deterministic Behavior Requirements

- A `run-mock-session` invocation with the same `--session-id`, `--learner-id`, and `--random-seed` produces the same sequence of `session_sequence_number` values and the same terminal state shape on every run. Runtime-generated identifiers (`trial_id`, `event_id`, etc.) are random UUIDs and therefore differ between runs; they are not part of the state-machine semantics being verified.
- `replay` of a completed session must reconstruct the same terminal `RuntimeState` as the live execution for that session.
- The CLI must not introduce non-deterministic output into the event stream; output formatting is separate from persisted events.
- `list-sessions` and `validate-store` produce output in deterministic order (ascending `session_id`).

## 9. Normal vs. Deterministic Identifiers

- **Normal CLI execution uses random production identifiers.** The default `run-mock-session` does not expose any deterministic-ID flag.
- **Deterministic identifiers are reserved solely for tests and demos and are not a CLI feature.** The CLI tests will verify replay correctness by comparing the CLI replay output to an independent in-memory reference state using a stable, ID-agnostic projection (see §14.2). No `uuid.uuid4` monkeypatch is used by the CLI.
- If future phases require a user-facing deterministic run mode, it must be implemented as an explicit, injectable identifier-generation dependency passed into `Runtime` and `ProviderSet` construction, not as a process-global patch.

## 10. Persistence Implications

- The CLI uses `SQLiteEventStore` for normal operation. It respects the existing schema (`PRAGMA user_version = 1`) and does not require schema changes.
- The CLI supports the same `MPE_EVENT_STORE_PATH` environment variable as `restart_demo`.
- `list-sessions` uses the public `EventStore.list_sessions()` interface; no SQL leaks into `cli.py`.
- The CLI always closes the store after each command via `SQLiteEventStore`'s context manager.

## 11. Database Lifecycle, Open Modes, and Locking

### 11.1 Connection and pragmas

The CLI uses the existing `SQLiteEventStore`, which opens a connection with:

- `isolation_level=None` (autocommit).
- `timeout=5.0` (connection open timeout).
- `PRAGMA journal_mode = WAL`.
- `PRAGMA synchronous = NORMAL`.
- `PRAGMA busy_timeout = 5000`.

### 11.2 Open mode

All commands open the store in the default read/write SQLite mode through `SQLiteEventStore.__init__`. Read-only commands do not invoke `append`/`append_batch`; they only call `read`, `list_sessions`, or are used indirectly by `Replay`.

### 11.3 Context-manager usage

Every command wraps store access in:

```python
with SQLiteEventStore(path) as store:
    ...
```

`SQLiteEventStore` already implements `__enter__`/`__exit__`, which calls `close()`. This guarantees connection and WAL lock release even if an exception is raised.

### 11.4 Locking failure semantics

- If another process holds the write lock and the `busy_timeout` expires, `SQLiteEventStore` maps `sqlite3.OperationalError` ("database is locked") to `ConcurrencyError`.
- The CLI maps `ConcurrencyError` to exit code `5`.
- Concurrent readers are safe under WAL mode.

### 11.5 Accidental store creation by read-only commands

`SQLiteEventStore.__init__` creates the parent directory and a new database file if the path does not exist. To prevent read-only commands (`replay`, `list-sessions`, `validate-store`) from silently creating an empty store, the CLI checks `path.exists()` before opening for those commands. If the file is missing, the command exits `3` (session/resource not found) and prints a clear error to stderr.

`run-mock-session` is permitted to create a new store, but the CLI logs (to stderr, with `-v`) the absolute path and whether a new database file was created, so operators can detect path typos.

### 11.6 Close behavior

`SQLiteEventStore.close()` closes the connection. The context manager ensures `close()` is called exactly once. If construction fails (e.g., permission denied), there is no store object to close; the exception propagates and maps to the appropriate exit code.

## 12. Failure and Recovery Semantics

### 12.1 Exit-code table

| Code | Meaning | Typical cause |
|---|---|---|
| `0` | Success | Command completed and produced valid output. |
| `2` | Usage or argument error | Unknown command, unknown flag, malformed `SESSION_ID`, missing required argument, `--format` value not `human`/`json`, path is a directory. |
| `3` | Session or resource not found | `replay` of a non-existent session; `list-sessions`/`validate-store` on a missing store file. |
| `4` | Invalid or corrupted event store | `ReplayError`, `ValidationError`, `EventOrderingError`, `UnknownSchemaVersionError`, or corrupt JSON row encountered during `replay` or `validate-store`. |
| `5` | Database unavailable or locking timeout | `ConcurrencyError` from `busy_timeout` expiry, permission denied, or other operational inability to open/use the store. |
| `6` | Internal invariant violation | `IllegalStateTransitionError`, `ProviderFailureError`, or a state-machine invariant failure not covered by exit code `4`. |
| `1` | Unexpected internal error | Any unhandled exception or `MPEError` subclass not otherwise classified. |

`argparse` automatically uses exit code `2` for usage errors; the CLI must not renumber this.

### 12.2 Stdout/stderr contract

- **stdout** is reserved for successful command results only: either human-readable text or a single JSON document when `--format json` is used.
- **stderr** is reserved for diagnostic messages, warnings (e.g., "created new database file"), verbose output (`-v`), and all error messages.
- When `--format json` is used, stdout must contain exactly one JSON document and no human commentary, even if `-v` is also set.
- On failure, stdout is empty; the error message is written to stderr, and the process exits with the appropriate non-zero code.

## 13. Path Handling and Security Constraints

`cli_helpers.resolve_store_path()` performs the following checks in order:

1. Obtain the raw path from `--store-path`, `MPE_EVENT_STORE_PATH`, or the default `/data/mpe/events.db`.
2. Convert to an absolute `Path` and resolve `..` and symlinks with `Path.resolve()`.
3. If the resolved path is a directory, exit `2` with a clear error.
4. If the command is read-only and the resolved path does not exist, exit `3`.
5. If the command is read-only and the resolved path exists but is not a regular file (e.g., a device node), exit `4`.
6. For `run-mock-session`, if the parent directory does not exist, `SQLiteEventStore` creates it; the CLI logs the resolved absolute path with `-v`.
7. If `run-mock-session` creates a new file, the CLI logs a warning to stderr: `created new event store at <path>`.

The CLI does not restrict paths to a specific filesystem subtree; container operators are responsible for mounting only intended volumes. The CLI does not follow network paths or expand shell wildcards.

## 14. Testing Strategy

### 14.1 Authoritative test-discovery command

The single authoritative test command is:

```bash
python -m unittest discover -s packages/mpe/tests -p 'test_*.py' -v
```

This is the same command used by `compose/testing.yaml` and `compose/persistence.yaml`. The Phase 4B.3 completion report must state the exact total test count reported by this command (the 68 existing tests plus the new CLI tests) and confirm zero collection errors.

### 14.2 CLI test levels

#### Parser/unit tests (`packages/mpe/tests/test_cli.py`)

Using `argparse` directly or by invoking `mpe.cli.main` with a patched `sys.argv`:

- `test_run_mock_session_persists_22_events` — run CLI in a temp directory, assert 22 events in store.
- `test_run_and_replay_match` — run CLI `run-mock-session --session-id <fixed>`, then CLI `replay <fixed> --format json`. Independently compute an in-memory reference state using `InMemoryEventStore` + `Runtime` with the same fixed `session_id`, `learner_id`, and `random_seed`. Compare the CLI `replay` JSON to the reference `as_dict()` after normalizing both dicts to remove runtime-generated identifier values (`trial_id`, `response_window_id`, `evaluation_id`, etc.) and by stringifying any remaining identifier objects. The projection must preserve `session_id`, `session_status`, `terminal`, `trials` count, `blocks` count, and payload-derived values. This avoids depending on random UUIDs while still verifying serialization and replay correctness.
- `test_replay_missing_session_fails` — replay a non-existent session, assert exit code `3` and stderr message.
- `test_list_sessions` — run two sessions, list, assert both present in ascending `session_id` order.
- `test_validate_store_passes` — run a session, validate, assert exit `0` and JSON `valid: true`.
- `test_validate_store_fails_on_corrupt_row` — manually corrupt a row, validate, assert exit `4` and `valid: false`.
- `test_store_path_env_var` — set `MPE_EVENT_STORE_PATH`, run without `--store-path`, assert file created at env path.
- `test_format_json_produces_valid_json` — every command with `--format json` emits parseable JSON.
- `test_verbose_writes_to_stderr_not_stdout` — with `-v`, diagnostic lines appear on stderr; stdout content is unchanged.
- `test_read_only_commands_do_not_create_store` — `replay`, `list-sessions`, `validate-store` on a missing path exit `3` and do not create a file.

#### Process-level invocation tests

- Use `subprocess.run([sys.executable, "-m", "mpe", ...])` or the installed `mpe` console script in a temporary virtual environment or Docker container to verify packaging, exit codes, and stdio separation.
- One test runs `mpe run-mock-session` in a subprocess, then `mpe replay` in a second subprocess, demonstrating cross-process replay.

#### Docker acceptance tests

- `docker build -t mpe:phase4b3 .` succeeds.
- `docker run --rm mpe:phase4b3 mpe --help` prints help and exits `0`.
- `docker run --rm mpe:phase4b3 python -m mpe --help` prints help and exits `0`.
- `docker compose -f compose/testing.yaml up --build` runs the full discovery command and passes (no new `compose/cli.yaml` is required).
- Manual two-container verification (see §15.2).

### 14.3 Existing test preservation

All 68 existing Phase 4B.1/4B.2 tests must continue to pass with no assertion changes. The new `EventStore.list_sessions()` method must not break any existing contract test.

## 15. Docker Verification Strategy

### 15.1 Image build and basic invocation

- `docker build -t mpe:phase4b3 .` must succeed.
- `docker run --rm mpe:phase4b3 mpe --help` and `docker run --rm mpe:phase4b3 python -m mpe --help` must both exit `0`.

### 15.2 Two-container manual verification

```bash
docker volume create mpe-cli-data
docker run --rm -v mpe-cli-data:/data mpe:phase4b3 \
    mpe run-mock-session --store-path /data/mpe/events.db

docker run --rm -v mpe-cli-data:/data mpe:phase4b3 \
    mpe list-sessions --store-path /data/mpe/events.db --format json

docker run --rm -v mpe-cli-data:/data mpe:phase4b3 \
    mpe replay <session-id> --store-path /data/mpe/events.db --format json

docker run --rm -v mpe-cli-data:/data mpe:phase4b3 \
    mpe validate-store --store-path /data/mpe/events.db --format json

docker volume rm mpe-cli-data
```

This supersedes or documents alongside the existing `restart_demo` two-container procedure; `restart_demo` is not removed in Phase 4B.3.

### 15.3 Compose file

No new `compose/cli.yaml` is required. `compose/testing.yaml` already runs `python -m unittest discover -s packages/mpe/tests -p 'test_*.py' -v`, which will collect and run `packages/mpe/tests/test_cli.py` once it exists. `compose/persistence.yaml` remains for persistence-specific tests. This avoids proliferating near-identical Compose files (C4, C5).

## 16. Measurable Acceptance Criteria

| # | Criterion | Verification command / check |
|---|---|---|
| 1 | All 68 Phase 4B.1/4B.2 tests pass unchanged | `python -m unittest discover -s packages/mpe/tests -p 'test_*.py' -v` → 68 + N total, OK |
| 2 | `mpe --help` and `python -m mpe --help` work | Run in Docker, exit `0` |
| 3 | `run-mock-session` persists 22 events by default | `mpe run-mock-session && mpe list-sessions --format json` shows `event_count` 22 |
| 4 | `replay` reconstructs the terminal state | `mpe replay <sid> --format json` output matches normalized in-memory reference |
| 5 | `list-sessions` reports sessions and counts correctly | Run two sessions; `list-sessions` shows both in ascending order |
| 6 | `validate-store` passes for valid store and reports first error for corrupt store | Corrupt a payload row; `validate-store` exits `4` with `valid: false` |
| 7 | `--store-path` and `MPE_EVENT_STORE_PATH` are respected | Unit test with temp directories |
| 8 | All commands support `--format json` with stable schemas | Parser and process-level tests parse every JSON output |
| 9 | Exit codes follow the table in §12.1 | Unit tests assert exact exit codes for each failure class |
| 10 | stdout/stderr contract enforced | `test_verbose_writes_to_stderr_not_stdout` and JSON-mode tests |
| 11 | Read-only commands do not create missing stores | `replay`/`list-sessions`/`validate-store` on missing path exit `3` and leave no file |
| 12 | `ruff` and `mypy` pass on `packages/mpe/src/mpe` | Run inside Docker |
| 13 | Docker build, `compose/testing.yaml`, and two-container CLI demo pass | Commands in §15 |
| 14 | No MPE v1.1 event envelope, payload schema, or runtime state-machine rule is modified | Code review; no changes to `events.py`, `aggregates.py`, `validation.py` beyond `SessionSummary`/`list_sessions` |
| 15 | No Hebrew, EEG, adaptation, REST API, web UI, cloud, or external service is introduced | Code review and scope exclusions |
| 16 | `pyproject.toml` has no new runtime dependencies; `requirements.txt` `click` entry removed or explained | Inspect manifests |
| 17 | Completion report states exact test count from the authoritative discovery command | Document audit |

## 17. Explicit Exclusions

- No Hebrew Engine or linguistic domain logic.
- No EEG, sensors, learner model, `StateInferenceModel`, or adaptation.
- No REST API, GraphQL, gRPC, or network service.
- No graphical user interface, dashboard, or web frontend.
- No cloud deployment, Kubernetes, serverless, or production orchestration.
- No additional persistence backend beyond SQLite; no PostgreSQL, Redis, Kafka, RabbitMQ, etc.
- No event compaction, snapshotting, or mutable state store.
- No backup/restore implementation.
- No fixture or provider overrides beyond the mock fixtures used by `run-mock-session`.
- No deterministic-ID CLI flag or `uuid.uuid4` monkeypatch.
- No new `EventStore` protocol methods beyond `list_sessions()`.
- No changes to approved MPE v1.1 specification documents (`docs/MPE_*.md`, `docs/specification/v1.1/*.md`) except this proposal and the review.
- No changes to `data/hebrew/phase3/`.
- No changes to root-level legacy prototypes.
- No removal of `mpe.demo` or `mpe.persistence.restart_demo` in Phase 4B.3.

## 18. Implementation Milestones

### Milestone 1 — `EventStore.list_sessions()` extension

- Add `SessionSummary` and `list_sessions()` to `EventStore` protocol and `InMemoryEventStore`.
- Implement `list_sessions()` on `SQLiteEventStore` with a `GROUP BY` query.
- Add unit tests for `list_sessions` in the existing event-store contract tests.
- Acceptance: `python -m unittest discover -s packages/mpe/tests -p 'test_*.py'` passes with the existing 68 tests plus new `list_sessions` tests.

### Milestone 2 — CLI skeleton and entry points

- Create `mpe/cli.py` with `argparse` and the four subcommands.
- Create `mpe/__main__.py`.
- Create `mpe/cli_helpers.py` with `resolve_store_path`, `open_store`, `format_output`, `build_mock_providers`, `build_mock_runtime`, `run_mock_session_in_runtime`.
- Add `mpe = "mpe.cli:main"` to `pyproject.toml`.
- Acceptance: `mpe --help` and `python -m mpe --help` work; `run-mock-session` persists 22 events.

### Milestone 3 — `replay`, `list-sessions`, and `validate-store`

- Implement `replay`, `list-sessions`, and `validate-store` with `--format human|json`.
- Enforce read-only commands do not create missing stores.
- Acceptance: all three commands produce correct human and JSON output and exit codes.

### Milestone 4 — CLI tests

- Add `packages/mpe/tests/test_cli.py` covering parser, process-level, and Docker-level scenarios.
- Acceptance: all new tests pass; the authoritative discovery command reports a single total count with zero errors.

### Milestone 5 — Docker verification

- Verify `docker build`, `docker compose -f compose/testing.yaml up --build`, and the two-container manual CLI demo.
- Acceptance: all pass.

### Milestone 6 — Dependency and manifest cleanup

- Remove unused `click` line from `requirements.txt` or regenerate the lock file from `pyproject.toml`.
- Acceptance: `mypy` and `ruff` pass; no new runtime dependencies in `pyproject.toml`.

### Milestone 7 — Documentation and completion report

- Create `docs/implementation/phase4b3/CLI_DESIGN.md`.
- Create `docs/implementation/phase4b3/PHASE_4B_3_COMPLETION_REPORT.md`.
- Update `docs/project/PROJECT_STATE.md` and `docs/project/NEXT_TASK.md`.
- Acceptance: documents reviewed and the completion report states the exact test count.

## 19. Risks and Unresolved Design Questions

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| `argparse` is slightly more verbose than `click` | Low | Low | Keep command functions short and delegate to `cli_helpers`; test with `argparse` directly. |
| `EventStore.list_sessions()` addition affects `mypy` typing of existing stores | Low | Low | Implement on both `InMemoryEventStore` and `SQLiteEventStore`; run `mypy` after. |
| Partial run persistence confuses operators | Low | Medium | Document append-only semantics; `validate-store` detects incomplete sessions. |
| Read-only commands accidentally create empty stores | Low | High | `cli_helpers.open_store()` checks existence for read-only commands. |
| `RuntimeState.as_dict()` JSON schema changes in a future phase | Low | Medium | Document `replay --format json` output as derived from `RuntimeState.as_dict()`; any future change to `as_dict()` is subject to existing MPE v1.1 change control. |

### Open questions resolved in this revision

1. **CLI framework:** `argparse` (stdlib). `click` is not adopted.
2. **`list-sessions` architecture:** `EventStore.list_sessions()` added to the protocol.
3. **`validate-store` architecture:** Generic CLI composition of `list_sessions()` + `Replay.replay()`.
4. **Default output format:** Human, with `--format json` opt-in for all commands.
5. **Deterministic IDs:** Not exposed in the CLI; tests use an independent in-memory reference with an ID-agnostic projection.
6. **Test-discovery command:** `python -m unittest discover -s packages/mpe/tests -p 'test_*.py' -v`; completion report must state exact count.
7. **`compose/cli.yaml`:** Not created; `compose/testing.yaml` is sufficient.

### Remaining design choices to confirm during implementation

- Exact set of keys to ignore/normalize in the `test_run_and_replay_match` state projection. The current proposal lists runtime-generated identifier fields; the final list will be confirmed against `RuntimeState.as_dict()`.
- Whether to remove `click` from `requirements.txt` by regeneration or manual edit. Manual removal is acceptable because `pyproject.toml` is the source of truth and `click` is unused.

## 20. Compatibility and Migration Considerations

- One new `EventStore` protocol method is added. `InMemoryEventStore` and `SQLiteEventStore` both implement it; no third-party store implementations exist.
- No database schema changes are required; the existing `events` table and `PRAGMA user_version = 1` are sufficient.
- The optional `session_id` parameter added to `Runtime.create_session`/`run_mock_session` in Phase 4B.2 is used by the CLI via `--session-id`. No further runtime changes are required.
- `mpe.demo` and `mpe.persistence.restart_demo` remain functional and are not removed.
- `compose/testing.yaml` requires no changes because the full `packages/mpe/tests` discovery pattern already covers `test_cli.py`.

## 21. Files Expected to Change

### New files

- `packages/mpe/src/mpe/cli.py`
- `packages/mpe/src/mpe/__main__.py`
- `packages/mpe/src/mpe/cli_helpers.py`
- `packages/mpe/tests/test_cli.py`
- `docs/implementation/phase4b3/CLI_DESIGN.md`
- `docs/implementation/phase4b3/PHASE_4B_3_COMPLETION_REPORT.md`

### Modified files

- `packages/mpe/src/mpe/event_store.py` — add `SessionSummary` and `list_sessions()`.
- `packages/mpe/src/mpe/persistence/store.py` — implement `list_sessions()`.
- `packages/mpe/pyproject.toml` — add console entry point.
- `requirements.txt` — remove unused `click` entry.
- `docs/project/PROJECT_STATE.md`
- `docs/project/NEXT_TASK.md`

### Files not to change

- `Dockerfile`.
- `compose/testing.yaml`, `compose/persistence.yaml`.
- All `docs/MPE_*.md` and `docs/specification/v1.1/*.md` except this proposal and the review.
- `data/hebrew/phase3/`.
- Root-level legacy source files.
- MPE v1.1 event envelopes, payload schemas, and runtime state-machine rules.

## 22. Revision Record

| Finding | Severity | Resolution in this revision |
|---|---|---|
| R1 — `list-sessions`/`validate-store` capability gap | REQUIRED | Added `EventStore.list_sessions()` with `SessionSummary`; `validate-store` defined as generic CLI composition of `list_sessions()` + `Replay.replay()` per session. |
| R2 — Exit codes and stdout/stderr contract | REQUIRED | Added explicit exit-code table (§12.1) and strict stdout/stderr contract (§12.2). |
| R3 — `click` dependency justification | REQUIRED | Replaced `click` with stdlib `argparse`; documented `click` in `requirements.txt` as an unused artifact to be removed; no new runtime dependency in `pyproject.toml`. |
| R4 — `uuid.uuid4` monkeypatch for deterministic IDs | REQUIRED | Removed deterministic-ID CLI flag entirely; normal CLI uses random production IDs; tests use independent in-memory reference with ID-agnostic projection. |
| R5 — `cli_helpers.py` optional | REQUIRED | Promoted `cli_helpers.py` to a required file (§5.1, §21). |
| R6 — Independent reference state for replay-live test | REQUIRED | Defined independent in-memory reference state and ID-agnostic projection comparison (§14.2). |
| R7 — Authoritative test-discovery command and count | REQUIRED | Specified `python -m unittest discover -s packages/mpe/tests -p 'test_*.py' -v` as the authoritative command and required exact count in the completion report (§14.1, §16). |
| C1 — Resolve `click` vs `argparse` in scope | RECOMMENDED | Resolved: `argparse` (§5.1, §19). |
| C2 — All commands support `--json` | RECOMMENDED | Resolved: replaced `--json` with `--format {human,json}` and applied to all four commands (§5.3). |
| C3 — Context-manager usage for store lifecycle | RECOMMENDED | Resolved: every command uses `with SQLiteEventStore(path) as store:` (§11.3). |
| C4 — Document `compose/cli.yaml` overlap with `restart_demo` | RECOMMENDED | Resolved: no new `compose/cli.yaml`; two-container CLI demo documented alongside existing `restart_demo` procedure (§15.2, §15.3). |
| C5 — Avoid proliferating Compose files | RECOMMENDED | Resolved: rely on existing `compose/testing.yaml` (§15.3). |
| O1 — Human-readable default output | OPTIONAL | **Accepted** (§5.3, §19). |
| O2 — No fixture/provider overrides | OPTIONAL | **Accepted** as firm exclusion (§17). |
| O3 — Deprecate `restart_demo` later | OPTIONAL | **Deferred** to a future completion report; `restart_demo` is not removed in Phase 4B.3 (§20). |
| O4 — Test `--verbose` behavior | OPTIONAL | **Accepted**; added `test_verbose_writes_to_stderr_not_stdout` to the test plan (§14.2). |

## 23. Self-Audit

| Category | Count | Status |
|---|---|---|
| BLOCKER | 0 | None identified in review. |
| REQUIRED (R1–R7) | 7 | All resolved in this revision. |
| RECOMMENDED (C1–C5) | 5 | All accepted and resolved. |
| OPTIONAL (O1–O4) | 4 | O1, O2, O4 accepted; O3 deferred. |
| Unresolved | 0 | None. |

## 24. Recommendation

**`APPROVE_PHASE_4B_3_IMPLEMENTATION`**

The revised scope addresses all REQUIRED findings from the critical review, accepts all RECOMMENDED findings, and records the OPTIONAL findings. The CLI remains a thin, stdlib-based infrastructure layer over the already-verified `Runtime`/`Replay`/`EventStore` foundation. It requires one controlled `EventStore` contract extension (`list_sessions()`), no new runtime dependencies, no MPE v1.1 semantic changes, and no domain expansion. The open questions remaining are implementation-level details (JSON key normalization, `requirements.txt` cleanup method) that do not affect the overall direction.
