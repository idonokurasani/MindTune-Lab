# MindTune Mantra Engine — Phase 1 Implementation Report

**Branch:** `feat/mantra-engine-phase1`

**Scope:** Build the provider-independent Phase 1 Mantra production
foundation and wire it to a SpeechGen `he-IL` TTS adapter, with a
deterministic fake provider for testing and offline validation.

## 1. What was implemented

### 1.1 Data model (`mantra/phase1/spec.py`)

- `MantraSpecification` — validated, frozen, typed mantra blueprint.
- `MantraForm` — one inflected Hebrew form with `hebrew_with_niqqud`,
  `vocalized`, `ipa_phonemes`, stress index/override, and pronunciation
  override.
- `GrammaticalGroup` — tense/section container.
- `SpeechConfig` — `provider`, `language`, `locale` (`he-IL`), `voice`,
  `rate`, `pitch`, `format`.  A separate `italian_speech` config is held
  on `MantraSpecification`.
- `PauseConfig` — all configurable silence durations.
- `OutputFormat` enum.
- Consistent Unicode NFC normalization on construction.

### 1.2 Timeline compilation (`mantra/phase1/timeline.py`)

- `compile_timeline(spec)` produces a deterministic, ordered list of
  `TimelineSegment` objects.
- Segment types: `OPENING_SILENCE`, `CLOSING_SILENCE`, `ITALIAN_CUE`,
  `ITALIAN_CUE_PAUSE`, `GRAMMATICAL_LABEL`, `HEBREW_FORM`,
  `INTRA_FORM_SILENCE`, `INTER_FORM_SILENCE`, `GROUP_PAUSE`,
  `CYCLE_PAUSE`.
- Stable, deterministic segment IDs via UUIDv5 over a canonical JSON
  payload.
- Supports `repetitions_per_form`, `repetitions_per_cycle`, `cycles`,
  `include_italian_cue`, and `include_grammatical_labels`.
- Each `TimelineSegment` now carries `provider`, `language`, `locale`, and
  `voice`, enabling per-segment multilingual routing.

### 1.3 TTS boundary and SpeechGen adapter (`mantra/phase1/tts.py`)

- `TTSProvider` protocol.
- `SpeechGenTTSProvider`:
  - Locale `he-IL`, default voice `Avri`.
  - Reads `SPEECHGEN_API_KEY` and `SPEECHGEN_EMAIL` from environment
    variables.
  - Optional `SPEECHGEN_API_URL`, `SPEECHGEN_VOICE` overrides.
  - Sends a single POST to `https://speechgen.io/index.php?r=api/text`
    and expects the audio file in the response body.
  - Validates the response as WAV and computes duration from the WAV
    header.
  - Fails with the exact missing credential name when credentials are
    absent.
  - Uses the per-segment `voice` and `locale` from the timeline so a
    single provider instance can serve multiple languages.
- `FakeTTSProvider` — deterministic offline WAV generator used by tests
  and for sample production when the live service is unavailable.
- `TTSCache` — deterministic disk cache keyed on text, `locale`, provider,
  voice, rate, pitch, format, and pronunciation override.

### 1.4 Audio assembly (`mantra/phase1/assembly.py`)

- Synthesizes/caches each speech segment.
- Generates silence segments from pause configuration.
- Selects the correct `SpeechConfig` and provider instance per segment
  language, so Hebrew and Italian segments can use different voices.
- Decodes incoming WAV to int16 mono at the target sample rate,
  resampling if necessary.
- Produces both a combined `mantra.wav` and per-segment WAVs in
  `segments/` for playback.
- Updates each `TimelineSegment` with `actual_duration`, `checksum`,
  `artifact_reference`, and `generation_status`.

### 1.5 Manifest (`mantra/phase1/manifest.py`)

- `MantraManifest` records provenance, specification, full timeline,
  planned/actual duration, validation results, warnings, and status.
- Records both `voice` / `provider` and `italian_voice` /
  `italian_provider` for multilingual builds.
- Deterministic `build_identity` derived from the canonical spec plus
  `build_seed`.

