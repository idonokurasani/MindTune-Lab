const els = {
  bridgeLine: document.querySelector("#bridgeLine"),
  lastUpdate: document.querySelector("#lastUpdate"),
  jobCount: document.querySelector("#jobCount"),
  deleteAbortedBtn: document.querySelector("#deleteAbortedBtn"),
  handshakeDumpBtn: document.querySelector("#handshakeDumpBtn"),
  handshakeStartBtn: document.querySelector("#handshakeStartBtn"),
  reconnectDumpBtn: document.querySelector("#reconnectDumpBtn"),
  jobs: document.querySelector("#jobs"),
  console: document.querySelector("#console"),
  logSelect: document.querySelector("#logSelect"),
  copyConsoleBtn: document.querySelector("#copyConsoleBtn"),
  connectSessionBtn: document.querySelector("#connectSessionBtn"),
  startBtn: document.querySelector("#startBtn"),
  stopBtn: document.querySelector("#stopBtn"),
  testFamily: document.querySelector("#testFamily"),
  testPreset: document.querySelector("#testPreset"),
  condition: document.querySelector("#condition"),
  pieceId: document.querySelector("#pieceId"),
  difficulty: document.querySelector("#difficulty"),
  sessionNote: document.querySelector("#sessionNote"),
  sleepHours: document.querySelector("#sleepHours"),
  sleepQuality: document.querySelector("#sleepQuality"),
  exerciseIntensity: document.querySelector("#exerciseIntensity"),
  caffeineCups: document.querySelector("#caffeineCups"),
  caffeineMg: document.querySelector("#caffeineMg"),
  caffeineMgLabel: document.querySelector("#caffeineMgLabel"),
  stressLevel: document.querySelector("#stressLevel"),
  cognitiveEnergy: document.querySelector("#cognitiveEnergy"),
  sessionTimeOfDay: document.querySelector("#sessionTimeOfDay"),
  duration: document.querySelector("#duration"),
  prep: document.querySelector("#prep"),
  guided: document.querySelector("#guided"),
  phaseLabel: document.querySelector("#phaseLabel"),
  countdown: document.querySelector("#countdown"),
  presetHint: document.querySelector("#presetHint"),
  liveFeatureLine: document.querySelector("#liveFeatureLine"),
  waveCanvas: document.querySelector("#waveCanvas"),
  batteryWidget: document.querySelector("#batteryWidget"),
  batteryPct: document.querySelector("#batteryPct"),
  fc11Source: document.querySelector("#fc11Source"),
  helmetLed: document.querySelector("#helmetLed"),
  ouraWidget: document.querySelector("#ouraWidget"),
  ouraSleep: document.querySelector("#ouraSleep"),
  ouraEnergy: document.querySelector("#ouraEnergy"),
  ouraPanel: document.querySelector("#ouraPanel"),
  ouraPanelBody: document.querySelector("#ouraPanelBody"),
  closeOuraPanel: document.querySelector("#closeOuraPanel"),
  dailyMode: document.querySelector("#dailyMode"),
  dailyModeReason: document.querySelector("#dailyModeReason"),
  dailyStateOrb: document.querySelector("#dailyStateOrb"),
  dailySleep: document.querySelector("#dailySleep"),
  dailyReadiness: document.querySelector("#dailyReadiness"),
  dailyEnergy: document.querySelector("#dailyEnergy"),
  adaptivePlanTitle: document.querySelector("#adaptivePlanTitle"),
  adaptivePlanLine: document.querySelector("#adaptivePlanLine"),
  labCards: document.querySelectorAll(".lab-card"),
  durationCards: document.querySelectorAll(".duration-card"),
  guidedLaunchBtn: document.querySelector("#guidedLaunchBtn"),
  guidedStopBtn: document.querySelector("#guidedStopBtn"),
  apkPanel: document.querySelector("#apkPanel"),
  apkSummary: document.querySelector("#apkSummary"),
  apkTaskLabel: document.querySelector("#apkTaskLabel"),
  apkTaskStats: document.querySelector("#apkTaskStats"),
  apkStimulus: document.querySelector("#apkStimulus"),
  apkStimulusText: document.querySelector("#apkStimulusText"),
  apkResponse: document.querySelector("#apkResponse"),
  apkPrimaryBtn: document.querySelector("#apkPrimaryBtn"),
  apkSecondaryBtn: document.querySelector("#apkSecondaryBtn"),
  apkTertiaryBtn: document.querySelector("#apkTertiaryBtn"),
  apkQuaternaryBtn: document.querySelector("#apkQuaternaryBtn"),
  apkEventCount: document.querySelector("#apkEventCount"),
  apkEventList: document.querySelector("#apkEventList"),
  memoryPanel: document.querySelector("#memoryPanel"),
  memoryPanelTitle: document.querySelector("#memoryPanelTitle"),
  memorySummary: document.querySelector("#memorySummary"),
  hebrewRecoveryWorkspace: document.querySelector("#hebrewRecoveryWorkspace"),
  hebrewRecoveryRationale: document.querySelector("#hebrewRecoveryRationale"),
  hebrewRecoveryStatus: document.querySelector("#hebrewRecoveryStatus"),
  hebrewRecoveryEvidence: document.querySelector("#hebrewRecoveryEvidence"),
  hebrewRecoveryPhases: document.querySelector("#hebrewRecoveryPhases"),
  hebrewRecoveryStage: document.querySelector("#hebrewRecoveryStage"),
  hebrewRecoveryStageMoment: document.querySelector("#hebrewRecoveryStageMoment"),
  hebrewRecoveryStageTitle: document.querySelector("#hebrewRecoveryStageTitle"),
  hebrewRecoveryStageProgress: document.querySelector("#hebrewRecoveryStageProgress"),
  hebrewRecoveryStageDescription: document.querySelector("#hebrewRecoveryStageDescription"),
  hebrewRecoveryTaskSurface: document.querySelector("#hebrewRecoveryTaskSurface"),
  hebrewRecoveryStageActions: document.querySelector("#hebrewRecoveryStageActions"),
  flashcardWorkspace: document.querySelector("#flashcardWorkspace"),
  conjugationWorkspace: document.querySelector("#conjugationWorkspace"),
  conjugationPresent: document.querySelector("#conjugationPresent"),
  conjugationPrompt: document.querySelector("#conjugationPrompt"),
  conjugationAnswer: document.querySelector("#conjugationAnswer"),
  conjugationCheckBtn: document.querySelector("#conjugationCheckBtn"),
  conjugationNextBtn: document.querySelector("#conjugationNextBtn"),
  conjugationSpeakBtn: document.querySelector("#conjugationSpeakBtn"),
  conjugationSpeechStatus: document.querySelector("#conjugationSpeechStatus"),
  conjugationFeedback: document.querySelector("#conjugationFeedback"),
  conjugationKeyboard: document.querySelector("#conjugationKeyboard"),
  conjugationKeyboardKeys: document.querySelector("#conjugationKeyboardKeys"),
  conjugationScore: document.querySelector("#conjugationScore"),
  conjugationTimer: document.querySelector("#conjugationTimer"),
  conjugationHistoryCount: document.querySelector("#conjugationHistoryCount"),
  conjugationHistoryList: document.querySelector("#conjugationHistoryList"),
  shoreshWorkspace: document.querySelector("#shoreshWorkspace"),
  shoreshModeLabel: document.querySelector("#shoreshModeLabel"),
  shoreshStatus: document.querySelector("#shoreshStatus"),
  shoreshClock: document.querySelector("#shoreshClock"),
  shoreshPreRatings: document.querySelector("#shoreshPreRatings"),
  shoreshPostRatings: document.querySelector("#shoreshPostRatings"),
  shoreshLucidity: document.querySelector("#shoreshLucidity"),
  shoreshFatigue: document.querySelector("#shoreshFatigue"),
  shoreshFamiliarity: document.querySelector("#shoreshFamiliarity"),
  shoreshEffort: document.querySelector("#shoreshEffort"),
  shoreshFrustration: document.querySelector("#shoreshFrustration"),
  shoreshFocus: document.querySelector("#shoreshFocus"),
  shoreshStimulus: document.querySelector("#shoreshStimulus"),
  shoreshPrompt: document.querySelector("#shoreshPrompt"),
  shoreshOptions: document.querySelector("#shoreshOptions"),
  shoreshStartBtn: document.querySelector("#shoreshStartBtn"),
  shoreshTrainingBtn: document.querySelector("#shoreshTrainingBtn"),
  shoreshSaveBtn: document.querySelector("#shoreshSaveBtn"),
  shoreshProgress: document.querySelector("#shoreshProgress"),
  shoreshMetrics: document.querySelector("#shoreshMetrics"),
  shoreshHistory: document.querySelector("#shoreshHistory"),
  flashcardDeck: document.querySelector("#flashcardDeck"),
  flashcardCatalog: document.querySelector("#flashcardCatalog"),
  flashcardSelectedSummary: document.querySelector("#flashcardSelectedSummary"),
  flashcardCard: document.querySelector("#flashcardCard"),
  flashcardFront: document.querySelector("#flashcardFront"),
  flashcardBack: document.querySelector("#flashcardBack"),
  flashcardMeta: document.querySelector("#flashcardMeta"),
  flashcardScore: document.querySelector("#flashcardScore"),
  flashcardTimer: document.querySelector("#flashcardTimer"),
  streetwisePanel: document.querySelector("#streetwisePanel"),
  streetwiseStatus: document.querySelector("#streetwiseStatus"),
  streetwiseList: document.querySelector("#streetwiseList"),
  helpItemPanel: document.querySelector("#helpItemPanel"),
  helpItemStatus: document.querySelector("#helpItemStatus"),
  helpItemMetrics: document.querySelector("#helpItemMetrics"),
  helpProfilePanel: document.querySelector("#helpProfilePanel"),
  helpProfileSummary: document.querySelector("#helpProfileSummary"),
  helpProfileDimensions: document.querySelector("#helpProfileDimensions"),
  helpProfileNote: document.querySelector("#helpProfileNote"),
  helpRefreshBtn: document.querySelector("#helpRefreshBtn"),
  hebrewKeyboard: document.querySelector("#hebrewKeyboard"),
  hebrewKeyboardKeys: document.querySelector("#hebrewKeyboardKeys"),
  flashcardShowBtn: document.querySelector("#flashcardShowBtn"),
  flashcardKnowBtn: document.querySelector("#flashcardKnowBtn"),
  flashcardHardBtn: document.querySelector("#flashcardHardBtn"),
  flashcardMissBtn: document.querySelector("#flashcardMissBtn"),
  memoryDueCount: document.querySelector("#memoryDueCount"),
  memoryDueList: document.querySelector("#memoryDueList"),
  hebrewMlfWorkspace: document.querySelector("#hebrewMlfWorkspace"),
  hebrewMlfUnit: document.querySelector("#hebrewMlfUnit"),
  hebrewMlfTrialType: document.querySelector("#hebrewMlfTrialType"),
  hebrewMlfStartBtn: document.querySelector("#hebrewMlfStartBtn"),
  hebrewMlfPrompt: document.querySelector("#hebrewMlfPrompt"),
  hebrewMlfPromptArea: document.querySelector("#hebrewMlfPromptArea"),
  hebrewMlfResponse: document.querySelector("#hebrewMlfResponse"),
  hebrewMlfSubmitBtn: document.querySelector("#hebrewMlfSubmitBtn"),
  hebrewMlfResult: document.querySelector("#hebrewMlfResult"),
  hebrewMlfOutcome: document.querySelector("#hebrewMlfOutcome"),
  hebrewMlfFeedback: document.querySelector("#hebrewMlfFeedback"),
  hebrewMlfNormalized: document.querySelector("#hebrewMlfNormalized"),
  hebrewMlfM0State: document.querySelector("#hebrewMlfM0State"),
  hebrewMlfRetests: document.querySelector("#hebrewMlfRetests"),
  hebrewMlfError: document.querySelector("#hebrewMlfError"),
};

let selectedLog = "";
let busy = false;
let macActive = false;
let macPhase = "";
let latestMacState = null;
let autoDetectInFlight = false;
let lastAutoDetectAt = 0;
let currentFlashcard = null;
let flashcardShownAt = 0;
let flashcardAnswerShownAt = 0;
let flashcardRecallElapsedMs = 0;
let flashcardAnswerVisible = false;
let flashcardTimerActive = false;
let flashcardStudyStarted = false;
let flashcardStats = { correct: 0, partial: 0, miss: 0 };
let flashcardCatalog = null;
let selectedFlashcardDecks = new Set();
let importingFlashcardDecks = new Set();
let pendingFlashcardDeck = "";
let pendingNextAfterId = "";
let flashcardSessionOrder = [];
let flashcardSessionSeen = new Set();
let flashcardSessionSignature = "";
let lastFlashcardId = "";
let flashcardSessionReviewedIds = [];
let reviewedFlashcardIds = [];
let reviewedFlashcards = new Map();
let flashcardEditTimers = new WeakMap();
let currentStreetwise = { cardId: "", canonicalItemId: "", loading: false, items: [], totalMatches: 0, resolution: "none" };
let streetwiseRequestToken = 0;
let streetwiseExposureKey = "";
let currentHelpItem = { cardId: "", loading: false, data: null };
let helpItemRequestToken = 0;
let currentHelpProfile = null;
let helpProfileLoading = false;
let helpAdaptivePriorities = new Map();
let currentHebrewRecoveryPlan = null;
let hebrewRecoveryPlanLoading = false;
let hebrewRecoveryFlow = null;
let activeHebrewInput = null;
let currentConjugation = null;
let conjugationDomino = null;
let conjugationPromptStartedAt = Date.now();
let conjugationScore = { correct: 0, miss: 0 };
let conjugationHistory = [];
let conjugationBehavioralSessionId = "";
let conjugationSpeechCapture = null;
let lastConjugationSpeech = null;
let catalogConjugationVerbs = [];
let shoreshCatalog = null;
let shoreshSession = {
  mode: "test",
  phase: "idle",
  sessionId: "",
  startedAt: "",
  baselineUntil: 0,
  itemStartedAt: 0,
  index: 0,
  items: [],
  events: [],
  score: { ok: 0, miss: 0, timeout: 0 },
  timeoutId: 0,
  tickId: 0,
  saved: false,
};
let hebrewMlfSession = {
  sessionId: "",
  studentId: "",
  unitId: "",
  trialType: "",
  prompt: "",
  state: "idle", // idle | prompt | done
};
let hebrewMlfUnits = [];
const HEBREW_MLF_STUDENT_NAME = "Andrea Amarante";
let apkTask = {
  taskId: "",
  taskLabel: "",
  condition: "",
  trial: 0,
  difficulty: 1,
  phase: "idle",
  startedAt: Date.now(),
  stimulusAt: 0,
  timeoutId: 0,
  current: null,
  events: [],
  allEvents: [],
  saved: false,
  score: { ok: 0, miss: 0, falseStart: 0 },
};
let timer = {
  phase: "ready",
  startedAt: 0,
  prep: 0,
  duration: 0,
};
let sessionFlow = {
  armed: false,
  running: false,
  taskStarted: false,
  presetId: "",
  startedAt: 0,
  stopReason: "",
};
let apkSaveInFlight = false;

const STROOP_COLORS = [
  { id: "red", label: "ROSSO", key: "r", css: "#ff5f6d" },
  { id: "green", label: "VERDE", key: "v", css: "#5ef0a8" },
  { id: "yellow", label: "GIALLO", key: "g", css: "#f5d66b" },
  { id: "blue", label: "BLU", key: "b", css: "#69a7ff" },
];

const SIMON_DIRECTIONS = [
  { id: "left", label: "SINISTRA", key: "←", shortcut: "arrowleft" },
  { id: "right", label: "DESTRA", key: "→", shortcut: "arrowright" },
];

const GO_NOGO = {
  goProbability: 0.72,
  responseWindowMs: 900,
  interTrialMs: 240,
};

const VISUAL_GRID = {
  minSize: 4,
  maxSize: 6,
  advanceDelayMs: 420,
};

const TREASURE_TRACKER = {
  minSlots: 6,
  maxSlots: 8,
  revealMs: 950,
  shuffleStepMs: 560,
  answerTimeoutMs: 9000,
  nextDelayMs: 520,
};

const LETTER_RECONSTRUCTION = {
  minLetters: 3,
  maxLetters: 9,
  nextDelayMs: 950,
  fallbackWords: [
    { word: "עברית", meaning: "ebraico", deck: "fallback" },
    { word: "ללמוד", meaning: "studiare", deck: "fallback" },
    { word: "לקרוא", meaning: "leggere", deck: "fallback" },
    { word: "לכתוב", meaning: "scrivere", deck: "fallback" },
    { word: "זיכרון", meaning: "memoria", deck: "fallback" },
  ],
};

const PRESETS = {
  baseline: {
    label: "Baseline",
    tests: [
      { id: "eyes_open", label: "Occhi aperti", condition: "eyes_open", duration: 120, prep: 20, guided: true, hint: "Sguardo stabile, niente telefono." },
      { id: "eyes_closed_alert", label: "Occhi chiusi vigile", condition: "eyes_closed_alert", duration: 120, prep: 20, guided: true, hint: "Occhi chiusi, restare sveglio." },
      { id: "recovery_eyes_open", label: "Recupero", condition: "recovery_eyes_open", duration: 120, prep: 15, guided: true, hint: "Recupero a occhi aperti." },
    ],
  },
  regulation: {
    label: "Regolazione",
    tests: [
      { id: "breathing", label: "Respirazione lenta", condition: "breathing", duration: 180, prep: 30, guided: true, hint: "Respira regolare, senza forzare." },
      { id: "floating", label: "Rilassamento", condition: "floating", duration: 180, prep: 25, guided: true, hint: "Rilassamento vigile, non sonno." },
      { id: "meditation_open_monitoring", label: "Meditazione", condition: "meditation_open_monitoring", duration: 300, prep: 30, guided: true, hint: "Attenzione morbida: nota distrazioni e ritorna." },
      { id: "mantra", label: "Mantra", condition: "mantra", duration: 300, prep: 30, guided: true, hint: "Ripetizione mentale regolare, corpo fermo." },
    ],
  },
  focus: {
    label: "Carico cognitivo",
    tests: [
      { id: "reading", label: "Lettura", condition: "reading", duration: 180, prep: 20, guided: true, hint: "Leggi senza muovere la mandibola." },
      { id: "mental_arithmetic", label: "Calcolo mentale", condition: "mental_arithmetic", duration: 120, prep: 20, guided: true, hint: "Calcolo intenso, corpo fermo." },
      { id: "sustained_attention", label: "Attenzione sostenuta", condition: "sustained_attention", duration: 300, prep: 20, guided: true, hint: "Fissa un punto e mantieni vigilanza stabile." },
    ],
  },
  apk_lab: {
    label: "Test cognitivi",
    apk: true,
    tests: [
      { id: "apk_reaction_time", label: "Reaction Time", condition: "apk_reaction_time", duration: 180, prep: 10, guided: false, hint: "Stimolo semplice: rispondi appena appare." },
      { id: "apk_tachistoscope", label: "Tachistoscopio", condition: "apk_tachistoscope", duration: 180, prep: 10, guided: false, hint: "Stimolo brevissimo, poi risposta e autoverifica." },
      { id: "apk_tachistoscope_adaptive", label: "Tachistoscopio adattivo", condition: "apk_tachistoscope_adaptive", duration: 180, prep: 10, guided: false, hint: "Soglia visiva: la durata si accorcia con risposte corrette e risale con errori." },
      { id: "apk_visual_grid", label: "Griglia attenzione", condition: "visual_attention_grid", duration: 180, prep: 10, guided: false, hint: "Ricerca visiva sequenziale: trova i numeri in ordine, senza saltare passaggi." },
      { id: "apk_stroop_word", label: "Stroop classico", condition: "stroop_color_word", duration: 180, prep: 10, guided: false, hint: "Rispondi al colore della scritta, ignorando la parola." },
      { id: "apk_simon_direction", label: "Simon direzione", condition: "simon_direction", duration: 180, prep: 10, guided: false, hint: "Rispondi alla parola, ignorando la posizione sullo schermo." },
      { id: "apk_go_nogo", label: "Go/No-Go", condition: "go_nogo", duration: 180, prep: 10, guided: false, hint: "Premi solo su GO. Su NO-GO resta fermo." },
      { id: "apk_live_stability", label: "Stabilità live", condition: "live_signal_stability", duration: 180, prep: 10, guided: false, hint: "Feedback lento sulla continuita del segnale, non su uno stato mentale." },
      { id: "apk_motion_guard", label: "Postura ferma", condition: "motion_guard", duration: 180, prep: 10, guided: false, hint: "Controllo movimento: usa l'IMU del casco quando disponibile." },
      { id: "apk_mantra_quiet", label: "Mantra quieto", condition: "apk_mantra_quiet", duration: 300, prep: 15, guided: false, hint: "Focus calmo: segnala distrazioni senza interrompere." },
    ],
  },
  memory: {
    label: "Ebraico moderno",
    hebrew: true,
    tests: [
      { id: "hebrew_recovery", label: "Percorso adattivo", condition: "hebrew_adaptive_recovery", duration: 1800, prep: 15, guided: true, hint: "Recupero avanzato: accesso lessicale, morfologia, comprensione e produzione." },
      { id: "hebrew_conjugations", label: "Domino verbale", condition: "hebrew_conjugations", duration: 180, prep: 15, guided: true, hint: "Trasforma persona e tempo mantenendo il verbo: recupero produttivo continuo." },
      { id: "hebrew_roots", label: "Radici", condition: "hebrew_roots", duration: 180, prep: 15, guided: true, hint: "Riconosci radice, famiglia semantica e forme derivate." },
    ],
  },
  piano: {
    label: "Piano Lab",
    tests: [
      { id: "piano_sight_reading", label: "Lettura a prima vista", condition: "piano_sight_reading", duration: 120, prep: 25, guided: true, hint: "Pezzo mai visto: continuita, errori, tempo e recupero." },
      { id: "piano_score_playing", label: "Suonare con spartito", condition: "piano_score_playing", duration: 180, prep: 20, guided: true, hint: "Pezzo noto o in studio: occhio-spartito, mano, previsione." },
      { id: "piano_memory", label: "Suonare senza spartito", condition: "piano_memory", duration: 180, prep: 20, guided: true, hint: "Memoria motoria, uditiva e strutturale del pezzo." },
      { id: "piano_listening_known", label: "Ascoltare musica", condition: "piano_listening_known", duration: 300, prep: 15, guided: true, hint: "Ascolto fermo: predizione, attenzione, forma, emozione." },
      { id: "piano_imagery", label: "Immaginare musica nota", condition: "piano_imagery", duration: 300, prep: 20, guided: true, hint: "Ripeti mentalmente il brano ascoltato o noto, senza muovere le mani." },
    ],
  },
  protocol: {
    label: "Protocollo",
    tests: [
      { id: "standard_mindtune_10min", label: "Standard 10 min", condition: "standard_mindtune_10min", duration: 600, prep: 30, guided: true, hint: "Baseline, respiro, focus, recupero." },
      { id: "nap_sleep_onset", label: "Nap onset", condition: "nap_sleep_onset", duration: 1200, prep: 30, guided: false, hint: "Sessione lunga: solo dopo preflight BLE." },
    ],
  },
  assessment: {
    label: "Assessment",
    assessment: true,
    tests: [
      { id: "assessment_consistency", label: "Consistency", condition: "assessment_consistency", duration: 180, prep: 15, guided: false, hint: "Reaction time: misura variabilità e stabilità." },
      { id: "assessment_depth", label: "Depth", condition: "assessment_depth", duration: 180, prep: 15, guided: false, hint: "Treasure tracker: accuratezza sotto carico di memoria." },
      { id: "assessment_speed", label: "Speed", condition: "assessment_speed", duration: 180, prep: 15, guided: false, hint: "Go/No-Go: velocità e controllo inibitorio." },
      { id: "assessment_recovery", label: "Recovery", condition: "assessment_recovery", duration: 120, prep: 15, guided: true, hint: "Breathing: recupero post-carico." },
    ],
  },
  program: {
    label: "Programma",
    program: true,
    tests: [
      { id: "program_focus_101", label: "Focus 101", condition: "program_focus_101", duration: 600, prep: 30, guided: true, hint: "Programma guidato: mantra → Stroop → recovery." },
      { id: "program_calm_101", label: "Calm 101", condition: "program_calm_101", duration: 600, prep: 30, guided: true, hint: "Programma guidato: breathing → tracking → mantra." },
    ],
  },
  diagnostics: {
    label: "Diagnostica",
    tests: [
      { id: "artifact", label: "Artefatti", condition: "artifact", duration: 120, prep: 15, guided: true, hint: "Solo per mappare movimenti e rumore." },
    ],
  },
};

const DECK_COLORS = {
  red: "#ff5a76",
  orange: "#ff9c45",
  pink: "#ff7bc8",
  yellow: "#ffe066",
  "light blue": "#71dcff",
  blue: "#5d93ff",
  lime: "#b9ff5c",
  green: "#66e39c",
  "dark green": "#19bf7a",
  turquoise: "#34f0d2",
  indigo: "#8578ff",
  purple: "#c078ff",
};

const HEBREW_KEY_ROWS = [
  ["/", "'", "ק", "ר", "א", "ט", "ו", "ן", "ם", "פ"],
  ["ש", "ד", "ג", "כ", "ע", "י", "ח", "ל", "ך", "ף"],
  ["ז", "ס", "ב", "ה", "נ", "מ", "צ", "ת", "ץ"],
  ["׳", "״", "-", " ", "⌫"],
];

const CONJUGATION_VERBS = [
  {
    infinitive: "לכתוב",
    italianInfinitive: "scrivere",
    present: ["כותב", "כותבת", "כותבים", "כותבות"],
    targets: {
      "בעבר · אני": ["כתבתי", "ho scritto"],
      "בעבר · אתה": ["כתבת", "hai scritto"],
      "בעבר · את": ["כתבת", "hai scritto"],
      "בעבר · הוא": ["כתב", "ha scritto"],
      "בעבר · היא": ["כתבה", "ha scritto"],
      "בעבר · אנחנו": ["כתבנו", "abbiamo scritto"],
      "בעבר · אתם": ["כתבתם", "avete scritto"],
      "בעבר · אתן": ["כתבתן", "avete scritto"],
      "בעבר · הם": ["כתבו", "hanno scritto"],
      "בעבר · הן": ["כתבו", "hanno scritto"],
      "בעתיד · אני": ["אכתוב", "scriverò"],
      "בעתיד · אתה": ["תכתוב", "scriverai"],
      "בעתיד · את": ["תכתבי", "scriverai"],
      "בעתיד · הוא": ["יכתוב", "scriverà"],
      "בעתיד · היא": ["תכתוב", "scriverà"],
      "בעתיד · אנחנו": ["נכתוב", "scriveremo"],
      "בעתיד · אתם": ["תכתבו", "scriverete"],
      "בעתיד · אתן": ["תכתבו", "scriverete"],
      "בעתיד · הם": ["יכתבו", "scriveranno"],
      "בעתיד · הן": ["יכתבו", "scriveranno"],
    },
  },
  {
    infinitive: "לדבר",
    italianInfinitive: "parlare",
    present: ["מדבר", "מדברת", "מדברים", "מדברות"],
    targets: {
      "בעבר · אני": ["דיברתי", "ho parlato"],
      "בעבר · אתה": ["דיברת", "hai parlato"],
      "בעבר · את": ["דיברת", "hai parlato"],
      "בעבר · הוא": ["דיבר", "ha parlato"],
      "בעבר · היא": ["דיברה", "ha parlato"],
      "בעבר · אנחנו": ["דיברנו", "abbiamo parlato"],
      "בעבר · אתם": ["דיברתם", "avete parlato"],
      "בעבר · אתן": ["דיברתן", "avete parlato"],
      "בעבר · הם": ["דיברו", "hanno parlato"],
      "בעבר · הן": ["דיברו", "hanno parlato"],
      "בעתיד · אני": ["אדבר", "parlerò"],
      "בעתיד · אתה": ["תדבר", "parlerai"],
      "בעתיד · את": ["תדברי", "parlerai"],
      "בעתיד · הוא": ["ידבר", "parlerà"],
      "בעתיד · היא": ["תדבר", "parlerà"],
      "בעתיד · אנחנו": ["נדבר", "parleremo"],
      "בעתיד · אתם": ["תדברו", "parlerete"],
      "בעתיד · אתן": ["תדברו", "parlerete"],
      "בעתיד · הם": ["ידברו", "parleranno"],
      "בעתיד · הן": ["ידברו", "parleranno"],
    },
  },
  {
    infinitive: "ללמוד",
    italianInfinitive: "studiare",
    present: ["לומד", "לומדת", "לומדים", "לומדות"],
    targets: {
      "בעבר · אני": ["למדתי", "ho studiato"],
      "בעבר · אתה": ["למדת", "hai studiato"],
      "בעבר · את": ["למדת", "hai studiato"],
      "בעבר · הוא": ["למד", "ha studiato"],
      "בעבר · היא": ["למדה", "ha studiato"],
      "בעבר · אנחנו": ["למדנו", "abbiamo studiato"],
      "בעבר · אתם": ["למדתם", "avete studiato"],
      "בעבר · אתן": ["למדתן", "avete studiato"],
      "בעבר · הם": ["למדו", "hanno studiato"],
      "בעבר · הן": ["למדו", "hanno studiato"],
      "בעתיד · אני": ["אלמד", "studierò"],
      "בעתיד · אתה": ["תלמד", "studierai"],
      "בעתיד · את": ["תלמדי", "studierai"],
      "בעתיד · הוא": ["ילמד", "studierà"],
      "בעתיד · היא": ["תלמד", "studierà"],
      "בעתיד · אנחנו": ["נלמד", "studieremo"],
      "בעתיד · אתם": ["תלמדו", "studierete"],
      "בעתיד · אתן": ["תלמדו", "studierete"],
      "בעתיד · הם": ["ילמדו", "studieranno"],
      "בעתיד · הן": ["ילמדו", "studieranno"],
    },
  },
];

function params() {
  const preset = activePreset();
  const condition = preset.condition || els.condition.value || preset.id || "session";
  els.condition.value = condition;
  const payload = {
    condition,
    duration: Number(els.duration.value || 120),
    prep: Number(els.prep.value || 20),
    guided: els.guided.checked,
    piece_id: els.pieceId.value.trim(),
    difficulty: Number(els.difficulty.value || 0),
    session_note: els.sessionNote.value.trim(),
    session_covariates: collectSessionCovariates(),
  };
  if (preset.id === "hebrew_recovery") {
    payload.study_context = selectedTaskContext();
  } else if (preset.id === "hebrew_flashcards") {
    payload.study_context = selectedTaskContext();
  } else if (preset.id === "hebrew_conjugations") {
    payload.study_context = selectedTaskContext();
  } else if (preset.id === "hebrew_roots") {
    payload.study_context = selectedTaskContext();
  } else if (preset.id.startsWith("apk_")) {
    payload.study_context = selectedTaskContext();
  }
  return payload;
}

function collectSessionCovariates() {
  const oura = (_lastOuraData && _lastOuraData.data) || {};
  const caffeineMg = syncCaffeineMgFromCups();
  return {
    sleep_h: Number(oura.sleep_duration_h ?? els.sleepHours.value ?? 0),
    sleep_quality: Number(els.sleepQuality.value || 0) || null,
    sleep_score: Number.isFinite(oura.sleep_score) ? Math.round(oura.sleep_score) : null,
    rem_h: Number.isFinite(oura.rem_h) ? oura.rem_h : null,
    deep_h: Number.isFinite(oura.deep_h) ? oura.deep_h : null,
    light_h: Number.isFinite(oura.light_h) ? oura.light_h : null,
    readiness_score: Number.isFinite(oura.readiness_score) ? Math.round(oura.readiness_score) : null,
    activity_score: Number.isFinite(oura.activity_score) ? Math.round(oura.activity_score) : null,
    steps: Number.isFinite(oura.steps) ? Math.round(oura.steps) : null,
    exercise_intensity: els.exerciseIntensity.value || oura.exercise_intensity || "none",
    caffeine_espresso: Number(els.caffeineCups?.value || 0),
    caffeine_mg: caffeineMg,
    caffeine_mg_per_espresso: CAFFEINE_MG_PER_ESPRESSO,
    stress_level: Number(els.stressLevel.value || 0) || (oura.stress_level ?? null),
    stress_summary: oura.stress_summary || null,
    cognitive_energy: Number(els.cognitiveEnergy.value || 0) || null,
    time_of_day: els.sessionTimeOfDay.value || "afternoon",
    oura_day: _lastOuraData?.day || null,
  };
}

function memoryParams() {
  return {
    deck: els.flashcardDeck.value.trim() || "Ebraico moderno",
  };
}

function activePreset() {
  const family = PRESETS[els.testFamily.value] || Object.values(PRESETS)[0];
  return family.tests.find((test) => test.id === els.testPreset.value) || family.tests[0];
}

function formatTime(totalSeconds) {
  const seconds = Math.max(0, Math.ceil(totalSeconds));
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

function renderBattery(percent, isLive = false) {
  const value = Number(percent);
  const known = Boolean(isLive && Number.isFinite(value) && value > 0);
  const clamped = known ? Math.max(0, Math.min(100, Math.round(value))) : null;
  const level = !known ? 0 : clamped > 66 ? 3 : clamped > 33 ? 2 : clamped > 0 ? 1 : 0;

  els.batteryWidget.className = `battery-widget level-${level}${known ? "" : " unknown"}`;
  els.batteryPct.textContent = known ? `${clamped}%` : "--%";
  els.batteryWidget.title = known ? `Batteria casco ${clamped}%` : "Batteria casco non letta";
}

function renderHelmetLed(mac) {
  if (!els.helmetLed) return;
  let color = (mac && mac.led_color) || "";
  let pattern = "";
  if (!color) {
    const phase = (mac && mac.phase) || "";
    const battery = mac && mac.battery_percent;
    const lowBattery = Number.isFinite(battery) && battery > 0 && battery < 3;
    if (lowBattery) {
      color = "red";
      pattern = "flash";
    } else if (phase === "error" || phase === "interrupted") {
      color = "red";
    } else if (["scan", "connecting", "ble_link", "handshake_sent"].includes(phase)) {
      color = "blue";
      pattern = "pulse";
    } else if (["connected", "starting", "prep", "recording"].includes(phase)) {
      color = "white";
    } else {
      color = "off";
    }
  }
  els.helmetLed.className = `helmet-led led-${color}${pattern ? " led-" + pattern : ""}`;
  els.helmetLed.title = `LED casco: ${color}${pattern ? " " + pattern : ""}`;
}

let _lastOuraData = null;
const CAFFEINE_MG_PER_ESPRESSO = 65;

function syncCaffeineMgFromCups() {
  const cups = Math.max(0, Number(els.caffeineCups?.value || 0));
  const mg = Math.round(cups * CAFFEINE_MG_PER_ESPRESSO);
  if (els.caffeineMg) els.caffeineMg.value = String(mg);
  if (els.caffeineMgLabel) els.caffeineMgLabel.textContent = `${mg} mg caffeina`;
  return mg;
}

function classifyDailyMode(data = null) {
  const d = data || (_lastOuraData && _lastOuraData.data) || {};
  const sleepH = Number(d.sleep_duration_h);
  const readiness = Number(d.readiness_score);
  const energy = Number(d.cognitive_energy);
  const sleepScore = Number(d.sleep_score);
  const usableSleep = Number.isFinite(sleepH) ? sleepH : null;
  const usableReadiness = Number.isFinite(readiness) ? readiness : null;
  const usableEnergy = Number.isFinite(energy) ? energy : Number.isFinite(sleepScore) ? sleepScore : null;
  let score = 0;
  if (usableSleep != null) score += usableSleep >= 7 ? 2 : usableSleep >= 6 ? 1 : usableSleep >= 5 ? 0 : -2;
  if (usableReadiness != null) score += usableReadiness >= 82 ? 2 : usableReadiness >= 70 ? 1 : usableReadiness >= 58 ? 0 : -2;
  if (usableEnergy != null) score += usableEnergy >= 78 ? 2 : usableEnergy >= 64 ? 1 : usableEnergy >= 50 ? 0 : -1;
  if (usableSleep == null && usableReadiness == null && usableEnergy == null) {
    return {
      mode: "calibrazione",
      tone: "neutral",
      title: "Calibrazione",
      reason: "Dati fisiologici non ancora disponibili: usa warm-up breve e giudizio prudente.",
      dose: "Dose prudente",
    };
  }
  if (score >= 4) return {
    mode: "green",
    tone: "green",
    title: "Giornata verde",
    reason: "Buona finestra per produzione, prima vista, nuovo materiale e retest impegnativi.",
    dose: "Dose alta",
  };
  if (score >= 1) return {
    mode: "yellow",
    tone: "yellow",
    title: "Giornata gialla",
    reason: "Meglio consolidare, aggiungere poco nuovo e controllare la fatica durante la sessione.",
    dose: "Dose media",
  };
  if (score >= -2) return {
    mode: "orange",
    tone: "orange",
    title: "Giornata arancio",
    reason: "Punta su re-entry, richiami facili, ascolto o pratica lenta. Niente eroismi.",
    dose: "Dose bassa",
  };
  return {
    mode: "red",
    tone: "red",
    title: "Giornata rossa",
    reason: "Fai solo mantenimento leggero o ascolto: oggi il dato serve a capire il recupero.",
    dose: "Micro-dose",
  };
}

function helpPlanSummary() {
  const evidence = currentHelpProfile?.evidence || {};
  const observed = Number(evidence.eligible_observation_count || 0);
  const required = Number(evidence.minimum_policy?.observations || 8);
  if (evidence.status === "preliminary") {
    const priorities = Number(currentHelpProfile?.adaptive_candidates?.length || 0);
    return priorities
      ? `HeLP segnala ${priorities} elementi da consolidare.`
      : "HeLP non rileva oggi priorità lessicali sopra soglia.";
  }
  return `HeLP in calibrazione: ${observed}/${required} osservazioni affidabili.`;
}

function updateDailyCommand(data = null) {
  const d = data || (_lastOuraData && _lastOuraData.data) || {};
  const mode = classifyDailyMode(d);
  if (els.dailyMode) els.dailyMode.textContent = mode.title;
  if (els.dailyModeReason) els.dailyModeReason.textContent = mode.reason;
  if (els.dailyStateOrb) els.dailyStateOrb.dataset.tone = mode.tone;
  if (els.dailySleep) {
    const sleep = Number(d.sleep_duration_h);
    els.dailySleep.textContent = Number.isFinite(sleep) ? `${sleep.toFixed(1)}h` : "--";
  }
  if (els.dailyReadiness) {
    const readiness = Number(d.readiness_score);
    els.dailyReadiness.textContent = Number.isFinite(readiness) ? Math.round(readiness) : "--";
  }
  if (els.dailyEnergy) {
    const energy = Number(d.cognitive_energy);
    const fallback = Number(d.sleep_score);
    els.dailyEnergy.textContent = Number.isFinite(energy) ? Math.round(energy) : Number.isFinite(fallback) ? Math.round(fallback) : "--";
  }
  if (els.adaptivePlanTitle) els.adaptivePlanTitle.textContent = `${mode.dose}: scegli il laboratorio giusto`;
  if (els.adaptivePlanLine) {
    const family = PRESETS[els.testFamily?.value];
    const lab = family?.label || "sessione";
    const profileLine = els.testFamily?.value === "memory" ? ` ${helpPlanSummary()}` : "";
    els.adaptivePlanLine.textContent = `${lab}: ${activePreset().hint || "misura performance, contesto e memoria nel tempo."}${profileLine}`;
  }
}

function guidedPlanForFamily(familyId) {
  if (familyId === "memory") {
    return {
      title: "Ebraico avanzato: attivazione, re-entry, produzione",
      line: "HeLP ricostruisce il profilo; Pealim alimenta il domino produttivo; radici, comprensione viva e produzione orale completano il recupero.",
      note: "re-entry ebraico · prestazione misurata",
      piece: "hebrew_adaptive_reentry",
      difficulty: 6,
    };
  }
  if (familyId === "piano") {
    return {
      title: "Piano performance: attivazione, prima vista, memoria",
      line: "Warm-up cognitivo-motorio, poi lettura, repertorio dormiente, imagery e controllo della fatica.",
      note: "piano lab · prima vista / memoria",
      piece: "piano_adaptive_session",
      difficulty: 7,
    };
  }
  if (familyId === "baseline") {
    return {
      title: "EEG libero: baseline, regolazione, osservazione",
      line: "Sessione pulita per guardare il segnale, respirazione, recupero o esplorazione senza compito specifico.",
      note: "eeg libero · baseline",
      piece: "free_eeg",
      difficulty: 3,
    };
  }
  return {
    title: "Attivazione cognitiva",
    line: "Simon, Stroop e controllo inibitorio per calibrare la giornata prima del lavoro principale.",
    note: "attivazione cognitiva",
    piece: "activation",
    difficulty: 5,
  };
}

function selectGuidedPath(familyId, presetId = "") {
  if (!PRESETS[familyId] || !els.testFamily || !els.testPreset) return;
  els.testFamily.value = familyId;
  populatePresets();
  const preset = PRESETS[familyId].tests.find((item) => item.id === presetId) || PRESETS[familyId].tests[0];
  els.testPreset.value = preset.id;
  applyPreset(preset);
  resetLocalTimerDisplay(preset);
  const plan = guidedPlanForFamily(familyId);
  if (els.sessionNote) els.sessionNote.value = plan.note;
  if (els.pieceId) els.pieceId.value = plan.piece;
  if (els.difficulty) els.difficulty.value = String(plan.difficulty);
  if (els.adaptivePlanTitle) els.adaptivePlanTitle.textContent = plan.title;
  if (els.adaptivePlanLine) els.adaptivePlanLine.textContent = plan.line;
  els.labCards?.forEach((button) => {
    button.classList.toggle("is-selected", button.dataset.family === familyId);
  });
  if (preset.id === "hebrew_recovery") resetHebrewRecoveryFlow();
  renderMemory(window.latestMemoryState);
}

function setGuidedDuration(seconds) {
  const value = Math.max(300, Number(seconds) || 1800);
  if (els.duration) els.duration.value = String(value);
  els.durationCards?.forEach((button) => {
    button.classList.toggle("is-selected", Number(button.dataset.duration) === value);
  });
  resetLocalTimerDisplay({ ...activePreset(), duration: value });
  if (activePreset().id === "hebrew_recovery") {
    currentHebrewRecoveryPlan = null;
    loadHebrewRecoveryPlan(true);
  }
}

function showOuraDataPanel() {
  if (!els.ouraPanel || !els.ouraPanelBody) return;
  els.ouraPanel.classList.remove("hidden");
  renderOuraPanel(_lastOuraData);
}
window.showOuraDataPanel = showOuraDataPanel;

function closeOuraDataPanel() {
  if (els.ouraPanel) els.ouraPanel.classList.add("hidden");
}

function renderOuraPanel(result) {
  if (!els.ouraPanelBody) return;
  if (!result || !result.ok || !result.data) {
    const checked = (result?.checked_paths || []).map((path) => `<li>${escapeHtml(path)}</li>`).join("");
    els.ouraPanelBody.innerHTML = `
      <p>${escapeHtml(result?.error || "Dati Oura non disponibili")}</p>
      ${result?.token_file ? `<p class="oura-note">Token letto da: ${escapeHtml(result.token_file)}</p>` : ""}
      ${checked ? `<details class="oura-details"><summary>Percorsi controllati</summary><ul>${checked}</ul></details>` : ""}
    `;
    return;
  }
  const d = result.data;
  const fmt = (v, suffix = "") => (v != null && v !== "" ? `${v}${suffix}` : "--");
  const score = (v) => (v != null ? Math.round(v) : "--");
  const row = (label, value, suffix = "") => `
    <tr><th>${escapeHtml(label)}</th><td>${escapeHtml(fmt(value, suffix))}</td></tr>
  `;
  const scoreClass = (value) => {
    const number = Number(value);
    if (!Number.isFinite(number)) return "neutral";
    if (number >= 80) return "good";
    if (number >= 65) return "ok";
    return "low";
  };
  const metricCard = (value, label, suffix = "") => `
    <div class="oura-metric">
      <span class="oura-metric-value">${escapeHtml(fmt(value, suffix))}</span>
      <span class="oura-metric-label">${escapeHtml(label)}</span>
    </div>
  `;
  const scoreCard = (value, label) => `
    <div class="oura-score-card ${scoreClass(value)}">
      <span class="oura-score-value">${escapeHtml(score(value))}</span>
      <span class="oura-score-label">${escapeHtml(label)}</span>
    </div>
  `;
  const sleepTotal = Number(d.sleep_duration_h || 0) + Number(d.awake_h || 0);
  const segmentPct = (value, total) => {
    const number = Number(value);
    const denom = Number(total);
    if (!Number.isFinite(number) || !Number.isFinite(denom) || denom <= 0) return "0%";
    return `${Math.max(0, Math.min(100, (number / denom) * 100)).toFixed(1)}%`;
  };
  const activityTotal = Number(d.low_activity_min || 0)
    + Number(d.medium_activity_min || 0)
    + Number(d.high_activity_min || 0)
    + Number(d.inactive_min || 0)
    + Number(d.resting_min || 0);
  const barValue = (value, max = 100) => {
    const number = Number(value);
    const denom = Number(max);
    if (!Number.isFinite(number) || !Number.isFinite(denom) || denom <= 0) return "0%";
    return `${Math.max(4, Math.min(100, (number / denom) * 100)).toFixed(1)}%`;
  };
  const sleepChart = `
    <div class="oura-chart-card">
      <h3>Architettura sonno</h3>
      <div class="oura-sleep-bar">
        <span class="rem" style="width:${segmentPct(d.rem_h, sleepTotal)}"></span>
        <span class="deep" style="width:${segmentPct(d.deep_h, sleepTotal)}"></span>
        <span class="light" style="width:${segmentPct(d.light_h, sleepTotal)}"></span>
        <span class="awake" style="width:${segmentPct(d.awake_h, sleepTotal)}"></span>
      </div>
      <div class="oura-legend">
        <span><b class="rem"></b>REM ${escapeHtml(fmt(d.rem_h, "h"))}</span>
        <span><b class="deep"></b>Profondo ${escapeHtml(fmt(d.deep_h, "h"))}</span>
        <span><b class="light"></b>Leggero ${escapeHtml(fmt(d.light_h, "h"))}</span>
        <span><b class="awake"></b>Veglia ${escapeHtml(fmt(d.awake_h, "h"))}</span>
      </div>
    </div>
  `;
  const activityChart = `
    <div class="oura-chart-card">
      <h3>Carico attività</h3>
      <div class="oura-bars">
        <span><b style="height:${barValue(d.high_activity_min, activityTotal)}"></b><em>alta</em></span>
        <span><b style="height:${barValue(d.medium_activity_min, activityTotal)}"></b><em>media</em></span>
        <span><b style="height:${barValue(d.low_activity_min, activityTotal)}"></b><em>bassa</em></span>
        <span><b style="height:${barValue(d.inactive_min, activityTotal)}"></b><em>fermo</em></span>
      </div>
    </div>
  `;
  const recoveryChart = `
    <div class="oura-chart-card">
      <h3>Recupero</h3>
      <div class="oura-recovery">
        <span style="--value:${barValue(d.readiness_score, 100)}"><b>Readiness</b><em>${escapeHtml(score(d.readiness_score))}</em></span>
        <span style="--value:${barValue(d.sleep_score, 100)}"><b>Sonno</b><em>${escapeHtml(score(d.sleep_score))}</em></span>
        <span style="--value:${barValue(d.activity_score, 100)}"><b>Attività</b><em>${escapeHtml(score(d.activity_score))}</em></span>
      </div>
    </div>
  `;
  const section = (title, body, tone = "") => `
    <section class="oura-section ${tone}">
      <h3>${escapeHtml(title)}</h3>
      ${body}
    </section>
  `;
  const apiRows = Object.entries(result.api_status || {}).map(([name, status]) => `
    <span class="oura-status ${status.ok ? "ok" : "miss"}">${escapeHtml(name)} ${status.ok ? "ok" : "no"}</span>
  `).join("");
  const contributorRows = Object.entries(d.contributors || {}).flatMap(([group, values]) => (
    Object.entries(values || {}).map(([name, value]) => `
      <tr><th>${escapeHtml(group)} · ${escapeHtml(name)}</th><td>${escapeHtml(fmt(value))}</td></tr>
    `)
  )).join("");
  const allMetricsRows = Object.entries(d.all_metrics || {})
    .filter(([, value]) => value !== null && value !== "" && typeof value !== "object")
    .sort(([a], [b]) => a.localeCompare(b))
    .slice(0, 180)
    .map(([name, value]) => `<tr><th>${escapeHtml(name)}</th><td>${escapeHtml(fmt(value))}</td></tr>`)
    .join("");
  const sleepRows = [
    row("Totale", d.sleep_duration_h, "h"),
    row("REM", d.rem_h, "h"),
    row("Profondo", d.deep_h, "h"),
    row("Leggero", d.light_h, "h"),
    row("Veglia", d.awake_h, "h"),
    row("Tempo a letto", d.time_in_bed_h, "h"),
    row("Latenza", d.latency_min, " min"),
    row("Efficienza", d.efficiency, "%"),
  ].join("");
  const activityRows = [
    row("Passi", d.steps),
    row("Calorie attive", d.active_calories),
    row("Calorie totali", d.total_calories),
    row("Attività bassa", d.low_activity_min, " min"),
    row("Attività media", d.medium_activity_min, " min"),
    row("Attività alta", d.high_activity_min, " min"),
    row("Inattività", d.inactive_min, " min"),
    row("Riposo", d.resting_min, " min"),
  ].join("");
  const cardioStressRows = [
    row("Stress", d.stress_summary || d.stress_level),
    row("FC media sonno", d.sleep_average_hr),
    row("FC minima sonno", d.sleep_lowest_hr),
    row("HRV media", d.sleep_average_hrv),
    row("Respiro medio", d.sleep_average_breath),
    row("Temperatura", d.temperature_deviation),
  ].join("");
  els.ouraPanelBody.innerHTML = `
    <div class="oura-hero">
      <div>
        <span class="oura-eyebrow">Oura · ${escapeHtml(result.day || d.day || "--")}</span>
        <h3>Stato fisiologico prima della sessione</h3>
      </div>
      <div class="oura-score-strip">
        ${scoreCard(d.readiness_score, "Readiness")}
        ${scoreCard(d.sleep_score, "Sonno")}
        ${scoreCard(d.activity_score, "Attività")}
      </div>
    </div>

    <div class="oura-priority-grid">
      ${metricCard(d.sleep_duration_h, "Sonno", "h")}
      ${metricCard(d.rem_h, "REM", "h")}
      ${metricCard(d.deep_h, "Profondo", "h")}
      ${metricCard(d.sleep_average_hrv, "HRV")}
      ${metricCard(d.stress_summary || d.stress_level, "Stress")}
      ${metricCard(d.steps, "Passi")}
    </div>

    ${d.bedtime_start || d.bedtime_end ? `
      <div class="oura-timeline">
        <span>Sonno: ${escapeHtml(d.bedtime_start || "--")}</span>
        <span>Risveglio: ${escapeHtml(d.bedtime_end || "--")}</span>
      </div>
    ` : ""}

    <div class="oura-manual-card">
      <div>
        <span class="oura-eyebrow">Dato manuale sessione</span>
        <h3>Espresso</h3>
      </div>
      <label>
        <input id="ouraCaffeineCupsPanel" type="number" min="0" max="12" step="0.5" value="${escapeHtml(els.caffeineCups?.value || "0")}">
        <small id="ouraCaffeineMgPanel">${escapeHtml(els.caffeineMgLabel?.textContent || "0 mg caffeina")}</small>
      </label>
    </div>

    <div class="oura-chart-grid">
      ${sleepChart}
      ${activityChart}
      ${recoveryChart}
    </div>

    <div class="oura-section-grid">
      ${section("Sonno", `<table class="oura-table compact"><tbody>${sleepRows}</tbody></table>`, "sleep")}
      ${section("Attività", `<table class="oura-table compact"><tbody>${activityRows}</tbody></table>`, "activity")}
      ${section("Stress e cardio", `<table class="oura-table compact"><tbody>${cardioStressRows}</tbody></table>`, "stress")}
    </div>

    ${contributorRows ? `
      <details class="oura-details">
        <summary>Contributors Oura</summary>
        <table class="oura-table"><tbody>${contributorRows}</tbody></table>
      </details>
    ` : ""}
    <details class="oura-details">
      <summary>Stato API e token</summary>
      <div class="oura-status-row">
        ${result.token_file ? `<span>Token: ${escapeHtml(result.token_file)}</span>` : ""}
        ${apiRows}
      </div>
    </details>
    ${allMetricsRows ? `
      <details class="oura-details">
        <summary>Tutti i campi ricevuti</summary>
        <table class="oura-table"><tbody>${allMetricsRows}</tbody></table>
      </details>
    ` : ""}
  `;
  const panelCaffeine = document.querySelector("#ouraCaffeineCupsPanel");
  const panelCaffeineLabel = document.querySelector("#ouraCaffeineMgPanel");
  if (panelCaffeine) {
    panelCaffeine.addEventListener("input", () => {
      if (els.caffeineCups) els.caffeineCups.value = panelCaffeine.value;
      const mg = syncCaffeineMgFromCups();
      if (panelCaffeineLabel) panelCaffeineLabel.textContent = `${mg} mg caffeina`;
    });
  }
}

if (els.closeOuraPanel) els.closeOuraPanel.addEventListener("click", closeOuraDataPanel);
if (els.ouraPanel) {
  els.ouraPanel.addEventListener("click", (e) => {
    if (e.target === els.ouraPanel || e.target.classList.contains("oura-panel-backdrop")) closeOuraDataPanel();
  });
}

async function fetchOuraDaily() {
  if (!els.ouraWidget) return;
  try {
    const response = await fetch("/api/oura_daily", { cache: "no-store" });
    const result = await response.json();
    if (result.needs_auth) {
      els.ouraWidget.className = "oura-pill oura-missing";
      els.ouraSleep.textContent = "Oura ⚠";
      els.ouraEnergy.textContent = "";
      els.ouraWidget.title = "Clicca per autorizzare Oura";
      els.ouraWidget.style.cursor = "pointer";
      els.ouraWidget.onclick = async () => {
        try {
          const res = await fetch("/api/oura_auth_url", { cache: "no-store" });
          const data = await res.json();
          if (data.auth_url) window.location.href = data.auth_url;
          else alert("Errore Oura: " + (data.error || "nessun URL"));
        } catch (exc) {
          alert("Errore rete: " + exc);
        }
      };
      updateDailyCommand(null);
      return;
    }
    _lastOuraData = result;
    els.ouraWidget.style.cursor = "pointer";
    els.ouraWidget.onclick = showOuraDataPanel;
    if (!result.ok || !result.data) {
      els.ouraWidget.className = "oura-pill oura-missing";
      els.ouraSleep.textContent = "scollegata";
      els.ouraEnergy.textContent = "";
      els.ouraWidget.title = result.error || "Oura: dati non disponibili";
      updateDailyCommand(null);
      return;
    }
    const d = result.data;
    const sleepScore = Number.isFinite(d.sleep_score) ? Math.round(d.sleep_score) : null;
    const sleepH = Number.isFinite(d.sleep_duration_h) ? d.sleep_duration_h : null;
    const energy = Number.isFinite(d.cognitive_energy) ? Math.round(d.cognitive_energy) : null;
    els.ouraWidget.className = "oura-pill oura-ok";
    els.ouraSleep.textContent = sleepH != null ? `${sleepH}h` : sleepScore != null ? `Sonno ${sleepScore}` : "collegata";
    els.ouraEnergy.textContent = [
      d.rem_h != null ? `REM ${d.rem_h}h` : "",
      d.deep_h != null ? `Deep ${d.deep_h}h` : "",
      energy != null ? `R ${energy}` : "",
      d.activity_score != null ? `A ${Math.round(d.activity_score)}` : "",
    ].filter(Boolean).join(" · ");
    const details = [];
    if (sleepH != null) details.push(`${sleepH}h`);
    if (d.deep_h != null) details.push(`deep ${d.deep_h}h`);
    if (d.rem_h != null) details.push(`REM ${d.rem_h}h`);
    els.ouraWidget.title = `Oura ${result.day}${details.length ? " · " + details.join(" · ") : ""}`;
    if (els.sleepHours && sleepH != null) els.sleepHours.value = sleepH;
    if (els.sleepQuality && sleepScore != null) {
      const quality = Math.max(1, Math.min(7, Math.round(sleepScore / 100 * 6) + 1));
      els.sleepQuality.value = String(quality);
    }
    if (els.cognitiveEnergy && energy != null) {
      const energyLevel = Math.max(1, Math.min(7, Math.round(energy / 100 * 6) + 1));
      els.cognitiveEnergy.value = String(energyLevel);
    }
    if (els.stressLevel && d.stress_level != null) {
      els.stressLevel.value = String(Math.max(1, Math.min(7, d.stress_level)));
    }
    if (els.exerciseIntensity && d.exercise_intensity) {
      const intensityMap = { none: "none", light: "light", moderate: "moderate", vigorous: "vigorous" };
      els.exerciseIntensity.value = intensityMap[d.exercise_intensity] || "none";
    }
    if (els.sessionTimeOfDay) {
      const hour = new Date().getHours();
      let tod = "night";
      if (hour >= 5 && hour < 12) tod = "morning";
      else if (hour >= 12 && hour < 18) tod = "afternoon";
      else if (hour >= 18 && hour < 22) tod = "evening";
      els.sessionTimeOfDay.value = tod;
    }
    updateDailyCommand(d);
  } catch (exc) {
    els.ouraWidget.className = "oura-pill oura-missing";
    els.ouraSleep.textContent = "errore";
    els.ouraEnergy.textContent = "";
    els.ouraWidget.title = String(exc);
    updateDailyCommand(null);
  }
}

function formatFeaturePct(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return "--";
  return `${Math.round(number * 100)}%`;
}

function renderLiveFeatures(mac) {
  if (!els.liveFeatureLine) return;
  const features = mac && mac.live_features;
  const livePhases = new Set(["prep", "recording"]);
  if (!features || !features.ok || !livePhases.has((mac && mac.phase) || "")) {
    els.liveFeatureLine.textContent = "";
    els.liveFeatureLine.classList.remove("warn");
    renderLiveStabilityStimulus(null);
    renderMotionGuardStimulus(null);
    renderStabilityBalloonStimulus(null);
    return;
  }
  const saturation = Number(features.saturation_pct || 0);
  const gaps = Number(features.packet_index_gaps || 0);
  const contact = features.contact_state ? ` · contatto ${features.contact_state}` : "";
  const warning = saturation > 1 || gaps > 0 || features.contact_state === "bad";
  els.liveFeatureLine.classList.toggle("warn", warning);
  els.liveFeatureLine.textContent = [
    `QC live ${Number(features.window_s || 0).toFixed(1)}s`,
    `RMS ${Math.round(Number(features.rms || 0))} ADC`,
    `p-p ${Math.round(Number(features.peak_to_peak || 0))} ADC`,
    `alpha ${formatFeaturePct(features.alpha_rel)}`,
    Number.isFinite(Number(features.alpha_peak_hz)) ? `picco α candidato ${Number(features.alpha_peak_hz).toFixed(1)}Hz` : "",
    `low/high β ${formatFeaturePct(features.low_beta_rel)}/${formatFeaturePct(features.high_beta_rel)}`,
    Number.isFinite(Number(features.imu_motion_energy)) ? `mov ${Math.round(Number(features.imu_motion_energy))}` : "",
    Number(features.blink_proxy || 0) > 0 ? `blink ${features.blink_proxy}` : "",
    Number(features.noise_spike_count || 0) > 0 ? `spike ${features.noise_spike_count}` : "",
    gaps ? `gap ${gaps}` : "",
    saturation > 0 ? `sat ${saturation.toFixed(1)}%` : "",
  ].filter(Boolean).join(" · ") + contact;
  updateZoneBiofeedback(features);
  renderLiveStabilityStimulus(features);
  renderMotionGuardStimulus(features);
  renderStabilityBalloonStimulus(features);
}

function liveStabilityScore(features) {
  if (!features || !features.ok) return 0;
  let score = 1;
  const saturation = Number(features.saturation_pct || 0);
  const gaps = Number(features.packet_index_gaps || 0);
  const p2p = Number(features.peak_to_peak || 0);
  if (features.contact_state === "bad") score -= 0.55;
  if (features.contact_state === "partial_or_unknown") score -= 0.25;
  if (gaps > 0) score -= Math.min(0.45, gaps * 0.12);
  if (saturation > 0) score -= Math.min(0.45, saturation / 8);
  if (p2p > 7000) score -= 0.25;
  return Math.max(0, Math.min(1, score));
}

function renderLiveStabilityStimulus(features) {
  if (effectiveApkTaskKind() !== "apk_live_stability" || !els.apkStimulus) return;
  const score = liveStabilityScore(features);
  const hasLive = Boolean(features && features.ok);
  els.apkStimulus.style.setProperty("--live-score", score.toFixed(3));
  if (!hasLive) {
    els.apkStimulusText.textContent = "In attesa EEG";
    return;
  }
  const label = score > 0.78 ? "STABILE" : score > 0.48 ? "USABILE" : "RUMORE";
  els.apkStimulusText.textContent = label;
}

function motionGuardScore(features) {
  const motion = Number(features && features.imu_motion_energy);
  if (!Number.isFinite(motion)) return null;
  const scaled = Math.log10(1 + Math.max(0, motion));
  return Math.max(0, Math.min(1, 1 - (scaled / 5)));
}

function renderMotionGuardStimulus(features) {
  if (effectiveApkTaskKind() !== "apk_motion_guard" || !els.apkStimulus) return;
  const score = motionGuardScore(features);
  const hasLive = Boolean(features && features.ok && score !== null);
  els.apkStimulus.style.setProperty("--motion-score", hasLive ? score.toFixed(3) : "0");
  if (!hasLive) {
    els.apkStimulusText.textContent = "In attesa IMU";
    return;
  }
  const motion = Math.round(Number(features.imu_motion_energy || 0));
  const label = score > 0.72 ? "FERMO" : score > 0.48 ? "MICRO-MOVIMENTO" : "MOVIMENTO";
  els.apkStimulusText.textContent = `${label} · ${motion}`;
}

function renderStabilityBalloonStimulus(features) {
  if (effectiveApkTaskKind() !== "apk_stability_balloon" || !els.apkStimulus) return;
  const score = liveStabilityScore(features);
  const hasLive = Boolean(features && features.ok);
  const y = 82 - (score * 58);
  els.apkStimulus.style.setProperty("--balloon-y", `${Math.max(18, Math.min(82, y)).toFixed(1)}%`);
  els.apkStimulus.style.setProperty("--live-score", score.toFixed(3));
  if (!hasLive) {
    els.apkStimulusText.textContent = "In attesa EEG";
    return;
  }
  const zone = apkTask.zone || {};
  const inZoneS = Math.round(Number(zone.inZoneMs || 0) / 1000);
  const outZoneS = Math.round(Number(zone.outZoneMs || 0) / 1000);
  els.apkStimulusText.textContent = score > 0.78
    ? `IN ZONA · ${inZoneS}s`
    : `FUORI ZONA · ${outZoneS}s`;
}

function updateZoneBiofeedback(features) {
  const kind = effectiveApkTaskKind();
  if (kind !== "apk_stability_balloon" && kind !== "apk_live_stability") return;
  const now = Date.now();
  apkTask.zone = apkTask.zone || {
    inZoneMs: 0,
    outZoneMs: 0,
    lastAt: 0,
    lastState: null,
    lastEmitAt: 0,
    sampleCount: 0,
    lastScore: 0,
  };
  if (!features || !features.ok) {
    apkTask.zone.lastAt = 0;
    return;
  }
  const score = liveStabilityScore(features);
  const state = score > 0.78 ? "in_zone" : "out_of_zone";
  const delta = apkTask.zone.lastAt ? Math.max(0, Math.min(2500, now - apkTask.zone.lastAt)) : 0;
  if (delta) {
    if (state === "in_zone") apkTask.zone.inZoneMs += delta;
    else apkTask.zone.outZoneMs += delta;
  }
  apkTask.zone.lastAt = now;
  apkTask.zone.lastScore = Number(score.toFixed(3));
  apkTask.zone.sampleCount += 1;
  apkTask.trial = apkTask.zone.sampleCount;
  apkTask.score.ok = Math.round(apkTask.zone.inZoneMs / 1000);
  apkTask.score.miss = Math.round(apkTask.zone.outZoneMs / 1000);
  if (apkTask.zone.lastState !== state || now - Number(apkTask.zone.lastEmitAt || 0) > 5000) {
    apkTask.zone.lastState = state;
    apkTask.zone.lastEmitAt = now;
    pushApkEvent(state === "in_zone" ? "zone_enter_or_hold" : "zone_exit_or_hold", {
      correct: state === "in_zone",
      live_score: Number(score.toFixed(3)),
      zone_state: state,
      in_zone_s: Math.round(apkTask.zone.inZoneMs / 1000),
      out_zone_s: Math.round(apkTask.zone.outZoneMs / 1000),
      rms: features.rms,
      peak_to_peak: features.peak_to_peak,
      saturation_pct: features.saturation_pct,
      packet_index_gaps: features.packet_index_gaps,
      contact_state: features.contact_state,
      source_pattern: "vendor_zone_progression",
    });
  } else {
    updateApkSessionFields();
  }
  if (els.apkTaskStats) {
    els.apkTaskStats.textContent = `${Math.round(apkTask.zone.inZoneMs / 1000)}s in zona · ${Math.round(apkTask.zone.outZoneMs / 1000)}s fuori · score ${Number(apkTask.zone.lastScore || 0).toFixed(2)}`;
  }
}

function setSourceState(source, state) {
  if (!source) return;
  source.classList.remove("active", "searching", "pending");
  source.classList.add(state);
}

function setButtonState(button, label, stateClass = "") {
  button.textContent = label;
  button.classList.remove("connecting", "connected");
  if (stateClass) {
    button.classList.add(stateClass);
  }
}

function reflectExportStatus(text) {
  if (!text || !/export_raspberry/i.test(selectedLog || "")) {
    return;
  }
  if (text.includes("EXPORT_OK")) {
    els.bridgeLine.textContent = "Export Raspberry riuscito · sessioni verificate e rimosse dal Mac";
    els.bridgeLine.style.color = "var(--accent)";
    const exportBtn = document.querySelector("#exportBtn");
    exportBtn.textContent = "Export OK";
    exportBtn.classList.add("connected");
    setTimeout(() => {
      exportBtn.textContent = "Esporta RPi";
      exportBtn.classList.remove("connected");
    }, 4500);
    return;
  }
  if (text.includes("ERRORE:")) {
    els.bridgeLine.textContent = "Export Raspberry non completato · file locali preservati";
    els.bridgeLine.style.color = "var(--danger)";
  }
}

function updateConnectionControls(mac) {
  const phase = (mac && mac.phase) || "";
  const running = Boolean(mac && mac.running);
  const syncGuidedLaunch = () => {
    if (!els.guidedLaunchBtn) return;
    els.guidedLaunchBtn.disabled = Boolean(els.startBtn.disabled);
    const isSessionBusy = ["starting", "prep", "recording"].includes(macPhase || phase);
    els.guidedLaunchBtn.textContent = isSessionBusy ? "Sessione in corso" : "Avvia sessione";
    els.guidedLaunchBtn.title = els.startBtn.title || "";
  };

  if (!running) {
    setButtonState(els.connectSessionBtn, "Connetti");
    els.startBtn.disabled = true;
    syncGuidedLaunch();
    return;
  }

  if (phase === "scan" || phase === "connecting") {
    setButtonState(els.connectSessionBtn, "In corso...", "connecting");
    els.startBtn.disabled = true;
    syncGuidedLaunch();
    return;
  }

  if (phase === "ble_link" || phase === "handshake_sent") {
    setButtonState(els.connectSessionBtn, "Verifica...", "connecting");
    els.startBtn.disabled = true;
    syncGuidedLaunch();
    return;
  }

  if (phase === "connected") {
    setButtonState(els.connectSessionBtn, "Connesso", "connected");
    const contactBad = mac && ["bad", "partial_or_unknown"].includes(mac.contact_state || "");
    els.startBtn.disabled = Boolean(busy || contactBad);
    els.startBtn.title = contactBad ? "Casco collegato ma contatto non pronto: indossalo o sistema gli elettrodi." : "";
    syncGuidedLaunch();
    return;
  }

  if (phase === "starting" || phase === "prep" || phase === "recording") {
    setButtonState(els.connectSessionBtn, "In corso...", "connected");
    els.startBtn.disabled = true;
    syncGuidedLaunch();
    return;
  }

  if (phase === "error") {
    setButtonState(els.connectSessionBtn, "Errore", "connecting");
    els.startBtn.disabled = true;
    syncGuidedLaunch();
    return;
  }

  if (phase === "interrupted") {
    setButtonState(els.connectSessionBtn, "Connetti");
    els.startBtn.disabled = true;
    syncGuidedLaunch();
    return;
  }

  setButtonState(els.connectSessionBtn, "In corso...", "connecting");
  els.startBtn.disabled = true;
  syncGuidedLaunch();
}

function populateFamilies() {
  els.testFamily.innerHTML = Object.entries(PRESETS)
    .map(([id, family]) => `<option value="${id}">${family.label}</option>`)
    .join("");
  els.testFamily.value = PRESETS.memory ? "memory" : "baseline";
  populatePresets();
}

function populatePresets() {
  const family = PRESETS[els.testFamily.value];
  els.testPreset.innerHTML = family.tests
    .map((test) => `<option value="${test.id}">${test.label}</option>`)
    .join("");
  applyPreset(family.tests[0]);
}

function resetLocalTimerDisplay(test = activePreset()) {
  timer = {
    phase: "ready",
    startedAt: 0,
    prep: Number(test.prep || 0),
    duration: Number(test.duration || 0),
  };
  els.phaseLabel.textContent = test.label;
  els.countdown.textContent = formatTime(test.duration);
}

function resetStudyState({ clearDecks = false } = {}) {
  stopIntegratedTask("reset");
  sessionFlow = {
    armed: false,
    running: false,
    taskStarted: false,
    presetId: "",
    startedAt: 0,
    stopReason: "reset",
  };
  currentConjugation = null;
  conjugationDomino = null;
  conjugationScore = { correct: 0, miss: 0 };
  conjugationHistory = [];
  conjugationBehavioralSessionId = "";
  stopConjugationSpeechCapture({ discard: true });
  lastConjugationSpeech = null;
  setConjugationSpeechStatus("");
  renderConjugationStats();
  renderConjugationHistory();
  els.conjugationTimer.textContent = "0.0s";
  els.conjugationFeedback.hidden = true;
  els.conjugationAnswer.value = "";
  flashcardStats = { correct: 0, partial: 0, miss: 0 };
  currentFlashcard = null;
  pendingNextAfterId = "";
  pendingFlashcardDeck = "";
  resetFlashcardSessionOrder();
  flashcardSessionReviewedIds = [];
  flashcardTimerActive = false;
  flashcardStudyStarted = false;
  flashcardShownAt = 0;
  flashcardAnswerShownAt = 0;
  flashcardRecallElapsedMs = 0;
  flashcardAnswerVisible = false;
  renderFlashcardScore();
  renderFlashcardTimer();
  resetShoreshSession();
  resetApkTask();
  if (clearDecks) {
    selectedFlashcardDecks = new Set();
    updateFlashcardDeckSummary();
  }
  selectFlashcard(null);
  updateTaskControlState();
}

function applyPreset(test = activePreset()) {
  const allPresetLabels = Object.values(PRESETS).flatMap((family) => family.tests.map((item) => item.label));
  const previousNote = els.sessionNote.value.trim();
  els.condition.value = test.condition;
  els.duration.value = test.duration;
  els.prep.value = test.prep;
  els.guided.checked = test.guided;
  els.presetHint.textContent = test.hint;
  if (els.testFamily.value === "piano" && (!previousNote || allPresetLabels.includes(previousNote))) {
    els.sessionNote.value = test.label;
  }
  if (els.testFamily.value === "memory") {
    const pieceDefaults = {
      hebrew_recovery: "hebrew_adaptive_recovery",
      hebrew_conjugations: "hebrew_conjugations",
      hebrew_roots: "hebrew_roots",
    };
    if (pieceDefaults[test.id]) els.pieceId.value = pieceDefaults[test.id];
    if (!previousNote || previousNote === "prima vista, mai ascoltato" || allPresetLabels.includes(previousNote)) {
      els.sessionNote.value = test.label;
    }
  }
  if (timer.phase === "ready" || timer.phase === "done") {
    els.phaseLabel.textContent = test.label;
    els.countdown.textContent = formatTime(test.duration);
  }
  updateFlashcardVisibility();
  if (test.id === "hebrew_flashcards") updateFlashcardSessionFields();
  if (test.id === "hebrew_mlf_b2_7") loadHebrewMlfUnits();
}

// ---------------------------------------------------------------------------
// MLF B2.7 Hebrew vertical-slice UI
// ---------------------------------------------------------------------------

async function loadHebrewMlfUnits() {
  if (!els.hebrewMlfUnit) return;
  try {
    const response = await fetch("/api/mlf/hebrew/units", { cache: "no-store" });
    const data = await response.json();
    hebrewMlfUnits = (data.units || []).filter((u) => u.allowed_trial_types && u.allowed_trial_types.length);
    const current = els.hebrewMlfUnit.value;
    els.hebrewMlfUnit.innerHTML = '<option value="">Scegli un\'unità</option>' +
      hebrewMlfUnits.map((u) => {
        const hebrew = u.canonical ? ` · ${u.canonical}` : "";
        const label = `${u.italian || u.canonical}${hebrew}`;
        return `<option value="${escapeHtml(u.unit_id)}">${escapeHtml(label)}</option>`;
      }).join("");
    if (current && hebrewMlfUnits.some((u) => u.unit_id === current)) {
      els.hebrewMlfUnit.value = current;
    }
  } catch (error) {
    if (els.hebrewMlfError) {
      els.hebrewMlfError.hidden = false;
      els.hebrewMlfError.textContent = "Errore caricamento unità MLF.";
    }
  }
}

function currentHebrewMlfUnit() {
  const unitId = els.hebrewMlfUnit?.value || hebrewMlfSession.unitId || "";
  return hebrewMlfUnits.find((u) => u.unit_id === unitId) || null;
}

function hebrewMlfSessionContext() {
  const unit = currentHebrewMlfUnit();
  return {
    family: "hebrew_modern",
    test: "hebrew_mlf_b2_7",
    domain_system: "mlf_hebrew_modern",
    primary_outcomes: ["response_accuracy", "retrieval_state", "scheduled_retest"],
    mlf_domain_id: "hebrew",
    mlf_adapter: "HebrewDomainAdapter",
    mlf_scorer: "HebrewScorer",
    student_name: HEBREW_MLF_STUDENT_NAME,
    student_id: hebrewMlfSession.studentId || "",
    mlf_session_id: hebrewMlfSession.sessionId || "",
    mlf_unit_id: hebrewMlfSession.unitId || unit?.unit_id || "",
    mlf_trial_type: hebrewMlfSession.trialType || els.hebrewMlfTrialType?.value || "recall",
    unit_label: unit ? (unit.italian || unit.canonical || "") : "",
    review_status: unit?.display_status || "technical_preview",
    session_covariates: collectSessionCovariates(),
    source: "mindtune_mlf_hebrew_b2_7",
  };
}

function postHebrewMlfEegEvent(eventType, extra = {}) {
  postEegTaskEvent({
    annotation_type: "mlf_hebrew_event",
    event: {
      event_type: eventType,
      task_id: "hebrew_mlf_b2_7",
      t_ms: sessionFlow.startedAt ? Date.now() - sessionFlow.startedAt : 0,
      ...extra,
    },
    study_context: hebrewMlfSessionContext(),
  });
}

async function startHebrewMlfSession(options = {}) {
  if (!els.hebrewMlfUnit || !els.hebrewMlfTrialType) return;
  if (hebrewMlfSession.state === "prompt") {
    showHebrewMlfError("Sessione MLF già avviata: invia la risposta o premi Stop.");
    return;
  }
  const unitId = els.hebrewMlfUnit.value;
  const trialType = els.hebrewMlfTrialType.value;
  if (!unitId || !trialType) {
    showHebrewMlfError("Seleziona un'unità e un tipo di prova.");
    return;
  }
  clearHebrewMlfResult();
  try {
    const response = await fetch("/api/mlf/hebrew/session/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ unit_id: unitId, trial_type: trialType, student_name: HEBREW_MLF_STUDENT_NAME }),
    });
    const data = await response.json();
    if (!data.ok) {
      showHebrewMlfError(data.error || "Errore avvio sessione");
      return;
    }
    hebrewMlfSession = {
      sessionId: data.session_id,
      studentId: data.student_id,
      unitId: data.unit_id,
      trialType: data.trial_type,
      prompt: data.prompt,
      state: "prompt",
    };
    if (els.hebrewMlfPrompt) els.hebrewMlfPrompt.textContent = data.prompt || "---";
    if (els.hebrewMlfPromptArea) els.hebrewMlfPromptArea.hidden = false;
    if (els.hebrewMlfResponse) {
      els.hebrewMlfResponse.value = "";
      els.hebrewMlfResponse.disabled = false;
      els.hebrewMlfResponse.focus();
    }
    if (els.hebrewMlfSubmitBtn) els.hebrewMlfSubmitBtn.disabled = false;
    postHebrewMlfEegEvent("mlf_session_start", {
      session_id: data.session_id,
      student_id: data.student_id,
      unit_id: data.unit_id,
      trial_id: data.trial_id,
      trial_type: data.trial_type,
      prompt: data.prompt || "",
      started_from_eeg: Boolean(options.fromEeg),
    });
  } catch (error) {
    showHebrewMlfError(error.message || "Errore rete");
  }
}

async function submitHebrewMlfResponse() {
  if (!hebrewMlfSession.sessionId || !els.hebrewMlfResponse) return;
  const raw = els.hebrewMlfResponse.value;
  if (!raw.trim()) {
    showHebrewMlfError("Inserisci una risposta.");
    return;
  }
  if (els.hebrewMlfSubmitBtn) els.hebrewMlfSubmitBtn.disabled = true;
  if (els.hebrewMlfResponse) els.hebrewMlfResponse.disabled = true;
  try {
    const response = await fetch("/api/mlf/hebrew/session/respond", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: hebrewMlfSession.sessionId, response: raw }),
    });
    const data = await response.json();
    if (!data.ok) {
      showHebrewMlfError(data.error || "Errore invio risposta");
      if (els.hebrewMlfResponse) els.hebrewMlfResponse.disabled = false;
      if (els.hebrewMlfSubmitBtn) els.hebrewMlfSubmitBtn.disabled = false;
      return;
    }
    hebrewMlfSession.state = "done";
    renderHebrewMlfResult(data);
    postHebrewMlfEegEvent("mlf_trial_result", {
      session_id: data.session_id,
      student_id: data.student_id,
      unit_id: data.unit_id,
      trial_id: data.trial_id,
      raw_response: data.raw_response || raw,
      normalized_response: data.normalized_response || "",
      outcome: data.outcome || "unknown",
      correct: data.outcome === "correct",
      feedback: data.feedback || "",
      m0_state: data.m0_state || {},
      retest_count: Array.isArray(data.retests) ? data.retests.length : 0,
      warnings: data.warnings || {},
    });
    await loadHelpProfile();
  } catch (error) {
    showHebrewMlfError(error.message || "Errore rete");
    if (els.hebrewMlfResponse) els.hebrewMlfResponse.disabled = false;
    if (els.hebrewMlfSubmitBtn) els.hebrewMlfSubmitBtn.disabled = false;
  }
}

function renderHebrewMlfResult(data) {
  if (els.hebrewMlfPromptArea) els.hebrewMlfPromptArea.hidden = true;
  if (els.hebrewMlfResult) els.hebrewMlfResult.hidden = false;
  if (els.hebrewMlfOutcome) {
    els.hebrewMlfOutcome.className = `hebrew-mlf-outcome outcome-${data.outcome}`;
    els.hebrewMlfOutcome.textContent = `Esito: ${data.outcome}`;
  }
  if (els.hebrewMlfFeedback) els.hebrewMlfFeedback.textContent = data.feedback || "";
  if (els.hebrewMlfNormalized) els.hebrewMlfNormalized.textContent = `Normalizzata: ${data.normalized_response || ""}`;
  if (els.hebrewMlfM0State) {
    const m0 = data.m0_state || {};
    els.hebrewMlfM0State.textContent = `M0: competence=${m0.competence ?? "-"}, count=${m0.count ?? "-"}`;
  }
  if (els.hebrewMlfRetests) {
    const retests = data.retests || [];
    if (retests.length) {
      els.hebrewMlfRetests.innerHTML = "<strong>Retest attivi:</strong>" +
        retests.map((r) => `<div>• ${escapeHtml(r.horizon)} — ${escapeHtml(r.state || "")} (${new Date(r.scheduled_at).toLocaleString()})</div>`).join("");
    } else {
      els.hebrewMlfRetests.textContent = "Nessun retest attivo.";
    }
  }
}

function showHebrewMlfError(message) {
  if (!els.hebrewMlfError) return;
  els.hebrewMlfError.hidden = false;
  els.hebrewMlfError.textContent = message;
}

function clearHebrewMlfResult() {
  if (els.hebrewMlfError) els.hebrewMlfError.hidden = true;
  if (els.hebrewMlfResult) els.hebrewMlfResult.hidden = true;
  if (els.hebrewMlfPrompt) els.hebrewMlfPrompt.textContent = "---";
  if (els.hebrewMlfPromptArea) els.hebrewMlfPromptArea.hidden = true;
  if (els.hebrewMlfResponse) els.hebrewMlfResponse.value = "";
  if (els.hebrewMlfSubmitBtn) els.hebrewMlfSubmitBtn.disabled = true;
}

function updateFlashcardVisibility() {
  const family = PRESETS[els.testFamily.value];
  const test = activePreset();
  const isHebrew = Boolean(family && (family.hebrew || family.flashcards));
  const isApk = Boolean(family && (family.apk || family.assessment || family.program));
  const isFlashcards = isHebrew && test.id === "hebrew_flashcards";
  const isRecovery = isHebrew && test.id === "hebrew_recovery";
  const isConjugations = isHebrew && test.id === "hebrew_conjugations";
  const isShoresh = isHebrew && test.id === "hebrew_roots";
  const isMlfHebrew = isHebrew && test.id === "hebrew_mlf_b2_7";
  els.apkPanel.hidden = !isApk;
  els.memoryPanel.hidden = !isFlashcards && !isRecovery && !isConjugations && !isShoresh && !isMlfHebrew;
  if (els.hebrewRecoveryWorkspace) els.hebrewRecoveryWorkspace.hidden = !isRecovery;
  els.flashcardWorkspace.hidden = !isFlashcards;
  els.conjugationWorkspace.hidden = !isConjugations && !(isRecovery && hebrewRecoveryFlow?.phase === "domino");
  if (els.shoreshWorkspace) els.shoreshWorkspace.hidden = !isShoresh;
  if (els.hebrewMlfWorkspace) els.hebrewMlfWorkspace.hidden = !isMlfHebrew;
  if (els.helpProfilePanel) els.helpProfilePanel.hidden = !isHebrew;
  els.memoryPanelTitle.textContent = isRecovery ? "Percorso di recupero" : isConjugations ? "Domino verbale" : isShoresh ? "Shoresh Lab" : isMlfHebrew ? "Ebraico MLF" : "Ebraico moderno";
  if (isApk) {
    renderApkTask();
  }
  if (isRecovery) {
    els.memorySummary.textContent = "prima → lavoro → dopo";
    if (!hebrewRecoveryFlow) resetHebrewRecoveryFlow();
  } else if (isConjugations) {
    els.memorySummary.textContent = "presente → passato/futuro";
    if (!currentConjugation) {
      nextConjugationPrompt();
    }
  }
  if (isRecovery && !currentHebrewRecoveryPlan && !hebrewRecoveryPlanLoading) loadHebrewRecoveryPlan();
  if (isShoresh) {
    els.memorySummary.textContent = "radici · riconoscimento · RT";
    loadShoreshCatalog();
    renderShoresh();
  }
  if (isMlfHebrew) {
    els.memorySummary.textContent = "";
  }
  if (isHebrew && !currentHelpProfile && !helpProfileLoading) loadHelpProfile();
  updateTaskControlState();
}

function activePresetId() {
  return activePreset().id || "";
}

function taskModeForPreset(preset = activePreset()) {
  const id = preset.id || "";
  if (id === "hebrew_recovery") return "conjugations";
  if (id === "hebrew_flashcards") return "flashcards";
  if (id === "hebrew_conjugations") return "conjugations";
  if (id === "hebrew_roots") return "shoresh";
  if (id === "hebrew_mlf_b2_7") return "mlf_hebrew";
  if (id.startsWith("apk_") || id.startsWith("assessment_") || id.startsWith("program_")) return "training";
  return "recording";
}

function integratedTaskLabel(preset = activePreset()) {
  if (preset.id === "hebrew_recovery") return "percorso ebraico adattivo";
  const mode = taskModeForPreset(preset);
  if (mode === "flashcards") return "flashcards";
  if (mode === "conjugations") return "coniugazioni";
  if (mode === "shoresh") return "Shoresh";
  if (mode === "mlf_hebrew") return "MLF ebraico";
  if (mode === "training") return preset.label || "training";
  return "registrazione EEG";
}

function selectedTaskContext() {
  const mode = taskModeForPreset();
  const covariates = collectSessionCovariates();
  if (mode === "flashcards") return { ...flashcardSessionContext(), session_covariates: covariates };
  if (mode === "conjugations") return { ...conjugationSessionContext(), session_covariates: covariates };
  if (mode === "shoresh") return { ...shoreshSessionContext(), session_covariates: covariates };
  if (mode === "mlf_hebrew") return { ...hebrewMlfSessionContext(), session_covariates: covariates };
  if (mode === "training") return { ...apkTaskContext(), session_covariates: covariates };
  return {
    family: els.testFamily.value,
    test: activePresetId(),
    domain_system: "eeg_context",
    primary_outcomes: ["signal_quality", "session_completion"],
    session_covariates: covariates,
  };
}

function postEegTaskEvent(event) {
  if (!sessionFlow.running && !macActive && event.persist_without_eeg !== true) return Promise.resolve(null);
  return fetch("/api/job", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action: "mac_log_task_event", params: event }),
  }).catch(() => {
    // Event annotation must never interrupt the task flow.
    return null;
  });
}

function ensureConjugationBehavioralSessionId() {
  if (conjugationBehavioralSessionId) return conjugationBehavioralSessionId;
  const suffix = globalThis.crypto?.randomUUID
    ? globalThis.crypto.randomUUID()
    : `${Date.now()}_${Math.random().toString(16).slice(2)}`;
  conjugationBehavioralSessionId = `conjugation_${Date.now()}_${suffix}`;
  return conjugationBehavioralSessionId;
}

function armIntegratedTask() {
  const preset = activePreset();
  sessionFlow = {
    armed: true,
    running: false,
    taskStarted: false,
    presetId: preset.id,
    startedAt: 0,
    stopReason: "",
  };
  if (taskModeForPreset(preset) === "flashcards") {
    flashcardStudyStarted = false;
    setFlashcardTimerActive(false);
    renderFlashcardTimer();
  }
  updateTaskControlState();
}

function beginIntegratedTask() {
  const preset = activePreset();
  if (sessionFlow.taskStarted && sessionFlow.presetId === preset.id) return;
  sessionFlow.armed = false;
  sessionFlow.running = true;
  sessionFlow.taskStarted = true;
  sessionFlow.presetId = preset.id;
  sessionFlow.startedAt = Date.now();
  const mode = taskModeForPreset(preset);
  if (mode === "flashcards") {
    flashcardStudyStarted = true;
    setFlashcardTimerActive(true);
    if (!currentFlashcard && selectedFlashcardDecks.size) {
      pendingFlashcardDeck = [...selectedFlashcardDecks][0] || "";
      renderMemory(window.latestMemoryState);
    }
  } else if (preset.id === "hebrew_recovery") {
    startHebrewRecoveryFlow();
  } else if (mode === "conjugations") {
    if (!currentConjugation) nextConjugationPrompt();
    conjugationPromptStartedAt = Date.now();
    els.conjugationTimer.textContent = "0.0s";
    els.conjugationAnswer.disabled = false;
    els.conjugationAnswer.focus();
  } else if (mode === "shoresh") {
    startShoresh("test", { fromEeg: true });
  } else if (mode === "mlf_hebrew") {
    startHebrewMlfSession({ fromEeg: true });
  } else if (mode === "training") {
    resetApkTask();
    startApkFlow();
  }
  updateTaskControlState();
}

function stopIntegratedTask(reason = "stop") {
  const wasRunning = sessionFlow.running || sessionFlow.taskStarted || sessionFlow.armed;
  const mode = taskModeForPreset();
  sessionFlow.armed = false;
  sessionFlow.running = false;
  sessionFlow.taskStarted = false;
  sessionFlow.stopReason = reason;
  if (mode === "flashcards") {
    setFlashcardTimerActive(false);
    flashcardStudyStarted = false;
  } else if (activePreset().id === "hebrew_recovery") {
    if (hebrewRecoveryFlow?.timeoutId) window.clearTimeout(hebrewRecoveryFlow.timeoutId);
    if (wasRunning && hebrewRecoveryFlow && !["preview", "complete"].includes(hebrewRecoveryFlow.phase)) {
      logHebrewRecoveryEvent("hebrew_recovery_session_interrupted", { reason, phase: hebrewRecoveryFlow.phase });
      setRecoveryStage("Pausa", "Sessione interrotta", "I dati già raccolti restano salvati. La prossima sessione ripartirà da una nuova calibrazione.", "--");
      if (els.hebrewRecoveryStageActions) els.hebrewRecoveryStageActions.innerHTML = `<span>Interruzione registrata senza trasformare prove incomplete in risultati.</span>`;
      if (els.conjugationWorkspace) els.conjugationWorkspace.hidden = true;
    }
  } else if (mode === "training") {
    if (apkTask.timeoutId) window.clearTimeout(apkTask.timeoutId);
    if (wasRunning && apkTask.events.length) pushApkEvent(reason === "done" ? "session_done" : "session_stop", { reason });
    saveApkTaskSession(reason === "done" ? "done" : reason);
    apkTask.phase = "idle";
    apkTask.current = null;
    renderApkTask();
  } else if (mode === "shoresh" && ["baseline", "item"].includes(shoreshSession.phase)) {
    stopShoresh(reason);
  } else if (mode === "mlf_hebrew" && hebrewMlfSession.state === "prompt") {
    postHebrewMlfEegEvent("mlf_session_interrupted", {
      session_id: hebrewMlfSession.sessionId,
      unit_id: hebrewMlfSession.unitId,
      trial_type: hebrewMlfSession.trialType,
      reason,
    });
  }
  updateTaskControlState();
}

function onMacPhaseForTask(phase) {
  if (phase === "recording") {
    beginIntegratedTask();
    return;
  }
  if (["done", "error", "interrupted"].includes(phase)) {
    stopIntegratedTask(phase);
  }
}

function updateTaskControlState() {
  const mode = taskModeForPreset();
  const isRunning = sessionFlow.running;
  const isArmed = sessionFlow.armed;
  const mainText = isRunning ? "In corso" : isArmed ? "Armato" : "Start";
  els.startBtn.textContent = mainText;
  els.startBtn.classList.toggle("is-armed", isArmed);
  els.startBtn.classList.toggle("is-running", isRunning);
  els.stopBtn.textContent = isRunning || isArmed || macActive ? "Stop" : "Stop";
  [
    els.testFamily, els.testPreset, els.duration, els.prep, els.condition, els.guided,
    els.sleepHours, els.sleepQuality, els.exerciseIntensity, els.caffeineCups, els.caffeineMg,
    els.stressLevel, els.cognitiveEnergy, els.sessionTimeOfDay,
  ].forEach((control) => {
    if (control) control.disabled = Boolean(isRunning || isArmed || busy);
  });

  let taskStatus;
  if (mode === "mlf_hebrew") {
    taskStatus = isRunning
      ? "MLF ebraico sincronizzato con EEG"
      : isArmed
        ? "MLF ebraico pronto: parte con la registrazione"
        : "MLF ebraico: premi Start per registrare EEG + task";
  } else {
    taskStatus = isRunning
      ? `${integratedTaskLabel()} sincronizzato con EEG`
      : isArmed
        ? `${integratedTaskLabel()} pronto: parte con la registrazione`
        : `${integratedTaskLabel()}: premi Start per registrare EEG + task`;
  }
  if (els.liveFeatureLine) els.liveFeatureLine.textContent = taskStatus;

  const taskButtonsEnabled = !busy && (mode === "recording" || isRunning);
  [els.flashcardShowBtn, els.flashcardKnowBtn, els.flashcardHardBtn, els.flashcardMissBtn].forEach((button) => {
    if (button) button.disabled = mode === "flashcards" ? !taskButtonsEnabled : false;
  });
  if (els.flashcardCard) els.flashcardCard.disabled = mode === "flashcards" ? !taskButtonsEnabled : false;

  if (els.conjugationAnswer) els.conjugationAnswer.disabled = mode === "conjugations" ? !taskButtonsEnabled : false;
  [els.conjugationCheckBtn, els.conjugationNextBtn, els.conjugationSpeakBtn].forEach((button) => {
    if (button) button.disabled = mode === "conjugations" ? !taskButtonsEnabled : false;
  });

  const trainingButtonsEnabled = !busy && (mode !== "training" || isRunning);
  [els.apkPrimaryBtn, els.apkSecondaryBtn, els.apkTertiaryBtn, els.apkQuaternaryBtn, els.apkStimulus].forEach((button) => {
    if (button) button.disabled = mode === "training" ? !trainingButtonsEnabled : false;
  });

  if (els.shoreshStartBtn) els.shoreshStartBtn.textContent = mode === "shoresh" ? "Avvia solo task" : "Avvia test";
  if (els.shoreshTrainingBtn) els.shoreshTrainingBtn.textContent = "Training";
}

function startLocalTimer() {
  timer = {
    phase: "prep",
    startedAt: Date.now(),
    prep: Number(els.prep.value || 0),
    duration: Number(els.duration.value || 0),
  };
  tickTimer();
}

function stopLocalTimer(label = "Fermato") {
  timer.phase = "ready";
  els.phaseLabel.textContent = label;
  els.countdown.textContent = formatTime(Number(els.duration.value || 0));
}

function showMacPhase(mac) {
  if (!mac) {
    return false;
  }

  const phase = mac.phase || "starting";
  if (!mac.running && phase !== "done" && phase !== "error" && phase !== "interrupted") {
    return false;
  }

  const phaseStartedAt = Number(mac.phase_started_at || 0) * 1000;
  const elapsed = phaseStartedAt ? (Date.now() - phaseStartedAt) / 1000 : 0;
  const prep = Number(mac.prep || els.prep.value || 0);
  const duration = Number(mac.duration || els.duration.value || 0);

  if (phase === "prep") {
    timer.phase = "ready";
    els.phaseLabel.textContent = "Preparazione";
    els.countdown.textContent = formatTime(prep - elapsed);
    return true;
  }

  if (phase === "recording") {
    onMacPhaseForTask("recording");
    timer.phase = "ready";
    els.phaseLabel.textContent = "Registrazione";
    els.countdown.textContent = formatTime(duration - elapsed);
    return true;
  }

  if (phase === "starting") {
    timer.phase = "ready";
    els.phaseLabel.textContent = "Avvio";
    els.countdown.textContent = "--:--";
    return true;
  }

  if (phase === "done") {
    onMacPhaseForTask("done");
    timer.phase = "done";
    els.phaseLabel.textContent = "Fine sessione";
    els.countdown.textContent = "00:00";
    return true;
  }

  if (phase === "error") {
    onMacPhaseForTask("error");
    timer.phase = "ready";
    els.phaseLabel.textContent = "Errore";
    els.countdown.textContent = "--:--";
    return true;
  }

  if (phase === "interrupted") {
    onMacPhaseForTask("interrupted");
    timer.phase = "ready";
    els.phaseLabel.textContent = "Interrotta";
    els.countdown.textContent = "--:--";
    return true;
  }

  if (phase === "connected") {
    timer.phase = "ready";
    els.phaseLabel.textContent = "Connessione stabilita";
    els.countdown.textContent = "--:--";
    return true;
  }

  if (phase === "ble_link") {
    timer.phase = "ready";
    els.phaseLabel.textContent = "Casco rilevato";
    els.countdown.textContent = "--:--";
    return true;
  }

  if (phase === "handshake_sent") {
    timer.phase = "ready";
    els.phaseLabel.textContent = "Verifica collegamento";
    els.countdown.textContent = "--:--";
    return true;
  }

  timer.phase = "ready";
  els.phaseLabel.textContent = phase === "scan" ? "Ricerca casco" : "Connessione";
  els.countdown.textContent = "--:--";
  return true;
}

function tickTimer() {
  if (timer.phase === "ready" || timer.phase === "done") return;

  const elapsed = (Date.now() - timer.startedAt) / 1000;
  if (elapsed < timer.prep) {
    els.phaseLabel.textContent = "Preparazione";
    els.countdown.textContent = formatTime(timer.prep - elapsed);
    return;
  }

  const recordingElapsed = elapsed - timer.prep;
  if (recordingElapsed < timer.duration) {
    timer.phase = "recording";
    els.phaseLabel.textContent = "Registrazione";
    els.countdown.textContent = formatTime(timer.duration - recordingElapsed);
    return;
  }

  timer.phase = "done";
  els.phaseLabel.textContent = "Conclusa";
  els.countdown.textContent = "00:00";
}

function drawWave() {
  const canvas = els.waveCanvas;
  const ctx = canvas.getContext("2d");
  const width = canvas.width;
  const height = canvas.height;
  const now = performance.now() / 1000;
  ctx.clearRect(0, 0, width, height);

  ctx.fillStyle = "#111816";
  ctx.fillRect(0, 0, width, height);

  const active = timer.phase === "prep" || timer.phase === "recording";
  const amplitude = active ? 14 : 8;
  const speed = active ? 0.9 : 0.45;

  for (let layer = 0; layer < 3; layer += 1) {
    ctx.beginPath();
    const yBase = height * (0.52 + layer * 0.055);
    for (let x = 0; x <= width; x += 3) {
      const y =
        yBase +
        Math.sin(x / 42 + now * speed + layer * 1.4) * amplitude * (1 - layer * 0.18) +
        Math.sin(x / 87 - now * 0.35) * 3;
      if (x === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.strokeStyle = layer === 0 ? "rgba(121, 210, 166, 0.82)" : `rgba(139, 183, 255, ${0.34 - layer * 0.07})`;
    ctx.lineWidth = layer === 0 ? 2 : 1.3;
    ctx.stroke();
  }

  requestAnimationFrame(drawWave);
}

function setBusy(value) {
  busy = value;
  document.querySelectorAll("button").forEach((button) => {
    if (button.closest("#memoryPanel")) return;
    button.disabled = value;
  });
  if (!value) {
    updateConnectionControls(latestMacState);
    updateFlashcardDeckSummary();
  }
  updateTaskControlState();
}

async function postJob(action, extra = {}) {
  if (busy) return false;
  setBusy(true);
  try {
    const response = await fetch("/api/job", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action, params: { ...params(), ...extra } }),
    });
    const data = await response.json();
    if (!data.ok) throw new Error(data.error || "errore");
    if (data.log) selectedLog = data.log;
    await refresh();
    return data;
  } catch (error) {
    els.console.textContent = `Errore: ${error.message}`;
    return false;
  } finally {
    setBusy(false);
  }
}

async function postMemory(action, extra = {}) {
  const response = await fetch("/api/memory", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action, params: { ...memoryParams(), ...extra } }),
  });
  const data = await response.json();
  if (!data.ok) throw new Error(data.error || "errore memoria");
  return data;
}

function colorLabel(color) {
  return {
    red: "Red",
    orange: "Orange",
    pink: "Pink",
    yellow: "Yellow",
    "light blue": "Light Blue",
    blue: "Blue",
    lime: "Lime",
    green: "Green",
    "dark green": "Dark Green",
    turquoise: "Turquoise",
    indigo: "Indigo",
    purple: "Purple",
    "non classificati": "Non classificati",
  }[color] || color;
}

function deckColorValue(color) {
  return DECK_COLORS[color] || "#edf7fb";
}

function deckColorClass(color) {
  return `deck-color-${String(color || "none").replaceAll(" ", "-")}`;
}

function renderHebrewKeyboard() {
  [els.hebrewKeyboardKeys, els.conjugationKeyboardKeys].forEach((container) => {
    container.innerHTML = HEBREW_KEY_ROWS.map((row) => `
      <div class="hebrew-keyboard-row" style="--key-count:${row.length}">
        ${row.map((key) => {
          const label = key === " " ? "spazio" : key;
          const value = escapeHtml(key);
          const keyClass = key === " " ? " space" : key === "⌫" ? " backspace" : "";
          return `<button class="hebrew-key${keyClass}" type="button" data-hebrew-key="${value}">${escapeHtml(label)}</button>`;
        }).join("")}
      </div>
    `).join("");
    container.querySelectorAll("[data-hebrew-key]").forEach((button) => {
      button.addEventListener("pointerdown", (event) => event.preventDefault());
      button.addEventListener("click", () => insertHebrewKey(button.dataset.hebrewKey));
    });
  });
}

function insertHebrewKey(key) {
  const input = activeHebrewInput;
  if (!input || !document.contains(input)) {
    els.console.textContent = "Seleziona prima il campo ebraico di una scheda.";
    return;
  }
  input.focus();
  if (input.isContentEditable) {
    const selection = window.getSelection();
    if (!selection || !selection.rangeCount) return;
    const range = selection.getRangeAt(0);
    if (key === "⌫") {
      if (!selection.isCollapsed) {
        range.deleteContents();
      } else {
        const text = input.firstChild;
        if (text && text.nodeType === Node.TEXT_NODE && range.startOffset > 0) {
          range.setStart(text, range.startOffset - 1);
          range.deleteContents();
        }
      }
    } else {
      range.deleteContents();
      const textNode = document.createTextNode(key);
      range.insertNode(textNode);
      range.setStartAfter(textNode);
      range.collapse(true);
      selection.removeAllRanges();
      selection.addRange(range);
    }
    dispatchInputChanged(input, "insertText", key === "⌫" ? null : key);
    return;
  }
  const start = input.selectionStart ?? input.value.length;
  const end = input.selectionEnd ?? start;
  if (key === "⌫") {
    if (start === end && start > 0) {
      input.value = `${input.value.slice(0, start - 1)}${input.value.slice(end)}`;
      input.setSelectionRange(start - 1, start - 1);
    } else {
      input.value = `${input.value.slice(0, start)}${input.value.slice(end)}`;
      input.setSelectionRange(start, start);
    }
    dispatchInputChanged(input, "deleteContentBackward");
    return;
  }
  input.value = `${input.value.slice(0, start)}${key}${input.value.slice(end)}`;
  const cursor = start + key.length;
  input.setSelectionRange(cursor, cursor);
  dispatchInputChanged(input, "insertText", key);
}

function cleanHebrewAnswer(value) {
  return String(value || "")
    .normalize("NFKD")
    .replace(/[\u0591-\u05bd\u05bf-\u05c7]/g, "")
    // Speech recognition and normal typing often append punctuation or bidi
    // controls. Scoring concerns the Hebrew letters, not those artifacts.
    .replace(/[^\u05d0-\u05ea]/g, "")
    .normalize("NFC");
}

function conjugationAlternatives(value) {
  return String(value || "")
    .split("|")
    .map((part) => cleanHebrewAnswer(part))
    .filter(Boolean);
}

function isConjugationAnswerCorrect(answer, expected) {
  const cleanedAnswer = cleanHebrewAnswer(answer);
  return conjugationAlternatives(expected).includes(cleanedAnswer);
}

function randomItem(items) {
  return items[Math.floor(Math.random() * items.length)];
}

function resetShoreshSession() {
  if (shoreshSession.timeoutId) window.clearTimeout(shoreshSession.timeoutId);
  if (shoreshSession.tickId) window.clearInterval(shoreshSession.tickId);
  shoreshSession = {
    mode: "test",
    phase: "idle",
    sessionId: "",
    startedAt: "",
    baselineUntil: 0,
    itemStartedAt: 0,
    index: 0,
    items: [],
    events: [],
    score: { ok: 0, miss: 0, timeout: 0 },
    timeoutId: 0,
    tickId: 0,
    saved: false,
  };
}

async function loadShoreshCatalog() {
  if (shoreshCatalog) return shoreshCatalog;
  const sources = window.location.protocol === "file:"
    ? ["../mindtune_lab/tasks/shoresh_lab/stimuli/shoresh_items_v1.json"]
    : ["/api/shoresh_catalog"];
  let lastError = "";
  for (const source of sources) {
    try {
      const response = await fetch(source, { cache: "no-store" });
      if (!response.ok) throw new Error(`${response.status} ${response.statusText}`.trim());
      const data = await response.json();
      if (data.ok === false) throw new Error(data.error || "catalogo Shoresh non disponibile");
      const items = Array.isArray(data.items) ? data.items : [];
      if (!items.length) throw new Error("catalogo Shoresh vuoto");
      shoreshCatalog = {
        ok: true,
        protocol_name: data.protocol_name || "shoresh_lab_v1",
        schema: data.schema || "shoresh_items_v1",
        items,
        coverage_report: data.coverage_report || {},
        session_blueprint: data.session_blueprint || {},
        source_file: data.source_file || source,
      };
      break;
    } catch (error) {
      lastError = error.message || String(error);
    }
  }
  if (!shoreshCatalog) {
    els.shoreshStatus.textContent = lastError || "Catalogo Shoresh non disponibile";
  }
  return shoreshCatalog;
}

function shoreshTimeoutMs(item) {
  const type = item?.task_type || "";
  if (type === "same_root") return 45000;
  if (type === "choose_root") return 60000;
  if (type === "odd_one_out") return 75000;
  return 60000;
}

function shuffleItems(items) {
  const copy = [...items];
  for (let index = copy.length - 1; index > 0; index -= 1) {
    const swap = Math.floor(Math.random() * (index + 1));
    [copy[index], copy[swap]] = [copy[swap], copy[index]];
  }
  return copy;
}

function selectShoreshItems() {
  const items = shoreshCatalog?.items || [];
  const wants = { same_root: 25, choose_root: 20, odd_one_out: 15 };
  const selected = [];
  Object.entries(wants).forEach(([taskType, count]) => {
    const pool = shuffleItems(items.filter((item) => item.task_type === taskType));
    selected.push(...pool.slice(0, count));
  });
  return shuffleItems(selected).slice(0, 60);
}

function shoreshRatingPayload(kind) {
  if (kind === "pre") {
    return {
      lucidity: Number(els.shoreshLucidity.value || 0),
      fatigue: Number(els.shoreshFatigue.value || 0),
      hebrew_familiarity: Number(els.shoreshFamiliarity.value || 0),
    };
  }
  return {
    effort: Number(els.shoreshEffort.value || 0),
    frustration: Number(els.shoreshFrustration.value || 0),
    focus: Number(els.shoreshFocus.value || 0),
  };
}

function shoreshSessionContext() {
  return {
    family: "ebraico_moderno",
    test: "shoresh_lab",
    domain_system: "morphological_root_processing",
    primary_outcomes: ["accuracy", "reaction_time", "root_recognition", "fatigue_resistance"],
    phase: shoreshSession.phase,
    mode: shoreshSession.mode,
    session_id: shoreshSession.sessionId,
    item_count: shoreshSession.items.length,
    answered_count: shoreshSession.events.length,
    score: { ...shoreshSession.score },
    pre_rating: shoreshRatingPayload("pre"),
  };
}

function shoreshOptionLabel(value, item) {
  if (item.task_type === "same_root") return value === "yes" ? "Sì  J" : "No  F";
  return String(value || "");
}

function renderShoresh() {
  if (!els.shoreshWorkspace) return;
  const total = shoreshSession.items.length || 60;
  els.shoreshModeLabel.textContent = shoreshSession.mode === "training" ? "Shoresh Training" : "Shoresh Test v1";
  els.shoreshProgress.textContent = `${Math.min(shoreshSession.index, total)}/${total}`;
  els.shoreshMetrics.innerHTML = `
    <span>${shoreshSession.score.ok} corrette</span>
    <span>${shoreshSession.score.miss} errori</span>
    <span>${shoreshSession.score.timeout} timeout</span>
  `;
  els.shoreshHistory.innerHTML = shoreshSession.events.slice(-12).reverse().map((event) => `
    <div class="shoresh-history-item ${event.is_correct ? "ok" : "miss"}">
      <span>${escapeHtml(event.task_type)} · ${escapeHtml(event.item_id)} · ${event.reaction_time_ms} ms</span>
      <small>${escapeHtml(event.answer || "timeout")} → ${escapeHtml(event.correct_answer)}</small>
    </div>
  `).join("") || `<div class="memory-empty">Nessuna risposta.</div>`;
  els.shoreshSaveBtn.hidden = shoreshSession.phase !== "post";
  els.shoreshPreRatings.hidden = !["idle", "baseline"].includes(shoreshSession.phase);
  els.shoreshPostRatings.hidden = shoreshSession.phase !== "post";
  if (shoreshSession.phase === "idle") {
    els.shoreshClock.textContent = "00:00";
    els.shoreshStatus.textContent = shoreshCatalog ? "Pronto. Il test salva CSV e JSON locali." : "Caricamento catalogo radici...";
    els.shoreshStimulus.textContent = "שורש";
    els.shoreshPrompt.textContent = "Test: baseline 30s, 60 item, niente feedback. Training: feedback abilitato.";
    els.shoreshOptions.innerHTML = "";
  }
}

function tickShoreshClock() {
  if (shoreshSession.phase === "baseline") {
    const left = Math.max(0, Math.ceil((shoreshSession.baselineUntil - Date.now()) / 1000));
    els.shoreshClock.textContent = `00:${String(left).padStart(2, "0")}`;
    if (left <= 0) nextShoreshItem();
  } else if (shoreshSession.phase === "item" && shoreshSession.itemStartedAt) {
    const elapsed = Math.max(0, Date.now() - shoreshSession.itemStartedAt);
    els.shoreshClock.textContent = `${(elapsed / 1000).toFixed(1)}s`;
  }
}

async function startShoresh(mode = "test", options = {}) {
  await loadShoreshCatalog();
  if (!shoreshCatalog?.items?.length) {
    els.shoreshStatus.textContent = "Catalogo Shoresh assente: genera shoresh_items_v1.json.";
    return;
  }
  resetShoreshSession();
  shoreshSession.mode = mode;
  shoreshSession.phase = mode === "test" ? "baseline" : "item";
  shoreshSession.sessionId = `shoresh_${new Date().toISOString().replace(/[-:T.Z]/g, "").slice(0, 14)}`;
  shoreshSession.startedAt = new Date().toISOString();
  shoreshSession.items = selectShoreshItems();
  shoreshSession.baselineUntil = Date.now() + (mode === "test" ? 30000 : 0);
  els.pieceId.value = shoreshSession.sessionId;
  els.sessionNote.value = `${mode === "test" ? "shoresh_test_v1" : "shoresh_training"} · 60 item · radici ebraico moderno`;
  shoreshSession.tickId = window.setInterval(tickShoreshClock, 120);
  if (options.fromEeg) {
    shoreshSession.eeg_synced = true;
  }
  renderShoresh();
  if (mode === "test") {
    els.shoreshStatus.textContent = "Baseline neutra: resta fermo, sguardo morbido.";
    els.shoreshStimulus.textContent = "•";
    els.shoreshPrompt.textContent = "Il test parte automaticamente.";
    els.shoreshOptions.innerHTML = "";
  } else {
    nextShoreshItem();
  }
}

function stopShoresh(reason = "stop") {
  if (shoreshSession.timeoutId) window.clearTimeout(shoreshSession.timeoutId);
  if (shoreshSession.tickId) window.clearInterval(shoreshSession.tickId);
  if (!shoreshSession.events.length) {
    shoreshSession.phase = "idle";
    renderShoresh();
    return;
  }
  shoreshSession.phase = "post";
  els.shoreshClock.textContent = reason === "done" ? "fine" : "stop";
  els.shoreshStimulus.textContent = "עצור";
  els.shoreshPrompt.textContent = reason === "done"
    ? "Sessione EEG conclusa. Compila il self-rating finale e salva."
    : "Sessione interrotta. Puoi salvare i dati raccolti finora.";
  els.shoreshOptions.innerHTML = "";
  els.shoreshStatus.textContent = "Shoresh fermato insieme all'EEG.";
  renderShoresh();
}

function renderShoreshItem(item) {
  const prompt = item.prompt_he;
  const promptText = Array.isArray(prompt) ? prompt.join("   /   ") : String(prompt || "");
  els.shoreshStimulus.textContent = promptText;
  els.shoreshPrompt.textContent = item.prompt_it || "";
  els.shoreshOptions.innerHTML = (item.options || []).map((option, index) => `
    <button class="shoresh-option" type="button" data-shoresh-answer="${escapeHtml(String(option))}">
      ${escapeHtml(shoreshOptionLabel(option, item))}
      ${item.task_type !== "same_root" ? `<small>${index + 1}</small>` : ""}
    </button>
  `).join("");
  els.shoreshOptions.querySelectorAll("[data-shoresh-answer]").forEach((button) => {
    button.addEventListener("click", () => answerShoresh(button.getAttribute("data-shoresh-answer") || ""));
  });
  if (shoreshSession.timeoutId) window.clearTimeout(shoreshSession.timeoutId);
  window.requestAnimationFrame(() => {
    shoreshSession.itemStartedAt = Date.now();
    shoreshSession.timeoutId = window.setTimeout(() => answerShoresh("", true), shoreshTimeoutMs(item));
  });
}

function nextShoreshItem() {
  if (shoreshSession.timeoutId) window.clearTimeout(shoreshSession.timeoutId);
  if (shoreshSession.index >= shoreshSession.items.length) {
    finishShoresh();
    return;
  }
  shoreshSession.phase = "item";
  const item = shoreshSession.items[shoreshSession.index];
  els.shoreshStatus.textContent = shoreshSession.mode === "test"
    ? "Rispondi senza feedback. J/F oppure 1-4."
    : "Training: il feedback compare dopo ogni risposta.";
  renderShoresh();
  renderShoreshItem(item);
}

function answerShoresh(answer, timeout = false) {
  if (shoreshSession.phase !== "item") return;
  const item = shoreshSession.items[shoreshSession.index];
  if (!item) return;
  if (shoreshSession.timeoutId) window.clearTimeout(shoreshSession.timeoutId);
  const reactionMs = shoreshSession.itemStartedAt ? Math.max(0, Date.now() - shoreshSession.itemStartedAt) : 0;
  const correct = !timeout && String(answer) === String(item.correct_answer);
  shoreshSession.score[correct ? "ok" : "miss"] += 1;
  if (timeout) shoreshSession.score.timeout += 1;
  const event = {
    timestamp: new Date().toISOString(),
    item_id: item.item_id,
    task_type: item.task_type,
    level: item.level,
    root: item.root,
    answer,
    correct_answer: item.correct_answer,
    is_correct: correct,
    reaction_time_ms: Math.round(reactionMs),
    timeout,
  };
  shoreshSession.events.push(event);
  postEegTaskEvent({
    annotation_type: "shoresh_response",
    event,
    study_context: shoreshSessionContext(),
  });
  shoreshSession.index += 1;
  if (shoreshSession.mode === "training") {
    els.shoreshStatus.textContent = correct ? "Corretto." : `Errore: radice ${item.root}, risposta ${item.correct_answer}.`;
    window.setTimeout(nextShoreshItem, 650);
  } else {
    nextShoreshItem();
  }
  renderShoresh();
}

function finishShoresh() {
  if (shoreshSession.timeoutId) window.clearTimeout(shoreshSession.timeoutId);
  if (shoreshSession.tickId) window.clearInterval(shoreshSession.tickId);
  shoreshSession.phase = "post";
  els.shoreshClock.textContent = "fine";
  els.shoreshStimulus.textContent = "סיום";
  els.shoreshPrompt.textContent = "Compila il self-rating finale e salva la sessione.";
  els.shoreshOptions.innerHTML = "";
  els.shoreshStatus.textContent = "Sessione completata. Salva CSV e JSON.";
  renderShoresh();
}

async function saveShoreshSession() {
  if (!shoreshSession.events.length || shoreshSession.saved) return;
  try {
    const data = await postMemory("save_shoresh_session", {
      session_id: shoreshSession.sessionId,
      mode: shoreshSession.mode,
      started_at: shoreshSession.startedAt,
      events: shoreshSession.events,
      pre: shoreshRatingPayload("pre"),
      post: shoreshRatingPayload("post"),
    });
    shoreshSession.saved = true;
    els.shoreshStatus.textContent = `Salvata: score ${data.summary?.root_skill_score ?? "--"} · ${data.summary?.accuracy_total ?? "--"} accuracy`;
    els.console.textContent = `Shoresh salvato\nCSV: ${data.csv}\nJSON: ${data.summary_json}`;
    await loadHelpProfile();
  } catch (error) {
    els.shoreshStatus.textContent = `Errore salvataggio: ${error.message}`;
  }
}

function renderConjugationStats() {
  els.conjugationScore.textContent = `${conjugationScore.correct} giuste · ${conjugationScore.miss} errori`;
}

function renderConjugationHistory() {
  els.conjugationHistoryCount.textContent = String(conjugationHistory.length);
  if (!conjugationHistory.length) {
    els.conjugationHistoryList.innerHTML = `<div class="memory-empty">Nessuna risposta.</div>`;
    return;
  }
  els.conjugationHistoryList.innerHTML = conjugationHistory.slice(0, 12).map((entry) => `
    <div class="conjugation-history-item ${entry.ok ? "ok" : "miss"}">
      <div class="history-top">
        <span dir="rtl">${escapeHtml(entry.present)} → ${escapeHtml(entry.prompt)}</span>
        <span>${entry.elapsed.toFixed(1)}s</span>
      </div>
      <div dir="rtl">tu: ${escapeHtml(entry.answer || "∅")}</div>
      <div dir="rtl">ok: ${escapeHtml(entry.expectedPhrase || entry.expected)}</div>
      <div>${escapeHtml(entry.italian)}</div>
    </div>
  `).join("");
}

async function loadConjugationCatalog() {
  if (window.location.protocol !== "file:") {
    const response = await fetch("/api/conjugation_catalog", { cache: "no-store" });
    const data = await response.json();
    catalogConjugationVerbs = data.pealim_practice_verbs || [];
    if (activePreset().id === "hebrew_conjugations") {
      currentConjugation = null;
      conjugationDomino = null;
      nextConjugationPrompt();
    } else if (activePreset().id === "hebrew_recovery" && [null, "preview"].includes(hebrewRecoveryFlow?.phase || null)) {
      renderHebrewRecoveryPreview();
    }
  }
}

function activeConjugationVerbs() {
  return catalogConjugationVerbs.filter((verb) => verb.source === "pealim");
}

function conjugationTargetEntries(verb) {
  const entries = Object.entries(verb.targets || {});
  const present = Array.isArray(verb.present) ? verb.present : [];
  const labels = [
    ["בהווה · זכר יחיד", "presente maschile singolare"],
    ["בהווה · נקבה יחידה", "presente femminile singolare"],
    ["בהווה · זכרים רבים", "presente maschile plurale"],
    ["בהווה · נקבות רבות", "presente femminile plurale"],
  ];
  present.slice(0, 4).forEach((form, index) => {
    if (form) entries.push([labels[index][0], [form, labels[index][1]]]);
  });
  return entries;
}

const CONJUGATION_PERSONS = [
  { he: "אני", it: "io", presentIndex: 0 },
  { he: "אתה", it: "tu m.", presentIndex: 0 },
  { he: "את", it: "tu f.", presentIndex: 1 },
  { he: "הוא", it: "lui", presentIndex: 0 },
  { he: "היא", it: "lei", presentIndex: 1 },
  { he: "אנחנו", it: "noi", presentIndex: 2 },
  { he: "אתם", it: "voi m.", presentIndex: 2 },
  { he: "אתן", it: "voi f.", presentIndex: 3 },
  { he: "הם", it: "loro m.", presentIndex: 2 },
  { he: "הן", it: "loro f.", presentIndex: 3 },
];

const CONJUGATION_TIMES = {
  present: ["היום", "עכשיו"],
  future: ["מחר", "בשבוע הבא", "בשנה הבאה", "אחר כך"],
  past: ["אתמול", "שלשום", "לפני שבוע", "בשנה שעברה"],
};

const ITALIAN_PRESENT_PROMPTS = {
  mangiare: ["io mangio", "tu mangi", "tu mangi", "lui mangia", "lei mangia", "noi mangiamo", "voi mangiate", "voi mangiate", "loro mangiano", "loro mangiano"],
  bere: ["io bevo", "tu bevi", "tu bevi", "lui beve", "lei beve", "noi beviamo", "voi bevete", "voi bevete", "loro bevono", "loro bevono"],
  andare: ["io vado", "tu vai", "tu vai", "lui va", "lei va", "noi andiamo", "voi andate", "voi andate", "loro vanno", "loro vanno"],
  venire: ["io vengo", "tu vieni", "tu vieni", "lui viene", "lei viene", "noi veniamo", "voi venite", "voi venite", "loro vengono", "loro vengono"],
  fare: ["io faccio", "tu fai", "tu fai", "lui fa", "lei fa", "noi facciamo", "voi fate", "voi fate", "loro fanno", "loro fanno"],
  parlare: ["io parlo", "tu parli", "tu parli", "lui parla", "lei parla", "noi parliamo", "voi parlate", "voi parlate", "loro parlano", "loro parlano"],
  scrivere: ["io scrivo", "tu scrivi", "tu scrivi", "lui scrive", "lei scrive", "noi scriviamo", "voi scrivete", "voi scrivete", "loro scrivono", "loro scrivono"],
  "leggere / chiamare": ["io leggo", "tu leggi", "tu leggi", "lui legge", "lei legge", "noi leggiamo", "voi leggete", "voi leggete", "loro leggono", "loro leggono"],
  "sentire / ascoltare": ["io sento", "tu senti", "tu senti", "lui sente", "lei sente", "noi sentiamo", "voi sentite", "voi sentite", "loro sentono", "loro sentono"],
  "ascoltare / prestare attenzione": ["io ascolto", "tu ascolti", "tu ascolti", "lui ascolta", "lei ascolta", "noi ascoltiamo", "voi ascoltate", "voi ascoltate", "loro ascoltano", "loro ascoltano"],
  "studiare / imparare": ["io studio", "tu studi", "tu studi", "lui studia", "lei studia", "noi studiamo", "voi studiate", "voi studiate", "loro studiano", "loro studiano"],
  lavorare: ["io lavoro", "tu lavori", "tu lavori", "lui lavora", "lei lavora", "noi lavoriamo", "voi lavorate", "voi lavorate", "loro lavorano", "loro lavorano"],
  vedere: ["io vedo", "tu vedi", "tu vedi", "lui vede", "lei vede", "noi vediamo", "voi vedete", "voi vedete", "loro vedono", "loro vedono"],
  volere: ["io voglio", "tu vuoi", "tu vuoi", "lui vuole", "lei vuole", "noi vogliamo", "voi volete", "voi volete", "loro vogliono", "loro vogliono"],
  sapere: ["io so", "tu sai", "tu sai", "lui sa", "lei sa", "noi sappiamo", "voi sapete", "voi sapete", "loro sanno", "loro sanno"],
  dare: ["io do", "tu dai", "tu dai", "lui dà", "lei dà", "noi diamo", "voi date", "voi date", "loro danno", "loro danno"],
  prendere: ["io prendo", "tu prendi", "tu prendi", "lui prende", "lei prende", "noi prendiamo", "voi prendete", "voi prendete", "loro prendono", "loro prendono"],
  comprare: ["io compro", "tu compri", "tu compri", "lui compra", "lei compra", "noi compriamo", "voi comprate", "voi comprate", "loro comprano", "loro comprano"],
  dire: ["io dico", "tu dici", "tu dici", "lui dice", "lei dice", "noi diciamo", "voi dite", "voi dite", "loro dicono", "loro dicono"],
  essere: ["io sono", "tu sei", "tu sei", "lui è", "lei è", "noi siamo", "voi siete", "voi siete", "loro sono", "loro sono"],
  dormire: ["io dormo", "tu dormi", "tu dormi", "lui dorme", "lei dorme", "noi dormiamo", "voi dormite", "voi dormite", "loro dormono", "loro dormono"],
  alzarsi: ["io mi alzo", "tu ti alzi", "tu ti alzi", "lui si alza", "lei si alza", "noi ci alziamo", "voi vi alzate", "voi vi alzate", "loro si alzano", "loro si alzano"],
  "sedersi / stare seduto": ["io mi siedo", "tu ti siedi", "tu ti siedi", "lui si siede", "lei si siede", "noi ci sediamo", "voi vi sedete", "voi vi sedete", "loro si siedono", "loro si siedono"],
  "stare in piedi": ["io sto in piedi", "tu stai in piedi", "tu stai in piedi", "lui sta in piedi", "lei sta in piedi", "noi stiamo in piedi", "voi state in piedi", "voi state in piedi", "loro stanno in piedi", "loro stanno in piedi"],
  entrare: ["io entro", "tu entri", "tu entri", "lui entra", "lei entra", "noi entriamo", "voi entrate", "voi entrate", "loro entrano", "loro entrano"],
  uscire: ["io esco", "tu esci", "tu esci", "lui esce", "lei esce", "noi usciamo", "voi uscite", "voi uscite", "loro escono", "loro escono"],
  tornare: ["io torno", "tu torni", "tu torni", "lui torna", "lei torna", "noi torniamo", "voi tornate", "voi tornate", "loro tornano", "loro tornano"],
  abitare: ["io abito", "tu abiti", "tu abiti", "lui abita", "lei abita", "noi abitiamo", "voi abitate", "voi abitate", "loro abitano", "loro abitano"],
  "chiedere / domandare": ["io chiedo", "tu chiedi", "tu chiedi", "lui chiede", "lei chiede", "noi chiediamo", "voi chiedete", "voi chiedete", "loro chiedono", "loro chiedono"],
  rispondere: ["io rispondo", "tu rispondi", "tu rispondi", "lui risponde", "lei risponde", "noi rispondiamo", "voi rispondete", "voi rispondete", "loro rispondono", "loro rispondono"],
  aprire: ["io apro", "tu apri", "tu apri", "lui apre", "lei apre", "noi apriamo", "voi aprite", "voi aprite", "loro aprono", "loro aprono"],
  chiudere: ["io chiudo", "tu chiudi", "tu chiudi", "lui chiude", "lei chiude", "noi chiudiamo", "voi chiudete", "voi chiudete", "loro chiudono", "loro chiudono"],
  capire: ["io capisco", "tu capisci", "tu capisci", "lui capisce", "lei capisce", "noi capiamo", "voi capite", "voi capite", "loro capiscono", "loro capiscono"],
  ricordare: ["io ricordo", "tu ricordi", "tu ricordi", "lui ricorda", "lei ricorda", "noi ricordiamo", "voi ricordate", "voi ricordate", "loro ricordano", "loro ricordano"],
  dimenticare: ["io dimentico", "tu dimentichi", "tu dimentichi", "lui dimentica", "lei dimentica", "noi dimentichiamo", "voi dimenticate", "voi dimenticate", "loro dimenticano", "loro dimenticano"],
  aiutare: ["io aiuto", "tu aiuti", "tu aiuti", "lui aiuta", "lei aiuta", "noi aiutiamo", "voi aiutate", "voi aiutate", "loro aiutano", "loro aiutano"],
  incontrare: ["io incontro", "tu incontri", "tu incontri", "lui incontra", "lei incontra", "noi incontriamo", "voi incontrate", "voi incontrate", "loro incontrano", "loro incontrano"],
  trovare: ["io trovo", "tu trovi", "tu trovi", "lui trova", "lei trova", "noi troviamo", "voi trovate", "voi trovate", "loro trovano", "loro trovano"],
  perdere: ["io perdo", "tu perdi", "tu perdi", "lui perde", "lei perde", "noi perdiamo", "voi perdete", "voi perdete", "loro perdono", "loro perdono"],
  iniziare: ["io inizio", "tu inizi", "tu inizi", "lui inizia", "lei inizia", "noi iniziamo", "voi iniziate", "voi iniziate", "loro iniziano", "loro iniziano"],
  finire: ["io finisco", "tu finisci", "tu finisci", "lui finisce", "lei finisce", "noi finiamo", "voi finite", "voi finite", "loro finiscono", "loro finiscono"],
  continuare: ["io continuo", "tu continui", "tu continui", "lui continua", "lei continua", "noi continuiamo", "voi continuate", "voi continuate", "loro continuano", "loro continuano"],
  "smettere / interrompere": ["io smetto", "tu smetti", "tu smetti", "lui smette", "lei smette", "noi smettiamo", "voi smettete", "voi smettete", "loro smettono", "loro smettono"],
  scegliere: ["io scelgo", "tu scegli", "tu scegli", "lui sceglie", "lei sceglie", "noi scegliamo", "voi scegliete", "voi scegliete", "loro scelgono", "loro scelgono"],
  pagare: ["io pago", "tu paghi", "tu paghi", "lui paga", "lei paga", "noi paghiamo", "voi pagate", "voi pagate", "loro pagano", "loro pagano"],
  vendere: ["io vendo", "tu vendi", "tu vendi", "lui vende", "lei vende", "noi vendiamo", "voi vendete", "voi vendete", "loro vendono", "loro vendono"],
  amare: ["io amo", "tu ami", "tu ami", "lui ama", "lei ama", "noi amiamo", "voi amate", "voi amate", "loro amano", "loro amano"],
  odiare: ["io odio", "tu odi", "tu odi", "lui odia", "lei odia", "noi odiamo", "voi odiate", "voi odiate", "loro odiano", "loro odiano"],
  pensare: ["io penso", "tu pensi", "tu pensi", "lui pensa", "lei pensa", "noi pensiamo", "voi pensate", "voi pensate", "loro pensano", "loro pensano"],
  credere: ["io credo", "tu credi", "tu credi", "lui crede", "lei crede", "noi crediamo", "voi credete", "voi credete", "loro credono", "loro credono"],
  "sentire / provare": ["io sento", "tu senti", "tu senti", "lui sente", "lei sente", "noi sentiamo", "voi sentite", "voi sentite", "loro sentono", "loro sentono"],
  "avere bisogno": ["io ho bisogno", "tu hai bisogno", "tu hai bisogno", "lui ha bisogno", "lei ha bisogno", "noi abbiamo bisogno", "voi avete bisogno", "voi avete bisogno", "loro hanno bisogno", "loro hanno bisogno"],
  mettere: ["io metto", "tu metti", "tu metti", "lui mette", "lei mette", "noi mettiamo", "voi mettete", "voi mettete", "loro mettono", "loro mettono"],
  "portare / portare qui": ["io porto", "tu porti", "tu porti", "lui porta", "lei porta", "noi portiamo", "voi portate", "voi portate", "loro portano", "loro portano"],
  "mandare / inviare": ["io mando", "tu mandi", "tu mandi", "lui manda", "lei manda", "noi mandiamo", "voi mandate", "voi mandate", "loro mandano", "loro mandano"],
  ricevere: ["io ricevo", "tu ricevi", "tu ricevi", "lui riceve", "lei riceve", "noi riceviamo", "voi ricevete", "voi ricevete", "loro ricevono", "loro ricevono"],
  "viaggiare / andare in veicolo": ["io viaggio", "tu viaggi", "tu viaggi", "lui viaggia", "lei viaggia", "noi viaggiamo", "voi viaggiate", "voi viaggiate", "loro viaggiano", "loro viaggiano"],
  volare: ["io volo", "tu voli", "tu voli", "lui vola", "lei vola", "noi voliamo", "voi volate", "voi volate", "loro volano", "loro volano"],
  guidare: ["io guido", "tu guidi", "tu guidi", "lui guida", "lei guida", "noi guidiamo", "voi guidate", "voi guidate", "loro guidano", "loro guidano"],
  correre: ["io corro", "tu corri", "tu corri", "lui corre", "lei corre", "noi corriamo", "voi correte", "voi correte", "loro corrono", "loro corrono"],
};

function conjugationPersonByHebrew(hebrew) {
  return CONJUGATION_PERSONS.find((person) => person.he === hebrew) || CONJUGATION_PERSONS[3];
}

function conjugationTenseLabel(tense) {
  if (tense === "future") return "עתיד";
  if (tense === "past") return "עבר";
  return "הווה";
}

function conjugationTimeAdverb(tense) {
  return randomItem(CONJUGATION_TIMES[tense] || CONJUGATION_TIMES.present);
}

function splitConjugationAlternatives(value) {
  return String(value || "")
    .split("|")
    .map((part) => part.trim())
    .filter(Boolean);
}

function uniqueConjugationForms(forms) {
  const seen = new Set();
  return forms
    .map((form) => String(form || "").trim())
    .filter((form) => {
      const key = cleanHebrewAnswer(form);
      if (!key || seen.has(key)) return false;
      seen.add(key);
      return true;
    });
}

function modernFuturePluralEquivalent(verb, personHe) {
  const modernSourcePerson = { "אתן": "אתם", "הן": "הם" }[personHe];
  if (!modernSourcePerson || !verb?.targets) return "";
  const target = verb.targets[`בעתיד · ${modernSourcePerson}`];
  return Array.isArray(target) ? String(target[0] || "").trim() : "";
}

function conjugationTargetPool(verb) {
  const pool = [];
  const present = Array.isArray(verb.present) ? verb.present : [];
  CONJUGATION_PERSONS.forEach((person) => {
    const form = present[person.presentIndex];
    if (form) {
      pool.push({
        tense: "present",
        person,
        form,
        italian: `${person.it} - presente: ${verb.italianInfinitive || verb.italian || ""}`.trim(),
      });
    }
  });
  Object.entries(verb.targets || {}).forEach(([label, targetValue]) => {
    const match = label.match(/^(בעבר|בעתיד)\s*·\s*(.+)$/);
    if (!match || !Array.isArray(targetValue)) return;
    const tense = match[1] === "בעבר" ? "past" : "future";
    const person = conjugationPersonByHebrew(match[2].trim());
    const pealimForm = String(targetValue[0] || "").trim();
    const modernForm = tense === "future" ? modernFuturePluralEquivalent(verb, person.he) : "";
    const form = uniqueConjugationForms([modernForm, pealimForm]).join("|");
    if (!form) return;
    pool.push({
      tense,
      person,
      form,
      italian: targetValue[1] || `${person.it} - ${tense}: ${verb.italianInfinitive || verb.italian || ""}`,
    });
  });
  return pool;
}

function conjugationPhrase(entry) {
  const first = splitConjugationAlternatives(entry.form)[0] || entry.form || "";
  return `${entry.person.he} ${first}`.trim();
}

function conjugationAcceptedPhrases(entry) {
  return splitConjugationAlternatives(entry.form).map((form) => `${entry.person.he} ${form}`.trim());
}

function conjugationExpectedAnswer(entry) {
  const forms = splitConjugationAlternatives(entry.form);
  const expected = [];
  forms.forEach((form) => {
    expected.push(form);
    expected.push(`${entry.person.he} ${form}`.trim());
  });
  return [...new Set(expected)].join("|");
}

function setConjugationSpeechStatus(message, { error = false } = {}) {
  if (!els.conjugationSpeechStatus) return;
  els.conjugationSpeechStatus.textContent = message;
  els.conjugationSpeechStatus.classList.toggle("error", error);
}

function mergeAudioChunks(chunks) {
  const length = chunks.reduce((sum, chunk) => sum + chunk.length, 0);
  const merged = new Float32Array(length);
  let offset = 0;
  chunks.forEach((chunk) => {
    merged.set(chunk, offset);
    offset += chunk.length;
  });
  return merged;
}

function resampleAudio(input, sourceRate, targetRate = 16000) {
  if (sourceRate === targetRate) return input;
  const outputLength = Math.max(1, Math.round(input.length * targetRate / sourceRate));
  const output = new Float32Array(outputLength);
  const ratio = sourceRate / targetRate;
  for (let index = 0; index < outputLength; index += 1) {
    const position = index * ratio;
    const left = Math.floor(position);
    const right = Math.min(input.length - 1, left + 1);
    const fraction = position - left;
    output[index] = input[left] * (1 - fraction) + input[right] * fraction;
  }
  return output;
}

function encodeMonoWav(samples, sampleRate = 16000) {
  const buffer = new ArrayBuffer(44 + samples.length * 2);
  const view = new DataView(buffer);
  const writeText = (offset, value) => {
    for (let index = 0; index < value.length; index += 1) view.setUint8(offset + index, value.charCodeAt(index));
  };
  writeText(0, "RIFF");
  view.setUint32(4, 36 + samples.length * 2, true);
  writeText(8, "WAVE");
  writeText(12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, 1, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  writeText(36, "data");
  view.setUint32(40, samples.length * 2, true);
  samples.forEach((sample, index) => {
    const clipped = Math.max(-1, Math.min(1, sample));
    view.setInt16(44 + index * 2, clipped < 0 ? clipped * 0x8000 : clipped * 0x7fff, true);
  });
  return new Blob([buffer], { type: "audio/wav" });
}

async function startConjugationSpeechCapture() {
  if (conjugationSpeechCapture) {
    await stopConjugationSpeechCapture();
    return;
  }
  try {
    const statusResponse = await fetch("/api/azure_speech/status", { cache: "no-store" });
    const status = await statusResponse.json();
    if (!status.configured) {
      setConjugationSpeechStatus("Azure Speech non configurato. Usa Dati > Configura trascrizione ebraica.", { error: true });
      return;
    }
    const stream = await navigator.mediaDevices.getUserMedia({
      audio: { channelCount: 1, echoCancellation: false, noiseSuppression: false, autoGainControl: false },
    });
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    const context = new AudioContextClass();
    const source = context.createMediaStreamSource(stream);
    const processor = context.createScriptProcessor(4096, 1, 1);
    const chunks = [];
    processor.onaudioprocess = (event) => {
      chunks.push(new Float32Array(event.inputBuffer.getChannelData(0)));
      event.outputBuffer.getChannelData(0).fill(0);
    };
    source.connect(processor);
    processor.connect(context.destination);
    const timeoutId = window.setTimeout(() => stopConjugationSpeechCapture(), 8000);
    conjugationSpeechCapture = { stream, context, source, processor, chunks, sampleRate: context.sampleRate, timeoutId };
    lastConjugationSpeech = null;
    els.conjugationSpeakBtn.classList.add("is-recording");
    els.conjugationSpeakBtn.textContent = "Ferma";
    setConjugationSpeechStatus("Sto ascoltando... parla in ebraico, poi premi Ferma.");
  } catch (error) {
    setConjugationSpeechStatus(`Microfono non disponibile: ${error.message || error}`, { error: true });
  }
}

async function stopConjugationSpeechCapture({ discard = false } = {}) {
  const capture = conjugationSpeechCapture;
  if (!capture) return;
  conjugationSpeechCapture = null;
  window.clearTimeout(capture.timeoutId);
  capture.processor.disconnect();
  capture.source.disconnect();
  capture.stream.getTracks().forEach((track) => track.stop());
  await capture.context.close();
  els.conjugationSpeakBtn?.classList.remove("is-recording");
  if (els.conjugationSpeakBtn) els.conjugationSpeakBtn.textContent = "Parla";
  if (discard) return;
  try {
    setConjugationSpeechStatus("Trascrizione in corso...");
    const raw = mergeAudioChunks(capture.chunks);
    if (raw.length < capture.sampleRate * 0.25) throw new Error("registrazione troppo breve");
    const wav = encodeMonoWav(resampleAudio(raw, capture.sampleRate));
    const response = await fetch("/api/azure_speech/transcribe", {
      method: "POST",
      headers: { "Content-Type": "audio/wav" },
      body: wav,
    });
    const result = await response.json();
    if (!response.ok || !result.ok) throw new Error(result.error || "trascrizione non riuscita");
    els.conjugationAnswer.value = result.display_text;
    activeHebrewInput = els.conjugationAnswer;
    lastConjugationSpeech = {
      provider: result.provider,
      locale: result.locale,
      recognized_text: result.display_text,
      recognition_confidence: result.recognition_confidence,
      duration_ms: result.duration_ms,
      request_id: result.request_id,
      audio_retained: false,
    };
    const confidence = Number.isFinite(result.recognition_confidence)
      ? ` · confidenza trascrizione ${Math.round(result.recognition_confidence * 100)}%`
      : "";
    setConjugationSpeechStatus(`Trascritto${confidence}. Correggi se serve, poi premi Invio.`);
    els.conjugationAnswer.focus();
  } catch (error) {
    lastConjugationSpeech = null;
    setConjugationSpeechStatus(`Trascrizione non riuscita: ${error.message || error}`, { error: true });
  }
}

function italianPresentQuestion(entry, verb) {
  const verbLabel = verb.italianInfinitive || verb.italian || "questo verbo";
  const personIndex = CONJUGATION_PERSONS.findIndex((person) => person.he === entry.person.he);
  const phrase = ITALIAN_PRESENT_PROMPTS[verbLabel]?.[personIndex] || `${entry.person.it} ${verbLabel}`;
  return `Come si dice \"${phrase}\"?`;
}

function nextConjugationDominoStep(previousStep = null) {
  const previousEntry = previousStep?.target || null;
  const verb = previousStep?.verb || randomItem(activeConjugationVerbs());
  const pool = conjugationTargetPool(verb);
  if (!pool.length) return null;
  let target = randomItem(pool);
  if (previousEntry && pool.length > 1) {
    for (let attempt = 0; attempt < 8 && target.tense === previousEntry.tense && target.person.he === previousEntry.person.he; attempt += 1) {
      target = randomItem(pool);
    }
  } else {
    const presentStarts = pool.filter((entry) => entry.tense === "present" && ["הוא", "היא"].includes(entry.person.he));
    if (presentStarts.length) target = randomItem(presentStarts);
  }
  const sourceTime = previousEntry ? conjugationTimeAdverb(previousEntry.tense) : "";
  const targetTime = conjugationTimeAdverb(target.tense);
  const prompt = previousEntry
    ? `אם ${conjugationPhrase(previousEntry)} ${sourceTime}, ${target.person.he} ${targetTime}?`
    : italianPresentQuestion(target, verb);
  return {
    verb,
    source: previousEntry,
    target,
    prompt,
    promptKind: previousEntry ? "domino" : "italian_seed",
    targetLabel: previousEntry
      ? `${conjugationTenseLabel(target.tense)} · ${target.person.he} · ${targetTime}`
      : "פתיחה · הווה",
    expected: conjugationExpectedAnswer(target),
    expectedPhrase: conjugationAcceptedPhrases(target).join(" / "),
    italian: target.italian,
  };
}

function nextConjugationPrompt() {
  stopConjugationSpeechCapture({ discard: true });
  lastConjugationSpeech = null;
  setConjugationSpeechStatus("");
  const verbs = activeConjugationVerbs();
  if (!verbs.length) {
    currentConjugation = null;
    conjugationDomino = null;
    els.conjugationPresent.textContent = "Pealim";
    els.conjugationPrompt.textContent = "Catalogo Pealim non caricato.";
    els.conjugationAnswer.value = "";
    els.conjugationFeedback.hidden = false;
    els.conjugationFeedback.className = "conjugation-feedback miss";
    els.conjugationFeedback.textContent = "Le coniugazioni non partono senza cache Pealim locale.";
    return;
  }
  const step = nextConjugationDominoStep(conjugationDomino);
  if (!step) return;
  conjugationDomino = step;
  const displayStem = step.source
    ? conjugationPhrase(step.source)
    : (step.verb.displayInfinitive || step.verb.infinitive || step.verb.source_query || "");
  currentConjugation = {
    verb: step.verb,
    present: displayStem,
    targetLabel: step.targetLabel,
    expected: step.expected,
    expectedPhrase: step.expectedPhrase,
    italian: step.italian,
    domino: {
      prompt_kind: step.promptKind,
      source_phrase: step.source ? conjugationPhrase(step.source) : "",
      source_tense: step.source?.tense || "",
      target_tense: step.target.tense,
      target_person: step.target.person.he,
    },
  };
  els.conjugationPresent.textContent = currentConjugation.present;
  els.conjugationPresent.dir = "rtl";
  els.conjugationPrompt.textContent = step.prompt;
  els.conjugationPrompt.dir = step.promptKind === "italian_seed" ? "ltr" : "rtl";
  els.conjugationAnswer.value = "";
  els.conjugationFeedback.hidden = true;
  els.conjugationFeedback.textContent = "";
  activeHebrewInput = els.conjugationAnswer;
  conjugationPromptStartedAt = Date.now();
  els.conjugationTimer.textContent = "0.0s";
}

function checkConjugationAnswer() {
  if (!currentConjugation) return;
  if (!els.conjugationFeedback.hidden) return;
  const rawAnswer = els.conjugationAnswer.value.trim();
  const ok = isConjugationAnswerCorrect(rawAnswer, currentConjugation.expected);
  const elapsed = (Date.now() - conjugationPromptStartedAt) / 1000;
  const verbLabel = currentConjugation.verb.displayInfinitive || currentConjugation.verb.infinitive || currentConjugation.verb.italianInfinitive || "";
  const meaning = currentConjugation.verb.italianInfinitive && currentConjugation.verb.italianInfinitive !== verbLabel
    ? ` · ${currentConjugation.verb.italianInfinitive}`
    : "";
  conjugationScore[ok ? "correct" : "miss"] += 1;
  renderConjugationStats();
  conjugationHistory.unshift({
    ok,
    elapsed,
    answer: rawAnswer,
    expected: currentConjugation.expected,
    expectedPhrase: currentConjugation.expectedPhrase,
    present: currentConjugation.present,
    prompt: currentConjugation.targetLabel,
    promptText: els.conjugationPrompt.textContent,
    italian: currentConjugation.italian,
    domino: currentConjugation.domino,
    sourceUrl: currentConjugation.verb.source_url || "",
  });
  handleHebrewRecoveryDominoResult({
    correct: ok,
    reactionTimeMs: Math.round(elapsed * 1000),
    answer: rawAnswer,
    expected: currentConjugation.expected,
    expectedPhrase: currentConjugation.expectedPhrase,
    verbId: currentConjugation.verb.id || "",
  });
  const behavioralEventId = globalThis.crypto?.randomUUID
    ? globalThis.crypto.randomUUID()
    : `${Date.now()}_${Math.random().toString(16).slice(2)}`;
  postEegTaskEvent({
    persist_without_eeg: true,
    behavioral_session_id: ensureConjugationBehavioralSessionId(),
    annotation_type: "conjugation_response",
    event: {
      event_id: behavioralEventId,
      timestamp: new Date().toISOString(),
      ok,
      reaction_time_ms: Math.round(elapsed * 1000),
      answer: rawAnswer,
      expected: currentConjugation.expected,
      expected_phrase: currentConjugation.expectedPhrase,
      present: currentConjugation.present,
      prompt: currentConjugation.targetLabel,
      prompt_text: els.conjugationPrompt.textContent,
      italian: currentConjugation.italian,
      domino: currentConjugation.domino,
      verb_id: currentConjugation.verb.id || "",
      verb_source: currentConjugation.verb.source || "",
      source_url: currentConjugation.verb.source_url || "",
      input_mode: lastConjugationSpeech ? "speech_to_text" : "keyboard",
      speech_recognition: lastConjugationSpeech,
      infinitive: currentConjugation.verb.infinitive || currentConjugation.verb.displayInfinitive || "",
      root: currentConjugation.verb.root || "",
      binyan: currentConjugation.verb.binyan || "",
    },
    study_context: conjugationSessionContext(),
  }).finally(() => window.setTimeout(loadHelpProfile, 100));
  renderConjugationHistory();
  els.conjugationFeedback.hidden = false;
  els.conjugationFeedback.className = `conjugation-feedback ${ok ? "ok" : "miss"}`;
  els.conjugationFeedback.innerHTML = `
    <div>${ok ? "Corretto" : rawAnswer ? "Da correggere" : "Risposta vuota: errore"}</div>
    <div>Tempo: ${elapsed.toFixed(1)}s</div>
    <div dir="rtl">תשובה: ${escapeHtml(currentConjugation.expectedPhrase || currentConjugation.expected)}</div>
    <div>${escapeHtml(currentConjugation.italian)} · verbo: ${escapeHtml(verbLabel)}${escapeHtml(meaning)}</div>
    <small>Invio di nuovo: prossimo tassello.</small>
  `;
}

function tickConjugationTimer() {
  const recoveryDomino = activePreset().id === "hebrew_recovery" && hebrewRecoveryFlow?.phase === "domino";
  if (!(activePreset().id === "hebrew_conjugations" || recoveryDomino) || !currentConjugation || !els.conjugationFeedback.hidden) {
    return;
  }
  els.conjugationTimer.textContent = `${((Date.now() - conjugationPromptStartedAt) / 1000).toFixed(1)}s`;
}

function updateFlashcardDeckSummary() {
  const count = selectedFlashcardDecks.size;
  els.flashcardDeck.value = [...selectedFlashcardDecks].join(", ");
  els.flashcardSelectedSummary.textContent = count
    ? `${count} ${count === 1 ? "colore selezionato" : "colori selezionati"}`
    : "Nessun colore selezionato";
  updateFlashcardSessionFields();
  if (!flashcardCatalog) return;
  els.flashcardCatalog.querySelectorAll("[data-deck-toggle]").forEach((box) => {
    box.checked = selectedFlashcardDecks.has(box.value);
  });
}

async function includeFlashcardColors(decks) {
  const selected = decks.filter((deck) => deck && !importingFlashcardDecks.has(deck));
  if (!selected.length) return;
  selected.forEach((deck) => importingFlashcardDecks.add(deck));
  els.flashcardSelectedSummary.textContent = "Caricamento colore...";
  try {
    const data = await postMemory("import_seed", { decks: selected });
    const imported = Number(data.imported || 0);
    const skipped = Number(data.skipped || 0);
    els.flashcardSelectedSummary.textContent = imported
      ? `${imported} carte aggiunte`
      : skipped
        ? "Colore gia caricato"
        : "Colore attivo";
    if (!currentFlashcard && selected.length) {
      pendingFlashcardDeck = selected[0];
    }
    await refresh();
    await loadHelpProfile();
  } catch (error) {
    if (window.location.protocol !== "file:") {
      els.console.textContent = `Colori: ${error.message}`;
    }
    updateFlashcardDeckSummary();
  } finally {
    selected.forEach((deck) => importingFlashcardDecks.delete(deck));
    if (!importingFlashcardDecks.size) updateFlashcardDeckSummary();
  }
}

function flashcardId(item) {
  return String(item?.id || "");
}

function shuffleFlashcardIds(ids) {
  const shuffled = [...ids];
  for (let index = shuffled.length - 1; index > 0; index -= 1) {
    const other = Math.floor(Math.random() * (index + 1));
    [shuffled[index], shuffled[other]] = [shuffled[other], shuffled[index]];
  }
  return shuffled;
}

function resetFlashcardSessionOrder() {
  flashcardSessionOrder = [];
  flashcardSessionSeen = new Set();
  flashcardSessionSignature = "";
  lastFlashcardId = "";
}

function flashcardSessionDeckSignature() {
  return [...selectedFlashcardDecks].sort().join("|");
}

function ensureFlashcardSessionOrder(items) {
  const ids = items.map(flashcardId).filter(Boolean);
  const signature = `${flashcardSessionDeckSignature()}::${[...ids].sort().join("|")}`;
  if (signature === flashcardSessionSignature) return;
  const currentId = flashcardId(currentFlashcard);
  flashcardSessionSignature = signature;
  flashcardSessionOrder = shuffleFlashcardIds(ids);
  if (currentId && ids.includes(currentId)) flashcardSessionSeen.add(currentId);
}

function flashcardMapById(items) {
  return new Map(items.map((item) => [flashcardId(item), item]).filter(([id]) => id));
}

function nextUniqueFlashcard(items, preferredDeck = "") {
  ensureFlashcardSessionOrder(items);
  const byId = flashcardMapById(items);
  if (!byId.size) return null;
  let candidates = flashcardSessionOrder.filter((id) => byId.has(id) && !flashcardSessionSeen.has(id));
  if (!candidates.length) {
    flashcardSessionOrder = shuffleFlashcardIds([...byId.keys()]);
    [...byId.keys()].forEach((id) => flashcardSessionSeen.delete(id));
    candidates = flashcardSessionOrder;
  }
  if (helpAdaptivePriorities.size) {
    candidates = [...candidates].sort((left, right) =>
      Number(helpAdaptivePriorities.get(right) || 0) - Number(helpAdaptivePriorities.get(left) || 0)
      || flashcardSessionOrder.indexOf(left) - flashcardSessionOrder.indexOf(right));
  }
  const preferredCandidates = preferredDeck
    ? candidates.filter((id) => {
        const item = byId.get(id);
        return item && (item.deck || item.context || "") === preferredDeck;
      })
    : [];
  const candidatePool = preferredCandidates.length ? preferredCandidates : candidates;
  const avoidId = flashcardId(currentFlashcard) || lastFlashcardId;
  const nonRepeated = candidatePool.filter((id) => id !== avoidId);
  const chosenId = nonRepeated[0] || candidatePool[0] || "";
  if (!chosenId) return null;
  flashcardSessionSeen.add(chosenId);
  return byId.get(chosenId) || null;
}

function flashcardSessionItems(items) {
  ensureFlashcardSessionOrder(items);
  const byId = flashcardMapById(items);
  return flashcardSessionOrder.map((id) => byId.get(id)).filter(Boolean);
}

function flashcardOrderValue(item) {
  return Number(item.study_position || item.seed_index || item.source_row || 0);
}

function orderedFlashcards(items) {
  return [...items].sort((a, b) => {
    const deckA = String(a.deck || a.context || "");
    const deckB = String(b.deck || b.context || "");
    const colorA = Number(a.citizen_level || 99);
    const colorB = Number(b.citizen_level || 99);
    return colorA - colorB
      || deckA.localeCompare(deckB)
      || flashcardOrderValue(a) - flashcardOrderValue(b)
      || String(a.id || "").localeCompare(String(b.id || ""));
  });
}

function renderFlashcardCatalog(catalog) {
  flashcardCatalog = catalog;
  selectedFlashcardDecks = new Set();
  const colors = catalog.colors || [];
  els.flashcardCatalog.innerHTML = colors
    .map((group) => {
      const decks = group.decks || [];
      const deck = decks[0] || { deck: colorLabel(group.color), cards: 0 };
      const disabled = Number(group.cards || 0) === 0 ? "disabled" : "";
      return `
        <label class="color-group color-check ${disabled ? "disabled" : ""}" data-color="${escapeHtml(group.color)}" style="--deck-color:${deckColorValue(group.color)}">
          <input type="checkbox" value="${escapeHtml(deck.deck)}" data-deck-toggle ${disabled}>
          <span class="color-dot color-${escapeHtml(String(group.color).replaceAll(" ", "-"))}"></span>
          <span>${escapeHtml(deck.deck)}</span>
          <small>${Number(group.cards || 0)} carte</small>
        </label>
      `;
    })
    .join("");
  els.flashcardCatalog.querySelectorAll("[data-deck-toggle]").forEach((box) => {
    box.addEventListener("change", async () => {
      const wasEmpty = selectedFlashcardDecks.size === 0;
      if (box.checked) {
        if (wasEmpty) flashcardSessionReviewedIds = [];
        selectedFlashcardDecks.add(box.value);
        if (!currentFlashcard) pendingFlashcardDeck = box.value;
      } else {
        selectedFlashcardDecks.delete(box.value);
        if (!selectedFlashcardDecks.size) flashcardSessionReviewedIds = [];
        if (currentFlashcard && (currentFlashcard.deck || currentFlashcard.context || "") === box.value) {
          currentFlashcard = null;
        }
      }
      updateFlashcardDeckSummary();
      renderMemory(window.latestMemoryState);
      if (box.checked) {
        await includeFlashcardColors([box.value]);
      }
    });
  });
  updateFlashcardDeckSummary();
}

async function loadFlashcardCatalog() {
  try {
    const response = await fetch("/api/flashcard_catalog", { cache: "no-store" });
    const catalog = await response.json();
    renderFlashcardCatalog(catalog);
  } catch (error) {
    els.flashcardCatalog.innerHTML = `<div class="catalog-empty">Catalogo non disponibile</div>`;
    els.flashcardSelectedSummary.textContent = error.message || "Catalogo non disponibile";
  }
}

function memoryDepthLabel(score) {
  const value = Number(score || 0);
  if (value >= 82) return "automatica";
  if (value >= 62) return "interiorizzata";
  if (value >= 42) return "recall";
  if (value >= 22) return "riconoscimento";
  return "nuova";
}

function flashcardStatusLabel(item) {
  if (!Number(item?.recall_count || 0) && !(item?.events || []).length) {
    return "nuova";
  }
  return memoryDepthLabel(item?.depth_score || 0);
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function cardFront(item) {
  return item ? item.raw_front ?? item.term ?? "" : "";
}

function cardBack(item) {
  return item ? item.raw_back ?? item.meaning ?? "" : "";
}

function editableText(node) {
  return (node?.innerText || node?.textContent || "").replace(/\u00a0/g, " ").trim();
}

function selectNodeText(node) {
  if (!node) return;
  const selection = window.getSelection();
  const range = document.createRange();
  range.selectNodeContents(node);
  selection.removeAllRanges();
  selection.addRange(range);
}

function isMacEditShortcut(event) {
  const key = String(event.key || "").toLowerCase();
  return (event.metaKey || event.ctrlKey) && ["a", "c", "v", "x", "z", "y"].includes(key);
}

function dispatchInputChanged(node, inputType = "insertText", data = null) {
  let event;
  try {
    event = new InputEvent("input", { bubbles: true, inputType, data });
  } catch {
    event = new Event("input", { bubbles: true });
  }
  node.dispatchEvent(event);
}

function selectedEditableText() {
  const selection = window.getSelection();
  return selection ? selection.toString() : "";
}

async function writeClipboardText(text) {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text);
    return true;
  }
  return false;
}

async function readClipboardText() {
  if (navigator.clipboard?.readText) {
    return navigator.clipboard.readText();
  }
  return "";
}

function replaceEditableSelection(node, text) {
  if (!node || !node.isContentEditable) return;
  node.focus();
  const selection = window.getSelection();
  if (!selection || !selection.rangeCount) return;
  const range = selection.getRangeAt(0);
  range.deleteContents();
  const textNode = document.createTextNode(text);
  range.insertNode(textNode);
  range.setStartAfter(textNode);
  range.collapse(true);
  selection.removeAllRanges();
  selection.addRange(range);
  dispatchInputChanged(node, "insertFromPaste", text);
}

async function handleEditableShortcut(event, node, row, saveFn) {
  if (!isMacEditShortcut(event)) return false;
  const key = String(event.key || "").toLowerCase();
  if (key === "a") {
    event.preventDefault();
    event.stopPropagation();
    selectNodeText(node);
    return true;
  }
  if (key === "c") {
    const text = selectedEditableText();
    if (text) {
      event.preventDefault();
      await writeClipboardText(text).catch(() => false);
    }
    event.stopPropagation();
    return true;
  }
  if (key === "x") {
    const text = selectedEditableText();
    if (text) event.preventDefault();
    if (text && await writeClipboardText(text).catch(() => false)) {
      replaceEditableSelection(node, "");
      if (row) scheduleFlashcardEditSave(row);
    }
    event.stopPropagation();
    return true;
  }
  if (key === "v") {
    event.preventDefault();
    event.stopPropagation();
    const text = await readClipboardText().catch(() => "");
    if (text) {
      replaceEditableSelection(node, text);
      if (row) scheduleFlashcardEditSave(row);
    }
    return true;
  }
  if (key === "z" || key === "y") {
    event.stopPropagation();
    if (saveFn) window.setTimeout(saveFn, 0);
    return true;
  }
  return false;
}

function handlePlainTextPaste(event, node, row) {
  const text = event.clipboardData?.getData("text/plain") || "";
  if (!text) return;
  event.preventDefault();
  event.stopPropagation();
  replaceEditableSelection(node, text);
  if (row) scheduleFlashcardEditSave(row);
}

async function handleTextControlShortcut(event) {
  const node = event.target;
  if (!node || !["INPUT", "TEXTAREA"].includes(node.tagName) || !isMacEditShortcut(event)) return false;
  const key = String(event.key || "").toLowerCase();
  const start = node.selectionStart ?? 0;
  const end = node.selectionEnd ?? start;
  const value = node.value || "";
  if (key === "a") {
    event.preventDefault();
    event.stopPropagation();
    node.select();
    return true;
  }
  if (key === "c") {
    const text = value.slice(start, end);
    if (text) {
      event.preventDefault();
      event.stopPropagation();
      await writeClipboardText(text).catch(() => false);
      return true;
    }
  }
  if (key === "x") {
    const text = value.slice(start, end);
    if (text) {
      event.preventDefault();
      event.stopPropagation();
      if (await writeClipboardText(text).catch(() => false)) {
        node.value = `${value.slice(0, start)}${value.slice(end)}`;
        node.setSelectionRange(start, start);
        dispatchInputChanged(node, "deleteByCut");
      }
      return true;
    }
  }
  if (key === "v") {
    event.preventDefault();
    event.stopPropagation();
    const text = await readClipboardText().catch(() => "");
    if (text) {
      node.value = `${value.slice(0, start)}${text}${value.slice(end)}`;
      const cursor = start + text.length;
      node.setSelectionRange(cursor, cursor);
      dispatchInputChanged(node, "insertFromPaste", text);
    }
    return true;
  }
  return false;
}

function isFlashcardTextEditing() {
  const active = document.activeElement;
  return Boolean(active && els.memoryDueList?.contains(active) && active.isContentEditable);
}

function selectedFlashcardDeckList() {
  return [...selectedFlashcardDecks];
}

function flashcardSessionContext() {
  const streetwise = currentStreetwise.cardId === currentFlashcard?.id && currentStreetwise.items.length
    ? {
        available: true,
        resolution: currentStreetwise.resolution,
        total_matches: currentStreetwise.totalMatches,
        enrichment_ids: currentStreetwise.items.map((item) => item.enrichment_id).filter(Boolean),
        source_ids: currentStreetwise.items.map((item) => item.source_id).filter(Boolean),
      }
    : { available: false };
  const helpEvidence = helpEvidenceSummary();
  return {
    family: "ebraico_moderno",
    test: "flashcards",
    domain_system: "lexical_recall",
    primary_outcomes: ["recall_accuracy", "recall_latency_s", "retention", "re_entry"],
    selected_decks: selectedFlashcardDeckList(),
    active_card_id: currentFlashcard?.id || "",
    active_deck: currentFlashcard?.deck || currentFlashcard?.context || "",
    session_order_size: flashcardSessionOrder.length,
    session_seen_count: flashcardSessionSeen.size,
    random_unique_session: true,
    score: { ...flashcardStats },
    streetwise_enrichment: streetwise,
    help_profiler: helpEvidence,
  };
}

function conjugationSessionContext() {
  const elapsedValues = conjugationHistory.map((entry) => Number(entry.elapsed)).filter((value) => Number.isFinite(value));
  const meanElapsed = elapsedValues.length
    ? elapsedValues.reduce((total, value) => total + value, 0) / elapsedValues.length
    : null;
  return {
    family: "ebraico_moderno",
    test: activePreset().id === "hebrew_recovery" ? "adaptive_recovery" : "coniugazioni",
    domain_system: "grammar_production",
    primary_outcomes: ["production_accuracy", "response_latency_s", "morphological_retrieval"],
    verb_source: "pealim",
    help_profiler: {
      profiler_id: currentHelpProfile?.profiler_id || "help_profiler",
      model_version: currentHelpProfile?.profiler_model_version || "",
      evidence_status: currentHelpProfile?.evidence?.status || "insufficient_data",
    },
    prompt_count: conjugationHistory.length,
    score: { ...conjugationScore },
    mean_latency_s: meanElapsed === null ? null : Number(meanElapsed.toFixed(3)),
    recent_prompts: conjugationHistory.slice(0, 24).map((entry) => ({
      ok: entry.ok,
      elapsed_s: Number(entry.elapsed.toFixed(3)),
      present: entry.present,
      prompt: entry.prompt,
      prompt_text: entry.promptText || "",
      expected: entry.expected,
      expected_phrase: entry.expectedPhrase || "",
      answer: entry.answer,
      italian: entry.italian,
      domino: entry.domino || {},
      source_url: entry.sourceUrl || "",
    })),
  };
}

function updateFlashcardSessionFields() {
  if (activePreset().id !== "hebrew_flashcards") return;
  const decks = selectedFlashcardDeckList();
  const current = currentFlashcard || {};
  els.pieceId.value = current.id || (decks.length ? `flashcards_${decks.join("_").replace(/\W+/g, "_")}`.slice(0, 80) : "hebrew_flashcards");
  els.sessionNote.value = [
    "flashcards",
    decks.length ? `mazzi=${decks.join("+")}` : "mazzi=nessuno",
    `score=${flashcardStats.correct}/${flashcardStats.partial}/${flashcardStats.miss}`,
    current.id ? `carta=${current.id}` : "",
  ].filter(Boolean).join(" · ").slice(0, 180);
}

function apkTaskKind() {
  return activePreset().id || "";
}

function effectiveApkTaskKind() {
  const kind = apkTaskKind();
  const assessmentMap = {
    assessment_consistency: "apk_reaction_time",
    assessment_depth: "apk_treasure_tracker",
    assessment_speed: "apk_go_nogo",
    assessment_recovery: "apk_mantra_quiet",
  };
  if (assessmentMap[kind]) return assessmentMap[kind];
  if (kind.startsWith("program_")) return "apk_mantra_quiet";
  return kind;
}

function resetApkTask() {
  saveApkTaskSession("reset");
  if (apkTask.timeoutId) window.clearTimeout(apkTask.timeoutId);
  stopContinuousGame();
  const preset = activePreset();
  apkTask = {
    taskId: preset.id || "",
    taskLabel: preset.label || "Training Lab",
    condition: preset.condition || preset.id || "training_lab",
    trial: 0,
    difficulty: 1,
    phase: "idle",
    startedAt: Date.now(),
    stimulusAt: 0,
    timeoutId: 0,
    current: null,
    events: [],
    allEvents: [],
    saved: false,
    score: { ok: 0, miss: 0, falseStart: 0 },
    zone: {
      inZoneMs: 0,
      outZoneMs: 0,
      lastAt: 0,
      lastState: null,
      lastEmitAt: 0,
      sampleCount: 0,
      lastScore: 0,
    },
  };
  renderApkTask();
}

function stroopColorById(id) {
  return STROOP_COLORS.find((color) => color.id === id) || STROOP_COLORS[0];
}

function simonDirectionById(id) {
  return SIMON_DIRECTIONS.find((direction) => direction.id === id) || SIMON_DIRECTIONS[0];
}

function setStroopButton(button, color) {
  if (!button || !color) return;
  button.hidden = false;
  button.innerHTML = `<span class="stroop-swatch" aria-hidden="true"></span><span class="stroop-key">${color.key.toUpperCase()}</span>`;
  button.setAttribute("aria-label", color.label);
  button.title = `${color.label} (${color.key.toUpperCase()})`;
  button.style.setProperty("--stroop-color", color.css);
}

function apkTaskContext() {
  const originalKind = apkTask.taskId || apkTaskKind();
  return {
    family: "training_lab",
    task_id: originalKind,
    task_label: apkTask.taskLabel || activePreset().label,
    condition: apkTask.condition || activePreset().condition || originalKind,
    domain_system: trainingLabDomainSystem(originalKind),
    primary_outcomes: trainingLabPrimaryOutcomes(originalKind),
    adaptive_level: apkTask.difficulty,
    tachistoscope_duration_ms: apkTask.current?.duration_ms || null,
    trial_count: apkTask.trial,
    score: { ...apkTask.score },
    zone_metrics: apkTask.zone ? {
      in_zone_s: Math.round(Number(apkTask.zone.inZoneMs || 0) / 1000),
      out_zone_s: Math.round(Number(apkTask.zone.outZoneMs || 0) / 1000),
      sample_count: Number(apkTask.zone.sampleCount || 0),
      last_score: Number(apkTask.zone.lastScore || 0),
      source_pattern: "vendor_zone_progression",
    } : null,
    event_count: (apkTask.allEvents || apkTask.events).length,
    recent_events: apkTask.events.slice(-20),
    source: "training_lab_local_task",
  };
}

function apkSessionPayload(reason = "stop") {
  const context = apkTaskContext();
  const startedAt = apkTask.startedAt || Date.now();
  const sessionId = [
    "task",
    context.task_id || "training",
    new Date(startedAt).toISOString().replace(/[-:T.Z]/g, "").slice(0, 14),
  ].join("_").replace(/[^A-Za-z0-9_.-]/g, "_");
  return {
    session_id: sessionId,
    session_type: "training_lab",
    reason,
    started_at_ms: startedAt,
    ended_at_ms: Date.now(),
    condition: context.condition || context.task_id || "training_lab",
    label: context.task_label || context.task_id || "Training Lab",
    context,
    score: { ...apkTask.score },
    events: (apkTask.allEvents || apkTask.events).slice(),
    covariates: collectSessionCovariates(),
    eeg_linked: Boolean(macActive || sessionFlow.running),
  };
}

function saveApkTaskSession(reason = "stop") {
  const events = apkTask.allEvents || apkTask.events || [];
  if (!events.length || apkTask.saved || apkSaveInFlight) return;
  const payload = apkSessionPayload(reason);
  if (payload.eeg_linked) {
    apkTask.saved = true;
    return;
  }
  apkTask.saved = true;
  apkSaveInFlight = true;
  fetch("/api/job", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action: "save_training_session", params: payload }),
  })
    .then((response) => (response.ok ? response.json() : null))
    .then((data) => {
      if (data && data.ok) {
        els.console.textContent = `Sessione gioco salvata: ${data.session_id || payload.session_id}`;
        refresh();
      }
    })
    .catch(() => {
      apkTask.saved = false;
    })
    .finally(() => {
      apkSaveInFlight = false;
    });
}

function trainingLabDomainSystem(kind) {
  if (kind.startsWith("assessment_")) {
    if (kind.includes("consistency")) return "baseline_consistency";
    if (kind.includes("depth")) return "baseline_depth";
    if (kind.includes("speed")) return "baseline_speed";
    if (kind.includes("recovery")) return "baseline_recovery";
  }
  if (kind.startsWith("program_")) return "guided_program";
  if (kind.includes("reaction")) return "simple_reaction_time";
  if (kind.includes("tachistoscope")) return "brief_visual_encoding";
  if (kind.includes("visual_grid")) return "visual_search_attention";
  if (kind.includes("treasure_tracker")) return "spatial_working_memory";
  if (kind.includes("letter_reconstruction")) return "hebrew_orthographic_assembly";
  if (kind.includes("hand_eye") || kind.includes("tracking")) return "visuomotor_control";
  if (kind.includes("stroop")) return "inhibitory_control";
  if (kind.includes("simon")) return "conflict_monitoring";
  if (kind.includes("go_nogo")) return "response_inhibition";
  if (kind.includes("stability") || kind.includes("motion")) return "signal_regulation";
  if (kind.includes("mantra")) return "attention_regulation";
  if (kind.includes("airballoon")) return "continuous_control";
  if (kind.includes("starship")) return "continuous_avoidance";
  return "cognitive_training";
}

function trainingLabPrimaryOutcomes(kind) {
  if (kind.startsWith("assessment_")) {
    if (kind.includes("consistency")) return ["rt_cv", "false_start_rate", "mean_reaction_time"];
    if (kind.includes("depth")) return ["location_accuracy", "max_span", "depth_load"];
    if (kind.includes("speed")) return ["mean_reaction_time", "commission_errors", "omission_errors"];
    if (kind.includes("recovery")) return ["time_to_baseline", "hrv_proxy", "compliance"];
  }
  if (kind.startsWith("program_")) return ["step_completion", "total_duration_s", "compliance"];
  if (kind.includes("airballoon")) return ["in_zone_ratio", "control_stability", "thrust_count"];
  if (kind.includes("starship")) return ["survival_time_s", "collision_count", "near_miss_count"];
  if (kind.includes("tracking")) return ["hit_rate", "spatial_error", "reaction_time", "adaptive_level"];
  if (kind.includes("visual_grid")) return ["sequence_completion_time", "visual_search_rt", "sequence_errors", "adaptive_level"];
  if (kind.includes("treasure_tracker")) return ["location_accuracy", "tracking_rt", "shuffle_span", "adaptive_level"];
  if (kind.includes("letter_reconstruction")) return ["exact_reconstruction", "edit_distance", "response_time", "adaptive_level"];
  if (kind.includes("hand_eye")) return ["hit_rate", "spatial_error", "reaction_time"];
  if (kind.includes("reaction")) return ["reaction_time", "false_start_rate"];
  if (kind.includes("tachistoscope")) return ["accuracy", "stimulus_duration_ms", "adaptive_threshold"];
  if (kind.includes("stroop") || kind.includes("simon")) return ["accuracy", "reaction_time", "conflict_cost"];
  if (kind.includes("go_nogo")) return ["commission_errors", "omission_errors", "reaction_time"];
  if (kind.includes("stability") || kind.includes("motion")) return ["signal_stability", "artifact_markers", "compliance"];
  return ["accuracy", "latency", "compliance"];
}

function pushApkEvent(type, extra = {}) {
  const event = {
    t_ms: Date.now() - apkTask.startedAt,
    event_type: type,
    task_id: apkTask.taskId || apkTaskKind(),
    trial_id: apkTask.trial,
    ...extra,
  };
  apkTask.events.push(event);
  apkTask.allEvents = apkTask.allEvents || [];
  apkTask.allEvents.push(event);
  apkTask.events = apkTask.events.slice(-80);
  renderApkEvents();
  updateApkSessionFields();
  postEegTaskEvent({
    annotation_type: "training_lab_event",
    event,
    study_context: apkTaskContext(),
  });
  return event;
}

function updateApkSessionFields() {
  const originalKind = apkTaskKind();
  const effectiveKind = effectiveApkTaskKind();
  if (!effectiveKind.startsWith("apk_") && !originalKind.startsWith("assessment_") && !originalKind.startsWith("program_")) return;
  const context = apkTaskContext();
  els.pieceId.value = `${context.task_id}_${String(apkTask.startedAt).slice(-6)}`;
  els.sessionNote.value = [
    "training_lab",
    activePreset().label,
    `prove=${context.trial_count}`,
    `ok=${context.score.ok}`,
    `miss=${context.score.miss}`,
    `false=${context.score.falseStart}`,
    context.zone_metrics && context.zone_metrics.sample_count ? `zona=${context.zone_metrics.in_zone_s}s/${context.zone_metrics.out_zone_s}s` : "",
  ].filter(Boolean).join(" · ").slice(0, 180);
}

function renderApkEvents() {
  if (!els.apkEventList) return;
  els.apkEventCount.textContent = String(apkTask.events.length);
  const rows = apkTask.events.slice(-8).reverse().map((event) => {
    const ms = typeof event.reaction_ms === "number" ? ` · ${event.reaction_ms} ms` : "";
    const response = event.response ? ` · ${escapeHtml(String(event.response))}` : "";
    const congruence = event.congruence ? ` · ${escapeHtml(event.congruence)}` : "";
    const status = event.correct === true ? "ok" : event.correct === false || event.false_start ? "miss" : "";
    return `
      <div class="apk-event ${status}">
        <span>${escapeHtml(event.event_type)}${ms}${response}${congruence}</span>
        <small>${(event.t_ms / 1000).toFixed(1)}s · prova ${event.trial_id || "-"}</small>
      </div>
    `;
  }).join("");
  els.apkEventList.innerHTML = rows || `<div class="memory-empty">Nessun evento.</div>`;
}

function renderApkTask() {
  if (!els.apkPanel) return;
  const preset = activePreset();
  const kind = effectiveApkTaskKind();
  els.apkTaskLabel.textContent = preset.label;
  if ((kind === "apk_stability_balloon" || kind === "apk_live_stability") && apkTask.zone) {
    els.apkTaskStats.textContent = `${Math.round(apkTask.zone.inZoneMs / 1000)}s in zona · ${Math.round(apkTask.zone.outZoneMs / 1000)}s fuori · score ${Number(apkTask.zone.lastScore || 0).toFixed(2)}`;
  } else if (kind === "apk_tachistoscope_adaptive") {
    const duration = tachistoscopeDurationMs();
    els.apkTaskStats.textContent = `${apkTask.trial} prove · ${apkTask.score.ok} ok · ${apkTask.score.miss} miss · soglia ${duration} ms`;
  } else if (kind === "apk_visual_grid") {
    const progress = apkTask.current && apkTask.phase === "visual_grid"
      ? ` · prossimo ${apkTask.current.next}/${apkTask.current.total}`
      : "";
    els.apkTaskStats.textContent = `${apkTask.trial} griglie · ${apkTask.score.ok} hit · ${apkTask.score.miss} errori · livello ${apkTask.difficulty}${progress}`;
  } else if (kind === "apk_treasure_tracker") {
    const progress = apkTask.current && apkTask.phase?.startsWith("treasure")
      ? ` · scambi ${apkTask.current.step_index || 0}/${apkTask.current.shuffle_steps || 0}`
      : "";
    els.apkTaskStats.textContent = `${apkTask.trial} prove · ${apkTask.score.ok} ok · ${apkTask.score.miss} errori · livello ${apkTask.difficulty}${progress}`;
  } else if (kind === "apk_letter_reconstruction") {
    els.apkTaskStats.textContent = `${apkTask.trial} parole · ${apkTask.score.ok} ok · ${apkTask.score.miss} errori · livello ${apkTask.difficulty}`;
  } else {
    els.apkTaskStats.textContent = `${apkTask.trial} prove · ${apkTask.score.ok} ok · ${apkTask.score.miss} miss`;
  }
  els.apkSummary.textContent = preset.hint || "Task locale di training";
  els.apkStimulus.className = "apk-stimulus";
  els.apkStimulusText.style.color = "";
  els.apkStimulusText.innerHTML = "";
  els.apkStimulus.style.removeProperty("--simon-x");
  els.apkStimulus.style.removeProperty("--track-x");
  els.apkStimulus.style.removeProperty("--track-y");
  els.apkStimulus.style.removeProperty("--track-radius");
  els.apkStimulus.style.removeProperty("--grid-size");
  els.apkResponse.parentElement?.classList.toggle("stroop-response-row", kind === "apk_stroop_word");
  els.apkResponse.parentElement?.classList.toggle("simon-response-row", kind === "apk_simon_direction");
  els.apkResponse.parentElement?.classList.toggle("go-nogo-response-row", kind === "apk_go_nogo");
  els.apkResponse.parentElement?.classList.toggle("letter-response-row", kind === "apk_letter_reconstruction");
  els.apkResponse.hidden = true;
  els.apkResponse.value = "";
  els.apkResponse.disabled = false;
  els.apkResponse.removeAttribute("dir");
  els.apkResponse.placeholder = "";
  els.apkTertiaryBtn.hidden = true;
  els.apkQuaternaryBtn.hidden = true;
  els.apkSecondaryBtn.textContent = "Reset";

  if (kind === "apk_reaction_time") {
    els.apkStimulusText.textContent = apkTask.phase === "armed" ? "Attendi..." : apkTask.phase === "go" ? "ORA" : "Reaction Time";
    els.apkStimulus.classList.toggle("go", apkTask.phase === "go");
    els.apkPrimaryBtn.textContent = apkTask.phase === "go" ? "Rispondi" : "Avvia prova";
  } else if (kind === "apk_tachistoscope" || kind === "apk_tachistoscope_adaptive") {
    const idleLabel = kind === "apk_tachistoscope_adaptive" ? `Tachistoscopio ${tachistoscopeDurationMs()} ms` : "Tachistoscopio";
    els.apkStimulusText.textContent = apkTask.current?.visible ? apkTask.current.stimulus : apkTask.phase === "answer" ? "Scrivi cosa hai visto" : idleLabel;
    els.apkResponse.hidden = apkTask.phase !== "answer";
    els.apkPrimaryBtn.textContent = apkTask.phase === "answer" ? "Segna corretta" : "Mostra stimolo";
    els.apkSecondaryBtn.textContent = apkTask.phase === "answer" ? "Segna errore" : "Reset";
  } else if (kind === "apk_hand_eye") {
    els.apkStimulusText.textContent = apkTask.current?.visible ? "●" : "Coordinazione";
    els.apkStimulus.classList.toggle("target", Boolean(apkTask.current?.visible));
    els.apkPrimaryBtn.textContent = apkTask.phase === "target" ? "Flusso attivo" : "Avvia flusso";
  } else if (kind === "apk_adaptive_tracking") {
    els.apkStimulus.classList.add("adaptive-tracking");
    els.apkStimulus.classList.toggle("tracking-active", Boolean(apkTask.current?.visible));
    els.apkStimulusText.textContent = apkTask.phase === "tracking" ? `livello ${apkTask.difficulty}` : "Tracking";
    if (apkTask.current?.visible) {
      els.apkStimulus.style.setProperty("--track-x", `${apkTask.current.x}%`);
      els.apkStimulus.style.setProperty("--track-y", `${apkTask.current.y}%`);
      els.apkStimulus.style.setProperty("--track-radius", `${apkTask.current.radiusPct}%`);
    }
    els.apkPrimaryBtn.textContent = apkTask.phase === "tracking" ? "Flusso attivo" : "Avvia flusso";
    els.apkSecondaryBtn.textContent = "Reset";
  } else if (kind === "apk_visual_grid") {
    els.apkStimulus.classList.add("visual-grid");
    els.apkStimulusText.innerHTML = renderVisualGridStimulus();
    els.apkPrimaryBtn.textContent = apkTask.phase === "visual_grid" ? "Flusso attivo" : "Avvia flusso";
    els.apkSecondaryBtn.textContent = "Reset";
  } else if (kind === "apk_treasure_tracker") {
    els.apkStimulus.classList.add("treasure-tracker");
    els.apkStimulusText.innerHTML = renderTreasureTrackerStimulus();
    els.apkPrimaryBtn.textContent = apkTask.phase?.startsWith("treasure") ? "Flusso attivo" : "Avvia flusso";
    els.apkSecondaryBtn.textContent = "Reset";
  } else if (kind === "apk_letter_reconstruction") {
    els.apkStimulus.classList.add("letter-reconstruction");
    els.apkStimulusText.innerHTML = renderLetterReconstructionStimulus();
    els.apkResponse.hidden = !["letter_answer", "letter_feedback"].includes(apkTask.phase);
    els.apkResponse.disabled = apkTask.phase === "letter_feedback";
    els.apkResponse.placeholder = "scrivi la parola in ebraico";
    els.apkResponse.setAttribute("dir", "rtl");
    els.apkPrimaryBtn.textContent = apkTask.phase === "letter_feedback" ? "Prossima" : apkTask.phase === "letter_answer" ? "Controlla" : "Avvia flusso";
    els.apkSecondaryBtn.textContent = apkTask.phase === "letter_answer" ? "Salta" : "Reset";
  } else if (kind === "apk_stroop_word") {
    els.apkStimulus.classList.add("stroop");
    if (apkTask.phase === "stroop" && apkTask.current) {
      const ink = stroopColorById(apkTask.current.ink);
      els.apkStimulusText.textContent = apkTask.current.wordLabel;
      els.apkStimulusText.style.color = ink.css;
      setStroopButton(els.apkPrimaryBtn, stroopColorById("red"));
      setStroopButton(els.apkSecondaryBtn, stroopColorById("green"));
      setStroopButton(els.apkTertiaryBtn, stroopColorById("yellow"));
      setStroopButton(els.apkQuaternaryBtn, stroopColorById("blue"));
    } else {
      els.apkStimulusText.textContent = "Stroop";
      els.apkPrimaryBtn.textContent = "Avvia flusso";
      els.apkSecondaryBtn.textContent = "Reset";
      els.apkTertiaryBtn.hidden = true;
      els.apkQuaternaryBtn.hidden = true;
    }
  } else if (kind === "apk_simon_direction") {
    els.apkStimulus.classList.add("simon");
    els.apkTertiaryBtn.hidden = true;
    els.apkQuaternaryBtn.hidden = true;
    if (apkTask.phase === "simon" && apkTask.current) {
      const word = simonDirectionById(apkTask.current.word);
      const side = simonDirectionById(apkTask.current.side);
      els.apkStimulusText.textContent = word.label;
      els.apkStimulus.style.setProperty("--simon-x", side.id === "left" ? "24%" : "76%");
      els.apkPrimaryBtn.textContent = "Sinistra";
      els.apkSecondaryBtn.textContent = "Destra";
      els.apkPrimaryBtn.title = "Sinistra";
      els.apkSecondaryBtn.title = "Destra";
    } else {
      els.apkStimulusText.textContent = "Simon";
      els.apkPrimaryBtn.textContent = "Avvia flusso";
      els.apkSecondaryBtn.textContent = "Reset";
    }
  } else if (kind === "apk_go_nogo") {
    els.apkStimulus.classList.add("go-nogo");
    els.apkTertiaryBtn.hidden = true;
    els.apkQuaternaryBtn.hidden = true;
    if (apkTask.phase === "go_nogo" && apkTask.current) {
      els.apkStimulus.classList.add(apkTask.current.type === "go" ? "go-cue" : "nogo-cue");
      els.apkStimulusText.textContent = apkTask.current.type === "go" ? "GO" : "NO-GO";
      els.apkPrimaryBtn.textContent = "Rispondi";
      els.apkSecondaryBtn.textContent = "Reset";
    } else {
      els.apkStimulusText.textContent = "Go/No-Go";
      els.apkPrimaryBtn.textContent = "Avvia flusso";
      els.apkSecondaryBtn.textContent = "Reset";
    }
  } else if (kind === "apk_airballoon") {
    els.apkStimulus.classList.add("airballoon");
    els.apkTertiaryBtn.hidden = true;
    els.apkQuaternaryBtn.hidden = true;
    els.apkStimulusText.textContent = apkTask.phase === "airballoon" ? "In volo" : "Airballoon";
    els.apkPrimaryBtn.textContent = "Spinta";
    els.apkSecondaryBtn.textContent = "Spinta forte";
    if (apkTask.current) {
      els.apkStimulus.style.setProperty("--balloon-y", `${(apkTask.current.y * 100).toFixed(1)}%`);
    }
  } else if (kind === "apk_starship") {
    els.apkStimulus.classList.add("starship");
    els.apkTertiaryBtn.hidden = true;
    els.apkQuaternaryBtn.hidden = true;
    els.apkStimulusText.textContent = apkTask.phase === "starship" ? "Vola" : "Starship";
    els.apkPrimaryBtn.textContent = "Su";
    els.apkSecondaryBtn.textContent = "Giu";
    if (apkTask.current) {
      els.apkStimulus.style.setProperty("--ship-y", `${(apkTask.current.y * 100).toFixed(1)}%`);
    }
  } else if (kind === "apk_live_stability") {
    els.apkStimulus.classList.add("live-stability");
    els.apkTertiaryBtn.hidden = true;
    els.apkQuaternaryBtn.hidden = true;
    els.apkStimulusText.textContent = "In attesa EEG";
    els.apkPrimaryBtn.textContent = "Marca stabile";
    els.apkSecondaryBtn.textContent = "Segna artefatto";
    renderLiveStabilityStimulus(latestMacState && latestMacState.live_features);
  } else if (kind === "apk_motion_guard") {
    els.apkStimulus.classList.add("motion-guard");
    els.apkTertiaryBtn.hidden = true;
    els.apkQuaternaryBtn.hidden = true;
    els.apkStimulusText.textContent = "In attesa IMU";
    els.apkPrimaryBtn.textContent = "Marca fermo";
    els.apkSecondaryBtn.textContent = "Segna movimento";
    renderMotionGuardStimulus(latestMacState && latestMacState.live_features);
  } else if (kind === "apk_stability_balloon") {
    els.apkStimulus.classList.add("stability-balloon");
    els.apkTertiaryBtn.hidden = true;
    els.apkQuaternaryBtn.hidden = true;
    els.apkStimulusText.textContent = "In attesa EEG";
    els.apkPrimaryBtn.textContent = "Marca stabile";
    els.apkSecondaryBtn.textContent = "Segna artefatto";
    renderStabilityBalloonStimulus(latestMacState && latestMacState.live_features);
  } else if (kind === "apk_mantra_quiet") {
    els.apkStimulusText.textContent = "Mantra";
    els.apkStimulus.classList.add("breath");
    els.apkPrimaryBtn.textContent = "Segna stabile";
    els.apkSecondaryBtn.textContent = "Distrazione";
  } else {
    els.apkStimulusText.textContent = "Training Lab";
    els.apkPrimaryBtn.textContent = "Avvia";
  }
  if (kind.startsWith("apk_") && !sessionFlow.running) {
    [els.apkPrimaryBtn, els.apkSecondaryBtn, els.apkTertiaryBtn, els.apkQuaternaryBtn].forEach((button) => {
      if (button) button.title = "Esercizio libero. Se l'EEG e attivo, gli eventi vengono sincronizzati.";
    });
  }
  renderApkEvents();
  updateApkSessionFields();
}

function startSimonTrial() {
  if (apkTask.timeoutId) window.clearTimeout(apkTask.timeoutId);
  apkTask.trial += 1;
  const word = SIMON_DIRECTIONS[Math.floor(Math.random() * SIMON_DIRECTIONS.length)];
  const forceIncongruent = Math.random() < 0.55;
  let side = SIMON_DIRECTIONS[Math.floor(Math.random() * SIMON_DIRECTIONS.length)];
  if (forceIncongruent && side.id === word.id) {
    side = SIMON_DIRECTIONS.find((direction) => direction.id !== word.id) || side;
  }
  apkTask.phase = "simon";
  apkTask.current = {
    word: word.id,
    wordLabel: word.label,
    side: side.id,
    sideLabel: side.label,
    congruent: word.id === side.id,
  };
  apkTask.stimulusAt = Date.now();
  pushApkEvent("stimulus_onset", {
    word: word.id,
    side: side.id,
    congruence: apkTask.current.congruent ? "congruente" : "incongruente",
  });
  renderApkTask();
}

function answerSimon(directionId) {
  if (apkTask.phase !== "simon" || !apkTask.current) {
    startSimonTrial();
    return;
  }
  const now = Date.now();
  if (apkTask.lastSimonResponseAt && now - apkTask.lastSimonResponseAt < 280) return;
  apkTask.lastSimonResponseAt = now;
  const reactionMs = now - apkTask.stimulusAt;
  const expected = apkTask.current.word;
  const correct = directionId === expected;
  apkTask.score[correct ? "ok" : "miss"] += 1;
  pushApkEvent("response", {
    response: directionId,
    expected,
    word: apkTask.current.word,
    side: apkTask.current.side,
    reaction_ms: reactionMs,
    congruence: apkTask.current.congruent ? "congruente" : "incongruente",
    correct,
  });
  startSimonTrial();
}

function scheduleGoNoGoNext(delay = GO_NOGO.interTrialMs) {
  if (apkTask.timeoutId) window.clearTimeout(apkTask.timeoutId);
  apkTask.timeoutId = window.setTimeout(startGoNoGoTrial, delay);
}

function startGoNoGoTrial() {
  if (apkTask.timeoutId) window.clearTimeout(apkTask.timeoutId);
  apkTask.trial += 1;
  const type = Math.random() < GO_NOGO.goProbability ? "go" : "nogo";
  apkTask.phase = "go_nogo";
  apkTask.current = {
    type,
    expected: type === "go" ? "response" : "withhold",
    response_window_ms: GO_NOGO.responseWindowMs,
  };
  apkTask.stimulusAt = Date.now();
  pushApkEvent("stimulus_onset", {
    stimulus_type: type,
    expected: apkTask.current.expected,
  });
  renderApkTask();
  apkTask.timeoutId = window.setTimeout(resolveGoNoGoTimeout, GO_NOGO.responseWindowMs);
}

function resolveGoNoGoTimeout() {
  if (apkTask.phase !== "go_nogo" || !apkTask.current) return;
  const isNoGo = apkTask.current.type === "nogo";
  const correct = isNoGo;
  apkTask.score[correct ? "ok" : "miss"] += 1;
  pushApkEvent(isNoGo ? "withhold_ok" : "omission", {
    stimulus_type: apkTask.current.type,
    response: "",
    expected: apkTask.current.expected,
    reaction_ms: GO_NOGO.responseWindowMs,
    correct,
  });
  apkTask.phase = "idle";
  apkTask.current = null;
  renderApkTask();
  scheduleGoNoGoNext();
}

function answerGoNoGo() {
  if (apkTask.phase !== "go_nogo" || !apkTask.current) {
    startGoNoGoTrial();
    return;
  }
  if (apkTask.timeoutId) window.clearTimeout(apkTask.timeoutId);
  const reactionMs = Date.now() - apkTask.stimulusAt;
  const isGo = apkTask.current.type === "go";
  const correct = isGo;
  apkTask.score[correct ? "ok" : "miss"] += 1;
  pushApkEvent(isGo ? "response" : "commission_error", {
    stimulus_type: apkTask.current.type,
    response: "press",
    expected: apkTask.current.expected,
    reaction_ms: reactionMs,
    correct,
    false_start: !correct,
  });
  apkTask.phase = "idle";
  apkTask.current = null;
  renderApkTask();
  scheduleGoNoGoNext();
}

function startStroopTrial() {
  if (apkTask.timeoutId) window.clearTimeout(apkTask.timeoutId);
  apkTask.trial += 1;
  const word = STROOP_COLORS[Math.floor(Math.random() * STROOP_COLORS.length)];
  const forceIncongruent = Math.random() < 0.72;
  let ink = STROOP_COLORS[Math.floor(Math.random() * STROOP_COLORS.length)];
  if (forceIncongruent && ink.id === word.id) {
    const alternatives = STROOP_COLORS.filter((color) => color.id !== word.id);
    ink = alternatives[Math.floor(Math.random() * alternatives.length)];
  }
  apkTask.phase = "stroop";
  apkTask.current = {
    word: word.id,
    wordLabel: word.label,
    ink: ink.id,
    inkLabel: ink.label,
    congruent: word.id === ink.id,
  };
  apkTask.stimulusAt = Date.now();
  pushApkEvent("stimulus_onset", {
    word: word.id,
    ink: ink.id,
    congruence: apkTask.current.congruent ? "congruente" : "incongruente",
  });
  renderApkTask();
}

function answerStroop(colorId) {
  if (apkTask.phase !== "stroop" || !apkTask.current) {
    startStroopTrial();
    return;
  }
  const reactionMs = Date.now() - apkTask.stimulusAt;
  const expected = apkTask.current.ink;
  const correct = colorId === expected;
  apkTask.score[correct ? "ok" : "miss"] += 1;
  pushApkEvent("response", {
    response: colorId,
    expected,
    word: apkTask.current.word,
    ink: apkTask.current.ink,
    reaction_ms: reactionMs,
    congruence: apkTask.current.congruent ? "congruente" : "incongruente",
    correct,
  });
  startStroopTrial();
}

function startReactionTrial() {
  if (apkTask.timeoutId) window.clearTimeout(apkTask.timeoutId);
  apkTask.trial += 1;
  apkTask.phase = "armed";
  apkTask.current = { delay_ms: 800 + Math.round(Math.random() * 1800) };
  pushApkEvent("trial_start", { delay_ms: apkTask.current.delay_ms });
  renderApkTask();
  apkTask.timeoutId = window.setTimeout(() => {
    apkTask.phase = "go";
    apkTask.stimulusAt = Date.now();
    pushApkEvent("stimulus_onset");
    renderApkTask();
  }, apkTask.current.delay_ms);
}

function answerReactionTrial() {
  if (apkTask.phase === "armed") {
    if (apkTask.timeoutId) window.clearTimeout(apkTask.timeoutId);
    apkTask.score.falseStart += 1;
    apkTask.phase = "idle";
    pushApkEvent("false_start", { false_start: true, correct: false });
    renderApkTask();
    return;
  }
  if (apkTask.phase !== "go") {
    startReactionTrial();
    return;
  }
  const reactionMs = Date.now() - apkTask.stimulusAt;
  const correct = reactionMs >= 120 && reactionMs <= 1200;
  apkTask.score[correct ? "ok" : "miss"] += 1;
  apkTask.phase = "idle";
  pushApkEvent("response", { reaction_ms: reactionMs, correct });
  renderApkTask();
}

function tachistoscopeDurationMs() {
  if (effectiveApkTaskKind() !== "apk_tachistoscope_adaptive") return 140;
  const level = Math.max(1, Math.min(12, apkTask.difficulty || 1));
  return Math.max(60, Math.min(260, 180 - (level - 1) * 10));
}

function recentTrialsMetrics(events, windowSize = 8) {
  const recent = events.slice(-windowSize).filter((event) => event && (event.correct === true || event.correct === false || event.timeout === true));
  const total = recent.length;
  if (total === 0) return null;
  const correctCount = recent.filter((event) => event.correct === true).length;
  const timeoutCount = recent.filter((event) => event.timeout === true).length;
  const rts = recent.map((event) => Number(event.reaction_ms || 0)).filter((value) => value > 0);
  const meanRT = rts.length ? rts.reduce((a, b) => a + b, 0) / rts.length : 0;
  return {
    total,
    accuracy: correctCount / total,
    timeoutRate: timeoutCount / total,
    meanRT,
  };
}

function recommendApkDifficulty({ current, events, taskType, windowSize = 8, min = 1, max = 12 }) {
  const metrics = recentTrialsMetrics(events, windowSize);
  if (!metrics || metrics.total < 3) {
    return { next: current, reason: "not_enough_trials", delta: 0 };
  }
  const rules = {
    apk_tachistoscope_adaptive: { upAcc: 0.85, downAcc: 0.55, rtMax: 8000, upRT: 2500, label: "tachistoscope" },
    apk_adaptive_tracking: { upAcc: 0.80, downAcc: 0.50, rtMax: 1500, upRT: 600, label: "tracking" },
    apk_treasure_tracker: { upAcc: 0.80, downAcc: 0.50, rtMax: 8000, upRT: 2200, label: "treasure" },
  };
  const rule = rules[taskType] || { upAcc: 0.85, downAcc: 0.55, rtMax: 5000, upRT: 1000, label: "default" };
  let delta = 0;
  let reason = "stable";
  if (metrics.accuracy >= rule.upAcc && metrics.meanRT < rule.upRT) {
    delta = 1;
    reason = "high_accuracy_fast_rt";
  } else if (metrics.accuracy <= rule.downAcc) {
    delta = -1;
    reason = "low_accuracy";
  } else if (metrics.meanRT > rule.rtMax) {
    delta = -1;
    reason = "slow_rt";
  }
  const next = Math.max(min, Math.min(max, current + delta));
  return { next, reason, delta, accuracy: metrics.accuracy, meanRT: metrics.meanRT };
}

function startTachistoscopeTrial() {
  const stimuli = ["ספר", "מלך", "בית", "אני", "C-E-G", "G7", "♩♪♩", "Δ7", "אבג"];
  const stimulus = stimuli[Math.floor(Math.random() * stimuli.length)];
  const durationMs = tachistoscopeDurationMs();
  apkTask.trial += 1;
  apkTask.phase = "flash";
  apkTask.current = { stimulus, visible: true, duration_ms: durationMs, adaptive_level: apkTask.difficulty };
  pushApkEvent("stimulus_onset", {
    stimulus_id: stimulus,
    duration_ms: apkTask.current.duration_ms,
    adaptive_level: apkTask.difficulty,
  });
  renderApkTask();
  apkTask.timeoutId = window.setTimeout(() => {
    apkTask.phase = "answer";
    apkTask.current.visible = false;
    renderApkTask();
    els.apkResponse.focus();
  }, apkTask.current.duration_ms);
}

function gradeTachistoscope(correct) {
  if (apkTask.phase !== "answer") {
    startTachistoscopeTrial();
    return;
  }
  const response = els.apkResponse.value.trim();
  apkTask.score[correct ? "ok" : "miss"] += 1;
  const previousLevel = apkTask.difficulty;
  if (effectiveApkTaskKind() === "apk_tachistoscope_adaptive") {
    const decision = recommendApkDifficulty({
      current: apkTask.difficulty,
      events: apkTask.events,
      taskType: "apk_tachistoscope_adaptive",
      min: 1,
      max: 12,
    });
    apkTask.difficulty = decision.next;
  }
  pushApkEvent("response", {
    stimulus_id: apkTask.current?.stimulus || "",
    response,
    duration_ms: apkTask.current?.duration_ms || null,
    adaptive_level: previousLevel,
    next_level: apkTask.difficulty,
    correct,
    adaptation_reason: effectiveApkTaskKind() === "apk_tachistoscope_adaptive" ? "rolling_accuracy" : undefined,
  });
  apkTask.phase = "idle";
  apkTask.current = null;
  renderApkTask();
}

function startHandEyeTrial() {
  apkTask.trial += 1;
  apkTask.phase = "target";
  apkTask.current = {
    visible: true,
    x: Math.round(18 + Math.random() * 64),
    y: Math.round(22 + Math.random() * 50),
  };
  apkTask.stimulusAt = Date.now();
  els.apkStimulus.style.setProperty("--target-x", `${apkTask.current.x}%`);
  els.apkStimulus.style.setProperty("--target-y", `${apkTask.current.y}%`);
  pushApkEvent("target_onset", { target_x_pct: apkTask.current.x, target_y_pct: apkTask.current.y });
  renderApkTask();
}

function answerHandEye(event) {
  if (effectiveApkTaskKind() !== "apk_hand_eye" || apkTask.phase !== "target" || !apkTask.current) return;
  const rect = els.apkStimulus.getBoundingClientRect();
  const clickX = ((event.clientX - rect.left) / rect.width) * 100;
  const clickY = ((event.clientY - rect.top) / rect.height) * 100;
  const dx = clickX - apkTask.current.x;
  const dy = clickY - apkTask.current.y;
  const missDistance = Math.round(Math.sqrt(dx * dx + dy * dy));
  const reactionMs = Date.now() - apkTask.stimulusAt;
  const correct = missDistance <= 9;
  apkTask.score[correct ? "ok" : "miss"] += 1;
  pushApkEvent("hit", { reaction_ms: reactionMs, miss_distance_pct: missDistance, correct });
  startHandEyeTrial();
}

function startAdaptiveTrackingTrial(delay = 0) {
  if (apkTask.timeoutId) window.clearTimeout(apkTask.timeoutId);
  const run = () => {
    const level = Math.max(1, Math.min(12, apkTask.difficulty || 1));
    const radiusPct = Math.max(4.2, 9.5 - level * 0.38);
    const responseWindowMs = Math.max(560, 1250 - level * 52);
    apkTask.trial += 1;
    apkTask.phase = "tracking";
    apkTask.current = {
      visible: true,
      x: Math.round(12 + Math.random() * 76),
      y: Math.round(18 + Math.random() * 58),
      radiusPct,
      response_window_ms: responseWindowMs,
      level,
    };
    apkTask.stimulusAt = Date.now();
    pushApkEvent("target_onset", {
      target_x_pct: apkTask.current.x,
      target_y_pct: apkTask.current.y,
      radius_pct: Number(radiusPct.toFixed(2)),
      response_window_ms: responseWindowMs,
      level,
    });
    renderApkTask();
    apkTask.timeoutId = window.setTimeout(() => {
      if (apkTask.phase !== "tracking" || !apkTask.current) return;
      apkTask.score.miss += 1;
      pushApkEvent("timeout", {
        correct: false,
        expected: "click_target",
        response_window_ms: responseWindowMs,
        level,
      });
      const decision = recommendApkDifficulty({
        current: apkTask.difficulty,
        events: apkTask.events,
        taskType: "apk_adaptive_tracking",
        min: 1,
        max: 12,
      });
      apkTask.difficulty = decision.next;
      pushApkEvent("level_change", {
        reason: decision.reason,
        previous_level: level,
        next_level: apkTask.difficulty,
      });
      apkTask.phase = "idle";
      apkTask.current = null;
      renderApkTask();
      startAdaptiveTrackingTrial(220);
    }, responseWindowMs);
  };
  if (delay > 0) {
    apkTask.timeoutId = window.setTimeout(run, delay);
  } else {
    run();
  }
}

function answerAdaptiveTracking(event) {
  if (effectiveApkTaskKind() !== "apk_adaptive_tracking") return;
  if (apkTask.phase !== "tracking" || !apkTask.current) {
    startAdaptiveTrackingTrial();
    return;
  }
  if (apkTask.timeoutId) window.clearTimeout(apkTask.timeoutId);
  const rect = els.apkStimulus.getBoundingClientRect();
  const clickX = ((event.clientX - rect.left) / rect.width) * 100;
  const clickY = ((event.clientY - rect.top) / rect.height) * 100;
  const dx = clickX - apkTask.current.x;
  const dy = clickY - apkTask.current.y;
  const missDistance = Math.sqrt(dx * dx + dy * dy);
  const reactionMs = Date.now() - apkTask.stimulusAt;
  const correct = missDistance <= apkTask.current.radiusPct;
  apkTask.score[correct ? "ok" : "miss"] += 1;
  pushApkEvent(correct ? "hit" : "spatial_error", {
    reaction_ms: reactionMs,
    miss_distance_pct: Number(missDistance.toFixed(2)),
    radius_pct: Number(apkTask.current.radiusPct.toFixed(2)),
    level: apkTask.current.level,
    correct,
  });
  const decision = recommendApkDifficulty({
    current: apkTask.difficulty,
    events: apkTask.events,
    taskType: "apk_adaptive_tracking",
    min: 1,
    max: 12,
  });
  apkTask.difficulty = decision.next;
  pushApkEvent("level_change", {
    reason: decision.reason,
    previous_level: apkTask.current.level,
    next_level: apkTask.difficulty,
    accuracy: decision.accuracy,
    mean_rt_ms: decision.meanRT,
  });
  apkTask.phase = "idle";
  apkTask.current = null;
  renderApkTask();
  startAdaptiveTrackingTrial(180);
}

function visualGridSize() {
  const level = Math.max(1, Math.min(9, apkTask.difficulty || 1));
  return Math.max(VISUAL_GRID.minSize, Math.min(VISUAL_GRID.maxSize, VISUAL_GRID.minSize + Math.floor((level - 1) / 3)));
}

function renderVisualGridStimulus() {
  if (apkTask.phase !== "visual_grid" || !apkTask.current) {
    return `<span class="visual-grid-idle">Griglia attenzione</span>`;
  }
  const current = apkTask.current;
  const completed = new Set(current.completed || []);
  const cells = (current.numbers || []).map((value) => {
    const done = completed.has(value);
    return `
      <span class="visual-grid-cell${done ? " done" : ""}" data-grid-cell="${value}">
        ${value}
      </span>
    `;
  }).join("");
  return `
    <span class="visual-grid-header">Trova ${current.next}</span>
    <span class="visual-grid-board" style="--grid-size:${current.grid_size}">
      ${cells}
    </span>
  `;
}

function startVisualGridTrial(delay = 0) {
  if (apkTask.timeoutId) window.clearTimeout(apkTask.timeoutId);
  const run = () => {
    const gridSize = visualGridSize();
    const total = gridSize * gridSize;
    const numbers = shuffleItems(Array.from({ length: total }, (_, index) => index + 1));
    const now = Date.now();
    apkTask.trial += 1;
    apkTask.phase = "visual_grid";
    apkTask.current = {
      visible: true,
      grid_size: gridSize,
      total,
      numbers,
      next: 1,
      completed: [],
      errors: 0,
      level: apkTask.difficulty,
      started_at: now,
      last_hit_at: now,
    };
    apkTask.stimulusAt = now;
    pushApkEvent("grid_start", {
      grid_size: gridSize,
      total_items: total,
      level: apkTask.difficulty,
    });
    renderApkTask();
  };
  if (delay > 0) {
    apkTask.timeoutId = window.setTimeout(run, delay);
  } else {
    run();
  }
}

function answerVisualGrid(value) {
  if (effectiveApkTaskKind() !== "apk_visual_grid") return;
  if (apkTask.phase !== "visual_grid" || !apkTask.current) {
    startVisualGridTrial();
    return;
  }
  const current = apkTask.current;
  const selected = Number(value);
  if (!Number.isFinite(selected)) return;
  const now = Date.now();
  const reactionMs = now - (current.last_hit_at || apkTask.stimulusAt || now);
  const expected = current.next;
  const correct = selected === expected;
  if (!correct) {
    current.errors += 1;
    apkTask.score.miss += 1;
    pushApkEvent("grid_error", {
      selected,
      expected,
      reaction_ms: reactionMs,
      grid_size: current.grid_size,
      level: current.level,
      correct: false,
    });
    renderApkTask();
    return;
  }
  current.completed.push(selected);
  current.next += 1;
  current.last_hit_at = now;
  apkTask.score.ok += 1;
  pushApkEvent("grid_hit", {
    sequence_value: selected,
    reaction_ms: reactionMs,
    grid_size: current.grid_size,
    ordinal: selected,
    level: current.level,
    correct: true,
  });
  if (current.next <= current.total) {
    renderApkTask();
    return;
  }
  const totalTimeMs = now - current.started_at;
  const previousLevel = apkTask.difficulty;
  if (current.errors === 0 && totalTimeMs < current.total * 1450) {
    apkTask.difficulty = Math.min(9, apkTask.difficulty + 1);
  } else if (current.errors > Math.max(1, Math.floor(current.total * 0.12))) {
    apkTask.difficulty = Math.max(1, apkTask.difficulty - 1);
  }
  pushApkEvent("grid_complete", {
    grid_size: current.grid_size,
    total_items: current.total,
    completion_time_ms: totalTimeMs,
    errors: current.errors,
    previous_level: previousLevel,
    next_level: apkTask.difficulty,
    correct: true,
  });
  apkTask.phase = "idle";
  apkTask.current = null;
  renderApkTask();
  startVisualGridTrial(VISUAL_GRID.advanceDelayMs);
}

function treasureSlotCount() {
  return apkTask.difficulty >= 6 ? TREASURE_TRACKER.maxSlots : TREASURE_TRACKER.minSlots;
}

function treasureShuffleSteps() {
  const level = Math.max(1, Math.min(10, apkTask.difficulty || 1));
  return Math.max(3, Math.min(10, 2 + level));
}

function renderTreasureTrackerStimulus() {
  if (!apkTask.current || !apkTask.phase?.startsWith("treasure")) {
    return `<span class="treasure-idle">Tracker spaziale</span>`;
  }
  const current = apkTask.current;
  const activeSwap = new Set(current.active_swap || []);
  const mode = apkTask.phase === "treasure_reveal" ? "osserva"
    : apkTask.phase === "treasure_shuffle" ? "segui gli scambi"
    : "dove si trova?";
  const cells = Array.from({ length: current.slot_count }, (_, index) => {
    const isTarget = apkTask.phase === "treasure_reveal" && index === current.target_position;
    const isSwapping = activeSwap.has(index);
    return `
      <span class="treasure-cell${isTarget ? " target" : ""}${isSwapping ? " swapping" : ""}" data-treasure-slot="${index}">
        <span class="treasure-dot"></span>
      </span>
    `;
  }).join("");
  return `
    <span class="treasure-header">${mode}</span>
    <span class="treasure-board" style="--treasure-slots:${current.slot_count}">
      ${cells}
    </span>
  `;
}

function makeTreasureSwaps(slotCount, steps) {
  return Array.from({ length: steps }, () => {
    const first = Math.floor(Math.random() * slotCount);
    let second = Math.floor(Math.random() * slotCount);
    while (second === first) second = Math.floor(Math.random() * slotCount);
    return [first, second];
  });
}

function applyTreasureSwap(current, swap) {
  if (!current || !swap) return;
  const [first, second] = swap;
  if (current.target_position === first) current.target_position = second;
  else if (current.target_position === second) current.target_position = first;
}

function startTreasureTrackerTrial(delay = 0) {
  if (apkTask.timeoutId) window.clearTimeout(apkTask.timeoutId);
  const run = () => {
    const slotCount = treasureSlotCount();
    const steps = treasureShuffleSteps();
    const targetPosition = Math.floor(Math.random() * slotCount);
    apkTask.trial += 1;
    apkTask.phase = "treasure_reveal";
    apkTask.current = {
      slot_count: slotCount,
      target_start: targetPosition,
      target_position: targetPosition,
      shuffle_steps: steps,
      swaps: makeTreasureSwaps(slotCount, steps),
      step_index: 0,
      active_swap: [],
      level: apkTask.difficulty,
      started_at: Date.now(),
      answer_started_at: 0,
    };
    apkTask.stimulusAt = Date.now();
    pushApkEvent("treasure_start", {
      slot_count: slotCount,
      target_start: targetPosition,
      shuffle_steps: steps,
      level: apkTask.difficulty,
    });
    renderApkTask();
    apkTask.timeoutId = window.setTimeout(runTreasureShuffleStep, TREASURE_TRACKER.revealMs);
  };
  if (delay > 0) {
    apkTask.timeoutId = window.setTimeout(run, delay);
  } else {
    run();
  }
}

function runTreasureShuffleStep() {
  if (effectiveApkTaskKind() !== "apk_treasure_tracker" || !apkTask.current) return;
  const current = apkTask.current;
  if (current.step_index >= current.swaps.length) {
    apkTask.phase = "treasure_answer";
    current.active_swap = [];
    current.answer_started_at = Date.now();
    pushApkEvent("treasure_answer_window", {
      slot_count: current.slot_count,
      shuffle_steps: current.shuffle_steps,
      level: current.level,
    });
    renderApkTask();
    apkTask.timeoutId = window.setTimeout(() => answerTreasureTracker(null), TREASURE_TRACKER.answerTimeoutMs);
    return;
  }
  apkTask.phase = "treasure_shuffle";
  const swap = current.swaps[current.step_index];
  current.active_swap = swap;
  current.step_index += 1;
  applyTreasureSwap(current, swap);
  pushApkEvent("treasure_shuffle_step", {
    step_index: current.step_index,
    swap: swap.join("-"),
    slot_count: current.slot_count,
    shuffle_steps: current.shuffle_steps,
  });
  renderApkTask();
  apkTask.timeoutId = window.setTimeout(runTreasureShuffleStep, TREASURE_TRACKER.shuffleStepMs);
}

function answerTreasureTracker(slot) {
  if (effectiveApkTaskKind() !== "apk_treasure_tracker") return;
  if (apkTask.phase !== "treasure_answer" || !apkTask.current) {
    startTreasureTrackerTrial();
    return;
  }
  if (apkTask.timeoutId) window.clearTimeout(apkTask.timeoutId);
  const current = apkTask.current;
  const selected = slot === null || slot === undefined ? null : Number(slot);
  const reactionMs = Date.now() - (current.answer_started_at || Date.now());
  const correct = selected === current.target_position;
  apkTask.score[correct ? "ok" : "miss"] += 1;
  const previousLevel = apkTask.difficulty;
  pushApkEvent(selected === null ? "treasure_timeout" : "treasure_response", {
    response: selected === null ? "" : String(selected + 1),
    selected_slot: selected,
    expected_slot: current.target_position,
    target_start: current.target_start,
    slot_count: current.slot_count,
    shuffle_steps: current.shuffle_steps,
    reaction_ms: reactionMs,
    correct,
  });
  const decision = recommendApkDifficulty({
    current: apkTask.difficulty,
    events: apkTask.events,
    taskType: "apk_treasure_tracker",
    min: 1,
    max: 10,
  });
  apkTask.difficulty = decision.next;
  pushApkEvent("level_change", {
    reason: decision.reason,
    previous_level: previousLevel,
    next_level: apkTask.difficulty,
    accuracy: decision.accuracy,
    mean_rt_ms: decision.meanRT,
  });
  apkTask.phase = "idle";
  apkTask.current = null;
  renderApkTask();
  startTreasureTrackerTrial(TREASURE_TRACKER.nextDelayMs);
}

function normalizeHebrewWord(value) {
  return String(value || "")
    .normalize("NFKD")
    .replace(/[\u0591-\u05bd\u05bf-\u05c7]/g, "")
    .replace(/[^\u05d0-\u05ea]/g, "");
}

function hebrewLetterItems() {
  const memory = window.latestMemoryState || {};
  const seen = new Set();
  const sourceItems = [...(memory.due || []), ...(memory.items || [])];
  const deckFilter = selectedFlashcardDecks && selectedFlashcardDecks.size
    ? (item) => selectedFlashcardDecks.has(item.deck || item.context || "")
    : () => true;
  const items = sourceItems
    .filter(deckFilter)
    .map((item) => {
      const word = normalizeHebrewWord(cardFront(item));
      if (word.length < LETTER_RECONSTRUCTION.minLetters || word.length > LETTER_RECONSTRUCTION.maxLetters) return null;
      if (seen.has(word)) return null;
      seen.add(word);
      return {
        word,
        meaning: cardBack(item),
        deck: item.deck || item.context || "",
        item_id: item.id || "",
      };
    })
    .filter(Boolean);
  return items.length ? items : LETTER_RECONSTRUCTION.fallbackWords;
}

function shuffleHebrewLetters(word) {
  const letters = Array.from(normalizeHebrewWord(word));
  if (letters.length <= 1) return letters;
  let shuffled = letters;
  for (let attempt = 0; attempt < 8; attempt += 1) {
    shuffled = shuffleItems(letters);
    if (shuffled.join("") !== letters.join("")) break;
  }
  return shuffled;
}

function editDistance(a, b) {
  const left = Array.from(a || "");
  const right = Array.from(b || "");
  const dp = Array.from({ length: left.length + 1 }, () => Array(right.length + 1).fill(0));
  for (let i = 0; i <= left.length; i += 1) dp[i][0] = i;
  for (let j = 0; j <= right.length; j += 1) dp[0][j] = j;
  for (let i = 1; i <= left.length; i += 1) {
    for (let j = 1; j <= right.length; j += 1) {
      const cost = left[i - 1] === right[j - 1] ? 0 : 1;
      dp[i][j] = Math.min(
        dp[i - 1][j] + 1,
        dp[i][j - 1] + 1,
        dp[i - 1][j - 1] + cost,
      );
    }
  }
  return dp[left.length][right.length];
}

function renderLetterReconstructionStimulus() {
  if (!apkTask.current || !apkTask.phase?.startsWith("letter")) {
    return `<span class="letter-idle">Ricostruzione lettere</span>`;
  }
  const current = apkTask.current;
  const letters = (current.shuffled_letters || []).map((letter) => `
    <span class="letter-tile">${escapeHtml(letter)}</span>
  `).join("");
  const feedback = apkTask.phase === "letter_feedback"
    ? `
      <span class="letter-feedback ${current.correct ? "ok" : "miss"}">
        ${current.correct ? "corretta" : `target: ${escapeHtml(current.word)}`}
      </span>
      ${current.meaning ? `<span class="letter-meaning">${escapeHtml(current.meaning)}</span>` : ""}
    `
    : `<span class="letter-hint">ricostruisci la parola</span>`;
  return `
    <span class="letter-board" dir="rtl">${letters}</span>
    ${feedback}
  `;
}

function startLetterReconstructionTrial(delay = 0) {
  if (apkTask.timeoutId) window.clearTimeout(apkTask.timeoutId);
  const run = () => {
    const pool = hebrewLetterItems();
    const selected = pool[Math.floor(Math.random() * pool.length)];
    const word = normalizeHebrewWord(selected.word);
    apkTask.trial += 1;
    apkTask.phase = "letter_answer";
    apkTask.current = {
      word,
      meaning: selected.meaning || "",
      deck: selected.deck || "",
      item_id: selected.item_id || "",
      shuffled_letters: shuffleHebrewLetters(word),
      level: apkTask.difficulty,
      started_at: Date.now(),
      correct: null,
    };
    apkTask.stimulusAt = Date.now();
    els.apkResponse.value = "";
    pushApkEvent("letter_prompt", {
      target_length: word.length,
      shuffled: apkTask.current.shuffled_letters.join(""),
      deck: apkTask.current.deck,
      item_id: apkTask.current.item_id,
      level: apkTask.difficulty,
    });
    renderApkTask();
    window.setTimeout(() => {
      if (apkTask.phase === "letter_answer") {
        els.apkResponse.focus();
        activeHebrewInput = els.apkResponse;
      }
    }, 30);
  };
  if (delay > 0) {
    apkTask.timeoutId = window.setTimeout(run, delay);
  } else {
    run();
  }
}

function answerLetterReconstruction(skip = false) {
  if (effectiveApkTaskKind() !== "apk_letter_reconstruction") return;
  if (apkTask.phase === "letter_feedback") {
    startLetterReconstructionTrial();
    return;
  }
  if (apkTask.phase !== "letter_answer" || !apkTask.current) {
    startLetterReconstructionTrial();
    return;
  }
  const current = apkTask.current;
  const response = skip ? "" : normalizeHebrewWord(els.apkResponse.value);
  const distance = editDistance(response, current.word);
  const correct = !skip && response === current.word;
  const reactionMs = Date.now() - (current.started_at || Date.now());
  apkTask.score[correct ? "ok" : "miss"] += 1;
  const previousLevel = apkTask.difficulty;
  if (correct && reactionMs < 6500) {
    apkTask.difficulty = Math.min(10, apkTask.difficulty + 1);
  } else if (!correct) {
    apkTask.difficulty = Math.max(1, apkTask.difficulty - 1);
  }
  current.correct = correct;
  current.response = response;
  current.edit_distance = distance;
  apkTask.phase = "letter_feedback";
  pushApkEvent(skip ? "letter_skip" : "letter_response", {
    response,
    expected: current.word,
    target_length: current.word.length,
    edit_distance: distance,
    reaction_ms: reactionMs,
    deck: current.deck,
    item_id: current.item_id,
    previous_level: previousLevel,
    next_level: apkTask.difficulty,
    correct,
  });
  renderApkTask();
  apkTask.timeoutId = window.setTimeout(() => startLetterReconstructionTrial(), LETTER_RECONSTRUCTION.nextDelayMs);
}

function logMantraEvent(type) {
  apkTask.trial += 1;
  const correct = type === "stable";
  apkTask.score[correct ? "ok" : "miss"] += 1;
  pushApkEvent(type === "stable" ? "in_zone_marker" : "distraction_marker", { correct });
  renderApkTask();
}

function logLiveStabilityMarker(type) {
  apkTask.trial += 1;
  const features = latestMacState && latestMacState.live_features;
  const score = liveStabilityScore(features);
  const correct = type === "stable";
  apkTask.score[correct ? "ok" : "miss"] += 1;
  pushApkEvent(type === "stable" ? "stable_signal_marker" : "artifact_marker", {
    correct,
    live_score: Number(score.toFixed(3)),
    rms: features?.rms,
    peak_to_peak: features?.peak_to_peak,
    saturation_pct: features?.saturation_pct,
    packet_index_gaps: features?.packet_index_gaps,
    contact_state: features?.contact_state,
  });
  renderApkTask();
}

function logMotionGuardMarker(type) {
  apkTask.trial += 1;
  const features = latestMacState && latestMacState.live_features;
  const score = motionGuardScore(features);
  const correct = type === "still";
  apkTask.score[correct ? "ok" : "miss"] += 1;
  pushApkEvent(type === "still" ? "still_marker" : "movement_marker", {
    correct,
    motion_score: score === null ? null : Number(score.toFixed(3)),
    imu_motion_energy: features?.imu_motion_energy,
    imu_event_count: features?.imu_event_count,
    contact_state: features?.contact_state,
  });
  renderApkTask();
}

function stopContinuousGame() {
  if (apkTask.animationFrameId) {
    cancelAnimationFrame(apkTask.animationFrameId);
    apkTask.animationFrameId = null;
  }
  if (apkTask.continuousTimer) {
    window.clearInterval(apkTask.continuousTimer);
    apkTask.continuousTimer = null;
  }
  const stimulus = els.apkStimulus;
  stimulus?.querySelectorAll(".starship-obstacle").forEach((el) => el.remove());
}

function startAirballoonLoop() {
  stopContinuousGame();
  apkTask.phase = "airballoon";
  apkTask.current = {
    y: 0.5,
    velocity: 0.0,
    lastTs: performance.now(),
    inZoneMs: 0,
    outZoneMs: 0,
    lastZone: null,
    zoneSince: performance.now(),
    thrustQueue: 0,
  };
  pushApkEvent("session_start", { source: "eeg_start", game: "airballoon" });
  renderApkTask();

  const targetTop = 0.35;
  const targetBottom = 0.55;
  const gravity = 0.00055;
  const thrust = 0.018;
  const damping = 0.96;

  function frame(now) {
    if (effectiveApkTaskKind() !== "apk_airballoon" || apkTask.phase !== "airballoon") return;
    const state = apkTask.current;
    const dt = Math.min(0.05, (now - state.lastTs) / 1000);
    state.lastTs = now;

    if (state.thrustQueue > 0) {
      state.velocity -= thrust * Math.min(state.thrustQueue, 3);
      state.thrustQueue = 0;
    }
    state.velocity += gravity;
    state.velocity *= damping;
    state.y += state.velocity;
    state.y = Math.max(0.05, Math.min(0.95, state.y));

    const inZone = state.y >= targetTop && state.y <= targetBottom;
    const zone = inZone ? "in" : "out";
    if (state.lastZone !== zone) {
      if (state.lastZone) {
        const elapsed = now - state.zoneSince;
        if (state.lastZone === "in") state.inZoneMs += elapsed;
        else state.outZoneMs += elapsed;
      }
      state.lastZone = zone;
      state.zoneSince = now;
      pushApkEvent("zone_change", { zone, y: Number(state.y.toFixed(4)) });
    }

    if (els.apkStimulus) {
      els.apkStimulus.style.setProperty("--balloon-y", `${(state.y * 100).toFixed(1)}%`);
      const label = inZone ? "IN ZONA" : "FUORI ZONA";
      els.apkStimulusText.textContent = `${label} · ${Math.round(state.inZoneMs / 100) / 10}s`;
    }
    apkTask.animationFrameId = requestAnimationFrame(frame);
  }
  apkTask.animationFrameId = requestAnimationFrame(frame);
}

function airballoonThrust() {
  if (effectiveApkTaskKind() === "apk_airballoon" && apkTask.current) {
    apkTask.current.thrustQueue += 1;
    pushApkEvent("thrust", { y: Number(apkTask.current.y.toFixed(4)) });
  }
}

function startStarshipLoop() {
  stopContinuousGame();
  apkTask.phase = "starship";
  apkTask.current = {
    y: 0.5,
    velocity: 0.0,
    lastTs: performance.now(),
    obstacles: [],
    score: 0,
    surviveMs: 0,
    spawnEveryMs: 1600,
    lastSpawn: performance.now(),
    speed: 0.35,
  };
  pushApkEvent("session_start", { source: "eeg_start", game: "starship" });
  renderApkTask();

  const shipX = 0.22;
  const acceleration = 0.0016;
  const damping = 0.94;

  function frame(now) {
    if (effectiveApkTaskKind() !== "apk_starship" || apkTask.phase !== "starship") return;
    const state = apkTask.current;
    const dt = Math.min(0.05, (now - state.lastTs) / 1000);
    state.lastTs = now;
    state.surviveMs += dt * 1000;

    state.velocity += acceleration * (state.targetY !== undefined ? (state.targetY - state.y) * 2 : 0);
    state.velocity *= damping;
    state.y += state.velocity;
    state.y = Math.max(0.08, Math.min(0.92, state.y));

    if (now - state.lastSpawn > state.spawnEveryMs) {
      state.lastSpawn = now;
      state.obstacles.push({ x: 1.0, y: 0.1 + Math.random() * 0.8, r: 0.05, created: now });
      state.spawnEveryMs = Math.max(700, state.spawnEveryMs - 30);
    }

    const hit = state.obstacles.some((obs) => {
      const dx = (obs.x - shipX) * 4;
      const dy = obs.y - state.y;
      return Math.sqrt(dx * dx + dy * dy) < obs.r + 0.05;
    });

    if (hit) {
      pushApkEvent("collision", { y: Number(state.y.toFixed(4)), survive_s: Number((state.surviveMs / 1000).toFixed(2)) });
      state.score = Math.max(0, state.score - 1);
      state.obstacles = state.obstacles.filter((obs) => {
        const dx = (obs.x - shipX) * 4;
        const dy = obs.y - state.y;
        return Math.sqrt(dx * dx + dy * dy) >= obs.r + 0.05;
      });
    }

    state.obstacles.forEach((obs) => {
      obs.x -= state.speed * dt;
    });
    state.obstacles = state.obstacles.filter((obs) => obs.x > -0.1);

    if (els.apkStimulus) {
      els.apkStimulus.style.setProperty("--ship-y", `${(state.y * 100).toFixed(1)}%`);
      els.apkStimulusText.textContent = `sopravvissuto ${Math.round(state.surviveMs / 100) / 10}s`;
      els.apkStimulus.querySelectorAll(".starship-obstacle").forEach((el) => el.remove());
      state.obstacles.forEach((obs) => {
        const el = document.createElement("div");
        el.className = "starship-obstacle";
        el.style.left = `${(obs.x * 100).toFixed(1)}%`;
        el.style.top = `${(obs.y * 100).toFixed(1)}%`;
        els.apkStimulus.appendChild(el);
      });
    }
    apkTask.animationFrameId = requestAnimationFrame(frame);
  }
  apkTask.animationFrameId = requestAnimationFrame(frame);
}

function starshipMoveToward(clientY) {
  if (effectiveApkTaskKind() !== "apk_starship" || !apkTask.current || !els.apkStimulus) return;
  const rect = els.apkStimulus.getBoundingClientRect();
  const y = (clientY - rect.top) / rect.height;
  starshipSetTarget(y);
}

function starshipSetTarget(y) {
  if (effectiveApkTaskKind() !== "apk_starship" || !apkTask.current) return;
  apkTask.current.targetY = Math.max(0.08, Math.min(0.92, y));
  pushApkEvent("move", { target_y: Number(apkTask.current.targetY.toFixed(4)) });
}

function startApkFlow() {
  const kind = effectiveApkTaskKind();
  if (kind === "apk_reaction_time") startReactionTrial();
  else if (kind === "apk_tachistoscope" || kind === "apk_tachistoscope_adaptive") startTachistoscopeTrial();
  else if (kind === "apk_hand_eye") startHandEyeTrial();
  else if (kind === "apk_adaptive_tracking") startAdaptiveTrackingTrial();
  else if (kind === "apk_visual_grid") startVisualGridTrial();
  else if (kind === "apk_treasure_tracker") startTreasureTrackerTrial();
  else if (kind === "apk_letter_reconstruction") startLetterReconstructionTrial();
  else if (kind === "apk_stroop_word") startStroopTrial();
  else if (kind === "apk_simon_direction") startSimonTrial();
  else if (kind === "apk_go_nogo") startGoNoGoTrial();
  else if (kind === "apk_live_stability" || kind === "apk_stability_balloon") {
    apkTask.phase = "live";
    pushApkEvent("session_start", { source: "eeg_start" });
    renderApkTask();
  } else if (kind === "apk_airballoon") {
    startAirballoonLoop();
  } else if (kind === "apk_starship") {
    startStarshipLoop();
  } else if (kind === "apk_motion_guard") {
    apkTask.phase = "motion";
    pushApkEvent("session_start", { source: "eeg_start" });
    renderApkTask();
  } else if (kind === "apk_mantra_quiet") {
    apkTask.phase = "mantra";
    pushApkEvent("session_start", { source: "eeg_start" });
    renderApkTask();
  }
}

function apkPrimaryAction() {
  if (taskModeForPreset() === "training" && !sessionFlow.running) {
    els.console.textContent = "Premi Start: il gioco parte solo insieme alla registrazione EEG.";
    return;
  }
  const kind = effectiveApkTaskKind();
  if (kind === "apk_reaction_time") answerReactionTrial();
  else if (kind === "apk_tachistoscope" || kind === "apk_tachistoscope_adaptive") gradeTachistoscope(true);
  else if (kind === "apk_hand_eye") startHandEyeTrial();
  else if (kind === "apk_adaptive_tracking") {
    if (apkTask.phase !== "tracking") startAdaptiveTrackingTrial();
  }
  else if (kind === "apk_visual_grid") {
    if (apkTask.phase !== "visual_grid") startVisualGridTrial();
  }
  else if (kind === "apk_treasure_tracker") {
    if (!apkTask.phase?.startsWith("treasure")) startTreasureTrackerTrial();
  }
  else if (kind === "apk_letter_reconstruction") answerLetterReconstruction(false);
  else if (kind === "apk_stroop_word") {
    if (apkTask.phase === "stroop") answerStroop("red");
    else startStroopTrial();
  }
  else if (kind === "apk_simon_direction") {
    if (apkTask.phase === "simon") answerSimon("left");
    else startSimonTrial();
  }
  else if (kind === "apk_go_nogo") {
    if (apkTask.phase === "go_nogo") answerGoNoGo();
    else startGoNoGoTrial();
  }
  else if (kind === "apk_airballoon") airballoonThrust();
  else if (kind === "apk_starship") starshipSetTarget(0.25);
  else if (kind === "apk_live_stability" || kind === "apk_stability_balloon") logLiveStabilityMarker("stable");
  else if (kind === "apk_motion_guard") logMotionGuardMarker("still");
  else if (kind === "apk_mantra_quiet") logMantraEvent("stable");
}

function apkSecondaryAction() {
  if (taskModeForPreset() === "training" && !sessionFlow.running) {
    els.console.textContent = "Premi Start: il gioco parte solo insieme alla registrazione EEG.";
    return;
  }
  const kind = effectiveApkTaskKind();
  if ((kind === "apk_tachistoscope" || kind === "apk_tachistoscope_adaptive") && apkTask.phase === "answer") gradeTachistoscope(false);
  else if (kind === "apk_stroop_word" && apkTask.phase === "stroop") answerStroop("green");
  else if (kind === "apk_simon_direction" && apkTask.phase === "simon") answerSimon("right");
  else if (kind === "apk_letter_reconstruction" && apkTask.phase === "letter_answer") answerLetterReconstruction(true);
  else if (kind === "apk_airballoon") {
    if (apkTask.current) apkTask.current.thrustQueue += 3;
  }
  else if (kind === "apk_starship") starshipSetTarget(0.75);
  else if (kind === "apk_live_stability" || kind === "apk_stability_balloon") logLiveStabilityMarker("artifact");
  else if (kind === "apk_motion_guard") logMotionGuardMarker("movement");
  else if (kind === "apk_mantra_quiet") logMantraEvent("distraction");
  else resetApkTask();
}

function renderFlashcardScore() {
  if (!els.flashcardScore) return;
  els.flashcardScore.textContent = `${flashcardStats.correct} sì · ${flashcardStats.partial} forse · ${flashcardStats.miss} no`;
}

function currentFlashcardRecallMs() {
  if (!currentFlashcard) return 0;
  if (!flashcardTimerActive || !flashcardShownAt) return flashcardRecallElapsedMs;
  if (flashcardAnswerVisible) return flashcardRecallElapsedMs;
  return Math.max(0, Date.now() - flashcardShownAt);
}

function renderFlashcardTimer() {
  if (!els.flashcardTimer) return;
  els.flashcardTimer.textContent = `${(currentFlashcardRecallMs() / 1000).toFixed(1)}s`;
}

function safeExternalUrl(value) {
  try {
    const url = new URL(String(value || ""));
    return ["https:", "http:"].includes(url.protocol) ? url.href : "";
  } catch {
    return "";
  }
}

function streetwiseDateLabel(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return new Intl.DateTimeFormat("it-IT", { year: "numeric", month: "short" }).format(date);
}

function streetwiseEvidenceSummary() {
  if (currentStreetwise.cardId !== currentFlashcard?.id) return null;
  return {
    canonical_item_id: currentStreetwise.canonicalItemId,
    resolution: currentStreetwise.resolution,
    total_matches: currentStreetwise.totalMatches,
    enrichment_ids: currentStreetwise.items.map((item) => item.enrichment_id).filter(Boolean),
    source_ids: currentStreetwise.items.map((item) => item.source_id).filter(Boolean),
    match_types: [...new Set(currentStreetwise.items.map((item) => item.match_type).filter(Boolean))],
  };
}

function helpEvidenceSummary() {
  const itemData = currentHelpItem.cardId === currentFlashcard?.id ? currentHelpItem.data : null;
  const profile = currentHelpProfile;
  return {
    profiler_id: profile?.profiler_id || "help_profiler",
    profiler_model_version: profile?.profiler_model_version || "",
    projection_schema_version: profile?.projection_schema_version || "",
    evidence_status: profile?.evidence?.status || "insufficient_data",
    lexical_norms_release_id: profile?.lexical_norms_ref?.release_id || "",
    item_match: Boolean(itemData?.norms?.matched),
    item_match_type: itemData?.norms?.match_type || "none",
    adaptive_priority: Number(helpAdaptivePriorities.get(String(currentFlashcard?.id || "")) || 0),
    policy: "read_only_projection",
  };
}

function logStreetwiseEvent(eventType, item = null) {
  const evidence = streetwiseEvidenceSummary();
  if (!evidence || !evidence.enrichment_ids.length) return;
  postEegTaskEvent({
    annotation_type: "streetwise_enrichment_event",
    event: {
      event_type: eventType,
      card_id: currentFlashcard?.id || "",
      ...evidence,
      source_id: item?.source_id || "",
      enrichment_id: item?.enrichment_id || "",
    },
    study_context: flashcardSessionContext(),
  });
}

function logStreetwiseExposureIfReady() {
  if (!flashcardAnswerVisible || !currentFlashcard || !currentStreetwise.items.length) return;
  const exposureKey = `${currentFlashcard.id}:${currentStreetwise.items.map((item) => item.enrichment_id).join(",")}`;
  if (streetwiseExposureKey === exposureKey) return;
  streetwiseExposureKey = exposureKey;
  logStreetwiseEvent("evidence_revealed");
}

function bindStreetwiseMediaEvents() {
  els.streetwiseList?.querySelectorAll("[data-streetwise-audio]").forEach((audio) => {
    audio.addEventListener("play", () => {
      const item = currentStreetwise.items.find((candidate) => candidate.enrichment_id === audio.dataset.streetwiseAudio);
      logStreetwiseEvent("audio_play", item || null);
    }, { once: true });
  });
  els.streetwiseList?.querySelectorAll("[data-streetwise-episode]").forEach((link) => {
    link.addEventListener("click", () => {
      const item = currentStreetwise.items.find((candidate) => candidate.enrichment_id === link.dataset.streetwiseEpisode);
      logStreetwiseEvent("episode_open", item || null);
    });
  });
}

function renderStreetwiseEnrichment() {
  if (!els.streetwisePanel || !els.streetwiseList || !els.streetwiseStatus) return;
  const belongsToCard = currentFlashcard && currentStreetwise.cardId === currentFlashcard.id;
  const shouldReveal = Boolean(belongsToCard && flashcardAnswerVisible);
  els.streetwisePanel.hidden = !shouldReveal;
  if (!shouldReveal) return;
  if (currentStreetwise.loading) {
    els.streetwiseStatus.textContent = "ricerca...";
    els.streetwiseList.innerHTML = `<div class="streetwise-empty">Cerco esempi pertinenti nel catalogo locale.</div>`;
    return;
  }
  if (!currentStreetwise.items.length) {
    els.streetwisePanel.hidden = true;
    return;
  }
  els.streetwiseStatus.textContent = `${currentStreetwise.totalMatches} ${currentStreetwise.totalMatches === 1 ? "episodio" : "episodi"}`;
  els.streetwiseList.innerHTML = currentStreetwise.items.map((item) => {
    const episodeUrl = safeExternalUrl(item.episode_url);
    const audioUrl = safeExternalUrl(item.audio_url);
    const excerpt = item.context_excerpt || item.usage_examples?.[0]?.hebrew_excerpt || "";
    const confidence = item.match_confidence === "high" ? "corrispondenza esatta" : "corrispondenza contestuale";
    const date = streetwiseDateLabel(item.published_at);
    return `
      <article class="streetwise-item">
        <div class="streetwise-item-copy">
          <div class="streetwise-item-title">
            ${episodeUrl
              ? `<a href="${escapeHtml(episodeUrl)}" target="_blank" rel="noopener noreferrer" data-streetwise-episode="${escapeHtml(item.enrichment_id)}">${escapeHtml(item.episode_title)}</a>`
              : `<span>${escapeHtml(item.episode_title)}</span>`}
          </div>
          ${excerpt ? `<blockquote dir="auto">${escapeHtml(excerpt)}</blockquote>` : ""}
          <small>${escapeHtml([date, confidence].filter(Boolean).join(" · "))} · enrichment non canonico</small>
        </div>
        ${audioUrl
          ? `<audio controls preload="none" src="${escapeHtml(audioUrl)}" data-streetwise-audio="${escapeHtml(item.enrichment_id)}" aria-label="Audio ${escapeHtml(item.episode_title)}"></audio>`
          : ""}
      </article>
    `;
  }).join("");
  bindStreetwiseMediaEvents();
}

async function loadStreetwiseEnrichment(item) {
  const requestToken = ++streetwiseRequestToken;
  const cardId = item?.id || "";
  const canonicalItemId = item?.canonical_item_id || "";
  currentStreetwise = {
    cardId,
    canonicalItemId,
    loading: Boolean(cardId),
    items: [],
    totalMatches: 0,
    resolution: "none",
  };
  renderStreetwiseEnrichment();
  if (!cardId) return;
  const query = new URLSearchParams({
    canonical_item_id: canonicalItemId,
    hebrew: cardFront(item),
    limit: "3",
  });
  try {
    const response = await fetch(`/api/streetwise_enrichment?${query.toString()}`, { cache: "no-store" });
    if (!response.ok) throw new Error(`Streetwise HTTP ${response.status}`);
    const data = await response.json();
    if (requestToken !== streetwiseRequestToken || currentFlashcard?.id !== cardId) return;
    currentStreetwise = {
      cardId,
      canonicalItemId: data.canonical_item_id || canonicalItemId,
      loading: false,
      items: Array.isArray(data.items) ? data.items : [],
      totalMatches: Number(data.total_matches || 0),
      resolution: data.resolution || "none",
    };
  } catch {
    if (requestToken !== streetwiseRequestToken || currentFlashcard?.id !== cardId) return;
    currentStreetwise = { cardId, canonicalItemId, loading: false, items: [], totalMatches: 0, resolution: "error" };
  }
  renderStreetwiseEnrichment();
  logStreetwiseExposureIfReady();
}

function helpMetricValue(value, suffix = "") {
  const number = Number(value);
  if (!Number.isFinite(number)) return "--";
  return `${number.toFixed(suffix === " ms" ? 0 : 2)}${suffix}`;
}

function renderHelpItem() {
  if (!els.helpItemPanel || !els.helpItemMetrics || !els.helpItemStatus) return;
  const belongsToCard = currentFlashcard && currentHelpItem.cardId === currentFlashcard.id;
  const shouldReveal = Boolean(belongsToCard && flashcardAnswerVisible);
  els.helpItemPanel.hidden = !shouldReveal;
  if (!shouldReveal) return;
  if (currentHelpItem.loading) {
    els.helpItemStatus.textContent = "ricerca...";
    els.helpItemMetrics.innerHTML = `<span class="help-empty">Cerco la forma esatta nelle norme lessicali.</span>`;
    return;
  }
  const data = currentHelpItem.data || {};
  const norms = data.norms || {};
  const personal = data.personal || {};
  if (!norms.matched) {
    els.helpItemStatus.textContent = "non presente";
    els.helpItemMetrics.innerHTML = `
      <span class="help-empty">Forma non rappresentata nel dataset HeLP. Non significa che sia errata o rara.</span>
      <span class="help-personal-line">Osservazioni personali: ${Number(personal.observation_count || 0)}</span>
    `;
    return;
  }
  const lexical = norms.lexical || {};
  const ld = norms.lexical_decision_norms || {};
  const naming = norms.naming_norms || {};
  els.helpItemStatus.textContent = "match esatto";
  els.helpItemMetrics.innerHTML = `
    <div><span>Frequenza corpus</span><strong>${helpMetricValue(lexical.frequency)}</strong></div>
    <div><span>Decisione lessicale</span><strong>${helpMetricValue(ld.median_rt_ms, " ms")}</strong><small>${Number.isFinite(Number(ld.accuracy)) ? `${Math.round(Number(ld.accuracy) * 100)}% accuratezza` : "--"}</small></div>
    <div><span>Denominazione</span><strong>${helpMetricValue(naming.median_rt_ms, " ms")}</strong><small>${Number.isFinite(Number(naming.accuracy)) ? `${Math.round(Number(naming.accuracy) * 100)}% accuratezza` : "--"}</small></div>
    <div><span>Il tuo richiamo</span><strong>${Number(personal.observation_count || 0)}</strong><small>${personal.median_recall_latency_ms == null ? "nessuna latenza" : `${Math.round(Number(personal.median_recall_latency_ms))} ms mediana`}</small></div>
  `;
}

async function loadHelpItem(item) {
  const requestToken = ++helpItemRequestToken;
  const cardId = item?.id || "";
  currentHelpItem = { cardId, loading: Boolean(cardId), data: null };
  renderHelpItem();
  if (!cardId) return;
  const query = new URLSearchParams({ item_id: cardId, hebrew: cardFront(item) });
  try {
    const response = await fetch(`/api/help/item?${query.toString()}`, { cache: "no-store" });
    if (!response.ok) throw new Error(`HeLP HTTP ${response.status}`);
    const data = await response.json();
    if (requestToken !== helpItemRequestToken || currentFlashcard?.id !== cardId) return;
    currentHelpItem = { cardId, loading: false, data };
  } catch {
    if (requestToken !== helpItemRequestToken || currentFlashcard?.id !== cardId) return;
    currentHelpItem = { cardId, loading: false, data: null };
  }
  renderHelpItem();
}

function helpEvidenceLabel(status) {
  return status === "preliminary" ? "profilo preliminare" : "calibrazione";
}

function renderHelpProfile() {
  if (!els.helpProfileSummary || !els.helpProfileDimensions || !els.helpProfileNote) return;
  if (helpProfileLoading) {
    els.helpProfileSummary.innerHTML = `<span class="help-profile-loading">Ricostruzione dagli eventi...</span>`;
    els.helpProfileDimensions.innerHTML = "";
    els.helpProfileNote.textContent = "";
    return;
  }
  const profile = currentHelpProfile;
  if (!profile) {
    els.helpProfileSummary.innerHTML = `<span class="help-profile-loading">Profilo non disponibile.</span>`;
    els.helpProfileDimensions.innerHTML = "";
    els.helpProfileNote.textContent = "HeLP non modifica curriculum o punteggi: legge soltanto gli eventi già registrati.";
    return;
  }
  const evidence = profile.evidence || {};
  const performance = profile.performance || {};
  const coverage = profile.coverage || {};
  const success = performance.success_ratio == null ? null : Number(performance.success_ratio);
  const matched = Number(coverage.lexical_archive_exact_help_match ?? coverage.active_flashcards_exact_help_match ?? 0);
  const active = Number(coverage.lexical_archive_items ?? coverage.active_flashcards ?? 0);
  els.helpProfileSummary.innerHTML = `
    <div><span>Stato</span><strong>${escapeHtml(helpEvidenceLabel(evidence.status))}</strong></div>
    <div><span>Osservazioni</span><strong>${Number(evidence.eligible_observation_count || 0)}</strong><small>${Number(evidence.distinct_session_count || 0)} sessioni</small></div>
    <div><span>Esito personale</span><strong>${success !== null && Number.isFinite(success) ? `${Math.round(success * 100)}%` : "--"}</strong><small>${performance.median_latency_ms == null ? "latenza da raccogliere" : `${Math.round(Number(performance.median_latency_ms))} ms mediana`}</small></div>
    <div><span>Archivio lessicale</span><strong>${matched}/${active}</strong><small>match esatti HeLP, sola evidenza</small></div>
  `;
  const dimensions = [
    ...(profile.root_summaries || []).slice(0, 3)
      .map((item) => ({ ...item, root: displayHebrewRoot(item.root) }))
      .filter((item) => item.root)
      .map((item) => ({ ...item, label: `Radice ${item.root}` })),
    ...(profile.binyan_summaries || []).slice(0, 3).map((item) => ({ label: `Binyan ${item.binyan}`, ...item })),
  ];
  els.helpProfileDimensions.innerHTML = dimensions.length
    ? dimensions.map((item) => `
        <div class="help-dimension">
          <span>${escapeHtml(item.label)}</span>
          <strong>${item.success_ratio == null ? "--" : `${Math.round(Number(item.success_ratio) * 100)}%`}</strong>
          <small>${Number(item.eligible_observation_count || 0)} prove · ${escapeHtml(helpEvidenceLabel(item.evidence_status))}</small>
        </div>
      `).join("")
    : `<span class="help-empty">Radici e binyan appariranno dopo risposte morfologiche registrate.</span>`;
  const minimum = evidence.minimum_policy || {};
  els.helpProfileNote.textContent = evidence.status === "preliminary"
    ? "HeLP propone priorità al percorso adattivo; BrainLab resta responsabile della scelta finale."
    : `Servono almeno ${minimum.observations || 8} osservazioni, ${minimum.sessions || 2} sessioni e ${minimum.items || 2} elementi distinti prima di produrre candidati adattivi.`;
}

async function loadHelpProfile() {
  if (helpProfileLoading) return;
  helpProfileLoading = true;
  renderHelpProfile();
  try {
    const response = await fetch("/api/help/profile", { cache: "no-store" });
    if (!response.ok) throw new Error(`HeLP HTTP ${response.status}`);
    const data = await response.json();
    currentHelpProfile = data.profile || null;
    helpAdaptivePriorities = new Map(
      (currentHelpProfile?.adaptive_candidates || []).map((item) => [String(item.item_id || ""), Number(item.priority || 0)]),
    );
  } catch {
    currentHelpProfile = null;
    helpAdaptivePriorities = new Map();
  } finally {
    helpProfileLoading = false;
    renderHelpProfile();
    if (activePreset().id === "hebrew_recovery") loadHebrewRecoveryPlan(true);
    updateDailyCommand();
  }
}

function newHebrewRecoveryFlow() {
  return {
    phase: "preview",
    phaseIndex: -1,
    trial: null,
    trialIndex: 0,
    activation: [],
    lexical: [],
    domino: [],
    comprehension: [],
    reentry: [],
    reentryResults: [],
    missed: [],
    timeoutId: 0,
  };
}

function medianNumber(values) {
  const usable = values.filter(Number.isFinite).sort((a, b) => a - b);
  if (!usable.length) return null;
  const middle = Math.floor(usable.length / 2);
  return usable.length % 2 ? usable[middle] : (usable[middle - 1] + usable[middle]) / 2;
}

function normalizeItalianAnswer(value) {
  return String(value || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/\([^)]*\)/g, " ")
    .replace(/[^a-z]+/g, " ")
    .trim()
    .replace(/\s+/g, " ");
}

function italianAnswerAlternatives(verb) {
  return String(verb?.italianInfinitive || verb?.italian || "")
    .split(/[|/;,]/)
    .map(normalizeItalianAnswer)
    .filter(Boolean);
}

function displayHebrewRoot(value) {
  return (String(value || "").match(/[\u05d0-\u05ea]/g) || []).join("-");
}

function showRecoveryAnswerFeedback({ correct, answer, expected, onContinue }) {
  if (!els.hebrewRecoveryTaskSurface || !els.hebrewRecoveryStageActions) return;
  const userAnswer = String(answer || "").trim() || "Nessuna risposta";
  const expectedAnswer = Array.isArray(expected) ? expected.filter(Boolean).join(" / ") : String(expected || "").trim();
  els.hebrewRecoveryTaskSurface.innerHTML = `
    <div class="hebrew-recovery-feedback ${correct ? "is-correct" : "is-incorrect"}">
      <span>${correct ? "RISPOSTA CORRETTA" : "DA RIVEDERE"}</span>
      <strong>${correct ? "Corretto" : `Risposta corretta: ${escapeHtml(expectedAnswer)}`}</strong>
      <small>Hai risposto: ${escapeHtml(userAnswer)}</small>
      <button type="button" class="ghost" data-recovery-continue>Continua</button>
    </div>`;
  els.hebrewRecoveryStageActions.innerHTML = `<span>La correzione resta visibile. Premi Invio oppure Continua.</span>`;
  let advanced = false;
  const advance = () => {
    if (advanced) return;
    advanced = true;
    window.removeEventListener("keydown", handleKeydown);
    onContinue();
  };
  const handleKeydown = (event) => {
    if (event.key !== "Enter") return;
    event.preventDefault();
    advance();
  };
  els.hebrewRecoveryTaskSurface.querySelector("[data-recovery-continue]")?.addEventListener("click", advance);
  window.addEventListener("keydown", handleKeydown);
}

function recoveryPhaseIndex() {
  return { activation: 0, lexical: 1, domino: 2, comprehension: 3, reentry: 4, complete: 5 }[hebrewRecoveryFlow?.phase] ?? -1;
}

function setRecoveryStage(moment, title, description, progress = "") {
  if (els.hebrewRecoveryStageMoment) els.hebrewRecoveryStageMoment.textContent = moment;
  if (els.hebrewRecoveryStageTitle) els.hebrewRecoveryStageTitle.textContent = title;
  if (els.hebrewRecoveryStageDescription) els.hebrewRecoveryStageDescription.textContent = description;
  if (els.hebrewRecoveryStageProgress) els.hebrewRecoveryStageProgress.textContent = progress;
}

function logHebrewRecoveryEvent(type, event) {
  return postEegTaskEvent({
    persist_without_eeg: true,
    behavioral_session_id: ensureConjugationBehavioralSessionId(),
    annotation_type: type,
    event: { event_id: globalThis.crypto?.randomUUID?.() || `${Date.now()}_${Math.random()}`, timestamp: new Date().toISOString(), ...event },
    study_context: { ...conjugationSessionContext(), course_mode: "adaptive_recovery", recovery_phase: hebrewRecoveryFlow?.phase || "" },
  });
}

function renderHebrewRecoveryPreview() {
  if (!els.hebrewRecoveryTaskSurface || !els.hebrewRecoveryStageActions) return;
  setRecoveryStage("Prima", "Calibrazione comportamentale", "Misuro controllo e accesso lessicale prima di scegliere la dose. Il domino inizierà soltanto dopo questa misura.", "0 / 5");
  els.hebrewRecoveryTaskSurface.innerHTML = `
    <div class="hebrew-recovery-preview-grid">
      <article data-moment="before"><span>PRIMA</span><strong>Controllo + lessico</strong><small>misuro accuratezza e velocità prima del lavoro</small></article>
      <article data-moment="work"><span>LAVORO</span><strong>Produzione + comprensione</strong><small>la dose si adatta alle risposte osservabili</small></article>
      <article data-moment="after"><span>DOPO</span><strong>Re-entry mirato</strong><small>ripeto errori e risposte lente per un confronto diretto</small></article>
    </div>`;
  els.hebrewRecoveryStageActions.innerHTML = `<span>Parte insieme alla registrazione EEG. Nessun punteggio EEG decide il contenuto.</span>`;
}

function resetHebrewRecoveryFlow() {
  if (hebrewRecoveryFlow?.timeoutId) window.clearTimeout(hebrewRecoveryFlow.timeoutId);
  hebrewRecoveryFlow = newHebrewRecoveryFlow();
  if (els.conjugationWorkspace && activePreset().id === "hebrew_recovery") els.conjugationWorkspace.hidden = true;
  renderHebrewRecoveryPreview();
  renderHebrewRecoveryPlan();
}

function startHebrewRecoveryFlow() {
  if (activePreset().id !== "hebrew_recovery") return;
  resetHebrewRecoveryFlow();
  hebrewRecoveryFlow.phase = "activation";
  hebrewRecoveryFlow.phaseIndex = 0;
  hebrewRecoveryFlow.trialIndex = 0;
  renderHebrewRecoveryPlan();
  scheduleRecoveryActivation();
}

function scheduleRecoveryActivation() {
  const flow = hebrewRecoveryFlow;
  if (!flow || flow.phase !== "activation") return;
  if (flow.trialIndex >= 8) {
    startRecoveryLexical();
    return;
  }
  setRecoveryStage("Prima", "Controllo attentivo", "Rispondi alla direzione della freccia, ignorando il lato in cui compare.", `${flow.trialIndex + 1} / 8`);
  els.hebrewRecoveryTaskSurface.innerHTML = `<div class="hebrew-recovery-trial"><div class="hebrew-recovery-stimulus">•</div><small>mantieni lo sguardo al centro</small></div>`;
  els.hebrewRecoveryStageActions.innerHTML = `<span>Usa ← e → oppure i due pulsanti.</span>`;
  const direction = Math.random() < 0.5 ? "left" : "right";
  const position = Math.random() < 0.5 ? "left" : "right";
  flow.timeoutId = window.setTimeout(() => {
    if (flow !== hebrewRecoveryFlow || flow.phase !== "activation") return;
    flow.trial = { kind: "activation", direction, position, startedAt: Date.now() };
    els.hebrewRecoveryTaskSurface.innerHTML = `
      <div class="hebrew-recovery-trial">
        <div class="hebrew-recovery-stimulus" data-position="${position}">${direction === "left" ? "←" : "→"}</div>
        <div class="hebrew-recovery-response-row">
          <button type="button" class="ghost" data-recovery-direction="left">← Sinistra</button>
          <button type="button" class="ghost" data-recovery-direction="right">Destra →</button>
        </div>
      </div>`;
    els.hebrewRecoveryTaskSurface.querySelectorAll("[data-recovery-direction]").forEach((button) => {
      button.addEventListener("click", () => answerRecoveryActivation(button.dataset.recoveryDirection));
    });
  }, 450 + Math.round(Math.random() * 350));
}

function answerRecoveryActivation(answer) {
  const flow = hebrewRecoveryFlow;
  const trial = flow?.trial;
  if (!flow || flow.phase !== "activation" || !trial) return;
  const reactionTimeMs = Date.now() - trial.startedAt;
  const correct = answer === trial.direction;
  flow.activation.push({ ...trial, answer, correct, reactionTimeMs });
  flow.trial = null;
  flow.trialIndex += 1;
  logHebrewRecoveryEvent("hebrew_recovery_activation_response", { correct, reaction_time_ms: reactionTimeMs, direction: trial.direction, stimulus_position: trial.position });
  els.hebrewRecoveryTaskSurface.innerHTML = `<div class="hebrew-recovery-trial"><strong>${correct ? "Corretto" : "Errore"}</strong><small>${reactionTimeMs} ms</small></div>`;
  flow.timeoutId = window.setTimeout(scheduleRecoveryActivation, 280);
}

function recoveryVerbSample(count) {
  const pool = [...activeConjugationVerbs()];
  for (let index = pool.length - 1; index > 0; index -= 1) {
    const other = Math.floor(Math.random() * (index + 1));
    [pool[index], pool[other]] = [pool[other], pool[index]];
  }
  pool.sort((left, right) =>
    Number(helpAdaptivePriorities.get(String(right.id || "")) || 0)
    - Number(helpAdaptivePriorities.get(String(left.id || "")) || 0));
  return pool.filter((verb) => verb.infinitive && italianAnswerAlternatives(verb).length).slice(0, count);
}

function startRecoveryLexical() {
  const flow = hebrewRecoveryFlow;
  if (!flow) return;
  flow.phase = "lexical";
  flow.phaseIndex = 1;
  flow.trialIndex = 0;
  flow.lexicalQueue = recoveryVerbSample(6);
  if (!flow.lexicalQueue.length) {
    setRecoveryStage("Preparazione", "Caricamento del corpus", "La cache Pealim locale non è ancora disponibile. Attendo i paradigmi prima di proseguire.", "--");
    els.hebrewRecoveryTaskSurface.innerHTML = `<div class="hebrew-recovery-trial"><strong>Preparazione linguistica</strong><small>Nessuna prova viene conteggiata durante l'attesa.</small></div>`;
    flow.timeoutId = window.setTimeout(startRecoveryLexical, 500);
    return;
  }
  renderHebrewRecoveryPlan();
  renderRecoveryLexicalTrial();
}

function renderRecoveryLexicalTrial(reentryTrial = null) {
  const flow = hebrewRecoveryFlow;
  const isReentry = flow?.phase === "reentry";
  const verb = reentryTrial?.verb || flow?.lexicalQueue?.[flow.trialIndex];
  if (!flow || !verb) {
    if (isReentry) finishHebrewRecoveryFlow();
    else startRecoveryDomino();
    return;
  }
  flow.trial = { kind: "lexical", verb, startedAt: Date.now(), reentry: isReentry };
  setRecoveryStage(isReentry ? "Dopo" : "Prima", isReentry ? "Re-entry lessicale" : "Accesso lessicale", "Scrivi il significato italiano dell'infinito. Rispondi senza frase di contorno.", isReentry ? `${flow.reentryIndex + 1} / ${flow.reentry.length}` : `${flow.trialIndex + 1} / ${flow.lexicalQueue.length}`);
  els.hebrewRecoveryTaskSurface.innerHTML = `
    <div class="hebrew-recovery-trial">
      <div class="hebrew-recovery-stimulus" dir="rtl">${escapeHtml(verb.displayInfinitive || verb.infinitive)}</div>
      <input id="hebrewRecoveryLexicalInput" class="hebrew-recovery-lexical-input" autocomplete="off" placeholder="significato in italiano">
    </div>`;
  els.hebrewRecoveryStageActions.innerHTML = `<span>Invio conferma la risposta · fonte paradigmi: Pealim · HeLP caratterizza lo stimolo quando disponibile.</span>`;
  const input = document.querySelector("#hebrewRecoveryLexicalInput");
  input?.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      answerRecoveryLexical(input.value);
    }
  });
  input?.focus();
}

function answerRecoveryLexical(answer) {
  const flow = hebrewRecoveryFlow;
  const trial = flow?.trial;
  if (!flow || !trial || trial.kind !== "lexical") return;
  const expected = italianAnswerAlternatives(trial.verb);
  const normalized = normalizeItalianAnswer(answer);
  const correct = expected.some((item) => normalized === item || (normalized.length > 4 && item.includes(normalized)));
  const reactionTimeMs = Date.now() - trial.startedAt;
  const result = { ...trial, answer, correct, reactionTimeMs };
  if (trial.reentry) flow.reentryResults.push(result);
  else flow.lexical.push(result);
  if (!correct && !trial.reentry) flow.missed.push({ kind: "lexical", verb: trial.verb });
  logHebrewRecoveryEvent(trial.reentry ? "hebrew_recovery_reentry_response" : "hebrew_recovery_lexical_response", {
    correct, reaction_time_ms: reactionTimeMs, answer_raw: answer, answer_normalized: normalized,
    expected: expected, verb_id: trial.verb.id || "", infinitive: trial.verb.infinitive || "",
    root: trial.verb.root || "", binyan: trial.verb.binyan || "",
  });
  flow.trial = null;
  const continueFlow = trial.reentry ? renderNextRecoveryReentry : renderRecoveryLexicalTrial;
  if (trial.reentry) {
    flow.reentryIndex += 1;
  } else {
    flow.trialIndex += 1;
  }
  showRecoveryAnswerFeedback({ correct, answer, expected, onContinue: continueFlow });
}

function startRecoveryDomino() {
  const flow = hebrewRecoveryFlow;
  if (!flow) return;
  flow.phase = "domino";
  flow.phaseIndex = 2;
  flow.dominoStartCount = conjugationHistory.length;
  flow.dominoTarget = 6;
  renderHebrewRecoveryPlan();
  setRecoveryStage("Lavoro", "Domino produttivo Pealim", "Mantieni il verbo e trasforma persona e tempo. Dopo sei risposte il percorso passa automaticamente alla comprensione.", `0 / ${flow.dominoTarget}`);
  els.hebrewRecoveryTaskSurface.innerHTML = `<div class="hebrew-recovery-trial"><strong>Produzione generativa</strong><small>Il tassello attivo è qui sotto.</small></div>`;
  els.hebrewRecoveryStageActions.innerHTML = `<span>Accuratezza e latenza vengono conservate come outcome; EEG e Oura restano contesto.</span>`;
  els.conjugationWorkspace.hidden = false;
  currentConjugation = null;
  conjugationDomino = null;
  nextConjugationPrompt();
}

function handleHebrewRecoveryDominoResult(result) {
  const flow = hebrewRecoveryFlow;
  if (!flow || flow.phase !== "domino") return;
  flow.domino.push(result);
  if (!result.correct) flow.missed.push({ kind: "domino" });
  const count = flow.domino.length;
  setRecoveryStage("Lavoro", "Domino produttivo Pealim", "Mantieni il verbo e trasforma persona e tempo.", `${count} / ${flow.dominoTarget}`);
  if (count >= flow.dominoTarget) window.setTimeout(startRecoveryComprehension, 900);
}

function shuffleRecoveryOptions(items) {
  const values = [...items];
  for (let index = values.length - 1; index > 0; index -= 1) {
    const other = Math.floor(Math.random() * (index + 1));
    [values[index], values[other]] = [values[other], values[index]];
  }
  return values;
}

function recoveryComprehensionSample(count) {
  const verbs = recoveryVerbSample(Math.max(count, 8));
  return verbs.slice(0, count).map((verb) => {
    const targets = conjugationTargetPool(verb);
    const target = randomItem(targets);
    const answer = verb.italianInfinitive || verb.italian;
    const distractors = [...new Set(verbs
      .filter((item) => item.id !== verb.id)
      .map((item) => item.italianInfinitive || item.italian)
      .filter((item) => item && normalizeItalianAnswer(item) !== normalizeItalianAnswer(answer)))]
      .slice(0, 3);
    return target ? { verb, target, phrase: conjugationPhrase(target), answer, options: shuffleRecoveryOptions([answer, ...distractors]) } : null;
  }).filter(Boolean);
}

function startRecoveryComprehension() {
  const flow = hebrewRecoveryFlow;
  if (!flow) return;
  flow.phase = "comprehension";
  flow.phaseIndex = 3;
  flow.trialIndex = 0;
  flow.comprehensionQueue = recoveryComprehensionSample(5);
  els.conjugationWorkspace.hidden = true;
  renderHebrewRecoveryPlan();
  renderRecoveryComprehensionTrial();
}

function renderRecoveryComprehensionTrial(reentryTrial = null) {
  const flow = hebrewRecoveryFlow;
  const isReentry = flow?.phase === "reentry";
  const item = reentryTrial?.item || flow?.comprehensionQueue?.[flow.trialIndex];
  if (!flow || !item) {
    if (isReentry) finishHebrewRecoveryFlow();
    else startRecoveryReentry();
    return;
  }
  flow.trial = { kind: "comprehension", item, startedAt: Date.now(), reentry: isReentry };
  setRecoveryStage(isReentry ? "Dopo" : "Trasferimento", isReentry ? "Re-entry di comprensione" : "Comprensione morfosintattica", "Scegli il significato del verbo nella frase. La forma cambia, il lessema resta lo stesso.", isReentry ? `${flow.reentryIndex + 1} / ${flow.reentry.length}` : `${flow.trialIndex + 1} / ${flow.comprehensionQueue.length}`);
  els.hebrewRecoveryTaskSurface.innerHTML = `
    <div class="hebrew-recovery-trial">
      <div class="hebrew-recovery-stimulus" dir="rtl">${escapeHtml(item.phrase)}</div>
      <div class="hebrew-recovery-response-row">${item.options.map((option, index) => `<button type="button" class="ghost" data-recovery-option-index="${index}">${escapeHtml(option)}</button>`).join("")}</div>
    </div>`;
  els.hebrewRecoveryStageActions.innerHTML = `<span>Qui misuro comprensione della forma, non memoria di una carta.</span>`;
  els.hebrewRecoveryTaskSurface.querySelectorAll("[data-recovery-option-index]").forEach((button) => {
    button.addEventListener("click", () => answerRecoveryComprehension(item.options[Number(button.dataset.recoveryOptionIndex)]));
  });
}

function answerRecoveryComprehension(answer) {
  const flow = hebrewRecoveryFlow;
  const trial = flow?.trial;
  if (!flow || !trial || trial.kind !== "comprehension") return;
  const correct = normalizeItalianAnswer(answer) === normalizeItalianAnswer(trial.item.answer);
  const reactionTimeMs = Date.now() - trial.startedAt;
  const result = { ...trial, answer, correct, reactionTimeMs };
  if (trial.reentry) flow.reentryResults.push(result);
  else flow.comprehension.push(result);
  if (!correct && !trial.reentry) flow.missed.push({ kind: "comprehension", item: trial.item });
  logHebrewRecoveryEvent(trial.reentry ? "hebrew_recovery_reentry_response" : "hebrew_recovery_comprehension_response", {
    correct, reaction_time_ms: reactionTimeMs, answer, expected: trial.item.answer, verb_id: trial.item.verb.id || "", phrase: trial.item.phrase,
    root: trial.item.verb.root || "", binyan: trial.item.verb.binyan || "",
  });
  flow.trial = null;
  const continueFlow = trial.reentry ? renderNextRecoveryReentry : renderRecoveryComprehensionTrial;
  if (trial.reentry) {
    flow.reentryIndex += 1;
  } else {
    flow.trialIndex += 1;
  }
  showRecoveryAnswerFeedback({ correct, answer, expected: trial.item.answer, onContinue: continueFlow });
}

function startRecoveryReentry() {
  const flow = hebrewRecoveryFlow;
  if (!flow) return;
  flow.phase = "reentry";
  flow.phaseIndex = 4;
  flow.reentry = flow.missed.filter((item) => ["lexical", "comprehension"].includes(item.kind)).slice(0, 5);
  if (!flow.reentry.length) {
    flow.reentry = flow.lexical.slice().sort((a, b) => b.reactionTimeMs - a.reactionTimeMs).slice(0, 2).map((item) => ({ kind: "lexical", verb: item.verb }));
  }
  flow.reentryIndex = 0;
  renderHebrewRecoveryPlan();
  renderNextRecoveryReentry();
}

function renderNextRecoveryReentry() {
  const flow = hebrewRecoveryFlow;
  const item = flow?.reentry?.[flow.reentryIndex];
  if (!flow || !item) {
    finishHebrewRecoveryFlow();
    return;
  }
  if (item.kind === "lexical") renderRecoveryLexicalTrial(item);
  else renderRecoveryComprehensionTrial(item);
}

function finishHebrewRecoveryFlow() {
  const flow = hebrewRecoveryFlow;
  if (!flow) return;
  flow.phase = "complete";
  flow.phaseIndex = 5;
  const before = [...flow.activation, ...flow.lexical];
  const learning = [...flow.domino, ...flow.comprehension];
  const correctRatio = (rows) => rows.length ? Math.round(rows.filter((item) => item.correct).length / rows.length * 100) : 0;
  const activationRt = medianNumber(flow.activation.map((item) => item.reactionTimeMs));
  const afterAccuracy = correctRatio(flow.reentryResults);
  setRecoveryStage("Dopo", "Sessione completata", "Il profilo è stato aggiornato dagli eventi osservabili. La prossima sessione ripartirà dagli errori e dalle risposte lente, non da un punteggio EEG.", "5 / 5");
  els.hebrewRecoveryTaskSurface.innerHTML = `
    <div class="hebrew-recovery-summary">
      <div><span>Prima</span><strong>${correctRatio(before)}%</strong><small>${activationRt == null ? "RT da raccogliere" : `${Math.round(activationRt)} ms controllo`}</small></div>
      <div><span>Lavoro</span><strong>${correctRatio(learning)}%</strong><small>${learning.length} risposte misurate</small></div>
      <div><span>Dopo</span><strong>${afterAccuracy}%</strong><small>${flow.reentryResults.length} elementi ripresi</small></div>
    </div>`;
  els.hebrewRecoveryStageActions.innerHTML = `<span>Ora puoi fermare la registrazione. Il riepilogo resta legato agli eventi della sessione.</span>`;
  els.conjugationWorkspace.hidden = true;
  logHebrewRecoveryEvent("hebrew_recovery_session_completed", { before_accuracy: correctRatio(before), learning_accuracy: correctRatio(learning), after_accuracy: afterAccuracy, reentry_count: flow.reentryResults.length, activation_median_rt_ms: activationRt })
    .finally(() => window.setTimeout(loadHelpProfile, 250));
  renderHebrewRecoveryPlan();
}

function renderHebrewRecoveryPlan() {
  if (!els.hebrewRecoveryPhases || !els.hebrewRecoveryStatus || !els.hebrewRecoveryEvidence) return;
  if (hebrewRecoveryPlanLoading) {
    els.hebrewRecoveryPhases.innerHTML = `<div class="hebrew-recovery-loading">Ricostruzione del percorso dalle prestazioni...</div>`;
    return;
  }
  const plan = currentHebrewRecoveryPlan;
  if (!plan) {
    els.hebrewRecoveryStatus.textContent = "Percorso locale";
    els.hebrewRecoveryEvidence.textContent = "Profilo non disponibile";
    els.hebrewRecoveryPhases.innerHTML = `<div class="hebrew-recovery-loading">Parto dalla misura iniziale, calibro la dose e concludo con un re-entry confrontabile.</div>`;
    return;
  }
  const evidence = plan.evidence || {};
  els.hebrewRecoveryStatus.textContent = plan.status_label || "Percorso pronto";
  const sourceLabel = evidence.resources_label || `${evidence.resources_ready || 0}/${evidence.resources_total || 0} fonti operative`;
  els.hebrewRecoveryEvidence.textContent = `${evidence.observations || 0} osservazioni · ${evidence.sessions || 0} sessioni · ${sourceLabel}`;
  if (els.hebrewRecoveryRationale) els.hebrewRecoveryRationale.textContent = plan.rationale || "Piano costruito da prestazioni e fonti linguistiche locali.";
  const activeIndex = recoveryPhaseIndex();
  els.hebrewRecoveryPhases.innerHTML = (plan.phases || []).map((phase, index) => `
    <article class="hebrew-recovery-phase${index === activeIndex ? " is-active" : ""}">
      <span>${String(index + 1).padStart(2, "0")}</span>
      <div><strong>${escapeHtml(phase.label || "Attività")}</strong><small>${escapeHtml(phase.purpose || "")}</small></div>
      <b>${Math.max(1, Math.round(Number(phase.minutes || 1)))} min</b>
    </article>
  `).join("");
}

async function loadHebrewRecoveryPlan(force = false) {
  if (hebrewRecoveryPlanLoading || (currentHebrewRecoveryPlan && !force)) return;
  hebrewRecoveryPlanLoading = true;
  renderHebrewRecoveryPlan();
  try {
    const durationMinutes = Math.max(15, Math.round(Number(els.duration?.value || 1800) / 60));
    const oura = (_lastOuraData && _lastOuraData.data) || {};
    const query = new URLSearchParams({ minutes: String(durationMinutes) });
    if (Number.isFinite(Number(oura.readiness_score))) query.set("readiness", String(oura.readiness_score));
    if (Number.isFinite(Number(oura.sleep_duration_h))) query.set("sleep_h", String(oura.sleep_duration_h));
    const response = await fetch(`/api/hebrew/recovery_plan?${query}`, { cache: "no-store" });
    if (!response.ok) throw new Error(`Recovery HTTP ${response.status}`);
    const data = await response.json();
    currentHebrewRecoveryPlan = data.plan || null;
  } catch {
    currentHebrewRecoveryPlan = null;
  } finally {
    hebrewRecoveryPlanLoading = false;
    renderHebrewRecoveryPlan();
  }
}

function selectFlashcard(item) {
  currentFlashcard = item || null;
  const selectedId = flashcardId(item);
  if (selectedId) flashcardSessionSeen.add(selectedId);
  if (selectedId) lastFlashcardId = selectedId;
  flashcardShownAt = item && flashcardStudyStarted && flashcardTimerActive ? Date.now() : 0;
  flashcardAnswerShownAt = 0;
  flashcardRecallElapsedMs = 0;
  flashcardAnswerVisible = false;
  streetwiseExposureKey = "";
  els.flashcardCard.classList.remove("is-answer-visible");
  if (els.flashcardShowBtn) els.flashcardShowBtn.textContent = "Mostra risposta";
  if (!item) {
    els.flashcardMeta.textContent = "Nessuna carta pronta";
    els.flashcardFront.textContent = "Scegli un colore";
    els.flashcardBack.textContent = "";
    els.flashcardBack.hidden = true;
    els.flashcardCard.style.removeProperty("--deck-color");
    renderFlashcardTimer();
    updateFlashcardSessionFields();
    loadStreetwiseEnrichment(null);
    loadHelpItem(null);
    return;
  }
  const score = Math.round(Number(item.depth_score || 0));
  els.flashcardCard.style.setProperty("--deck-color", deckColorValue(item.citizen_color));
  els.flashcardMeta.textContent = `${item.deck || "Colore"} · ${flashcardStatusLabel(item)} · ${score}%`;
  els.flashcardFront.textContent = cardFront(item) || "(fronte vuoto)";
  els.flashcardBack.textContent = cardBack(item) || "(retro vuoto)";
  els.flashcardBack.hidden = true;
  els.pieceId.value = item.id || "";
  renderFlashcardTimer();
  updateFlashcardSessionFields();
  loadStreetwiseEnrichment(item);
  loadHelpItem(item);
}

function showFlashcardAnswer() {
  if (!currentFlashcard) return;
  if (!flashcardAnswerVisible) {
    if (!flashcardShownAt) {
      flashcardShownAt = Date.now();
    }
    flashcardRecallElapsedMs = flashcardShownAt ? Math.max(0, Date.now() - flashcardShownAt) : 0;
    flashcardAnswerShownAt = Date.now();
  }
  flashcardAnswerVisible = true;
  els.flashcardBack.hidden = false;
  els.flashcardCard.classList.add("is-answer-visible");
  if (els.flashcardShowBtn) els.flashcardShowBtn.textContent = "Risposta visibile";
  renderFlashcardTimer();
  renderStreetwiseEnrichment();
  renderHelpItem();
  logStreetwiseExposureIfReady();
}

function setFlashcardTimerActive(active) {
  const shouldRun = Boolean(active && flashcardStudyStarted && activePreset().id === "hebrew_flashcards");
  if (flashcardTimerActive === shouldRun) return;
  flashcardTimerActive = shouldRun;
  if (flashcardTimerActive && currentFlashcard && !flashcardAnswerVisible) {
    flashcardShownAt = Date.now();
    flashcardRecallElapsedMs = 0;
  }
  if (!flashcardTimerActive && !flashcardAnswerVisible) {
    flashcardShownAt = 0;
    flashcardRecallElapsedMs = 0;
  }
  renderFlashcardTimer();
}

function prepareFlashcardEegSession() {
  const current = currentFlashcard || {};
  const preset = PRESETS.memory.tests.find((test) => test.id === "hebrew_flashcards");
  els.testFamily.value = "memory";
  populatePresets();
  els.testPreset.value = preset.id;
  applyPreset(preset);
  els.pieceId.value = current.id || `flashcards_${Date.now()}`;
  els.sessionNote.value = `flashcards · ${current.deck || els.flashcardDeck.value || "colore"} · ${cardFront(current) || "sessione"}`.slice(0, 180);
  els.phaseLabel.textContent = preset.label;
  els.presetHint.textContent = preset.hint;
}

async function saveFlashcardEdit(itemId, rawFront, rawBack) {
  if (!rawFront || !rawBack) {
    els.console.textContent = "Ebraico e italiano non possono essere vuoti.";
    return null;
  }
  const data = await postMemory("update_item", {
    item_id: itemId,
    raw_front: rawFront,
    raw_back: rawBack,
  });
  reviewedFlashcards.set(data.item.id, data.item);
  if (!reviewedFlashcardIds.includes(data.item.id)) {
    reviewedFlashcardIds.unshift(data.item.id);
  }
  if (currentFlashcard && currentFlashcard.id === data.item.id) {
    currentFlashcard = data.item;
    selectFlashcard(data.item);
  }
  els.console.textContent = "Carta aggiornata nel catalogo.";
  renderMemory(data.memory);
  return data;
}

async function deleteFlashcard(itemId) {
  if (!itemId) return;
  try {
    const data = await postMemory("delete_item", { item_id: itemId });
    if (currentFlashcard && currentFlashcard.id === itemId) {
      currentFlashcard = null;
    }
    reviewedFlashcards.delete(itemId);
    reviewedFlashcardIds = reviewedFlashcardIds.filter((id) => id !== itemId);
    els.console.textContent = "Carta eliminata.";
    renderMemory(data.memory);
  } catch (error) {
    els.console.textContent = `Eliminazione: ${error.message}`;
  }
}

function renderAddFlashcardCard(deck) {
  return `
    <div class="memory-item memory-add-item" data-memory-add-card data-deck="${escapeHtml(deck)}">
      <button class="memory-add" type="button" data-memory-add="${escapeHtml(deck)}" aria-label="Aggiungi carta">+</button>
      <span class="memory-side">Aggiungi</span>
      <span class="memory-term memory-editable" contenteditable="true" role="textbox" data-new-front dir="rtl" spellcheck="false" tabindex="0">עברית</span>
      <span class="memory-meaning memory-editable" contenteditable="true" role="textbox" data-new-back dir="auto" spellcheck="true" tabindex="0">traduzione</span>
      <span class="memory-meta">Invio salva nel mazzo ${escapeHtml(deck)}</span>
    </div>
  `;
}

async function addFlashcardToDeck(deck, rawFront, rawBack) {
  const front = rawFront.trim();
  const back = rawBack.trim();
  if (!deck || !front || !back || front === "עברית" || back.toLowerCase() === "traduzione") {
    els.console.textContent = "Scrivi ebraico e traduzione prima di aggiungere la carta.";
    return;
  }
  try {
    const data = await postMemory("add_flashcard", {
      deck,
      raw_front: front,
      raw_back: back,
    });
    reviewedFlashcards.set(data.item.id, data.item);
    reviewedFlashcardIds = [data.item.id, ...reviewedFlashcardIds.filter((id) => id !== data.item.id)].slice(0, 24);
    pendingNextAfterId = "";
    currentFlashcard = data.item;
    els.console.textContent = "Carta aggiunta al mazzo.";
    renderMemory(data.memory);
  } catch (error) {
    els.console.textContent = `Aggiunta carta: ${error.message}`;
  }
}

async function saveEditableFlashcardRow(row) {
  if (!row || row.dataset.saving === "1") return null;
  const frontNode = row.querySelector("[data-edit-front]");
  const backNode = row.querySelector("[data-edit-back]");
  const front = editableText(frontNode);
  const back = editableText(backNode);
  const changed = [...row.querySelectorAll("[data-edit-front], [data-edit-back]")]
    .some((editable) => editableText(editable) !== editable.dataset.original);
  if (!changed) return null;
  const state = row.querySelector("[data-edit-state]");
  let needsResave = false;
  row.dataset.saving = "1";
  if (state) state.textContent = "salvataggio...";
  try {
    const data = await saveFlashcardEdit(row.dataset.memoryId, front, back);
    if (frontNode) frontNode.dataset.original = front;
    if (backNode) backNode.dataset.original = back;
    needsResave = editableText(frontNode) !== front || editableText(backNode) !== back;
    if (needsResave) {
      row.dataset.dirty = "1";
      if (state) state.textContent = "modifica...";
    } else {
      row.dataset.dirty = "0";
      if (state) state.textContent = "salvata";
    }
    return data;
  } catch (error) {
    els.console.textContent = `Correzione: ${error.message}`;
    if (state) state.textContent = "errore";
    return null;
  } finally {
    row.dataset.saving = "0";
    if (needsResave) scheduleFlashcardEditSave(row);
  }
}

function scheduleFlashcardEditSave(row) {
  if (!row) return;
  const previous = flashcardEditTimers.get(row);
  if (previous) window.clearTimeout(previous);
  const state = row.querySelector("[data-edit-state]");
  row.dataset.dirty = "1";
  if (state) state.textContent = "modifica...";
  const timer = window.setTimeout(() => {
    flashcardEditTimers.delete(row);
    saveEditableFlashcardRow(row);
  }, 700);
  flashcardEditTimers.set(row, timer);
}

function flushFlashcardEditSave(row) {
  if (!row) return;
  const previous = flashcardEditTimers.get(row);
  if (previous) {
    window.clearTimeout(previous);
    flashcardEditTimers.delete(row);
  }
  saveEditableFlashcardRow(row);
}

function renderMemory(memory) {
  if (!memory) return;
  window.latestMemoryState = memory;
  if (isFlashcardTextEditing()) return;
  if (["hebrew_recovery", "hebrew_conjugations"].includes(activePreset().id)) {
    els.memorySummary.textContent = activePreset().id === "hebrew_recovery"
      ? "prima · lavoro · dopo"
      : "presente → passato/futuro";
    return;
  }
  if (activePreset().id === "hebrew_mlf_b2_7") {
    return;
  }
  const selectedDecks = selectedFlashcardDecks;
  const filterByDeck = (item) => !selectedDecks.size || selectedDecks.has(item.deck || item.context || "");
  const due = orderedFlashcards((memory.due || []).filter(filterByDeck));
  const visibleItems = orderedFlashcards((memory.items || []).filter(filterByDeck));
  const selectableItems = visibleItems;
  const total = Number(memory.total || 0);
  const decks = (memory.decks || []).length;
  els.memorySummary.textContent = selectedDecks.size
    ? `${due.length} carte attive · ${decks} colori totali`
    : `${total} carte · scegli un colore`;
  if (!selectedDecks.size) {
    pendingFlashcardDeck = "";
    pendingNextAfterId = "";
    selectFlashcard(null);
    els.memoryDueList.innerHTML = `<div class="memory-empty">Seleziona uno o piu colori.</div>`;
    els.memoryDueCount.textContent = "0";
    return;
  }

  if (pendingFlashcardDeck) {
    const preferredDeck = pendingFlashcardDeck;
    pendingFlashcardDeck = "";
    selectFlashcard(nextUniqueFlashcard(selectableItems, preferredDeck));
  } else if (pendingNextAfterId) {
    pendingNextAfterId = "";
    selectFlashcard(nextUniqueFlashcard(selectableItems));
  } else if (currentFlashcard) {
    const currentDeck = currentFlashcard.deck || currentFlashcard.context || "";
    const updatedCurrent = selectableItems.find((item) => item.id === currentFlashcard.id);
    if (updatedCurrent) currentFlashcard = updatedCurrent;
    else if (currentDeck && !selectedDecks.has(currentDeck)) selectFlashcard(nextUniqueFlashcard(selectableItems));
    else if (!selectableItems.length) selectFlashcard(null);
  } else if (selectableItems.length) {
    selectFlashcard(nextUniqueFlashcard(selectableItems));
  } else {
    selectFlashcard(null);
  }

  let neighborItems = [];
  const orderedItems = flashcardSessionItems(selectableItems);
  if (currentFlashcard && orderedItems.length) {
    const byId = flashcardMapById(selectableItems);
    const currentIndex = orderedItems.findIndex((item) => item.id === currentFlashcard.id);
    const previousId = flashcardSessionReviewedIds.find((id) => id !== currentFlashcard.id && byId.has(id));
    const previousItem = previousId ? byId.get(previousId) : null;
    const nextItem = currentIndex >= 0
      ? orderedItems.slice(currentIndex + 1).find((item) => item.id !== currentFlashcard.id)
        || orderedItems.find((item) => item.id !== currentFlashcard.id)
      : null;
    neighborItems = [
      previousItem ? { item: previousItem, side: "Prima" } : null,
      nextItem ? { item: nextItem, side: "Dopo" } : null,
    ].filter(Boolean);
  }
  const canAddCard = selectedDecks.size === 1;
  els.memoryDueCount.textContent = String(neighborItems.length + (canAddCard ? 1 : 0));

  if (!neighborItems.length && !canAddCard) {
    els.memoryDueList.innerHTML = `<div class="memory-empty">Nessuna carta pronta.</div>`;
    return;
  }
  const neighborHtml = neighborItems
    .map(({ item, side }) => {
      const score = Math.round(Number(item.depth_score || 0));
      const reviewedClass = reviewedFlashcardIds.includes(item.id) ? " reviewed" : "";
      const itemId = escapeHtml(item.id);
      return `
        <div class="memory-item${reviewedClass}" data-memory-id="${itemId}">
          <button class="memory-delete" type="button" data-memory-delete="${itemId}" aria-label="Elimina carta">×</button>
          <span class="memory-side">${side}</span>
          <span class="memory-term memory-editable" contenteditable="true" role="textbox" tabindex="0" data-edit-front dir="rtl" spellcheck="false" style="--deck-color:${deckColorValue(item.citizen_color)}">${escapeHtml(cardFront(item))}</span>
          <span class="memory-meaning memory-editable" contenteditable="true" role="textbox" tabindex="0" data-edit-back dir="auto" spellcheck="true">${escapeHtml(cardBack(item) || "")}</span>
          <span class="memory-meta" style="--deck-color:${deckColorValue(item.citizen_color)}">${escapeHtml(item.deck || "Colore")} · ${escapeHtml(flashcardStatusLabel(item))} · ${score}% <span class="memory-edit-state" data-edit-state></span></span>
        </div>
      `;
    })
    .join("");
  const addHtml = canAddCard ? renderAddFlashcardCard([...selectedDecks][0]) : "";
  els.memoryDueList.innerHTML = neighborHtml + addHtml;
  els.memoryDueList.querySelectorAll("[data-memory-delete]").forEach((node) => {
    node.addEventListener("click", (event) => {
      event.stopPropagation();
      deleteFlashcard(node.dataset.memoryDelete);
    });
  });
  els.memoryDueList.querySelectorAll("[data-edit-front], [data-edit-back]").forEach((node) => {
    const row = node.closest("[data-memory-id]");
    node.dataset.original = editableText(node);
    node.addEventListener("pointerdown", (event) => event.stopPropagation());
    node.addEventListener("mousedown", (event) => event.stopPropagation());
    node.addEventListener("click", (event) => event.stopPropagation());
    node.addEventListener("focus", (event) => {
      event.stopPropagation();
      if (node.matches("[data-edit-front]")) activeHebrewInput = node;
    });
    node.addEventListener("input", (event) => {
      event.stopPropagation();
      scheduleFlashcardEditSave(row);
    });
    node.addEventListener("paste", (event) => {
      handlePlainTextPaste(event, node, row);
    });
    node.addEventListener("keydown", async (event) => {
      if (await handleEditableShortcut(event, node, row)) return;
      event.stopPropagation();
      if (event.key === "Enter") {
        event.preventDefault();
        flushFlashcardEditSave(row);
      }
    });
    node.addEventListener("blur", () => {
      flushFlashcardEditSave(row);
    });
  });
  els.memoryDueList.querySelectorAll("[data-memory-add-card]").forEach((row) => {
    const frontNode = row.querySelector("[data-new-front]");
    const backNode = row.querySelector("[data-new-back]");
    const save = () => addFlashcardToDeck(row.dataset.deck || "", editableText(frontNode), editableText(backNode));
    row.querySelector("[data-memory-add]")?.addEventListener("click", (event) => {
      event.stopPropagation();
      save();
    });
    [frontNode, backNode].forEach((node) => {
      node?.addEventListener("pointerdown", (event) => event.stopPropagation());
      node?.addEventListener("mousedown", (event) => event.stopPropagation());
      node?.addEventListener("click", (event) => event.stopPropagation());
      node?.addEventListener("paste", (event) => {
        handlePlainTextPaste(event, node, null);
      });
      node?.addEventListener("focus", () => {
        if (node.matches("[data-new-front]")) activeHebrewInput = node;
        if (
          (node.matches("[data-new-front]") && editableText(node) === "עברית")
          || (node.matches("[data-new-back]") && editableText(node).toLowerCase() === "traduzione")
        ) {
          selectNodeText(node);
        }
      });
      node?.addEventListener("keydown", async (event) => {
        if (await handleEditableShortcut(event, node, null)) return;
        event.stopPropagation();
        if (event.key === "Enter") {
          event.preventDefault();
          save();
        }
      });
    });
  });
}

async function gradeFlashcard(result) {
  if (!currentFlashcard) {
    els.console.textContent = "Nessuna carta selezionata.";
    return;
  }
  if (!flashcardAnswerVisible) {
    showFlashcardAnswer();
    return;
  }
  const recallMs = currentFlashcardRecallMs();
  const reviewMs = flashcardAnswerShownAt ? Math.max(0, Date.now() - flashcardAnswerShownAt) : 0;
  const latency = Number((recallMs / 1000).toFixed(2));
  const profile = {
    correct: { confidence: 9, effort: 2 },
    partial: { confidence: 6, effort: 6 },
    miss: { confidence: 2, effort: 8 },
  }[result];
  try {
    const data = await postMemory("log_recall", {
      item_id: currentFlashcard.id,
      result,
      latency_s: latency,
      review_s: Number((reviewMs / 1000).toFixed(2)),
      deck: currentFlashcard.deck || currentFlashcard.context || "",
      citizen_color: currentFlashcard.citizen_color || "",
      selected_decks: selectedFlashcardDeckList(),
      front: cardFront(currentFlashcard),
      back: cardBack(currentFlashcard),
      streetwise_evidence: streetwiseEvidenceSummary(),
      help_evidence: helpEvidenceSummary(),
      study_context: flashcardSessionContext(),
      ...profile,
    });
    flashcardStats[result] += 1;
    renderFlashcardScore();
    els.console.textContent = `Carta aggiornata · ${data.item.next_due_label} · profondita ${Math.round(data.item.depth_score || 0)}%`;
    reviewedFlashcards.set(data.item.id, data.item);
    reviewedFlashcardIds = [data.item.id, ...reviewedFlashcardIds.filter((id) => id !== data.item.id)].slice(0, 24);
    flashcardSessionReviewedIds = [data.item.id, ...flashcardSessionReviewedIds.filter((id) => id !== data.item.id)].slice(0, 80);
    flashcardStudyStarted = true;
    flashcardTimerActive = true;
    pendingNextAfterId = currentFlashcard.id;
    currentFlashcard = null;
    updateFlashcardSessionFields();
    await refresh();
    await loadHelpProfile();
  } catch (error) {
    els.console.textContent = `Flashcards: ${error.message}`;
  }
}

async function autoDetectHelmet() {
  const now = Date.now();
  const terminalPhase = latestMacState && ["error", "interrupted"].includes(latestMacState.phase);
  const terminalUpdatedAt = Number((latestMacState && latestMacState.updated_at) || 0) * 1000;
  if (terminalPhase && terminalUpdatedAt && now - terminalUpdatedAt < 5000) {
    return;
  }
  if (busy || macActive || autoDetectInFlight || now - lastAutoDetectAt < 8000) {
    return;
  }
  autoDetectInFlight = true;
  lastAutoDetectAt = now;
  try {
    const response = await fetch("/api/job", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: "mac_connect_recording", params: { ...params(), scan_seconds: 6 } }),
    });
    const data = await response.json();
    if (data.ok && data.log) {
      selectedLog = data.log;
    }
  } catch {
    // Auto-detect is best-effort; the visible state refresh keeps the UI honest.
  } finally {
    autoDetectInFlight = false;
  }
}

function statusLabel(status) {
  return `<span class="badge ${status}">${status}</span>`;
}

function renderJobs(jobs) {
  els.jobCount.textContent = String(jobs.length);
  if (!jobs.length) {
    els.jobs.innerHTML = `<div class="job"><span class="badge">vuota</span><div class="job-name">--</div></div>`;
    return;
  }
  els.jobs.innerHTML = jobs
    .slice(0, 12)
    .map((job) => {
      const log = job.log ? ` data-log="${job.log}"` : "";
      return `
        <button class="job" type="button"${log}>
          ${statusLabel(job.status)}
          <span>
            <span class="job-name">${job.name}</span>
            <span class="job-meta">${job.mtime_label}</span>
          </span>
        </button>
      `;
    })
    .join("");

  els.jobs.querySelectorAll("[data-log]").forEach((node) => {
    node.addEventListener("click", () => {
      selectedLog = node.dataset.log;
      refresh();
    });
  });
}

function renderSessions(sessions, jobs) {
  const macRows = (sessions || []).slice(0, 8).map((session) => {
    const isTask = session.source === "task";
    const isEegV2 = session.source === "eeg_v2";
    const samples = session.samples ?? session.rows ?? 0;
    const hz = session.sample_rate_est_hz ? `${Number(session.sample_rate_est_hz).toFixed(1)} Hz` : "--";
    const gaps = session.packet_index_gaps ?? (isEegV2 ? "v2" : "--");
    const flashcards = Number(session.flashcard_events || 0);
    const behavioral = Number(session.behavioral_events || 0);
    const flashcardMeta = flashcards ? ` · ${flashcards} flashcard` : "";
    const behavioralMeta = behavioral ? ` · ${behavioral} eventi test` : "";
    const cov = session.session_covariates || {};
    const sleepMeta = cov.sleep_h ? ` · sonno ${cov.sleep_h}h` : "";
    const energyMeta = cov.cognitive_energy ? ` · energia ${cov.cognitive_energy}/7` : "";
    const covariateMeta = sleepMeta + energyMeta;
    const taskScore = session.behavioral_score
      ? ` · score ${session.behavioral_score.ok || 0}/${session.behavioral_score.miss || 0}`
      : "";
    const taskExportMeta = session.eeg_linked ? " · eventi su EEG" : " · locale, non esportato";
    const meta = isTask
      ? `${session.mtime_label} · ${behavioral || 0} eventi test${taskScore}${taskExportMeta}${covariateMeta}`
      : `${session.mtime_label} · ${samples} campioni · ${hz} · buchi ${gaps}${flashcardMeta}${behavioralMeta}${covariateMeta}`;
    const badge = isEegV2 ? "Mac v2" : isTask ? "Task" : "Mac";
    const deleteAttr = isTask || isEegV2
      ? `data-task-session="${escapeHtml(session.session_id || "")}" data-task-dir="${escapeHtml(session.session_dir || "")}"`
      : `data-session="${escapeHtml(session.name || "")}"`;
    return `
      <div class="job session-row">
        <span class="badge done">${badge}</span>
        <span class="session-text">
          <span class="job-name">${session.name}</span>
          <span class="job-meta">${meta}</span>
        </span>
        <button class="delete-session" type="button" ${deleteAttr}>Elimina</button>
      </div>
    `;
  });

  const raspberryRows = (jobs || []).slice(0, 4).map((job) => {
    const log = job.log ? ` data-log="raspberry/${job.log}"` : "";
    return `
      <button class="job" type="button"${log}>
        ${statusLabel(job.status)}
        <span>
          <span class="job-name">${job.name}</span>
          <span class="job-meta">${job.mtime_label}</span>
        </span>
      </button>
    `;
  });

  const rows = [...macRows, ...raspberryRows];
  els.jobCount.textContent = String((sessions || []).length);
  if (!rows.length) {
    els.jobs.innerHTML = `<div class="job"><span class="badge">vuota</span><div class="job-name">--</div></div>`;
    return;
  }
  els.jobs.innerHTML = rows.join("");
  els.jobs.querySelectorAll("[data-log]").forEach((node) => {
    node.addEventListener("click", () => {
      selectedLog = node.dataset.log;
      refresh();
    });
  });
  els.jobs.querySelectorAll("[data-session]").forEach((node) => {
    node.addEventListener("click", async (event) => {
      event.preventDefault();
      event.stopPropagation();
      if (node.dataset.deleting === "1") return;
      const name = node.dataset.session;
      node.dataset.deleting = "1";
      node.disabled = true;
      node.textContent = "Elimino...";
      try {
        const result = await postJob("mac_delete_session", { name });
        if (result && result.deleted) {
          els.console.textContent = result.deleted.length
            ? `Eliminati: ${result.deleted.join(", ")}`
            : (result.message || "Sessione gia eliminata");
        } else {
          els.console.textContent = result?.error || result?.message || "Eliminazione non riuscita";
        }
      } finally {
        await refresh();
      }
    });
  });
  els.jobs.querySelectorAll("[data-task-session]").forEach((node) => {
    node.addEventListener("click", async (event) => {
      event.preventDefault();
      event.stopPropagation();
      if (node.dataset.deleting === "1") return;
      const session_id = node.dataset.taskSession;
      const session_dir = node.dataset.taskDir || "";
      node.dataset.deleting = "1";
      node.disabled = true;
      node.textContent = "Elimino...";
      try {
        const result = await postJob("delete_training_session", { session_id, session_dir });
        if (result && result.deleted) {
          els.console.textContent = result.deleted.length
            ? `Eliminati: ${result.deleted.join(", ")}`
            : (result.message || "Sessione gia eliminata");
        } else {
          els.console.textContent = result?.error || result?.message || "Eliminazione non riuscita";
        }
      } finally {
        await refresh();
      }
    });
  });
}

function renderLogs(logs) {
  const current = selectedLog || (logs[0] && (logs[0].id || logs[0].name)) || "";
  const existing = Array.from(els.logSelect.options).map((option) => option.value).join("|");
  const incoming = logs.map((log) => log.id || log.name).join("|");
  if (existing !== incoming) {
    els.logSelect.innerHTML = logs
      .map((log) => {
        const id = log.id || log.name;
        const source = log.source === "mac" ? "Mac" : "Raspberry";
        return `<option value="${id}">${log.mtime_label} ${source} · ${log.name}</option>`;
      })
      .join("");
  }
  if (current) {
    els.logSelect.value = current;
  }
}

async function refresh() {
  const suffix = selectedLog ? `?log=${encodeURIComponent(selectedLog)}` : "";
  const response = await fetch(`/api/state${suffix}`, { cache: "no-store" });
  const data = await response.json();

  els.lastUpdate.textContent = data.time;
  latestMacState = data.mac || null;
  macActive = Boolean(data.mac && data.mac.running);
  macPhase = (data.mac && data.mac.phase) || "";
  const latest = data.mac && data.mac.latest_session;
  const liveBatteryPhases = new Set(["ble_link", "handshake_sent", "connected", "starting", "prep", "recording"]);
  const searchingPhases = new Set(["scan", "connecting"]);
  const hasLiveHelmet = Boolean(macActive && liveBatteryPhases.has(macPhase));
  const isSearchingHelmet = Boolean(macActive && searchingPhases.has(macPhase));
  const batteryPercent = hasLiveHelmet ? data.mac && data.mac.battery_percent : null;
  renderBattery(batteryPercent, hasLiveHelmet);
  renderHelmetLed(macActive ? data.mac : null);
  renderLiveFeatures(macActive ? data.mac : null);
  setSourceState(els.fc11Source, hasLiveHelmet ? "active" : isSearchingHelmet ? "searching" : "pending");
  updateConnectionControls(data.mac);
  if (macActive && data.mac && data.mac.phase === "error") {
    els.bridgeLine.textContent = "MacBook casco non disponibile · riaccendilo, riparto in ricerca";
    els.bridgeLine.style.color = "var(--danger)";
  } else if (macActive && data.mac && data.mac.phase === "interrupted") {
    els.bridgeLine.textContent = `MacBook interrotto: ${data.mac.condition || "sessione"}`;
    els.bridgeLine.style.color = "var(--muted)";
  } else if (macActive && hasLiveHelmet) {
    const contactText = data.mac.contact_state === "ok"
      ? " · contatto ok"
      : data.mac.contact_state === "bad"
        ? " · contatto da sistemare"
        : data.mac.contact_state
          ? ` · contatto ${data.mac.contact_state}`
          : "";
    const streamText = data.mac.samples || data.mac.packets
      ? ` · stream ${data.mac.samples || 0} campioni`
      : data.mac.phase === "connected"
        ? " · stream in attesa"
        : "";
    const phaseLabel = {
      scan: "in attesa del casco FC11",
      connecting: "aggancio FC11",
      ble_link: "casco rilevato",
      handshake_sent: "verifica collegamento",
      connected: "casco collegato",
      starting: "avvio registrazione",
      prep: "preparazione",
      recording: "registra",
      error: "errore",
      interrupted: "interrotto",
    }[data.mac.phase || ""] || "attivo";
    const conditionText = ["starting", "prep", "recording"].includes(data.mac.phase || "")
      ? `: ${data.mac.condition || "sessione"}`
      : "";
    els.bridgeLine.textContent = `MacBook ${phaseLabel}${conditionText}${contactText}${streamText}`;
    els.bridgeLine.style.color = "var(--cyan)";
  } else if (latest) {
    els.bridgeLine.textContent = `MacBook pronto · ultima sessione ${latest.mtime_label} · ${(latest.samples ?? latest.rows ?? 0)} campioni`;
    els.bridgeLine.style.color = "var(--accent)";
  } else {
    els.bridgeLine.textContent = "MacBook pronto · accendi il casco FC11 per iniziare";
    els.bridgeLine.style.color = "var(--accent-2)";
  }

  renderSessions(data.sessions || [], data.jobs || []);
  renderMemory(data.memory);
  renderLogs(data.logs || []);
  showMacPhase(data.mac);
  updateTaskControlState();
  autoDetectHelmet();

  selectedLog = data.selected_log || selectedLog;
  els.console.textContent = data.selected_log_text || "Nessun log selezionato.";
  reflectExportStatus(els.console.textContent);
}

document.querySelector("#refreshBtn").addEventListener("click", refresh);
document.querySelector("#exportBtn").addEventListener("click", async () => {
  els.console.textContent = "Export Raspberry avviato. Cancello dal Mac solo dopo verifica remota completa.";
  await postJob("mac_export_sessions");
});
els.deleteAbortedBtn.addEventListener("click", async () => {
  els.console.textContent = "Eliminazione sessioni abortite...";
  const result = await postJob("mac_delete_aborted_sessions");
  if (result && result.deleted) {
    els.console.textContent = result.deleted.length
      ? `Eliminate: ${result.deleted.join(", ")}`
      : "Nessuna sessione abortita da eliminare.";
    await refresh();
  }
});
document.querySelector("#bridgeBtn").addEventListener("click", () => postJob("start_bridge"));
document.querySelector("#pingBtn").addEventListener("click", () => postJob("raspberry_ping"));
els.connectSessionBtn.addEventListener("click", async () => {
  if (macActive) {
    els.console.textContent = "C'e gia una sessione Mac attiva.";
    return;
  }
  setButtonState(els.connectSessionBtn, "In corso...", "connecting");
  const result = await postJob("mac_connect_recording", { scan_seconds: 12 });
  if (result && result.connected) {
    els.phaseLabel.textContent = "Connessione stabilita";
    els.countdown.textContent = "--:--";
  } else if (result && result.message) {
    els.console.textContent = result.message;
    els.phaseLabel.textContent = result.battery_percent == null ? "Casco non pronto" : "Casco rilevato";
    els.countdown.textContent = "--:--";
  }
});
els.labCards?.forEach((button) => {
  button.addEventListener("click", () => {
    selectGuidedPath(button.dataset.family, button.dataset.preset);
    updateDailyCommand();
  });
});
els.durationCards?.forEach((button) => {
  button.addEventListener("click", () => {
    setGuidedDuration(button.dataset.duration);
    updateDailyCommand();
  });
});
els.guidedLaunchBtn?.addEventListener("click", () => {
  if (els.startBtn.disabled) {
    const title = els.startBtn.title || "Accendi e indossa il casco: MindTune abilita l'avvio solo quando FC11 e MacBook sono davvero pronti.";
    if (els.adaptivePlanLine) els.adaptivePlanLine.textContent = title;
    els.console.textContent = title;
    return;
  }
  els.startBtn.click();
});
els.guidedStopBtn?.addEventListener("click", () => {
  els.stopBtn.click();
});
document.querySelector("#batteryTestBtn").addEventListener("click", () => postJob("mac_battery", { scan_seconds: 6 }));
document.querySelector("#dryRunBtn").addEventListener("click", () => postJob("dry_run_readiness"));
document.querySelector("#bleBtn").addEventListener("click", () => postJob("mac_smoke", { scan_seconds: 10, smoke_seconds: 12 }));
els.handshakeDumpBtn.addEventListener("click", async () => {
  els.console.textContent = "Dump handshake in corso: e normale che alla fine si scolleghi.";
  await postJob("mac_handshake_dump", { scan_seconds: 12, after_pair: 1, after_validate: 2 });
});
els.handshakeStartBtn.addEventListener("click", async () => {
  els.console.textContent = "Dump + START in corso: dopo la stretta di mano provo 2 secondi di stream.";
  await postJob("mac_handshake_dump", { scan_seconds: 12, after_pair: 1, after_validate: 1, start: true });
});
els.reconnectDumpBtn.addEventListener("click", async () => {
  els.console.textContent = "Reconnect test in corso: salto PAIR e provo VALIDATE + START.";
  await postJob("mac_handshake_dump", { scan_seconds: 12, after_validate: 1, skip_pair: true, start: true });
});
document.querySelector("#brainlabBtn").addEventListener("click", () => postJob("brainlab_preflight"));
els.startBtn.addEventListener("click", async () => {
  if (macActive && ["scan", "connecting", "starting"].includes(macPhase)) {
    els.console.textContent = "Attendi che la fase in corso finisca, oppure premi Stop.";
    return;
  }
  if (activePreset().id === "hebrew_mlf_b2_7" && !els.hebrewMlfUnit?.value) {
    els.console.textContent = "Seleziona un'unità MLF prima di avviare EEG + task.";
    showHebrewMlfError("Seleziona un'unità MLF prima di premere Start.");
    return;
  }
  armIntegratedTask();
  const result = await postJob("mac_start_recording");
  if (result && result.started) {
    timer.phase = "ready";
    els.phaseLabel.textContent = "Preparazione";
    els.countdown.textContent = "--:--";
    els.console.textContent = `Sessione armata: EEG + ${integratedTaskLabel()} partiranno insieme.`;
  } else if (result && result.message) {
    stopIntegratedTask("start_failed");
    els.console.textContent = result.message;
  } else {
    stopIntegratedTask("start_failed");
  }
});
document.querySelector("#statusBtn").addEventListener("click", () => postJob("mac_status"));
document.querySelector("#tailBtn").addEventListener("click", () => postJob("record_tail", { lines: 160 }));
document.querySelector("#csvBtn").addEventListener("click", () => postJob("latest_csv"));

els.stopBtn.addEventListener("click", async () => {
  stopIntegratedTask("stop");
  stopLocalTimer();
  if (macActive) await postJob("mac_stop_recording");
});

els.conjugationAnswer.addEventListener("focus", () => {
  activeHebrewInput = els.conjugationAnswer;
  els.conjugationKeyboard.open = true;
});
els.conjugationCheckBtn.addEventListener("click", checkConjugationAnswer);
els.conjugationNextBtn.addEventListener("click", nextConjugationPrompt);
els.conjugationSpeakBtn?.addEventListener("click", startConjugationSpeechCapture);
els.conjugationAnswer.addEventListener("keydown", (event) => {
  if (isMacEditShortcut(event)) return;
  if (event.key === "Enter") {
    event.preventDefault();
    if (!els.conjugationFeedback.hidden) {
      nextConjugationPrompt();
      return;
    }
    checkConjugationAnswer();
  }
});

els.shoreshStartBtn?.addEventListener("click", () => startShoresh("test"));
els.shoreshTrainingBtn?.addEventListener("click", () => startShoresh("training"));
els.shoreshSaveBtn?.addEventListener("click", saveShoreshSession);
els.helpRefreshBtn?.addEventListener("click", loadHelpProfile);
els.flashcardCard.addEventListener("click", showFlashcardAnswer);
els.flashcardShowBtn.addEventListener("click", showFlashcardAnswer);
els.flashcardKnowBtn.addEventListener("click", () => gradeFlashcard("correct"));
els.flashcardHardBtn.addEventListener("click", () => gradeFlashcard("partial"));
els.flashcardMissBtn.addEventListener("click", () => gradeFlashcard("miss"));
els.apkPrimaryBtn?.addEventListener("click", apkPrimaryAction);
els.apkSecondaryBtn?.addEventListener("click", apkSecondaryAction);
els.apkTertiaryBtn?.addEventListener("click", () => answerStroop("yellow"));
els.apkQuaternaryBtn?.addEventListener("click", () => answerStroop("blue"));
els.apkStimulus?.addEventListener("click", (event) => {
  if (effectiveApkTaskKind() === "apk_hand_eye" && apkTask.phase === "target") answerHandEye(event);
  else if (effectiveApkTaskKind() === "apk_adaptive_tracking") answerAdaptiveTracking(event);
  else if (effectiveApkTaskKind() === "apk_starship") starshipMoveToward(event.clientY);
  else if (effectiveApkTaskKind() === "apk_airballoon") airballoonThrust();
  else if (effectiveApkTaskKind() === "apk_visual_grid") {
    const cell = event.target?.closest?.("[data-grid-cell]");
    if (cell && apkTask.phase === "visual_grid") {
      event.preventDefault();
      answerVisualGrid(Number(cell.dataset.gridCell));
    } else if (apkTask.phase !== "visual_grid") {
      apkPrimaryAction();
    }
  }
  else if (effectiveApkTaskKind() === "apk_treasure_tracker") {
    const slot = event.target?.closest?.("[data-treasure-slot]");
    if (slot && apkTask.phase === "treasure_answer") {
      event.preventDefault();
      answerTreasureTracker(Number(slot.dataset.treasureSlot));
    } else if (!apkTask.phase?.startsWith("treasure")) {
      apkPrimaryAction();
    }
  }
  else if (effectiveApkTaskKind() === "apk_letter_reconstruction" && apkTask.phase === "letter_answer") return;
  else if (effectiveApkTaskKind() === "apk_stroop_word" && apkTask.phase === "stroop") return;
  else if (effectiveApkTaskKind() === "apk_simon_direction" && apkTask.phase === "simon") return;
  else apkPrimaryAction();
});
els.apkStimulus?.addEventListener("pointerdown", (event) => {
  if (effectiveApkTaskKind() !== "apk_starship") return;
  event.preventDefault();
  els.apkStimulus.setPointerCapture?.(event.pointerId);
  starshipMoveToward(event.clientY);
});
els.apkStimulus?.addEventListener("pointermove", (event) => {
  if (effectiveApkTaskKind() !== "apk_starship" || !apkTask.current) return;
  if (event.pointerType === "mouse" || event.buttons || els.apkStimulus.hasPointerCapture?.(event.pointerId)) {
    starshipMoveToward(event.clientY);
  }
});
els.apkResponse?.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    event.preventDefault();
    if (effectiveApkTaskKind() === "apk_letter_reconstruction") {
      answerLetterReconstruction(false);
    } else {
      gradeTachistoscope(true);
    }
  }
});
els.apkResponse?.addEventListener("focus", () => {
  if (effectiveApkTaskKind() === "apk_letter_reconstruction") activeHebrewInput = els.apkResponse;
});

document.addEventListener("keydown", (event) => {
  if (event.metaKey || event.ctrlKey || event.altKey) return;
  if (event.target && ["INPUT", "TEXTAREA", "SELECT"].includes(event.target.tagName)) return;
  if (event.target && event.target.closest("[contenteditable='true']")) return;
  const presetId = activePreset().id;
  if (presetId === "hebrew_recovery" && sessionFlow.running && hebrewRecoveryFlow?.phase === "activation") {
    const key = event.key.toLowerCase();
    if (key === "arrowleft") {
      event.preventDefault();
      answerRecoveryActivation("left");
    } else if (key === "arrowright") {
      event.preventDefault();
      answerRecoveryActivation("right");
    }
    return;
  }
  if (presetId.startsWith("apk_") || presetId.startsWith("assessment_") || presetId.startsWith("program_")) {
    if (effectiveApkTaskKind() === "apk_stroop_word" && apkTask.phase === "stroop") {
      const key = event.key.toLowerCase();
      const byShortcut = STROOP_COLORS.find((color, index) => key === color.key || key === String(index + 1));
      if (byShortcut) {
        event.preventDefault();
        answerStroop(byShortcut.id);
      }
    } else if (effectiveApkTaskKind() === "apk_simon_direction" && apkTask.phase === "simon") {
      const key = event.key.toLowerCase();
      if (key === "arrowleft" || key === "a" || key === "1") {
        event.preventDefault();
        answerSimon("left");
      } else if (key === "arrowright" || key === "l" || key === "2") {
        event.preventDefault();
        answerSimon("right");
      }
    } else if (effectiveApkTaskKind() === "apk_starship" && apkTask.phase === "starship") {
      const key = event.key.toLowerCase();
      if (key === "arrowup" || key === "w") {
        event.preventDefault();
        starshipSetTarget(Math.max(0.08, Number(apkTask.current?.targetY ?? apkTask.current?.y ?? 0.5) - 0.14));
      } else if (key === "arrowdown" || key === "s") {
        event.preventDefault();
        starshipSetTarget(Math.min(0.92, Number(apkTask.current?.targetY ?? apkTask.current?.y ?? 0.5) + 0.14));
      }
    } else if (event.key === " " || event.key === "Enter") {
      event.preventDefault();
      apkPrimaryAction();
    } else if (event.key === "Escape") {
      event.preventDefault();
      apkSecondaryAction();
    }
    return;
  }
  if (activePreset().id === "hebrew_roots" && shoreshSession.phase === "item") {
    const item = shoreshSession.items[shoreshSession.index];
    const key = event.key.toLowerCase();
    if (item?.task_type === "same_root") {
      if (key === "j" || key === "arrowright") {
        event.preventDefault();
        answerShoresh("yes");
      } else if (key === "f" || key === "arrowleft") {
        event.preventDefault();
        answerShoresh("no");
      }
    } else if (/^[1-4]$/.test(key)) {
      const option = item?.options?.[Number(key) - 1];
      if (option) {
        event.preventDefault();
        answerShoresh(option);
      }
    }
    return;
  }
  if (event.key === " ") {
    event.preventDefault();
    showFlashcardAnswer();
  } else if (event.key === "1") {
    gradeFlashcard("miss");
  } else if (event.key === "2") {
    gradeFlashcard("partial");
  } else if (event.key === "3") {
    gradeFlashcard("correct");
  }
});

document.addEventListener("keydown", (event) => {
  handleTextControlShortcut(event).catch(() => {});
}, true);

els.copyConsoleBtn.addEventListener("click", async () => {
  const text = els.console.textContent || "";
  try {
    await navigator.clipboard.writeText(text);
  } catch {
    const area = document.createElement("textarea");
    area.value = text;
    area.setAttribute("readonly", "");
    area.style.position = "fixed";
    area.style.left = "-9999px";
    document.body.appendChild(area);
    area.select();
    document.execCommand("copy");
    area.remove();
  }
  els.copyConsoleBtn.classList.add("copied");
  els.copyConsoleBtn.title = "Copiato";
  setTimeout(() => {
    els.copyConsoleBtn.classList.remove("copied");
    els.copyConsoleBtn.title = "Copia console";
  }, 1200);
});

els.testFamily.addEventListener("change", () => {
  resetStudyState({ clearDecks: true });
  populatePresets();
  resetLocalTimerDisplay(activePreset());
  renderMemory(window.latestMemoryState);
  if (activePreset().id === "hebrew_recovery") resetHebrewRecoveryFlow();
  updateDailyCommand();
});
els.testPreset.addEventListener("change", () => {
  resetStudyState();
  applyPreset();
  resetLocalTimerDisplay(activePreset());
  renderMemory(window.latestMemoryState);
  if (activePreset().id === "hebrew_recovery") resetHebrewRecoveryFlow();
  updateDailyCommand();
  if (activePreset().id === "hebrew_mlf_b2_7") {
    clearHebrewMlfResult();
    loadHebrewMlfUnits();
  }
});
els.duration.addEventListener("change", () => {
  applyPreset({ ...activePreset(), duration: Number(els.duration.value || 0) });
  updateDailyCommand();
});
els.caffeineCups?.addEventListener("input", syncCaffeineMgFromCups);

els.logSelect.addEventListener("change", () => {
  selectedLog = els.logSelect.value;
  refresh();
});

if (els.hebrewMlfStartBtn) {
  els.hebrewMlfStartBtn.addEventListener("click", startHebrewMlfSession);
}
if (els.hebrewMlfSubmitBtn) {
  els.hebrewMlfSubmitBtn.addEventListener("click", submitHebrewMlfResponse);
}
if (els.hebrewMlfResponse) {
  els.hebrewMlfResponse.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      submitHebrewMlfResponse();
    }
  });
}

populateFamilies();
selectGuidedPath("memory", "hebrew_recovery");
setGuidedDuration(1800);
renderHebrewKeyboard();
loadConjugationCatalog();
renderConjugationStats();
renderConjugationHistory();
renderFlashcardScore();
renderBattery(null);
syncCaffeineMgFromCups();
refresh();
fetchOuraDaily();
setInterval(refresh, 1000);
setInterval(fetchOuraDaily, 60000);
setInterval(tickTimer, 250);
setInterval(tickConjugationTimer, 100);
setInterval(renderFlashcardTimer, 100);
requestAnimationFrame(drawWave);
