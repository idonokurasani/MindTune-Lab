# Phase 3 Plan — Automated Linguistic Reliability Expansion

## Objective

Raise the general linguistic reliability of the shared Hebrew engine through automated validation, differential testing, gold expansion, adversarial testing, confidence calibration, and strict abstention.

## Scope

Modern Israeli Hebrew verb morphology, orthography, and pronunciation only.

Reliability dimensions: lemma, root, binyan, tense/mood, person, gender, number, vocalized form, canonical unvocalized spelling, pronunciation, lexical stress, shva classification, accepted variants, rejection of nonexistent forms.

## Constraints

- No TTS work.
- No UI features.
- No human review workflow.
- No claim of 9.5/10 reliability without measured benchmark evidence.
- Phase 2 baseline is immutable; any modification requires a diff and justification.

## Strategy

1. **Normative rule engine**  
   Build a rule-tracing wrapper around existing sources (Verb Inflector, Eran Tomer, internal grammar tables) and explicit orthographic/phonological rules. The engine records every transformation and can abstain when the derivation is unclear.

2. **Orthography module**  
   Replace heuristic `standard_unvocalized` with an explicit Modern Hebrew spelling module that produces canonical, full, defective, common nonstandard and rejected spelling classes with rule traces.

3. **Phonological validation**  
   Store phonemic, practical pronunciation, syllabification, stress, shva, dagesh, begadkefat realization, variants, rule traces, Phonikud comparison and override comparison. Phonikud remains advisory.

4. **Gold expansion**  
   Starting from the 3 Phase 2 gold verbs, use the Verb Inflector over the Eran Tomer `TheVerbIndex.csv` plus SVLM corpus frequency to select and generate candidate paradigms for the most frequent verbs. Each candidate is classified as `verified_automatic_gold`, `high_confidence_candidate`, `disputed`, `unresolved`, or `rejected`.

5. **Independent evidence consensus**  
   Compare evidence groups, track derivations, require independent confirmation, and produce per-form evidence reports.

6. **Differential testing**  
   Run large-scale comparisons among the internal normative engine, Verb Inflector, Eran Tomer and approved Pealim records. Classify disagreements and produce `DIFFERENTIAL_DISAGREEMENTS.md`.

7. **Round-trip property testing**  
   `lemma + features → generate → analyze → reconstruct`. Generate at least 100,000 cases from Eran Tomer and Verb Inflector outputs across binyanim and root classes.

8. **Adversarial testing**  
   Generate malformed and plausible-but-invalid forms. Measure false-acceptance rate.

9. **Benchmark**  
   Create frozen `development.jsonl`, `validation.jsonl`, `blind_test.jsonl`, and `benchmark_manifest.json` with the required record counts (target minimums).

10. **Confidence and abstention**  
    Calibrate confidence components against the validation partition. Enforce abstention on low-confidence, ambiguous, conflicted or unattested cases.

11. **Metrics**  
    Compute per-component metrics (lemma, root, binyan, features, spelling, pronunciation, stress, shva, false acceptance, learner diagnosis, calibration) and produce `RELIABILITY_METRICS.json`.

12. **Reports**  
    Generate all requested Phase 3 deliverables in `data/hebrew/phase3/`.

## Implementation order

1. Read Phase 2 baseline and freeze it.
2. Build orthography and phonology modules.
3. Build normative engine with rule traces.
4. Generate expanded gold candidates.
5. Differential testing.
6. Round-trip and adversarial tests.
7. Build benchmark partitions.
8. Confidence calibration and metrics.
9. Final report.