### 1.6 Event model (`mantra/phase1/events.py`)

- `MantraEvent` and `EventEmitter` for build and playback events:
  `BUILD_STARTED`, `SPEC_VALIDATED`, `TIMELINE_COMPILED`,
  `SEGMENT_REQUESTED`, `SEGMENT_CACHE_HIT`, `SEGMENT_GENERATED`,
  `SEGMENT_GENERATION_FAILED`, `AUDIO_ASSEMBLED`, `BUILD_COMPLETED`,
  `PLAYBACK_STARTED`, `SEGMENT_STARTED`, `SEGMENT_COMPLETED`,
  `PLAYBACK_PAUSED`, `PLAYBACK_RESUMED`, `PLAYBACK_COMPLETED`,
  `PLAYBACK_STOPPED`.

### 1.7 Playback (`mantra/phase1/playback.py`)

- `PlaybackController` plays per-segment WAVs in a background thread.
- Emits `SEGMENT_STARTED` / `SEGMENT_COMPLETED` events.
- Supports `start`, `pause`, `resume`, `stop`, `current_segment`, and
  elapsed-time tracking.
- `SubprocessAudioPlayer` (macOS `afplay` / Linux `aplay`) and
  `NullAudioPlayer` for headless/test runs.

### 1.8 Adaptation boundary (`mantra/phase1/adaptation.py`)

- `AdaptationCommand` enum and `AdaptationBoundary` validator for Phase 2
  commands (`EXTEND_NEXT_PAUSE`, `REDUCE_NEXT_PAUSE`,
  `REPEAT_CURRENT_FORM`, `REPEAT_CURRENT_GROUP`, `HOLD_PROGRESSION`,
  `RESUME_PROGRESSION`, `REDUCE_NEW_MATERIAL_RATE`,
  `RESTORE_BASELINE_CADENCE`).
- Rejects unsupported commands and out-of-bound deltas/repeat counts
  without mutating the event stream.

### 1.9 Fixture loader (`mantra/phase1/fixtures.py`)

- `load_fixture_001_lichtov()` maps the verified
  `data/mantra/scripts/001_lichtov.json` script into a
  `MantraSpecification`.

### 1.10 CLI (`mantra/phase1/cli.py`)

```bash
# Validate a specification
python -m mantra.phase1.cli validate -i path/to/spec.json

# Build with the default SpeechGen he-IL provider (requires credentials)
python -m mantra.phase1.cli build -f 001_lichtov -o output/mantra_phase1 --voice Hila --italian-voice Giuseppe

# Build with the fake provider for offline testing
python -m mantra.phase1.cli build -f 001_lichtov -o output/mantra_phase1 --provider fake

# Play a built mantra
python -m mantra.phase1.cli play output/mantra_phase1/manifest.json --fake-audio
```

## 2. Files changed

New files:

- `mantra/phase1/__init__.py`
- `mantra/phase1/utils.py`
- `mantra/phase1/spec.py`
- `mantra/phase1/timeline.py`
- `mantra/phase1/events.py`
- `mantra/phase1/tts.py`
- `mantra/phase1/assembly.py`
- `mantra/phase1/manifest.py`
- `mantra/phase1/playback.py`
- `mantra/phase1/adaptation.py`
- `mantra/phase1/fixtures.py`
- `mantra/phase1/cli.py`
- `tests/test_mantra_engine.py`
- `docs/implementation/mantra/MINDTUNE_MANTRA_ENGINE_PHASE1_IMPLEMENTATION_REPORT.md`

Configuration:

- `pyproject.toml` — ruff `per-file-ignores` for Phase 1 complexity,
  added `mantra` to `known-first-party`, and updated `mypy`
  `python_version` to `3.12` so that modern `numpy` stubs parse.

Pre-existing uncommitted Phase 4C.2 files were left untouched:

- `packages/mpe/src/mpe/cli.py`
- `packages/mpe/src/mpe/cli_helpers.py`
- `packages/mpe/src/mpe/protocol/*.py`
- `packages/mpe/tests/test_protocol_recognition.py`
- `docs/implementation/phase4c2/MPE_PHASE_4C2_GATE1_RECOGNITION_IMPLEMENTATION_REPORT.md`

