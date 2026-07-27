# Scientific Reproducibility Milestone 2 (SR-M2) — Scope proposal

**Status:** Proposed — awaiting approval
**Predecessor:** SR-M1 (delivered: event integrity, wall-clock recording, session provenance, supported interchange)
**Successors:** SR-M3 (device profiles, EEG acquisition, preprocessing registry, feature provenance), SR-M4 (BIDS export, publication bundle)

This is a scope proposal, not an implementation plan and not an ADR. It defines what SR-M2 is, what it is not, and which decisions must be taken before a plan can be written. No production code is proposed here.

---

## 1. The one sentence

SR-M1 made *what happened* trustworthy. SR-M2 must make *what we conclude from it* trustworthy: every analytical choice becomes a versioned, recorded object, and every derived number states which policy produced it.

---

## 2. Where SR-M1 left the system

Delivered and available to build on:

| Capability | Where |
|---|---|
| Per-stream SHA-256 chain, verified-by-default reads | `mpe/integrity.py`, `persistence/store.py` |
| Self-asserted UTC wall time per event | `Runtime.emit`, `wallclock_at` |
| `session_provenance_recorded` at sequence 2, causally binding | `mpe/runtime.py`, `mpe/provenance.py` |
| Discriminated provenance on every derived result | `ProvenanceReference` |
| Deployment-safe software revision with recorded source | `resolve_software_revision()` |
| Supported export/import, rebuild-from-empty, determinism properties | `persistence/interchange.py` |

Deliberately still open, and now blocking SR-M2 (audit §4, R5):

- **Analytical parameters are unversioned code constants.** `repeat_cap` and `latency_bound` are arguments and literals in protocol construction. Two runs with different values are indistinguishable after the fact except by reading the code at that revision.
- **The provenance record has the fields but no producers.** `scoring_policy_version`, `rt_policy_version` and `signal_processing_policy_version` are recorded as explicit `null` today, precisely so that SR-M2 can fill them without a schema change.
- **There is no retrospective layer.** The event vocabulary separates raw → captured → interpreted → normalized → evaluated, but there is no place to record an analysis, an exclusion, or a re-scoring *without touching the trial history* (audit §4, §2.3).
- **Latency is documented as an adaptation proxy, not a behavioral measure.** Nothing in the system today may be presented as a reaction time.

---

## 3. What SR-M2 must deliver

### WP-1 — Policy registry and policy identity

A policy is an immutable, addressable object: `{policy_id, policy_version, kind, parameters}`, where `kind` ∈ {scoring, rt, exclusion, signal_processing}. Registered policies are content-addressed and never mutated in place; changing a parameter produces a new version. `repeat_cap` and `latency_bound` become policy parameters instead of call arguments.

The registry must be readable from an exported session alone. A reviewer with the JSONL and nothing else must be able to say which rule produced a number.

### WP-2 — Policy versions bound to sessions

`Runtime.record_provenance` starts populating `scoring_policy_version` and `rt_policy_version` from the registry rather than recording `null`. The binding is the one SR-M1 already enforces: the provenance event is sequence 2, so a session cannot exist without declaring the policies under which it ran.

Open design point: whether a session may reference a policy the local registry does not contain (an imported foreign session). The proposal is yes, readable and analysable, but flagged — same shape as `unavailable_legacy`.

### WP-3 — Reaction time as a derived, policy-governed quantity

Today's per-item latency is a difference between two protocol-clock values and is explicitly not a behavioral measure. SR-M2 must define an RT policy that states, per protocol, the anchor event, the terminating event, the clock used, the validity window, and the treatment of repeats — and must produce RT only through that policy, with the policy version attached to every value.

Where the two-clock model is insufficient (display latency, input latency), SR-M2 must record the limitation rather than paper over it. Device-supplied time remains SR-M3.

### WP-4 — Signal detection theory on behavioral data only

Hit / miss / false alarm / correct rejection derived from the Recognition event stream, with d′ and criterion, an explicit and versioned correction for extreme rates (log-linear or similar — the choice is a policy, not a constant), and a refusal to compute where the design does not support it. No EEG involvement whatsoever: SR-M3 owns physiology, and the roadmap is explicit that the EEG subsystem must not become authoritative.

### WP-5 — The retrospective layer

The gap the audit called out in §2.3. Exclusions, re-scoring and analyses are recorded as their own append-only records referencing the trials they concern, never as edits to the trial history. A trial excluded from an analysis remains in the event stream unchanged; the exclusion is a separate, provenanced statement with its own policy version and rationale.

Open design point, and the largest one in SR-M2: whether these records live in the same `EventStore` as a new event family, or in a separate derived-analysis store that references event ids. The first keeps one authoritative history and one integrity chain; the second keeps the session stream purely observational. My recommendation is the first, on the strength of roadmap §2.1, with the analysis events clearly typed as retrospective and emitted outside the session lifecycle.

### WP-6 — Power and sensitivity

Design-time power analysis and post-hoc sensitivity, as a versioned policy with recorded inputs, so that a reported n is traceable to the assumptions that produced it. This is the smallest work package and can be deferred without blocking WP-1 to WP-5.

---

## 4. Explicitly out of scope

- EEG, physiological signals, device capability profiles, preprocessing, feature provenance — all SR-M3.
- BIDS export, validator integration, publication bundles, Methods appendices — all SR-M4.
- Snapshots as a second source of truth — permanently excluded.
- Any anchor mechanism for tail truncation. ADR-0001 §2.10 remains binding and unchanged: truncation stays `undetermined`.
- Any medical-device, clinical or regulatory positioning.
- Audio pipeline work, which remains a separate product workstream.

---

## 5. Decisions needed before a plan can be written

| # | Question | Recommendation |
|---|---|---|
| 1 | Do retrospective analyses live in the `EventStore` as a new event family, or in a separate derived store? | Same store, new retrospective event family |
| 2 | Does SR-M2 require a new ADR, or an amendment to ADR-0001? | New ADR-0002, since it introduces the analysis layer rather than changing integrity |
| 3 | Is the policy registry a code registry, a data file in the repo, or rows in the store? | Code-declared and content-addressed, exported with the session |
| 4 | Does the event schema need to move to 1.3? | Only if the analysis records are events; if so, yes, and 1.2 streams stay readable exactly as 1.1 streams are today |
| 5 | Is `repeat_cap` / `latency_bound` migration allowed to change existing protocol call signatures? | Yes, with the current values registered as version 1 of the corresponding policies so existing sessions remain interpretable |
| 6 | Priority order among WP-1 to WP-6 | WP-1 → WP-2 → WP-5 → WP-3 → WP-4 → WP-6; the registry and the retrospective layer are the structural ones |

---

## 6. Approval

Reply with one of:

```
APPROVE_SRM2_SCOPE
APPROVE_SRM2_SCOPE_WITH_CONDITIONS
REVISE
BLOCK
```

An approved scope authorizes only the writing of ADR-0002 and the SR-M2 implementation plan, not implementation.
