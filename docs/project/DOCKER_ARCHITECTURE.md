# MindTune Lab — Docker Architecture

## 1. Purpose

This document specifies the Docker architecture for MindTune Lab. It defines containers, networks, volumes, and persistent storage. It does **not** contain Dockerfiles, compose files, or runtime configuration.

The architecture is designed to support deterministic, reproducible development and testing while keeping MPE, the Hebrew Engine, and future engines isolated in their own service boundaries.

## 2. Design principles

1. **One concern per container.** Each container runs a single logical service (runtime, event store, provider, domain engine, test runner).
2. **Domain engines are isolated.** The Hebrew Engine and future engines run in separate containers from MPE core.
3. **Event store is central.** All state-changing runtime events flow through the event-store container.
4. **Volumes are explicit.** Persistent data is stored in named volumes; generated cache is ephemeral.
5. **Development parity.** Development and test containers use the same base images as production targets.

## 3. Container inventory

### 3.1 Core platform containers

| Container | Responsibility | Base image strategy | Notes |
|---|---|---|---|
| `mpe-runtime` | Executes MPE sessions and protocol logic | Python slim | Main runtime service. |
| `mpe-event-store` | Append-only event storage and validation | Python slim or dedicated storage image | May start as SQLite/flat-file; later migrate to PostgreSQL or event-store backend. |
| `mpe-persistence` | Snapshot and registry persistence | Python slim | Handles `ContentItem`, fixture, and snapshot storage. |
| `mpe-scheduler` | Item selection and scheduling policy | Python slim | May be co-located with `mpe-runtime` in early Phase 4B. |

### 3.2 Provider containers

| Container | Responsibility | Base image strategy | Notes |
|---|---|---|---|
| `mpe-renderer-hebrew` | Hebrew text-to-speech and media rendering | Python slim with TTS dependencies | Depends on Hebrew engine data. |
| `mpe-renderer-audio` | Generic audio playback rendering | Python slim | Future. |
| `mpe-provider-keyboard` | Typed input observation provider | Python slim | May run as a sidecar or local process. |
| `mpe-provider-microphone` | Voice sample capture (future) | Python slim with audio deps | Future. |

### 3.3 Domain engine containers

| Container | Responsibility | Base image strategy | Notes |
|---|---|---|---|
| `mpe-engine-hebrew` | Hebrew `ContentItem` provision, normalization, evaluation | Python slim with Hebrew NLP dependencies | Approved Hebrew Engine boundary. |
| `mpe-engine-piano` | Piano phrase provision and evaluation (future) | TBD | Future placeholder. |
| `mpe-engine-italian` | Italian language engine (future) | TBD | Future placeholder. |

### 3.4 Application containers

| Container | Responsibility | Base image strategy | Notes |
|---|---|---|---|
| `mpe-cli` | Command-line interface | Python slim | May be invoked as a one-shot container or local binary. |
| `mpe-ui` (future) | Web or mobile UI | Node or Python | Future; screen is secondary by design. |
| `mpe-dashboard` (future) | Analytics dashboard | Node or Python | Future; read-only. |

### 3.5 Analytics and research containers

| Container | Responsibility | Base image strategy | Notes |
|---|---|---|---|
| `brainlab` (future) | EEG/sensor preprocessing and offline analysis | Python with scientific Python stack | Future; diagnostic only in Phase 4. |
| `mpe-research-notebook` (future) | Jupyter notebooks for research | Jupyter datascience image | Future. |

### 3.6 Test containers

| Container | Responsibility | Base image strategy | Notes |
|---|---|---|---|
| `mpe-test-unit` | Runs unit tests for `packages/*` | Python dev image | One-shot container. |
| `mpe-test-integration` | Runs integration tests against composed services | Python dev image | Depends on `mpe-runtime`, `mpe-event-store`, `mpe-persistence`, `mpe-engine-hebrew`. |
| `mpe-test-replay` | Validates event-stream replay for sample sessions | Python dev image | Loads events and rebuilds session state. |
| `mpe-test-e2e` | End-to-end smoke tests | Python dev image | Uses `compose/testing.yaml`. |

### 3.7 Development containers

| Container | Responsibility | Base image strategy | Notes |
|---|---|---|---|
| `mpe-dev` | General development shell with all packages editable | Python dev image | Mounts repository as a volume. |
| `mpe-dev-hebrew` | Development shell for Hebrew Engine | Python dev image with Hebrew deps | Mounts `packages/mpe-hebrew/` and `data/hebrew/`. |
| `mpe-dev-docs` | Documentation preview and lint | Node or Python with mkdocs | Future. |

