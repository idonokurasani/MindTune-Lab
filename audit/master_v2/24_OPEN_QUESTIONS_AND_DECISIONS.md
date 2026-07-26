# 24 — Open Questions and Decisions

## Decisions Now Made

1. **Repository strategy for V2:** Incremental development inside `mindtune_console` using a strangler architecture. No new replacement repository. Preserve `packages/mpe/` and add `packages/clm/`.
2. **Credential exposure:** The Oura `client_secret` must be revoked immediately and Git history must be purged on a separate branch (see `SECURITY_HISTORY_CLEANUP_PLAN.md`).
3. **Raspberry Pi bridge:** Optional sensor gateway implementing the same provider contract as simulated, FC11, LSL, and replay gateways; not a core assumption.
4. **TTS / voice strategy:** Provider-agnostic voice rendering; local/offline rendering required for closed-loop; remote TTS only for asset generation.
5. **FocusCalm signal chain:** Separate experimental workstream; not a prerequisite for CLM-01. Progression: simulated → recorded replay → validated native-buffer/LSL → live.
6. **MLF relationship:** Do not merge `mindtune-learning-framework` into MPE during CLM-01; keep typed boundaries.
7. **UI strategy:** Web-first; PyWebView optional thin container; same web app and API contracts.
8. **First vertical slice:** CLM-01 Closed-Loop Mantra Control Kernel, proving the causal chain `ObservationFrame → CognitiveStateEstimate → ControlDecision → MantraControlState → ActuationReceipt → AdaptedStimulus → InterventionOutcome`.

## Remaining Decisions / Open Questions

1. **CLM-01 `MantraControlState` parameters** — Which exact parameters are actuated first? (rate, pause duration, segment selection, playback mode, etc.)
2. **Control policy** — Which thresholds and hysteresis values should CLM-01 use for `apply/maintain/withdraw/abstain/stop`?
3. **ObservationFrame schema** — Which evidence fields are required for CLM-01? (cognitive load index, quality flags, latency, correctness, HRV?)
4. **FC11 experimental schedule** — When will recorded-replay data be available for CLM-02?
5. **Local TTS model** — Which offline voice-rendering engine will be the first supported provider?
6. **`mindtune-learning-framework` boundary** — Define the exact interface contract between learning objectives and control decisions before CLM-02.
7. **Biohacking data** — Whether `/mnt/biohacking/sqlite/health_data.db` still exists and how to integrate it.
8. **Backup copies** — Confirm the user approves archiving `mindtune_console_BACKUP_*`, `mindtune_eeg_github_recovery/`, `mindtune_rescue/`, and `mindtune_archives/` after secret scan.
