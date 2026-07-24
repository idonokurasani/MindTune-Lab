# Hebrew Lab 2.0 - Specifica educativa e architetturale

Versione: 0.1
Data: 2026-07-11
Stato: bozza da approvare prima di qualsiasi implementazione
Lingua di mediazione: italiano
Lingua target: ebraico moderno

## 1. Principio guida

Hebrew Lab 2.0 non e' un refactoring delle flashcards.

E' una piattaforma educativa completa per l'ebraico moderno dentro MindTune Lab. Il suo compito e' accompagnare uno studente adulto, gia' alfabetizzato e con conoscenze intermedie, verso una competenza avanzata, professionale e accademica.

La lingua di spiegazione, feedback, traduzione, grammatica, commento e istruzione e' sempre l'italiano. L'ebraico resta la lingua studiata.

Principi non negoziabili:

- la struttura educativa e' stabile;
- BrainLab non modifica mai il curriculum;
- BrainLab personalizza solo tempi, dosi, richiami e carico;
- l'organizzazione per colori viene eliminata;
- la flashcard non e' piu' l'unita' fondamentale;
- l'unita' fondamentale diventa la Learning Unit;
- ogni dato linguistico deve essere verificabile, correggibile e tracciabile;
- performance osservabile e qualita' linguistica hanno priorita' su qualsiasi score biometrico.

## 1B. Fondazioni metodologiche

Il curriculum di Hebrew Lab 2.0 non deve essere inventato da zero. Deve nascere da una sintesi critica delle metodologie piu' solide per l'insegnamento dell'ebraico moderno ad adulti, integrate con ricerca su acquisizione linguistica, memoria, frequenza lessicale e pratica di recupero.

Obiettivo: non copiare un corso esistente, ma estrarre i principi migliori e costruire un percorso nuovo, personale, misurabile e durevole.

### Fonti e approcci da confrontare

#### Modello Ulpan

Punti forti:

- immersione intensiva;
- ritmo quotidiano;
- forte enfasi comunicativa;
- uso rapido della lingua in contesti reali;
- progressione pratica per livelli;
- integrazione di grammatica, ascolto, lettura e conversazione.

Limiti per MindTune Lab:

- spesso ottimizzato per inserimento rapido, non per precisione a lungo termine;
- puo' privilegiare performance immediata rispetto a consolidamento profondo;
- non sempre esplicita abbastanza radici, famiglie lessicali e metacognizione;
- puo' essere troppo lineare per uno studente adulto gia' non principiante.

Decisione progettuale:

Hebrew Lab prende dall'Ulpan intensita', comunicazione e cicli brevi di uso reale, ma aggiunge scheduling adattivo, revisione longitudinale, re-entry e organizzazione per radici/frequenza.

#### Curricula universitari di ebraico moderno

Punti forti:

- progressione grammaticale esplicita;
- attenzione a lettura e scrittura;
- valutazione formale;
- sviluppo di competenze accademiche;
- uso di testi autentici negli stadi avanzati.

Limiti per MindTune Lab:

- ritmo spesso semestrale, non adattivo;
- poco sensibile allo stato fisiologico e cognitivo dello studente;
- valutazione periodica piu' che continua;
- minor granularita' sui tempi di recupero e automatizzazione.

Decisione progettuale:

Hebrew Lab prende dai curricula universitari rigore, competenze scritte, progressione verso registro formale/accademico e valutazione per outcome. Non eredita pero' la rigidita' semestrale: BrainLab gestisce dose, ripasso e re-entry.

#### Manuali riconosciuti di ebraico moderno

Manuali come Hebrew from Scratch, Brandeis Modern Hebrew, Routledge/academic modern Hebrew courses e grammatiche didattiche offrono modelli importanti:

- dialoghi e testi graduati;
- grammatica esplicita;
- vocabolario tematico;
- esercizi produttivi;
- introduzione progressiva di forme verbali e strutture sintattiche.

Limiti:

- molti manuali sono pensati per corsi lineari;
- il lessico e' spesso tematico piu' che rigorosamente frequenziale;
- la revisione distribuita e' lasciata allo studente/docente;
- la relazione radice -> famiglia -> uso reale non sempre diventa principio centrale.