## 4. Networks

| Network | Members | Purpose |
|---|---|---|
| `mpe-core` | `mpe-runtime`, `mpe-event-store`, `mpe-persistence`, `mpe-scheduler` | Internal MPE runtime communication. |
| `mpe-providers` | `mpe-runtime`, `mpe-renderer-*`, `mpe-provider-*` | Provider adapter communication. |
| `mpe-domain` | `mpe-runtime`, `mpe-engine-hebrew`, `mpe-engine-*` | Domain engine communication. |
| `mpe-research` | `brainlab`, `mpe-research-notebook`, `mpe-runtime` (read-only) | Research and analytics access. |
| `mpe-public` | `mpe-ui`, `mpe-dashboard`, `mpe-cli` (if exposed) | External-facing application network. |

## 5. Volumes and persistent storage

### 5.1 Named volumes

| Volume | Containers | Purpose |
|---|---|---|
| `mpe-event-store-data` | `mpe-event-store` | Persistent event logs and indices. |
| `mpe-persistence-data` | `mpe-persistence` | Snapshots, registries, and derived state. |
| `mhebrew-data` | `mpe-engine-hebrew`, `mpe-renderer-hebrew` | Hebrew engine models, pronunciation data, and cached `ContentItem` metadata. |
| `mpe-media-cache` | `mpe-renderer-*` | Rendered media cache for fast replay. |
| `mpe-provider-cache` | `mpe-provider-*` | Provider-specific transient caches. |

### 5.2 Bind mounts (development only)

| Source | Target container | Purpose |
|---|---|---|
| `packages/` | `mpe-dev`, `mpe-runtime` | Editable source code. |
| `data/` | `mpe-engine-hebrew`, `mpe-persistence` | Read-only data and fixtures. |
| `docs/` | `mpe-dev-docs` | Documentation source. |

### 5.3 Ephemeral storage

| Path | Containers | Purpose |
|---|---|---|
| `/tmp/mpe-runtime` | `mpe-runtime` | Temporary state during session execution. |
| `/tmp/mpe-render-cache` | `mpe-renderer-*` | Short-lived rendered media. |
| `/tmp/mpe-tests` | `mpe-test-*` | Test artifacts and logs. |

## 6. Image versioning strategy

1. Base images are pinned by digest in `infrastructure/docker/base/` lock files.
2. Application images are tagged with the Git commit short SHA and a semantic version.
3. Provider and engine images include their contract version in the image label (e.g., `mpe.engine.hebrew.contract=v1.1`).
4. Compose files reference image tags, not `latest`.

## 7. Security boundaries

| Boundary | Rule |
|---|---|
| Domain engines | No outbound network except to `mpe-core` and `mpe-domain`. |
| Event store | Only `mpe-runtime` and `mpe-persistence` may write; others read-only. |
| Provider adapters | No access to `mpe-persistence` or `mpe-event-store` data volumes. |
| Research containers | Read-only access to anonymized exports; no write access to runtime state. |

## 8. Future services

The following containers are planned but not part of Phase 4B:

- `mpe-engine-piano` — piano performance evaluation.
- `mpe-engine-italian` — additional language engine.
- `brainlab` — EEG and sensor ingestion.
- `mpe-research-notebook` — interactive research notebooks.
- `mpe-ui` and `mpe-dashboard` — user interfaces.
- `mpe-metrics` — metrics collection and export (Prometheus/OpenTelemetry, future).

## 9. Migration path from current state

The current repository contains legacy Python files at the root and a `hebrew/` top-level directory. The Docker architecture does not require moving these files immediately, but Phase 4B implementation should progressively relocate them:

1. `hebrew/` -> `packages/mpe-hebrew/` or `data/hebrew/` (depending on file type).
2. `server.py`, `mindtune_app.py` -> `packages/mpe-server/` or `packages/mpe-cli/`.
3. `app.js`, `index.html`, `styles.css` -> `packages/mpe-ui/` (future) or archive.
4. `.venv*` directories -> removed from version control and excluded by `.gitignore`.

## 10. No implementation yet

This document is architecture-only. No Dockerfiles, `.dockerignore`, compose files, or build scripts are created in Phase 4A.6. Implementation begins in Phase 4B with the first package layout and base image definitions.
