# Phase 4B.1 — Implementation Decisions

**Date:** 2026-07-23

## 1. Language and runtime

- **Python 3.14** is used for the MPE core package. The existing `.venv` at repository root was reused for Phase 4B.1 development.
- All source code is type-annotated where practical and uses `from __future__ import annotations`.

## 2. Package layout

- The `mpe` package lives at `packages/mpe/src/mpe/` following a `src`-layout convention.
- Package metadata is defined in `packages/mpe/pyproject.toml`.
- The package is installed in editable mode into the workspace virtual environment.

## 3. Module responsibilities

| Module | Responsibility |
|---|---|
| `mpe.types` | Canonical `Identifier` classes and `make_id` factory. |
| `mpe.enums` | Canonical string enums with validation (`CanonicalEnum`). |
| `mpe.errors` | Typed exceptions used by runtime, providers, and validation. |
| `mpe.events` | Immutable `Event` envelope, `SUPPORTED_EVENT_TYPES`, and `PAYLOAD_SCHEMAS`. |
| `mpe.validation` | Event envelope, ordering, payload, and session-transition validation. |
| `mpe.event_store` | In-memory append-only event store with optimistic concurrency. |
| `mpe.aggregates` | `RuntimeState` and sub-aggregates (`TrialState`, `BlockState`, `ResponseWindowState`). |
| `mpe.providers` | Provider protocols and deterministic mock providers. |
| `mpe.runtime` | `Runtime` orchestrator and `Clock` for deterministic mock sessions. |
| `mpe.replay` | Deterministic state reconstruction via `Replay`. |
| `mpe.demo` | `run_demo()` and CLI entry point used for verification. |
| `mpe.fixtures` | Static mock protocol fixtures. |

## 4. Design decisions

- **No persistence.** The event store is in-memory only. Persistence is deferred to a later phase.
- **No Hebrew Engine integration.** The `MockEvaluator` compares typed text to the `ContentItem.surface_form` deterministically.
- **No network, API, UI, or database.** Phase 4B.1 is strictly a single-process executable core.
- **Replay as proof.** The `RuntimeState` supports `apply(event)` and is reconstructed from the stored event stream. Equality of `as_dict()` between live execution and replay is the primary correctness criterion.
- **Event immutability.** Events are frozen dataclasses with `MappingProxyType` payloads and tuple provenance/quality flags.
- **Optimistic concurrency.** `InMemoryEventStore.append` accepts an `expected_version` and rejects stale appends.

## 5. Docker and workspace tooling

- **Docker image:** `python:3.11-slim` with a pinned `requirements.txt` lock file.
- **Dependency lock:** `requirements.txt` generated from a clean Python 3.12 virtual environment with pinned runtime and dev tool versions.
- **Compose:** `compose/testing.yaml` runs tests and the deterministic demo; `docker-compose.yml` runs the demo.
- **Static checks:** `mypy` and `ruff` are installed in the image and pass against `packages/mpe/src/mpe`.
- **Non-root user:** The container runs as `mpe` (uid 1000) with writable cache directories for `ruff` and `mypy`.
