# ADR-0002 — Analytical policy versioning and the retrospective analysis layer

**Status:** **Proposed** — awaiting approval. The approval token block is §7.
**Date:** 2026-07-27
**Programme:** Scientific Reproducibility Milestone 2 (SR-M2). A parallel programme; deliberately not mapped onto the MPE phase numbering.
**Supersedes:** nothing. **Superseded by:** nothing.
**Related:** `docs/architecture/adr/ADR-0001-event-integrity-and-provenance.md`, `docs/scientific-reproducibility/milestone-2-scope.md`

The SR-M2 scope was merged with its six decisions recorded as recommendations rather than answered individually. This ADR adopts those recommendations as its decisions; each one is marked **[scope Q<n>]** so that rejecting a recommendation means revising exactly one section.

---

## 1. Context

SR-M1 established that the event history can be checked for the integrity properties defined in ADR-0001 §2.10, carries a self-asserted UTC wall-clock time, and records what software produced it. Three gaps remain, all identified in the Phase 1 audit and all now blocking:

1. **Analytical parameters are unversioned code constants (audit R5).** `repeat_cap` and `latency_bound` are call arguments and literals in protocol construction. Two runs analysed under different rules are indistinguishable after the fact except by reading the source at that revision — which is exactly the situation event-sourcing exists to prevent.
2. **Provenance reserves policy fields that nothing produces.** `scoring_policy_version`, `rt_policy_version` and `signal_processing_policy_version` are recorded as explicit `null` in every `session_provenance_recorded` event today. SR-M1 reserved them deliberately so SR-M2 could fill them without an envelope change.
3. **There is no retrospective layer (audit §2.3).** The vocabulary separates raw → captured → interpreted → normalized → evaluated, but an exclusion, a re-scoring, or an analysis has nowhere to live. Recording one today would mean editing trial history, which the architecture forbids and the hash chain now detects.

A fourth constraint is a matter of honesty rather than mechanism: per-item latency is currently documented as an *adaptation proxy*. Nothing in the system may be presented as a reaction time until a policy defines what one is.

---

## 2. Decision

### 2.1 A policy is an immutable, content-addressed object **[scope Q3]**

```
Policy = {policy_id, policy_version, kind, parameters}
kind ∈ {scoring, rt, exclusion, sdt, power}
```

Policies are declared in code and content-addressed: `policy_version` is derived from the canonical encoding of `parameters` using the encoder ADR-0001 §2.3.1 already defines. A policy is never mutated in place — changing a parameter yields a new version, and the old version remains resolvable because sessions reference it.

A code registry is chosen over a data file or a store table because a policy must be *executable*, and a parameter set that no code can apply is not a policy. Data-file and table variants were rejected: both allow a policy to exist that no revision of the software can run, and both reintroduce mutable analytical state outside the event history.

The registry is exported with the session. A reviewer holding only the JSONL must be able to say which rule produced a number, without access to this repository.

### 2.2 `repeat_cap` and `latency_bound` become policy parameters **[scope Q5]**

Their current values are registered as version 1 of the corresponding scoring and RT policies, so existing sessions remain interpretable under a named, versioned rule rather than under an implicit one. Protocol call signatures may change to accept a policy reference instead of loose numbers; this is a deliberate, reviewable break, not an incidental one.

### 2.3 Policy versions are bound to the session at sequence 2

`Runtime.record_provenance` populates `scoring_policy_version` and `rt_policy_version` from the registry instead of `null`. No new binding mechanism is invented: ADR-0001 already forces provenance to occupy sequence 2 and refuses every later event until it exists, so a session cannot run without declaring the policies it ran under.

`signal_processing_policy_version` stays `null` in SR-M2. It belongs to SR-M3, and inventing a value for it now would be exactly the fabricated-default failure that ADR-0001 §2.8 forbids.

#### 2.3.1 A session may reference a policy this installation does not have

An imported foreign session must remain readable and analysable. The resolution result is discriminated, in the same shape as `ProvenanceReference`:

```
policy_status: "resolved" | "unresolved_foreign"
```

`unresolved_foreign` permits reading and reporting but refuses to compute any quantity that requires executing the policy. Silently substituting a local policy of the same `policy_id` is rejected: it would report a number under a rule that did not produce it.

### 2.4 Retrospective analyses are a new event family in the existing store **[scope Q1]**

This is the consequential decision. Exclusions, re-scorings and analyses are recorded as append-only events in the *same* `EventStore`, typed as retrospective and emitted **outside** the session lifecycle, referencing the events they concern through the existing `provenance` mechanism.

A separate derived-analysis store was the main alternative and is rejected on the strength of roadmap §2.1: two stores means two histories, and the moment they disagree nothing decides which is authoritative — the same argument ADR-0001 §2.1 used against a parallel audit log. Keeping one store also means retrospective records inherit the hash chain, the verified-by-default reads, and the interchange path for free, rather than needing a second integrity mechanism.

The cost is accepted explicitly: the session stream is no longer purely observational. It is mitigated by three rules.