Decisione progettuale:

Hebrew Lab usa i manuali come controllo di plausibilita' didattica: se una struttura o un tipo di esercizio ricorre in piu' manuali seri, probabilmente e' pedagogicamente utile. Tuttavia l'ordine finale deve essere guidato da frequenza, prerequisiti grammaticali, produttivita' della radice e utilita' comunicativa.

#### CEFR e progressione per competenze

Il CEFR non e' specifico per l'ebraico, ma fornisce una cornice utile per descrivere competenze comunicative, ricezione, produzione, interazione e mediazione.

Punti forti:

- orientamento a cosa lo studente sa fare;
- distinzione tra ricezione, produzione, interazione e mediazione;
- descrittori di progressione;
- possibilita' di mappare obiettivi osservabili.

Limiti:

- non cattura automaticamente specificita' semitiche come radici, binyanim, stato costrutto e preposizioni flesse;
- puo' risultare troppo generico se usato da solo.

Decisione progettuale:

Hebrew Lab usa una progressione ispirata al CEFR per gli outcome comunicativi, ma mantiene una struttura interna specifica per ebraico: radici, binyanim, famiglie lessicali, morfologia, registro israeliano moderno.

#### Second Language Acquisition

Principi rilevanti:

- input comprensibile e leggermente sfidante;
- attenzione al significato prima della sola forma;
- produzione guidata;
- feedback correttivo;
- interleaving tra competenze;
- automatizzazione progressiva;
- ruolo della frequenza e dell'esposizione distribuita.

Decisione progettuale:

Ogni Learning Unit deve poter generare piu' tipi di attivita':

- riconoscimento;
- richiamo;
- produzione;
- uso contestuale;
- trasferimento;
- re-entry.

Questo evita che una parola sia "saputa" solo perche' riconosciuta su una carta.

#### Frequenza lessicale e HeLP

Il lessico deve seguire, quando possibile, frequenza reale dell'ebraico moderno. HeLP e risorse simili sono particolarmente utili per:

- frequenza;
- tempi di decisione lessicale;
- accuratezza;
- dati di naming;
- confronto tra forme;
- priorita' di revisione.

Materiale locale gia' disponibile in MindTune Lab:

- `mindtune_console/data/hebrew_verbs_help_forms.csv`: 10.557 forme verbali con collegamenti HeLP dove disponibili;
- `mindtune_console/data/hebrew_verbs_help_audit.csv`: audit su 334 verbi;
- `mindtune_console/data/hebrew_verbs_help_enrichment.json`: sintesi di copertura e note metodologiche.

Decisione progettuale:

HeLP deve essere usato come evidenza lessicale e sperimentale, non come oracolo grammaticale. Una forma non presente in HeLP non e' automaticamente sbagliata; puo' essere rara, flessa, produttiva o assente dal campione. La frequenza guida priorita' e scheduling, non sostituisce la revisione linguistica.

#### Vocabolario, retrieval practice e spaced repetition

La ricerca su apprendimento e memoria sostiene fortemente:

- pratica di recupero;
- ripetizione distribuita;
- test come apprendimento, non solo valutazione;
- spacing adattivo;
- interleaving;
- difficolta' desiderabile, ma non frustrazione costante.

Decisione progettuale:

Hebrew Lab non deve misurare solo "quante parole ho visto". Deve misurare:

- richiamo;
- latenza;
- stabilita' dopo tempo;
- recupero dopo pausa;
- trasferimento in frase;
- errore morfologico;
- errore semantico;
- automatizzazione.

## 1C. Alternative metodologiche e scelte finali

### Organizzazione tematica vs frequenziale

Alternativa A: organizzare per temi, come molti manuali.

Vantaggi:

- piu' naturale per conversazione;
- contesti coerenti;
- facile costruire dialoghi.

Limiti:

- puo' introdurre parole rare troppo presto;
- non massimizza utilita' immediata;
- meno adatta a scheduling quantitativo.

Alternativa B: organizzare per frequenza.

