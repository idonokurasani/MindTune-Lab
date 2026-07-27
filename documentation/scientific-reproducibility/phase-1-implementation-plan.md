# Phase 1 — Scientific Reproducibility Implementation Plan (Milestone 1)

**Status:** proposal. No implementation is included in this deliverable.
**Companion document:** `phase-1-architecture-audit.md` (same directory).
**Audited revision:** `78b984c656d5555b5405163886f5ea84631a6029`
**Scope:** Milestone 1 of the Scientific Reproducibility Roadmap — "Scientific provenance foundation" (Workstream A only).

---

## 1. Objective and exit criterion

Objective: make a MindTune session **reconstructable and self-describing** — a complete session can be replayed from authoritative events alone, and every derived result identifies the versions that produced it.

Exit criterion (from the roadmap, restated as a testable statement):

> Given only a session's persisted event stream, the system can (a) verify that the stream has not been mutated or truncated since it was written, (b) rebuild the identical projection in a fresh process against an empty database, and (c) report the protocol, curriculum, policy, provider, and software versions that produced every derived result.

Everything outside that statement — behavioral policies, EEG, BIDS, preregistration — is explicitly deferred to Milestones 2–4.

---

## 2. Design constraints

1. The existing `EventStore` remains the sole authoritative record (roadmap §2.1). Integrity is an **optional capability of the existing persistence layer**, not a new subsystem.
2. No snapshot store (roadmap §2.2).
3. `InMemoryEventStore` and `SQLiteEventStore` must continue to satisfy one shared `EventStore` protocol; existing callers (`Runtime`, `Replay`, CLI, both protocols) must keep working unchanged.
4. Existing persisted stores (`PRAGMA user_version = 1`) must remain readable; integrity is opt-in and forward-only.
5. Documentation uses **"tamper-evident"**, never "tamper-proof" (roadmap §A1).
6. No changes to `docs/MPE_*.md`, `docs/specification/v1.1/*`, or canonical registries without an approved ADR.

---

## 3. Work packages

### WP-1 — Event integrity chain (roadmap A1)

**Where:** `packages/mpe/src/mpe/persistence/` (serializer + store) and the `Event` envelope.

Add to the persistence layer, not to a new module tree:

1. **Canonical event bytes.** Extend `serializer.py` with a `canonical_bytes(event) -> bytes` function producing a deterministic UTF-8 encoding of the *whole* envelope (sorted keys, fixed separators, explicit null handling, digest fields excluded from their own input). Reuse the existing `_to_json` conventions so payload encoding does not change.
2. **Digest fields.** Add three nullable columns and matching envelope fields:
   - `content_digest` — `sha256(canonical_bytes(event))`, hex;
   - `previous_digest` — `content_digest` of the preceding event in the same session stream, `NULL` for sequence 1;
   - `writer_revision` — resolved software revision (see WP-3).
   Bump the SQLite schema to `PRAGMA user_version = 2`, with a read path that accepts version 1 stores and reports them as `integrity: unavailable` rather than failing.
3. **Chain enforcement on append.** In `_append_in_transaction` and `append_batch`, compute the digest, require `previous_digest` to match the stored tail, and reject mismatches with a new `IntegrityError` (subclass of `MPEError`, added to `errors.py`).
4. **Verification on read.** Extend `SQLiteEventStore.read`/`all_events` with an optional `verify: bool` parameter (default preserving current behaviour) that recomputes and compares digests.
5. **Verification command.** Extend the existing `mpe validate-store` command (`cli.py:290`) with `--verify-integrity`, reporting per session: event count, chain continuity, first divergent sequence number, and schema version. Do **not** add a new CLI subcommand tree.

Explicit non-claims to be stated in the code docstring and the ADR: the chain detects mutation, deletion, reordering, and truncation *of a stream we already hold*; it does not prove authorship, does not prove the recorded time, and does not protect against a full rewrite of the entire chain by someone holding the writer.

