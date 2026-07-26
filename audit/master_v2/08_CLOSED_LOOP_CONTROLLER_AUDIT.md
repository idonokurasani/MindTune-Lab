# 08 — Closed-Loop Controller Audit

## 1. Evidence Against the Canonical Loop

The canonical closed loop is implemented end-to-end inside `mpe/protocol/immediate_recall.py`:

1. **Stimulus** → `pipeline.emit_instruction(PRESENT_STIMULUS)` + `pipeline.emit_stimulus()` (`immediate_recall.py:229-331`).
2. **Response** → `pipeline.open_response_window()` + `pipeline.poll_observation()` (`immediate_recall.py:265-280`).
3. **Behavioral evidence** → `self_confirmation`, `latency`, `answer_status` (`immediate_recall.py:281-356`).
4. **Sensor evidence** → `_poll_eeg()` / `_emit_eeg_observation()` (`immediate_recall.py:218-222`, `374-403`).
5. **Cognitive-state estimation** → `CognitiveStateEstimator.update()` (`cognitive_state.py:52-88`).
6. **Adaptation decision** → `AdaptationPolicy.decide()` (`adaptation_policy.py:96-154`).
7. **Changed next runtime parameter** → `self.response_deadline` updated and used in the next `ResponseWindowSpec` (`immediate_recall.py:420-434` and `269`).
8. **Persisted events** → `adaptation_decision` appended to `EventStore`.
9. **Deterministic replay** → `Replay.replay(session_id)` reconstructs `RuntimeState` including event sequence.

## 2. Cognitive-State Estimator

`mpe/protocol/cognitive_state.py`:

- Behavioral load: `1.0` if incorrect, `0.5` if correct but above latency bound, `0.0` otherwise.
- EEG load: gated by `artifact` / `poor_signal` quality flags; `cognitive_load_index` from mock EEG.
- Combined load: `max(behavioral_load, eeg_load)` **only if behavioral load > 0**; otherwise EEG is ignored.
- Hysteresis: `STABLE → POSSIBLE_DRIFT → RECOVERY_REQUIRED → RECOVERING → STABLE`.

## 3. Adaptation Policy

`mpe/protocol/adaptation_policy.py`:

- `target_dimension`: `response_deadline`.
- `baseline_deadline` = 10.0, `max_response_deadline` = 20.0, `deadline_step` = 0.5.
- `_target_deadline()` returns `max_response_deadline` only in `RECOVERY_REQUIRED`; otherwise returns `baseline_deadline`.
- `_step()` bounds changes by `deadline_step` to prevent oscillation.
- `deployment_status` defaults to `SHADOW_MODE` (`adaptation_policy.py:91`).

## 4. Scientific Validity

- **Behavior-primary** is enforced in code.
- **EEG contextual** is enforced: EEG cannot create an adaptation by itself.
- **Thresholds and steps** are design choices (HYPOTHESIS maturity); no empirical validation file was found.
- **Shadow mode** means the loop changes `response_deadline` in the runner but is not deployed in production.

## 5. Disposition

- `cognitive_state.py` → **KEEP** (validated architecture, validate thresholds in V2).
- `adaptation_policy.py` → **KEEP** (good bounded policy; remove shadow mode after validation).
- `immediate_recall.py` → **KEEP** (demonstrates the full loop).
- Production deployment → **REWRITE** `server.py` to use the MPE closed-loop flow with real or mock EEG providers.
