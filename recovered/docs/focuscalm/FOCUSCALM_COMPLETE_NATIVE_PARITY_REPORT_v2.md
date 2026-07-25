# FocusCalm Native EEG Pipeline — Complete Parity Report v2

**Date:** current session  
**libfusi.so target:** ARM64 `libfusi.so` from FocusCalm app (`tech.brainco.focuscalm` v3.1.0 build 3110)  
**Goal:** Reverse-engineer the native EEG pipeline, replicate it in Python, and prove bit-level parity via a Frida-driven golden vector.

---

## 1. Executive summary

The FocusCalm native EEG pipeline was reverse-engineered and reproduced in Python with near-perfect parity. The key remaining mismatch was traced to the FFT implementation: `libfusi.so` embeds `fft-c` (a public-domain FFTPACK-derived C library), not NumPy's `pocketfft`. After compiling `fft-c` locally and wrapping it with `ctypes`, every tested stage matches the native capture.

`test_native_parity.py` now reports `ALL TESTS PASSED` for 137 windows captured from a controlled synthetic feed. Maximum absolute differences:

| stage | max abs diff |
|---|---|
| `scaled_samples` | `0.0` |
| `attention/features` (169) | `1.1e-15` |
| `attention/network_output` (3) | `3.3e-16` |
| `attention/score_raw` | `6.8e-17` |
| `attention/score_smoothed` | `1.8e-15` |
| `meditation/features_pre_norm` (33) | `5.7e-08` |
| `meditation/features_normalized` (33) | `8.5e-10` |
| `meditation/network_output` (2) | `2.2e-16` |
| `meditation/score_raw` | `2.8e-14` |
| `meditation/score_smoothed` | `8.5e-14` |

The controlled-capture CSV (`fc11_stream_1781471387_eeg.csv`) is dominated by a large DC offset. The native pipeline has **no DC-removal stage**, so both native and Python meditation scores saturate near `100.0`. This is expected and confirms the model was trained on near-zero-mean data.

---

## 2. Native function offsets (libfusi.so ARM64)

These offsets are used by `synthetic_feed_frida.js`:

| symbol | offset | purpose |
|---|---|---|
| `device_data_create` | `0x14f44` | allocate `DeviceData` object |
| `analyze_eeg` | `0x15a30` | main entry: copy packet into circular buffer, call `analyze_eeg_windows` |
| `analyze_eeg_windows` | `0x153b8` | linearize buffer, FFT, magnitude, dispatch attention/meditation |
| `compute_attention_features` | `0x434e0` | build 169 attention features |
| `compute_meditation_features` | `0x43530` | build 33 meditation features |
| `normalize_features` | `0x431f4` | z-score normalize 33 meditation features |
| `run_network` | `0x264fc` | generic fully-connected network runner |
| `execute_attention_callback` | `0x1d748` | attention score callback |
| `execute_meditation_callback` | `0x1d7c8` | meditation score callback |
| `fft_forward` | `0x28214` | real FFT wrapper |
| `detect_changing_state` | `0x14768` | **must be no-oped** in Frida (uses uninitialized globals) |

Other offsets observed during disassembly:

| symbol | offset | purpose |
|---|---|---|
| `attention_moving_average` | `0x4375c` | 20-slot attention smoother |
| `meditation_moving_average` | `0x439b0` | 80-slot meditation smoother (effective window 20) |
| `should_compute_attention` | `0x43898` | gate: `d8 % 2 == 0` and contact flag |
| `should_compute_meditation` | `0x43b08` | gate: `d8 % 2 == 0` and contact flag |
| `parse_content` | `0x16574` | decode BLE payload to `raw_s24` and scaled doubles |

---

## 3. `DeviceData` structure (relevant fields)

All offsets are from the `DeviceData` pointer returned by `device_data_create`.

| offset | type | meaning |
|---|---|---|
| `+0x08` | `uint8` | contact-state flag used by `should_compute_*` |
| `+0x10` | `double` | EEG scale divisor (`128.0`) |
| `+0x20` | `uint8` | device contact state (set to `1` to enable compute) |
| `+0x68` | `int32` | `samples_per_packet` (set to `20` for `fc11` stream) |
| `+0x70` | `double*` | pointer to current packet sample buffer |
| `+0x78` | `int32` | total samples in `this+0x80` (stops at 800) |
| `+0x80` | `double*` | 800-sample circular buffer |
| `+0x88` | `double*` | 800-sample linearized window / in-place FFT buffer |
| `+0x90` | `double*` | 400-sample FFT magnitude buffer |
| `+0x98` | `uint8*` | spike-detection flags |
| `+0xa0` | `double*` | 169 attention features |
| `+0xa8` | `double*` | 33 meditation features (pre-normalization) |
| `+0xd8` | `int32` | circular-buffer overwrite index (`d8`) |
| `+0xe0` | `double` | smoothed attention score |
| `+0xf8` | `double` | smoothed meditation score |
| `+0x110` | `uint8` | contact-state related |
| `+0x118` | `FFTTransformer*` | real FFT transformer object |
| `+0x138` | `void*` | attention network pointer |
| `+0x140` | `void*` | meditation network pointer |