Vantaggi:

- massimizza utilita' comunicativa;
- supporta priorita' oggettive;
- migliora copertura dei testi.

Limiti:

- puo' produrre sequenze poco naturali;
- non basta per imparare uso pragmatico.

Scelta Hebrew Lab:

frequenza come asse primario, topic e contesto come vincoli didattici. Non si studiano liste nude: si studiano unita' frequenti dentro contesti e famiglie.

### Grammatica esplicita vs immersione comunicativa

Alternativa A: grammatica esplicita.

Vantaggi:

- utile per adulti;
- chiarisce pattern;
- importante in ebraico per radici/binyanim.

Limiti:

- rischio di sapere regole senza usarle.

Alternativa B: immersione comunicativa.

Vantaggi:

- facilita automatizzazione;
- aumenta tolleranza all'ambiguita';
- prepara all'uso reale.

Limiti:

- puo' lasciare fossilizzare errori.

Scelta Hebrew Lab:

grammatica esplicita breve + uso immediato + recupero distribuito. Ogni regola deve produrre azione linguistica.

### Flashcards atomiche vs Learning Unit

Alternativa A: flashcard parola-traduzione.

Vantaggi:

- veloce;
- facile da schedulare;
- utile per richiamo iniziale.

Limiti:

- povera semanticamente;
- rischia calchi;
- non misura produzione reale;
- non cattura radici, registro, collocazioni.

Alternativa B: Learning Unit.

Vantaggi:

- supporta parola, frase, radice, ascolto, produzione, lettura;
- collega contenuto e competenza;
- permette esercizi multipli sullo stesso oggetto.

Limiti:

- piu' complessa da modellare.

Scelta Hebrew Lab:

Learning Unit come oggetto principale. La vecchia flashcard diventa solo uno dei possibili "prompt types" generati da una Learning Unit.

### Livelli quantitativi vs livelli competenziali

Alternativa A: livello = numero di parole.

Vantaggi:

- semplice da misurare.

Limiti:

- non dice se lo studente sa usare la lingua;
- incentiva accumulo superficiale.

Alternativa B: livello = competenza.

Vantaggi:

- coerente con CEFR;
- misura funzioni reali;
- collega ricezione e produzione.

Limiti:

- richiede valutazione piu' ricca.

Scelta Hebrew Lab:

livelli competenziali. La quantita' lessicale e' un target, non la definizione del livello.

## 1D. Fonti metodologiche iniziali

Fonti da usare come base e da ampliare nella fase di revisione:

- Council of Europe, CEFR e Companion Volume: https://www.coe.int/en/web/common-european-framework-reference-languages
- Dunlosky et al., 2013, "Improving Students' Learning With Effective Learning Techniques": https://doi.org/10.1177/1529100612453266
- Roediger & Karpicke, 2006, "Test-enhanced learning": https://doi.org/10.1111/j.1467-9280.2006.01693.x
- Cepeda et al., 2006, review su distributed practice: https://doi.org/10.1037/0033-2909.132.3.354
- HeLP / Hebrew Lexicon Project, dati lessicali e sperimentali per ebraico moderno: https://doi.org/10.3758/s13428-024-02502-4

Queste fonti non esauriscono il lavoro. Prima della migrazione reale dei contenuti, ogni modulo dovra' avere una micro-bibliografia propria.

## 2. Architettura educativa

Gerarchia principale:

```text
Curriculum
  -> Livelli
    -> Moduli
      -> Learning Unit
```

La gerarchia e' educativa, non cronologica in senso rigido. Uno studente puo' lavorare su piu' moduli dello stesso livello, ma una Learning Unit mantiene sempre il livello assegnato.

Separazione fondamentale:

```text
Curriculum fisso
  contenuti, livelli, obiettivi, prerequisiti, relazioni linguistiche

Stato personale
  esposizioni, errori, tempi, consolidamento, re-entry, scheduling
```

BrainLab legge lo stato personale e i sensori, ma non riscrive il curriculum.

## 3. Struttura del curriculum

Il curriculum e' organizzato in otto livelli di competenza.

