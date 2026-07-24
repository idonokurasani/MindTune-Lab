# HebTTS Evaluation Report

## Scope

This report evaluates `slp-rl/HebTTS` as a candidate production TTS voice for the MindTune Lab Mantra system, limited to the three approved verbs:

- `לִכְתֹּב` (to write)
- `לִהְיוֹת` (to be)
- `לַעֲשׂוֹת` (to do)

No integration into MindTune Lab was performed. No additional verbs were generated.

## Setup and Hardware

| Item | Value |
|------|-------|
| Repository | `https://github.com/slp-rl/HebTTS` |
| Checkpoint | Google Drive `11NoOJzMLRX9q1C_Q4sX0w2b9miiDjGrv` → `repos/HebTTS/ckpt.pt` (3.4 GB) |
| EnCodec model | `~/.cache/torch/hub/checkpoints/encodec_24khz-d7cc33bc.th` (88.9 MB) |
| Python venv | `.venv_hebtts` (Python 3.12) |
| Hardware | MacBook Neo, Apple A18 Pro, 6 cores (2P+4E), 8 GB RAM |
| MPS available | Yes (`torch.backends.mps.is_available() == True`) |
| CUDA available | No |

### Key dependency versions

- `torch` 2.13.0
- `torchaudio` 2.11.0
- `torchcodec` 0.15.0 (required by torchaudio for save/load on this version)
- `transformers` 5.14.1
- `lhotse` 2.0.0a2.dev+git.cfc429b.clean
- `librosa` 0.11.0
- `encodec` 0.1.1
- `omegaconf` 2.3.1
- `torchmetrics` 1.9.0
- `phonemizer` 3.3.0
- `psutil` 7.2.2
- `soundfile` 0.14.0

## Installation Notes

- `pip install -e repos/HebTTS` fails because the repo has no `packages` directive and `setuptools` rejects the flat layout.
- Installed all dependencies manually instead.
- `torch.load` in PyTorch 2.13 defaults to `weights_only=True`, which rejects this checkpoint. Required `TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1`.
- `torchaudio` 2.11.0 required `torchcodec` for WAV save/load; installed separately.
- `audiocraft` (required for Multi Band Diffusion) was **not** installed; it failed earlier because PyAV/`pkg-config`/`libav` were missing and is a heavy dependency.

## Generated Assets

- `data/hebtts_eval/audio/` — WAV and MP3 samples.
- `data/hebtts_eval/inputs/` — CSV inputs used for `infer.py`.
- `data/hebtts_eval/hebtts_evaluation.csv` — per-sample metadata.
- `data/hebtts_eval/hebtts_evaluation.json` — machine-readable metadata.

## What Was Generated

| Category | Count | Status |
|----------|-------|--------|
| Plain unvocalized forms + sentences + experiments | 20 | generated |
| Speaker variations (`geek`, `shaul`) on infinitives | 6 | generated |
| Vocalized Hebrew inputs | 13 | skipped / crashed |
| IPA phoneme input | 1 | failed (`KeyError: 'li'`) |
| Multi Band Diffusion attempt | 1 | failed (`ModuleNotFoundError: audiocraft`) |

### Plain generated forms

For each verb the following were generated with the default `osim` speaker:

- infinitive
- present masculine singular
- past 1st singular
- future 1st singular
- full sentence (`אני רוצה …`)

Plus three repeated `לכתוב` samples, `top_k=1` and `top_k=80` variants, and one punctuation variant (`אני רוצה לכתוב,`).

## Performance on Current Hardware

| Metric | Value |
|--------|-------|
| Model load time | ~20–30 s per `infer.py` invocation |
| Average generation time per sample (batched) | ~23 s |
| Peak RSS observed | 2.1 GB |
| Average generated audio duration | 1.24 s |
| Average RTF (real-time factor) | ~23× (23 s of CPU per 1 s of audio) |
| RTF range | 8.6× to 38.8× |

On this 8 GB Apple Silicon Mac, inference is **functional but very slow** on CPU. It is not real-time usable for an interactive mantra app.

### CPU / GPU / MPS compatibility

- **CPU**: Works. The repo defaults to CPU on this machine.
- **CUDA**: Not applicable.
- **MPS**: `torch.backends.mps.is_available()` is `True`, but the inference script only checks `torch.cuda.is_available()`. A manual patch to select `mps` caused the model load to hang with no further output for >5 minutes and was aborted. MPS is **not practically usable** with this codebase.

## Niqqud, Punctuation, Phonemes, Determinism

