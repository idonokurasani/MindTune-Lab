# 16 — Test Coverage and Quality Audit

## 1. Test Inventory

### `mindtune_console/tests/` (21 files)

- `test_audio_profile.py`
- `test_behavioral_event_store.py`
- `test_curriculum_identity.py`
- `test_curriculum_policy.py`
- `test_forbidden_legacy_sources.py`
- `test_frontend_contracts.py`
- `test_hebrew_engine.py`
- `test_hebrew_recovery.py`
- `test_hebrew_vendor_resources.py`
- `test_help_profiler.py`
- `test_mantra_engine.py`
- `test_native_bundle_contracts.py`
- `test_orthography.py`
- `test_phase3_validation.py`
- `test_phase4d.py`
- `test_phonology.py`
- `test_repository_integrity.py`
- `test_shared_assets.py`
- `test_shared_assets_and_domino.py`

### `packages/mpe/tests/` (22 files)

- `test_cli.py`
- `test_enums.py`
- `test_event_store.py`
- `test_hebrew_domain.py`
- `test_help_integration.py`
- `test_identifiers.py`
- `test_invariants.py`
- `test_protocol_immediate_recall.py`
- `test_protocol_recognition.py`
- `test_providers.py`
- `test_reference_flow.py`
- `test_replay.py`
- `test_shared_extraction.py`
- `test_state_machines.py`
- `persistence/*`

### `mindtune_capture/tests/` (6 files)

- `test_fc11_capture_pipeline.py`
- `test_lsl_bridge.py`
- `test_scientific_qc.py`
- `test_scientific_spectral.py`
- `test_scientific_longitudinal.py`
- `test_session_labeling.py`

## 2. Latest Results

- `test_forbidden_legacy_sources`: 4 tests passed.
- Selected policy/audio/contract suites: 75 tests passed.
- `packages/mpe/tests` discovery: 224 tests passed.
- `test_hebrew_recovery` + `test_help_profiler`: 10 tests passed.
- **Total: 313 tests passed** (reported in read-only audit notes).

## 3. Static Analysis

- **Ruff:** passed.
- **mypy:** 31 errors in `test_hebrew_domain.py` due to test-side type precision, not runtime defects.

## 4. Disposition

**KEEP** — Test infrastructure is strong. V2 should migrate the test pyramid to the new repo and add frontend/API tests.
