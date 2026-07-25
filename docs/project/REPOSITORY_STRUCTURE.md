# MindTune Lab — Repository Structure

## 1. Purpose

This document defines the canonical directory tree for MindTune Lab. It explains the purpose, ownership, modification rules, and dependencies of each directory.

The repository is currently in a pre-reorganization state. Some legacy files and directories exist at the root and will be migrated into this structure during Phase 4B. This document is the target state; `PROJECT_STATE.md` describes the current deviations.

## 2. Top-level target structure

```text
mindtune_console/
├── .devin/                    # Devin AI-agent skills and configuration
├── .github/                   # GitHub templates and workflows (future)
├── bin/                       # Executable entry-point scripts
├── compose/                   # Docker Compose specifications (future)
├── data/                      # Curated datasets and registries
├── docs/                      # All project documentation
├── infrastructure/            # Docker, infrastructure-as-code, secrets (future)
├── packages/                  # All implementation packages (monorepo)
├── research/                  # Analysis notebooks and experimental scripts (future)
├── repos/                     # External dependency clones / submodules
├── runtime/                   # Runtime-generated artifacts (gitignored)
├── scripts/                   # Development and maintenance scripts
├── services/                  # Docker service definitions (future)
├── tests/                     # Top-level integration and e2e tests
├── tools/                     # Lint, format, codegen, and other dev tools
├── AGENTS.md                  # AI-agent onboarding
├── LICENSE                    # License (future)
├── README.md                  # Project-level README
├── pyproject.toml             # Python workspace metadata (future)
└── uv.lock / requirements.txt # Lock files (future)
```

## 3. Directory reference

### `.devin/`

- **Purpose:** Devin skills, agent memory, and project-specific configuration.
- **Owner:** AI-agent tooling.
- **Modifiable by:** Devin, human maintainers.
- **Stability:** stable.
- **Dependencies:** none.
- **Future evolution:** May grow as more agent skills are added.

### `.github/`

- **Purpose:** Pull-request templates, issue templates, CI workflows.
- **Owner:** Repository maintainers.
- **Modifiable by:** Human maintainers, Devin with approval.
- **Stability:** experimental in Phase 4.
- **Dependencies:** none.
- **Future evolution:** CI workflows added in Phase 5+.

### `bin/`

- **Purpose:** Executable entry points for the CLI and admin tools.
- **Owner:** Core platform team.
- **Modifiable by:** Developers working on CLI or runtime.
- **Stability:** stable.
- **Dependencies:** `packages/mpe`, `packages/cli`.
- **Future evolution:** New entry points added per application.

### `compose/`

- **Purpose:** Docker Compose files for local development, testing, and production.
- **Owner:** Infrastructure maintainers.
- **Modifiable by:** Developers with ADR approval for infrastructure changes.
- **Stability:** experimental until Phase 5.
- **Dependencies:** `infrastructure/`, `services/`.
- **Future evolution:** `development.yaml`, `testing.yaml`, `production.yaml`.

### `data/`

- **Purpose:** Immutable and curated datasets, content registries, and gold-standard data.
- **Owner:** Domain experts and data maintainers.
- **Modifiable by:** Domain engine owners; human approval required for gold data changes.
- **Stability:** immutable for released datasets; experimental for in-progress collections.
- **Dependencies:** none at rest; consumed by domain engines and tests.
- **Future evolution:** New `data/<language>/`, `data/eeg/`, `data/external/` directories as engines expand.

Current contents:

- `data/hebrew/phase3/` — approved Phase 3 Hebrew dataset. Immutable.
- `data/external/` — third-party datasets or imports. Stable.

### `docs/`

- **Purpose:** All project documentation.
- **Owner:** Documentation maintainers.
- **Modifiable by:** All developers, with ADR for architectural changes.
- **Stability:** mixed; see `AGENTS.md` for immutable documents.
- **Dependencies:** none.
- **Future evolution:** New `docs/specification/vX.Y/` directories as specifications evolve.

