# MindTune Lab — Shared Hebrew Linguistic Engine

This package provides **shared linguistic infrastructure** for all Hebrew features in MindTune Lab (Mantra, conjugation drills, root drills, reading, listening, pronunciation, etc.). It is intentionally **not** Mantra-specific.

## Architecture

```
mindtune_console/hebrew/
  models.py                 shared data model
  normalization.py          Unicode and orthographic normalization
  morphology.py             feature parsing / binyan mapping
  conjugation_engine.py     aggregates sources into paradigms
  pronunciation_engine.py   Phonikud + central override layer
  provenance.py             source evidence and conflict detection
  validation.py             answer validation and error diagnosis
  overrides.py              central override registry
  exceptions.py             engine errors
  resources/                resource loaders and index builders
  adapters/                 external engine adapters (Phonikud, Piper, Verb Inflector)
  services/                 high-level service API
data/hebrew/
  resources/                upstream/local resource files
  indexes/                  generated indexes
  manifests/                resource manifests
  overrides/                central override JSON
  audits/                   audit trail
  approved/                 validated paradigms
  rejected/                 rejected records
```

## Required runtime

Activate the `phonikud` virtual environment (it already contains `phonikud`, `piper-onnx`, `soundfile`, `numpy`):

```bash
cd "/Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console"
source .venv_phonikud/bin/activate
```

The Verb Inflector requires Java. On macOS the engine was tested with:

```bash
/opt/homebrew/opt/openjdk/bin/java -version  # OpenJDK 26
```

The adapter tries `/opt/homebrew/opt/openjdk/bin/java` first, then falls back to `JAVA_HOME` or `java` on `PATH`.

## Build indexes and manifests

```bash
source .venv_phonikud/bin/activate
python -m hebrew.ingest
```

This parses Eran Tomer (`data/hebrew/resources/eran_tomer/`) and SVLM (`data/hebrew/resources/svlm/`) and writes:

- `data/hebrew/indexes/eran_tomer/{records,indexes,rejected,manifest}.json`
- `data/hebrew/indexes/svlm/{sentences,indexes,rejected,manifest}.json`
- `data/hebrew/manifests/hebrew_resources_manifest.json`

SVLM ingestion is intentionally candidate-only; sentences are not marked pedagogically suitable until reviewed.

## Validate the three target verbs

```bash
source .venv_phonikud/bin/activate
python -m hebrew.validate_three_verbs
```

This generates approved paradigms and source-comparison reports under `data/hebrew/approved/` for `לכתוב`, `להיות`, `לעשות`.

## Run tests

```bash
source .venv_phonikud/bin/activate
python -m unittest tests.test_hebrew_engine -v
```

## Core service API

```python
from hebrew.services.verb_service import VerbService
from hebrew.services.sentence_service import SentenceService
from hebrew.services.pronunciation_service import PronunciationService
from hebrew.services.validation_service import ValidationService

verb_service = VerbService()
paradigm = verb_service.get_full_paradigm(
    "לִכְתֹּב", "לכתוב", "כ-ת-ב", "PA'AL"
)
forms = verb_service.get_conjugation(
    "לכתוב", tense="past", person="first", number="singular"
)

sentence_service = SentenceService()
examples = sentence_service.get_example_sentences("לכתוב", limit=5)

pron = PronunciationService().get_pronunciation("לִכְתֹּב")

result = ValidationService().validate("כותב", "כּוֹתֵב")
```

## Source hierarchy

1. Manually approved record / central override
2. Pealim-verified record
3. Agreement between trusted local sources
4. Single-source candidate (requires review)

No unresolved conflict is silently promoted to approved status.

## Design principles

- Morphology, pronunciation and voice rendering are separate layers.
- The `PiperAdapter` can be replaced without touching morphology or curriculum data.
- Central overrides propagate to every Hebrew Lab consumer.
- Every form carries `source_evidence`, `applied_overrides` and `unresolved_conflicts`.
