# Phase 2 Hardening Report — Shared Hebrew Linguistic Engine

## 1. What was implemented

### 1.1 Source registry and policy

- Created `data/hebrew/source_registry.json` with 8 sources and explicit eligibility fields.
- Created `data/hebrew/SOURCE_POLICY.md` defining the 5 eligibility tiers and runtime filtering rules.
- Added `hebrew/resources/source_registry.py` (`SourceRegistry`) with `is_eligible`, `filter_records`, `production_approved`, `research_only`, `reference_only`, and `blocked_or_unknown` helpers.

### 1.2 Approval layers

- Extended `hebrew/models.py` with explicit fields:
  - `linguistic_status` (`raw`, `normalized`, `candidate`, `validated`, `disputed`, `rejected`)
  - `curriculum_status` (`not_reviewed`, `approved`, `restricted`, `rejected`)
  - `validation_evidence`, `source_agreement`, `reviewer_status`, `confidence`, `rejection_reason`
- Added `hebrew/approval.py` (`ApprovalPipeline`) enforcing the separation:
  - a raw record can be normalized,
  - a normalized record can be a candidate,
  - a candidate can be validated,
  - only a validated record with a `production_approved` source can become `curriculum_status: approved`.

### 1.3 Form consensus

- Added `hebrew/consensus.py` (`build_consensus`) that compares source-specific forms and produces:
  - canonical vocalized and unvocalized forms,
  - agreement/disagreement counts,
  - source form map,
  - confidence score,
  - preserved `SourceDisagreement` records.
- Integrated consensus into `hebrew/conjugation_engine.py`; the engine now merges Pealim, Eran Tomer and Verb Inflector forms by `form_key` and by matching surface/plain form, and preserves all disagreements.

### 1.4 Modern-usage classification

- Added `hebrew/usage.py` (`classify_form`, `classify_sentence`).
- Classifications: `core_modern`, `common_modern`, `valid_but_rare`, `literary`, `archaic`, `disputed`, `unattested`, `unknown`.
- Does **not** infer common usage from morphology alone; uses SVLM corpus counts and a small `CORE_FORM_KEYS` whitelist for the most essential forms.

### 1.5 Three-verb gold fixtures

- Created `hebrew/build_gold_fixtures.py`.
- Generated immutable fixtures:
  - `data/hebrew/gold_verbs/lichtov.json`
  - `data/hebrew/gold_verbs/lihyot.json`
  - `data/hebrew/gold_verbs/laasot.json`
- Each fixture contains: approved lemma, root, binyan, full approved paradigm, all forms, pronunciation, stress, source comparisons, known exceptions, accepted variants, rejected variants and shva-ambiguous cases.

### 1.6 Shva and pronunciation audit

- Added `hebrew/shva.py` with explicit `shva_status` values: `vocal`, `silent`, `ambiguous`, `not_applicable`.
- Manual override is authoritative; Phonikud prediction is low-confidence; everything else defaults to `ambiguous`.
- Added `shva` diagnosis to `PronunciationRecord` and `VerbForm`.
- Preserved all existing pronunciation overrides in `data/hebrew/overrides/pronunciation.json`.

### 1.7 Sentence candidate safety

- Hardened `hebrew/services/sentence_service.py`:
  - computes target-form presence, exact/morphological match, token count, punctuation quality, suspected noise, ambiguity, vocabulary complexity and licensing eligibility;
  - SVLM candidates are never auto-approved;
  - `curriculum_status` remains `not_reviewed` or `rejected` until explicit review.

### 1.8 Answer diagnosis schema

- Added `hebrew/diagnosis.py` and `hebrew/services/diagnosis_service.py`.
- Diagnosis types: `correct`, `spelling`, `niqqud_only`, `wrong_person`, `wrong_gender`, `wrong_number`, `wrong_tense`, `wrong_binyan`, `wrong_root`, `valid_alternate`, `pronunciation_only`, `unknown`.
- `diagnose_answer` compares a learner answer against a gold `VerbForm` and known forms, returning `diagnosis_type` and `affected_feature`.

### 1.9 Tests

- Expanded `tests/test_hebrew_engine.py` from 13 to 38 tests covering:
  - source registry and eligibility filtering,
  - approval-layer transitions,
  - consensus and disagreement preservation,
  - shva diagnosis and ambiguity reports,
  - usage classification,
  - gold fixture existence, required fields and infinitive approval,
  - sentence candidate rejection,
  - learner-answer diagnosis,
  - vocalized and unvocalized matching.
- All 38 tests pass.

## 2. Exact test results

