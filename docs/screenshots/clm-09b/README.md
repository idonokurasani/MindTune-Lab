# CLM-09B Research Console Screenshots

These screenshots were captured from the running MindTune Research Console (`http://127.0.0.1:5173`) launched by `python scripts/run_mindtune_demo.py`.

| # | Screenshot | Page | Scenario | Source fixture | Visible components | Expected state |
|---|------------|------|----------|----------------|--------------------|----------------|
| 1 | [01-overview.png](01-overview.png) | Overview | Fresh launch | API health + seeded demo | Liveness, System Health badges, API/Live Loop/Voice Cache/Renderer/Playback/Event Store/MPE/Sensor | All subsystems healthy; API ready |
| 2 | [02-experiments.png](02-experiments.png) | Experiments | Demo fixture loaded | `CLM-09B Demo Hebrew Adaptive` experiment | Experiment name, protocol version, creation time, create form | One validated Hebrew adaptive experiment listed |
| 3 | [03-session-create.png](03-session-create.png) | Create Session | Form visible | Seeded experiment + protocols | Experiment select, protocol select, runtime mode, participant pseudonym, sensor/stimulus/playback inputs | Session creation form ready |
| 4 | [04-live-session.png](04-live-session.png) | Live Session | Seeded synthetic-live session running | `p-demo-01` synthetic-live session | Session ID, status badge, Readiness, SafetyControls, SensorPanel, AudioPanel, DecisionPanel, OutcomePanel, EventTimeline | Session status `running`; readiness passes; events flowing |
| 5 | [05-hebrew-trial.png](05-hebrew-trial.png) | Hebrew | New Hebrew trial started and answered | `heb-...` session | Pointed Hebrew, Italian prompt, response input, Submit button, Feedback card with scoring and next action | Correct response `להיות` submitted; feedback shows morphology/pointing scores |
| 6 | [06-calibration.png](06-calibration.png) | Profile Review | Load `p-demo-01` calibration profile | `profile-...` for `p-demo-01` | Participant, profile ID, provenance, feature baselines table | Profile valid; 60 accepted, 0 rejected; feature baselines populated |
| 7 | [07-scientific-validation.png](07-scientific-validation.png) | Scientific Validation | Study loaded and analyzed | `study-084522ec` (or equivalent) | Study table with ID, title, status, primary endpoint | Study in `draft`/`validated` state; primary endpoint visible |
| 8 | [08-session-review.png](08-session-review.png) | Review | Active running session selected | Synthetic-live session | ExportPanel, EventTimeline, CausalTrace, Hebrew stimulus metadata | Events and export available; causal trace complete |
| 9 | [09-system-operations.png](09-system-operations.png) | System | System page loaded | API health + protocols + sensors | API health, version, protocols list, sensors list | API healthy; protocols and seeded sensor visible |

## Verification checklist

- [x] No real participant data, credentials, or private recordings appear in any screenshot.
- [x] Hebrew text renders right-to-left with niqqud (e.g., `לִהְיוֹת`).
- [x] Italian prompts render left-to-right (`io essere`).
- [x] No blank pages, no permanent loading states, no unhandled error banners.
- [x] All screenshots were captured from the real running application via Playwright.

## Application commit SHA

Application commit SHA when screenshots were generated: **4d58cc5fc62bca3bec0a5077b749123bbe915e5d**
