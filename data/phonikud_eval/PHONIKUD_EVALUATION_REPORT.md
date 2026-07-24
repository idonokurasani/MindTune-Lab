# Phonikud / Renikud Pronunciation Evaluation Report

## Scope

Three Modern Hebrew verbs were evaluated as a proof-of-concept for replacing or augmenting the MindTune Lab Azure TTS pipeline:

- `לִכְתֹּב` (to write)
- `לִהְיוֹת` (to be)
- `לַעֲשׂוֹת` (to do)

For each verb, Pealim was used as the pronunciation authority. All required conjugated forms were extracted with full niqqud and stress markers. The Phonikud and Renikud G2P systems were run over these forms, stress and vocal shva were identified, mismatches were flagged, and a manual phoneme override was produced for every incorrect form.

Three audio samples were also generated with `phonikud-tts` (one per infinitive) and compared with Azure TTS (plain and vocalized Hebrew input) and Mic Hebrew-TTS.

## Files Produced

- `data/phonikud_eval/pealim_forms.json` — raw Pealim extraction with niqqud and transcriptions.
- `data/phonikud_eval/phonikud_evaluation.csv` — per-form audit table (62 rows).
- `data/phonikud_eval/phonikud_evaluation.json` — machine-readable audit data.
- `data/phonikud_eval/audio/` — comparison audio files.
  - `azure_plain_*.mp3`
  - `azure_vocalized_*.mp3`
  - `phonikud_tts_*.mp3`
  - `mic_hebrew_tts_*.mp3`
- This report.

## G2P Accuracy Summary

| Metric | Phonikud (raw) | Phonikud (after manual override) | Renikud (raw) |
|--------|----------------|----------------------------------|---------------|
| Vowel-sequence accuracy vs. Pealim | 59 / 62 (95.2%) | 62 / 62 (100%) | 47 / 62 (75.8%) |
| Stress accuracy vs. Pealim | 49 / 62 (79.0%) | 62 / 62 (100%) | 49 / 62 (79.0%) |
| Forms needing manual override | 13 / 62 (21.0%) | 0 | 13 / 62 used for cross-check |

Phonikud’s raw vowel quality is excellent because it is fed the Pealim-vocalized forms. Its main weaknesses on this sample were:

- Moving lexical stress onto the pronominal suffix in suffixed past forms (`katavti`, `hayiti`, `asiti`, etc.).
- Dropping the vocal shva / epenthetic `e` in future geminate-consonant forms (`tichtevi`, `tichtevu`, `yichtevu`).

Renikud was stronger at stress and vocal-shva placement in some of those cases, but frequently misread vowel quality when given unvocalized input (`lektav` for `lichtov`, `katˈeveta` for `katavta`, `ʔosˈa` for `osˈe`). It is therefore not reliable as the sole G2P layer for unvocalized text.

## Forms Requiring Manual Override

All 13 corrected forms (from `phonikud_evaluation.csv`):

| Verb | Form | Pealim transliteration | Raw Phonikud | Manual override | Reason |
|------|------|------------------------|--------------|-----------------|--------|
| לכתוב | present_feminine_singular | kotevet | `kotevˈet` | `kotˈevet` | stress shift |
| לכתוב | past_1_singular | katavti | `katavtˈi` | `katˈavti` | stress shift |
| לכתוב | past_2_masculine_singular | katavta | `katavtˈa` | `katˈavta` | stress shift |
| לכתוב | past_1_plural | katavnu | `katavnˈu` | `katˈavnu` | stress shift |
| לכתוב | future_2_feminine_singular | tichtevi | `tiχtvˈi` | `tiχtevˈi` | missing vocal shva `e` |
| לכתוב | future_2_plural | tichtevu | `tiχtvˈu` | `tiχtevˈu` | missing vocal shva `e` |
| לכתוב | future_3_plural | yichtevu | `jiχtvˈu` | `jiχtevˈu` | missing vocal shva `e` |
| להיות | past_1_singular | hayiti | `hajitˈi` | `hajˈiti` | stress shift |
| להיות | past_2_masculine_singular | hayita | `hajitˈa` | `hajˈita` | stress shift |
| להיות | past_1_plural | hayinu | `hajinˈu` | `hajˈinu` | stress shift |
| לעשות | past_1_singular | asiti | `ʔasitˈi` | `ʔasˈiti` | stress shift |
| לעשות | past_2_masculine_singular | asita | `ʔasitˈa` | `ʔasˈita` | stress shift |
| לעשות | past_1_plural | asinu | `ʔasinˈu` | `ʔasˈinu` | stress shift |

