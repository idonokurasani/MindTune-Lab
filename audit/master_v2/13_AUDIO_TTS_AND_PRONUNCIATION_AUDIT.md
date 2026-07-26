# 13 — Audio, TTS, and Pronunciation Audit

## 1. Mantra Phase 1 Engine (`mantra/phase1/`)

| Module | Purpose | Status |
|---|---|---|
| `spec.py` | `MantraSpecification`, `MantraForm`, `SpeechConfig` | Production |
| `timeline.py` | Segment-based deterministic timeline with UUIDv5 IDs | Production |
| `assembly.py` | WAV concatenation, resampling, silence insertion | Production |
| `playback.py` | `PlaybackController`, segment-aware events | Production |
| `tts.py` | `SpeechGenTTSProvider`, `TTSCache`, deterministic cache keys | Production |
| `assets.py` | `AudioAssetRegistry`, global shared assets | Production |
| `curriculum.py` | 320-verb `Curriculum` + `MantraSelectionPolicy` | Production |
| `sheva.py` / `pronunciation.py` | Sheva classification and pronunciation lexicon | Production |

## 2. TTS Providers

| Provider | Location | Status | Notes |
|---|---|---|---|
| SpeechGen | `mantra/phase1/tts.py` | Production | Requires `SPEECHGEN_API_KEY` and `SPEECHGEN_EMAIL` (`AGENTS.md:22-24`) |
| Piper | `mantra/piper_adapter.py` | Prototype, unused | ARCHIVE candidate |
| BlueTTS | `repos/BlueTTS/` | Prototype, unused | ARCHIVE candidate |
| HebTTS | `repos/HebTTS/` | Research, unused | ARCHIVE candidate |

## 3. Output / Cache

- `output/mantra_global_tts_cache/` — deterministic WAV cache.
- `output/mantra_audio_assets.json` — stable asset registry.
- `data/mantra/audio/` — pre-generated MP3/WAV assets.

## 4. Audio Design Rules

From `AGENTS.md:47-54`:

- Hebrew voice resolved by `AudioProfile` (production: Aaron, `he-IL`).
- Pointed `source_text` and unpointed `tts_text` explicitly stored.
- Italian infinitive introduction only, once per compact mantra.
- No Italian grammatical labels inside the mantra.
- Merge identical masculine/feminine plural forms with `וְ`.
- Domino tense markers are global reusable assets.

## 5. Disposition

- `mantra/phase1/` → **KEEP** (mature deterministic audio pipeline).
- `mantra/piper_adapter.py`, `repos/BlueTTS/`, `repos/HebTTS/` → **ARCHIVE**.
- SpeechGen TTS → **MIGRATE** (decouple with a provider-agnostic TTS adapter boundary; support offline cache-only mode).
