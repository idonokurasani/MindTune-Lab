# Curriculum v1.0.0 Audit Report

- Curriculum version: 1.0.0
- Generated at: deterministic (no timestamp)
- Source: hebrew.phase3.eran_tomer

## Summary

- total_verbs: 320
- duplicate_verb_ids: 0
- duplicate_infinitives: 22
- duplicate_asset_id_prefixes: 0
- suspicious_spellings: 0
- possible_defective_variants: 0
- tokenization_problems: 0
- lexical_ambiguities: 23
- blocking_issues: 0
- missing_italian_infinitives: 320

## Investigated verbs

### לעשות (lasot)
- asset_id_prefix: lasot
- binyan: PA'AL
- frequency: 130571
- is_infinitive: True
- issues: ['missing_italian_infinitive']
- confidence: high
- recommended action: keep_with_note
- blocks asset generation: False
- evidence: source=A_50_עשה; source_record_count=1; frequency=130571; selection_reason=["binyan_PA'AL", 'root_class_guttural', 'root_class_final_he', 'root_class_irregular']

### לתת (latet)
- asset_id_prefix: latet
- binyan: PA'AL
- frequency: 51410
- is_infinitive: True
- issues: ['missing_italian_infinitive']
- confidence: high
- recommended action: keep_with_note
- blocks asset generation: False
- evidence: source=A_28_נתן; source_record_count=1; frequency=51410; selection_reason=['frequency']

### לחבור (lachbor)
- asset_id_prefix: lachbor
- binyan: PA'AL
- frequency: 98023
- is_infinitive: True
- issues: ['missing_italian_infinitive']
- confidence: high
- recommended action: keep_with_note
- blocks asset generation: False
- evidence: source=A_10_חבר; source_record_count=1; frequency=98023; selection_reason=['frequency']

### לבצוע (livtzoa)
- asset_id_prefix: livtzoa
- binyan: PA'AL
- frequency: 9895
- is_infinitive: True
- issues: ['missing_italian_infinitive']
- confidence: high
- recommended action: keep_with_note
- blocks asset generation: False
- evidence: source=A_22_בצע; source_record_count=1; frequency=9895; selection_reason=['frequency']

### לחבר (lechaber)
- asset_id_prefix: lechaber
- binyan: PI'EL
- frequency: 99418
- is_infinitive: True
- issues: ['missing_italian_infinitive']
- confidence: high
- recommended action: keep_with_note
- blocks asset generation: False
- evidence: source=C_1_חבר; source_record_count=1; frequency=99418; selection_reason=['frequency']


## Methodology

The audit compares the curriculum JSON against the Eran Tomer source records keyed by source group, preserves all source records for homographic infinitives, detects duplicate verb_ids / asset prefixes, checks Unicode normalization (NFC), flags non-infinitive lemmas, and records pedagogical notes. Corpus frequency alone does not determine pedagogical priority.