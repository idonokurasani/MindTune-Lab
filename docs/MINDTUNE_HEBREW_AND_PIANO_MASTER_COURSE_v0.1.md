# MindTune Lab - corso personale ebraico/pianoforte v0.1

Status: working design, not frozen
Date: 2026-07-15
Owner: Andrea Amarante + Codex

## 1. Principio guida

MindTune Lab non deve piu essere una console piena di prove. Deve diventare un direttore di sessione.

All'apertura l'utente deve rispondere solo a due domande:

1. Cosa facciamo oggi?
   - Ebraico
   - Pianoforte
   - EEG libero
2. Quanto dura?
   - 15, 30, 45, 60 minuti

Il resto lo decide MindTune:

- verifica FC11 e qualita di contatto;
- legge Oura e stato recente;
- esegue un warm-up cognitivo breve;
- sceglie dose, sequenza e difficolta;
- registra EEG + eventi comportamentali;
- salva andamento, errori, tempi e recupero;
- programma re-test e re-entry.

La prestazione osservabile batte sempre il biomarcatore. EEG, Oura, sonno e contesto spiegano la performance; non la sostituiscono.

## 2. Fonti e gerarchia della verita

### 2.1 Ebraico

La gerarchia deve essere rigida:

1. Academy of the Hebrew Language
   - riferimento normativo per ortografia, forme, coniugazioni, declinazioni, termini, dizionario moderno, decisioni grammaticali.
   - uso: normalizzazione e risoluzione dei dubbi.
2. Pealim
   - riferimento pratico per paradigmi verbali e cache morfologica operativa.
   - uso: generazione/validazione dei prompt di coniugazione e domino.
3. Streetwise Hebrew
   - fonte d'uso vivo: collocazioni, registro, fraseologia, ascolto, pronuncia, contesto.
   - uso: enrichment e training contestuale, senza sporcare il corpus canonico.
4. Citizen Cafe
   - corpus personale di re-entry: cio che Andrea ha studiato davvero.
   - uso: recupero di competenze dormienti, memoria episodica, consolidamento.
   - non e fonte normativa.
5. HeLP
   - profiler sperimentale: frequenza, tempi di decisione lessicale, naming, lunghezza, densita ortografica, struttura semitica.
   - uso: stima difficolta, diagnosi errori, scheduling e adattamento.
   - non e contenuto didattico.

### 2.2 Pianoforte

Il Piano Lab non deve diventare una collezione di giochini. Deve misurare cinque stati musicali distinti:

1. Lettura a prima vista.
2. Suonare con spartito.
3. Suonare senza spartito.
4. Ascoltare musica.
5. Immaginare musica nota.

Ogni sessione deve salvare:

- pezzo;
- compositore, se noto;
- stato del pezzo: nuovo, in studio, dormiente, consolidato;
- modalita: vista, spartito, memoria, ascolto, imagery;
- durata;
- errori o blocchi annotati;
- performance soggettiva;
- EEG e contesto Oura.

## 3. Letteratura e principi scientifici da incorporare

Questi principi guidano il design, non sono decorazione.

### 3.1 Apprendimento e memoria

- Retrieval practice: richiamare attivamente batte rileggere.
- Spacing: il richiamo distribuito e piu stabile del ripasso concentrato.
- Interleaving: alternare tipi di prova migliora transfer e discriminazione.
- Desirable difficulty: difficolta moderata, non frustrazione.
- Re-entry: una competenza dormiente va misurata per velocita di riattivazione, non solo per accuratezza.

### 3.2 Second-language acquisition

- Input comprensibile ma non banale.
- Output obbligato: produrre frasi e forme, non solo riconoscere.
- Feedback immediato ma non invasivo.
- Lessico ad alta frequenza prima del lessico raro.
- Collocazioni, registro e contesto prima delle liste isolate.
- Morfologia semitica: radice, binyan, pattern e famiglia lessicale vanno integrati progressivamente.

### 3.3 HeLP come profilatore

HeLP deve contribuire con:

- frequenza e log_frequency: priorita di apprendimento;
- word_length: carico visivo/ortografico;
- orthographic_neighborhood_density: rischio di confusione;
- ld_mean_rt e ld_accuracy: difficolta di riconoscimento lessicale;
- naming_mean_rt e naming_accuracy: difficolta di produzione/lettura;
- semitic_structure e clitic_count: complessita morfologica;
- phonological_entropy: incertezza fonologica.

Uso previsto:

- item con alta frequenza e alta difficolta personale: priorita alta;
- item con alta accuratezza ma tempo lento: fluency training;
- item con errori morfologici ricorrenti: Shoresh/binyan training;
- item gia noto ma decaduto: re-entry;
- item raro e non utile: rinvio.

### 3.4 Pianoforte e neuroscienze della performance

Piano Lab deve distinguere componenti che spesso vengono confuse:

- prima vista: parsing visivo, anticipazione, memoria di lavoro, continuita motoria;
- con spartito: controllo visuo-motorio e correzione online;
- senza spartito: memoria motoria, uditiva, armonica e strutturale;
- ascolto: previsione uditiva, attenzione, memoria della forma;
- imagery: generazione interna del suono e simulazione motoria senza gesto.

La pratica mentale non sostituisce il pianoforte, ma puo rinforzare rappresentazione, continuita, recupero e memoria, soprattutto se confrontata con ascolto reale e performance reale.

## 4. Sessione ebraico - flusso ideale

### 4.1 Avvio

MindTune valuta:

- sonno totale;
- REM/profondo se disponibili;
- readiness;
- stress;
- attivita recente;
- caffeina dichiarata;
- qualita segnale FC11;
- prestazione nel warm-up.

Produce un colore operativo:

- verde: dose alta, nuovo + produzione;
- giallo: consolidamento + poco nuovo;
- arancio: re-entry leggero + ascolto/lettura;
- rosso: mantenimento minimo o solo ascolto;
- calibrazione: dati insufficienti, dose prudente.

### 4.2 Warm-up obbligatorio

Durata: 2-4 minuti.

Componenti:

- Simon direzione: controllo risposta/interferenza;
- Stroop classico: inibizione;
- reaction time o Go/No-Go: velocita/stabilita.

Output:

- tempo medio;
- variabilita;
- errori;
- fatica iniziale;
- confidence score della sessione.

### 4.3 Sequenza ebraico adattiva

La sequenza deve essere scelta da BrainLab in base allo stato.

#### Verde

1. Warm-up.
2. Re-entry Citizen Cafe difficile.
3. Domino verbale da Pealim.
4. Produzione frasi.
5. Streetwise context.
6. Richiamo finale.

#### Giallo

1. Warm-up.
2. Flashcard/re-entry medio.
3. Coniugazioni mirate.
4. Breve ascolto o lettura.
5. Richiamo finale.

#### Arancio

1. Warm-up leggero.
2. Carte ad alta familiarita.
3. Lettura lenta.
4. Ascolto contestuale.
5. Nessun nuovo materiale salvo sorpresa positiva.

#### Rosso

1. Baseline o ascolto breve.
2. 3-5 richiami facili.
3. Stop prima della fatica.

## 5. Esercizio chiave: domino verbale

Obiettivo: trasformare coniugazione in movimento mentale continuo.

Esempio concettuale:

1. "Come si dice: lui mangia?"
   - risposta attesa in ebraico.
2. "Se lui mangia oggi, lei domani...?"
   - risposta in futuro femminile singolare.
3. "Se lei [risposta], loro ieri...?"
   - risposta in passato plurale.
4. Continua con pronome, tempo e avverbio temporale variabili.

Regole:

- tutte le risposte operative in ebraico;
- prompt misti italiano/ebraico solo finche serve;
- progressiva ebraicizzazione dei prompt;
- Pealim/cache come fonte morfologica;
- ogni passaggio salva:
  - verbo;
  - binyan;
  - tempo;
  - persona/genere/numero;
  - risposta;
  - correttezza;
  - tempo;
  - tipo errore;
  - EEG window.

