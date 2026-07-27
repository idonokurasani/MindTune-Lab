# ADR-0001 — Event integrity and provenance

**Status:** Proposed — published for review. No production code may be written against this ADR until it is approved.
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

A session therefore cannot today be independently verified, dated, or attributed to a build.

---

## 2. Decision

Extend the existing persistence layer with a per-stream hash chain, populate a real recorded time, and introduce one provenance event that every derived result must causally reference. Concretely, the eleven decisions below.

### 2.1 Integrity extends the existing store; no parallel audit log

The hash chain lives in `packages/mpe/src/mpe/persistence/` (`serializer.py`, `store.py`) as an optional capability of the store that already exists. A separate audit-log subsystem is rejected: it would create a second record of runtime activity, and the moment the two disagree there is no principled way to decide which is authoritative. One authoritative history is the whole point of the architecture. This also means the existing `EventStore` protocol continues to be satisfied by both `InMemoryEventStore` and `SQLiteEventStore`, with identical digest semantics on both.

### 2.2 Snapshots are excluded as scientific evidence

No persisted snapshot store is introduced. Projections and summaries remain folds over events. If a snapshot cache is ever added for load performance, it is a cache: discardable at any time, never read as evidence, and never a second source of truth. A test asserts that nothing other than the `events` table is required to produce a `ProtocolSummary`.

### 2.3 Integrity metadata is separate from provenance metadata

Two distinct concerns, deliberately not merged into one "metadata" group:

| Group | Fields | Claim it supports | In the digest input? |
|---|---|---|---|
| **Integrity** | `content_digest`, `previous_digest` | Structural only: these bytes follow those bytes in this stream. No claim about who or what wrote them. | `content_digest` is the output, so not an input; `previous_digest` **is** covered, otherwise the link could be rewritten freely. |
| **Provenance** | `writer_revision`, alongside the existing `component` and `component_version` | Scientific: this software produced this event. | Yes — ordinary envelope content, covered like any other field. |

`writer_revision` is **not** part of the integrity mechanism. It is provenance that the integrity mechanism happens to protect. A matching digest is evidence about bytes, never evidence about authorship, and this ADR states that explicitly so a later reader cannot conflate the two.

### 2.4 Three version namespaces; these changes require event schema `1.2`

| Namespace | Where | Meaning | Decision |
|---|---|---|---|
| SQLite `PRAGMA user_version` | the database file | on-disk table layout of the persistence backend | `1` → `2` |
| Event envelope `schema_version` | every event, validated against `SUPPORTED_SCHEMA_VERSIONS` | the canonical MPE event contract | `1.1` → **`1.2`** |
| Software revision | `writer_revision` (new), `component_version` (existing) | which build emitted the event | new field, resolver in §2.7 |

Adding `content_digest`, `previous_digest`, and `writer_revision` to the envelope, and adding `session_provenance_recorded` to `SUPPORTED_EVENT_TYPES`, both change the canonical event contract: a reader implementing only `1.1` cannot validate a `1.2` stream, and a `1.1` writer cannot produce a chain. Therefore `SUPPORTED_SCHEMA_VERSIONS` becomes `{"1.1", "1.2"}`; historical `1.1` streams stay readable, new events are `1.2`, and a single stream must not mix versions — the store rejects a `1.1` append into a `1.2` stream and vice versa.

### 2.5 Verification is the default read path for v2 stores

| Store `user_version` | `read` / `all_events` | Status reported |
|---|---|---|
| 2 | recompute and compare every digest; raise `IntegrityError` at the first divergence | `integrity: verified`, or an error |
| 1 | no chain exists to check; existing validation still applies | `integrity: unavailable` |

An unverified read of a v2 store is **not** a flag on the normal API. It is a separately named recovery entry point, `read_unverified(..., reason: str)`, which logs the supplied reason, marks anything it produces `integrity: unverified`, and is called from no normal application path (`Runtime`, `Replay`, `ProtocolSummary`, standard CLI commands). A test asserts that no module outside the recovery path and its own tests references it. Rationale: an opt-in `verify=True` parameter would make the unsafe behaviour the default for every caller that forgets it.

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

