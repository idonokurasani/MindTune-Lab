# FocusCalm - registrazione diretta da Mac

Data: 2026-06-29

## Risposta breve

Si, dovrebbe essere possibile collegare il FocusCalm direttamente al Mac via
Bluetooth Low Energy e registrare senza Raspberry.

Il protocollo usato dal casco e BLE standard:

```text
SERVICE_UUID 0d740001-d26f-4dbb-95e8-a4f5c55c57a9
WRITE_UUID   0d740002-d26f-4dbb-95e8-a4f5c55c57a9
NOTIFY_UUID  0d740003-d26f-4dbb-95e8-a4f5c55c57a9
```

La libreria Python `bleak` supporta anche macOS. Il punto delicato e che macOS
spesso non mostra il MAC address reale del dispositivo, quindi il recorder Mac
non deve affidarsi a `58:94:B2:03:6D:DC`: deve fare scan e collegarsi al device
trovato tramite service UUID/nome.

## Implementazione locale

Creato:

```text
focuscalm_mac_capture/fc11_mac_capture.py
focuscalm_mac_capture/README.md
```

Comandi disponibili:

```text
scan
smoke
record
```

Output CSV:

```text
focuscalm_mac_capture/sessions/session_CONDITION_YYYYMMDD_HHMMSS.csv
```

Colonne:

```text
sample_global,ts,raw_s24,packet_index
```

`sample_global`, `ts` e `raw_s24` sono compatibili con BrainLab. `packet_index`
serve per diagnosticare buchi di stream.

## Preparazione una tantum

```bash
cd /Users/idonokurasani/Documents/Chatgpt/Biohacking
python3 -m venv focuscalm_mac_capture/.venv
focuscalm_mac_capture/.venv/bin/python -m pip install --upgrade pip
focuscalm_mac_capture/.venv/bin/python -m pip install bleak
```

Permesso macOS:

```text
Impostazioni di Sistema -> Privacy e Sicurezza -> Bluetooth
```

Consentire Bluetooth a Terminale/Python/Codex quando macOS lo chiede.

## Sequenza test

Con casco vicino e app ufficiale chiusa:

```bash
focuscalm_mac_capture/.venv/bin/python focuscalm_mac_capture/fc11_mac_capture.py scan --seconds 10
```

Poi:

```bash
focuscalm_mac_capture/.venv/bin/python focuscalm_mac_capture/fc11_mac_capture.py smoke --seconds 12
```

Se lo smoke test passa:

```bash
focuscalm_mac_capture/.venv/bin/python focuscalm_mac_capture/fc11_mac_capture.py record \
  --condition piano_lab_20min \
  --duration 1200 \
  --prep 30
```

## Import BrainLab

Dopo la registrazione:

```bash
python -m brainlab.cli import-csv SESSION.csv \
  --db /mnt/biohacking/sqlite/brainlab.db \
  --condition piano_lab_20min \
  --notes "Piano Lab registrato da Mac" \
  --dry-run
```

Per ora il database BrainLab resta sul Raspberry, quindi l'import finale puo
essere fatto copiando il CSV sul Raspberry o aggiungendo una funzione di import
remoto dalla console.

## Rischi pratici

- macOS potrebbe non vedere il casco se non e in advertising;
- l'app ufficiale o il telefono possono agganciare il casco prima del Mac;
- la prima esecuzione puo fallire finche il permesso Bluetooth non e concesso;
- la stabilita BLE del Mac va misurata con `smoke`, non presunta;
- se il Mac va in stop, la registrazione cade: tenere alimentazione e stop
  disattivati durante sessioni lunghe.

## Decisione operativa

Da ora il progetto ha due modalita:

```text
Raspberry mode: registrazione stabile headless, ideale in laboratorio fisso.
Mac mode: registrazione mobile, ideale per Piano Lab o sessioni fuori setup.
```

La prossima cosa da fare con casco presente e testare:

1. `scan`;
2. `smoke --seconds 12`;
3. registrazione di 60 secondi;
4. import BrainLab dry-run.
