# Curriculum v1.0.0 Audit Report

- Curriculum version: 1.0.0
- Generated at: 2026-07-25T11:47:18.931852+00:00
- Source: hebrew.phase3.eran_tomer

## Summary

- total_verbs: 320
- duplicate_verb_ids: 22
- duplicate_infinitives: 22
- duplicate_asset_id_prefixes: 0
- suspicious_spellings: 123
- possible_defective_variants: 0
- tokenization_problems: 0
- lexical_ambiguities: 22
- blocking_issues: 142

## Investigated verbs

### לעשות
- asset_id_prefix: lasot
- binyan: PA'AL
- frequency: 130571
- is_infinitive: True
- issues: none
- confidence: high
- recommended action: keep
- blocks asset generation: False
- evidence: source=A_50_עשה; frequency=130571; selection_reason=["binyan_PA'AL", 'root_class_guttural', 'root_class_final_he', 'root_class_irregular']

### לתת
- asset_id_prefix: latet
- binyan: PA'AL
- frequency: 51410
- is_infinitive: True
- issues: none
- confidence: high
- recommended action: keep
- blocks asset generation: False
- evidence: source=A_28_נתן; frequency=51410; selection_reason=['frequency']

### לחבור
- asset_id_prefix: lachbor
- binyan: PA'AL
- frequency: 98023
- is_infinitive: True
- issues: none
- confidence: high
- recommended action: keep
- blocks asset generation: False
- evidence: source=A_10_חבר; frequency=98023; selection_reason=['frequency']

### לבצוע
- asset_id_prefix: livtzoa
- binyan: PA'AL
- frequency: 9895
- is_infinitive: True
- issues: none
- confidence: high
- recommended action: keep
- blocks asset generation: False
- evidence: source=A_22_בצע; frequency=9895; selection_reason=['frequency']

### לחבר
- asset_id_prefix: lechaber
- binyan: PI'EL
- frequency: 99418
- is_infinitive: True
- issues: ['unicode_not_nfc']
- confidence: high
- recommended action: correct_in_next_curriculum_version
- blocks asset generation: True
- evidence: source=C_1_חבר; frequency=99418; selection_reason=['frequency']


## Methodology

The audit compares the curriculum JSON against the Eran Tomer source lookup, detects duplicates, checks Unicode normalization (NFC), flags non-infinitive lemmas, and records pedagogical notes. Corpus frequency alone does not determine pedagogical priority.