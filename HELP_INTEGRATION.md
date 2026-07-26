# HeLP — Hebrew Lexicon Project Integration

## Overview

HeLP (Stein, Frost & Siegelman, 2024) is now the canonical psycholinguistic
evidence source for the Hebrew domain in MindTune Lab.  It provides lexical
and conjugation norms that inform difficulty priors, item selection and
profiler evidence without entering the domain-independent MPE runtime.

## Data files

| File | Role |
|------|------|
| `data/hebrew_verbs_help_forms.csv` | Form-level frequency, AoA and length norms. |
| `data/hebrew_verbs_help_audit.csv` | Audit trail linking raw records to canonical items. |
| `data/hebrew_verbs_help_enrichment.json` | Optional verb-level enrichment payload. |

## Domain module

```
packages/mpe/src/mpe/domains/hebrew/help/
├── __init__.py      # public exports
├── models.py        # HeLPProvenance, HeLPFormEvidence, HeLPVerbSummary
├── provenance.py    # provenance record builders
├── schemas.py       # lightweight record validation
├── validation.py    # duplicate detection and import reports
├── loader.py        # deterministic loader from configured paths
├── repository.py    # read-only in-memory query layer
└── profiler.py      # difficulty and selection profiling
```

## Canonical Hebrew entity

`packages/mpe/src/mpe/domains/hebrew/canonical.py` defines `HebrewLexicalEntity`,
a stable domain object enriched with optional HeLP evidence.  The repository's
`enrich_entity()` method attaches evidence without mutating source data.

## Usage

```python
from mpe.domains.hebrew.help import HeLPLoader, HeLPRepository

loader = HeLPLoader().load()
repo = HeLPRepository()
forms = repo.by_form("אוכל")
summaries = repo.by_verb("אכל")
```

## Boundary rules

- HeLP evidence is consumed only by Hebrew-domain code.
- The generic MPE runtime receives only `BehavioralEvidence` (correctness,
  latency, omission, evaluation status and stable identifiers).
- No HeLP-specific fields, roots or binyan labels cross the adapter boundary.
- Difficulty priors are surfaced only as generic selection or pacing hints,
  never as hard cognitive-state transitions.

## Provenance

Every loaded HeLP record carries a `HeLPProvenance` object with the source
dataset, import timestamp and dataset version.  When no explicit version is
supplied, the dataset file modification time is used.

## Tests

`packages/mpe/tests/test_help_integration.py` covers loader, repository,
profiler and canonical entity enrichment.
