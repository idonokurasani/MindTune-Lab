# MPE Phase 4C.1 — Minimal Protocol Vertical Slice Plan

**Document:** `docs/implementation/phase4c1/MPE_PHASE_4C1_MINIMAL_PROTOCOL_VERTICAL_SLICE_PLAN.md`
**Type:** Architecture + implementation-planning (documentation only)
**Date:** 2026-07-24
**Protocol in scope:** **Immediate Recall** (exactly one)

> **Documentation-only.** No production code is written, no Git action is taken, `mpe_audio` is not implemented, and no EEG / ASR / live TTS / spaced repetition / Hebrew-specific logic is introduced. This plan describes *what to build* and *how to verify it against the real repository* before building.

> **PROVISIONAL_DESIGN_MAPPING notice (applies to the entire document).** Every reference to a repository contract, symbol, event name, CLI command, package path, method signature, test command, or file location is a **PROVISIONAL_DESIGN_MAPPING**. The MPE source repository was **not available on the planning host**, so **nothing here is source-verified**. No symbol is claimed to be "implemented" unless explicitly established by approved repository documentation cited inline. All mappings must be reconciled against the local repository before any implementation begins (see **§3 REPOSITORY VERIFICATION REQUIRED BEFORE IMPLEMENTATION** and the **§17 Disk handoff checklist**).

---

## Table of contents

1. Objective
2. Architectural boundaries
3. **REPOSITORY VERIFICATION REQUIRED BEFORE IMPLEMENTATION**
4. Repository assumptions
5. Minimal Immediate Recall semantics
6. Contract mapping (PROVISIONAL_DESIGN_MAPPING)
7. Proposed file/package changes
8. Event matrix
9. State and data flow
10. Persistence and replay design
11. CLI proposal
12. Test matrix
13. Implementation sequence
14. Risks
15. Exclusions
16. Acceptance criteria
17. Disk handoff checklist
18. Stop conditions
19. Final recommendation

---

## 1. Objective

Design the **smallest possible end-to-end protocol implementation** that proves the **MPE Protocol Library v1.0** can execute through the **existing MPE runtime** — persistence (Phase 4B.2), CLI (Phase 4B.3), event/replay model — **without introducing a second DSL** and **without breaking any existing contract**.

The slice implements exactly one protocol, **Immediate Recall**, over a **domain-neutral fixture** with opaque item identifiers, using **only fixture/pre-existing audio assets** (no provider, no SpeechGen, no live synthesis). It exercises the full target flow:

```
Protocol definition
  → planning
  → typed MPE instructions
  → execution
  → observations
  → bounded adaptation (one rule, cap 1 repeat)
  → emitted events
  → persistence
  → event replay
  → derived protocol summary
```

Success = this flow runs deterministically, round-trips through persistence, replays with equality, and yields a summary derived purely from events — proving the Protocol Library architecture is executable and additive.

---

## 2. Architectural boundaries

**In scope**

- One protocol: Immediate Recall (domain-neutral).
- One bounded adaptation rule (repeat-once-on-negative/slow; cap = 1).
- A minimal, **additive** protocol-definition structure (only if existing typed contracts are insufficient — see §6).
- A fixture domain (`item.alpha`, `item.beta`) with deterministic self-confirmation input and fixture audio assets.
- Reuse of existing typed MPE contracts, events, persistence, replay, and CLI wherever they exist.

**Out of scope (hard boundaries)** — see §15 for the full list: mpe_audio implementation, SpeechGen/provider calls, live TTS, ASR, EEG, spaced-repetition scheduling, full taxonomy, domain adapters (Hebrew/Piano), stochastic policies, multi-protocol composition, counterfactual/protocol replay (deferred; see §10).

**Invariants preserved (from approved docs)**

- **No second DSL.** The protocol is expressed through typed instructions/contracts, not a textual grammar.
- **Provider invisibility & no synchronous synthesis in execution** (Audio Pipeline Phase A).
- **Behavior authoritative; latency is only a proxy; no EEG** (Protocol Library §8–§10).
- **Do not weaken Phase 4B.2 replay guarantees** (deterministic ordering, asset-version pinning).
- **Additive-only** extensions to existing event/persistence/CLI contracts (Protocol Library Phase A Acceptance Record, conditions C2/C3).