### 2.8 Provenance is causally binding, not conventional

One new event type, `session_provenance_recorded`, emitted immediately after `session_created`, carrying protocol, curriculum, condition, seed, stimulus-set, policy versions, software revision, and the verified provider-version map. Nullable-by-design fields are explicit `null`, never invented defaults.

Three enforcement mechanisms, so that omission is impossible rather than merely discouraged:

1. `Runtime` refuses to emit any event other than `session_created` until the provenance event has been appended, raising `IllegalStateTransitionError`. Provenance always occupies sequence 2.
2. `ProtocolSummary` (and any future derived-analysis record) gains a **required** `provenance_event_id`, and `summary_walk.walk_session` raises rather than returning a summary when no provenance event is present — including for historical `1.1` streams, which go through an explicitly labelled legacy path that marks provenance as absent instead of silently producing an unprovenanced result.
3. The first trial event of the session lists the provenance event's `EventID` in its existing `provenance` list, so the linkage is visible in the stream, not only in the projection.

The invariant: an unprovenanced derived result cannot be constructed.

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

Existing `user_version = 1` / schema `1.1` stores remain readable and report `integrity: unavailable`. They are **not** rewritten to add digests: rewriting historical events would itself be a mutation, and would fabricate provenance that was never recorded. New sessions are written as `1.2` into `user_version = 2` stores. `1.1` streams cannot be extended with `1.2` events.

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

**Positive.** A session becomes independently verifiable against interior tampering, dated with a recorded UTC time, and attributable to a build, a protocol version, a seed, and a verified provider set. Derived results cannot be produced without a provenance reference. Reproducibility becomes a testable property via a supported export/import path.

**Negative / accepted costs.**

- An event-schema bump to `1.2`, with two supported versions to maintain and a legacy path for `1.1` streams.
- Digest computation on every append and every read; expected to be negligible against SQLite I/O, but it is real work on the hot path.
- Historical `1.1` sessions can never be retrofitted with integrity or provenance, and are permanently weaker evidence.
- Tail truncation remains undetected until a future milestone delivers an anchor. This is an accepted, documented residual risk (audit R1b), not an oversight.
- A `source: "unknown"` software revision is a valid but weaker session, and downstream reports must carry that flag.

**Out of scope for this ADR.** Behavioral-analysis policies, reaction-time derivation, SDT, power analysis; device capability profiles, EEG acquisition or preprocessing, feature provenance; BIDS export, publication bundles, Methods appendices; any regulatory claim. Also out of scope: any anchoring, signing, or trusted-timestamping mechanism. The audio pipeline is a separate product workstream and is not part of SR-M1.

---

## 5. Verification

This ADR is satisfied when the SR-M1 test suite demonstrates all of the following:

1. digest stability across processes;
2. rejection of an in-place payload edit, an interior deletion, an insertion, and a reordering;
3. **acceptance** of a truncated tail with `tail_truncation: undetermined`, and rejection only when an `expected_terminal` is supplied — the executable statement of §2.10;
4. verified-by-default reads on v2 stores, `integrity: unavailable` on v1, and `read_unverified` reachable only from the recovery path;
5. a full stream exported and re-imported into an empty database yielding an identical terminal digest, `RuntimeState.as_dict()`, and `ProtocolSummary`;
6. no artifact other than the `events` table required to produce a `ProtocolSummary`;
7. explicit failure on unsupported `schema_version` and on mixing `1.1` and `1.2` within one stream;
8. inability to emit past `session_created` without provenance, and inability to construct an unprovenanced `ProtocolSummary`;
9. property-based determinism over generated valid streams (`hypothesis`).

---

## 6. Decision record

`APPROVE_ADR_0001` / `APPROVE_ADR_0001_WITH_CONDITIONS` / `REVISE_ADR_0001` / `BLOCK_ADR_0001`

Awaiting review. No SR-M1 production code may be written until one of the approving tokens is recorded here.
