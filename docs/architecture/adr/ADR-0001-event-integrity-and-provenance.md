# ADR-0001 — Event integrity and provenance

**Status:** Proposed (revision 2, conditions applied) — published for final approval. No production code may be written against this ADR until an approving token is recorded in §6.
**Date:** 2026-07-27
**Programme:** Scientific Reproducibility Milestone 1 (SR-M1). A parallel programme; deliberately not mapped onto the MPE phase numbering.
**Context revision:** `78b984c656d5555b5405163886f5ea84631a6029`
**Supersedes:** nothing. **Superseded by:** nothing.
**Related:** `docs/scientific-reproducibility/phase-1-architecture-audit.md`, `docs/scientific-reproducibility/phase-1-implementation-plan.md`

---

## 1. Context

MindTune Lab's MPE runtime already keeps a single authoritative, append-only event history (`packages/mpe/src/mpe/event_store.py`, `persistence/store.py`), validates every event on append *and* on read, and reconstructs all state and all derived summaries as a pure fold over that history. There is no snapshot subsystem.

The SR-M1 audit found three consequences of what is missing:

1. **The store is append-only by discipline, not by evidence.** Any actor with write access to the SQLite file can edit a payload in place; provided ordering and payload schema still validate, the store accepts it on read. Nothing binds an event's bytes to anything.
2. **No session records when it actually happened.** `timestamp` is a deterministic protocol clock starting at `1.0` and advancing by `0.1`. `wallclock_at` exists in the envelope, the SQLite schema, and the serializer, but `Runtime.emit` never populates it.
3. **No session records what produced it.** `component_version` is the literal `"1.0.0"`; `ProviderSet.check_versions()` verifies provider versions at runtime and then persists nothing; no curriculum, condition, stimulus-set, or policy version exists anywhere in the stream.

A session therefore cannot today be checked for the integrity properties defined in §2.10, carries no self-asserted UTC wall-clock time, and has no recorded software-revision metadata.

---

## 2. Decision

Extend the existing persistence layer with a per-stream hash chain, populate a self-asserted UTC wall-clock time, and introduce one provenance event that every schema-1.2 derived result must causally reference. Concretely, the eleven decisions below.

### 2.1 Integrity extends the existing store; no parallel audit log

The hash chain lives in `packages/mpe/src/mpe/persistence/` (`serializer.py`, `store.py`) as **a native capability of the existing store, unavailable for historical schema-1.1 streams and mandatory for all schema-1.2 streams**. A separate audit-log subsystem is rejected: it would create a second record of runtime activity, and the moment the two disagree there is no principled way to decide which is authoritative. One authoritative history is the whole point of the architecture. This also means the existing `EventStore` protocol continues to be satisfied by both `InMemoryEventStore` and `SQLiteEventStore`, with identical digest semantics on both.

### 2.2 Snapshots are excluded as scientific evidence

No persisted snapshot store is introduced. Projections and summaries remain folds over events. If a snapshot cache is ever added for load performance, it is a cache: discardable at any time, never read as evidence, and never a second source of truth. A test asserts that nothing other than the `events` table is required to produce a `ProtocolSummary`.

### 2.3 Integrity metadata is separate from provenance metadata

Two distinct concerns, deliberately not merged into one "metadata" group:

| Group | Fields | Claim it supports | In the digest input? |
|---|---|---|---|
| **Integrity** | `content_digest`, `previous_digest` | Structural only: these bytes follow those bytes in this stream. No claim about who or what wrote them. | `content_digest` is the output, so not an input; `previous_digest` **is** covered, otherwise the link could be rewritten freely. |
| **Provenance** | `writer_revision`, alongside the existing `component` and `component_version` | Scientific: this software produced this event. | Yes — ordinary envelope content, covered like any other field. |

`writer_revision` is **not** part of the integrity mechanism. It is provenance that the integrity mechanism happens to protect. A matching digest is evidence about bytes, never evidence about authorship, and this ADR states that explicitly so a later reader cannot conflate the two.

#### 2.3.1 Two canonical serializations, not one

