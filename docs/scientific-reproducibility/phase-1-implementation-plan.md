# Scientific Reproducibility Milestone 1 (SR-M1) — Implementation Plan

**Status:** proposal, revised after review. No implementation is included in this deliverable. `ADR-0001` was **approved on 2026-07-27** (`APPROVE_ADR_0001`), so the gate in §9 is now satisfied; implementation is authorised from the commit that records the token.
**Programme:** SR-M1. This is a parallel programme; it is deliberately **not** mapped onto the MPE phase numbering (it is not Phase 4D and not Phase 5).
**Companion document:** `phase-1-architecture-audit.md` (same directory).
**Audited revision:** `78b984c656d5555b5405163886f5ea84631a6029`
**Scope:** Milestone 1 of the Scientific Reproducibility Roadmap — "Scientific provenance foundation" (Workstream A only).

---

## 1. Objective and exit criterion

Objective: make a MindTune session **reconstructable and self-describing** — a complete session can be replayed from authoritative events alone, and every derived result identifies the versions that produced it.

Exit criterion, restated as a testable statement with its limit made explicit:

> Given only a session's persisted event stream, the system can (a) verify that **no event within the retained stream** has been mutated, deleted from the interior, inserted, or reordered since it was written; (b) rebuild the identical projection in a fresh process against an empty database using the supported export/import path; and (c) report the protocol, curriculum, policy, provider, and software versions that produced every derived result.

**Explicit limit of (a): tail truncation is not detected by the chain alone.** A per-stream SHA-256 chain binds each event to its predecessor, so it cannot distinguish "the stream ended here" from "the stream was cut here" — a truncated chain is internally consistent. Truncation becomes detectable only when an expected terminal state is **independently retained or anchored** outside the stream being verified: a separately stored terminal digest, a separately stored event count, a signed manifest, or an external append-only log. SR-M1 does **not** deliver such an anchor; §3.1.7 specifies only the verifier hook that makes one possible in a later milestone, and until an anchor exists every integrity report must state truncation as `undetermined`, never as `pass`.

Everything outside the exit criterion — behavioral policies, EEG, BIDS, preregistration — is explicitly deferred to Milestones 2–4.

---

## 2. Design constraints

1. The existing `EventStore` remains the sole authoritative record (roadmap §2.1). Integrity is **a native capability of the existing persistence layer** — unavailable for historical schema-1.1 streams and mandatory for all schema-1.2 streams — not a new subsystem.
2. No snapshot store (roadmap §2.2).
3. `InMemoryEventStore` and `SQLiteEventStore` must continue to satisfy one shared `EventStore` protocol; existing callers (`Runtime`, `Replay`, CLI, both protocols) must keep working unchanged.
4. Existing persisted stores (`PRAGMA user_version = 1`) must remain readable and report `integrity: unavailable`. For `user_version = 2` stores, verification is **not** opt-in: it is the default read behaviour, and any unverified read is an explicitly named recovery path (§3.1.5).
5. Documentation uses **"tamper-evident"**, never "tamper-proof" (roadmap §A1), and never claims truncation detection without a retained anchor.
6. No changes to `docs/MPE_*.md`, `docs/specification/v1.1/*`, or canonical registries without an approved ADR.
7. Integrity metadata and provenance metadata are separate concerns and must not be conflated in the same field group (§3.1.2).

---

## 3. Work packages

### WP-1 — Event integrity chain (roadmap A1)

**Where:** `packages/mpe/src/mpe/persistence/` (serializer + store) and the `Event` envelope. Added to the persistence layer, not to a new module tree.

#### 3.1.1 Canonical event bytes

Extend `serializer.py` with **two** deterministic UTF-8 serializations sharing one canonical encoder (sorted keys, fixed separators, explicit null handling, the existing `_to_json` conventions so payload encoding does not change):

- `canonical_digest_bytes(event)` — the input to `sha256`: all semantically bound fields **including `previous_digest`**, **excluding `content_digest`** (its own output);
- `canonical_record_bytes(event)` — the complete stored row and exported line, **including both digest fields**.

They must not be described as producing the same object; a `canonical_record_bytes` round-trip must reproduce byte-identical `canonical_digest_bytes` (ADR-0001 §2.3.1).