**Estimate:** ~250 lines of production code, ~200 lines of tests.

### WP-2 — Real time and device time (roadmap A1, gaps R2)

`Runtime.emit` currently sets only the deterministic session `timestamp`. Populate `wallclock_at` with `time.time()` (UTC epoch seconds) at emission, keeping the deterministic `timestamp` as the ordering clock so existing replay-equality tests remain valid. Document the two-clock model: `timestamp` is the protocol clock, `wallclock_at` is the recorded UTC time, and a future `source_device_timestamp` (Milestone 3) will be the third, device-supplied clock. Provide an injectable wall clock so deterministic tests can pin it.

**Estimate:** ~40 lines of production code, ~60 lines of tests.

### WP-3 — Session provenance record (roadmap A3)

Introduce **one** new event type, `session_provenance_recorded`, emitted immediately after `session_created`, carrying a flat, fully typed payload:

| Field | Source today | Notes |
|---|---|---|
| `protocol_id`, `protocol_version_id` | protocol construction | `protocol_id` newly surfaced |
| `curriculum_id`, `curriculum_version` | none | nullable until a curriculum is bound |
| `experimental_condition` | none | nullable |
| `randomization_seed` | `session_started.random_seed` | duplicated here intentionally for a single provenance record |
| `stimulus_set_id`, `stimulus_set_version` | fixture assets | |
| `scoring_policy_version`, `rt_policy_version`, `signal_processing_policy_version` | none | nullable in Milestone 1; populated in Milestones 2–3 |
| `software_revision` | none | `git rev-parse HEAD` resolved at build/run time, plus a dirty flag |
| `provider_versions` | `ProviderSet.check_versions` | persist the same map that is verified |
| `schema_version`, `writer_component`, `writer_version` | envelope | |

Adding an event type requires: an entry in `SUPPORTED_EVENT_TYPES`, a `PAYLOAD_SCHEMAS` rule set, an aggregate handler in `aggregates.py` (populating new `RuntimeState` provenance fields and appearing in `as_dict()`), and an ADR because it touches the canonical event vocabulary. That ADR is a Milestone 1 deliverable, not a side effect.

Nullable-by-design fields must be represented as explicit `null`, never as invented defaults — the same rule the roadmap applies to missing impedance values in §C4.

**Estimate:** ~180 lines of production code, ~150 lines of tests.

### WP-4 — Replay determinism and integrity test suite (roadmap A2)

Add to `packages/mpe/tests/persistence/`:

1. `test_integrity_chain.py` — digest stability across processes; chain rejects an in-place payload edit, a deleted middle event, a reordered pair, and a truncated tail; version-1 stores report `integrity: unavailable` rather than failing.
2. `test_rebuild_from_empty.py` — export a full stream, ingest it into a brand-new empty database, assert `RuntimeState.as_dict()` equality and `ProtocolSummary` equality against the original.
3. `test_no_snapshot_dependency.py` — assert that no persisted artifact other than the `events` table is required to produce a `ProtocolSummary` (guards roadmap §2.2 against regression).
4. `test_schema_version_rejection.py` — an event with an unsupported `schema_version` fails explicitly on both append and read.
5. Property-based determinism check over generated valid streams (`hypothesis` if approved as a new dev dependency; otherwise a seeded generator using the standard library only).

**Estimate:** ~400 lines of tests, no production code.

### WP-5 — Architecture decision record

One repository-level ADR, `docs/architecture/adr/ADR-0001-event-integrity-and-provenance.md`, covering: why integrity extends the existing store instead of a parallel audit log; why snapshots are excluded as evidence; the two-clock (soon three-clock) model; the explicit "tamper-evident, not tamper-proof" statement; the new event type and its schema-version implications; the migration path for `user_version = 1` stores.

**Estimate:** one document.

### WP-6 — Repository hygiene blocking reproducibility (audit R7–R9)

These are small but they currently prevent an independent party from reproducing the test run at all:

