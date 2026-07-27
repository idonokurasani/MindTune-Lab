# MindTune Research Console — CLM-09B Demo Walkthrough

This document describes how to launch and operate the MindTune Research Console demo end-to-end.

## Prerequisites

- macOS with Python 3.11+
- Node.js 18+ and npm
- No FC11 hardware required
- No SpeechGen account required
- No paid audio generation required

## One-command launch (development)

From the repository root:

```bash
git checkout feat/clm-09b-research-console-demo
python scripts/run_mindtune_demo.py
```

The launcher will:

1. Validate the Python virtual environment and required packages.
2. Validate Node.js, npm, and `apps/research-console/node_modules`.
3. Create `data/clm09b_demo/` as the temporary demo data directory.
4. Start the CLM API on `http://127.0.0.1:8000`.
5. Start the Research Console dev server on `http://127.0.0.1:5173`.
6. Seed a complete demo fixture (experiment, replay session, synthetic-live session, Hebrew session, calibration profile, study, analysis, export).
7. Open the default browser automatically.

## URLs

- Research Console: `http://127.0.0.1:5173`
- CLM API: `http://127.0.0.1:8000/api/v1`

## Production-style launch

```bash
python scripts/run_mindtune_demo.py --production --no-browser
```

This builds `apps/research-console` with `VITE_API_BASE=http://127.0.0.1:8000/api/v1` and serves the static bundle from `npx vite preview`. The console is still reachable at `http://127.0.0.1:5173`; the API is available at `http://127.0.0.1:8000/api/v1` and the frontend talks to it via CORS.

## Manual install (if the launcher reports missing dependencies)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
cd apps/research-console
npm install
cd ../..
```

Then run `python scripts/run_mindtune_demo.py` again.

## Demo walkthrough

1. **Checkout branch**
   ```bash
   git checkout feat/clm-09b-research-console-demo
   ```

2. **Launch**
   ```bash
   python scripts/run_mindtune_demo.py
   ```

3. **Open the URL** printed by the launcher (`http://127.0.0.1:5173`).

4. **Overview** — confirm all health badges are green: API, Live Loop, Voice Cache, Renderer, Playback, Event Store, MPE, Sensor.

5. **Experiments** — view the seeded "CLM-09B Demo Hebrew Adaptive" experiment. Note the protocol version, curriculum version, and calibration requirement shown in the parameters.

6. **Create Session** — select the demo experiment, enter a pseudonymous participant ID, choose `Synthetic Live` or `Replay`, and click `Create Session`. The readiness panel updates in real time.

7. **Live Session** — click `Live Session`. The seeded synthetic-live session is already running; observe sensor state, readiness, audio panel, decision panel, and event timeline.

8. **Hebrew** — click `Hebrew`, then `Start Hebrew Session`. A trial appears with pointed Hebrew (`לִהְיוֹת`) and an Italian prompt (`io essere`). Type the unpointed Hebrew response (`להיות`) and click `Submit`. Observe the deterministic feedback, morphology/pointing scores, and next-item decision.

9. **Calibration** — click `Profile Review`, enter `p-demo-01` as the participant and the profile ID from the demo fixture, then click `Load`. The profile shows valid status, accepted/rejected counts, and feature baselines.

10. **Scientific Validation** — click `Validation` to see the demo study, conditions, primary endpoint, and assignment status.

11. **Review** — click `Review` to inspect the event timeline, causal trace, Hebrew stimulus metadata, and export options for the active session.

12. **System** — click `System` to inspect API version, protocols, sensors, and operational health.

13. **Export** — on the `Review` page, click `Export` to generate a JSON export of the current session. The download URL is printed in the export panel.

14. **Stop** — press `Ctrl+C` in the terminal running `python scripts/run_mindtune_demo.py`. The launcher terminates the API and frontend process groups and exits cleanly.

## What is seeded

- One validated Hebrew adaptive experiment (`CLM-09B Demo Hebrew Adaptive`)
- One completed replay session (`p-demo-01`)
- One running synthetic-live session (`p-demo-01`)
- One synthetic sensor (`synth-fc11-01`) connected to the live session
- One Hebrew adaptive session with a submitted correct response
- One CLM-07 calibration profile for `p-demo-01` (`fc11.default`)
- One CLM-08 study (`CLM-09B Demo Adaptive vs Fixed`) with an assignment and analysis
- One JSON export request for the replay session

## Safety and data notes

- All data is synthetic. No real participants, recordings, credentials, or paid audio are used.
- FC11 hardware is detected as unavailable/non-fatal; the demo runs on synthetic sources.
- The launcher uses deterministic playback; no SpeechGen request is made.
- Demo data is written to `data/clm09b_demo/` and is not committed.