1. Foundation
2. Core
3. Expansion
4. Integration
5. Fluency
6. Advanced
7. Professional
8. Academic

Questi livelli non indicano solo quantita' di parole. Indicano competenze:

- lessico disponibile;
- grammatica controllata;
- velocita' di recupero;
- accuratezza produttiva;
- comprensione di registro;
- lettura;
- ascolto;
- capacita' di produzione orale e scritta;
- autonomia in contesti reali.

## 4. Definizione dei livelli

### Foundation

Obiettivo: consolidare la base gia' acquisita e correggere fragilita' residue.

Lessico: parole comuni, vita quotidiana, azioni concrete, tempo, luogo, persone, oggetti frequenti.

Grammatica: presente, passato e futuro dei verbi comuni; genere e numero; stato costrutto elementare; preposizioni frequenti; pronomi; negazione; domande.

Produzione: frasi semplici ma corrette; descrizioni brevi; domande e risposte immediate.

Ricezione: comprensione di frasi chiare, dialoghi lenti e testi brevi.

Fluenza attesa: recupero non automatico ma stabile.

### Core

Obiettivo: rendere sistematico cio' che lo studente conosce parzialmente.

Lessico: frequenza medio-alta, verbi quotidiani, aggettivi descrittivi, sostantivi funzionali.

Grammatica: uso affidabile dei binyanim piu' frequenti; preposizioni flesse; oggetti diretti; comparativi; subordinate semplici.

Produzione: narrazione breve al passato/futuro; spiegazione di preferenze, intenzioni, necessita'.

Ricezione: testi didattici e conversazioni naturali lente.

Fluenza attesa: risposta con esitazioni moderate, errori ricorrenti identificabili.

### Expansion

Obiettivo: ampliare lessico e strutture verso uso reale.

Lessico: famiglie lessicali, verbi derivati, espressioni idiomatiche frequenti, collocazioni.

Grammatica: alternanza tra binyanim; forme nominali derivate; connettivi; frasi relative; costrutti temporali e causali.

Produzione: spiegare eventi, motivazioni, ipotesi semplici.

Ricezione: articoli semplici, dialoghi autentici, contenuti audio controllati.

Fluenza attesa: buona continuita' su temi noti.

### Integration

Obiettivo: integrare lessico, radici, grammatica e uso pragmatico.

Lessico: lessico tematico maturo, radici produttive, famiglie semantiche.

Grammatica: precisione nei tempi verbali; riconoscimento di registri; uso di forme passive/riflessive dove appropriate.

Produzione: paragrafi coerenti, sintesi, opinioni argomentate.

Ricezione: conversazioni naturali, lettura estensiva, ascolto con ridondanza limitata.

Fluenza attesa: comprensione funzionale e produzione non ancora pienamente automatica.

### Fluency

Obiettivo: aumentare velocita', naturalezza e resistenza cognitiva.

Lessico: alta disponibilita' di parole comuni e medio-frequenti; idiomi frequenti.

Grammatica: automatizzazione delle strutture principali; autocorrezione rapida.

Produzione: conversazione sostenuta; riformulazione; narrazione estesa.

Ricezione: audio autentico con velocita' moderata; testi giornalistici non specialistici.

Fluenza attesa: comunicazione fluida con errori residui.

### Advanced

Obiettivo: portare l'ebraico a livello avanzato generale.

Lessico: argomenti astratti, societa', politica, cultura, psicologia, tecnologia.

Grammatica: costruzioni complesse; nuance aspettuali; registro formale/informale.

Produzione: argomentazione, sintesi critica, scrittura strutturata.

Ricezione: articoli autentici, interviste, podcast, lezioni accessibili.

Fluenza attesa: autonomia ampia, con carico cognitivo ancora misurabile.

### Professional

Obiettivo: usare l'ebraico in contesti professionali.

Lessico: lavoro, comunicazione formale, email, presentazioni, negoziazione, documenti.

Grammatica: accuratezza elevata; formule pragmatiche; stile appropriato al contesto.

Produzione: email professionali, riassunti, presentazioni, spiegazioni tecniche.

