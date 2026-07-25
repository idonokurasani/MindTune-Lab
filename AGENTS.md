# Agent Notes — MindTune Console Hebrew Audio Pipeline

## Lint / Type / Test commands

```bash
.venv/bin/ruff check <path>
.venv/bin/mypy --exclude 'hebrew/' <path>
PYTHONPATH=/Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console .venv/bin/python -m unittest tests.test_shared_assets tests.test_mantra_engine tests.test_frontend_contracts
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

- Hebrew voice: Hannah, fully vocalized (niqqud); `source_text == tts_text`.
- Italian infinitive introduction only, once per compact mantra.
- No Italian grammatical labels inside the mantra.
- Merge identical masculine/feminine plural forms with `וְ`.
- Domino tense markers are global reusable assets (`he.tense.past`, `he.tense.present`, `he.tense.future`).
- No narrative temporal expressions in Domino prompts.
