# BrainLab - refactor handover

Data: 2026-06-28

Fonte:

- `https://chatgpt.com/share/6a412ceb-d9d4-83ed-b26c-cad9331d29e1`

## Richiesta principale

BrainLab deve diventare una libreria scientifica personale per analisi EEG
FocusCalm. Non deve essere trattato come una nuova pagina della vecchia dashboard
Grafana.

Istruzione esplicita:

```text
NON voglio piu lavorare sulla vecchia dashboard Grafana.
Il progetto BrainLab e separato.
```

Quindi il lavoro prioritario non e dashboarding, ma refactor software:
pacchetto Python, API pulita, test automatici, export riproducibili e report
statici.

## Stato dichiarato nella conversazione

Host e ambiente:

```text
Raspberry Pi 5
Python venv: ~/focuscalm
Repository: /mnt/biohacking/home/brainlab
Database: /mnt/biohacking/sqlite/brainlab.db
```

Struttura gia creata:

```text
brainlab/
  analysis/
  collector/
  features/
  models/
  storage/
  reports/
  dashboard/
  tests/
```

Tabelle:

```text
sessions
eeg_raw
eeg_features
```

Formato CSV importato:

```text
sample_global
ts
raw_s24
```

Dato sperimentale verificato:

```text
40200 campioni
162.75 s
247.0 Hz
```

## Regola scientifica non negoziabile

Per l'analisi non usare `ts` come base temporale, perche ha molti valori
ripetuti.

La base temporale corretta e:

```python
t = sample_global / 247.0
```

`ts` puo restare come dato grezzo originale nel database, ma non deve entrare in:

- segmentazione;
- finestre;
- PSD/Welch;
- feature temporali;
- report scientifici.

## Modulo esistente

Esiste gia un primo `eeg_features.py` con:

- `clean_signal()`;
- Welch PSD;
- band power;
- spectral entropy;
- Hjorth parameters.

Questo va trasformato in moduli testabili, non moltiplicato in script sparsi.

## Architettura target

```text
brainlab/
  __init__.py
  config.py
  io/
    __init__.py
    csv_loader.py
    parquet.py
  preprocessing/
    __init__.py
    signal.py
  features/
    __init__.py
    spectral.py
    time_domain.py
    extractor.py
  storage/
    __init__.py
    database.py
    schema.py
  reports/
    __init__.py
    html.py
    plots.py
  pipeline/
    __init__.py
    analyze_session.py
  cli.py
tests/
  test_signal_timebase.py
  test_preprocessing.py
  test_features.py
  test_database.py
```

Il vecchio `analyze_session.py` deve diventare solo orchestrazione.

## Contratto dati interno

Ogni sessione preparata deve diventare un DataFrame con almeno:

```text
session_id
sample_global
t
raw_s24
signal_clean
```

Le feature a finestre devono contenere almeno:

```text
session_id
window_index
start_sample
end_sample
start_t
end_t
duration_s
delta_power
theta_power
alpha_power
beta_power
gamma_power
total_power
spectral_entropy
hjorth_activity
hjorth_mobility
hjorth_complexity
```

## Separazione responsabilita

Il pipeline collega i moduli, ma non contiene la scienza.

Funzioni/ruoli desiderati:

- `load_raw_session()`: legge dal database;
- `prepare_signal()`: ordina, ricostruisce `t`, pulisce il segnale;
- `extract_features()`: calcola feature a finestre;
- `save_features()`: salva su SQLite;
- `save_session_parquet()`: export prepared;
- `save_features_parquet()`: export feature;
- `generate_session_report()`: report HTML statico.

Nessun modulo scientifico deve fare query SQL dirette.

## Export

Directory consigliata:

```text
/mnt/biohacking/home/brainlab/data/
  raw/
  prepared/
  features/
```

File:

```text
data/prepared/session_000001_prepared.parquet
data/features/session_000001_features.parquet
```

## Report HTML

Prima fase: niente dashboard complessa.

Output statico e riproducibile:

```text
reports/session_000001.html
reports/session_000001/
  signal.png
  psd.png
  bandpowers.png
  entropy.png
```

Contenuti minimi:

- metadati sessione;
- durata;
- numero campioni;
- frequenza di campionamento;
- segnale pulito;
- PSD media;
- andamento bande;
- spectral entropy;
- Hjorth activity/mobility/complexity.

## Test minimi richiesti

1. Timebase: `t` deve derivare da `sample_global`, non da `ts`.
2. Segnale sintetico 10 Hz: alpha power deve dominare theta/beta.
3. Feature extraction: colonne attese presenti.
4. SQLite temporaneo: save/load funzionano.
5. Parquet: file creati e leggibili.

Test chiave:

```python
def test_timebase_uses_sample_global_not_ts():
    df = pd.DataFrame({
        "sample_global": [0, 1, 2, 247],
        "ts": [100.0, 100.0, 100.0, 100.0],
        "raw_s24": [1, 2, 3, 4],
    })

    out = prepare_signal(df, fs=247.0)

    assert out["t"].tolist() == [0.0, 1/247.0, 2/247.0, 1.0]
```

## CLI desiderata

Comando:

```bash
python -m brainlab.cli analyze-session 1 \
  --db /mnt/biohacking/sqlite/brainlab.db \
  --output /mnt/biohacking/home/brainlab/output \
  --fs 247.0
```

Comandi futuri:

```text
analyze-session
list-sessions
export-session
```

## Ordine di lavoro corretto

1. Audit non distruttivo del repository remoto BrainLab.
2. Commit 1: struttura pacchetto e spostamento logica, senza nuovi algoritmi.
3. Commit 2: timebase e preprocessing, con test dedicato.
4. Commit 3: feature extraction e test su sinusoidi.
5. Commit 4: storage SQLite isolato in `BrainLabDB`.
6. Commit 5: export parquet.
7. Commit 6: report HTML statico.
8. Commit 7: CLI.

## Relazione con FocusCalm long recording

La parte `tmux`/`nohup` e importante ma secondaria: serve per proteggere le
registrazioni lunghe (`nap_sleep_onset`) e per annotare correttamente sessioni
fallite o contaminate.

Non deve spostare il focus principale: BrainLab e una libreria scientifica
separata, non un appendice operativa di Grafana.
