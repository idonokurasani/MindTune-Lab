# Hebrew Source Cleanup Report

## Summary

All legacy Hebrew content sources — Citizen Café, Streetwise Hebrew, and the
quizlet seed pipeline that carried them — have been removed from the active
MindTune Lab codebase.  Azure Speech is no longer reachable from Hebrew audio
flows; the runtime now relies on SpeechGen for TTS.

## Sources removed

### Commercial / non-canonical content

- `data/citizen_cafe_all_courses/` — complete Citizen Café extract and derived
  drafts.
- `data/citizen_cafe_consolidation/` — consolidation reports, scores and
  reconstruction protocol.
- `data/hebrew_enrichment/streetwise_hebrew/` — Streetwise Hebrew enrichment
  candidates, matches, raw RSS and import manifests.
- `data/quizlet_hebrew_seed*.json`, `data/quizlet_hebrew_audit*.csv`,
  `data/quizlet_pdf_raw/*`, `data/blue_purple_translation_patch_*` — all
  quizlet-derived seed artifacts that bundled the legacy sources.

### Build / import scripts

- `scripts/build_citizen_cafe_all_courses.py`
- `scripts/consolidate_citizen_cafe_corpus.py`
- `scripts/export_citizen_cafe_review_package.py`
- `scripts/import_streetwise_enrichment.py`
- `tests/test_azure_speech.py`

### Documentation drafts

- `docs/ADVANCED_HEBREW_PERSONALIZED_COURSE_PLAN_v0.1.md`
- `docs/MINDTUNE_HEBREW_AND_PIANO_MASTER_COURSE_v0.1.md`
- `docs/MINDTUNE_LAB_BUILD_NOTES_2026-07-15.md`
- `data/DOCKER_HEBREW_REVIEW_AUDIT_2026-07-03.md`
- `data/HEBREW_DATABASE_REVIEW_DOCUMENTATION.md`
- `REPOSITORY_RECOVERY_REPORT.md`

## Runtime changes

- `server.py`: removed legacy flashcard seed import, migration, enrichment and
  API endpoints.  The source registry endpoint now silently drops unknown or
  legacy source IDs instead of surfacing them.
- `app.js`: removed the Streetwise enrichment panel, event logging and
  exposure tracking.  Removed the Azure Speech conjugation speech-to-text
  capture path; the speak button is now a no-op stub.
- `index.html`: removed the Streetwise panel markup.
- `pyproject.toml`: removed ruff per-file ignores for deleted files.
- `tests/test_hebrew_recovery.py`: updated assertions to expect HeLP as the
  operational psycholinguistic source and verified legacy IDs are dropped.
- `tests/test_help_profiler.py`: replaced the Azure Speech transcription
  provider in the fixture with `speechgen`.

## Regression safeguards

`tests/test_forbidden_legacy_sources.py` now scans the repository for
Citizen Café, Streetwise Hebrew and Azure Speech references.  It ignores
historical audit/README files that legitimately cite the old names, but any
active runtime or data reference will fail the test.

## Verification

```bash
PYTHONPATH=/Users/idonokurasani/Documents/Chatgpt/Biohacking/mindtune_console .venv/bin/python -m unittest tests.test_forbidden_legacy_sources
```

Result: pass.

## Known remaining notes

Historical reports under `docs/audits/`, `docs/project/`,
`docs/implementation/phase4b1/`, `data/mantra/` and `data/phonikud_eval/`
still mention Azure Speech for provenance.  These are documentation, not code
or runtime dependencies, and are excluded from the regression scan.