Ricezione: riunioni, documenti, istruzioni, contenuti settoriali.

Fluenza attesa: affidabilita' comunicativa in compiti reali.

### Academic

Obiettivo: comprendere e produrre ebraico accademico.

Lessico: lessico astratto, scientifico, argomentativo, critico.

Grammatica: strutture nominali complesse, registro alto, connettivi logici, stile saggistico.

Produzione: abstract, commento critico, esposizione accademica, argomentazione scritta.

Ricezione: articoli, saggi, conferenze, materiale universitario.

Fluenza attesa: competenza alta ma ancora ottimizzabile per dominio.

## 5. Moduli

Ogni livello puo' contenere i seguenti moduli. Non tutti i moduli devono essere presenti con la stessa intensita' in ogni livello.

### Vocabulary

Lessico frequente, collocazioni, sinonimi, contrari, registro, esempi d'uso.

Outcome primari:

- riconoscimento;
- richiamo;
- uso in frase;
- velocita' di recupero;
- stabilita' a distanza.

### Verbs

Verbi come sistemi produttivi: infinito, presente, passato, futuro, imperativo quando utile, reggenze e preposizioni.

Outcome primari:

- coniugazione corretta;
- scelta del tempo;
- traduzione produttiva;
- uso contestuale.

### Roots

Radici e famiglie lessicali.

Esempio:

```text
כתב
  כתב
  כותב
  כתיבה
  מכתב
  להכתיב
  התכתבות
```

Outcome primari:

- riconoscimento della radice;
- collegamento semantico;
- previsione del significato;
- distinzione tra parentela reale e falsa analogia.

### Binyanim

Binyanim come pattern grammaticali e semantici.

Outcome primari:

- riconoscimento del binyan;
- interpretazione della funzione;
- produzione di forme derivate;
- confronto tra forme correlate.

### Reading

Lettura graduata, testi autentici, scansione, comprensione globale e dettagliata.

Outcome primari:

- accuratezza di comprensione;
- tempo di lettura;
- inferenza lessicale;
- resistenza alla fatica.

### Listening

Ascolto graduato e autentico.

Outcome primari:

- discriminazione;
- comprensione globale;
- recupero di parole chiave;
- trascrizione parziale;
- comprensione sotto velocita' naturale.

### Writing

Produzione scritta guidata e libera.

Outcome primari:

- correttezza;
- coerenza;
- registro;
- uso di lessico target;
- autocorrezione.

### Speaking

Produzione orale, lettura ad alta voce, ripetizione, risposta a prompt.

Outcome primari:

- latenza;
- continuita';
- accuratezza;
- naturalezza;
- capacita' di riformulazione.

### Idioms

Espressioni idiomatiche, formule colloquiali, modi di dire.

Outcome primari:

- comprensione pragmatica;
- uso appropriato;
- riconoscimento di registro.

### Israeli Culture

Contesto sociale, culturale, storico e pragmatico.

Outcome primari:

- comprensione di riferimenti culturali;
- registro comunicativo;
- appropriatezza.

### Revision

Richiamo, consolidamento, re-entry, recupero dopo pausa.

Outcome primari:

- retention;
- velocita' di recupero;
- errori residui;
- ritorno al plateau.

### Conversation

Dialoghi, role-play, interazione simulata.

Outcome primari:

- risposta contestuale;
- turn-taking;
- adattamento;
- pragmatica.

## 6. Learning Unit

La Learning Unit sostituisce la flashcard.

Una Learning Unit puo' essere:

- parola;
- frase;
- espressione;
- dialogo;
- esercizio di ascolto;
- esercizio produttivo;
- esercizio grammaticale;
- testo breve;
- famiglia lessicale;
- famiglia di radice;
- pattern di binyan;
- contrasto tra due forme.

Una Learning Unit non e' necessariamente atomica nel senso Anki/Quizlet. Puo' contenere piu' esercizi, ma deve avere un obiettivo educativo chiaro.

### Tipi iniziali di Learning Unit

```text
lexeme
sentence
expression
dialogue
listening_item
production_prompt
grammar_item
reading_item
root_family
lexical_family
binyan_pattern
minimal_pair
reentry_item
```

