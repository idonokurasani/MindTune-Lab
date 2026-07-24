# Phase 4B.1 — Docker Reproducibility Report

**Date:** 2026-07-23  
**Image:** `mpe:phase4b1` (also `compose-mpe-test:latest` via `compose/testing.yaml`)  
**Base image:** `python:3.11-slim`  

## Objective

Provide a deterministic, isolated Docker environment that builds the MPE Phase 4B.1 package, runs the full test suite, verifies live/replay determinism, and runs type checking and linting without requiring the host Python runtime.

## Files created or modified

| File | Purpose |
|---|---|
| `/Dockerfile` | Single development/test image for MPE. |
| `/.dockerignore` | Excludes virtual environments, caches, IDE files, and host-only data from the build context. |
| `/requirements.txt` | Locked Python dependency manifest used by `Dockerfile`. |
| `/pyproject.toml` | Workspace-level project metadata and tool configuration (black, ruff, mypy). |
| `/docker-compose.yml` | Convenience Compose service that runs the deterministic demo. |
| `/compose/testing.yaml` | Compose service that runs the full test suite and the demo. |
| `packages/mpe/README.md` | Package readme referenced by `pyproject.toml`. |
| `packages/mpe/pyproject.toml` | Package metadata; ruff/black/mypy configuration. |

## Build commands

```bash
# Build the image from repository root
docker build -t mpe:phase4b1 .

# Or build and run tests + demo via Compose
docker compose -f compose/testing.yaml up --build
```

## Verification commands executed inside Docker

```bash
# 1. Full test suite
python -m unittest discover -s packages/mpe/tests -p 'test_*.py' -v

# 2. Deterministic live + replay demo
python -m mpe.demo

# 3. Replay sanity check via Replay class
python -c 'from mpe.demo import run_demo; live, events, replayed, store = run_demo(); assert live.terminal and replayed.terminal and live == replayed; print("Replay OK: live and replay states match.")'

# 4. Static type check
mypy packages/mpe/src/mpe

# 5. Lint
ruff check packages/mpe/src/mpe
```

## Results

All commands were executed inside a container built from `mpe:phase4b1`. The complete captured output is available in `DOCKER_VERIFICATION_LOG.txt`.

| Step | Result |
|---|---|
| Full unit test suite | **42/42 passed** |
| Deterministic demo | **Live and replay states match** (22 events) |
| Replay class sanity check | **Passed** |
| mypy type check | **No issues found in 13 source files** |
| ruff lint | **All checks passed** |

## Compose verification

`docker compose -f compose/testing.yaml up --build` produced:

- Image `compose-mpe-test:latest` built successfully.
- Container `mpe-test-1` ran `42/42` tests and the deterministic demo.
- Service exited with code `0`.

## Determinism

The Docker build uses a pinned `requirements.txt` and copies package source at build time. The Compose test service additionally bind-mounts `packages/mpe` at runtime, so source changes are reflected without rebuild. The demo and replay produce identical event streams and terminal state across host and container runs because the mock providers and `Clock` are deterministic and seeded.

## Non-root user

The image creates and runs as user `mpe` (uid `1000`). Cache directories for `ruff` (`/tmp/ruff_cache`) and `mypy` (`/tmp/mypy_cache`) are pre-created and owned by `mpe` to avoid permission errors during lint/type checks.

## Notes

- No database, message broker, network API, or external service is required.
- No root-level legacy modules are imported by `packages/mpe`.
- The Docker environment is intentionally minimal; persistence and real Hebrew Engine integration are deferred to later phases.