1. A retrospective event never modifies, supersedes, or invalidates a trial event. A trial excluded from an analysis remains in the stream unchanged; the exclusion is a separate statement about it.
2. Retrospective events are emitted after the session reaches a terminal state and are refused inside an active session lifecycle. The runtime state machine is untouched.
3. Every projection distinguishes the two families. A behavioral summary that silently mixed observations with retrospective judgements would be the exact failure this layer exists to prevent.

Each retrospective event carries the policy version under which it was produced, a rationale, and the analyst identity. An exclusion without a recorded reason is not constructible.

### 2.5 Reaction time is defined by policy or is not produced

An RT policy states, per protocol: the anchor event, the terminating event, the clock used, the validity window, and the treatment of repeated attempts. RT is produced only through a policy, and every value carries the version that produced it.

Where the two-clock model cannot support a claim — display latency, input latency, anything requiring device-supplied time — the limitation is recorded rather than absorbed into the number. Source-device time remains SR-M3. Until an RT policy exists for a protocol, that protocol reports latency as the adaptation proxy it already is.

### 2.6 SDT is computed on behavioral data only

Hit / miss / false alarm / correct rejection derived from the Recognition event stream, with d′ and criterion. The correction for extreme rates is a **policy parameter**, not a constant: log-linear is the default, and the choice is recorded with the result. Where the design does not support the computation, the analysis refuses rather than returning a degenerate value.

No physiological input participates. The roadmap is explicit that the EEG subsystem must not become the authoritative controller of the protocol, and letting it enter behavioral SDT in SR-M2 would breach that before SR-M3 has even defined acquisition.

### 2.7 Event schema moves to 1.3 **[scope Q4]**

The retrospective family is new event types, so the vocabulary changes and the schema version follows. The precedent set by SR-M1 is applied unchanged: 1.2 streams remain readable exactly as 1.1 streams are today, no stream mixes versions, and no historical event is ever rewritten or retro-typed.

### 2.8 Nothing here touches integrity or its threat model

ADR-0001 §2.10 remains binding and unamended. SR-M2 adds no anchor, and tail truncation remains `undetermined`. Retrospective events are chained like any other event, which means the chain says exactly as much about them as it says about trials: something about the retained stream, nothing about its removed tail.

---

## 3. Consequences

**Positive.** Every derived number becomes traceable to a named, versioned, executable rule. Exclusions become first-class, recorded evidence rather than undocumented analyst behaviour. The reproducibility path SR-M1 built extends over the analytical layer at no additional structural cost.

**Negative, and accepted.** The event store now holds two kinds of statement, and every consumer must respect the distinction. Protocol signatures change. Schema 1.3 adds a third readable-but-closed generation of historical streams. The policy registry is code, so a policy cannot be added without a release — deliberate, since a policy that cannot be executed is not a policy.

**Rejected alternatives.** A separate derived store (§2.4); a data-file or table-backed registry (§2.1); silent local substitution of unresolved foreign policies (§2.3.1); computing RT from the existing latency without a policy; involving physiological data in SDT (§2.6); amending ADR-0001 instead of writing this ADR **[scope Q2]** — integrity and analysis are different concerns and their approval histories should not be entangled.

---

## 4. Delivery order **[scope Q6]**

WP-1 registry → WP-2 session binding → WP-5 retrospective layer → WP-3 RT → WP-4 SDT → WP-6 power. The registry and the retrospective layer are structural; the three analyses are consumers of them. WP-6 may be deferred without blocking anything.

Each work package is committed, tested, and published for review before the next begins, as in SR-M1.

---

## 5. Verification conditions

An implementation satisfies this ADR only if all of the following hold.

1. A policy's `policy_version` is derived from its parameters; changing a parameter changes the version, and a test asserts it.
2. A session's `scoring_policy_version` and `rt_policy_version` are non-null and resolve to registered policies; `signal_processing_policy_version` remains null.
3. An imported session referencing an unknown policy is readable, reports `unresolved_foreign`, and refuses to compute quantities requiring that policy.
4. A retrospective event is refused inside an active session lifecycle and accepted after a terminal state.
5. No retrospective event modifies, supersedes, or invalidates any trial event; a test asserts the trial stream is byte-identical before and after an exclusion is recorded.
6. An exclusion without a recorded rationale and policy version is not constructible.
7. A behavioral summary never silently mixes observational and retrospective records; the distinction is visible in its output.
8. RT is produced only through an RT policy, and every value carries the producing version.
9. SDT refuses where the design does not support it, and the extreme-rate correction is recorded with the result.
10. Schema 1.2 streams remain readable and analysable after the move to 1.3, with no stream mixing versions.
11. Export, import, and rebuild-from-empty round-trip a stream containing retrospective events with byte-identical canonical records.
12. No claim in the codebase or documentation asserts tail-truncation detection, tamper-proofness, or external attestation.

---

## 6. What this ADR does not authorize

EEG, physiological signals, device profiles, preprocessing, feature provenance (SR-M3); BIDS, validators, publication bundles (SR-M4); snapshots in any evidential role; any truncation anchor; any medical-device, clinical, or regulatory positioning; audio pipeline work.

---

## 7. Approval

```
APPROVE_ADR_0002
APPROVE_ADR_0002_WITH_CONDITIONS
REVISE
BLOCK
```

Approval authorizes the SR-M2 implementation plan and, on the order in §4, implementation. It does not authorize any item in §6.
