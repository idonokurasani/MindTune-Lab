# Open Questions and Decisions v1

## Open questions

### 1. What is the authoring format for protocols?

- **Options:**
  - A. Versioned JSON/YAML fixtures only.
  - B. Typed model with JSON serialization now, optional textual DSL later.
  - C. Textual DSL from the start.
- **Recommendation:** B with A as the concrete serialization.
- **Evidence needed:** None for Phase 4A; the typed model is a design decision.
- **Deadline:** Before Phase 4A ends.
- **Status:** Decided in `MPE_DSL_DECISION_RECORD.md`.

### 2. How should the runtime handle microphone failures?

- **Options:**
  - A. Fall back to button input immediately.
  - B. Pause and retry microphone.
  - C. Abort session after N failures.
- **Recommendation:** A for Phase 4C with a logged `safety_rule_triggered` event.
- **Evidence needed:** Usability data on failure rates.
- **Deadline:** Before Phase 4C begins.

### 3. Should delayed recall be built into the protocol scheduler or as a separate program?

- **Options:**
  - A. Built into scheduler as a special review block.
  - B. Separate delayed-assessment program.
- **Recommendation:** B initially; delayed recall is a different purpose (`assessment` vs `retrieval`).
- **Evidence needed:** Retention study design.
- **Deadline:** Before Phase 6.

### 4. What is the exact set of Hebrew `error_category` values?

- **Options:**
  - A. Reuse `hebrew/phase3` status labels and add `tense`, `person`, `gender`, `number`, `binyan`, `spelling`, `out_of_scope`, `engine_error`.
  - B. Keep only `correct`/`incorrect`/`partial`/`abstained`.
- **Recommendation:** A if the Hebrew engine can supply them; B as fallback.
- **Evidence needed:** Hebrew engine diagnostic capability.
- **Deadline:** Before Phase 4C begins.

### 5. Should `StateEstimate` inputs include historical performance or only current observations?

- **Options:**
  - A. Only current observations within a time window.
  - B. Current observations plus recent session history.
  - C. Full learner history.
- **Recommendation:** A for Phase 5B; B for Phase 5C after validation.
- **Evidence needed:** Model validation showing added value of history.
- **Deadline:** Before Phase 5C.

### 6. How is `acceptable_variant` scored for retention metrics?

- **Options:**
  - A. Full correctness credit (`correctness_credit = 1.0`).
  - B. Partial credit (`0.5`–`0.8`).
  - C. Separate metric, not collapsed into accuracy.
- **Recommendation:** A for Phase 4C but record `accepted_variant_id` separately.
- **Evidence needed:** Pedagogical study of variant acceptance impact.
- **Deadline:** Before Phase 6.

### 7. What voice configuration is canonical for Hebrew TTS in Phase 4C?

- **Options:**
  - A. `shaul` Piper voice.
  - B. Azure `he-IL-AvriNeural`.
  - C. Support both with per-protocol config.
- **Recommendation:** C with a single default per `ProtocolVersion`.
- **Evidence needed:** Voice quality and phoneme coverage tests.
- **Deadline:** Before Phase 4C begins.

### 8. Should the runtime support live streaming of TTS or pre-rendered audio?

- **Options:**
  - A. Pre-rendered only in Phase 4B/4C.
  - B. Streaming optional.
- **Recommendation:** A for Phase 4; streaming as a Phase 5 optimization.
- **Evidence needed:** Latency measurements per renderer.
- **Deadline:** Before Phase 4B begins.

## Decisions already made

- Logical vs executable identity: see `MPE_OBJECT_MODEL_V1_1.md`.
- Covert instruction semantics: see `COGNITIVE_PROTOCOL_ONTOLOGY.md`.
- Response processing layers: see `COGNITIVE_PROTOCOL_ONTOLOGY.md`.
- Provider boundaries: see `MPE_PROVIDER_BOUNDARIES.md`.
- DSL strategy: see `MPE_DSL_DECISION_RECORD.md`.
- Phase 4 split: see `MPE_PHASE_4_IMPLEMENTATION_PLAN.md`.