---

## 3. REPOSITORY VERIFICATION REQUIRED BEFORE IMPLEMENTATION

> **This section is mandatory and blocking.** The planning host had **no access to the MPE source repository**. A full-filesystem search found no `packages/mpe/...`, no `PROJECT_STATE.md`/`NEXT_TASK.md`, and no project `.git`. Consequently:
>
> 1. **Every** contract/symbol/event/CLI/path/signature/test-command reference in this plan is a **PROVISIONAL_DESIGN_MAPPING**, not a verified fact.
> 2. **No source-level verification is claimed** anywhere in this document.
> 3. **No symbol is classified as "implemented"** unless an approved repository document explicitly establishes it; where a doc is cited, it is the *documentation* that is the basis, not inspected source.
> 4. Implementation **must not begin** until the §17 Disk handoff checklist is completed against the real repository and each PROVISIONAL_DESIGN_MAPPING in §6/§8/§11/§12 is either **confirmed** or **replaced with the actual symbol**, applying the stated fallback.
> 5. This plan is **implementation-ready in structure** but deliberately **does not invent repository structure, method signatures, event names, CLI syntax, or package paths as facts**. Where a concrete name is shown, it is a *candidate* to be verified, always paired with a fallback.

The final recommendation (§19) is therefore explicitly **conditional on local repository reconciliation** and is never a clean approval.

---

## 4. Repository assumptions

These are **assumptions**, each traceable to an approved document (not to source). If any is false, the dependent mappings in §6 change per their fallbacks.

| # | Assumption | Supporting approved document | If false |
|---|---|---|---|
| A1 | An MPE runtime with a typed **event model** and **event store** exists (append + replay). | "MPE Protocol Engine runtime and event model"; Phase 4B.2 persistence & replay | Treat all event mappings as NEW; re-scope §8 |
| A2 | **Persistence + event replay** exist with deterministic ordering and asset-version pinning (SQLite + in-memory backends). | Phase 4B.2 persistence & replay; Protocol Library Phase A Acceptance Record §7 | Re-scope §10; may raise to REVISE |
| A3 | A **CLI** exists under an `mpe` entry point with a subcommand surface, exit-code contract, and JSON output mode. | Phase 4B.3 CLI | Re-scope §11 to actual CLI surface |
| A4 | Typed contracts exist or are named for **Instruction, StimulusRequest, RenderedStimulus, Observation, AdaptationDecision, ScheduleDecision**. | Task brief; Protocol Library v1.0 §12 (conceptual); Audio Pipeline Phase A | For any missing one, use its fallback in §6 |
| A5 | An **approved-asset registry / asset-version pin** concept exists (or fixtures can stand in). | Audio Pipeline Phase A (registry, immutable versioned assets) | Use fixture manifest with explicit version field (§5.3) |
| A6 | The Protocol Library object model (`Protocol`, `ProtocolStep`, `ExecutionPlan`, `ExecutionResult`, `ProtocolSummary`) is **conceptual/new**, not yet implemented. | Protocol Library v1.0 §12; Phase A Acceptance Record §3 (NEW) | Confirm additive; no change to verdict |

> **Note on A4/A6:** the task brief lists `Instruction, StimulusRequest, RenderedStimulus, Observation, AdaptationDecision, ScheduleDecision` as *pre-existing* typed contracts to reuse. This plan treats their **existence and names as PROVISIONAL** (established, if at all, by runtime/event-model documentation), and never asserts their signatures.

---

## 5. Minimal Immediate Recall semantics

### 5.1 Cognitive framing (from Protocol Library v1.0 §7.2.1)

Immediate Recall strengthens retrieval immediately after encoding: **cue → retrieve internally → confirm**. Primary goal: *Retrieve*. Behavior (self-confirmation) is authoritative; latency is a proxy only.

### 5.2 Exact minimal step sequence (per item)

