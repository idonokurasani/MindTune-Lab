# Mantra dataset schema

Two file families are produced for every verb:

1. `data/mantra/verbs_master.json` — one canonical master record per verb.
2. `data/mantra/scripts/###_key.json` — per-verb display / spoken / TTS script.
3. `data/mantra/ssml/###_key.xml` — Azure Speech SSML input for audio generation.
4. `data/mantra/audio/###_key.mp3` — resulting audio.

## `verbs_master.json` entry

| Field | Type | Meaning |
|-------|------|---------|
| `order` | int | 1-based position in the 100-verb sequence |
| `infinitive_hebrew_with_niqqud` | string | Vowelled infinitive for TTS / display |
| `infinitive_hebrew_without_niqqud` | string | Same, vowel marks removed |
| `infinitive_transliteration` | string | Lowercase Italian-friendly transliteration |
| `italian_translation` | string | Italian infinitive / meaning |
| `root` | string | Three-letter root (e.g. `כ-ת-ב`) |
| `binyan` | string | Binyan: `PA'AL`, `PI'EL`, `HIF'IL`, `HITPA'EL`, `NIF'AL`, `PU'AL`, `HUF'AL` |
| `source_url` | string | Pealim dict URL used for verification |
| `source_checked_date` | string | ISO date of verification |
| `source_notes` | string | Any linguistic caveats |
| `example_*` | string | Hebrew with/without niqqud, transliteration, Italian |
| `present` / `past` / `future` | object | Conjugation table keyed by form |
| `stress_metadata` | object | Stress-pattern notes |
| `pronunciation_verification_status` | string | `verified_from_pealim` / `pending` |
| `content_verification_status` | string | `verified` / `pending` |

### Form object

```json
{
  "hebrew_with_niqqud": "כּוֹתֵב",
  "hebrew_without_niqqud": "כותב",
  "display_transliteration": "kotev",
  "tts_input": "כּוֹתֵב",
  "stress_syllable_index": 1,
  "italian_gloss": "io scrivo"
}
```

- `display_transliteration` is for on-screen display. It is **not** used as SSML text.
- `tts_input` is Hebrew with niqqud and is the text passed to Azure TTS.
- `stress_syllable_index` is the 1-based syllable that carries primary lexical stress.

## Per-verb script JSON

```json
{
  "order": 1,
  "verb_key": "lichtov",
  "hebrew_infinitive": "לִכְתֹּב",
  "italian_infinitive": "scrivere",
  "root": "כ-ת-ב",
  "binyan": "PA'AL",
  "source_url": "https://www.pealim.com/dict/1-lichtov/",
  "sections": [ ... ],
  "spoken_script": "LICHTOV.\nSCRIVERE.\n...",
  "display_script": "...",
  "hebrew_script": "...",
  "italian_script": "...",
  "transliteration": "...",
  "pauses_ms": { "between_forms": 500, "between_sections": 900, "after_example": 700 },
  "speaking_rate": "-15%",
  "ssml_path": "data/mantra/ssml/001_lichtov.xml"
}
```

`sections` contains one entry per tense (`infinitive`, `present`, `past`, `future`).
Each `lines` entry has the same fields as the master form object plus `form_key`.

## SSML

SSML files use `he-IL-AvriNeural` with `<prosody rate="-15%">`. Italian words are wrapped in `<lang xml:lang="it-IT">` so the Azure voice switches language for the translation. Breaks between forms and sections are taken from the script's `pauses_ms`.
