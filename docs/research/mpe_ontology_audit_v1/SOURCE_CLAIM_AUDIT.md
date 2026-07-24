# Source Claim Audit v1

## Scope

This document audits claims from the following sources:

- `docs/MINDTUNE_PROTOCOL_ENGINE_ARCHITECTURE_v1.0.md`
- `data/hebrew/phase3/PHASE_3_FINAL_REPORT.md`
- `data/DOCKER_HEBREW_REVIEW_AUDIT_2026-07-03.md`
- `data/mantra/UNCERTAINTIES.md`
- `data/hebrew/UNRESOLVED_ISSUES.md`

Evidence grades:

- `A` — supported by completed project artifact or explicit license/test result.
- `B` — supported by literature or expert review, but not yet validated in this system.
- `C` — plausible hypothesis, requires empirical validation.
- `D` — unsupported or misleading as stated.
- `N/A` — not a factual claim.

## Claim audit

### From MPE v1.0

| # | Claim | Source section | Grade | Status in v1.1 |
|---|---|---|---|---|
| 1 | "MindTune Lab is becoming the first platform dedicated to Adaptive Cognitive Protocols." | v1.0 Vision | D | Quarantined as product-positioning hypothesis. |
| 2 | "The most effective learning state may happen with eyes closed, minimal visual stimulation, auditory guidance, internal speech, mental imagery, controlled cognitive load." | v1.0 Vision | C | Retained as experimental hypothesis, not architecture axiom. |
| 3 | "A protocol is a structured cognitive sequence with objective, cognitive target, linguistic target, timing, adaptation rules, progression rules, evaluation metrics." | v1.0 2.2 | B | Retained, with stricter trial-level observability. |
| 4 | "Perceive → Predict → Resolve → Reinforce is the learning loop." | v1.0 4.1 | D | Reclassified as Language Prediction-Retrieval Loop; generic trial structure added. |
| 5 | `arousal`, `attention`, `cognitive_load`, `fatigue`, `engagement`, `fluency` can be estimated from listed EEG/behavioral features. | v1.0 4.2 | D | Replaced by `LatentEstimate` with operational definitions and `exploratory_only` status. |
| 6 | Alpha/theta ratio correlates with arousal; frontal asymmetry with attention; theta/beta with cognitive load. | v1.0 11.4 | D | Removed from core; moved to experimental `StateInferenceModel`. |
| 7 | `expect(mental_hebrew)` is a valid primitive. | v1.0 6.1, 6.3 | D | Replaced by `INSTRUCT_COVERT_RETRIEVAL` + observable probe. |
| 8 | `wait_for_state(target, timeout)` is a valid primitive. | v1.0 6.1 | D | Removed. |
| 9 | A single `Provider` can render, observe, and evaluate. | v1.0 5.4, 14.1 | D | Decomposed into six narrow interfaces. |
| 10 | `increase_difficulty()` / `decrease_difficulty()` are valid primitives. | v1.0 6.1 | D | Replaced by typed difficulty dimensions and `AdaptationDecision`. |
| 11 | `pause_duration 0.5–8.0s`, `speech_rate 0.7x–1.3x`, `new_item_rate 0–50%` are safe/optimal ranges. | v1.0 8.3 | D | Reclassified as provisional configurable bounds with evidence grade. |
| 12 | `time_in_target_state` is a session-level KPI. | v1.0 12.1 | D | Removed from Phase 4/5A KPIs; experimental diagnostic only. |
| 13 | Phase 4 can implement core MPE + Hebrew + audio + DSL parser + runtime in one phase. | v1.0 19 | D | Split into 4A, 4B, 4C. |

### From Phase 3 Final Report

| # | Claim | Source section | Grade | Status in v1.1 |
|---|---|---|---|---|
| 14 | The Phase 3 Hebrew pipeline is internally consistent for a 100-verb subset. | Phase 3 Key metrics / Status summary | A | Accepted as domain authority within its scope. |
| 15 | `verified_consensus` labels reflect self-consistency of Eran Tomer and Verb Inflector, not independent corroboration. | Phase 3 Honest limitations | A | Retained as limitation; MPE uses `status` and `scope` fields. |
| 16 | Pronunciation validation depends on Phonikud and is advisory. | Phase 3 Honest limitations | A | MPE treats `pronunciation_metadata` as advisory. |
| 17 | Phase 3 coverage is limited to verbs. | Phase 3 Honest limitations | A | MPE restricts Phase 4C to 100-verb subset. |

### From Docker Hebrew Review Audit

| # | Claim | Source section | Grade | Status in v1.1 |
|---|---|---|---|---|
| 18 | The Docker-processed `quizlet_hebrew_audit_reviewed.csv` must not replace `quizlet_hebrew_seed.json` as the active app source. | Docker audit Recommendation | A | No impact on MPE; MPE does not consume flashcard database directly in Phase 4. |
| 19 | Automatic `front` modification is dangerous for Hebrew didactic data. | Docker audit Violations | A | Reinforces that MPE must not normalize or modify Hebrew content; Hebrew engine is authority. |

### From Mantra Uncertainties

| # | Claim | Source section | Grade | Status in v1.1 |
|---|---|---|---|---|
| 20 | Infinitive spelling `לִכְתֹּב` vs `לִכְתּוֹב` is an open linguistic decision. | Mantra UNCERTAINTIES #1 | A | MPE must expose both as accepted variants via Hebrew engine; not decide internally. |
| 21 | Stress in past 2nd-person plural has variants; the reduced-vowel form was chosen. | Mantra UNCERTAINTIES #2 | A | MPE uses Hebrew engine pronunciation metadata; may expose variants. |
| 22 | Transliteration of silent/glottal alef is marked in metadata only. | Mantra UNCERTAINTIES #3 | A | MPE does not generate transliterations; metadata advisory. |
| 23 | Future feminine plural forms are omitted from recitation. | Mantra UNCERTANTIES #5 | A | ProtocolVersion may declare omitted forms; MPE core does not decide. |

### From Hebrew Unresolved Issues

| # | Claim | Source section | Grade | Status in v1.1 |
|---|---|---|---|---|
| 24 | `standard_unvocalized` is a heuristic, not a full G2P/orthographic model. | UNRESOLVED_ISSUES #1 | A | MPE uses `canonical_unvocalized` from `hebrew/orthography.py`; does not invent spelling. |
| 25 | Imperative forms have not been manually validated. | UNRESOLVED_ISSUES #3 | A | MPE excludes unvalidated imperatives from Phase 4C. |
| 26 | Vocal shva flag comes from manual audit/overrides, not Phonikud. | UNRESOLVED_ISSUES #4 | A | MPE treats phonology as advisory. |
| 27 | Weak roots and hollow verbs need systematic testing. | UNRESOLVED_ISSUES #6 | A | Phase 4C restricted to validated 100-verb subset. |
| 28 | `validate_user_answer` does not diagnose wrong tense/person/gender/number/binyan/lemma without paradigm context. | UNRESOLVED_ISSUES #8 | A | MPE delegates all correctness and error-category diagnosis to Hebrew `Evaluator`. |

## Summary

- 8 claims accepted (A).
- 1 claim supported by literature/review (B).
- 2 claims plausible hypotheses (C).
- 13 claims rejected or corrected (D).
- 0 claims N/A.

The dominant pattern in rejected claims is reification of covert mental activity, EEG semantics, generic difficulty, and premature implementation scope. v1.1 corrects these by separating logical from executable identity, adding response-processing layers, and quarantining all sensor/EEG interpretations.