| Test | Result |
|------|--------|
| Niqqud accepted? | **No — crashes**. Vocalized input (`לִכְתֹּב`, `אֲנִי רוֹצֶה…`) produces `KeyError: 'ִ'` in the text collater. Niqqud is therefore **harmful**, not ignored. |
| Punctuation? | `replace_chars()` strips `,.?-"` before tokenization. The comma in `אני רוצה לכתוב,` was removed; output did not show a deterministic pause. Output differed from the non-punctuated run only because sampling is stochastic. |
| Repeated forms stable? | **No**. Three `לכתוב` generations with default `top_k=40` produced three different SHA-256 hashes. |
| Deterministic with `top_k=1`? | Still produced a unique hash, so even top-1 with `temperature=1` is not byte-identical across runs. |
| Does `top_k` change pronunciation? | It changes the generated audio (different hashes for `top_k=1` vs `40` vs `80`). It is not possible to say from this data whether it changes only voice/prosody or also phonetic content. |
| Explicit phoneme input? | **Not accepted**. Passing `liχtˈov` failed with `KeyError: 'li'`. HebTTS has no phoneme input interface. |
| Multi Band Diffusion? | Not tested because `audiocraft` is not installed. The repo’s MBD path is a single conditional import; installing `audiocraft` (and its PyAV/FFmpeg build deps) is required. |

## Speaker Coverage

`speakers/speakers.yaml` bundles three speakers:

- `osim` (default)
- `geek`
- `shaul`

All three produced audio for the three infinitives. The speaker prompt WAVs are `osim.wav` (396 KB), `geek.wav` (324 KB), `shaul.wav` (971 KB).

## Pronunciation Accuracy vs. Pealim / Phonikud Audit

HebTTS is a **diacritics-free TTS** model: it receives unvocalized Hebrew and must infer vowels, stress, and vocal shva internally. The generated forms were compared at the **text-input level** with the Pealim-vocalized forms and the corrected Phonikud phonemes.

**Important caveat:** No Hebrew ASR was available in this environment, so the actual audio pronunciation (vowels, stress, vocal shva) was not machine-verified. The table below shows the expected phonemes and stress for every generated plain form.

| Verb | Form | HebTTS input | Pealim vocalized | Expected stress | Corrected Phonikud phonemes | Audio duration |
|------|------|--------------|------------------|-----------------|-----------------------------|----------------|
| לכתוב | infinitive | `לכתוב` | `לִכְתֹּב` | 2 | `liχtˈov` | 2.23 s |
| לכתוב | present ms | `כותב` | `כּוֹתֵב` | 2 | `kotˈev` | 0.73 s |
| לכתוב | past 1s | `כתבתי` | `כָּתַבְתִּי` | 2 | `katˈavti` | 2.23 s |
| לכתוב | future 1s | `אכתוב` | `אֶכְתֹּב` | 2 | `ʔeχtˈov` | 0.60 s |
| לכתוב | sentence | `אני רוצה לכתוב` | `אֲנִי רוֹצֶה לִכְתֹּב` | — | — | 2.11 s |
| להיות | infinitive | `להיות` | `לִהְיוֹת` | 2 | `lihjˈot` | 0.60 s |
| להיות | past 1s | `הייתי` | `הָיִיתִי` | 2 | `hajˈiti` | 0.89 s |
| להיות | future 1s | `אהיה` | `אֶהְיֶה` | 2 | `ʔehjˈe` | 0.69 s |
| להיות | sentence | `אני רוצה להיות` | `אֲנִי רוֹצֶה לִהְיוֹת` | — | — | 2.71 s |
| לעשות | infinitive | `לעשות` | `לַעֲשׂוֹת` | 3 | `laʔasˈot` | 0.89 s |
| לעשות | present ms | `עושה` | `עוֹשֶׂה` | 2 | `ʔosˈe` | 1.01 s |
| לעשות | past 1s | `עשיתי` | `עָשִׂיתִי` | 2 | `ʔasˈiti` | 1.05 s |
| לעשות | future 1s | `אעשה` | `אֶעֱשֶׂה` | 3 | `ʔeʔesˈe` | 0.60 s |
| לעשות | sentence | `אני רוצה לעשות` | `אֲנִי רוֹצֶה לַעֲשׂוֹת` | — | — | 2.11 s |

Because the input text for every plain form matches the standard unvocalized Pealim spelling, the model **should** be saying the correct word. Whether it produces the correct Pealim vowels, stress, and vocal shva is an audio-level question that requires listening or ASR verification.

## Naturalness and Voice Quality (estimated)