```
$ source .venv_phonikud/bin/activate
$ python -m unittest tests.test_hebrew_engine -v
----------------------------------------------------------------------
Ran 38 tests in ~4.3s
OK
```

## 3. Unresolved licensing issues

| Source | Eligibility | Issue |
|--------|-------------|-------|
| Pealim | `reference_only` | No explicit license from pealim.com. The local forms are used only as an internal reference and must be replaced or relicensed before any redistribution. |
| Pealim audit | `reference_only` | Derived from Pealim; same unresolved status. |
| SVLM | `private_research_only` | CC-BY-SA 3.0 share-alike. It is unclear whether a derived curriculum dataset can remain private or must be published under the same license. |
| Phonikud (library) | `private_research_only` | PyPI package `phonikud 0.4.1` has no explicit license. Runtime dependency only, but license should be clarified. |
| Piper voice `shaul` | `reference_only` | License of `shaul.onnx` and generated audio is unverified. Commercial use is unconfirmed. |

## 4. Unresolved linguistic issues

1. **Standard unvocalized spelling heuristic** still has edge cases (e.g., `רֹאשׁ` > `ראש` should not insert `ו`).
2. **Vocal shva** is not automatically detected; ambiguous cases remain and require manual review.
3. **Root extraction** is not automated; roots come from Pealim or are supplied manually.
4. **Imperative and rare feminine/plural forms** are generated by the Verb Inflector but not always attested in Pealim or SVLM.
5. **Present forms of `להיות`** are missing from the local Pealim snapshot; they were approved from Eran Tomer + Verb Inflector consensus.
6. **Surface spelling variants** (e.g., `הָיְתָה` vs `הָיְיתָה` for `lihyot`) are recorded as accepted variants but may need final editorial choice.
7. **Sentence pedagogy** is not yet validated by a Hebrew linguist; corpus filters are mechanical.

## 5. Records blocked from production

Sources that are **not** `production_approved` in strict mode:

- `pealim` (reference only)
- `pealim_audit` (reference only)
- `svlm` (private research only)
- `phonikud` (private research only)
- `piper_voice_shaul` (reference only)
- any record whose `source_id` is missing from the registry

Runtime result: Pealim-derived forms are validated but start as `curriculum_status: not_reviewed` or `restricted`. Only `manual_override`, `eran_tomer`, and `verb_inflector` can directly support `curriculum_status: approved`.

## 6. Disagreements found in the three verbs

| Verb | Approved forms | All forms | Rejected forms | Shva ambiguous | Known exceptions |
|------|----------------|-----------|----------------|----------------|------------------|
| `לכתוב` | 25 | 27 | 2 | 23 | 19 |
| `להיות` | 22 | 22 | 0 | 10 | 12 |
| `לעשות` | 19 | 22 | 3 | 2 | 30 |

Typical disagreements preserved:
- `surface_vocalized` (minor): holam on vav vs. holam on consonant (e.g., `לִכְתּוֹב` vs `לִכְתֹּב`).
- `lexical_stress`: Phonikud vs. manual Pealim audit stress positions.
- `phonemes_corrected`: raw Phonikud output vs. manual corrected phonemes.
- `surface_plain`: genuine spelling variants (e.g., `היתה` vs `הייתה` for `lihyot`).

Rejected forms are mainly unapproved feminine/plural imperatives and `future_second_f_plural`, which lack Pealim attestation or have unresolved conflicts.

## 7. Readiness recommendations

| Use case | Ready? | Notes |
|----------|--------|-------|
| Private experiments | **Yes** | Engine, indexes, tests and fixtures are functional. |
| Mantra generation | **Cautious yes** | Use only `curriculum_status: approved` records and `manual_override` pronunciation. Do not ship Pealim-derived data. |
| Hebrew Lab exercises | **Cautious yes** | Same as Mantra; verify each approved form and sentence before release. |
| Public distribution | **No** | Pealim licensing is unresolved; CC-BY-SA implications for SVLM-derived content are unresolved; Phonikud and `shaul` voice licenses are unverified. |
| Commercial distribution | **No** | Same blockers as public distribution, plus commercial status of Phonikud and voice assets is unverified. |

## 8. Next steps (outside this phase)

1. Replace or license Pealim reference data.
2. Resolve `shaul.onnx` / generated-audio license and confirm commercial eligibility.
3. Obtain or confirm Phonikud license.
4. Run a linguist review of the three gold fixtures, especially ambiguous shva cases and accepted spelling variants.
5. Implement a manual sentence-approval workflow before SVLM examples enter production exercises.
6. Add CI step that runs `python -m unittest tests.test_hebrew_engine` and blocks `curriculum_status: approved` changes that rely on `reference_only` sources.
