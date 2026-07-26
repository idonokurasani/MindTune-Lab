# MindTune Lab — Master V2 Reconstruction Blueprint

## Deliverable Index

| # | Deliverable | Purpose |
|---|---|---|
| 01 | [01_EXECUTIVE_SUMMARY.md](01_EXECUTIVE_SUMMARY.md) | Highest-level verdict and critical findings |
| 02 | [02_SYSTEM_OVERVIEW.md](02_SYSTEM_OVERVIEW.md) | Ecosystem scope, repositories, and runtime picture |
| 03 | [03_REPOSITORY_AND_BRANCH_INVENTORY.md](03_REPOSITORY_AND_BRANCH_INVENTORY.md) | Git repos, branches, HEADs, stashes, worktrees |
| 04 | [04_ARCHITECTURE_MAP.md](04_ARCHITECTURE_MAP.md) | Runtime, protocol, sensor, and domain boundaries |
| 05 | [05_COMPONENT_REUSE_MATRIX.md](05_COMPONENT_REUSE_MATRIX.md) | Component disposition matrix (KEEP/MIGRATE/REWRITE/ARCHIVE/DISCARD/UNVERIFIED) |
| 06 | [06_DATA_AND_DATABASE_INVENTORY.md](06_DATA_AND_DATABASE_INVENTORY.md) | Data assets, schemas, generated caches |
| 07 | [07_PROTOCOL_ENGINE_AUDIT.md](07_PROTOCOL_ENGINE_AUDIT.md) | MPE protocol engine evidence |
| 08 | [08_CLOSED_LOOP_CONTROLLER_AUDIT.md](08_CLOSED_LOOP_CONTROLLER_AUDIT.md) | Cognitive-state estimation and adaptation |
| 09 | [09_EVENT_MODEL_AND_REPLAY_AUDIT.md](09_EVENT_MODEL_AND_REPLAY_AUDIT.md) | Event sourcing and replay determinism |
| 10 | [10_SENSOR_AND_EEG_PIPELINE_AUDIT.md](10_SENSOR_AND_EEG_PIPELINE_AUDIT.md) | EEG, Oura, HRV, sensor integrations |
| 11 | [11_FOCUSCALM_REVERSE_ENGINEERING_AUDIT.md](11_FOCUSCALM_REVERSE_ENGINEERING_AUDIT.md) | FC11 / FocusCalm reverse-engineering artifacts |
| 12 | [12_HEBREW_DOMAIN_AUDIT.md](12_HEBREW_DOMAIN_AUDIT.md) | Hebrew learning, HeLP, immediate-recall adapter |
| 13 | [13_AUDIO_TTS_AND_PRONUNCIATION_AUDIT.md](13_AUDIO_TTS_AND_PRONUNCIATION_AUDIT.md) | Mantra, TTS, pronunciation pipelines |
| 14 | [14_BRAINLAB_AND_ANALYTICS_AUDIT.md](14_BRAINLAB_AND_ANALYTICS_AUDIT.md) | BrainLab protocols and analytics |
| 15 | [15_APP_UI_AND_DASHBOARD_AUDIT.md](15_APP_UI_AND_DASHBOARD_AUDIT.md) | UI, dashboard, console frontend |
| 16 | [16_TEST_COVERAGE_AND_QUALITY_AUDIT.md](16_TEST_COVERAGE_AND_QUALITY_AUDIT.md) | Test inventory and static-analysis results |
| 17 | [17_SECURITY_PRIVACY_AND_SECRETS_AUDIT.md](17_SECURITY_PRIVACY_AND_SECRETS_AUDIT.md) | Credentials, secrets, privacy |
| 18 | [18_TECHNICAL_DEBT_AND_DUPLICATION.md](18_TECHNICAL_DEBT_AND_DUPLICATION.md) | Debt, duplication, dead code |
| 19 | [19_SCIENTIFIC_CONTRACT.md](19_SCIENTIFIC_CONTRACT.md) | Behavior-primary scientific contract |
| 20 | [20_PRODUCT_REQUIREMENTS_V2.md](20_PRODUCT_REQUIREMENTS_V2.md) | V2 product specification |
| 21 | [21_V2_TARGET_ARCHITECTURE.md](21_V2_TARGET_ARCHITECTURE.md) | V2 clean architecture |
| 22 | [22_V2_IMPLEMENTATION_PLAN.md](22_V2_IMPLEMENTATION_PLAN.md) | Implementation plan and milestones |
| 23 | [23_MIGRATION_AND_ARCHIVE_PLAN.md](23_MIGRATION_AND_ARCHIVE_PLAN.md) | Migration, archive, discard plan |
| 24 | [24_OPEN_QUESTIONS_AND_DECISIONS.md](24_OPEN_QUESTIONS_AND_DECISIONS.md) | Unresolved questions requiring user decision |

## Machine-readable Inventories

- [component_inventory.csv](component_inventory.csv)
- [component_inventory.json](component_inventory.json)
- [repository_inventory.csv](repository_inventory.csv)
- [data_inventory.csv](data_inventory.csv)
- [test_inventory.csv](test_inventory.csv)
- [dependency_inventory.csv](dependency_inventory.csv)

## Method Notes

- All findings are read-only; no source files were modified.
- Evidence is drawn from direct file inspection, Git metadata, and test/static-analysis observations.
- Conclusions distinguish observed fact, inference, and recommendation.
