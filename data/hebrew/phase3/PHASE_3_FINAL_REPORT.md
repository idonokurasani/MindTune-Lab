# Phase 3 Final Report — Hebrew Linguistic Reliability Pipeline

**Date:** 2026-07-23  
**Scope:** Build a deterministic, reproducible validation and benchmark pipeline for Modern Israeli Hebrew verb forms, with explicit abstention and without treating LLM output as authoritative.  
**Target:** Justify (or limit) the claim that the pipeline can produce reliable, externally-grounded records for Hebrew verb morphology, orthography, pronunciation, and stress.

## Executive conclusion

**Target justified only for a restricted scope.**

The deterministic Phase 3 pipeline is internally consistent, testable, and reproducible for a high-frequency 100-verb subset of Modern Israeli Hebrew. It correctly labels records, separates benchmark partitions, and abstains when evidence is insufficient. However, the two largest "production" sources (Eran Tomer and the Verb Inflector) derive from the same codebase/data, pronunciation validation still depends on an advisory tool (Phonikud), and the entire effort is scoped to verbs. A broader claim for the full language or a fully independent gold standard is **not yet justified**.

## What was delivered

| Module | File | Role | Status |
|---|---|---|---|
| Normative orthography | `hebrew/orthography.py` | `canonical_unvocalized`, root-class classification, variant classes (`full`/`defective`/`common_nonstandard`/`rejected`) | Done |
| Phonology / stress | `hebrew/phonology.py` | Phonemic/practical transcription, syllabification, 1-indexed lexical stress, shva, dagesh, begadkefat, variants, `unresolved` flag | Done |
| 100-verb selection | `hebrew/phase3/selection.py` | High-frequency coverage of all seven binyanim + major weak-root classes | Done |
| Verified-consensus expansion | `hebrew/phase3/gold_expansion.py` | Produces `data/hebrew/phase3/automatic_gold_100.json` with per-form evidence, rule traces, and status labels | Done |
| Confidence & abstention | `hebrew/phase3/confidence.py` | `verified_consensus`, `high_confidence_candidate`, `disputed`, `unresolved`, `rejected` | Done |
| Differential testing | `hebrew/phase3/differential.py` | Compares Eran Tomer vs. fresh Verb Inflector generation | Done |
| Round-trip / property tests | `hebrew/phase3/round_trip.py` | Morphology tag → form key → generated surface | Done |
| Adversarial invalid-form tests | `hebrew/phase3/adversarial.py` | Mutated surfaces checked against the corpus | Done |
| Frozen benchmark partitions | `hebrew/phase3/benchmark.py` | `development`/`calibration`/`blind_evaluation` with leakage detection | Done |
| CI regression gate | `scripts/phase3_ci.sh` | Runs full test suite and prints key metrics | Done |

## Key metrics

All numbers below were produced by `scripts/phase3_ci.sh` (and its embedded Python snippet) on the current checkout.

| Metric | Value | Interpretation |
|---|---|---|
| Full test suite | **96 passed, 67 subtests passed** | `pytest tests/ -q` |
| Differential agreement | **241,497 / 241,497** signatures match between Eran Tomer and the fresh Verb Inflector generation | `differential.py` reports 0 disagreements |
| Round-trip success rate | **1.0000** (1000-form random sample) | `round_trip.py` confirms morphology tags map to expected surfaces |
| Adversarial false-acceptance rate | **0.0381** (100-form sample, 315 mutations) | ~3.8% of mutations coincidentally exist in the corpus; the engine/corpus correctly rejects the rest |
| Benchmark partitions | **157,980 unique (surface, form_key) pairs** | `development` 15,282; `calibration` 31,076; `blind_evaluation` 111,622 |
| Cross-partition leakage | **0** | No (surface, form_key) pair appears in more than one partition |
| 100-verb expansion | **100 verbs, 3,006 unique forms, 100% `verified_consensus`** | `automatic_gold_100.json` status summary: `verified_consensus: 3006` |

## Evidence model and status labels

`hebrew/phase3/confidence.py` implements the required hierarchy:

- `verified_consensus` — two production-approved sources agree, no production rejection.
- `high_confidence_candidate` — one production source plus strong corpus/private-research support.
- `disputed` — independent sources disagree on the accepted form.
- `unresolved` — insufficient evidence or `unresolved=True` from orthography/phonology.
- `rejected` — a production source or normative rule explicitly rejects the form.

Important: the "gold" label is reserved for externally grounded benchmark records. `automatic_gold_100.json` is a **candidate** set, not benchmark gold.

## LLM feasibility outcome

DictaLM 3.0 1.7B is the only practical local/Apple-Silicon option; HEBATRON's 31.6B Mamba2+MoE and ~24–34 GB quantized sizes make it a later-phase option. Both models remain **advisory only** and are never on the required path. The final evaluation is in `data/hebrew/phase3/ISRAELI_HEBREW_MODELS_EVALUATION.md`.

## Honest limitations that restrict the target

1. **Non-independent production sources.** Eran Tomer `InflectedVerbsExtended.csv` and the Verb Inflector `Inflected verbs Extended.txt` are generated by the same Java codebase. The differential test therefore finds zero disagreements by construction, and the `verified_consensus` labels reflect self-consistency, not independent corroboration.
2. **Pronunciation is advisory.** `hebrew/phonology.py` uses Phonikud as a deterministic proposal and honors manual overrides; unresolved disagreements are flagged but do not by themselves block a spelling/morphology consensus. This is the correct abstention behavior, but it means stress/phonemic fields should not be treated as independently verified.
3. **Limited lexical coverage.** The 100-verb expansion covers the seven binyanim and major weak-root classes, but it is a small slice of Hebrew. The frozen benchmark is larger (~158k unique pairs) but still derived from the same Verb Inflector/Eran Tomer generator.
4. **Adversarial false acceptances are expected corpus collisions.** A 3.8% false-acceptance rate for mutations is acceptable for a sanity gate, but it also shows that simple surface membership can be fooled by accidental homographs or valid variants.
5. **No human or Academy-of-the-Hebrew-Language sign-off.** All records are machine-derived; the "verified" in `verified_consensus` refers to algorithmic agreement, not institutional certification.

## Recommendation

- **For the restricted scope** — high-frequency Modern Israeli Hebrew verbs, deterministic orthography, advisory phonology, and a frozen external benchmark — the target is **justified**.
- **For general Hebrew linguistic reliability, full pronunciation accuracy, or a true independent gold standard** — the target is **not yet justified**.
- Keep LLMs out of the required path.
- Treat `automatic_gold_100.json` as a candidate set and continue to seek independent sources (Pealim, academic lexica, manually annotated benchmarks) to corroborate or dispute its `verified_consensus` records.

## Files produced / updated

- `hebrew/orthography.py` + `tests/test_orthography.py`
- `hebrew/phonology.py` + `tests/test_phonology.py`
- `hebrew/phase3/selection.py`
- `hebrew/phase3/gold_expansion.py`
- `hebrew/phase3/confidence.py`
- `hebrew/phase3/data_loader.py`
- `hebrew/phase3/differential.py`
- `hebrew/phase3/round_trip.py`
- `hebrew/phase3/adversarial.py`
- `hebrew/phase3/benchmark.py`
- `tests/test_phase3_validation.py`
- `scripts/phase3_ci.sh`
- `data/hebrew/phase3/automatic_gold_100.json`
- `data/hebrew/phase3/benchmark_partitions.json`
- `data/hebrew/phase3/ISRAELI_HEBREW_MODELS_EVALUATION.md`
- This report: `data/hebrew/phase3/PHASE_3_FINAL_REPORT.md`