```
STEP 1  present cue                (primitive: Play stimulus  — role=prompt/cue)
STEP 2  open anticipation window   (primitive: Pause + Expect internal response)
STEP 3  collect observation        (primitive: Observe → self-confirmation from fixture; latency proxy)
STEP 4  present confirmation       (primitive: Confirm       — role=confirmation)
STEP 5  bounded adaptation         (primitive: Branch)
          if observation is negative OR slow  → Repeat once (go to STEP 1 for same item), cap=1
          else                                → complete item
STEP 6  complete item              (primitive: Transition — item done; Record item outcome)
--- after all items ---
STEP 7  complete protocol          (primitive: Transition — protocol done; Record completion)
```

**Primitive coverage (Protocol Library §6):** Play stimulus, Pause, Expect internal response, Observe, Confirm, Branch, Repeat, Transition, Record. `Score` is *not* used (no machine grading — the fixture provides a deterministic self-confirmation observation, which is behavioral evidence). `Wait`, `Explain` unused in execution.

### 5.3 Domain-neutral fixture

A fixture "domain" with **opaque** identifiers — no Hebrew, no linguistic concepts.

```
fixture: "minimal"
items:
  - item_id: "item.alpha"
      cue_asset_ref:          { item: "item.alpha", role: "cue",          version: "<pinned>" }
      confirmation_asset_ref: { item: "item.alpha", role: "confirmation", version: "<pinned>" }
      expected_relation:      "associate(item.alpha.cue, item.alpha.target)"   # abstract only
      deterministic_self_confirmation: "positive"     # fixture-provided observation
  - item_id: "item.beta"
      cue_asset_ref:          { item: "item.beta", role: "cue",          version: "<pinned>" }
      confirmation_asset_ref: { item: "item.beta", role: "confirmation", version: "<pinned>" }
      expected_relation:      "associate(item.beta.cue, item.beta.target)"
      deterministic_self_confirmation: "negative"     # drives the repeat path deterministically
```

- **Assets are fixtures** (checked-in test audio or silent placeholder assets) with an explicit **version** field so asset-version pinning is exercised without any provider.
- **`deterministic_self_confirmation`** makes execution fully deterministic and testable (positive → no repeat; negative → one repeat). No live user input, no EEG, no ASR.
- The fixture supplies **cue asset, confirmation asset, expected relation, deterministic self-confirmation input** exactly as the task allows.

### 5.4 Bounded adaptation rule (single rule)

- **negative** self-confirmation **or** latency above a fixed bound → **one** bounded repeat of the item (back to STEP 1).
- **positive** self-confirmation → complete the item.
- **repetition count capped at 1** (a second negative after the one allowed repeat → complete the item anyway, recording it as unresolved).
- **Behavior authoritative** (self-confirmation decides); **latency is a proxy** that can only *trigger the same bounded repeat*, never mark correctness; **no EEG**.

---

## 6. Contract mapping (PROVISIONAL_DESIGN_MAPPING)

For every mapping: **assumed contract/symbol · source document supporting the assumption · exact point Disk must verify · fallback if the assumed contract differs.** Ratings: **REUSE** (existing, reused), **EXTEND** (existing + additive payload), **NEW** (new structure), **DERIVED** (computed, not persisted). All ratings are provisional.

