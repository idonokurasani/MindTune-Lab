# Phase 1 — Scientific Reproducibility Architecture Audit

**Status:** read-only audit. No production code was modified.
**Repository:** `idonokurasani/MindTune-Lab` (local mirror of `mindtune_console`)
**Audited revision:** `78b984c656d5555b5405163886f5ea84631a6029`
**Audit date:** 2026-07-27
**Scope:** current state of the MPE runtime relative to Milestone 1 ("Scientific provenance foundation") of the Scientific Reproducibility Roadmap.

---

## 1. Purpose and method

This document records what the repository actually contains today, measured against the roadmap's Workstream A requirements (event integrity, replay verification, protocol provenance) and against the architectural principles in roadmap sections 2.1–2.4.

Method:

1. Static reading of `packages/mpe/src/mpe/**` (4 330 lines of Python across 32 source modules).
2. Reading of the persisted SQLite schema and canonical serializer.
3. Reading of `packages/mpe/tests/**` (162 tests) with attention to replay, persistence, and serialization coverage.
4. Reading of `docs/project/PROJECT_STATE.md`, `docs/project/NEXT_TASK.md`, `docs/implementation/phase4c1/*`, `docs/implementation/phase4c2/*`.
5. Execution of the existing test, lint, and type-check commands (section 8).

No assumption was carried over from the roadmap text: every claim below is anchored to a file and, where useful, a line region.

---

## 2. Current architecture (as built)

### 2.1 Event envelope

`packages/mpe/src/mpe/events.py` defines a single frozen `Event` dataclass with a fixed envelope:

| Field | Present | Notes |
|---|---|---|
| `event_id` | yes | `EventID`, UUID4 via `make_id` |
| `event_type` | yes | constrained to `SUPPORTED_EVENT_TYPES` (24 types) |
| `schema_version` | yes | constrained to `SUPPORTED_SCHEMA_VERSIONS = {"1.1"}` |
| `session_id` | yes | stream identity |
| `session_sequence_number` | yes | monotonic within the session stream |
| `protocol_version_id` | yes | on every event |
| `timestamp` | yes | deterministic session clock (`Clock`), **not** UTC wall time |
| `wallclock_at` | yes, optional | nullable; not populated by the runtime today |
| `component` / `component_version` | yes | writer identity and writer version |
| `provenance` | yes | list of causally prior `EventID`s |
| `payload` | yes | deep-copied and exposed as `MappingProxyType` |
| `sensitive` / `data_classification` | yes | privacy classification |
| `trial_id` / `block_id` / `correlation_id` | yes, optional | |
| `quality_flags` | yes | free-form list of strings |

The envelope is immutable at the Python level: `__post_init__` freezes `payload`, `provenance`, and `quality_flags`.

### 2.2 Storage

Two implementations satisfy the shared `EventStore` protocol declared in `packages/mpe/src/mpe/event_store.py`:

- `InMemoryEventStore` — append-only dict of streams.
- `SQLiteEventStore` (`packages/mpe/src/mpe/persistence/store.py`) — WAL-mode SQLite, single table `events`, `PRAGMA user_version = 1`, `UNIQUE (session_id, session_sequence_number)`, `BEGIN IMMEDIATE` transactions, single-writer lock, batch append with contiguity checks.

Serialization (`packages/mpe/src/mpe/persistence/serializer.py`) is already canonical in the JSON sense: `sort_keys=True`, `separators=(",", ":")`, `ensure_ascii=False`, with a deterministic encoder for `Identifier` and `CanonicalEnum`.

Append-time invariants enforced by both stores:

- unknown `event_type` rejected;
- full payload-schema validation via `validate_event`;
- duplicate `event_id` rejected;
- optimistic concurrency via `expected_version`;
- strictly increasing `session_sequence_number`;
- non-decreasing `timestamp`;
- provenance existence within the same session.

Read-time invariants (`SQLiteEventStore.read`, `.all_events`): every row is re-validated with `validate_event(event, previous_events=events)`, which re-checks ordering and provenance causality on load.

