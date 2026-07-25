# Agent Notes — MindTune Console Hebrew Audio Pipeline

## Lint / Type / Test commands

```bash
.venv/bin/ruff check <path>
.venv/bin/mypy --exclude 'hebrew/' <path>
PYTHONPATH=/Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console .venv/bin/python -m unittest tests.test_shared_assets tests.test_mantra_engine tests.test_frontend_contracts tests.test_phase4d tests.test_curriculum_policy

Full suite (requires `phonikud`, use `.venv_phonikud` on Python 3.12 or install `pip install -e ".[hebrew]"`):

```bash
PYTHONPATH=/Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console .venv_phonikud/bin/python -m unittest discover -s tests -p 'test_*.py'
```
```

## SpeechGen credentials

Both builders require:

```bash
export SPEECHGEN_API_KEY="..."
export SPEECHGEN_EMAIL="..."
```

## Build commands

Full-niqqud diagnostic package for a verb:

```bash
PYTHONPATH=/Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console .venv/bin/python scripts/build_lehitkasher_hannah_full_niqqud.py
```

Compact mantra + shared assets + Domino exercises for לְהִתְקַשֵּׁר:

```bash
PYTHONPATH=/Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console .venv/bin/python scripts/build_compact_mantra_lehitkasher.py
```

## Output paths

- Full diagnostic: `output/mantra_phase1_lehitkasher_hannah_full_niqqud/`
- Compact mantra: `output/mantra_phase1_lehitkasher_hannah_full_niqqud/compact_mantra.wav`
- Shared audio asset registry: `output/mantra_audio_assets.json`
- Global TTS cache: `output/mantra_global_tts_cache/`

## Audio design rules

- Hebrew voice resolved by `AudioProfile` (production profile: Aaron, `he-IL`); linguistic specifications store pointed `source_text` and explicit unpointed `tts_text`.
- Italian infinitive introduction only, once per compact mantra.
- No Italian grammatical labels inside the mantra.
- Merge identical masculine/feminine plural forms with `וְ`.
- Domino tense markers are global reusable assets (`he.tense.past`, `he.tense.present`, `he.tense.future`).
- No narrative temporal expressions in Domino prompts.

## Curriculum and selection

- Generate/regenerate the 320-verb canonical curriculum:

  ```bash
  PYTHONPATH=/Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console .venv/bin/python scripts/generate_curriculum_320.py
  ```

- Curriculum JSON: `data/hebrew/curriculum_v1_320.json`
- Selection policy: `mantra/phase1/curriculum.py` (`MantraSelectionPolicy`)
- Policy tests: `tests/test_curriculum_policy.py`

The policy is deterministic, never calls TTS, never reads EEG, and filters to
verbs whose required audio assets exist unless `asset_preparation_mode=True`.
