# 23 — Migration and Archive Plan

## Migrate to V2

- `packages/mpe/src/mpe/` → `packages/mpe/` (core).
- `packages/mpe/src/mpe/domains/hebrew/` → `mpe-adapters/hebrew/`.
- `hebrew/` → `mpe-adapters/hebrew/linguistic/` or separate package.
- `mantra/phase1/` → `mpe-adapters/hebrew/audio/` renderer.
- `mindtune_capture/` → `mpe-sensors/fc11/`, `mpe-sensors/lsl/`, `mpe-sensors/scientific/`.
- `oura_api.py` → `mpe-sensors/oura/`.
- `help_profiler.py` → `mpe-adapters/hebrew/help/profiler.py`.
- `brainlab_protocols/` → V2 `data/protocols/`.
- `tests/` and `packages/mpe/tests/` → V2 `tests/`.

## Archive

- `mindtune_console_BACKUP_BEFORE_GITHUB_CLEANUP/`
- `mindtune_eeg_github_recovery/`
- `mindtune_rescue/`
- `FOCUSCALM_ZAI_AUDIT_PACKET_2026-07-19/` (after extracting key findings to a smaller artifact)
- `mindtune_archives/` (keep latest `MindTune Lab.app`)
- `tmp/`
- `forensic_audit_20260618_025114/`
- `devin_handoffs/`
- `firmware_analysis/`
- `repos/BlueTTS/`, `repos/HebTTS/`, `mantra/piper_adapter.py`

## Discard

- `.pnpm-store/`
- `__pycache__`, `.mypy_cache`, `.pytest_cache`, `.ruff_cache`
- Duplicate `data/citizen_cafe_all_courses/` copies
- `azure_speech.py` references

## Risk: Credentials in Backup Copies

Before archiving or discarding backup/recovery directories, scan them for `client_secret`, `api_key`, `.oura_credentials`, and `.oura_token`. Purge or rotate any secrets found, or treat copies as confidential waste.
