# 10 — Sensor and EEG Pipeline Audit

## 1. Oura Integration

- `mindtune_console/oura_api.py` — full OAuth2 flow with localhost callback on port 8765.
- Stores tokens in `.oura_token` and credentials in `.oura_credentials`.
- Fetches sleep, readiness, activity, stress data from Oura API v2.
- **Security issue:** `.oura_credentials` at `/Users/idonokurasani/Documents/Chatgpt/Biohacking/.oura_credentials` contains a live `client_secret`.

## 2. FC11 EEG Capture (`mindtune_capture/`)

| Module | Purpose | Status |
|---|---|---|
| `fc11_mac_capture.py` | BLE protocol for BrainCo/FocusCalm FC11 helmet | Production, macOS-only |
| `fc11_capture_pipeline.py` | Async bounded queues, raw CSV writers, optional feature consumer | Production |
| `lsl_bridge.py` | LSL outlet `MindTune_FC11_EEG` 1ch @ 250Hz + markers | Production (optional) |
| `scientific_qc.py` | Window-level QC (MAD, clipping, 50Hz line, abrupt jumps) | Production |
| `scientific_spectral.py` | Hann periodogram, delta/theta/alpha/beta/gamma bands | Production |
| `scientific_longitudinal.py` | Session-level alpha reactivity, Cohen's d | Production |

## 3. EEG Provider in MPE

- `mpe/protocol/eeg_provider.py` — `MockEEGProvider` driven by fixture `eeg_load` and `eeg_quality_flags`.
- No real EEG provider is wired into `mpe` yet.
- `ImmediateRecallRunner` calls `_poll_eeg()` if `providers.eeg` is present.

## 4. Withings / Libre / HRV

- **Withings:** no implementation found.
- **Libre3:** only remote diagnostic scripts in `tools/remote_diagnose_libre3.py` and `remote_fix_libre3_grafana_units_time.py`.
- **HRV:** computed as part of `scientific_spectral.py` band powers and Oura readiness.

## 5. Raspberry Pi Bridge

- `server.py` references `BRIDGE`, `INBOX`, `RUNNING`, `DONE`, `FAILED`, `LOGS` directories for an RPi bridge.
- `.raspberry_bridge/` is missing; `pi_mnt/` is empty.
- Server-side Pi integration is incomplete.

## 6. Disposition

- `mindtune_capture/` → **KEEP / MIGRATE** (abstract BLE for cross-platform V2).
- `oura_api.py` → **KEEP / MIGRATE** (rotate secret, encrypt tokens).
- `mpe/protocol/eeg_provider.py` → **MIGRATE** (extend with real EEG adapter).
- Withings / Libre → **DISCARD or ARCHIVE** current fragments, implement proper adapters in V2 if needed.