### 2.3 Replay and projection

`packages/mpe/src/mpe/replay.py` (32 lines) is intentionally thin: read the stream, fold each event into a fresh `RuntimeState`, wrap any failure as `ReplayError` annotated with the failing sequence number.

`packages/mpe/src/mpe/aggregates.py` implements `RuntimeState` as a pure left fold over the event stream with one handler per event type, and `as_dict()` returns a deterministic, comparable projection. There is **no** persisted snapshot mechanism anywhere in the codebase — `as_dict()` is an in-memory comparison surface only, and `ItemHistorySnapshotID` is a scheduler-context identifier, not a state cache. This matches roadmap §2.2 by construction.

Derived reporting is also event-derived: `packages/mpe/src/mpe/protocol/summary.py` and `summary_recognition.py` build `ProtocolSummary` objects exclusively by walking persisted events (`summary_walk.walk_session`).

### 2.4 Providers

`ProviderSet` (`packages/mpe/src/mpe/providers.py:395`) groups six typed provider protocols: `Renderer`, `ObservationProvider`, `ResponseInterpreter`, `DomainNormalizer`, `Evaluator`, `Scheduler`. Each exposes `capabilities()`, and `ProviderSet.check_versions()` compares reported provider versions against a protocol's declared dependency versions, raising `UnsupportedProviderVersionError` on mismatch.

Important limitation: `check_versions` compares against **hard-coded provider keys** (`mock_renderer`, `mock_keyboard`, `mock_interpreter`, `mock_normalizer`, `mock_evaluator`, `mock_scheduler`). It is a mock-oriented check, not a general provider-version registry, and the verified versions are **not** written into the event stream as a session-level provenance record.

### 2.5 Protocols

Two protocols exist (Phase 4C.1 Immediate Recall, Phase 4C.2 Recognition) sharing `protocol/trial_pipeline.py`, which emits the invariant trial event flow while keeping cognitive semantics in protocol-specific modules. `bounded_repeat.py` implements the bounded adaptation rule. Latency is captured per item and explicitly documented as an adaptation proxy, not as a behavioral measure.

### 2.6 What does not exist

Verified absent from `packages/mpe`:

- no EEG, physiological, sensor, or device-profile code (`grep -i eeg packages/mpe/src` → 0 matches; EEG appears only in the legacy root prototype `server.py` and in narrative docs);
- no BIDS export;
- no statistical, reaction-time, SDT, or power-analysis module;
- no preregistration or study-manifest artifact;
- no policy-version registry of any kind;
- no snapshot store (correctly, per §2.2).

---

## 3. Gap analysis against Workstream A

### A1 — Event integrity

| Roadmap requirement | Present | Evidence / gap |
|---|---|---|
| Canonical event serialization | **Yes** | `serializer._to_json` is deterministic (sorted keys, fixed separators). It is used for the `payload`, `provenance`, and `quality_flags` columns; there is no canonical form of the *whole* event yet. |
| Stable event identifiers | **Yes** | `EventID` UUID4, `PRIMARY KEY` in SQLite, duplicate-rejecting in memory. Identifiers are random, not content-derived — acceptable, but they do not themselves bind content. |
| Monotonic sequence numbers per stream | **Yes** | Enforced on append (strictly increasing), on batch append (contiguous), and re-checked on read. |
| Previous-event digest | **No** | No `previous_digest` column, field, or computation. |
| Current-event SHA-256 digest | **No** | `hashlib` is not imported anywhere in `packages/mpe/src`. |
| Schema version | **Yes** | `schema_version` on the envelope and column; unsupported values raise `UnknownSchemaVersionError`. |
| Writer / runtime version | **Partial** | `component` + `component_version` exist per event, but the value is a default literal (`"runtime"`, `"1.0.0"`) rather than a resolved software revision. |
| Recorded UTC timestamp | **No (misleading today)** | `timestamp` is a deterministic session clock starting at `1.0` and advancing by `0.1`. `wallclock_at` exists in the envelope, the schema, and the serializer, but the runtime never populates it. Nothing in a stored session records when it actually happened. |
| Optional source-device timestamp | **No** | No device-time field; no device concept. |
| Integrity verification command | **Partial** | `mpe validate-store` (`cli.py:290`) exists and re-replays every session, so it detects schema, ordering, and provenance violations. It cannot detect content mutation of an individual event, because there is nothing to compare a payload against. |