Digest input and stored/exported record are **different objects** and must never be described as the same serialization. They share one canonical encoder (sorted keys, fixed separators, `ensure_ascii=False`, deterministic `Identifier`/`CanonicalEnum` handling) and differ in their field sets:

| Function | Purpose | Field set |
|---|---|---|
| `canonical_digest_bytes(event)` | the exact input to `sha256` | **all semantically bound fields, including `previous_digest`**; **excludes `content_digest`**, which is the output of this function and cannot be an input to itself |
| `canonical_record_bytes(event)` | the complete stored row and the exported line | the full record, **including both `content_digest` and `previous_digest`** |

Consequences to respect in implementation: a digest is recomputed from `canonical_digest_bytes` and compared against the stored `content_digest`; export and import use `canonical_record_bytes`; a round-trip through `canonical_record_bytes` must reproduce byte-identical `canonical_digest_bytes`, and a test asserts exactly that. Sharing the encoder is an implementation detail; conflating the two representations would either make the digest self-referential or leave the digest fields unprotected on export.

### 2.4 Three version namespaces; these changes require event schema `1.2`

| Namespace | Where | Meaning | Decision |
|---|---|---|---|
| SQLite `PRAGMA user_version` | the database file | on-disk table layout of the persistence backend | `1` → `2` |
| Event envelope `schema_version` | every event, validated against `SUPPORTED_SCHEMA_VERSIONS` | the canonical MPE event contract | `1.1` → **`1.2`** |
| Software revision | `writer_revision` (new), `component_version` (existing) | which build emitted the event | new field, resolver in §2.7 |

Adding `content_digest`, `previous_digest`, and `writer_revision` to the envelope, and adding `session_provenance_recorded` to `SUPPORTED_EVENT_TYPES`, both change the canonical event contract: a reader implementing only `1.1` cannot validate a `1.2` stream, and a `1.1` writer cannot produce a chain. Therefore `SUPPORTED_SCHEMA_VERSIONS` becomes `{"1.1", "1.2"}`; historical `1.1` streams stay readable, new events are `1.2`, and a single stream must not mix versions — the store rejects a `1.1` append into a `1.2` stream and vice versa.

### 2.5 Integrity status is a property of the stream, not of the file

A store's `PRAGMA user_version` describes only the physical table layout. What may be verified is determined by the **stream**: its `schema_version` and its chain state. The authoritative matrix:

| Store `user_version` | Stream `schema_version` | Chain state | Read behaviour | Status | Append |
|---|---|---|---|---|---|
| 1 | 1.1 | no digest columns exist | readable; existing validation only | `integrity: unavailable` | **refused** — no new appends to a v1 store |
| 2 | 1.1 (historical) | no digests | readable; existing validation only | `integrity: unavailable` | **refused** — the stream is closed to append |
| 2 | 1.2 | complete chain | **verification mandatory** — recompute and compare every digest | `integrity: verified`, or raise `IntegrityError` | allowed, chain continuity enforced |
| 2 | 1.2 | digest fields missing or partial | **invalid** — raise `IntegrityError` on read and on append | error | refused |

The fourth row is deliberate: a schema-1.2 stream with a partial chain is not "partly verified" and not "unavailable", it is corrupt. There is no state in which a 1.2 stream is read without verification through the normal path, and no state in which a 1.1 stream is claimed to be verified.

#### 2.5.1 Backend-independent semantics

`InMemoryEventStore` has no `PRAGMA user_version`, so integrity meaning cannot be derived from storage layout. It is derived from the stream in both backends, identically:

- a schema-1.2 stream **requires** a complete, verified chain;
- a schema-1.1 stream reports `integrity: unavailable` and is closed to append;
- **no partial chains** — a 1.2 stream with any missing digest is an error, not a degraded state;
- **no mixed schema versions within one stream** — enforced on append in both backends.

SQLite `user_version` therefore only answers "does this file have the columns?"; the stream answers "what may be claimed about this data?". The shared `EventStore` contract tests assert the same status semantics against both backends.

#### 2.5.2 Unverified access

