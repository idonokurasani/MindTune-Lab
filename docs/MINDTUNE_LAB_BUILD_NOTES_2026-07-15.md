# MindTune Lab build notes - 2026-07-15

Version: 3.19.0
Build: 20260715.5

## Purpose

First rebuild toward the guided MindTune Lab model:

- the opening screen now asks what to do today;
- the opening screen now asks session duration;
- Oura daily state is summarized into an operational day mode;
- FC11 readiness gates the guided launch button;
- Piano Lab is reduced to five scientifically interpretable activities:
  - sight-reading;
  - playing with score;
  - playing without score;
  - listening;
  - known-music imagery;
- the app now contains the master Hebrew/Piano course design document.
- Streetwise Hebrew enrichment is queried locally by canonical Citizen Cafe ID;
- short real-use excerpts and episode audio appear only after recall;
- enrichment exposure and audio use are linked to flashcard and EEG events;
- Streetwise evidence remains separate from the canonical Hebrew corpus.
- HeLP lexical norms are exposed only as stimulus-level evidence after recall;
- the personal HeLP profiler is rebuilt read-only from flashcard, conjugation, Shoresh and MLF events;
- adaptive flashcard priorities remain disabled until the minimum evidence gate is met;
- HeLP model, dataset release and item-match lineage are stored with recall events.

## Files touched

- `mindtune_console/index.html`
- `mindtune_console/app.js`
- `mindtune_console/styles.css`
- `mindtune_console/help_profiler.py`
- `mindtune_console/tests/test_help_profiler.py`
- `mindtune_native/MindTuneNative.m`
- `MindTune Lab.app/Contents/Info.plist`
- `MindTune Lab.app/Contents/MacOS/MindTuneLab`
- `tools/audit_mindtune_local_privacy.py`
- `mindtune_console/docs/MINDTUNE_HEBREW_AND_PIANO_MASTER_COURSE_v0.1.md`

## Verification

- Python syntax: passed for server/Oura/import/consolidation scripts.
- HTML parse: passed.
- JavaScript syntax: passed via macOS JavaScript engine.
- HeLP profiler unit tests: passed (exact matching, evidence gate, deterministic score-correction lineage).
- Native wrapper: compiled with Cocoa/WebKit.
- App signature: valid after local signing.

## Known limitation of this Codex sandbox

The local HTTP smoke test could not be run from inside the sandbox because binding a local port returned `PermissionError: Operation not permitted`. This is a sandbox limitation, not a server syntax failure.

## Privacy audit note

The privacy audit no longer reports false telemetry markers from `previousEntry` or `thread_id`.

Remaining audit findings are expected external references:

- Oura API endpoints;
- Pealim source references;
- Academy/Streetwise/CEFR documentation URLs.