| Conceptual element | Assumed symbol (PROVISIONAL) | Source doc for assumption | Disk must verify | Fallback | Rating |
|---|---|---|---|---|---|
| Protocol definition | `Protocol` / `ProtocolStep` (small additive struct) | Protocol Library v1.0 §12 (conceptual/NEW) | Whether any protocol-definition type already exists; if not, add minimal additive struct | Define a minimal in-package dataclass-like struct; no core-contract change | NEW |
| Typed instruction | `Instruction` | Task brief; runtime/event-model doc | Actual `Instruction` type name, fields, discriminant | Wrap steps in the actual instruction type; if none, add additive instruction variants | REUSE (assumed) |
| Stimulus request | `StimulusRequest` | Task brief; Audio Pipeline Phase A | Exact request shape + how asset ref/version is expressed | Use actual field names; if absent, add additive request carrying (item, role, version) | REUSE (assumed) |
| Rendered stimulus | `RenderedStimulus` | Task brief | Whether rendering resolves a **local** asset + returns version | Map to actual type; if absent, fixture resolver returns (path, version) | REUSE (assumed) |
| Observation | `Observation` | Task brief; Protocol Library §10 | Field for self-confirmation value + latency proxy | Extend additively (payload field) or add observation subtype | REUSE / EXTEND |
| Adaptation decision | `AdaptationDecision` | Task brief; Protocol Library §8 | Fields: source, parameter, prev/new, reason | Extend additively; must record source=behavior/latency, cap | REUSE / EXTEND |
| Schedule decision | `ScheduleDecision` | Task brief | Whether it applies to non-spaced flows; may be **unused** here | If spacing-only, do **not** use it (no scheduler in slice); document as N/A | REUSE (likely N/A) |
| Execution plan | `ExecutionPlan` | Protocol Library §12 (NEW) | Confirm no existing authoritative plan contract | Minimal additive planning struct; not persisted as core contract | NEW |
| Execution result | `ExecutionResult` | Protocol Library §12 | Composed from session+events | DERIVED from event stream | DERIVED |
| Protocol summary | `ProtocolSummary` vs `SessionSummary` | Phase 4B.3 CLI (`SessionSummary`, `list_sessions()`); Phase A Acceptance Record §3 | Whether summary can be a deterministic-ordering superset of `SessionSummary` | Derive summary from events; keep minimal + deterministic ordering | DERIVED / EXTEND |
| Event store | `EventStore.append` / replay | Phase 4B.2 persistence & replay | Append + replay API names, ordering guarantees | Use actual API; if names differ, adapt caller only | REUSE |
| Asset-version pin | approved-asset registry / pinned version | Audio Pipeline Phase A | How versions are represented + pinned in events | Fixture manifest version field carried into events | REUSE / EXTEND |
| CLI | `mpe` entry point + subcommands | Phase 4B.3 CLI | Actual command/option grammar, exit codes, JSON mode | Add subcommand under existing parser; match exit-code contract | REUSE / EXTEND |

> **No symbol above is asserted to exist in source.** Where "REUSE (assumed)" appears, existence is assumed from documentation only and must be confirmed (§17).

---

## 7. Proposed file/package changes (PROVISIONAL_DESIGN_MAPPING)

> Package paths are **candidates**, not facts. Do not create these paths until §17 confirms the real layout. Prefer the **smallest additive** footprint inside the existing `mpe` package (per Acceptance Record: additive-only).

| Candidate path (PROVISIONAL) | Purpose | Rating | Verify (Disk) |
|---|---|---|---|
| `packages/mpe/src/mpe/protocol/immediate_recall.py` | Minimal Immediate Recall definition + step builder | NEW (additive) | Confirm `protocol/` subpackage location or actual convention |
| `packages/mpe/src/mpe/protocol/plan.py` | Minimal `ExecutionPlan` builder (planning) | NEW (additive) | Confirm no existing plan contract to reuse |
| `packages/mpe/src/mpe/protocol/fixture_minimal.py` | Domain-neutral fixture (items + deterministic self-confirmation + fixture assets) | NEW (additive) | Confirm fixture/test-data convention |
| `packages/mpe/src/mpe/protocol/summary.py` | Derive `ProtocolSummary` from events | NEW (additive, DERIVED) | Confirm relation to `SessionSummary` |
| `packages/mpe/src/mpe/cli.py` (+`cli_helpers.py`, `__main__.py`) | Add `protocol run` / `protocol show` subcommand(s) | EXTEND | Confirm CLI wiring + exit-code contract |
| `packages/mpe/tests/test_protocol_immediate_recall.py` | Slice acceptance tests (§12) | NEW (additive) | Confirm test dir + runner (Phase 4B.3 used `unittest discover`) |
| `packages/mpe/tests/fixtures/audio/...` | Fixture/placeholder audio assets with pinned versions | NEW (additive) | Confirm fixture storage + size limits |

**Explicitly not changed:** any existing event/persistence/replay/CLI *contract semantics*; `PROJECT_STATE.md`; `NEXT_TASK.md`; `mpe_audio` (unimplemented).

---

## 8. Event matrix