An unverified read of a schema-1.2 stream is **not** a flag on the normal API. It is a separately named recovery entry point, `read_unverified(..., reason: str)`, which logs the supplied reason, marks anything it produces `integrity: unverified`, and is called from no normal application path (`Runtime`, `Replay`, `ProtocolSummary`, standard CLI commands). A test asserts that no module outside the recovery path and its own tests references it. Rationale: an opt-in `verify=True` parameter would make the unsafe behaviour the default for every caller that forgets it.

### 2.6 Two clocks now, three later

`timestamp` remains the deterministic protocol clock, so existing replay-equality tests remain valid. `wallclock_at` is populated at emission with UTC epoch seconds through an injectable wall clock, so deterministic tests can pin it. A third clock — the source-device timestamp — is anticipated for Milestone 3 and is not introduced here. The recorded UTC time is a *record*, not a proof: nothing in SR-M1 attests it externally.

### 2.7 Deployment-safe software-revision resolver; git is a development fallback only

One shared function with a strict ordered fallback:

| Order | Source | Typical case | Result |
|---|---|---|---|
| 1 | embedded build metadata (generated `_build_info.py`) | container / wheel builds | `{revision, source: "build_metadata"}` |
| 2 | environment-provided revision (`MPE_SOFTWARE_REVISION`) | CI, orchestrated deployments | `{revision, source: "environment"}` |
| 3 | installed package metadata (`importlib.metadata`) | pip-installed without build stamping | `{revision, source: "package_metadata"}` |
| 4 | `git rev-parse HEAD` plus a dirty-worktree flag | developer working copy only | `{revision, source: "git", dirty: bool}` |
| 5 | none of the above | unknown deployment | `{revision: null, source: "unknown"}` |

`git rev-parse` is explicitly the development-only last resort: a deployed container, a wheel install, or a read-only image has no `.git` directory, and shelling out to git at runtime is fragile and costs startup time. The resolver never raises and never blocks session start. The `source` is always recorded next to the value so a reader can judge its strength. An unresolved revision is recorded as an explicit `unknown` — never an empty string, a placeholder, or a fabricated version. A session reporting `source: "unknown"` remains valid but must be flagged in any downstream scientific report.

### 2.8 Provenance is causally binding for schema 1.2; legacy streams are explicitly discriminated

One new event type, `session_provenance_recorded`, emitted immediately after `session_created`, carrying protocol, curriculum, condition, seed, stimulus-set, policy versions, software revision, and the verified provider-version map. Nullable-by-design fields are explicit `null`, never invented defaults.

Three enforcement mechanisms, so that omission is impossible rather than merely discouraged:

1. `Runtime` refuses to emit any event other than `session_created` until the provenance event has been appended, raising `IllegalStateTransitionError`. Provenance always occupies sequence 2.
2. Derived results carry a **discriminated** provenance reference (§2.8.1), and the normal analysis API raises rather than returning a schema-1.2 result without one.
3. The first trial event of the session lists the provenance event's `EventID` in its existing `provenance` list, so the linkage is visible in the stream, not only in the projection.

#### 2.8.1 Discriminated provenance result model

The earlier absolute phrasing — "an unprovenanced derived result cannot be constructed" — contradicted the requirement that historical `1.1` streams remain analysable. It is replaced by a two-case model that is honest about which case a result belongs to:

```
provenance_status:   "recorded" | "unavailable_legacy"
provenance_event_id: EventID | None
```

The rules, enforced by validation on construction of every derived result:

| `provenance_status` | `provenance_event_id` | Permitted for | Reachable via |
|---|---|---|---|
| `"recorded"` | **required**, must reference a `session_provenance_recorded` event in that stream | schema 1.2 only | the normal analysis API |
| `"unavailable_legacy"` | **must be `None`** | **schema 1.1 only** | an explicitly named legacy API only |

Therefore: a schema-1.2 derived result cannot exist without a valid `session_provenance_recorded` reference; `"recorded"` with a `None` id is invalid; `"unavailable_legacy"` with an id is invalid; and `"unavailable_legacy"` on a schema-1.2 stream is invalid. Schema-1.1 streams may be analysed **only** through the named legacy entry point (e.g. `walk_session_legacy`), which cannot be reached accidentally from the normal path and always produces `unavailable_legacy` results.