1. Replace the hard-coded macOS `cwd` in `packages/mpe/tests/test_protocol_recognition.py:369` with a repository-root path derived from `__file__`.
2. Update `AGENTS.md` to use a relative `PYTHONPATH` instead of `/Users/idonokurasani/...`.
3. Decide explicitly whether `black` is authoritative. Either format the codebase in one isolated commit or remove `black` from dev dependencies; the present state (declared but not applied to 23 of 50 files) makes "run the formatter" a destructive instruction.

These are **not** part of this read-only deliverable and require separate approval.

---

## 4. Sequence and gating

| Step | Work package | Gate |
|---|---|---|
| 1 | WP-5 (ADR) | Andrea approves the ADR before any code |
| 2 | WP-6 | Approval to touch a test file and `AGENTS.md` |
| 3 | WP-2 | Wall-clock recording; must not break replay-equality tests |
| 4 | WP-1 | Integrity chain behind an opt-in schema bump |
| 5 | WP-3 | New event type; depends on the approved ADR |
| 6 | WP-4 | Test suite proving the exit criterion |

WP-1 and WP-3 are independent of each other and can be parallelised after the ADR, but WP-4 must land last because it asserts the combined exit criterion.

---

## 5. Backwards compatibility

| Concern | Mitigation |
|---|---|
| Existing SQLite stores at `user_version = 1` | Read-only support retained; integrity reported as unavailable; no automatic rewrite (rewriting historical events would itself be a mutation) |
| `InMemoryEventStore` | Implements the same digest computation in memory so the shared contract tests apply to both backends |
| Existing 162 tests | Must all pass unchanged; the deterministic `timestamp` clock is not altered |
| Existing replay projections | `as_dict()` gains provenance fields — any test comparing full dicts compares two projections of the same stream, so equality assertions remain valid |
| Docker images / `compose/*.yaml` | No change required; `--verify-integrity` is an added flag |

---

## 6. Deliverables

1. `docs/architecture/adr/ADR-0001-event-integrity-and-provenance.md`
2. Integrity extension in `packages/mpe/src/mpe/persistence/{serializer,store}.py` + `IntegrityError` in `errors.py`
3. `wallclock_at` population in `runtime.py` with an injectable wall clock
4. `session_provenance_recorded` event type across `events.py`, `validation.py`, `aggregates.py`
5. `mpe validate-store --verify-integrity`
6. Test suite WP-4
7. Update of `docs/project/PROJECT_STATE.md` and `docs/project/NEXT_TASK.md` recording the phase (allowed by the existing phase rules only for recording completion and next task)

---

## 7. Out of scope for Milestone 1

Behavioral-analysis policies, reaction-time derivation, SDT, power analysis (Milestone 2); device capability profiles, EEG acquisition contracts, preprocessing registry, feature provenance (Milestone 3); BIDS export, validator integration, publication bundle, Methods appendix (Milestone 4); all regulatory work, per roadmap §8.

Explicitly excluded, permanently: a parallel audit-log subsystem, snapshots as scientific evidence, and any claim of tamper-proofness, external timestamping, or proven authorship.

---

## 8. Open questions for Andrea

1. **ADR location.** The repository has `docs/architecture/` but no `adr/` subdirectory and no existing ADR, while `docs/project/DEVELOPER_WORKFLOW.md` defines an ADR process. Confirm the path and numbering convention.
2. **Documentation root.** These two reports were placed at `documentation/scientific-reproducibility/` as instructed, which is a new top-level directory parallel to the existing `docs/`. Confirm whether the reproducibility programme should live there permanently or be moved under `docs/`.
3. **Phase numbering.** The roadmap's "Milestone 1" does not map onto the repository's MPE phase numbering (currently Phase 4C.2). Confirm whether this becomes Phase 4D / Phase 5 or a parallel track.
4. **`hypothesis`** as a new dev dependency for property-based determinism tests: approve or restrict WP-4 to the standard library.
5. **`black`**: authoritative or removed (audit R9).