Every event the slice must emit, classified per the task: **existing & reused**, **existing + additive payload extension**, **new event required**, or **derived only (not persisted)**. **All classifications are PROVISIONAL** and must be reconciled (§17, item 3).

| # | Event (candidate name) | When | Classification (PROVISIONAL) | Payload essentials | Verify (Disk) / Fallback |
|---|---|---|---|---|---|
| E1 | `SessionStarted` | plan → execution begins | existing & reused | session_id, protocol id, fixture id, plan hash | Confirm existing session-start event; else NEW |
| E2 | `StimulusPresented` (cue) | STEP 1 | existing + additive payload | item_id, asset ref, **asset_version pin**, role=cue, onset/offset | Confirm stimulus/render event; add role+version if missing |
| E3 | `WindowOpened` / anticipation | STEP 2 | new event required (likely) | item_id, window bound | If a generic timing event exists, reuse; else NEW additive |
| E4 | `ObservationRecorded` | STEP 3 | existing + additive payload | item_id, self_confirmation (pos/neg), latency proxy, source=behavior | Confirm `Observation` event; add self-confirm field |
| E5 | `StimulusPresented` (confirmation) | STEP 4 | existing + additive payload | item_id, asset ref, version, role=confirmation | As E2 |
| E6 | `AdaptationDecided` | STEP 5 | existing + additive payload | source (behavior/latency), rule id, decision=repeat/complete, prev/new repeat_count, cap=1 | Confirm `AdaptationDecision` event; add fields |
| E7 | `ItemCompleted` | STEP 6 | new event required (likely) | item_id, outcome (resolved/unresolved), repeats_used | If item-scope event exists, reuse; else NEW additive |
| E8 | `SessionCompleted` / `ProtocolCompleted` | STEP 7 | existing & reused | session_id, completion reason, counts | Confirm existing completion event |
| — | `ProtocolSummary` | post-hoc | **derived only, not persisted** | aggregates from E1–E8 | Derived at read time (§10.6) |

**Rules honored:** reuse existing events wherever possible; every new/extended event is **additive** and must not change existing event semantics (Acceptance Record C2). Asset-version pins ride on E2/E5 so replay is exact.

---

## 9. State and data flow

```
                 ┌──────────────────────────────────────────────┐
                 │ Fixture "minimal" (opaque items + assets +     │
                 │ deterministic self-confirmation + versions)    │
                 └───────────────┬──────────────────────────────┘
                                 │ (planning)
                 ┌───────────────▼──────────────┐
                 │ ExecutionPlan (NEW, additive) │  selected protocol, items,
                 │  - protocol: immediate-recall │  asset-version pins, timing
                 │  - items: [alpha, beta]       │  bounds, deterministic order,
                 │  - pins, bounds, order, sid   │  session identity
                 └───────────────┬──────────────┘
                                 │ typed Instructions (REUSE assumed)
                 ┌───────────────▼──────────────┐
                 │ Execution (runtime executor)  │  Play→Pause/Expect→Observe→
                 │  per item, per step (§5.2)     │  Confirm→Branch(cap1)→Transition
                 └───────┬───────────────┬───────┘
                         │ observations  │ adaptation decisions
                         ▼               ▼
                 ┌──────────────────────────────┐
                 │ Events E1..E8 (append)         │  behavior authoritative,
                 │  → EventStore (REUSE)          │  latency proxy, no EEG
                 └───────────────┬──────────────┘
                                 │ persist (Phase 4B.2)
                 ┌───────────────▼──────────────┐
                 │ Persistence (SQLite/in-memory) │  deterministic order,
                 └───────────────┬──────────────┘  asset-version pinned
                                 │ event replay (Phase 4B.2)
                 ┌───────────────▼──────────────┐
                 │ Replay == original event seq   │  (equality guarantee)
                 └───────────────┬──────────────┘
                                 │ derive
                 ┌───────────────▼──────────────┐
                 │ ProtocolSummary (DERIVED)      │  items, repeats_used,
                 └──────────────────────────────┘  outcomes, timing aggregates
```

Durable learning-state (`state_deltas`) is **not** introduced in this slice (no scheduler, no mastery store); the summary is derived from events only.

---

## 10. Persistence and replay design