### Contenuto minimo

Ogni Learning Unit deve contenere:

- testo ebraico;
- spiegazione italiana;
- traduzione italiana se pertinente;
- uno o piu' esempi;
- obiettivo educativo;
- tipo di risposta attesa;
- criteri di valutazione.

## 7. Metadata schema

Schema concettuale minimo:

```json
{
  "id": "he_lu_000001",
  "version": 1,
  "status": "active",
  "language_target": "he",
  "language_mediation": "it",
  "level": "Core",
  "module": "Vocabulary",
  "unit_type": "lexeme",
  "topic": ["vita quotidiana"],
  "hebrew": {
    "text": "לכתוב",
    "normalized": "לכתוב",
    "script": "Hebr",
    "niqqud": false
  },
  "italian": {
    "translation": "scrivere",
    "explanation": "Verbo comune per l'azione di scrivere.",
    "examples": [
      {
        "he": "אני כותב מכתב",
        "it": "Scrivo una lettera"
      }
    ]
  },
  "linguistic": {
    "root": "כתב",
    "binyan": "pa'al",
    "part_of_speech": "verb",
    "lexical_family": "scrittura",
    "frequency_band": "high",
    "register": "neutral",
    "gender": null,
    "number": null,
    "transitivity": "transitive",
    "prepositions": []
  },
  "curriculum": {
    "prerequisites": [],
    "related_units": ["he_lu_000002"],
    "competency_tags": ["verb", "root_awareness", "daily_action"],
    "productive_targets": ["coniugare al presente", "usare in frase"],
    "receptive_targets": ["riconoscere in testo", "riconoscere in ascolto"]
  },
  "quality": {
    "source": "curated",
    "review_status": "verified",
    "reviewer": "human",
    "notes": ""
  }
}
```

### Campi obbligatori

- id
- level
- module
- unit_type
- hebrew.text
- italian.explanation o italian.translation
- topic
- competency_tags
- review_status

### Campi opzionali ma raccomandati

- root
- binyan
- frequency_band
- register
- prerequisites
- related_units
- examples
- source
- reviewer
- quality notes

## 8. Stato personale dello studente

Lo stato personale non vive nella Learning Unit.

Ogni studente ha uno stato separato per ogni Learning Unit.

Stati dinamici:

```text
New
Learning
Consolidated
Automatic
Dormant
Re-entry
Suspended
```

Campi principali:

```json
{
  "student_id": "andrea",
  "learning_unit_id": "he_lu_000001",
  "state": "Learning",
  "first_seen_at": "2026-07-11T08:00:00Z",
  "last_seen_at": "2026-07-11T08:07:00Z",
  "next_due_at": "2026-07-12T08:00:00Z",
  "exposures": 4,
  "correct": 3,
  "partial": 1,
  "miss": 0,
  "mean_reaction_ms": 2100,
  "last_reaction_ms": 1800,
  "retention_score": 0.72,
  "automaticity_score": 0.31,
  "error_patterns": ["tempo verbale", "preposizione"],
  "brainlab": {
    "recommended_review_intensity": "medium",
    "reason": "errore recente + buon recupero fisiologico"
  }
}
```

BrainLab puo' modificare:

- next_due_at;
- review_intensity;
- session dose;
- ordine di presentazione;
- mix tra nuovo e ripasso;
- re-entry scheduling.

BrainLab non puo' modificare:

- level;
- module;
- contenuto ebraico;
- spiegazione italiana;
- prerequisiti;
- struttura curricolare.

## 9. Database model

Modello relazionale proposto, estendibile verso SQLite locale e Raspberry.

### curriculum_levels

- id
- name
- order_index
- description_it
- objectives_it
- vocabulary_targets_it
- grammar_competencies_it
- productive_abilities_it
- receptive_abilities_it
- reading_skills_it
- listening_skills_it
- expected_fluency_it

### curriculum_modules

- id
- name
- description_it
- default_enabled
- order_index

### learning_units

