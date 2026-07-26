# 05 — Component Reuse Matrix

## Reuse Matrix (Core Subsystems)

| Component | Repository/Path | Purpose | Current Status | Runtime Relevance | Maturity | Scientific | Test Coverage | Dependencies | Coupling | Known Defects | Security/Privacy | Disposition | Confidence | Migration Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| MPE Runtime | `packages/mpe/src/mpe/runtime.py` | Event-sourced protocol runtime | Authoritative core | Core | PRODUCTION | PARTIALLY SUPPORTED | High (224 mpe tests pass) | dataclasses | Low (protocol-agnostic) | None | None | KEEP | HIGH | Core of V2 |
| MPE Event Model | `packages/mpe/src/mpe/events.py` | 27 canonical event types + payload schemas | Authoritative | Core | PRODUCTION | VALIDATED | High | `mpe.enums`, `mpe.types` | Low | None | None | KEEP | HIGH | Core of V2 |
| MPE Event Store | `packages/mpe/src/mpe/event_store.py` | Append-only in-memory store contract | Authoritative | Core | PRODUCTION | VALIDATED | High | `mpe.events`, `mpe.validation` | Low | Only in-memory backend for default; SQLite experiments in `persistence/` | None | KEEP | HIGH | Add PostgreSQL backend for V2 |
| MPE Replay | `packages/mpe/src/mpe/replay.py` | Deterministic replay | Authoritative | Core | PRODUCTION | VALIDATED | High (`test_replay.py`) | `mpe.aggregates` | Low | None | None | KEEP | HIGH | Core of V2 |
| Immediate Recall | `packages/mpe/src/mpe/protocol/immediate_recall.py` | Closed-loop protocol runner | Authoritative library, not wired to UI | Core (library) | PRODUCTION | PARTIALLY SUPPORTED | High | MPE runtime, providers, cognitive state, adaptation | Medium | Adaptation in shadow mode | None | KEEP | HIGH | Wire into V2 API and UI |
| Cognitive State Estimator | `packages/mpe/src/mpe/protocol/cognitive_state.py` | Behavioral-authoritative load estimation | Implemented | Core | PRODUCTION | HYPOTHESIS | High | `mpe.enums` | Low | Thresholds not validated empirically | None | KEEP | HIGH | Validate in V2 pilots |
| Adaptation Policy | `packages/mpe/src/mpe/protocol/adaptation_policy.py` | Bounded response-deadline policy | Implemented, shadow mode | Core | PRODUCTION | HYPOTHESIS | High | `mpe.cognitive_state`, `mpe.enums` | Low | `deployment_status` defaults to `SHADOW_MODE` | None | KEEP | HIGH | Activate after validation |
| Trial Pipeline | `packages/mpe/src/mpe/protocol/trial_pipeline.py` | Domain-agnostic trial event flow | Authoritative | Core | PRODUCTION | VALIDATED | High | MPE runtime, providers | Low | None | None | KEEP | HIGH | Reuse as-is |
| Hebrew Domain Adapter | `packages/mpe/src/mpe/domains/hebrew/adapter.py` | Hebrew immediate recall adapter | Authoritative | Domain | PRODUCTION | VALIDATED | Good (`test_hebrew_domain.py`) | `mpe.domain.base`, Hebrew models | Low | None | None | KEEP | HIGH | Reuse as adapter |
| HeLP Integration | `packages/mpe/src/mpe/domains/hebrew/help/` | HeLP norms loader + repository | Authoritative | Domain | PRODUCTION | VALIDATED | Good (`test_help_integration.py`) | CSV/JSON | Low | Data files `data/hebrew_verbs_help_*.csv` may be absent in some checkouts | None | KEEP | HIGH | Reuse as adapter source |
| Hebrew Linguistic Engine | `hebrew/` | Multi-source conjugation / pronunciation consensus | Active | Domain | PRODUCTION | VALIDATED | Good | `phonikud` (optional) | Medium | Some license uncertainty (Pealim/Phonikud) | None | KEEP | HIGH | Keep as package |
| Mantra Phase 1 | `mantra/phase1/` | Hebrew verb audio production | Active | Domain | PRODUCTION | VALIDATED | Good (`test_mantra_engine.py`) | numpy, wave, TTS providers | Medium | Requires SpeechGen credentials | None (creds env-only) | KEEP | HIGH | Reuse audio pipeline |
| Mantra Curriculum | `mantra/phase1/curriculum.py` | 320-verb selection policy | Active | Domain | PRODUCTION | VALIDATED | Good (`test_curriculum_policy.py`) | `data/hebrew/curriculum_v1_320.json` | Low | None | None | KEEP | HIGH | Reuse |
| server.py | `server.py` | HTTP orchestration server | Active UI/API | Runtime | PRODUCTION | PARTIALLY SUPPORTED | Unknown (manual) | oura_api, help_profiler, MLF (opt) | High (monolith) | Pi bridge dirs missing | Exposes routes for Oura; see credentials | REWRITE | HIGH | Split into API + services |
| app.js / index.html / styles.css | `app.js`, `index.html`, `styles.css` | Desktop web UI | Active | UI | PRODUCTION | N/A | None (frontend) | None | High (6,896-line JS) | No tests | None | REWRITE / MIGRATE | HIGH | Modular SPA for V2 |
| mindtune_app.py | `mindtune_app.py` | PyWebView launcher | Active | UI | PRODUCTION | N/A | None | webview, subprocess | Low | None | None | MIGRATE | HIGH | Keep if PyWebView retained |
| oura_api.py | `oura_api.py` | Oura OAuth2 + daily fetch | Active | Sensor/wearable | PRODUCTION | VALIDATED | Unknown | urllib, http.server | Low | Tokens stored plaintext | `.oura_credentials` at root contains live secret | MIGRATE | HIGH | Encrypt tokens, rotate secret |
| help_profiler.py | `help_profiler.py` | HeLP norms + personal profiler | Active | Domain science | PRODUCTION | VALIDATED | Good (`test_help_profiler.py`) | csv, sqlite3 | Low | None | Personal profile data in SQLite | KEEP | HIGH | Reuse |
| FC11 BLE Capture | `mindtune_capture/fc11_mac_capture.py` | macOS BLE EEG capture | Active | Sensor | PRODUCTION | VALIDATED | Good (`test_fc11_capture_pipeline.py`) | bleak, protobuf | Medium | macOS-only | BLE pairing uses fixed UUID | MIGRATE | HIGH | Abstract BLE for V2 |
| FC11 Pipeline | `mindtune_capture/fc11_capture_pipeline.py` | Async bounded queue processing | Active | Sensor | PRODUCTION | VALIDATED | Good | asyncio, csv | Low | None | None | KEEP | HIGH | Reuse |
| LSL Bridge | `mindtune_capture/lsl_bridge.py` | Lab Streaming Layer outlet | Active (optional) | Sensor | PRODUCTION | VALIDATED | Good (`test_lsl_bridge.py`) | pylsl (optional) | Low | None | None | KEEP | HIGH | Reuse |
| Scientific QC | `mindtune_capture/scientific_qc.py` | EEG quality control | Active | Sensor | PRODUCTION | VALIDATED | Good (`test_scientific_qc.py`) | statistics, math | Low | None | None | KEEP | HIGH | Reuse |
| Scientific Spectral | `mindtune_capture/scientific_spectral.py` | PSD / band power | Active | Sensor | PRODUCTION | VALIDATED | Good (`test_scientific_spectral.py`) | math | Low | None | None | KEEP | HIGH | Reuse |
| Scientific Longitudinal | `mindtune_capture/scientific_longitudinal.py` | Session-level summaries | Active | Analysis | PRODUCTION | VALIDATED | Medium | statistics | Low | None | None | KEEP | HIGH | Reuse |
| FocusCalm RE Packet | `FOCUSCALM_ZAI_AUDIT_PACKET_2026-07-19/` | Native attention/meditation reverse engineering | Reference | Research | PROTOTYPE | PARTIALLY SUPPORTED | Medium | numpy, tensorflow | Low | Signal chain to native buffer not verified end-to-end | None | ARCHIVE | MEDIUM | Extract verified findings then archive |
| BlueTTS Repo | `repos/BlueTTS/` | ONNX TTS experiment | Unused | None | PROTOTYPE | UNSUPPORTED | None | ONNX Runtime | High | Not integrated | None | ARCHIVE | MEDIUM | Remove or archive |
| HebTTS Repo | `repos/HebTTS/` | VALLe-based Hebrew TTS | Unused | None | PROTOTYPE | PARTIALLY SUPPORTED | None | tokenizers | High | Not integrated | None | ARCHIVE | MEDIUM | Remove or archive |
| Piper Adapter | `mantra/piper_adapter.py` | Piper TTS evaluation | Unused | None | PROTOTYPE | UNSUPPORTED | None | piper_onnx | Medium | Not used | None | ARCHIVE | MEDIUM | Discard |
| Backup Copies | `mindtune_console_BACKUP_BEFORE_GITHUB_CLEANUP/`, `mindtune_eeg_github_recovery/`, `mindtune_rescue/` | Copies / worktrees | Obsolete | None | LEGACY | N/A | N/A | None | None | May contain old credentials | Risk of leaked secrets | ARCHIVE/DISCARD | HIGH | Verify, then archive/discard |
| App Bundle Archives | `mindtune_archives/`, `tmp/` | Old `.app` builds | Obsolete | None | LEGACY | N/A | N/A | None | None | May embed credentials | Risk | ARCHIVE | HIGH | Keep latest, archive rest |

## Disposition Summary

- **KEEP:** 22 components
- **MIGRATE:** 6 components
- **REWRITE:** 3 components (`server.py`, `app.js`/frontend monolith)
- **ARCHIVE:** 8 components
- **DISCARD:** 1 component (`.pnpm-store`, `tmp` transient caches)
- **UNVERIFIED:** `athena_mac_wrappers/`, `wordpress/`, `tools/`