1. **What must be persisted:** the ordered event stream E1–E8 for the session, including **asset-version pins** on stimulus events. `ExecutionPlan` may be persisted as a plan record or reconstructed; **do not** make it a new authoritative core contract if the session+events already capture everything (prefer events as record of truth).
2. **Deterministic event ordering:** events are appended in execution order with a monotonic per-session sequence; ordering must match Phase 4B.2 guarantees. The fixture's deterministic self-confirmation makes the entire sequence reproducible.
3. **Asset-version pinning:** E2/E5 carry the exact pinned asset version from the fixture manifest; replay resolves the same versioned asset. This exercises the Audio Pipeline Phase A immutability/versioning principle **without any provider**.
4. **Event replay expectations:** replaying the persisted stream reproduces the **identical** event sequence and payloads (including pins). **No weakening of Phase 4B.2 replay guarantees.** Replay equality is a test (§12 T7).
5. **Protocol replay:** **DEFERRED** in this slice (Protocol Library §15.2; Acceptance Record NEW capability). Only **event replay** is implemented now; counterfactual/EEG-ablation replay is explicitly out of scope (§15).
6. **Summary derivation:** `ProtocolSummary` is computed **from the replayed/persisted events** (DERIVED, not persisted): per-item outcome, `repeats_used`, cap enforcement, latency aggregates, completion reason. Deriving from events (not from live state) guarantees the summary is reproducible and replay-consistent.

---

## 11. CLI proposal (PROVISIONAL_DESIGN_MAPPING)

Minimum surface, **preferably under the existing `mpe` CLI** as an additive subcommand group. **Exact syntax is PROVISIONAL** and must not conflict with the current CLI (Phase 4B.3 defined `run-mock-session`, `replay`, `list-sessions`, `validate-store` with exit codes 0–6 and single-document JSON on stdout).

| Candidate command (PROVISIONAL) | Purpose | Verify (Disk) / Fallback |
|---|---|---|
| `mpe protocol run --protocol immediate-recall --fixture minimal [--json]` | Plan + execute + persist one session; print session id / JSON summary | Confirm subcommand style vs flat verbs; if flat convention, use e.g. `mpe run-protocol`; match existing option placement |
| `mpe protocol show <session_id> [--json]` | Derive + print the protocol summary from persisted events | If `replay`/`list-sessions` already render summaries, extend those instead of adding `show` |

**Contract conformance (must match Phase 4B.3):** success → stdout only, exit 0; usage/argument error → exit 2; not-found → exit 3; corrupted store → exit 4; DB unavailable/lock → exit 5; invariant violation → exit 6; unexpected → exit 1. JSON mode emits exactly one JSON document; no logs/tracebacks on JSON stdout. **These are PROVISIONAL** and must be reconciled against the actual exit-code/stdout contract.

---

## 12. Test matrix

Minimum acceptance suite. **Test framework/commands are PROVISIONAL** (Phase 4B.3 doc indicated `python -m unittest discover`); confirm in §17. Each test is deterministic via the fixture.

| ID | Test | Expectation |
|---|---|---|
| T1 | Successful single-item execution | `item.alpha` (positive) runs STEP1–6, completes, no repeat |
| T2 | Repeat on negative confirmation | `item.beta` (negative) triggers exactly one repeat |
| T3 | No repeat on positive confirmation | `item.alpha` never repeats |
| T4 | Repeat cap enforced | second negative after the allowed repeat → item completed (unresolved), no 2nd repeat |
| T5 | Deterministic event order | E1–E8 sequence identical across runs |
| T6 | Persistence round trip | persist → load → identical event stream |
| T7 | Replay equality | event replay reproduces identical sequence + payloads (incl. pins) |
| T8 | Summary derivation | summary computed from events matches expected outcomes/repeats |
| T9 | Asset-version pin retained | pins on E2/E5 persisted and identical after replay |
| T10 | No provider access | no network/provider call during plan/execute/replay (assert zero provider calls) |
| T11 | No EEG influence | no EEG event/field present; EEG code path absent |
| T12 | CLI success | `protocol run` exits 0, stdout-only, valid single JSON in `--json` |
| T13 | CLI invalid input | bad args → exit 2; unknown session → exit 3; empty stdout on failure |

