# MindTune Lab — AI-Agent Onboarding

## 1. What MindTune Lab is

MindTune Lab is a research and development project exploring Adaptive Cognitive Protocols: structured, audio-driven learning experiences that use minimal visual stimulation, internal speech, and regulated cognitive load. The platform is designed to run cognitive protocols, collect learner responses, and eventually adapt difficulty and timing based on behavioral and (in the future) physiological signals.

The project is intentionally experimental. Its scientific assumptions are stated as falsifiable hypotheses, not architecture axioms.

## 2. What MPE is

**MPE (MindTune Protocol Engine)** is the core runtime that executes cognitive protocols. It is an approved subsystem with a complete v1.1 architecture and Phase 4A implementation specification.

MPE is:

- **Domain-agnostic.** It does not contain Hebrew or language-specific logic.
- **Event-driven.** All runtime state is derived from an immutable event stream.
- **Provider-based.** It delegates rendering, observation, normalization, and evaluation to providers.
- **Safety-first.** Safety instructions override all protocol flow.

MPE is defined by these authoritative documents:

- `docs/MPE_ARCHITECTURE_V1_1.md`
- `docs/MPE_OBJECT_MODEL_V1_1.md`
- `docs/MPE_EVENT_MODEL_V1_1.md`
- `docs/MPE_PROVIDER_BOUNDARIES.md`
- `docs/MPE_ADAPTATION_CONTRACT.md`
- `docs/MPE_CANONICAL_ENUM_REGISTRY.md`
- `docs/MPE_CANONICAL_IDENTIFIER_REGISTRY.md`
- `docs/MPE_OBJECT_EVENT_COVERAGE_MATRIX.csv`
- `docs/specification/v1.1/*.md`
- `docs/specification/v1.1/walkthroughs/*.md`

## 3. What the Hebrew Engine is

The **Hebrew Engine** is an approved domain engine that handles all Hebrew-specific content. MPE delegates every Hebrew correctness decision to it.

The Hebrew Engine:

- Provides `ContentItem` metadata for Hebrew words, forms, roots, and binyans.
- Normalizes Hebrew responses.
- Evaluates Hebrew responses against expected answers.
- Declares accepted variants, scope status, evidence groups, and abstention reasons.

It is defined by:

- `docs/MPE_HEBREW_PROVIDER_CONTRACT.md`
- `data/hebrew/phase3/PHASE_3_FINAL_REPORT.md`
- `data/hebrew/phase3/automatic_gold_100.json`
- `hebrew/` (existing top-level directory, to be migrated into `packages/mpe-hebrew/`)

## 4. Current project phase

**Phase: 4A.6 — Repository Architecture & Development Environment**

Phase 4A implementation specification and Phase 4A.5 walkthroughs are complete. Phase 4B has been approved but **must not begin yet**.

This phase is documentation-only: repository structure, Docker architecture, developer workflow, agent onboarding, project state, next task, and testing strategy.

## 5. Authoritative documents

When in doubt, read these documents in this order:

1. `docs/project/NEXT_TASK.md` — what you are allowed to do now.
2. `docs/project/AGENTS.md` — this document.
3. `docs/project/SYSTEM_ARCHITECTURE.md` — ecosystem overview.
4. `docs/project/REPOSITORY_STRUCTURE.md` — where files live.
5. `docs/project/DEVELOPER_WORKFLOW.md` — how to make changes.
6. `docs/project/TESTING_STRATEGY.md` — how to verify changes.
7. `docs/MPE_ARCHITECTURE_V1_1.md` — MPE design.
8. `docs/MPE_HEBREW_PROVIDER_CONTRACT.md` — Hebrew Engine contract.

## 6. Documents you must never modify without an ADR

The following are immutable unless an ADR is approved:

- `docs/MPE_ARCHITECTURE_V1_1.md`
- `docs/MPE_OBJECT_MODEL_V1_1.md`
- `docs/MPE_EVENT_MODEL_V1_1.md`
- `docs/MPE_PROVIDER_BOUNDARIES.md`
- `docs/MPE_HEBREW_PROVIDER_CONTRACT.md`
- `docs/MPE_ADAPTATION_CONTRACT.md`
- `docs/MPE_CANONICAL_ENUM_REGISTRY.md`
- `docs/MPE_CANONICAL_IDENTIFIER_REGISTRY.md`
- `docs/MPE_OBJECT_EVENT_COVERAGE_MATRIX.csv`
- `docs/research/mpe_ontology_audit_v1/*`
- `data/hebrew/phase3/PHASE_3_FINAL_REPORT.md`
- `data/hebrew/phase3/automatic_gold_100.json`

You may update `docs/project/*.md` and package READMEs without an ADR, provided you do not change subsystem boundaries or approved architecture.

## 7. Current implementation status

- **MPE v1.1 architecture:** approved, specified, walkthrough-verified.
- **Hebrew Engine:** approved contract and dataset; implementation may already exist in `hebrew/`.
- **Repository structure:** target defined in `REPOSITORY_STRUCTURE.md`; current root contains legacy files to migrate.
- **Docker architecture:** specified in `DOCKER_ARCHITECTURE.md`; not implemented.
- **Tests:** strategy defined in `TESTING_STRATEGY.md`; not implemented.
- **Code packages:** not yet organized under `packages/`.

## 8. Prohibited architectural changes

Do **not** do any of the following without an ADR:

1. Redesign MPE objects, events, or provider boundaries.
2. Merge the Hebrew Engine into MPE core.
3. Introduce a new top-level package or service.
4. Change canonical enums or identifiers.
5. Modify the approved Phase 3 Hebrew dataset.
6. Make EEG or physiological signals blocking conditions in Phase 4.
7. Add a UI that replaces the CLI as the source of runtime truth.
8. Implement Docker, CI, databases, or APIs in Phase 4A.6.

## 9. Allowed work in this phase

- Create and edit `docs/project/*.md`.
- Update `.devin/` configuration.
- Update `.gitignore` to reflect target structure.
- Create empty package directories under `packages/` for Phase 4B seeding.
- Add tooling configs (lint, format) if they are purely development setup and do not implement runtime logic.

## 10. Future roadmap

| Phase | Focus |
|---|---|
| 4B | Implement MPE runtime, event store, persistence, CLI, Hebrew provider integration |
| 5A | Adaptation policies and `AdaptationDecision` |
| 5B | BrainLab sensor ingestion and offline `StateEstimate` production |
| 6 | UI/Dashboard, multi-language engines, Piano Engine |
| 7+ | Production orchestration, scalable backends, cloud deployments |

## 11. How to ask for help

- If a task is unclear, read `NEXT_TASK.md` and `DEVELOPER_WORKFLOW.md`.
- If you want to change architecture, propose an ADR in `docs/project/adrs/`.
- If you discover a contradiction in approved documents, document it and ask the user for direction.

## 12. Agent checklist before starting work

- [ ] I have read `NEXT_TASK.md`.
- [ ] I have read `AGENTS.md`.
- [ ] I know which phase the project is in.
- [ ] I know which documents are immutable.
- [ ] I have identified the correct package/directory for my task.
- [ ] I have a `todo_write` plan.
- [ ] I will not implement Phase 4B code unless explicitly told to.