---

## 4. End-to-end pipeline

```
BLE payload
    │
    ▼
parse_content  ──►  raw_s24  (3-byte signed BE int)
    │
    ▼
raw_s24 * 0.040690104166666664 / 128.0  ──►  scaled double
    │
    ▼
analyze_eeg copies 20 scaled samples into circular buffer this+0x80
    │
    ▼
analyze_eeg_windows (once buffer full)
    │ linearizes this+0x80 into this+0x88 (rotation by d8*spp)
    │ calls fft_forward(this+0x118, this+0x88)
    │ computes magnitudes into this+0x90
    │
    ├──► compute_attention_features(this+0x90[20:189]  → 169 features)
    │         run_network(attention_net, 169) → 3 outputs
    │         score_raw = output[0] * 100
    │         attention_moving_average(score_raw) → smoothed
    │
    └──► compute_meditation_features(this+0x88 clipped to [-2000,2000]  → 33 features)
              normalize_features(33) → z-score
              run_network(meditation_net, 33) → 2 outputs
              score_raw = output[1] * 100
              meditation_moving_average(score_raw) → smoothed
```

---

## 5. Sample scaling

```python
sample = raw_s24 * 0.040690104166666664 / 128.0
```

The numerator `0.040690104166666664` is a `.rodata` double; the divisor `128.0` is stored at `this+0x10`.

---

## 6. Window cadence

- `window_size = 800` samples
- `samples_per_packet = 20` (observed for `fc11`)
- `analyze_eeg` increments `this+0xd8` after each overwrite and resets it when `d8 * spp >= 800`
- `should_compute_attention` and `should_compute_meditation` both require `d8 % 2 == 0`
- Therefore the network stride is `2 * 20 = 40` samples
- First native compute window starts at sample `40`, ends at `840`
- Total windows from 6300 samples: `(6300 - 800) // 40 = 137`

---

## 7. FFT details (the key to parity)

`libfusi.so` statically links `fft-c` (a C reimplementation of FFTPACK, original OggSquish/NETLIB code, public domain). The symbols are `__fft_real_forward`, `__fft_real_init`, `__fft_real_backward`, `__fft_cosq_*`.

`fft_forward(transformer, input)` is **in-place**:
1. calls `__fft_real_forward(n, input, wsave, ifac)`
2. if `scale_output == 1`, divides every `input[i]` by `n`

For `n = 800` the packed FFTPACK output (after scaling by `1/800`) is:

```
out[0]   = DC real
out[1]   = Nyquist real
out[2]   = real of bin 1
out[3]   = imag of bin 1
out[4]   = real of bin 2
out[5]   = imag of bin 2
...      ...
out[796] = real of bin 397
out[797] = imag of bin 397
out[798] = real of bin 398
out[799] = imag of bin 398
```

`analyze_eeg_windows` then walks `i = 0, 2, 4, ..., 798` and computes:

```
mag[i/2] = sqrt(out[i]^2 + out[i+1]^2)
```

This produces 400 magnitude bins (`0..399`). Bin 0 is `sqrt(DC^2 + Nyquist^2)`, which for real signals without Nyquist energy is effectively `|DC|`. The native code discards the formal Nyquist bin.

`reconstruct_attention_features.py` uses `mag[20:189]` (169 bins). `reconstruct_meditation_features.py` uses `mag[0:200]` (200 bins) split into five 40-bin bands.

The local Python wrapper is `focuscalm_lib/native_fft.py`:
- loads `third_party/fft-c/libfftpack.dylib` (macOS) or `.so` (Linux)
- compiles it on demand if missing
- caches `FFTTransformer` objects per `(n, scale_output)`
- returns `n // 2` magnitudes

---

## 8. Attention feature extraction

```python
spectrum = fftpack_magnitude(eeg, scale_output=True)   # 400 bins
start = floor(4.0 * 800.0 / 160.6 + 0.5)   # 20
end   = floor(38.0 * 800.0 / 160.6 + 0.5)  # 189
attention_features = spectrum[start:end]    # 169 bins, 4-38 Hz
```

The attention branch does **not** clip the signal.

---

## 9. Meditation feature extraction

`meditation_features_pre_norm` returns 33 doubles:

1. **Features 0-3**: time-domain moments on `np.clip(eeg, -2000.0, 2000.0)`
   - `mean`
   - signed central moment order 2
   - signed central moment order 3
   - signed central moment order 4
2. **Features 4-23**: 5 frequency bands × 4 moments
   - bands are `mag[0:40]`, `mag[40:80]`, `mag[80:120]`, `mag[120:160]`, `mag[160:200]`
   - each band gets the same 4 moments
3. **Features 24-32**: deciles 10%-90% of the **clipped** time-domain signal
   - interpolation: `q = (N-1) * p / 10`, `base = floor(q)`, `frac = q - base`
   - `decile = sorted[base] * (1 - frac) + sorted[base - 1] * frac`

Then `normalize_features` computes:

```python
normalized = (pre_norm - MEDITATION_MEANS) / MEDITATION_STDS
```

using the 33 mean/std values in `meditation_normalization.json`.

---

## 10. Networks

Networks are stored as JSON in `attention_network.json` and `meditation_network.json`.

`run_fusi_network.py` implements the native runner:
- fully-connected layers
- activations: `0 = sigmoid`, `2 = ReLU`, `4 = softmax`
- `run_network(net, x)` propagates `x = W @ x + b; x = activation(x)`

Native scores:
- attention raw score `= output[0] * 100.0`
- meditation raw score `= output[1] * 100.0`

---

## 11. Smoothing

`focuscalm_smoothing.py` mirrors the native moving averages:

**AttentionSmoother** (`attention_moving_average`, `0x4375c`):
- ring size 20, initial value `2.5`, accumulator initial `50.0`
- each update: `scaled = candidate / 20`, replace oldest, output accumulator
- steady-state = mean of last 20 raw scores

**MeditationSmoother** (`meditation_moving_average`, `0x439b0`):
- ring size 80, lag 20, scale `20.0`
- each update subtracts the value written 20 steps ago, so effective window is 20
- same initial value `2.5`, accumulator `50.0`

---

## 12. Frida synthetic-feed capture

`synthetic_feed_frida.js` is injected into a live Android process (FocusCalm app or `com.android.settings` fallback with `libfusi.so` pushed to `/data/local/tmp`).

### Setup details
1. Push `libc++_shared.so` and `libfusi.so` to `/data/local/tmp`
2. `setenforce 0` so `/data/local/tmp` libraries are loadable
3. Load `libc++_shared.so` with `RTLD_GLOBAL`, then `libfusi.so`
4. Allocate a fake parent object and call `device_data_create`
5. Patch `this+0x68` to `20`, `this+0x70` to a 20-double sample buffer, `this+0x20` to `1`
6. Replace `detect_changing_state` (`0x14768`) with a no-op `NativeCallback` to avoid a null-dereference crash
7. Attach `Interceptor` hooks on `compute_attention_features`, `compute_meditation_features`, `normalize_features`, `run_network`, and both callbacks

### Capture schema (`native_capture.json`)

```json
{
  "metadata": {
    "source": "frida-synthetic-feed",
    "package": "tech.brainco.focuscalm",
    "windows_captured": 137,
    "sample_rate_hz": 160.6,
    "window_size": 800,
    "golden_status": "native"
  },
  "windows": [
    {
      "window_index": 0,
      "sample_start": 40,
      "sample_end": 840,
      "scaled_samples": [ ... 800 doubles ... ],
      "attention": {
        "features": [ ... 169 doubles ... ],
        "network_output": [ ... 3 doubles ... ],
        "score_raw": 86.53095378334163,
        "score_smoothed": 86.53095378334166
      },
      "meditation": {
        "features_pre_norm": [ ... 33 doubles ... ],
        "features_normalized": [ ... 33 doubles ... ],
        "network_output": [ ... 2 doubles ... ],
        "score_raw": 96.42530618096714,
        "score_smoothed": 96.42530618096714
      }
    }
  ]
}
```

### Running the capture

```bash
cd /Users/idonokurasani/focuscalm_lib
.venv/bin/python run_synthetic_feed.py [out.json]
```

If the FocusCalm app is not running it falls back to `com.android.settings` after starting the app via `adb shell am start`.

---

## 13. Python reference generator

`generate_golden_and_hashes.py` rebuilds the same pipeline from the source CSV:

```bash
cd /Users/idonokurasani/focuscalm_lib
.venv/bin/python generate_golden_and_hashes.py
```

Output files:
- `fixtures/FOCUSCALM_CONTROLLED_CAPTURE_GOLDEN_v1.json`
- `fixtures/FOCUSCALM_CONTROLLED_CAPTURE_RAW_BLE.bin`
- `fixtures/FOCUSCALM_NATIVE_BUFFER_800_v1.npz`
- `fixtures/FOCUSCALM_NATIVE_FEATURES_v1.json`
- `fixtures/FOCUSCALM_SHA256_v1.txt`

