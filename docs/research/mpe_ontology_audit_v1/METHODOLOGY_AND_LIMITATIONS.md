# Methodology and Limitations v1

## Methodology

This audit was performed by comparing `docs/MINDTUNE_PROTOCOL_ENGINE_ARCHITECTURE_v1.0.md` against:

1. The explicit non-negotiable principles in the v1.1 revision brief.
2. The completed Phase 3 Hebrew engine outputs and `data/hebrew/phase3/PHASE_3_FINAL_REPORT.md`.
3. Domain-independent design constraints (single-responsibility provider boundaries, separation of concerns).
4. Cognitive-science conservatism (covert mental activity is not observable, EEG cannot read thoughts, adaptation must abstain).
5. Software-engineering staging principles (no premature DSL, no monolithic interfaces, deterministic before adaptive).

Each claim in v1.0 and related source documents was classified with an evidence grade:

- `A` — supported by project artifact.
- `B` — supported by literature/expert review.
- `C` — plausible hypothesis.
- `D` — unsupported or misleading.

Claims graded `D` were marked for correction in v1.1.

## Limitations

1. **Missing original audit inputs.** The documents `COGNITIVE_PROTOCOL_ONTOLOGY.md`, `PROTOCOL_PRIMITIVES_CATALOG.md`, `SOURCE_CLAIM_AUDIT.md`, `DOMAIN_INDEPENDENCE_MAP.md`, `OPEN_QUESTIONS_AND_DECISIONS.md`, and `EXECUTIVE_SYNTHESIS.md` did not exist before this audit. They were created as audit outputs and now serve as the audit inputs for v1.1.
2. **No external expert review.** This audit is an internal design review. Independent cognitive, linguistic, and clinical review is still required before deployment.
3. **No empirical validation.** The audit does not run experiments. It only checks consistency, traceability, and conservative interpretation.
4. **Limited clinical scope.** The audit treats cognitive rehabilitation and clinical protocols as future domains requiring separate justification.
5. **Technology dependencies.** The audit assumes the existing Hebrew engine, TTS pipeline, and EEG acquisition code are available but does not verify their runtime performance.
6. **Domain coverage.** The audit focuses on Hebrew as the first domain. Music, memory, and other domains are assumed to require analogous provider implementations.

## Traceability

Every correction in v1.1 can be traced to:
- a v1.0 section or claim,
- an audit document in this package,
- a Phase 3 constraint where applicable.
