# 15 — App UI and Dashboard Audit

## 1. Frontend Stack

- `index.html` (~550 lines) — HTML template, Italian UI.
- `app.js` (~6,896 lines) — monolithic vanilla JavaScript.
- `styles.css` (~4,195 lines) — monolithic CSS.
- `mindtune_app.py` — PyWebView wrapper that starts `server.py`.

## 2. UI Features (from `app.js`)

- Session launch board (guided mode).
- FC11 helmet status and battery monitoring.
- Oura widget.
- Hebrew recovery workspace (conjugation drills, flashcards, HeLP panel).
- RPi bridge job panel (`inbox/running/done/failed`).
- APK / memory panel.

## 3. Server (`server.py`)

- 3,796 lines.
- Routes for RPi bridge jobs, FC11 EEG recording, Oura OAuth/data, Hebrew MLF/BrainLab, behavioral events, flashcard catalog.
- Couples many responsibilities.

## 4. Dashboards

- `DASHBOARD_BLUEPRINT.md` proposes 6 dashboards but they are not implemented in the web UI.
- Grafana notes are historical; no live Grafana config found.

## 5. Disposition

- `app.js`, `index.html`, `styles.css` → **REWRITE / MIGRATE** to a modular web UI (e.g., FastAPI + minimal SPA) in V2.
- `server.py` → **REWRITE** into API services: protocol runtime, sensor ingestion, Hebrew domain, dashboard API.
- `mindtune_app.py` → **MIGRATE** if PyWebView desktop shell is retained.
