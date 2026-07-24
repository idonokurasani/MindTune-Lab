# Mantra content dataset — Phase 1

This directory contains the curated Modern Hebrew verb dataset for the MindTune Lab Mantra section.

## Files

- `verbs_master.json` — canonical full records (currently verbs 1–3, verified).
- `scripts/001_*.json` — per-verb spoken/display/Hebrew/Italian scripts with section timing.
- `ssml/001_*.xml` — Azure Speech SSML inputs.
- `audio/001_*.mp3` — generated audio (produced by `scripts/generate_mantra_audio.py`).
- `VERBS_100_PLAN.md` — proposed ordered list of 100 verbs with selection rationale.
- `MANTRA_CONTENT_AUDIT.csv` — QA audit for all 100 verbs (3 complete, 97 planned).
- `UNCERTAINTIES.md` — documented open linguistic decisions.

## Schema notes

- `display_transliteration` is lowercase and Italian-friendly; stress is in `stress_syllable_index`.
- `tts_input` is Hebrew with niqqud and is used in Azure SSML, not the transliteration.
- Feminine plural future forms follow ordinary modern usage (masculine plural form).

## Audio generation

Run `python3 scripts/generate_mantra_audio.py` after exporting the Azure Speech key and region.
