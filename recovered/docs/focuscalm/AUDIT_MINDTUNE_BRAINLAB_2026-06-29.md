# Audit MindTune Lab / BrainLab - 2026-06-29

## Stato letto

Sono stati letti:

```text
CODEX_MINDTUNE_LAB_BRAINLAB_FC11_HANDOFF_2026-06-29.md
CODEX_MINDTUNE_TASK_PACKET_2026-06-29/
session_000010_nap_sleep_onset_clean_report.md
session_000010_nap_sleep_onset_report.md
session_000010_nap_sleep_onset_trend.csv
```

## Punti confermati

La sessione `session_000010` e' esplorativamente utile ma legacy: manca di
`sequence_num`, contatto, lead-off, warning qualita' e IMU.

Le librerie native recuperate altrove indicano che FC11 / Crimson espone
attenzione, meditazione, engagement, EEG, bande cerebrali, IMU, orientamento,
contatto e lead-off.

Il recorder Mac attuale scriveva CSV legacy. Ora genera anche una cartella
MindTune v2 a fine registrazione.

## Limite operativo

Il Raspberry non era raggiungibile via `raspberry-pi-andrea.local` durante
questo audit, quindi BrainLab non e' stato patchato direttamente.

## Decisione tecnica

Il Python incluso in MindTune Lab non ha `pyarrow`, `pandas` o `numpy`.
Per questo il recorder scrive sempre CSV/JSON v2 e prova a scrivere parquet
solo se `pyarrow` e' disponibile. La conversione parquet puo' avvenire su
BrainLab quando il Raspberry e' raggiungibile.
