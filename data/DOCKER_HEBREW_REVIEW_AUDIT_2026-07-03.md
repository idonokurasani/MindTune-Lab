# Docker Hebrew Review Audit

Data: 2026-07-03

## Verdetto

La lavorazione Docker non va promossa a database principale.

Il compito richiesto era limitato:

- lavorare solo su `source = citizen_cafe_text_export_import`;
- lavorare solo su `deck = Blue` oppure `Purple`;
- lavorare solo sulle righe con `flags` contenente `needs_italian_review`;
- modificare solo `back` e `flags`;
- non modificare `front`;
- non eliminare righe;
- non deduplicare globalmente.

Docker ha invece fatto una deduplicazione globale, ha normalizzato testo fuori
scope e ha modificato anche `front`.

## File prodotti da non usare come fonte principale

```text
mindtune_console/data/quizlet_hebrew_audit_reviewed.csv
mindtune_console/data/quizlet_hebrew_audit_FINAL_20260703_225446.csv
mindtune_console/data/quizlet_hebrew_audit_coherent_backup_20260703_225035.csv
mindtune_console/data/HEBREW_DATABASE_REVIEW_DOCUMENTATION.md
```

Questi file possono essere conservati solo come esperimento o riferimento
manuale, ma non devono sostituire il catalogo attivo.

## File attivo dell'app

MindTune Lab usa:

```text
mindtune_console/data/quizlet_hebrew_seed.json
```

Il server lo carica da:

```text
mindtune_console/server.py
FLASHCARD_SEED_FILE = APP / "data" / "quizlet_hebrew_seed.json"
```

Quindi la lavorazione Docker non sembra aver sostituito direttamente il file
attivo dell'app.

## Numeri principali

Confronto fra:

```text
input:  mindtune_console/data/quizlet_hebrew_audit.csv
output: mindtune_console/data/quizlet_hebrew_audit_reviewed.csv
```

Risultati:

```text
righe input:  10547
righe output:  9268
righe rimosse: 1279
colonne: 13 -> 13
front modificati su righe ancora presenti: 486
back modificati su righe ancora presenti: 1690
flags modificati su righe ancora presenti: 448
```

Righe target secondo il mandato originale:

```text
totale target: 390
Blue target:   191
Purple target: 199
```

Effetti fuori scope:

```text
target rimossi:      68
non-target rimossi: 1211
target modificati:  322
non-target modificati: 1819
```

Righe rimosse per deck, principali:

```text
Lime                           193
Dark Green                     153
Rosetta Stone Hebrew Level 1   151
Indigo                         127
Alex Study Sheet               103
Blue                            90
Yellow                          80
Pink                            68
Orange                          59
Light Blue                      53
Purple                          14
```

Righe rimosse per source, principali:

```text
pdf_extracted_raw               679
verified_tabular                389
citizen_cafe_review_zip         136
citizen_cafe_text_export_import  75
```

## Violazioni concrete

### 1. Ha eliminato righe

Il mandato diceva esplicitamente di non eliminare righe.

Docker ha ridotto il file da 10547 a 9268 righe.

### 2. Ha modificato `front`

Il mandato diceva di non toccare `front` e `front_original`.

Esempi di `front` modificato:

```text
'שטויות )רבים, נ' -> 'שטויות)רבים, נ'
'!איזה קטע' -> '! איזה קטע'
'עבר  )להביא הבאתי' -> 'עבר)להביא הבאתי'
'ירח )ז' -> 'ירח)ז'
'היא מרגישה הרבה יותר טוב .' -> 'היא מרגישה הרבה יותר טוב.'
```

Anche quando sembrano solo spazi o punteggiatura, in un database didattico
ebraico queste modifiche non vanno fatte automaticamente.

### 3. Ha lavorato fuori scope

Ha modificato o rimosso righe Red, Orange, Pink, Yellow, Lime, Green, Dark Green,
Turquoise, Indigo e sorgenti non richieste.

### 4. La documentazione contiene affermazioni fuorvianti

Esempio:

```text
Front intatti: SI
```

Ma il confronto mostra almeno 486 `front` modificati sulle righe ancora
presenti, oltre alle righe eliminate.

### 5. Deduplicazione non sicura

La deduplicazione per `front` e pericolosa qui, perche due carte con lo stesso
fronte possono appartenere a livelli, fonti, contesti o traduzioni diverse.

Esempio tipico: lo stesso termine puo comparire in un livello base con una
traduzione semplice e in un livello avanzato con uso idiomatico.

## Stato Blue/Purple nel file Docker

Nel file Docker finale:

```text
Blue:   263 righe, 166 semantic_review
Purple: 185 righe,  56 semantic_review
```

Questo significa che buona parte della revisione non e davvero conclusa. In piu,
alcune righe Blue/Purple provengono ancora da estrazione PDF grezza e contengono
tracce palesemente sporche.

Esempi dal file Docker:

```text
בסבלנות | p a tientl y (with p a tience)
לחכות ל... עתיד | :
ח כה | ת
ח כי | ת
לנקות את.... מנקה, מנקה | To clean.... i clean(m.),I clean(f.
```

## Raccomandazione operativa

Non usare `quizlet_hebrew_audit_reviewed.csv` o `quizlet_hebrew_audit_FINAL...`
come sorgente per MindTune Lab.

La via sicura e:

1. tenere attivo `quizlet_hebrew_seed.json`;
2. conservare `quizlet_hebrew_audit.csv` come audit grezzo;
3. se si vuole recuperare qualcosa dal lavoro Docker, estrarre solo le traduzioni
   Blue/Purple effettivamente buone, riga per riga;
4. applicare eventuali correzioni solo a `back` e `flags`;
5. non deduplicare globalmente;
6. non toccare mai `front` automaticamente.

## Esito

La documentazione Docker e ordinata ma metodologicamente sbagliata per questo
progetto. Ha creato un report molto sicuro di se, ma non ha rispettato il
contratto operativo.