#### 3.1.2 Integrity metadata vs provenance metadata (separated)

These are two distinct concerns and are specified separately:

| Group | Fields | Meaning | In digest input? |
|---|---|---|---|
| **Integrity** | `content_digest`, `previous_digest` | Binds this event's bytes to its predecessor within one stream. Purely structural; carries no claim about who wrote it or with what code. | `content_digest`: no (it is the output). `previous_digest`: yes — it must be covered, otherwise the link can be rewritten freely. |
| **Provenance** | `writer_revision` (alongside the existing `component`, `component_version`) | Identifies the software that produced the event. A scientific claim, not an integrity mechanism. | Yes — it is ordinary envelope content and is covered like any other field. |

`writer_revision` is therefore **not** part of the integrity mechanism; it is provenance that the integrity mechanism happens to protect. The ADR must state this explicitly so a later reader does not mistake a matching digest for evidence about authorship. Resolution of `writer_revision` is specified in §3.3.1.

#### 3.1.3 Three version namespaces

Three independent version namespaces exist and must never be conflated:

| Namespace | Where | Meaning | SR-M1 change |
|---|---|---|---|
| **SQLite `PRAGMA user_version`** | physical database file | On-disk table layout of the persistence backend. Nothing to do with the domain model. | `1` → `2` (adds the integrity and provenance columns) |
| **Event envelope `schema_version`** | every event, validated against `SUPPORTED_SCHEMA_VERSIONS` | The canonical MPE event contract: envelope fields, payload schemas, event vocabulary. | `1.1` → **`1.2` required** |
| **Software revision** | `writer_revision` (new), `component_version` (existing) | Which build of the code emitted the event. | new field, resolver in §3.3.1 |

**Decision: the new envelope fields and the new event type require event schema `1.2`.** Adding `content_digest`, `previous_digest`, and `writer_revision` to the envelope, and adding `session_provenance_recorded` to `SUPPORTED_EVENT_TYPES`, both change the canonical event contract; a reader implementing only `1.1` cannot validate a `1.2` stream, and a `1.1` writer cannot produce a chain. `SUPPORTED_SCHEMA_VERSIONS` becomes `{"1.1", "1.2"}`: `1.1` events remain readable as historical streams, while newly emitted events are `1.2`. A single stream must not mix schema versions — the store rejects a `1.1` append into a `1.2` stream and vice versa. This change to the canonical event model is precisely why `ADR-0001` gates the work.

#### 3.1.4 Chain enforcement on append

In `_append_in_transaction` and `append_batch`: compute `content_digest`, require the event's `previous_digest` to equal the stored tail's `content_digest` (and to be `NULL` exactly at sequence 1), and reject any mismatch with a new `IntegrityError` (subclass of `MPEError`, added to `errors.py`).

#### 3.1.5 Verification on read — verified by default for v2

Verification is the **normal** read path, not an option, and integrity status is a property of the **stream** (its `schema_version` and chain state), not of the file. The authoritative matrix is ADR-0001 §2.5:

| Store `user_version` | Stream schema | Chain | Behaviour | Status | Append |
|---|---|---|---|---|---|
| 1 | 1.1 | none | readable | `integrity: unavailable` | refused |
| 2 | 1.1 (historical) | none | readable | `integrity: unavailable` | refused (stream closed) |
| 2 | 1.2 | complete | verification mandatory | `verified` or `IntegrityError` | allowed |
| 2 | 1.2 | missing/partial | invalid | `IntegrityError` | refused |

`InMemoryEventStore` has no `PRAGMA user_version` and derives the same semantics from the stream alone (ADR-0001 §2.5.1): no partial chains, no mixed schema versions in one stream.

Unverified reads of a v2 store are reachable **only** through an explicitly named recovery API — `read_unverified(..., reason: str)` — which is called nowhere in the normal application path (`Runtime`, `Replay`, `ProtocolSummary`, standard CLI commands), logs the supplied reason, and marks any result it produces `integrity: unverified`. A test asserts that no module outside the recovery path and its own tests references it.

#### 3.1.6 Verification command

