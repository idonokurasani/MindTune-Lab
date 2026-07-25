# FocusCalm EEG Pipeline — Reverse-Engineering Report

**Target:** `libfusi.so` (FocusCalm v3.1.0, ARM64)  
**Goal:** decode how 800-sample EEG windows are turned into attention/meditation scores, and verify the equivalent Python reconstruction.

---

## 1. High-level flow

`analyze_eeg` (`0x15a30`) is called each time a window of EEG data is ready. Its path is:

1. Copy the 800 most-recent samples from `this+0x80` into the FFT buffer `this+0x88`.
2. `fft_forward` (`0x28214`) — real FFT with optional `1/N` scaling. The plan used by the app has the scale flag set, so the forward output is divided by `N = 800`.
3. `analyze_eeg_windows` (`0x153b8`) computes magnitude `sqrt(re^2 + im^2)` for each frequency bin and stores the result in `this+0x90`.
4. If the timing flags say so, call:
   - `compute_attention_features` (`0x434e0`) → `this+0xa0`
   - `analyze_eeg_attention` (`0x43830`) uses the attention network (`this+0x138`) and the 169 features at `this+0xa0`, then smooths the result.
   - `compute_meditation_features` (`0x43530`) → `this+0xa8`
   - `analyze_eeg_meditation` (`0x43aa0`) uses the meditation network (`this+0x140`) and the 33 features at `this+0xa8`, then smooths the result.

The networks are embedded protobuf NN models extracted as `attention_network.json` and `meditation_network.json`.

---

## 2. Constants verified in `libfusi.so`

| Symbol | Address | Value | Usage |
|--------|---------|-------|-------|
| Sampling rate (`fs`) | `0x433e8` / `0x4064133333333333` | **160.6 Hz** | frequency-to-bin mapping |
| Window size (`N`) | `0x433e4` / `0x320` | **800 samples** | FFT length; also divide factor for FFT magnitude |
| Clip low | `0x43554` / `0xc09f4000...` | **-2000.0** | `clip()` in `compute_meditation_features` |
| Clip high | `0x43540` / `0x409f4000...` | **2000.0** | `clip()` in `compute_meditation_features` |
| Meditation band size | `0x43558` / `0x28` | **40 bins** | five contiguous FFT bands |
| Meditation last bin | `0x4355c` / `0xc7` | **199** (inclusive) → 200 bins used | `get_frequency_band_moments` |
| Attention start/end | `0x434ec`/`0x434f0` | **5 / 189** | `get_frequency_magnitude` arguments |

The FFT forward path explicitly divides every output element by the FFT size when the plan flag is `1` (see `fft_forward` `0x28258`–`0x282bc`), matching the Python `np.fft.rfft(...) / 800.0` scaling.

---

## 3. BLE payload → EEG sample decoding

`parse_content` (`0x16574`) is the BLE payload entry point. It validates the packet footer (`b'PKED'`) and then walks a sequence of TLV chunks:

```
[type: 2 bytes BE][length: 2 bytes BE][payload: length bytes]
...
footer: b'PKED' (0x50 0x4b 0x45 0x44)
```

The EEG chunk has type `0x4547` (big-endian characters "EG").  Its payload is a sequence of 3-byte, big-endian, **signed** 24-bit integers:

```python
raw24 = (b0 << 16) | (b1 << 8) | b2
if raw24 & 0x800000:
    raw24 |= 0xff000000       # sign-extend to 32 bits
```

The integer is then converted to the double stored in the per-packet sample buffer (`this+0x70`):

```python
sample = raw24 * 0.040690104166666664 / 128.0
```

- `0.040690104166666664` is the double at `.rodata` offset `0x75b30` (loaded by `ldr d3, [x10, #0xb30]` at `0x16920`).
- `128.0` is the value loaded from `this+0x10` (initialised to `0x80` in `device_data_create`).

A different chunk (probably accelerometer/gyro) uses the constant `0.244140625` at `0x75b38` (`0x16b14`) and divides by `0.5` and by a per-chunk length; it is not part of the EEG score pipeline.

`focuscalm_sample_decoder.py` reproduces this exact conversion and maintains the 800-sample sliding window consumed by `meditation_features()` / `attention_features()`.

**Note on `fc11_stream_1781471387_eeg.csv`**: the `raw_s24` column appears to be the raw signed 24-bit integer, *not* the already-scaled `this+0x70` value.  Scripts using that CSV must apply `scale_raw_s24()` before feeding the signal to the feature-extraction pipeline.

## 4. Attention feature extraction

`compute_attention_features` (`0x434e0`) does only one thing: call `get_frequency_magnitude` with
- start frequency = 4 Hz
- end frequency = 38 Hz
- window size = 800
- sample rate = 160.6 Hz

`get_frequency_magnitude` maps a frequency to a bin with

```
bin = trunc(freq * 800 / 160.6 + 0.5)
```

which gives:
- `start = 20`
- `end   = 189` (exclusive upper bound)
- copied bins: `20 … 188` → **169 features**

The values are raw FFT magnitudes (no clipping, no normalization). The 169-element vector is passed directly to the attention network.

**Attention network**
- layer sizes: `[169, 70, 30, 3]`
- activations: `2` (ReLU) → `0` (sigmoid) → `4` (softmax)
- final attention candidate: `output[0] * 100.0`

Python equivalent: `reconstruct_attention_features.py` → `test_attention_pipeline.py`.

