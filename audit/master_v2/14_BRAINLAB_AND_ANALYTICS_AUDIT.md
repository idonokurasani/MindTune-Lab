# 14 — BrainLab and Analytics Audit

## 1. BrainLab Protocols

`brainlab_protocols/` contains JSON protocol definitions:

- `cognitive_core_45min.json`
- `hebrew_reentry_recall_30min.json`
- `piano_skill_reactivation_35min.json`
- `piano_lab_20min.json`
- `brain_health_weekly_scaffold.json`
- `sleep_consolidation_retest_24h.json`
- `sport_cognition_weekly_optimization.json`
- `programs/calm_101.json`, `programs/focus_101.json`
- Schemas: `session_manifest_v2_schema.json`, `training_log_schema.json`
- Templates: `training_log_template.csv`, `daily_state_template.csv`

## 2. MLF Core (`mindtune-learning-framework/`)

- `mlf/core/brainlab.py` is a domain-agnostic learning coordinator.
- Features: event store management, session lifecycle, protocol resolution, domain adapter delegation, scorer, scheduler, knowledge graph, state caching, lineage tracking.
- This is a separate directory with its own `pyproject.toml` and tests.

## 3. Analytics in `mindtune_capture/`

- `scientific_qc.py` — per-window QC metrics.
- `scientific_spectral.py` — PSD and band powers.
- `scientific_longitudinal.py` — session-level alpha reactivity and effect sizes.

## 4. Dashboard Documentation

- `DASHBOARD_BLUEPRINT.md` defines 6 dashboards: Daily Command Center, Sleep/Recovery, Metabolism, Environment, FocusCalm Lab, Data Quality.
- Grafana setup notes at root (`GRAFANA_*.md`).
- No live Grafana config found in `mindtune_console/`.

## 5. Disposition

- `brainlab_protocols/` → **KEEP** (well-structured protocol definitions).
- `mindtune-learning-framework/` → **KEEP** (domain-agnostic core; decide whether to merge or keep separate).
- `scientific_*.py` → **KEEP** (transparent, auditable).
- Grafana / dashboard → **REWRITE** for V2 (build web UI dashboards from event store, not from separate CSV dumps).