## 3. Verification

### 3.1 Targeted Mantra tests

```bash
.venv/bin/python -m unittest tests.test_mantra_engine -v
```

Result: **21/21 passed**.

### 3.2 MPE tests (main `.venv`)

```bash
.venv/bin/python -m unittest discover -s packages/mpe/tests -v
```

Result: **132/132 passed**.

### 3.3 Root test suite (`.venv_phonikud` for Hebrew support)

```bash
.venv_phonikud/bin/python -m unittest discover -s tests -v
```

Result: **112/112 passed**.

The root suite cannot be run in the main `.venv` because `phonikud`
uses compiled extensions that are not built for Python 3.14; this is an
environment mismatch, not a code defect.

### 3.4 Lint and type check

```bash
.venv/bin/ruff check mantra/phase1/ tests/test_mantra_engine.py
.venv/bin/mypy mantra/phase1/ tests/test_mantra_engine.py
```

Result: **all checks passed**.

## 4. Sample production output

### 4.1 Fake-provider sample

```bash
.venv/bin/python -m mantra.phase1.cli build \
  -f 001_lichtov \
  -o output/mantra_phase1_fake \
  --provider fake
```

Output:

- `output/mantra_phase1_fake/mantra.wav` (mono, 22050 Hz, 16-bit, 58.75 s)
- `output/mantra_phase1_fake/manifest.json`
- `output/mantra_phase1_fake/events.jsonl`
- `output/mantra_phase1_fake/segments/*.wav`

### 4.2 Live SpeechGen rebuild with multilingual voice routing

A complete rebuild was performed using live SpeechGen with explicit
multilingual routing:

```bash
SPEECHGEN_API_KEY="..." SPEECHGEN_EMAIL="..." \
.venv/bin/python -m mantra.phase1.cli build \
  -f 001_lichtov \
  -o output/mantra_phase1_speechgen \
  --voice Hila \
  --italian-voice Giuseppe \
  --sample-rate 22050
```

Output:

- `output/mantra_phase1_speechgen/mantra.wav` (mono, 22050 Hz, 16-bit, 83.57 s)
- `output/mantra_phase1_speechgen/manifest.json`
- `output/mantra_phase1_speechgen/events.jsonl`
- `output/mantra_phase1_speechgen/segments/*.wav`

Event log summary:

- 46 speech segments requested (23 Hebrew + 23 Italian).
- 23 Hebrew segments served from cache (valid prior audio reused).
- 23 Italian segments newly synthesized with the native Italian voice
  `Giuseppe`.
- 0 synthesis failures.

Manifest validation: `status: completed`.

Voice routing validation:

- 0 Italian segments use the Hebrew voice.
- 0 Hebrew segments use the Italian voice.
- Every timeline segment records `provider`, `language`, `locale`, and
  `voice`.

## 5. SpeechGen live-access status

Live SpeechGen access is available.  Hebrew segments use the `he-IL`
voice `Hila`; Italian segments use the native `it-IT` voice `Giuseppe`.

To build with live SpeechGen:

```bash
export SPEECHGEN_API_KEY="<your-api-token>"
export SPEECHGEN_EMAIL="<account-email>"

python -m mantra.phase1.cli build \
  -f 001_lichtov \
  -o output/mantra_phase1_speechgen \
  --voice Hila \
  --italian-voice Giuseppe
```

The adapter does **not** fall back to Azure, Mic, Hebrew-TTS, HebTTS,
BlueTTS, or Piper when SpeechGen is unavailable.

## 6. Notes and next steps for Phase 2

- The `AdaptationBoundary` validates Phase 2 commands but does not yet
  mutate the timeline; that belongs in the adaptive engine.
- Playback currently pauses at segment boundaries with the subprocess
  player; a `sounddevice`-based player can be added later for
  sub-segment precision.
- SpeechGen response handling can be extended to parse JSON error bodies
  and retry transient failures once a live API key is available.

COMPLETE_MINDTUNE_MANTRA_ENGINE_PHASE1
