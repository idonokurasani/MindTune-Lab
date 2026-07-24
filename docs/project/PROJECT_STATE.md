# MindTune Lab — Project State

## 1. Completed phases

| Phase | Status | Key deliverables |
|---|---|---|
| Phase 1 — Initial concept & prototype | Completed | Early prototypes (`app.js`, `index.html`, `server.py`, `mindtune_app.py`) |
| Phase 2 — Critical review & ontology audit | Completed | `docs/research/mpe_ontology_audit_v1/`, `docs/MPE_V1_0_CRITICAL_REVIEW.md` |
| Phase 3 — Hebrew Engine data & contract | Completed | `data/hebrew/phase3/PHASE_3_FINAL_REPORT.md`, `data/hebrew/phase3/automatic_gold_100.json`, `docs/MPE_HEBREW_PROVIDER_CONTRACT.md` |
| Phase 4A — MPE v1.1 specification | Completed | `docs/MPE_ARCHITECTURE_V1_1.md`, `docs/MPE_OBJECT_MODEL_V1_1.md`, `docs/MPE_EVENT_MODEL_V1_1.md`, `docs/MPE_PROVIDER_BOUNDARIES.md`, `docs/MPE_ADAPTATION_CONTRACT.md`, canonical registries, `docs/specification/v1.1/*.md` |
| Phase 4A.5 — Architecture walkthroughs | Completed | `docs/specification/v1.1/walkthroughs/*.md`, acceptance matrix, completion report with `APPROVE_PHASE_4B` recommendation |
| Phase 4A.6 — Repository architecture | Completed | `docs/project/*.md` |
| Phase 4B.1 — Core MPE runtime skeleton | Completed | `packages/mpe/`, `docs/implementation/phase4b1/*.md` |
| Phase 4B.2 — Persistence foundation | Completed | `packages/mpe/src/mpe/persistence/`, shared `EventStore` protocol, SQLite store, restart/replay verification, `docs/implementation/phase4b2/*.md` |
| Phase 4B.3 — Minimal CLI | Completed | `packages/mpe/src/mpe/cli.py`, `mpe` console script, `EventStore.list_sessions()`, `docs/implementation/phase4b3/*.md` |

## 2. Current phase

**Phase 4B.3 complete.**

Objective achieved: the smallest executable MPE core capable of creating a session, executing a deterministic mock protocol, producing 22 canonical events, storing them in memory, enforcing lifecycle transitions, reconstructing state via replay, and verifying consistency between live execution and replay. Legacy root-level files were not modified.

## 3. Approved documents

The following documents are approved and binding for Phase 4B:

- `docs/MPE_ARCHITECTURE_V1_1.md`
- `docs/MPE_OBJECT_MODEL_V1_1.md`
- `docs/MPE_EVENT_MODEL_V1_1.md`
- `docs/MPE_PROVIDER_BOUNDARIES.md`
- `docs/MPE_HEBREW_PROVIDER_CONTRACT.md`
- `docs/MPE_ADAPTATION_CONTRACT.md`
- `docs/MPE_CANONICAL_ENUM_REGISTRY.md`
- `docs/MPE_CANONICAL_IDENTIFIER_REGISTRY.md`
- `docs/MPE_OBJECT_EVENT_COVERAGE_MATRIX.csv`
- `docs/MPE_RISK_REGISTER_V1_1.md`
- `docs/specification/v1.1/*.md`
- `docs/specification/v1.1/walkthroughs/*.md`
- `data/hebrew/phase3/PHASE_3_FINAL_REPORT.md`
- `data/hebrew/phase3/automatic_gold_100.json`

## 4. Phase 4B.3 completion status