The invariant, correctly stated: **no derived result can be silently unprovenanced** — every result declares whether provenance was recorded or is unavailable because the stream predates it, and the unavailable case is confined to schema 1.1 behind a deliberately separate API.

### 2.9 A supported export/import interchange

`packages/mpe/src/mpe/persistence/interchange.py`, surfaced as `mpe export-session` and `mpe import-session`. Export emits one canonical JSON object per line, in ascending sequence, using the same encoding as the digest, and reads through the verified path — refusing to export a stream that fails verification. Import appends through the **ordinary** `append` / `append_batch` API, so every existing invariant is re-applied on ingest, and refuses to write into a stream that already exists.

This exists so that "rebuild from an empty database" is a property of the system rather than of a test that pokes SQLite tables directly. It is an internal reproducibility path — explicitly not a scientific archive format, and not BIDS.

### 2.10 Threat model and its limits

On a stream we already hold, the chain detects:

- mutation of any event's content;
- deletion of an interior event;
- insertion of an event;
- reordering of events.

**It does not detect removal of the tail of the stream.** A truncated chain is internally consistent: every remaining link verifies, and nothing in the retained data distinguishes "the stream ended here" from "the stream was cut here". Tail truncation is detectable only against an **independently retained expected terminal state** — a separately stored terminal digest, a separately stored event count, a signed manifest, or an external append-only log. **SR-M1 delivers no such anchor.** The verifier accepts an optional `expected_terminal` input so a future milestone can supply one, and reports `tail_truncation: pass|fail` when it is supplied and `undetermined` when it is not; producing, retaining, distributing, or signing an anchor is out of scope and must not be described as delivered.

The chain further does **not**:

- prove authorship — it says nothing about who ran the writer;
- prove the recorded time — `wallclock_at` is self-asserted, with no external timestamping;
- protect against a full rewrite of the entire chain by an actor holding the writer, who can recompute every digest.

The system is **tamper-evident**. It is not tamper-proof, and no document, docstring, report, or CLI output may describe it as such, nor as detecting truncation.

### 2.11 Migration of existing stores

Existing `user_version = 1` / schema `1.1` stores remain readable and report `integrity: unavailable`. They are **not** rewritten to add digests: rewriting historical events would itself be a mutation, and would fabricate provenance that was never recorded.

The structural migration from database v1 to v2 is exactly this, and nothing more:

1. `ALTER TABLE events` to add the new columns — `content_digest`, `previous_digest`, `writer_revision` — all **nullable**, so existing rows remain valid without modification;
2. `PRAGMA user_version = 2`;
3. **do not rewrite, re-encode, or re-digest any historical event**;
4. preserve every existing schema-1.1 session exactly as stored: readable, `integrity: unavailable`, and closed to further append;
5. write **only new sessions** as schema 1.2, with a complete chain from sequence 1.

A migrated v2 file therefore legitimately contains both kinds of stream side by side, distinguished by the stream's `schema_version` (§2.5), not by the file. A `1.1` stream can never be extended with a `1.2` event, and migration is one-way — no downgrade path is provided.

---

## 3. Alternatives considered

| Alternative | Rejected because |
|---|---|
| Separate audit-log subsystem alongside the event store | Creates a second source of truth; contradicts the one-authoritative-history principle; divergence would be unresolvable |
| Periodic state snapshots as the record of a session | Snapshots are caches, not evidence; a snapshot cannot be independently re-derived and invites treating a cached projection as scientific fact |
| Content-addressed event IDs (`event_id = digest`) instead of a chain | Binds content but not order or completeness; a deleted interior event would still be undetectable, and it would break the existing typed `EventID` contract |
| Merkle tree over the stream instead of a linear chain | Real benefit only for partial-proof or large-scale verification, neither of which SR-M1 needs; strictly more complexity for the same truncation limitation |
| Signing each event with a key held by the writer | Would begin to address authorship, but requires key management, distribution, and rotation that this project has no infrastructure or threat justification for; deferred, not rejected in principle |
| Opt-in `verify=True` parameter on `read` | Makes the unsafe path the default for every caller who forgets the flag |
| No new event type — put provenance in `session_started`'s payload | Would overload an existing typed payload, and would still leave nothing that derived results can causally reference |
| Deferring the schema bump and adding the fields as "optional 1.1" | A `1.1` reader would silently ignore integrity fields and report unverified data as valid; version boundaries exist precisely for this |