Current contents:

- `docs/project/` — project architecture and onboarding (this task).
- `docs/research/` — historical research and audit artifacts. Immutable unless superseded by ADR.
- `docs/specification/v1.1/` — Phase 4A implementation specification. Stable.
- `docs/MPE_*.md` — approved MPE v1.1 architecture. Immutable unless ADR.

### `infrastructure/`

- **Purpose:** Docker base images, infrastructure-as-code templates, secret templates.
- **Owner:** Infrastructure maintainers.
- **Modifiable by:** Devin or humans with ADR approval.
- **Stability:** experimental until Phase 5.
- **Dependencies:** `compose/`, `services/`.
- **Future evolution:** Terraform, Kubernetes manifests, secrets management.

### `packages/`

- **Purpose:** All implementation code in a monorepo layout.
- **Owner:** Core platform and domain teams.
- **Modifiable by:** Feature owners.
- **Stability:** stable structure; individual packages evolve.
- **Dependencies:** varies by package.
- **Future evolution:** New packages added for new engines, applications, and analytics.

Target contents:

```text
packages/
├── mpe/                   # MPE runtime core
│   ├── src/mpe/
│   └── tests/
├── mpe-event-store/       # Event-store backend(s)
│   ├── src/mpe_event_store/
│   └── tests/
├── mpe-persistence/       # Snapshot and persistence logic
│   ├── src/mpe_persistence/
│   └── tests/
├── mpe-scheduler/         # Scheduling policies and item selection
│   ├── src/mpe_scheduler/
│   └── tests/
├── mpe-cli/               # Command-line interface
│   ├── src/mpe_cli/
│   └── tests/
├── mpe-hebrew/            # Hebrew provider, normalizer, evaluator
│   ├── src/mpe_hebrew/
│   └── tests/
├── mpe-piano/             # Future Piano Engine (placeholder)
│   ├── src/mpe_piano/
│   └── tests/
├── brainlab/              # Future EEG/sensor subsystem (placeholder)
│   ├── src/brainlab/
│   └── tests/
└── shared/                # Cross-package utilities (minimal)
    ├── src/mpe_shared/
    └── tests/
```

### `research/`

- **Purpose:** Analysis notebooks, experimental scripts, and ad-hoc reports.
- **Owner:** Research team.
- **Modifiable by:** Researchers, data scientists.
- **Stability:** experimental.
- **Dependencies:** `packages/`, `data/`.
- **Future evolution:** May be split into separate repository if it grows large.

### `repos/`

- **Purpose:** External dependencies cloned as git submodules or vendored code.
- **Owner:** Infrastructure maintainers.
- **Modifiable by:** Devin/humans with explicit approval; upstream updates only.
- **Stability:** stable for pinned versions; experimental for bleeding-edge clones.
- **Dependencies:** external upstream repositories.
- **Future evolution:** Replaced by package managers as dependencies mature.

### `runtime/`

- **Purpose:** Runtime-generated artifacts (logs, caches, media, local databases).
- **Owner:** Runtime.
- **Modifiable by:** Runtime processes only.
- **Stability:** generated.
- **Dependencies:** `.gitignore` must exclude this directory.
- **Future evolution:** May be replaced by Docker volumes in production.

### `scripts/`

- **Purpose:** Development, maintenance, and migration scripts.
- **Owner:** Core platform team.
- **Modifiable by:** Developers.
- **Stability:** stable.
- **Dependencies:** `packages/`, `data/`.
- **Future evolution:** Scripts may be promoted to `bin/` or `tools/`.

### `services/`

- **Purpose:** Docker service definitions (one per container/service).
- **Owner:** Infrastructure maintainers.
- **Modifiable by:** Devin/humans with ADR for service changes.
- **Stability:** experimental until Phase 5.
- **Dependencies:** `infrastructure/`, `compose/`.
- **Future evolution:** One subdirectory per service (event-store, persistence, hebrew-engine, etc.).

