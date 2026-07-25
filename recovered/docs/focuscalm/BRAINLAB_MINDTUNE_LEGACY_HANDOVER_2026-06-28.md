# BrainLab / FocusCalm - handover operativo

Data: 2026-06-28

Fonte principale:

- `https://chatgpt.com/share/6a412ceb-d9d4-83ed-b26c-cad9331d29e1`

## Stato reale

La sessione condivisa aggiorna il progetto FocusCalm verso BrainLab. La richiesta
principale, pero, non e la gestione delle registrazioni lunghe: e trasformare
BrainLab in una libreria scientifica personale separata dalla vecchia dashboard
Grafana.

Il refactor principale e documentato in:

- `BRAINLAB_REFACTOR_HANDOVER_2026-06-28.md`

La parte sotto riguarda l'incidente operativo successivo: una registrazione lunga
`nap_sleep_onset` persa per caduta SSH.

Risultati dichiarati nella conversazione:

- `eyes_open` registrata bene;
- `eyes_closed` registrata bene, ma non va trattata come baseline pulita;
- durante `eyes_closed` il soggetto stava scivolando verso sonnolenza;
- tentativo `nap_sleep_onset` non registrato per caduta della connessione SSH;
- il dato soggettivo resta importante: pisolino / sleep onset riuscito;
- problema operativo identificato: le registrazioni lunghe non devono dipendere
  da una sessione SSH interattiva.

Conclusione operativa: registrazioni lunghe solo dentro `tmux` oppure con
`nohup`.

## Nota scientifica

La sessione `eyes_closed` del 2026-06-28 non e una baseline neutra occhi chiusi.
Va etichettata come probabilmente `drowsy` o contaminata da transizione verso
sonno.

Questo e utile, non un fallimento: indica che per questo soggetto occhi chiusi e
immobilita possono portare rapidamente verso sonnolenza. Va separato da una vera
baseline `eyes_closed_alert`, vigile, seduta e breve.

## Prossima sequenza consigliata

1. Documentare BrainLab con note e runbook.
2. Rendere obbligatorio `tmux` o `nohup` per sessioni lunghe.
3. Registrare `eyes_closed_alert` breve, 120 secondi, vigile e seduto.
4. Registrare `nap_sleep_onset` in `tmux`, 20 minuti.
5. Dopo ogni registrazione controllare subito file, righe e dimensione.

## Comandi di verifica post-sessione

Sul Raspberry:

```bash
cd /mnt/biohacking/home/focuscalm/calibration
ls -lt session_*_20260628_*.csv | head -20
wc -l session_*_20260628_*.csv
```

Per cercare file parziali recenti:

```bash
find /mnt/biohacking/home/focuscalm/calibration \
  -name "session_*_20260628_*.csv" \
  -mmin -120 \
  -ls
```

## Nota da conservare sul Raspberry

File remoto previsto:

```text
/mnt/biohacking/home/brainlab/notes/reference_sessions_20260628.md
```

Contenuto minimo:

```text
## Nap attempt - not recorded

Condition: nap_sleep_onset
EEG recorded: no
Reason: SSH connection dropped during attempted recording
Subjective state: nap / sleep onset
Fell asleep: yes
Notes:

## Eyes closed - caution

Condition: eyes_closed
EEG recorded: yes
Quality: to be analyzed
Interpretation caution: subject was drifting toward sleep
Use as clean eyes-closed baseline: no
Suggested replacement: eyes_closed_alert, 120 s, seated, awake
```

## Regola BrainLab

Ogni sessione deve avere una tripla separata:

1. dato EEG raw;
2. metadati della condizione;
3. nota soggettiva.

Le sessioni perse o contaminate non vanno cancellate dalla memoria del progetto:
vanno etichettate. BrainLab deve imparare anche dai fallimenti operativi e dagli
stati soggettivi, senza mischiarli con dati calibrativi puliti.