---

## 4. Consequences

**Positive.** A schema-1.2 session becomes verifiable for the integrity properties defined in §2.10, recorded with a self-asserted UTC wall-clock time, and associated with recorded software-revision, protocol, seed, and provider-version metadata. Derived results declare their provenance status rather than leaving it implicit. Reproducibility becomes a testable property via a supported export/import path.

**Negative / accepted costs.**

- An event-schema bump to `1.2`, with two supported versions to maintain and a legacy path for `1.1` streams.
- Digest computation on every append and every read; expected to be negligible against SQLite I/O, but it is real work on the hot path.
- Historical `1.1` sessions can never be retrofitted with integrity or provenance, are closed to further append, are analysable only through the named legacy API, and are permanently weaker evidence.
- Tail truncation remains undetected until a future milestone delivers an anchor. This is an accepted, documented residual risk (audit R1b), not an oversight.
- A `source: "unknown"` software revision is a valid but weaker session, and downstream reports must carry that flag.

**Out of scope for this ADR.** Behavioral-analysis policies, reaction-time derivation, SDT, power analysis; device capability profiles, EEG acquisition or preprocessing, feature provenance; BIDS export, publication bundles, Methods appendices; any regulatory claim. Also out of scope: any anchoring, signing, or trusted-timestamping mechanism. The audio pipeline is a separate product workstream and is not part of SR-M1.

---

## 5. Verification

This ADR is satisfied when the SR-M1 test suite demonstrates all of the following:

1. digest stability across processes;
2. rejection of an in-place payload edit, an interior deletion, an insertion, and a reordering;
3. **acceptance** of a truncated tail with `tail_truncation: undetermined`, and rejection only when an `expected_terminal` is supplied — the executable statement of §2.10;
4. the four rows of the §2.5 status matrix, each asserted independently, including that a schema-1.2 stream with a partial chain raises `IntegrityError` rather than reporting `unavailable`; and `read_unverified` reachable only from the recovery path;
5. the same status semantics asserted against `InMemoryEventStore` and `SQLiteEventStore` through the shared contract tests (§2.5.1);
6. the two canonical serializations are distinct and mutually consistent: `content_digest` is absent from `canonical_digest_bytes` and present in `canonical_record_bytes`, and a `canonical_record_bytes` round-trip reproduces byte-identical `canonical_digest_bytes` (§2.3.1);
7. a full stream exported and re-imported into an empty database yielding an identical terminal digest, `RuntimeState.as_dict()`, and derived summary;
8. no artifact other than the `events` table required to produce a derived summary;
9. explicit failure on unsupported `schema_version` and on mixing `1.1` and `1.2` within one stream;
10. inability to emit past `session_created` without provenance on schema 1.2; the discriminated model of §2.8.1 rejects `"recorded"` with a `None` id, `"unavailable_legacy"` with an id, and `"unavailable_legacy"` on a schema-1.2 stream; and `unavailable_legacy` results are reachable only through the named legacy API;
11. **migration acceptance test.** A database structurally migrated from `user_version = 1` to `user_version = 2` must: preserve historical schema-1.1 streams byte-unchanged and readable with `integrity: unavailable`; accept new schema-1.2 sessions and report them `integrity: verified`; and refuse a schema-1.2 append to a historical schema-1.1 stream;
12. property-based determinism over generated valid streams (`hypothesis`).

---

## 6. Decision record

`APPROVE_ADR_0001` / `APPROVE_ADR_0001_WITH_CONDITIONS` / `REVISE_ADR_0001` / `BLOCK_ADR_0001`

Awaiting review. No SR-M1 production code may be written until one of the approving tokens is recorded here.
