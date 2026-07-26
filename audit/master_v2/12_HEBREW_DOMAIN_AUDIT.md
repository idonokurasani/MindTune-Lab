# 12 — Hebrew Domain Audit

## 1. Domain Adapter (`packages/mpe/src/mpe/domains/hebrew/`)

| Module | Purpose | Status |
|---|---|---|
| `adapter.py` | `HebrewDomainAdapter`: resolve content, build prompts, normalize/evaluate typed responses | Production |
| `canonical.py` | `HebrewLexicalEntity` with optional HeLP enrichment | Production |
| `fixtures.py` | Versioned Hebrew immediate-recall content fixtures | Production |
| `models.py` | Typed Hebrew content models | Production |
| `normalization.py` | Conservative normalization (NFC, whitespace, punctuation) | Production |
| `integration.py` | MPE runtime glue | Production |
| `help/` | HeLP loader, models, repository, profiler, validation | Production |

## 2. HeLP Integration

- `HELP_INTEGRATION.md` declares HeLP as the canonical psycholinguistic source.
- Data: `data/hebrew_verbs_help_forms.csv`, `data/hebrew_verbs_help_audit.csv`, `data/hebrew_verbs_help_enrichment.json`.
- `HeLPLoader` is deterministic; `HeLPRepository` is read-only in-memory.
- Boundary rule: generic MPE runtime receives only `BehavioralEvidence`, never HeLP fields.

## 3. Source Policy

`data/hebrew/SOURCE_POLICY.md` defines 5 eligibility tiers:

- `production_approved`
- `private_research_only`
- `reference_only`
- `blocked`
- `unknown`

`data/hebrew/source_registry.json` lists 8 sources with explicit eligibility.

## 4. Shared Hebrew Engine (`hebrew/`)

- `models.py` — multi-source trust tiers, approval status, usage classification.
- `conjugation_engine.py` — aggregates Eran Tomer, Pealim, Verb Inflector.
- `adapters/phonikud_adapter.py` — IPA phonemization via `phonikud`.
- `services/` — diagnosis, pronunciation, sentence, validation, verb.

## 5. Scientific Validity

- HeLP norms are peer-reviewed (Stein, Frost & Siegelman 2024).
- Multi-source consensus and source eligibility provide transparent provenance.
- Pealim and Phonikud licenses are unclear/unknown; marked `reference_only` or `private_research_only`.

## 6. Disposition

**KEEP** — Hebrew domain adapter and HeLP integration are well-architected and should be reused as V2 domain adapters.