Extend the existing `mpe validate-store` command (`cli.py:290`) — do **not** add a new subcommand tree — to report per session: event count, `schema_version` range, store `user_version`, chain continuity, first divergent sequence number if any, and a separate `tail_truncation` field. Absent an anchor that field is always `undetermined`, with a one-line explanation in the output. The command must never print a result implying the tail was verified.

#### 3.1.7 Anchor hook (design only, not delivered)

So a later milestone can make truncation detectable without redesigning this work: the verification result object accepts an optional `expected_terminal` input (terminal `content_digest` and event count). When supplied from an independently retained source, verification compares it against the observed tail and reports `tail_truncation: pass|fail`; when absent, `undetermined`. SR-M1 delivers the parameter and the comparison — **not** any mechanism that produces, retains, distributes, or signs the anchor. That is out of scope and must not be described as delivered.

#### 3.1.8 Explicit non-claims (code docstring + ADR)

On a stream we already hold, the chain detects mutation of an event, deletion of an interior event, insertion, and reordering. It does **not** detect removal of the tail of the stream, because a truncated chain is internally consistent; truncation is detectable only against an independently retained expected terminal state (digest, count, signed manifest, or external anchor), which SR-M1 does not provide. It does not prove authorship, does not prove the recorded time, and does not protect against a full rewrite of the entire chain by an actor holding the writer. The system is **tamper-evident**, never tamper-proof.

**Estimate:** ~320 lines of production code, ~250 lines of tests.

### WP-2 — Real time and device time (roadmap A1, gaps R2)

`Runtime.emit` currently sets only the deterministic session `timestamp`. Populate `wallclock_at` with `time.time()` (UTC epoch seconds) at emission, keeping the deterministic `timestamp` as the ordering clock so existing replay-equality tests remain valid. Document the two-clock model: `timestamp` is the protocol clock, `wallclock_at` is the recorded UTC time, and a future `source_device_timestamp` (Milestone 3) will be the third, device-supplied clock. Provide an injectable wall clock so deterministic tests can pin it.

**Estimate:** ~40 lines of production code, ~60 lines of tests.

### WP-3 — Session provenance record (roadmap A3)

Introduce **one** new event type, `session_provenance_recorded`, emitted immediately after `session_created` and before any other event, carrying a flat, fully typed payload:

| Field | Source today | Notes |
|---|---|---|
| `protocol_id`, `protocol_version_id` | protocol construction | `protocol_id` newly surfaced |
| `curriculum_id`, `curriculum_version` | none | nullable until a curriculum is bound |
| `experimental_condition` | none | nullable |
| `randomization_seed` | `session_started.random_seed` | duplicated here intentionally for a single provenance record |
| `stimulus_set_id`, `stimulus_set_version` | fixture assets | |
| `scoring_policy_version`, `rt_policy_version`, `signal_processing_policy_version` | none | nullable in Milestone 1; populated in Milestones 2–3 |
| `software_revision` | none | resolved by the deployment-safe resolver of §3.3.1; recorded together with its `source`, and as an explicit `unknown` when unresolvable. Git is only the development fallback |
| `provider_versions` | `ProviderSet.check_versions` | persist the same map that is verified |
| `schema_version`, `writer_component`, `writer_version`, `writer_revision` | envelope | |

Adding an event type requires: an entry in `SUPPORTED_EVENT_TYPES`, a `PAYLOAD_SCHEMAS` rule set, an aggregate handler in `aggregates.py` (populating new `RuntimeState` provenance fields and appearing in `as_dict()`), the schema bump to `1.2` (§3.1.3), and an approved ADR because it touches the canonical event vocabulary.

Nullable-by-design fields must be represented as explicit `null`, never as invented defaults — the same rule the roadmap applies to missing impedance values in §C4.

#### 3.3.1 Software revision resolver (deployment-safe)

`software_revision` and `writer_revision` are resolved by one shared function with a strict, ordered fallback. `git rev-parse` is a **development-only** last resort: a deployed container, a wheel install, or a read-only image has no `.git` directory, and shelling out to git at runtime is both fragile and a startup cost.