The reference now uses `native_fft.fftpack_magnitude` for the FFT stage, so it matches the native golden vector.

---

## 14. Verification

```bash
cd /Users/idonokurasani/focuscalm_lib
.venv/bin/python test_native_parity.py native_capture.json fixtures/FOCUSCALM_CONTROLLED_CAPTURE_GOLDEN_v1.json
```

Latest result: `ALL TESTS PASSED` (137 windows).

Other smoke tests:

```bash
.venv/bin/python test_attention_pipeline.py
.venv/bin/python test_meditation_pipeline.py
.venv/bin/python test_real_focuscalm_meditation.py
```

---

## 15. Files created / modified in this phase

| file | role |
|---|---|
| `focuscalm_lib/native_fft.py` | `ctypes` wrapper for `fft-c` |
| `focuscalm_lib/third_party/fft-c/fft.c` | `fft-c` source (downloaded from `adis300/fft-c`) |
| `focuscalm_lib/third_party/fft-c/fft.h` | `fft-c` header |
| `focuscalm_lib/third_party/fft-c/libfftpack.dylib` | compiled macOS library |
| `focuscalm_lib/reconstruct_attention_features.py` | now uses `fftpack_magnitude` |
| `focuscalm_lib/reconstruct_meditation_features.py` | now uses `fftpack_magnitude` |
| `focuscalm_lib/synthetic_feed_frida.js` | fixed `sample_start`/`sample_end`, emits one combined window, no-ops `detect_changing_state` |
| `focuscalm_lib/generate_golden_and_hashes.py` | native cadence (start offset 40) and `fft-c` FFT |
| `focuscalm_lib/test_native_parity.py` | unchanged, now passes |
| `focuscalm_lib/native_capture.json` | native golden vector (137 windows) |
| `focuscalm_lib/fixtures/FOCUSCALM_CONTROLLED_CAPTURE_GOLDEN_v1.json` | Python reference matching native |
| `focuscalm_lib/AGENTS.md` | agent notes for reproduction |

---

## 16. Known issues / open questions

1. **DC offset / meditation saturation**
   - The pipeline has **no DC removal**.
   - With the `fc11` CSV mean around `78.7`, `meditation` raw scores saturate at essentially `100.0`.
   - This matches native behavior but may indicate the provided CSV is not representative of the signal the deployed model was trained on, or that a baseline calibration step exists elsewhere in the app.

2. **`detect_changing_state` no-op**
   - Required for Frida stability because the function reads uninitialized globals.
   - This function is not on the main compute path, so it does not affect the captured features.

3. **Real vs synthetic feed**
   - The current `native_capture.json` is produced by feeding pre-scaled samples directly to `analyze_eeg`, bypassing `parse_content`.
   - A complete real-world capture would also verify `parse_content` against raw BLE payloads.

---

## 17. How to reproduce from scratch

```bash
# 1. setup Python environment
cd /Users/idonokurasani/focuscalm_lib
python3 -m venv .venv
.venv/bin/pip install frida frida-tools numpy pandas

# 2. ensure fft-c library is built (native_fft.py builds it on demand)
#    or manually:
#    cd third_party/fft-c && clang -dynamiclib -O2 -o libfftpack.dylib fft.c -lm

# 3. regenerate Python reference
.venv/bin/python generate_golden_and_hashes.py

# 4. capture native vector (needs Android emulator/device + frida-server)
.venv/bin/python run_synthetic_feed.py

# 5. compare
.venv/bin/python test_native_parity.py native_capture.json fixtures/FOCUSCALM_CONTROLLED_CAPTURE_GOLDEN_v1.json
```

---

## 18. Appendix: key constants

```python
EEG_SCALE_NUMERATOR = 0.040690104166666664
EEG_SCALE_DIVISOR   = 128.0
SAMPLE_RATE_HZ      = 160.6
SAMPLES_PER_PACKET  = 20
WINDOW_SIZE         = 800
STRIDE_SAMPLES      = 40  # 2 * SAMPLES_PER_PACKET
FIRST_WINDOW_START  = 40  # STRIDE_SAMPLES

ATTENTION_BIN_START = 20   # floor(4 * 800 / 160.6 + 0.5)
ATTENTION_BIN_END   = 189  # floor(38 * 800 / 160.6 + 0.5)
ATTENTION_FEATURES  = 169  # 189 - 20

MEDITATION_CLIP_LO  = -2000.0
MEDITATION_CLIP_HI  =  2000.0
MEDITATION_FEATURES = 33
```