### `tests/`

- **Purpose:** Top-level integration, end-to-end, and smoke tests.
- **Owner:** QA / core platform team.
- **Modifiable by:** Developers adding integration coverage.
- **Stability:** stable.
- **Dependencies:** `packages/`, `data/`, `compose/` for e2e.
- **Future evolution:** Grows as more subsystems integrate.

### `tools/`

- **Purpose:** Lint, format, codegen, schema validation, and other developer tools.
- **Owner:** Core platform team.
- **Modifiable by:** Developers.
- **Stability:** stable.
- **Dependencies:** none.
- **Future evolution:** CI may run these tools automatically.

## 4. Stability classification

| Directory | Classification | Notes |
|---|---|---|
| `.devin/` | stable | Agent configuration. |
| `.github/` | experimental | Not yet in use. |
| `bin/` | stable | Entry points. |
| `compose/` | experimental | Future Docker orchestration. |
| `data/hebrew/phase3/` | immutable | Approved Phase 3 dataset. |
| `docs/project/` | stable | Architecture documents. |
| `docs/research/` | immutable | Historical artifacts. |
| `docs/specification/v1.1/` | stable | Phase 4A spec. |
| `docs/MPE_*.md` | immutable | Approved MPE v1.1. |
| `infrastructure/` | experimental | Future. |
| `packages/` | stable | Structure fixed; packages evolve. |
| `research/` | experimental | Analysis and experiments. |
| `repos/` | stable | Pinned external deps. |
| `runtime/` | generated | Gitignored. |
| `scripts/` | stable | Dev scripts. |
| `services/` | experimental | Future Docker services. |
| `tests/` | stable | Integration tests. |
| `tools/` | stable | Dev tooling. |

## 5. Current deviations

The following files and directories currently exist at the repository root and are not yet in the target structure. They are considered legacy or in-progress and will be migrated during Phase 4B:

| Current location | Target or disposition |
|---|---|
| `app.js` | Legacy prototype UI; candidate for `packages/mpe-ui/` or removal. |
| `index.html` | Legacy prototype UI; candidate for `packages/mpe-ui/` or removal. |
| `server.py` | Legacy prototype server; candidate for `packages/mpe-server/` or removal. |
| `styles.css` | Legacy prototype UI styling; candidate for `packages/mpe-ui/` or removal. |
| `mindtune_app.py` | Legacy entry point; migrate to `bin/` or `packages/mpe-cli/`. |
| `azure_speech.py` | Speech provider prototype; migrate to `packages/mpe-providers/` or `packages/mpe-hebrew/`. |
| `oura_api.py` | Sensor/third-party API prototype; loads credentials from a local `.oura_credentials` file (gitignored). Use `.oura_credentials.example` as a template. Migrate to `packages/brainlab/` or `research/` in future phases. |
| `help_profiler.py` | Diagnostic script; migrate to `tools/` or `research/`. |
| `hebrew/` (top-level) | Approved Hebrew Engine workspace; target `packages/mpe-hebrew/` or `data/hebrew/` depending on contents. |
| `mantra/` | Existing content; evaluate for `data/` or `packages/content-mantra/`. |
| `.venv*`, `__pycache__`, `.pytest_cache` | Generated artifacts; ensure `.gitignore` excludes. |

## 6. Ownership summary

| Area | Owner |
|---|---|
| MPE core | Core platform team |
| Event store | Core platform team |
| Persistence | Core platform team |
| Scheduler | Core platform team |
| CLI | Core platform team |
| Hebrew Engine | Hebrew/domain team |
| Piano Engine (future) | Piano/domain team |
| BrainLab (future) | Research/sensor team |
| Docker / infrastructure | Infrastructure maintainers |
| Documentation | All developers; ADR for architecture changes |
| Data | Domain experts |
| Research | Research team |
