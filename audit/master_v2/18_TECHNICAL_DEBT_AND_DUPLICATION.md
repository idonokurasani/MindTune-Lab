# 18 — Technical Debt and Duplication

## 1. Duplication

| Duplicate / Copy | Locations | Disposition |
|---|---|---|
| Console backups | `mindtune_console/`, `mindtune_console_BACKUP_BEFORE_GITHUB_CLEANUP/`, `mindtune_eeg_github_recovery/`, `mindtune_rescue/` | ARCHIVE / DISCARD |
| App bundles | `MindTune Lab.app/`, `mindtune_archives/`, `tmp/` | Keep latest, archive rest |
| Citizen Café data | `data/citizen_cafe_all_courses/` in multiple copies | DISCARD (replaced by HeLP) |
| Hebrew resources | `data/hebrew/resources/` vs `data/hebrew_resources/vendor/Hebrew-Resources/` | CONSOLIDATE / clarify separation |
| TTS repos | `repos/BlueTTS/`, `repos/HebTTS/`, `mantra/piper_adapter.py` | ARCHIVE / DISCARD |
| Generated caches | `.pnpm-store/`, `__pycache__`, `.mypy_cache`, `.pytest_cache`, `.ruff_cache` | DISCARD |

## 2. Technical Debt

- `server.py` is a 3,796-line monolith.
- `app.js` is a 6,896-line monolith with no tests.
- `mpe` uses dataclasses with manual validation; Pydantic is not used despite `pyproject.toml` depending on it.
- MPE `EventStore` only has an in-memory default; persistent SQLite backend is in `persistence/` experiments.
- Raspberry Pi bridge directories referenced but not present.
- `/mnt/biohacking` mount path not resolved.
- mypy errors in `test_hebrew_domain.py` (test-side).

## 3. Dead Code

- `azure_speech.py` references (legacy, guarded by `test_forbidden_legacy_sources.py`).
- `repos/BlueTTS/`, `repos/HebTTS/`, `mantra/piper_adapter.py` (not integrated).
- `mindtune_eeg_github_recovery/recovered/` older copies of current code.

## 4. Disposition

- Cleanup → **ARCHIVE** backup copies and **DISCARD** caches/legacy TTS repos.
- Monoliths → **REWRITE** in V2 with clean package boundaries.
