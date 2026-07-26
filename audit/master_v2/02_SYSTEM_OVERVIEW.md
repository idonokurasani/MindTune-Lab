# 02 — System Overview

## 1. Authoritative Root

`/Users/idonokurasani/Documents/Chatgpt/Biohacking` is the Biohacking root. The primary live repository is `mindtune_console/`. All other MindTune-related directories are copies, recovery worktrees, archives, or supporting tooling.

## 2. Primary Repository Layout (`mindtune_console/`)

```
mindtune_console/
├── packages/mpe/              # MindTune Protocol Engine v1.1 (core runtime)
│   └── src/mpe/
│       ├── runtime.py         # Event-sourced runtime
│       ├── events.py          # Canonical event envelope & payload schemas
│       ├── event_store.py     # Append-only in-memory/SQLite event store contract
│       ├── replay.py          # Deterministic replay
│       ├── aggregates.py      # RuntimeState & event handlers
│       ├── providers.py       # Provider protocols & mock implementations
│       ├── protocol/          # Protocol runners (immediate_recall, recognition, ...)
│       └── domains/hebrew/    # Hebrew domain adapter + HeLP integration
├── hebrew/                    # Shared Hebrew linguistic engine
├── mantra/                    # Audio/TTS/mantra production pipeline
│   └── phase1/                # Phase 1 Mantra engine
├── data/                      # Curated data (hebrew, audio_profiles, mantra)
├── data/hebrew_resources/     # Vendor Hebrew resources (WordNet, etc.)
├── repos/                     # External TTS/model repos (BlueTTS, HebTTS)
├── tests/                     # Console-level tests
├── scripts/                   # Build, diagnostic, evaluation scripts
├── server.py                  # HTTP orchestration server
├── mindtune_app.py            # PyWebView desktop wrapper
├── app.js                     # Frontend (monolithic)
├── index.html                 # Frontend template
├── styles.css                 # Frontend styling
├── oura_api.py                # Oura Ring OAuth client
├── help_profiler.py           # HeLP norms + personal profiler
├── docs/                      # Architecture + implementation docs
├── docker-compose.yml         # Minimal compose
└── Dockerfile
```

## 3. Satellite Repositories / Directories

| Path | Role | Status |
|---|---|---|
| `mindtune-learning-framework/` | MLF Core / BrainLab learning framework | Active, separate repo with own `pyproject.toml` |
| `mindtune_capture/` | macOS BLE FC11 EEG capture + scientific QC + LSL bridge | Active, mature |
| `brainlab_protocols/` | JSON protocol definitions | Active |
| `FOCUSCALM_ZAI_AUDIT_PACKET_2026-07-19/` | FocusCalm native parity reverse engineering | Reference/audit |
| `mindtune_console_BACKUP_BEFORE_GITHUB_CLEANUP/` | Full backup copy | Archive candidate |
| `mindtune_eeg_github_recovery/` | Git worktree (recovery branch) | Archive candidate |
| `mindtune_rescue/` | Git worktree (rescue branch) | Archive candidate |
| `mindtune_archives/`, `tmp/` | App bundle archives | Archive / discard |
| `systemd/`, `remote_scripts/` | ATHENA backup/document processing | Keep, but not core MindTune |
| `firmware_analysis/` | MC03/Gigaset investigation | Archive |
| `athena_mac_wrappers/`, `wordpress/`, `tools/` | Uninvestigated | Unverified |

## 4. Runtime Use Today

- **Console / UI:** `server.py` + `mindtune_app.py` + `index.html`/`app.js`/`styles.css` provide an Italian-language desktop web UI for FC11 EEG recording, Oura data, Hebrew recovery, and RPi bridge job queues.
- **Protocol Engine:** `packages/mpe/` runs offline unit tests and CLI mock sessions (`mpe.cli`). It is not yet served by `server.py` routes.
- **EEG Capture:** `mindtune_capture/fc11_mac_capture.py` runs as a macOS BLE subprocess and writes CSV/JSON. `lsl_bridge.py` can stream to Lab Streaming Layer.
- **Hebrew Audio:** `mantra/phase1/` builds deterministic audio assets using SpeechGen TTS (requires `SPEECHGEN_API_KEY`/`SPEECHGEN_EMAIL`).

## 5. Product-Definition Conformance

| Canonical Requirement | Evidence | Verdict |
|---|---|---|
| Protocol → Stimulus | `mpe/protocol/immediate_recall.py` + `mpe/protocol/trial_pipeline.py` | Supported |
| Stimulus → Response | `TrialPipeline.open_response_window`, `poll_observation` | Supported |
| Response → Behavioral evidence | `mpe/protocol/immediate_recall.py:304-350`, `mpe/aggregates.py` | Supported |
| Sensor evidence contextual | `mpe/protocol/cognitive_state.py:65-72` (EEG cannot create load by itself) | Supported |
| Cognitive-state estimation | `CognitiveStateEstimator` in `cognitive_state.py` | Supported |
| Adaptation changes execution | `adaptation_policy.py` changes `response_deadline` for next trial in `immediate_recall.py:420-434` | Supported at library level, shadow-mode in policy |
| Every session auditable | `EventStore` append-only, `session_sequence_number` monotonic, provenance | Supported |
| Deterministic replay | `mpe/replay.py` replays events to `RuntimeState` | Supported |
| Hebrew as adapter | `mpe/domains/hebrew/adapter.py`, `HELP_INTEGRATION.md` boundary rules | Supported |

The implementation **contradicts** the definition only in that the production `server.py` does not close the loop with real EEG and the adaptation policy is not deployed.

## 6. Inaccessible Components

- `.raspberry_bridge/` and `pi_mnt/` referenced by `server.py` but not present.
- `/mnt/biohacking/sqlite/health_data.db` referenced in `BIOHACKING_MASTERPLAN.md` not located in the working tree.
- Some `.venv` subdirectories may not be inspectable due to file permissions or symlinks; no source code is believed to be missing.
