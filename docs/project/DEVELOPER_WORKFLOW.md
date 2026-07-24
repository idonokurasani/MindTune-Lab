# MindTune Lab — Developer Workflow

## 1. Purpose

This document describes how development proceeds in the MindTune Lab repository. It covers feature introduction, branching, documentation, ADRs, testing, and releases. It is binding for human developers and AI agents.

## 2. Development model

MindTune Lab uses a **trunk-based** workflow with short-lived feature branches and ADR-driven architectural changes.

```text
main
  │
  ├── feature/mpe-<feature-name>
  ├── feature/hebrew-<feature-name>
  ├── docs/<doc-name>-update
  └── adr/<adr-number>-<title>
```

## 3. Feature introduction

### 3.1 Before writing code

1. Confirm the feature is in scope for the current phase by reading `NEXT_TASK.md`.
2. Identify the owning package and directory from `REPOSITORY_STRUCTURE.md`.
3. Check `AGENTS.md` for prohibited architectural changes.
4. If the feature touches architecture, write or update an ADR.
5. Update documentation before or alongside code.

### 3.2 During implementation

1. Work in the correct `packages/<package>/` directory.
2. Follow the package's `README.md` and coding conventions.
3. Add tests in the package `tests/` directory or `tests/` top-level directory as appropriate.
4. Run unit tests and integration tests locally.
5. Keep commits small and focused.

### 3.3 After implementation

1. Update relevant documentation (`docs/specification/`, `docs/project/`, package README).
2. Run the full test suite.
3. Open a pull request with a clear description and linked ADR if applicable.
4. Squash or rebase as requested by maintainers.

## 4. Branch strategy

| Branch type | Naming | Purpose | Lifetime |
|---|---|---|---|
| `main` | `main` | Stable, always deployable / runnable | Permanent |
| Feature | `feature/<area>-<short-desc>` | One feature or bugfix | Days to weeks |
| Documentation | `docs/<short-desc>` | Documentation-only changes | Days |
| ADR | `adr/<number>-<title>` | Architectural decision records | Days |
| Hotfix | `hotfix/<issue>` | Critical fixes against `main` | Hours to days |

### 4.1 Branch rules

- `main` is protected. All changes go through pull request.
- Feature branches must be rebased on `main` before merging.
- No force-pushing to `main`.
- No long-lived feature branches. Split large work into smaller, reviewable pieces.

## 5. Documentation updates

### 5.1 When to update documentation

| Change | Documents to update |
|---|---|
| New object or event | `MPE_OBJECT_MODEL_V1_1.md`, `MPE_EVENT_MODEL_V1_1.md`, `SCHEMA_VALIDATION_RULES.md` (requires ADR) |
| New provider contract | `MPE_PROVIDER_BOUNDARIES.md`, domain contract (requires ADR) |
| New package | `REPOSITORY_STRUCTURE.md`, `SYSTEM_ARCHITECTURE.md` |
| New Docker service | `DOCKER_ARCHITECTURE.md` |
| New test type | `TESTING_STRATEGY.md` |
| New phase | `PROJECT_STATE.md`, `NEXT_TASK.md` |

### 5.2 Immutable documents

The following documents are immutable without an ADR:

- `docs/MPE_ARCHITECTURE_V1_1.md`
- `docs/MPE_OBJECT_MODEL_V1_1.md`
- `docs/MPE_EVENT_MODEL_V1_1.md`
- `docs/MPE_PROVIDER_BOUNDARIES.md`
- `docs/MPE_HEBREW_PROVIDER_CONTRACT.md`
- `docs/MPE_ADAPTATION_CONTRACT.md`
- `docs/MPE_CANONICAL_ENUM_REGISTRY.md`
- `docs/MPE_CANONICAL_IDENTIFIER_REGISTRY.md`
- `docs/research/mpe_ontology_audit_v1/*` (historical artifacts)
- `data/hebrew/phase3/PHASE_3_FINAL_REPORT.md`
- `data/hebrew/phase3/automatic_gold_100.json`

### 5.3 Mutable project documents

The `docs/project/` documents (including this one) are updated as the project evolves. They do not require an ADR unless they change subsystem boundaries or approved architecture.

## 6. ADR workflow

### 6.1 When an ADR is required

An ADR is required for:

- Changing an approved MPE object or event.
- Introducing a new top-level package or service.
- Changing provider boundaries.
- Changing the Hebrew Engine contract.
- Adding a new canonical enum or identifier.
- Changing persistence or Docker architecture boundaries.

### 6.2 ADR format

ADRs live in `docs/project/adrs/` and follow the template in `docs/project/ADR_TEMPLATE.md` (to be created when the first ADR is needed).

Each ADR includes:

- Context and problem statement
- Decision
- Consequences
- Alternatives considered
- Affected documents
- Status (proposed / accepted / rejected / superseded)

### 6.3 ADR approval

- ADRs are opened as pull requests.
- Architecture-affecting ADRs require at least one human maintainer approval.
- Approved ADRs are merged into `main` and the affected documents are updated.

## 7. Testing workflow

### 7.1 Local testing

1. Run package unit tests:
   ```bash
   # Target command (future)
   pytest packages/<package>/tests
   ```
2. Run integration tests with local dependencies.
3. Run event replay tests for sample sessions.
4. Run static checks (lint, type check, format) from `tools/`.

### 7.2 Pre-commit

Pre-commit hooks (future) will run:

- Lint and format
- Unit tests for changed packages
- Documentation link checks
- Schema validation for fixtures

### 7.3 CI testing (future)

CI will run:

- Unit tests for all packages
- Integration tests in Docker compose test environment
- Event replay tests against committed sample sessions
- Hebrew provider tests

See `TESTING_STRATEGY.md` for detailed test categories.

## 8. Release workflow

### 8.1 Versioning

- MPE and packages use semantic versioning independently.
- `ProgramVersion` and `ProtocolVersion` are versioned by content checksum, not release tag.
- Docker images are tagged with Git SHA and package version.

### 8.2 Release steps

1. Update `PROJECT_STATE.md` and `CHANGELOG.md` (future).
2. Tag the release with the package/version being released.
3. Build and smoke-test Docker images.
4. Run full integration and replay tests.
5. Merge release branch to `main`.
6. Publish release notes.

## 9. AI-agent workflow

AI agents (Devin, Codex, etc.) follow the same workflow as human developers, with these additions:

1. **Read `AGENTS.md` first** before any work.
2. **Read `NEXT_TASK.md`** to confirm current objective and forbidden scope.
3. **Do not modify immutable documents** without an approved ADR.
4. **Use the `todo_write` tool** to track progress and expose it to the user.
5. **Prefer existing conventions** in the package being modified.
6. **Ask for confirmation** before destructive operations (deleting files, rewriting history, dropping data).
7. **Propose ADRs** rather than silently changing architecture.

## 10. Communication

- Technical questions: open a discussion or issue in the repository.
- Architecture changes: open an ADR.
- Bugs: open an issue with reproduction steps and affected package.
- Phase planning: update `PROJECT_STATE.md` and `NEXT_TASK.md`.