After override, all 62 rows match Pealim stress and vowel patterns.

## Audio Comparison (three infinitives)

| Engine | Input | Notes |
|--------|-------|-------|
| Azure plain | `לכתוב` / `להיות` / `לעשות` (unvocalized) | Generated with `he-IL-HilaNeural`. Fast, natural voice; stress and vowel behavior is the Azure default. |
| Azure vocalized | `לִכְתֹּב` / `לִהְיוֹת` / `לַעֲשׂוֹת` | Same voice, niqqud supplied. Azure does not fully use Hebrew diacritics for stress control. |
| phonikud-tts | Manual-override phonemes (`liχtˈov`, `lihjˈot`, `laʔasˈot`) | Local Piper-based synthesis. Very fast, offline, deterministic stress; voice is small and less natural than Azure. |
| Mic Hebrew-TTS | `לכתוב` / `להיות` / `לעשות` | Web trial endpoint (`/api/tts/trial-direct`). Returned MP3; quality is good but the service is rate-limited and has no public API at this tier. |

Generated files are in `data/phonikud_eval/audio/`.

## Comparison Dimensions

| Dimension | Azure (plain) | Azure (vocalized) | phonikud-tts | Mic Hebrew-TTS |
|-----------|---------------|-------------------|--------------|----------------|
| Pronunciation accuracy | Baseline; cannot be driven by IPA or precise stress | Slightly better with niqqud, but still no explicit stress/phoneme control | High when fed corrected phonemes; every phoneme is explicit | High for the supplied text; internal model adds its own diacritics |
| Stress accuracy | Controlled by Azure’s internal G2P only | Same as plain; diacritics are not enough | Exact, because stress mark is in the phoneme string | Internal stress model; not externally controllable |
| Vocal shva handling | Hidden / not controllable | Hidden / not controllable | Requires manual override for some geminate forms | Handled internally; results vary |
| Naturalness | High (neural voice) | High | Low-to-moderate (small Piper voice) | Moderate-to-high |
| Voice quality | High | High | Functional, somewhat robotic | Good |
| Speed control | SSML `prosody` rate/pitch | Same as plain | Piper `length_scale` (local, continuous) | No speed control in trial endpoint |
| Latency | Network round-trip | Network round-trip | Local, real-time | Network round-trip |
| Offline feasibility | No | No | Yes, after model download (~80 MB total) | No |
| Licensing | Azure Speech subscription / standard Microsoft terms | Same | Phonikud/Renikud code CC BY 4.0 / MIT; **TTS voice `shaul.onnx` is `cc-nc` (non-commercial)** | Unknown / no public API; commercial use unclear |
| Maintainability | High (managed service) | High | Moderate — requires per-form G2P verification and a stress/vocal-shva correction layer | Low — no API, web-only, rate limits |

## Licensing and Feasibility Notes

- **Phonikud** code and ONNX diacritization model: permissive (MIT/CC BY 4.0).
- **Renikud** code and ONNX model: CC BY 4.0.
- **Piper ONNX runtime**: MIT.
- **phonikud-tts `shaul.onnx` voice**: explicitly non-commercial (`cc-nc`). A different, commercially licensed Piper voice would be needed for a commercial product.
- All three local models together require ~80 MB of disk space and run in real time on CPU.

## Recommended Production Pipeline

A hybrid pipeline gives the best of both worlds:

1. **G2P layer**: Use `phonikud` (with Pealim/verified vocalized Hebrew as input) for vowel quality and consonant accuracy.
2. **Stress / vocal-shva correction**: Apply a small rule-based or Renikud-assisted checker that flags forms where Phonikud stress deviates from the Pealim stress index or drops an epenthetic `e`. The 62-form test suggests ~20% of forms need such an override.
3. **TTS synthesis**: Feed the corrected IPA phonemes to a Piper-based TTS engine for deterministic, local, offline playback.
4. **Cloud fallback**: Keep Azure for natural-sounding output when network is available and correctness is not critical, or use Azure only for preview/fallback while the local phoneme-driven pipeline is the canonical source.

This approach yields **deterministic pronunciation** (stress, vowels, consonants, vocal shva under explicit control) while remaining local and low-latency.

## Stop Condition

Evaluation was limited to the three requested verbs. No integration into MindTune Lab has been performed, and no global changes were made to the application. Audio samples are available for listening and approval before any pipeline switch.