1. Minimal `argparse`-based CLI implemented in `packages/mpe/src/mpe/cli.py` with `run-mock-session`, `replay`, `list-sessions`, and `validate-store` commands.
2. `packages/mpe/src/mpe/cli_helpers.py` centralizes shared CLI logic.
3. Both `python -m mpe` and the installed `mpe` console entry point work.
4. `EventStore.list_sessions()` added to the shared protocol and implemented for `InMemoryEventStore` and `SQLiteEventStore`.
5. 89 total tests pass: the original Phase 4B.1 suite, the shared event-store contract tests, the persistence-specific tests, and the new CLI tests.
6. Docker verification completed: `docker build`, `docker run mpe --help`, `docker run python -m mpe --help`, two-container CLI demo, and `docker compose -f compose/testing.yaml up --build` all pass.
7. `ruff check packages/mpe/src packages/mpe/tests` and `mypy packages/mpe/src/mpe` pass.
8. `PHASE_4B_3_COMPLETION_REPORT.md` recommends `APPROVE_PHASE_4B_3_CLOSURE`.

## 5. Phase 4B.2 completion status (archived)

1. `packages/mpe/persistence/` SQLite-backed event store implemented.
2. Shared `EventStore` protocol added; `InMemoryEventStore` and `SQLiteEventStore` both satisfy it.
3. Deterministic canonical serialization and full identifier/enum round-trip verified.
4. 68 total tests pass: the original Phase 4B.1 suite, the shared `InMemoryEventStore` and `SQLiteEventStore` contract tests, and the 17 persistence-specific tests.
5. Docker persistence verification completed: `compose/persistence.yaml` passes; two-container `restart_demo` on a named volume verifies cross-process replay.
6. `PHASE_4B_2_COMPLETION_REPORT.md` recommends `APPROVE_PHASE_4B_2_CLOSURE`.

## 6. Known risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Legacy root-level files create confusion about where new code belongs | High | Medium | `REPOSITORY_STRUCTURE.md` and `PROJECT_STATE.md` explicitly map legacy files to target locations. |
| Multiple Python virtual environments at root cause environment drift | Medium | Medium | Document and migrate to a single workspace virtual environment under `packages/` or `.venv` in `.gitignore`. |
| Phase 4B.4 may start before ADR workflow is in place | Medium | High | `DEVELOPER_WORKFLOW.md` defines ADR process and immutable documents. |
| Hebrew Engine implementation may predate MPE contracts | Medium | Medium | Review `hebrew/` against `MPE_HEBREW_PROVIDER_CONTRACT.md` during Phase 4B integration. |
| UI prototypes may be mistaken for approved architecture | Low | Medium | `AGENTS.md` and `SYSTEM_ARCHITECTURE.md` clarify that UI is secondary and prototypes are legacy. |

## 7. Technical debt

| Debt | Origin | Plan |
|---|---|---|
| Mixed root-level Python/JS files | Phase 1 prototypes | Migrate to `packages/` or archive during Phase 4B. |
| Multiple `.venv*` directories | Ad-hoc development | Consolidate into workspace-managed environment. |
| `__pycache__` and `.pytest_cache` in repo | Local development | Ensure `.gitignore` excludes generated artifacts. |
| `hebrew/` top-level directory | Pre-architecture Hebrew work | Migrate to `packages/mpe-hebrew/` and `data/hebrew/` as appropriate. |
| Root `.gitignore` incomplete | Local development | Ensure `.gitignore` excludes `.venv*`, `__pycache__`, `.pytest_cache`, and host artifacts. |

## 8. Future roadmap

| Phase | Goal |
|---|---|
| 4B.4 | Hebrew provider integration under `packages/mpe-hebrew/` (requires explicit approval). |
| 5A | Add adaptation policies, `AdaptationDecision`, and reversible parameter changes. |
| 5B | Add BrainLab sensor ingestion and offline `StateEstimate` production. |
| 6 | Build Piano Engine, additional language engines, UI, and dashboard. |
| 7+ | Production orchestration, scalable event-store backend, cloud deployment. |

## 9. Last updated

2026-07-24 — Phase 4B.3 completed; 89 tests passing, CLI (`mpe` / `python -m mpe`), SQLite persistence, and cross-process replay verification.
