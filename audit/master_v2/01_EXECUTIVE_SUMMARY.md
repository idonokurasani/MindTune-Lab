# 01 — Executive Summary

## Overall Verdict: INCOMPLETE (existing implementation partially supports the canonical closed-loop definition)

The MindTune ecosystem contains a mature, event-sourced protocol engine (`packages/mpe/`), a working Hebrew audio/mantra pipeline, and a functioning FC11 EEG capture toolchain (`mindtune_capture/`).  However, the canonical closed-loop cognitive-experimentation platform is only **partially realized**: the `ImmediateRecallRunner` demonstrates the full loop at the library level, but the production console (`server.py` / `app.js`) does not yet close the loop with real EEG, and the adaptation policy defaults to `SHADOW_MODE` (`packages/mpe/src/mpe/protocol/adaptation_policy.py:91`).

## Highest-Confidence Findings

1. **Event-sourced core is sound.** `mpe/runtime.py`, `mpe/events.py`, `mpe/event_store.py`, and `mpe/replay.py` implement an append-only, sequence-ordered, deterministic event store with 27 canonical event types. `mpe/replay.py` replays events into `RuntimeState` via `state.apply(event)`.
2. **Behavior-primary closed loop is implemented in code.** `mpe/protocol/immediate_recall.py` and `mpe/protocol/cognitive_state.py` make behavioral evidence authoritative and treat EEG as contextual. `adaptation_policy.py` adapts `response_deadline` for the next trial. This matches the candidate product definition.
3. **Hebrew is a clean domain adapter.** `packages/mpe/src/mpe/domains/hebrew/adapter.py` and `mantra/phase1/` maintain domain separation; HeLP evidence is consumed only inside the Hebrew domain (`HELP_INTEGRATION.md:51-54`).
4. **Test suite is substantive.** 313 tests passed in the most recent read-only run (`tests/`, `packages/mpe/tests/`). Ruff passed; mypy has 31 test-side type precision errors in `test_hebrew_domain.py`.
5. **Critical security defect.** `/Users/idonokurasani/Documents/Chatgpt/Biohacking/.oura_credentials` contains a live Oura `client_secret` committed in the working tree. A history-purge plan exists at `docs/audits/HISTORY_PURGE_PLAN.md` but the secret is still present.
6. **Heavy duplication and dead copies.** `mindtune_console_BACKUP_BEFORE_GITHUB_CLEANUP/`, `mindtune_eeg_github_recovery/`, `mindtune_rescue/`, `mindtune_archives/`, and `tmp/` contain duplicate or obsolete copies that should be archived or discarded.
7. **Raspberry Pi / BrainLab bridge is incomplete.** `server.py` references `BRIDGE`, `INBOX`, `RUNNING`, `DONE`, `FAILED` paths for an RPi bridge, but the actual `.raspberry_bridge/` and `pi_mnt/` directories are missing or empty.
8. **FocusCalm reverse engineering is valuable but incomplete.** The `FOCUSCALM_ZAI_AUDIT_PACKET_2026-07-19/` packet reproduces native attention/meditation networks, but the end-to-end BLE sample-to-analysis-buffer signal chain is not verified.

## Critical Contradictions

- **Adaptation is declared but not deployed.** `AdaptationPolicy` emits `adaptation_decision` events with `deployment_status=SHADOW_MODE` (`adaptation_policy.py:91`). The closed loop changes runtime parameters in `ImmediateRecallRunner` but is not wired into `server.py`/UI.
- **Production console does not use the new MPE.** `server.py` (3,796 lines) orchestrates FC11 recording, Oura, RPi bridge, and Hebrew recovery, but the adaptive `ImmediateRecall` flow lives only in `packages/mpe/tests/` and scripts, not in the live server routes.
- **Hebrew TTS requires external paid credentials.** `mantra/phase1/tts.py` depends on `SPEECHGEN_API_KEY` and `SPEECHGEN_EMAIL` (`AGENTS.md:22-24`), making local/offline operation impossible unless TTS is pre-cached.
- **Data ownership is split.** Behavioral events live in `mpe/event_store.py` (in-memory/SQLite experiments), EEG data in `mindtune_capture/` CSV, Oura in `.oura_token`, and biohacking metrics in a separate `/mnt/biohacking/sqlite/health_data.db` referenced in `BIOHACKING_MASTERPLAN.md` but not found at expected mount. No unified session datastore exists.

## Recommended Dispositions (Summary)

- **KEEP / MIGRATE:** `packages/mpe/`, `mantra/phase1/`, `hebrew/`, `data/hebrew/`, `oura_api.py`, `help_profiler.py`, `mindtune_capture/` (FC11 pipeline), `brainlab_protocols/`.
- **REWRITE:** `server.py` monolith and `app.js` monolith for V2 (split into API + web UI + protocol runner).
- **ARCHIVE:** `mindtune_console_BACKUP_BEFORE_GITHUB_CLEANUP/`, `mindtune_eeg_github_recovery/`, `mindtune_rescue/`, `mindtune_archives/`, `FOCUSCALM_ZAI_AUDIT_PACKET_2026-07-19/` (after extraction of key findings), `forensic_audit_20260618_025114/`, `devin_handoffs/`.
- **DISCARD:** `tmp/`, `.pnpm-store/`, duplicate `citizen_cafe_all_courses/` copies, `azure_speech.py` references.
- **UNVERIFIED:** `athena_mac_wrappers/`, `wordpress/`, `tools/`, `pi_mnt/`, `.raspberry_bridge/` (if present).
