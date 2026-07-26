# 20 — Product Requirements for MindTune Lab V2

## 1. Primary and Secondary Users

- **Primary:** A single researcher or self-experimenter running real-time closed-loop cognitive-motor protocols (initially mantra audio training).
- **Secondary:** Collaborators reviewing session data; future multi-user lab deployments.

## 2. Research Use Cases

- Closed-loop adaptive mantra / Hebrew verb conjugation audio training.
- EEG-correlated attention / cognitive-load protocols using FC11, LSL, replay, or simulated sensors.
- Wearable covariate logging (Oura, HRV, Libre3, etc.) as contextual evidence.
- Deterministic replay and offline analysis of closed-loop sessions.

## 3. Functional Requirements by CLM Phase

| Capability | CLM-01 Kernel | CLM-02 Replay | CLM-03 Audio | CLM-04 Live | CLM-05 UI/API |
|---|---|---|---|---|---|
| Observation frames | Simulated, multimodal, quality-gated | Recorded FC11 replay | Simulated/replay | Live FC11/LSL | Live + replay sources |
| Cognitive state estimate | Deterministic + uncertainty | Deterministic + uncertainty | Deterministic + uncertainty | Real-time + uncertainty | Real-time + uncertainty |
| Control decision | apply/maintain/withdraw/abstain/stop | Same | Same | Same + safety stop | Same + safety stop |
| Mantra control state | Rate, pause, segment selection, mode | Same | Same + audio params | Same + audio params | Same + audio params |
| Actuator | In-memory deterministic | In-memory deterministic | Audio rendering | Audio rendering | Audio rendering |
| Actuation receipt | Yes, with provenance | Yes | Yes | Yes | Yes |
| Adapted stimulus | Text/segment plan | Text/segment plan | WAV/rendered audio | WAV/rendered audio | WAV/rendered audio |
| Intervention outcome | Yes | Yes | Yes | Yes | Yes |
| Event sourcing | Yes (MPE) | Yes | Yes | Yes | Yes |
| Replay | In-memory | In-memory + recorded data | In-memory | In-memory | In-memory + persistent backend |
| API / UI | None | None | None | Minimal CLI | FastAPI + web |

## 4. Non-Functional Requirements

- **Determinism:** the same observation sequence + control policy + seed produces the same `MantraControlState` and adapted stimulus.
- **Reproducibility:** every control cycle, decision, and outcome is an event with provenance.
- **Auditability:** full event stream can be replayed and inspected.
- **Safety:** unsafe control parameters are clamped or rejected; `STOP` is always available.
- **Modularity:** `clm/` knows nothing about Hebrew, TTS provider, or EEG hardware brand.
- **Offline operation:** local/offline voice rendering must support closed-loop actuation without network calls.
- **Web-first UI:** PyWebView optional; browser and shell use the same web app and API.
- **Portability:** macOS, Linux, Windows via Docker.
