# MindTune Lab — Next Task (Single Source of Truth)

> **Read this document first every time you start work on this repository.**

## 1. Current objective

**Phase 4B.3 is complete.** The minimal MPE CLI is implemented, tested, and verified. It exposes `run-mock-session`, `replay`, `list-sessions`, and `validate-store` commands through both `python -m mpe` and the installed `mpe` console script.

The next phase is **Phase 4B.4 — Hebrew provider integration**, but it **must not begin until the user explicitly approves it**.

## 2. Allowed scope

In Phase 4B.4, you may (after user approval):

- Implement Hebrew provider integration under `packages/mpe-hebrew/`.
- Connect Hebrew Engine to the MPE runtime through the approved provider boundary.
- Add integration tests that exercise the Hebrew provider with the MPE CLI and persistence.

Phase 4B.3 already added the CLI and `EventStore.list_sessions()`, so provider integration remains open.

## 3. Forbidden scope

In Phase 4B.4, you must **not**:

- Modify `docs/MPE_*.md` or `docs/specification/v1.1/*.md` without an approved ADR.
- Modify `data/hebrew/phase3/` dataset files.
- Delete legacy root-level files without explicit user confirmation.
- Introduce network services, production databases, UI, or CI/CD without explicit approval.
- Change MPE v1.1 event envelopes, payload schemas, or runtime state-machine rules without an approved ADR.

## 4. Completed Phase 4B.3 deliverables

- `packages/mpe/src/mpe/cli.py` — `argparse` CLI for the four approved commands.
- `packages/mpe/src/mpe/cli_helpers.py` — shared CLI utilities.
- `packages/mpe/src/mpe/__main__.py` — enables `python -m mpe`.
- `packages/mpe/pyproject.toml` — `[project.scripts]` `mpe = "mpe.cli:main"`.
- `packages/mpe/src/mpe/event_store.py` — `SessionSummary` and `EventStore.list_sessions()`.
- `packages/mpe/src/mpe/persistence/store.py` — `SQLiteEventStore.list_sessions()`.
- `packages/mpe/tests/test_cli.py` — parser/unit and process-level CLI tests.
- `packages/mpe/tests/test_event_store.py` — `test_list_sessions` contract test.
- `requirements.txt` — unused `click` entry removed.
- `docs/implementation/phase4b3/CLI_DESIGN.md` and `PHASE_4B_3_COMPLETION_REPORT.md`.
- 89 total tests passing; `ruff`, `mypy`, Docker build, compose, and two-container CLI demo verified.

## 5. Current implementation priorities

Priority 1: Await user approval and any additional direction for Phase 4B.4.  
Priority 2: When approved, design Hebrew provider integration before writing code.  
Priority 3: Keep `packages/mpe/`, the CLI, and the persistence layer stable and deterministic.

## 6. How to proceed after this phase

1. Confirm Phase 4B.3 acceptance with the user.
2. Update `PROJECT_STATE.md` to reflect Phase 4B.4 start.
3. Begin Phase 4B.4 design and implementation only after explicit user approval.

## 7. Quick reference

- Architecture: `SYSTEM_ARCHITECTURE.md`
- Directory map: `REPOSITORY_STRUCTURE.md`
- Agent rules: `AGENTS.md`
- Workflow: `DEVELOPER_WORKFLOW.md`
- Testing: `TESTING_STRATEGY.md`
- Project state: `PROJECT_STATE.md`
- Phase 4B.1 deliverables: `docs/implementation/phase4b1/`
- Phase 4B.2 deliverables: `docs/implementation/phase4b2/`
- Phase 4B.3 deliverables: `docs/implementation/phase4b3/`
- MPE docs: `docs/MPE_*.md`
- MPE spec: `docs/specification/v1.1/*.md`