**Assessment.** The store is append-only *by discipline and by validation*, not *tamper-evident*. Any actor with write access to the SQLite file can edit a payload in place and the store will accept it on read, provided ordering and payload schema still validate. This is the single largest Milestone 1 gap.

### A2 — Replay verification

| Roadmap requirement | Present | Evidence / gap |
|---|---|---|
| Same stream → same projection | **Yes** | `tests/test_replay.py::test_repeated_replay_is_equal`, `test_full_replay_matches_live_state`; `tests/persistence/test_replay_from_disk.py::test_live_equals_replay_from_disk` compares live state to a cross-process replay. |
| Rebuild from an empty database | **Partial** | `persistence/restart_demo.py` and the restart-recovery tests demonstrate a fresh-process rebuild from a persisted file, but there is no test that constructs an empty DB, ingests an exported stream, and asserts projection equality. |
| Snapshots discardable | **N/A / satisfied** | No snapshots exist. This should be recorded as an explicit architectural decision so it is not "solved" later by adding a second source of truth. |
| Corrupted or reordered events detected | **Partial** | Reordering is detected (`EventOrderingError` on read via `validate_event(..., previous_events=...)`); corrupt JSON is detected (`ReplayError` in `from_row`); **semantic content tampering is not detected**. |
| Unsupported schema versions fail explicitly | **Yes** | `UnknownSchemaVersionError`; DB-level `PRAGMA user_version` mismatch raises `ValidationError`. |

### A3 — Protocol provenance

Each event carries `protocol_version_id`. `session_started` carries `program_version_id`, `learner_id`, and `random_seed`. That is the full extent of recorded provenance.

| Required provenance element | Present |
|---|---|
| Protocol identifier and version | Partial — `protocol_version_id` only; no separate logical `protocol_id` in the stream |
| Curriculum identifier and version | No |
| Experimental condition | No |
| Randomization seed or allocation reference | Yes — `random_seed` on `session_started` (default `"seed_0"`) |
| Stimulus-set version | Partial — fixture assets are version-pinned on `stimulus_requested`/`stimulus_ready`; there is no session-level stimulus-set version |
| Scoring-policy version | No |
| RT-policy version | No |
| Signal-processing-policy version | No |
| Software revision | No — no VCS revision is captured anywhere |
| Provider and device versions | Partial — checked at runtime by `ProviderSet.check_versions`, never persisted |

---

## 4. Alignment with roadmap architectural principles

| Principle | Verdict | Comment |
|---|---|---|
| §2.1 One authoritative event history | **Aligned** | `EventStore` is the only record. The roadmap's instruction not to build a parallel audit-log subsystem is directly compatible with the current design: integrity must be added *inside* `packages/mpe/src/mpe/persistence/`. |
| §2.2 Replay before snapshots | **Aligned** | No snapshot subsystem exists; all projections and summaries are folds over events. |
| §2.3 Raw / derived / interpreted separated | **Partially aligned** | The event vocabulary already separates `observation_received` → `captured_response_created` → `response_interpreted` → `domain_response_normalized` → `evaluation_completed`, each linked by `provenance`. This is a strong foundation. What is missing is the *retrospective analysis* layer: there is no event or record type for derived analysis outputs, and therefore no place today where an exclusion or transformation could be recorded without touching raw trials. |
| §2.4 Versioned scientific policy | **Not aligned** | Analytical choices are currently embedded in mutable code: the bounded-repeat rule (`repeat_cap`, `latency_bound`) lives in protocol construction, and summary interpretation lives in `summary.py`. No policy identity, no policy version, no registry. |

