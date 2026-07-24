# MPE Open Decisions v1.1

## Audit basis

This document records the open questions from `OPEN_QUESTIONS_AND_DECISIONS.md` and the acknowledged limitations from `METHODOLOGY_AND_LIMITATIONS.md` §Limitations that require evidence before closure. Closed decisions are cross-referenced to the architecture documents that implement them.

## Open decisions

### 1. Protocol authoring format

- **Options:**
  - A. Versioned JSON/YAML fixtures only.
  - B. Typed model with JSON/YAML serialization.
  - C. Textual DSL from the start.
- **Recommendation:** B with A as the concrete format.
- **Evidence needed:** None for Phase 4A; model stability after 4A.
- **Deadline:** End of Phase 4A.
- **Status:** Provisional; see `MPE_DSL_DECISION_RECORD.md`.

### 2. Microphone failure fallback

- **Options:**
  - A. Immediate button fallback.
  - B. Pause and retry.
  - C. Abort session after N failures.
- **Recommendation:** A for Phase 4C.
- **Evidence needed:** Failure-rate observations.
- **Deadline:** Before Phase 4C.

### 3. Voice response path

- **Options:**
  - A. ASR transcript → `HebrewDomainNormalizer` → `HebrewEvaluator`.
  - B. Record audio and manually review later; use button in session.
  - C. Use phoneme-based pronunciation scoring.
- **Recommendation:** A for button-fallback sessions with stored audio for audit.
- **Evidence needed:** ASR accuracy on Hebrew verb forms.
- **Deadline:** Before Phase 4C.

### 4. Delayed recall architecture

- **Options:**
  - A. Built into scheduler as review block.
  - B. Separate delayed-assessment `ProtocolVersion`.
- **Recommendation:** B.
- **Evidence needed:** Retention study design.
- **Deadline:** Before Phase 6.

### 5. Hebrew `error_category` values

- **Options:**
  - A. Full set (`tense`, `person`, `gender`, `number`, `binyan`, `spelling`, `out_of_scope`, `engine_error`).
  - B. Minimal set (`correct`, `incorrect`, `abstained`).
- **Recommendation:** A if Hebrew engine can supply; B as fallback.
- **Evidence needed:** Hebrew engine diagnostic capability.
- **Deadline:** Before Phase 4C.

### 6. `correctness_credit` for acceptable variants

- **Options:**
  - A. Full credit (1.0).
  - B. Partial credit (0.5–0.8).
  - C. Separate metric.
- **Recommendation:** A for Phase 4C; record `accepted_variant_id` separately.
- **Evidence needed:** Pedagogical impact study.
- **Deadline:** Before Phase 6.

### 7. Canonical TTS voice for Phase 4C

- **Options:**
  - A. `shaul` Piper.
  - B. Azure `he-IL-AvriNeural`.
  - C. Support both.
- **Recommendation:** C with a single default per `ProtocolVersion`.
- **Evidence needed:** Voice quality and phoneme coverage tests.
- **Deadline:** Before Phase 4C.

### 8. Streaming vs pre-rendered TTS

- **Options:**
  - A. Pre-rendered only in Phase 4.
  - B. Streaming optional.
- **Recommendation:** A for Phase 4; streaming later.
- **Evidence needed:** Latency measurements.
- **Deadline:** Before Phase 4B.

### 9. StateEstimate history inputs

- **Options:**
  - A. Current window only.
  - B. Recent session history.
  - C. Full learner history.
- **Recommendation:** A for Phase 5B; B for Phase 5C after validation.
- **Evidence needed:** Offline model validation.
- **Deadline:** Before Phase 5C.

## Closed decisions

- Logical/executable identity separation: closed; see `MPE_OBJECT_MODEL_V1_1.md`.
- Covert instruction semantics: closed; see `COGNITIVE_PROTOCOL_ONTOLOGY.md`.
- Response processing layers: closed; see `MPE_OBJECT_MODEL_V1_1.md`.
- Provider decomposition: closed; see `MPE_PROVIDER_BOUNDARIES.md`.
- DSL strategy: closed; see `MPE_DSL_DECISION_RECORD.md`.
- Phase 4 split: closed; see `MPE_PHASE_4_IMPLEMENTATION_PLAN.md`.
- EEG `exploratory_only`: closed; see `MPE_PROVIDER_BOUNDARIES.md` and `MPE_ADAPTATION_CONTRACT.md`.

## Traceability

This document mirrors `OPEN_QUESTIONS_AND_DECISIONS.md` and `METHODOLOGY_AND_LIMITATIONS.md` §Limitations. Closed decisions are cross-referenced to the architecture documents that implement them. Open questions are deferred to Phase 4B–5C evidence milestones and are recorded as known-unknowns, not as design gaps.
