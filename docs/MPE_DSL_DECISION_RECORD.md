# MPE DSL Decision Record v1.1

## Audit basis

This decision implements `OPEN_QUESTIONS_AND_DECISIONS.md` #1 (Protocol authoring format), `EXECUTIVE_SYNTHESIS.md` point 6 (No textual DSL in Phase 4), and `METHODOLOGY_AND_LIMITATIONS.md` §Limitations #1 (missing original audit inputs now produced).

## Question

Should the protocol authoring format be:

1. Versioned JSON or YAML schema only,
2. An internal typed protocol model plus optional authoring syntax later,
3. A textual DSL from the beginning?

## Status

**Provisional decision: schema-first, typed model, optional textual DSL later.**

## Evaluation

### Option 1: Versioned JSON/YAML schema only

| Criterion | Assessment |
|---|---|
| Implementation complexity | Low. Schema validation, no parser. |
| Validation | Strong. JSON Schema or YAML schema can enforce required fields and types. |
| Migration | Easy. Add schema versions; old fixtures remain parseable. |
| Tooling | Good. Existing validators, editors, diff tools. |
| User authoring | Mediocre for non-developers; acceptable for researchers and developers. |
| Debugging | Good. Fixtures are explicit and inspectable. |
| Security | Good. No arbitrary code execution risk. |
| Reproducibility | Excellent. Same file + same engine version = same protocol. |
| AI-generated protocols | Good. LLMs and scripts can emit JSON reliably. |
| Long-term maintainability | Good. Schema evolution is explicit. |

### Option 2: Internal typed model + optional authoring syntax later

| Criterion | Assessment |
|---|---|
| Implementation complexity | Medium. Requires a typed model layer and a serialization format. |
| Validation | Strong. Types enforce structure at build/load time. |
| Migration | Medium. Model versioning and migration code required. |
| Tooling | Medium. Can generate JSON Schema from types. |
| User authoring | Initial syntax is JSON/YAML; a friendlier syntax can be added later. |
| Debugging | Good. Model is inspectable. |
| Security | Good. No arbitrary code execution. |
| Reproducibility | Excellent if the typed model is the canonical representation. |
| AI-generated protocols | Good. Generate the typed model or its JSON equivalent. |
| Long-term maintainability | Excellent. The model is the authority; syntax is a skin. |

### Option 3: Textual DSL from the beginning

| Criterion | Assessment |
|---|---|
| Implementation complexity | High. Parser, lexer, AST, error messages, source maps. |
| Validation | Medium. Must build DSL-specific validation on top of parsing. |
| Migration | Hard. Textual syntax changes are harder to migrate than schema fields. |
| Tooling | Poor initially. No IDE support, syntax highlighting, or linting without investment. |
| User authoring | Potentially better for humans, but only after the syntax is stable. |
| Debugging | Hard. Source-to-runtime mapping requires source maps. |
| Security | Medium. A DSL can accidentally permit unsafe constructs if not carefully scoped. |
| Reproducibility | Good if the parsed AST is versioned, but the parser itself is a source of variance. |
| AI-generated protocols | Medium. LLMs can emit text, but may produce syntax errors. |
| Long-term maintainability | Poor if the DSL is frozen before the model is validated. |

## Comparison summary

| Criterion | Option 1 | Option 2 | Option 3 |
|---|---|---|---|
| Phase 4A readiness | Excellent | Good | Poor |
| Determinism / reproducibility | Excellent | Excellent | Good |
| Safety and security | Excellent | Excellent | Medium |
| Authoring ergonomics (now) | Acceptable | Acceptable | Unknown |
| Long-term maintainability | Good | Excellent | Risky |
| Risk of premature commitment | Low | Low | High |

## Decision

**Select Option 2 with Option 1 as the concrete serialization format in Phase 4A.**

That means:
- Define an internal typed protocol model (`Protocol`, `Block`, `Trial`, `Instruction`, `StimulusRequest`, etc.).
- Author and store protocols as versioned JSON or YAML fixtures that serialize the typed model.
- Validate fixtures against a JSON Schema generated from the typed model.
- Do not build a textual DSL parser in Phase 4.
- A textual authoring syntax may be introduced later (Phase 6+) only after the typed model is stable and validated.

## Why not a textual DSL now?

- The protocol model is not yet validated by real sessions.
- A textual DSL would force early syntax decisions before semantics are proven.
- Parser maintenance would divert effort from the runtime, Hebrew integration, and behavioral validation.
- JSON/YAML fixtures are sufficient for Phase 4A–4C and Phase 5A simulation.
- A textual DSL can be added as a compile-to-JSON layer without changing the runtime.

## Open question

What should the textual DSL look like if it is introduced later? This is deferred to `MPE_OPEN_DECISIONS.md`.

## Traceability

This decision implements `OPEN_QUESTIONS_AND_DECISIONS.md` #1 (authoring format options and recommendation), `EXECUTIVE_SYNTHESIS.md` point 6 (no textual DSL in Phase 4), and `METHODOLOGY_AND_LIMITATIONS.md` §Limitations #1 (missing original audit inputs now produced). It also aligns with `MPE_PHASE_4_IMPLEMENTATION_PLAN.md` Phase 4A (schema-first fixtures).