---

## 5. Risks found during the audit

| # | Risk | Severity | Evidence |
|---|---|---|---|
| R1 | Stored events are mutable in practice; no cryptographic binding of content | High | No digest fields; SQLite file is directly editable |
| R2 | No wall-clock record of when a session occurred | High | `Clock` starts at `1.0`; `wallclock_at` never populated by `Runtime.emit` |
| R3 | No software revision recorded in any session | High | `component_version="1.0.0"` default literal in `Runtime.emit` |
| R4 | Provider versions are verified but not persisted | Medium | `ProviderSet.check_versions` raises on mismatch, writes nothing |
| R5 | Analytical parameters (`latency_bound`, `repeat_cap`) are unversioned code constants | Medium | `protocol/bounded_repeat.py`, protocol constructors |
| R6 | `component_version` and `schema_version` cannot distinguish two runtimes that produced the same event type differently | Medium | Both are literals, not resolved at build time |
| R7 | Non-portable absolute macOS path hard-coded in a test | Low (but blocks CI) | `packages/mpe/tests/test_protocol_recognition.py:369` uses `cwd="/Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console"`; this is the single failing test on any non-Andrea machine |
| R8 | `AGENTS.md` documents the same absolute macOS path as the canonical `PYTHONPATH` | Low | `AGENTS.md`, lint/test command block |
| R9 | `black` is a declared dev dependency but the codebase is not black-formatted (23 of 50 files would be reformatted), so "run the formatter" is currently a destructive instruction | Low | `black --check packages/mpe` |
| R10 | Roadmap language risk: a hash chain alone must not be described as tamper-proof | Documentation | Roadmap §A1 explicitly requires the term "tamper-evident" |

---

## 6. What Milestone 1 must not do

Derived from the roadmap's non-goals and from the current phase gates in `docs/project/NEXT_TASK.md`:

- do not introduce a second audit-log store;
- do not introduce snapshots as scientific evidence;
- do not add EEG, sensor, BIDS, or statistical modules in Milestone 1;
- do not modify `docs/MPE_*.md`, `docs/specification/v1.1/*`, or the canonical registries without an approved ADR;
- do not describe the hash chain as proving authorship, external timestamping, or tamper-proofness;
- do not break the existing `EventStore` protocol for `InMemoryEventStore` consumers.

---

## 7. Summary judgement

The repository is a *good* starting point for Milestone 1 and a *poor* starting point for Milestones 2–4.

Strengths: a single authoritative append-only event history; typed identifiers; per-event payload schema validation; deterministic canonical JSON; deterministic replay proven by cross-process tests; no snapshot shortcut; clean separation of raw observation from interpretation and evaluation; 162 tests, clean `ruff` and `mypy`.

Gaps, in priority order: (1) no cryptographic integrity chain; (2) no real recorded time; (3) no software/provider/policy revision provenance; (4) no versioned-policy concept at all; (5) no derived-analysis record type.

Milestone 1 is achievable as a persistence-layer extension plus a provenance event, with no change to the runtime's conceptual model.

---

## 8. Verification commands executed

Environment: Ubuntu, Python 3.12 (the repo requires `>=3.11`; the machine's system Python 3.10 is insufficient), virtual environment at `.venv`, `pip install -e ".[dev]"` plus `pip install -e packages/mpe`.

| Command | Result |
|---|---|
| `python -m unittest discover -s packages/mpe/tests -t packages/mpe -p 'test_*.py'` | 162 tests, **1 error** — `test_protocol_recognition` CLI subprocess test fails with `FileNotFoundError` on the hard-coded macOS `cwd` (R7). All other tests pass. |
| `.venv/bin/ruff check packages/mpe/src packages/mpe/tests` | All checks passed |
| `.venv/bin/mypy packages/mpe/src/mpe` | Success: no issues found in 32 source files |
| `.venv/bin/black --check packages/mpe` | 23 files would be reformatted, 27 unchanged (R9) — reported, not applied |

No production code, test, or configuration file was modified by this audit.