| Order | Source | Typical case | Result |
|---|---|---|---|
| 1 | Embedded build metadata — a generated `_build_info.py` written at package build time | container / wheel builds | `{revision, source: "build_metadata"}` |
| 2 | Environment-provided revision — `MPE_SOFTWARE_REVISION` (or the platform's standard build-SHA variable) | CI, orchestrated deployments | `{revision, source: "environment"}` |
| 3 | Installed package metadata — `importlib.metadata.version("mpe")` plus distribution metadata | pip-installed without build stamping | `{revision, source: "package_metadata"}` |
| 4 | `git rev-parse HEAD` plus a dirty-worktree flag | developer working copy only | `{revision, source: "git", dirty: bool}` |
| 5 | none of the above | unknown deployment | `{revision: null, source: "unknown"}` |

Rules: the resolver never raises and never blocks session start; the `source` is recorded alongside the value so a reader can judge its strength; an unresolved revision is recorded as an explicit `unknown`, never as an empty string, a placeholder, or a fabricated version. A session whose provenance reports `source: "unknown"` remains valid but must be flagged in any downstream scientific report.

#### 3.3.2 Causal binding of derived results

Provenance must be impossible to omit, not merely conventional:

1. **Runtime enforcement.** `Runtime` refuses to emit any event other than `session_created` until `session_provenance_recorded` has been appended to that stream, raising `IllegalStateTransitionError`. Provenance therefore always occupies sequence 2.
2. **Causal reference from derived results, discriminated by schema.** Derived results carry `provenance_status: "recorded" | "unavailable_legacy"` and `provenance_event_id: EventID | None`. `"recorded"` requires a valid ID and is the only case permitted for schema 1.2; `"unavailable_legacy"` requires `None` and is permitted only for schema 1.1, reachable only through an explicitly named legacy API. `summary_walk.walk_session` raises on a schema-1.2 stream lacking `session_provenance_recorded`. See ADR-0001 §2.8.1.
3. **Event-level linkage.** The first trial event of the session includes the provenance event's `EventID` in its existing `provenance` list, so causal linkage is visible in the stream itself and not only in the projection.

The intended invariant: **no derived result can be silently unprovenanced** — a schema-1.2 result cannot exist without a valid provenance reference, and a legacy result must declare `unavailable_legacy` explicitly.

**Estimate:** ~260 lines of production code, ~220 lines of tests.

### WP-4 — Replay determinism and integrity test suite (roadmap A2)

Add to `packages/mpe/tests/persistence/`:

1. `test_integrity_chain.py` — digest stability across processes; the chain **rejects** an in-place payload edit, a deleted interior event, an inserted event, and a reordered pair. It must additionally assert the negative case: a **truncated tail is accepted** by chain verification and reported as `tail_truncation: undetermined`, and is rejected only when an independently retained `expected_terminal` (terminal digest + event count) is supplied to the verifier. This test is the executable statement of the limit in §1 and must not be written as though truncation were caught.
2. `test_verified_by_default.py` — a v2 store read through the normal path verifies digests with no opt-in; a tampered v2 store raises `IntegrityError` from `Runtime`, `Replay`, and `ProtocolSummary` alike; `read_unverified` is reachable only from the recovery path and marks its output `integrity: unverified`; a v1 store reports `integrity: unavailable`.
3. `test_rebuild_from_empty.py` — must use the supported path defined in §3.4.1, not direct table manipulation.
4. `test_no_snapshot_dependency.py` — assert that no persisted artifact other than the `events` table is required to produce a `ProtocolSummary` (guards roadmap §2.2 against regression).
5. `test_schema_version_rejection.py` — an unsupported `schema_version` fails explicitly on both append and read; a `1.1` event cannot be appended to a `1.2` stream or vice versa.
6. `test_provenance_required.py` — a runtime that skips `session_provenance_recorded` cannot emit further events; no `ProtocolSummary` can be constructed without a provenance reference.
7. Property-based determinism over generated valid streams using `hypothesis` (**approved** as a dev dependency).

#### 3.4.1 Supported export/import path

`test_rebuild_from_empty.py` must exercise a real, supported, user-facing path — manipulating SQLite tables directly would test the test rather than the system. SR-M1 therefore defines a minimal stream interchange in `packages/mpe/src/mpe/persistence/interchange.py`:

- **Export.** `mpe export-session --session-id <id> --out <file.jsonl>`, backed by `export_stream(store, session_id) -> Iterator[bytes]`, emitting one `canonical_record_bytes(event)` JSON object per line, in ascending `session_sequence_number`. It uses the shared canonical encoder but the complete record field set, including `content_digest` and `previous_digest`; digest verification separately recomputes `canonical_digest_bytes(event)`. Export is read-only and reads through the normal verified path; it refuses to export a stream that fails verification.
- **Import.** `mpe import-session --in <file.jsonl> --store <path>`, backed by `import_stream(store, lines)`, appending each event through the **ordinary** `append` / `append_batch` API so every existing invariant — schema validation, ordering, provenance existence, chain continuity — is re-applied on ingest. Import refuses to write into a stream that already exists.
- **Round-trip property.** For any exported stream, re-importing into an empty database yields byte-identical canonical bytes per event, an identical terminal `content_digest`, an identical `RuntimeState.as_dict()`, and an identical `ProtocolSummary`.

This interchange is an internal reproducibility path. It is explicitly **not** a scientific archive format and **not** BIDS (Milestone 4).

**Estimate:** ~200 lines of production code (interchange + two CLI commands), ~550 lines of tests.

### WP-5 — Architecture decision record

One repository-level ADR at the confirmed path `docs/architecture/adr/ADR-0001-event-integrity-and-provenance.md`. **Implementation of WP-1 through WP-4 may not begin until this ADR is reviewed and approved.** It must cover, at minimum:

1. why integrity extends the existing store instead of a parallel audit log (roadmap §2.1);
2. why snapshots are excluded as scientific evidence (roadmap §2.2);
3. the separation of integrity metadata from provenance metadata (§3.1.2);
4. the three version namespaces and the decision that these changes require event schema `1.2` (§3.1.3);
5. verified-by-default reads for v2 stores and the explicitly unsafe recovery path (§3.1.5);
6. the two-clock (soon three-clock) model (WP-2);
7. the software-revision resolver ordering, with `git rev-parse` as a development fallback only and `unknown` as an explicit outcome (§3.3.1);
8. the discriminated provenance model that prevents a silently unprovenanced derived result (§3.3.2);
9. the supported export/import interchange (§3.4.1);
10. the threat model, stated in the ADR's own words: the chain detects mutation, interior deletion, insertion, and reordering; **it does not detect tail truncation**, which is detectable only against an independently retained expected terminal state, and no such anchor is delivered by SR-M1; the system is tamper-evident, not tamper-proof, and proves neither authorship nor recorded time;
11. the migration path for `user_version = 1` / schema `1.1` stores.

**Estimate:** one document.

### WP-6 — Repository hygiene blocking reproducibility (audit R7–R9)

These are small but they currently prevent an independent party from reproducing the test run at all:

1. Replace the hard-coded macOS `cwd` in `packages/mpe/tests/test_protocol_recognition.py:369` with a repository-root path derived from `__file__`.
2. Update `AGENTS.md` to use a relative `PYTHONPATH` instead of `/Users/idonokurasani/...`.

These two path fixes are approved and must be delivered as their own small change, **separate from any formatting work**.

3. `black` is confirmed authoritative. Repository-wide formatting (23 of 50 files) must land in its **own isolated commit or PR**: never mixed with the SR-M1 implementation, and never mixed with the two path fixes above.

None of the three is part of this read-only deliverable.

---

## 4. Sequence and gating

| Step | Work package | Gate |
|---|---|---|
| 1 | WP-5 (ADR) | **Hard gate — satisfied.** `APPROVE_ADR_0001` recorded 2026-07-27; implementation is authorised from the commit publishing the token |
| 2 | WP-6.1–6.2 (path fixes) | Approved; separate change, no formatting |
| 2b | WP-6.3 (`black`) | Isolated commit or PR of its own, at any time, never mixed with SR-M1 |
| 3 | WP-2 | Wall-clock recording; must not break replay-equality tests |
| 4 | WP-1 | Integrity chain + schema `1.2` + verified-by-default reads |
| 5 | WP-3 | Provenance event and causal binding; depends on the schema decision in WP-1 |
| 6 | WP-4 | Interchange path and the test suite asserting the exit criterion *and its truncation limit* |

WP-1 must precede WP-3 because both depend on the single schema bump to `1.2`, and WP-4 lands last because it asserts the combined exit criterion.

---

## 5. Backwards compatibility

| Concern | Mitigation |
|---|---|
| Existing SQLite stores at `user_version = 1` | Read-only support retained; integrity reported as `unavailable`; no automatic rewrite, since rewriting historical events to add digests would itself be a mutation and would fabricate provenance that was never recorded |
| Existing schema `1.1` streams | Remain readable; cannot be extended with `1.2` events; derived results from them go through an explicitly labelled legacy path that marks provenance as absent (§3.3.2) |
| `InMemoryEventStore` | Implements the same digest computation and the same verified-by-default semantics, so the shared contract tests apply to both backends |
| Existing 162 tests | Must all pass unchanged; the deterministic `timestamp` clock is not altered |
| Existing replay projections | `as_dict()` gains provenance fields — any test comparing full dicts compares two projections of the same stream, so equality assertions remain valid |
| Docker images / `compose/*.yaml` | No change required; `validate-store` gains report fields, and `export-session` / `import-session` are additive commands |

---

## 6. Deliverables

1. `docs/architecture/adr/ADR-0001-event-integrity-and-provenance.md` (gating deliverable)
2. Integrity extension in `packages/mpe/src/mpe/persistence/{serializer,store}.py` + `IntegrityError` in `errors.py`, with verified-by-default reads and a separate `read_unverified` recovery path
3. Event schema `1.2` in `events.py` / `validation.py`, and SQLite `user_version = 2`
4. `wallclock_at` population in `runtime.py` with an injectable wall clock
5. Software-revision resolver with the ordered fallback of §3.3.1
6. `session_provenance_recorded` event type across `events.py`, `validation.py`, `aggregates.py`, plus the causal binding of §3.3.2
7. `persistence/interchange.py` with `mpe export-session` / `mpe import-session`
8. `mpe validate-store` reporting chain continuity and `tail_truncation: undetermined`
9. Test suite WP-4, including the explicit truncation-limit test
10. Update of `docs/project/PROJECT_STATE.md` and `docs/project/NEXT_TASK.md` recording SR-M1 as a parallel programme (allowed by the existing phase rules only for recording completion and next task)

---

## 7. Out of scope for Milestone 1

Behavioral-analysis policies, reaction-time derivation, SDT, power analysis (Milestone 2); device capability profiles, EEG acquisition contracts, preprocessing registry, feature provenance (Milestone 3); BIDS export, validator integration, publication bundle, Methods appendix (Milestone 4); all regulatory work, per roadmap §8.

Also out of scope for SR-M1, and explicitly **not** delivered: any anchor mechanism that would make tail truncation detectable — an external append-only log, signed manifests, trusted timestamping, or the retention and distribution of terminal digests. §3.1.7 delivers only the verifier parameter that a future anchor would supply.

Explicitly excluded, permanently: a parallel audit-log subsystem, snapshots as scientific evidence, and any claim of tamper-proofness, unconditional truncation detection, external timestamping, or proven authorship.

---

## 8. Decisions recorded (previously open questions)

| # | Question | Decision |
|---|---|---|
| 1 | ADR location | `docs/architecture/adr/ADR-0001-event-integrity-and-provenance.md` |
| 2 | Documentation root | These reports live at `docs/scientific-reproducibility/`; no parallel top-level `documentation/` root |
| 3 | Phase numbering | Parallel programme named **Scientific Reproducibility Milestone 1 (SR-M1)**; not mapped to Phase 4D or Phase 5 |
| 4 | `hypothesis` | Approved as a development dependency for determinism and property tests |
| 5 | `black` | Authoritative; repository-wide formatting isolated in its own commit or PR, never mixed with SR-M1 |
| 6 | Hygiene fixes | Hard-coded test path and `AGENTS.md` absolute path to be fixed, kept separate from broad formatting |
| 7 | Truncation | The chain does not detect tail truncation; all claims to the contrary are removed, and truncation is reported as `undetermined` absent an independently retained anchor |