HebTTS is a VALL-E-style language model operating on EnCodec discrete tokens, trained on in-the-wild Hebrew speech (HebDB). It is architecturally capable of high naturalness. The observed audio durations vary significantly across runs and speakers (e.g. `לכתוב` from 0.85 s to 2.23 s), which suggests the sampling is expressive but also unstable.

Compared to the other candidates:

| Engine | Naturalness estimate | Speed | Size | Offline | Notes |
|--------|----------------------|-------|------|---------|-------|
| HebTTS | High potential (neural LM, trained on spontaneous Hebrew) | Very slow on CPU (RTF ~23×) | 3.4 GB + EnCodec | Yes | No niqqud, no phoneme input, non-deterministic |
| Piper/Phonikud-TTS | Lower (small Piper voice) | Fast (real-time) | ~80 MB total | Yes | Deterministic, phoneme-driven, but voice is less natural |
| Azure plain / vocalized | High (cloud neural voice) | Cloud latency | N/A | No | No precise stress/phoneme control |
| Mic Hebrew-TTS | Moderate-to-high | Cloud latency | N/A | No | No public API, trial endpoint only |

## Licensing Audit

| Asset | License found | Notes |
|-------|---------------|-------|
| Repository top-level (`infer.py`, `utils.py`, `hebrew_root_tokenizer.py`, `pyproject.toml`) | **None / all rights reserved** | No `LICENSE` file in repo root; no license headers in the HebTTS-specific files. The README does not state a license. |
| `valle/` subdirectory | Apache-2.0 | Per-file headers; code is derived from `lifeiteng/vall-e`. |
| Checkpoint `ckpt.pt` | **None stated** | Published via Google Drive; no license or model card attached. Treat as all rights reserved unless authors confirm otherwise. |
| HebDB training data | CC BY 4.0 | Confirmed by Hugging Face dataset card and the HebDB paper. |
| Bundled speaker WAVs (`osim.wav`, `geek.wav`, `shaul.wav`) | **None stated** | No license or attribution file included. |
| Generated output | Depends on checkpoint license | If the checkpoint is unlicensed, commercial redistribution of generated audio is legally unclear. |

**Licensing verdict:** The HebTTS repository and checkpoint are **not safe for commercial use without explicit permission from the authors**, because no license is granted. The training data is CC BY 4.0, but that does not license the model weights or the inference code.

## Ratings (1–5, 5 best)

| Criterion | Rating | Rationale |
|-----------|--------|-----------|
| Vowel accuracy | N/A (unverified) | No ASR; model is diacritics-free and trained on Hebrew speech, so it should infer vowels, but cannot be confirmed here. |
| Stress accuracy | N/A (unverified) | Same as above. |
| Vocal-shva accuracy | N/A (unverified) | Same as above. |
| Intelligibility | 4 (estimated) | VALL-E on a large Hebrew dataset is likely very intelligible. |
| Israeli naturalness | 4 (estimated) | Training data is in-the-wild Israeli Hebrew. |
| Voice quality | 4 (estimated) | Neural LM TTS generally produces high-quality audio. |
| Repeated-listening suitability | 2 | Non-determinism and variable durations make it hard to guarantee consistency across repetitions. |
| Local inference practicality | 1 | Very slow (RTF ~23×), 3.4 GB model, 2.1 GB peak RAM, MPS unsupported/hangs. |
| Licensing suitability | 1 | No license on repo code or checkpoint; not usable commercially without clarification. |

## Verdict and Recommendation

**HebTTS is not recommended as the production voice for MindTune Lab today.**

Reasons:

1. **Does not accept vocalized Hebrew or phonemes**, so the verified Pealim pronunciation cannot be injected. Niqqud causes a crash.
2. **Non-deterministic output** and variable durations make it unsuitable for an app that requires repeatable mantra playback.
3. **Too slow for local, interactive use** on this Mac (RTF ~23×). MPS support is missing and hangs when forced.
4. **Licensing is unclear** for both the code and the checkpoint; commercial use is not permitted without an explicit license.
5. **Multi Band Diffusion is impractical** without installing a heavy `audiocraft` dependency chain.

The best current pipeline remains:

- `phonikud` (with Pealim-vocalized input) + manual stress/vocal-shva correction + `phonikud-tts`/Piper for deterministic local synthesis, **or**
- Azure as a natural-sounding cloud fallback when pronunciation does not need to be explicitly controlled.

HebTTS would only become competitive if the authors release a permissive license, add phoneme/vocalized-text support, add determinism, and optimize inference for Apple Silicon or provide GPU/MPS support.