Modalita:

- domino lento: accuratezza prima di velocita;
- domino fluente: tempo massimo per risposta;
- domino re-entry: verbi dormienti;
- domino contrastivo: coppie simili o radici confuse;
- domino produttivo: aggiunta di mini-frase.

## 6. Sessione pianoforte - flusso ideale

### 6.1 Avvio

Stesso avvio di ebraico:

- FC11 stabile;
- Oura;
- warm-up cognitivo breve;
- scelta automatica dose.

### 6.2 I cinque compiti ammessi

#### 1. Lettura a prima vista

Uso:

- pezzo mai visto;
- durata breve;
- continuita piu importante della perfezione.

Metriche:

- tempo di mantenimento;
- blocchi;
- ripartenze;
- autovalutazione;
- eventuale audio futuro.

#### 2. Suonare con spartito

Uso:

- pezzo noto o in studio;
- attenzione a controllo visivo, previsione e correzione.

Metriche:

- stabilita;
- punti di blocco;
- sezione studiata;
- fatica percepita.

#### 3. Suonare senza spartito

Uso:

- memoria del brano;
- recupero di pezzi dormienti;
- controllo del panico da vuoto.

Metriche:

- punto di perdita;
- recupero;
- continuita;
- confidenza.

#### 4. Ascoltare musica

Uso:

- ascolto fermo, senza mani;
- brano noto o appena suonato;
- attenzione a forma, armonia, fraseggio.

Metriche:

- familiarita;
- previsione;
- engagement;
- distrazioni.

#### 5. Immaginare musica nota

Uso:

- dopo ascolto o dopo esecuzione;
- ripetizione mentale di 2-10 minuti;
- corpo fermo.

Metriche:

- continuita dell'immagine sonora;
- vividezza;
- perdita della forma;
- confronto con ascolto reale.

### 6.3 Sequenza consigliata

#### Verde

1. Warm-up.
2. Prima vista.
3. Con spartito.
4. Senza spartito.
5. Ascolto.
6. Imagery.

#### Giallo

1. Warm-up.
2. Con spartito.
3. Senza spartito breve.
4. Ascolto.

#### Arancio

1. Warm-up leggero.
2. Ascolto.
3. Imagery.
4. Una micro-sezione con spartito.

#### Rosso

1. Ascolto o imagery.
2. Stop.

## 7. Memoria longitudinale

Ogni sessione alimenta una memoria personale:

- cosa ho studiato;
- cosa ho ascoltato;
- cosa ho immaginato;
- cosa ho recuperato;
- cosa e decaduto;
- quali condizioni precedono buone prestazioni;
- quale dose migliora senza sovraccaricare.

Metriche longitudinali:

- learning velocity;
- retention index;
- re-entry index;
- fluency index;
- fatigue resistance;
- recovery index;
- confidence score;
- cognitive efficiency: performance / fatica.

## 8. Implementazione a breve termine

### 8.1 App

La schermata iniziale deve guidare:

- ebraico / pianoforte / EEG libero;
- durata;
- stato Oura;
- stato FC11;
- avvio sessione.

I dettagli tecnici restano sotto, ma non devono essere la porta d'ingresso.

### 8.2 Ebraico

Prima versione utile:

- HeLP metrics leggibili dal sistema;
- Citizen Cafe consolidato come re-entry corpus;
- Pealim cache di almeno 60 verbi;
- domino verbale;
- flashcards solo se hanno significato e traduzione controllabili.

### 8.3 Pianoforte

Prima versione utile:

- cinque preset e basta;
- campo pezzo obbligatorio o suggerito;
- salvataggio modalita;
- confronto ascolto reale / imagery;
- report per pezzo.

## 9. Decisione finale

MindTune Lab non deve ottimizzare uno score EEG.

Deve ottimizzare:

- apprendimento;
- recupero di competenze dormienti;
- efficienza cognitiva;
- prestazione reale;
- memoria a lungo termine;
- autonomia.

Il casco e Oura servono per capire in quali condizioni Andrea impara, recupera e performa meglio.