- id
- version
- status
- level_id
- module_id
- unit_type
- topic_json
- hebrew_text
- hebrew_normalized
- italian_translation
- italian_explanation
- examples_json
- root
- binyan
- lexical_family
- part_of_speech
- frequency
- frequency_band
- register
- prerequisites_json
- related_units_json
- competency_tags_json
- source
- review_status
- quality_notes
- created_at
- updated_at

### learning_unit_assets

Per audio, testo lungo, immagini, trascrizioni.

- id
- learning_unit_id
- asset_type
- path_or_url
- local_hash
- language
- transcript_it
- transcript_he
- metadata_json

### student_unit_state

- student_id
- learning_unit_id
- state
- first_seen_at
- last_seen_at
- next_due_at
- exposures
- correct
- partial
- miss
- mean_reaction_ms
- last_reaction_ms
- retention_score
- automaticity_score
- error_patterns_json
- brainlab_recommendation_json

### learning_events

Ogni risposta produce un evento.

- id
- session_id
- student_id
- learning_unit_id
- event_type
- prompt_type
- response_text
- expected_response
- score
- reaction_ms
- correctness
- eeg_session_id
- context_json
- created_at

### sessions

- id
- started_at
- ended_at
- mode
- level_id
- module_id
- eeg_session_id
- oura_context_json
- caffeine_mg
- subjective_state_json
- summary_json

### curriculum_reviews

- id
- learning_unit_id
- reviewer
- decision
- notes
- created_at

## 10. Strategia di migrazione

La migrazione delle flashcards esistenti viene dopo l'approvazione dell'architettura.

Fasi:

### Fase 1 - Freeze

- bloccare il sistema colori come legacy;
- non usarlo per nuove decisioni educative;
- conservare backup integrale;
- nessuna riscrittura automatica distruttiva.

### Fase 2 - Import grezzo

Ogni carta esistente diventa una candidata Learning Unit, non una Learning Unit verificata.

Campi iniziali:

- front -> hebrew_text candidato;
- back -> italian_translation candidata;
- deck colore -> source_legacy;
- stato -> unverified_import.

### Fase 3 - Normalizzazione linguistica

- rimuovere niqqud se non necessario;
- normalizzare spazi e direzione RTL;
- separare parole, frasi, espressioni e verbi;
- identificare doppioni;
- identificare campi vuoti o inutilizzabili.

### Fase 4 - Revisione educativa

Per ogni candidata:

- verificare ebraico;
- verificare italiano;
- assegnare livello;
- assegnare modulo;
- assegnare tipo;
- aggiungere root/binyan dove possibile;
- aggiungere frequenza/register;
- aggiungere esempi;
- decidere se mantenere, riscrivere, fondere o scartare.

### Fase 5 - Promozione

Solo le unita' revisionate diventano Learning Unit attive.

Stati possibili:

```text
active
needs_review
duplicate_candidate
discarded
merged
```

## 11. Strategia di revisione

La revisione deve essere conservativa: meglio poche unita' buone che molte unita' confuse.

Controlli per ogni Learning Unit:

- correttezza ebraica;
- naturalezza ebraica;
- traduzione italiana naturale;
- assenza di calchi inglesi;
- registro;
- frequenza;
- utilita' didattica;
- coerenza col livello;
- relazione con radice/famiglia;
- esempi realistici;
- duplicati o quasi duplicati.

Flags:

```text
verified
needs_italian_review
needs_hebrew_review
needs_frequency_review
needs_level_review
needs_root_review
duplicate_candidate
discard_candidate
academic_later
professional_later
```

Regola importante: non preservare contenuto mediocre solo perche' gia' esiste.

## 12. BrainLab e scheduling adattivo

BrainLab lavora sullo scheduling, non sul curriculum.

Input futuri:

- accuratezza;
- tempo di risposta;
- retention;
- errori;
- re-entry dopo pausa;
- sonno;
- HRV;
- readiness;
- caffeina;
- EEG;
- fatica soggettiva;
- storico personale.

Output:

- oggi ripassa queste unita';
- oggi introduci poche unita' nuove;
- oggi lavora su radici correlate;
- oggi fai solo consolidamento;
- oggi evita materiale nuovo;
- oggi fai re-entry;
- oggi lavora su automatizzazione.

Formula concettuale:

```text
Prossimo carico = funzione(
  performance,
  qualita' dati,
  stato fisiologico,
  storico,
  obiettivo della sessione
)
```

Nessun biomarcatore supera l'outcome comportamentale.

## 13. Tipi di sessione Hebrew Lab 2.0

Sessioni iniziali sensate:

### Richiamo lessicale

Prompt ebraico o italiano, risposta mentale/scritta/orale.

Metriche:

- correttezza;
- tempo;
- grado di sicurezza;
- retention.

### Produzione verbale

Prompt con tempo/persona/contesto.

Metriche:

- forma corretta;
- tempo di risposta;
- errore morfologico;
- errore lessicale.

### Famiglia di radice

Da radice a parole derivate, oppure da parola a radice.

Metriche:

- riconoscimento;
- estensione semantica;
- falsi collegamenti.

### Lettura graduata

Testo breve con obiettivi lessicali e grammaticali.

Metriche:

- tempo lettura;
- comprensione;
- parole inferite;
- carico percepito.

### Ascolto graduato

Audio breve, trascrizione parziale o risposta a domande.

Metriche:

- comprensione;
- parole riconosciute;
- errori fonologici;
- latenza.

### Produzione scritta

Prompt italiano o situazione comunicativa.

Metriche:

- correttezza;
- uso delle unita' target;
- registro;
- lunghezza utile.

### Re-entry

Ripresa di materiale dormiente dopo pausa.

Metriche:

- tempo per recuperare;
- errori iniziali;
- ritorno al plateau;
- resistenza.

## 14. Roadmap di implementazione

### Milestone 1 - Approvazione architettura

Output:

- approvazione o revisione di questo documento;
- decisione sui nomi italiani dei livelli e moduli;
- decisione sul primo livello operativo.

### Milestone 2 - Schema dati locale

Output:

- file schema JSON;
- SQLite locale o JSON versionato;
- separazione curriculum/progress;
- validatore.

### Milestone 3 - UI Hebrew Lab 2.0

Output:

- rimozione visiva del sistema colori;
- navigazione Curriculum -> Livelli -> Moduli -> Learning Unit;
- pannello stato personale;
- pannello sessione.

### Milestone 4 - Primo seed verificato

Output:

- piccolo set Foundation/Core;
- 50-100 Learning Unit curate;
- verbi e radici collegati;
- niente import automatico massivo.

### Milestone 5 - Scheduler BrainLab

Output:

- New/Learning/Consolidated/Automatic;
- scheduling basato su performance;
- re-entry;
- dose giornaliera.

### Milestone 6 - Migrazione legacy controllata

Output:

- conversione candidate;
- revisione manuale/assistita;
- promozione solo delle unita' buone;
- archivio legacy preservato.

### Milestone 7 - Integrazione EEG/Oura

Output:

- eventi Hebrew Lab annotati sulle sessioni EEG;
- contesto fisiologico salvato;
- analisi longitudinali;
- nessuna decisione educativa presa solo da biomarcatori.

## 15. Decisioni da approvare

Prima di implementare serve decidere:

1. Mantenere i nomi inglesi dei livelli o tradurli in italiano?
2. Partire da Foundation/Core o da Core direttamente?
3. Usare SQLite subito o iniziare con JSON versionato e validato?
4. Primo modulo operativo: Vocabulary, Verbs, Roots o Reading?
5. BrainLab scheduling semplice iniziale o gia' con re-entry?

## 16. Raccomandazione iniziale

Proposta conservativa:

1. approvare architettura;
2. creare schema dati;
3. costruire UI minima Hebrew Lab 2.0;
4. seed iniziale Core con:
   - 40 verbi;
   - 40 parole frequenti;
   - 20 unita' root-family;
   - 10 frasi;
5. collegare progress personale;
6. solo dopo migrare il materiale legacy.

Questo evita di trascinare gli errori delle vecchie flashcards dentro una struttura nuova.
