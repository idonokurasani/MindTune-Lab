# Phase 4B.3 CLI Design

## Overview

Phase 4B.3 exposes the MPE runtime, replay engine, and `EventStore` persistence layer through a minimal command-line interface built with Python stdlib `argparse`. The CLI is intentionally infrastructure-only: it adds no Hebrew, EEG, adaptation, network, or UI logic and introduces only one new `EventStore` protocol method (`list_sessions()`).

## Architecture

### Modules

- `packages/mpe/src/mpe/cli.py` — argument parsing and command dispatch.
- `packages/mpe/src/mpe/cli_helpers.py` — shared utilities for store-path resolution, output formatting, mock-provider construction, and runtime execution.
- `packages/mpe/src/mpe/__main__.py` — enables `python -m mpe`.

### Entry points

- `python -m mpe <command>`
- Installed console script `mpe <command>` (declared in `pyproject.toml` `[project.scripts]`)

## Command grammar

```text
mpe [-h] [--version] [-v] [--store-path PATH] <command> ...
```

| Command | Arguments | Options |
|---|---|---|
| `run-mock-session` | (none) | `--session-id`, `--learner-id` (default `learner_001`), `--random-seed` (default `seed_0`), `--format {human,json}` |
| `replay` | `SESSION_ID` | `--format {human,json}` |
| `list-sessions` | (none) | `--format {human,json}` |
| `validate-store` | (none) | `--format {human,json}` |

`--format` defaults to `human` for all commands. `--store-path` resolution order: CLI option, `MPE_EVENT_STORE_PATH` environment variable, default `/data/mpe/events.db`.

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Success |
| `1` | Unexpected internal error |
| `2` | Usage or argument error |
| `3` | Session or resource not found |
| `4` | Invalid or corrupted event store |
| `5` | Database unavailable or locking timeout |
| `6` | Internal invariant violation (e.g., provider failure, illegal state transition) |

## Stdout/stderr contract

- stdout carries only successful command results: human-readable text or a single JSON document when `--format json` is used.
- stderr carries diagnostics, warnings, verbose output (`-v`), and all error messages.
- On failure, stdout is empty and the process exits with a non-zero code.

## Implementation notes

- All commands use `SQLiteEventStore` through its context manager (`with SQLiteEventStore(path) as store:`).
- Read-only commands (`replay`, `list-sessions`, `validate-store`) check that the store file exists before opening, so they never create a missing database.
- `run-mock-session` may create a new store; it logs `Created new event store at <path>` to stderr.
- `validate-store` validates each session independently by calling `Replay(store).replay(session_id)`, avoiding the cross-session ordering problem of validating a global event stream.
- Deterministic identifier generation is not exposed as a public CLI option. Normal CLI execution uses random UUIDs; the test suite verifies replay correctness against an independent in-memory reference state using an ID-agnostic projection.
