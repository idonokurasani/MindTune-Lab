# MindTune Protocol Ontology Audit v1

This package contains the audit inputs used to revise the MindTune Protocol Engine (MPE) architecture from v1.0 to v1.1.

It is a documentation-only artifact. It does not modify source code, tests, the Hebrew engine, or runtime schemas.

## Files

- `COGNITIVE_PROTOCOL_ONTOLOGY.md` — Core conceptual entities and their operational definitions.
- `PROTOCOL_PRIMITIVES_CATALOG.md` — Catalog of allowed and prohibited protocol primitives.
- `SOURCE_CLAIM_AUDIT.md` — Audit of claims in MPE v1.0 and other source documents, with evidence grades.
- `SOURCE_CLAIM_AUDIT.csv` — Machine-readable version of the claim audit.
- `DOMAIN_INDEPENDENCE_MAP.md` — Separation between MPE core and domain/sensor providers.
- `OPEN_QUESTIONS_AND_DECISIONS.md` — Unresolved decisions and evidence needed before implementation.
- `EXECUTIVE_SYNTHESIS.md` — Summary of audit findings and v1.1 direction.
- `METHODOLOGY_AND_LIMITATIONS.md` — How the audit was performed and its limits.
- `PROTOCOL_DECOMPOSITION_MATRIX.csv` — Trial/task decomposition across protocol families.

## Purpose

The audit enforces the following non-negotiable principles:

1. Behavioral evidence is primary.
2. Covert mental activity is not directly observable.
3. Cognitive states are estimates, not facts.
4. The Hebrew engine is the domain authority for Hebrew correctness.
5. EEG and sensor features are exploratory until validated.
6. Adaptation must abstain when evidence is insufficient.
7. Phase 4 must work without EEG, adaptation, or a textual DSL.

## Status

This is the v1 audit package. It is intended to be read before MPE v1.1 architecture documents are approved.