---

## 5. Meditation feature extraction

`compute_meditation_features` (`0x43530`) builds 33 features:

| Indices | Source | Function |
|---------|--------|----------|
| 0–3 | clipped time signal | `get_time_window_moments` (`0x3043c`) |
| 4–23 | 5 FFT bands × 4 moments | `get_frequency_band_moments` (`0x301c4`) |
| 24–32 | 9 deciles (10 % … 90 %) | `percentileselect` (`0x2ff40`) |

### 4.1 Clipping
`clip()` is called with `[-2000.0, 2000.0]`. The clipped buffer is used for time-domain moments and deciles. Important: the FFT buffer `this+0x88` is a copy taken **before** clipping, so frequency-band moments use the **unclipped** signal.

### 4.2 Frequency bands
`get_frequency_band_moments` receives `start = 0`, `end = 199`, band size `40`. The function iterates with `start += 40` and reads 40 consecutive magnitude bins each time, so the bands are:

```
bins 0–39, 40–79, 80–119, 120–159, 160–199
```

i.e. the first **200** FFT magnitude bins (≈ 0–40 Hz). This is why `reconstruct_meditation_features.py` slices `spectrum[:200]` and uses `[160:200]` for the last band.

### 4.3 Moment computation
For each segment the function computes the same four quantities:
- mean
- signed central moment of order 2
- signed central moment of order 3
- signed central moment of order 4

A signed central moment is implemented as:

```python
raw = mean((x - mean(x)) ** order)
value = sign(raw) * abs(raw) ** (1.0 / order)
```

which matches the `pow` + sign handling in `get_frequency_band_moments` and `get_time_window_moments`.

### 4.4 Deciles
`percentileselect` computes, for `p = 1 … 9`:

```
q    = (N - 1) * p / 10.0
base = floor(q)
frac = q - base
value = sorted[base - 1] * frac + sorted[base] * (1 - frac)
```

This is the interpolation used in `reconstruct_meditation_features.py`.

### 4.5 Normalization
`normalize_features` (`0x431f4`) does a standard z-score per feature with 33 means and 33 standard deviations stored as `float` values at `.rodata` offsets `0xa2d70` and `0xa3114` respectively. The Python arrays in `reconstruct_meditation_features.py` were verified byte-for-byte against `libfusi.so`.

**Meditation network**
- layer sizes: `[33, 70, 30, 2]`
- activations: `2` (ReLU) → `0` (sigmoid) → `4` (softmax)
- final meditation candidate: `output[1] * 100.0`

Python equivalent: `reconstruct_meditation_features.py` → `test_meditation_pipeline.py`.

---

## 6. Network execution

`run_network` (`0x264fc`) walks the layers. Each `run_layer` (`0x24118`):
1. Multiplies input by weights.
2. Adds bias.
3. Applies the activation function looked up by the layer's activation code.

The activation codes decoded from `attention_network.json` / `meditation_network.json` and used by `run_fusi_network.py` are:
- `0` → sigmoid
- `2` → ReLU
- `4` → softmax (output layer divides by the sum of exponentials)

`run_layer` also contains a special softmax branch: when the activation code is `4` it sums the layer outputs and divides each element by that sum.

---

## 7. Files created / updated

- `reconstruct_meditation_features.py` — updated to match native constants:
  - clip threshold `±2000.0` (was `±1984.0`)
  - FFT magnitude scaling `1/800`
  - 200 FFT bins, last band `160:200`
  - time/deciles use clipped signal; frequency bands use unclipped signal
  - means/stds verified against `.rodata`
- `reconstruct_attention_features.py` — new; 169 raw FFT magnitudes for 4–38 Hz
- `test_attention_pipeline.py` — new; loads `attention_network.json` and prints `output[0] * 100`
- `test_meditation_pipeline.py` — updated demo `fs` to `160.6`
- `meditation_normalization.json` — unchanged; already correct
- `focuscalm_sample_decoder.py` — new; parses FocusCalm BLE payload and decodes signed 24-bit EEG samples to the exact native `double` values

---

## 8. Verification

A Python virtual environment was created in `/Users/idonokurasani/focuscalm_lib/.venv` with `numpy`/`pandas`. All scripts run successfully:

```bash
cd /Users/idonokurasani/focuscalm_lib
.venv/bin/python reconstruct_meditation_features.py    # 33 features
.venv/bin/python test_meditation_pipeline.py           # score candidate ~98.97
.venv/bin/python test_real_focuscalm_meditation.py     # score candidate ~96.67
.venv/bin/python reconstruct_attention_features.py       # 169 features
.venv/bin/python test_attention_pipeline.py             # score candidate ~19.19
```

The attention feature count mismatch (expected 169) is now resolved: `189 - 20 = 169` bins using `fs = 160.6 Hz` and `N = 800`.

---

## 9. Not implemented / out of scope

The moving-average smoothers (`attention_moving_average` `0x4375c` and `meditation_moving_average` `0x439b0`) are not included in the test scripts. They only affect the final displayed score over time; the network candidates produced by `test_*_pipeline.py` already match the raw `output * 100` that is fed into those smoothers.

The real-time packet parser is now implemented in `focuscalm_sample_decoder.py`; the moving-average smoothers (`attention_moving_average` `0x4375c` and `meditation_moving_average` `0x439b0`) are not yet integrated into the end-to-end test.
