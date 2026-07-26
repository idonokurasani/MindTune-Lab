# 11 — FocusCalm Reverse-Engineering Audit

## 1. Artifact Location

`/Users/idonokurasani/Documents/Chatgpt/Biohacking/FOCUSCALM_ZAI_AUDIT_PACKET_2026-07-19/`

## 2. Contents

- `reconstruct_attention_features.py` — 169 FFT magnitudes for 4–38 Hz.
- `reconstruct_meditation_features.py` — 33 features (time moments, frequency bands, deciles).
- `run_fusi_network.py` — Neural network execution.
- `focuscalm_smoothing.py` — Moving-average smoothing.
- Models: `attention.pb`, `meditation.pb`, `attention_network.json`, `meditation_network.json`, `meditation_normalization.json`.
- Real EEG capture: `fc11_stream_1781471387_eeg.csv`.
- `evidence/FOCUSCALM_REVERSE_ENGINEERING_REPORT.md`.

## 3. Native Parity Findings

- Target library: `libfusi.so` (ARM64, FocusCalm Android 3.1.0).
- EEG window: 800 samples.
- Sampling rate: 160.6 Hz.
- Attention input: 169 FFT magnitudes (bins 20–188, 4–38 Hz).
- Meditation input: 33 normalized features.
- FFT scaling: `1/N` (not `2/N`).
- Attention network: 169 → 70 → 30 → 3.
- Meditation network: 33 → 70 → 30 → 2.

## 4. Critical Gap

The exact transformation from BLE packet samples to the units written into the native 800-sample analysis buffer has **not** been demonstrated end-to-end. Therefore, native parity of the score outputs cannot be asserted for live data.

## 5. Test Coverage

- `test_attention_pipeline.py`
- `test_meditation_pipeline.py`
- `test_real_focuscalm_meditation.py`

## 6. Disposition

**ARCHIVE** — The packet is valuable research evidence. Extract the verified constants and model architecture into a V2 artifact, then archive the original directory to cold storage.