**Regression guard:** existing Phase 4B.3 CLI/store tests and Phase 4B.2 replay tests must still pass (additive-only change).

---

## 13. Implementation sequence

Ordered so nothing is built on an unverified assumption:

0. **Complete §17 Disk handoff checklist** — reconcile every PROVISIONAL_DESIGN_MAPPING against the real repo. **Blocking.**
1. Add the **fixture** (`minimal`): items, deterministic self-confirmation, pinned fixture assets. (T-data)
2. Add the **minimal protocol definition** + step builder for Immediate Recall (§5.2), using confirmed contract names.
3. Add the **planning** step producing `ExecutionPlan` (selected protocol/items/pins/bounds/order/session id).
4. Wire **execution** to emit typed instructions and events E1–E8 through the existing runtime + event store (confirmed APIs).
5. Implement the **one bounded adaptation rule** (cap 1; behavior authoritative; latency proxy).
6. Confirm **persistence + event replay** round-trip and **replay equality**; add **summary derivation** from events.
7. Add the **CLI** subcommand(s), matching the exit-code/stdout/JSON contract.
8. Add the **test suite** T1–T13; ensure existing tests still pass.
9. Update slice docs only (no `PROJECT_STATE.md`/`NEXT_TASK.md`).

---

## 14. Risks

| ID | Risk | Severity | Mitigation |
|---|---|---|---|
| R1 | PROVISIONAL contract names wrong (repo unavailable) | High | §3 gate + §17 checklist; fallbacks per mapping; no source claims |
| R2 | Accidentally introduces a second DSL | Medium | Typed instructions only; no textual grammar; review gate |
| R3 | New/extended events break existing replay/CLI consumers | Medium | Additive-only (C2); regression tests; deterministic ordering |
| R4 | Asset-version pin representation differs from Audio Pipeline registry | Medium | Fixture manifest version field; reconcile in §17 item 6 |
| R5 | CLI syntax collides with existing verbs / exit-code contract | Medium | Reconcile in §17 item 4; match Phase 4B.3 contract exactly |
| R6 | Summary derivation depends on unstable `RuntimeState.as_dict()` ordering | Medium | Derive from events with stable ordering (Acceptance Record C3) |
| R7 | Scope creep (EEG/ASR/spacing/domain adapter) | Medium | §15 hard exclusions; single adaptation rule; one protocol |
| R8 | `ScheduleDecision` misused to imply spacing | Low | Documented N/A in slice; no scheduler |

---

## 15. Exclusions (intentionally deferred)

- Full protocol taxonomy (only Immediate Recall here).
- Hebrew Lab adapter; Piano Lab adapter; any real domain adapter.
- SpeechGen / any provider; `mpe_audio` implementation; live audio synthesis.
- ASR; EEG (no input, no events, no fields).
- Adaptive spacing / spaced-repetition scheduler; `ScheduleDecision` usage.
- Stochastic policies (adaptation is deterministic, cap 1).
- Multi-protocol composition; session orchestration beyond one protocol.
- Protocol replay / counterfactual / EEG-ablation replay (only **event replay** now).
- Durable learning-state / mastery store; curriculum.
- Any change to existing runtime contracts, `PROJECT_STATE.md`, `NEXT_TASK.md`.

---

## 16. Acceptance criteria

The slice is acceptable when **all** hold:

1. Exactly one protocol (Immediate Recall) executes end-to-end via the existing runtime; **no second DSL** introduced.
2. Fixture is domain-neutral (`item.alpha`, `item.beta`); no Hebrew/linguistic concepts.
3. No provider/SpeechGen/live-TTS/ASR/EEG/scheduler code path exists or is exercised (T10, T11).
4. The one bounded adaptation rule works with cap = 1; behavior authoritative; latency proxy only (T1–T4).
5. Events E1–E8 emitted; every event correctly classified and **additive**; asset-version pins carried (T5, T9).
6. Persistence round-trip + **event replay equality**; Phase 4B.2 guarantees not weakened (T6, T7).
7. `ProtocolSummary` derived from events, reproducible (T8).
8. CLI success + invalid-input behavior match the existing exit-code/stdout/JSON contract (T12, T13).
9. Existing Phase 4B.2/4B.3 tests still pass (regression).
10. **Every PROVISIONAL_DESIGN_MAPPING was reconciled** via §17 before implementation; no unverified symbol shipped as fact.

---

## 17. Disk handoff checklist

Complete **all** items against the **local repository** before writing code. Each item converts PROVISIONAL_DESIGN_MAPPINGs into verified facts (or applies a fallback).

1. **Repository root verification** — locate the MPE repo; confirm `packages/mpe/...` layout, test dir, and that `PROJECT_STATE.md`/`NEXT_TASK.md` exist (and will not be modified). Record the actual root path.
2. **Actual contract-symbol mapping** — confirm real names/fields/signatures for `Instruction`, `StimulusRequest`, `RenderedStimulus`, `Observation`, `AdaptationDecision`, `ScheduleDecision`, and any protocol/plan/summary types. Replace §6 candidates or apply fallbacks. Mark any as NEW only if genuinely absent.
3. **Event reuse/new-event decision** — for each of E1–E8, confirm whether an existing event is reused, extended additively, or must be new. Lock final event names + payloads; ensure additivity (no existing-semantics change).
4. **CLI reconciliation** — confirm the real command grammar, subcommand vs flat-verb convention, option placement, exit-code contract (0–6), and JSON single-document rule. Finalize `protocol run`/`protocol show` (or fallbacks) accordingly.
5. **Persistence/replay verification** — confirm the event-store append/replay APIs, deterministic-ordering guarantee, and backends (SQLite + in-memory). Confirm event replay is sufficient (protocol replay deferred).
6. **Asset-pin representation** — confirm how asset versions are represented/pinned (Audio Pipeline registry vs fixture manifest) and how the pin is carried in stimulus events + preserved through replay.
7. **Test-command verification** — confirm the test runner/command (e.g., `python -m unittest discover -s packages/mpe/tests -p 'test_*.py'` or actual), the fixtures location/size policy, and that T1–T13 fit existing conventions; confirm lint/type commands to run.

Only after items 1–7 are complete and recorded may implementation begin.

---

## 18. Stop conditions

Stop and escalate (do not proceed) if any occur:

- The repository is unavailable or its structure contradicts §4 assumptions (A1–A3 false).
- Reconciling §6 would require **breaking an existing contract** (non-additive change) — re-plan instead.
- Implementing the slice would require introducing a **second DSL**, a provider call, EEG/ASR, or a scheduler — out of scope.
- Phase 4B.2 replay determinism cannot be preserved with the proposed events — REVISE.
- Any attempt to modify `PROJECT_STATE.md` or `NEXT_TASK.md` — not permitted here.

This planning task itself **stops after producing this document** (no implementation).

---

## 19. Final recommendation

The vertical slice is **well-scoped, minimal, additive, and implementation-ready in structure**: one protocol (Immediate Recall), a domain-neutral deterministic fixture, one bounded adaptation rule (cap 1), reuse of the existing runtime/event/persistence/replay/CLI surfaces, event-only replay, and an events-derived summary — with no provider, EEG, ASR, scheduler, or second DSL. However, **the MPE repository was unavailable during planning**, so **every contract/symbol/event/CLI/path/test-command reference is a PROVISIONAL_DESIGN_MAPPING** and **no source-level verification is claimed**. Implementation is therefore explicitly **conditional on completing the §17 local repository reconciliation** (and honoring the §16 acceptance criteria and §18 stop conditions).

**Recommendation:**

```
APPROVE_PHASE_4C1_IMPLEMENTATION_WITH_CONDITIONS
```

Conditions (summary): (1) complete the §17 Disk handoff checklist and reconcile all PROVISIONAL_DESIGN_MAPPINGs before coding; (2) keep every event/persistence/CLI change strictly additive and preserve Phase 4B.2 replay determinism; (3) introduce no second DSL, provider, EEG, ASR, or scheduler; (4) derive the summary from events with stable ordering; (5) make no changes to existing runtime contracts, `PROJECT_STATE.md`, or `NEXT_TASK.md`.
