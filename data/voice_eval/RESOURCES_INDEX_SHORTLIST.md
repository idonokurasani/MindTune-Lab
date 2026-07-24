# Hebrew NLP Resources Index — Shortlist for MindTune Lab Mantra Voice Layer

Source repository inspected: `https://github.com/AdamKaabyia/Resources` (treated as a curated index only).

Scope: Hebrew text-to-speech, speech synthesis, pronunciation, G2P, niqqud restoration, lexical stress, vocal shva, Hebrew speech datasets, phoneme-aware TTS, Israeli Hebrew voices.

**Bottom line:** the index is mostly pre-2020 and contains **no runnable, commercially-licensed, offline Hebrew TTS voice**. The only speech-producing entry is an online service (`AlmaReader`). The most useful entries are vocalized-verb datasets and a Java verb vocalizer, which can support the *pronunciation layer* but not the *voice layer*.

## Genuinely relevant candidates from the index

| Name | Purpose | URL | Executable code | Pretrained weights | Accepts niqqud / phoneme input | Produces speech | Code license | Weights license | Dataset license | Apple Silicon feasibility | Relevance to Mantra pipeline | Verdict |
|------|---------|-----|-----------------|--------------------|-------------------------------|-----------------|--------------|-----------------|-----------------|---------------------------|------------------------------|---------|
| **Eran Tomer Vocalized Verb Dataset** | 250k fully vocalized Hebrew inflected verb forms with morphology (Time/Person/Gender/Number/Spelling) | `linguistic_resources/word_lists/hebrew_verbs_eran_tomer/` in the index repo | No (CSV data) | No | N/A | No | N/A | N/A | CC BY 4.0 | N/A | **High** — can be used to cross-check or supplement Pealim vocalizations, stress, and vocal-shva for the three verbs and beyond; not a TTS. | Keep as reference data |
| **Verb Inflector** | Java tool that generates vocalized + morphologically tagged Hebrew verbs from a non-vocalized base form and a pattern number | `code/VerbInflector/` in the index repo | Yes (Java; requires build) | No | No (takes base form + pattern, not niqqud or phonemes) | No | Apache 2.0 | N/A | N/A | Yes (Java) | **Medium** — could regenerate vocalized forms if Pealim data is missing, but the existing pipeline already has verified Pealim forms; not a TTS. | Optional upstream vocalization tool |
| **Eran Tomer Digital Vocalized Text Corpus** | A corpus of digital vocalized Hebrew texts | Dropbox link in README.rst (index repo) | No | No | N/A | No | N/A | N/A | Apache 2.0 | N/A | **Medium** — useful as training/validation text for a future TTS; not a voice. | Keep as reference data |
| **SVLM Hebrew Wikipedia Corpus** | 50K Hebrew Wikipedia sentences selected to ensure phoneme coverage for a sentence-recording project | https://github.com/NLPH/SVLM-Hebrew-Wikipedia-Corpus | No | No | N/A | No | N/A | N/A | CC-BY-SA 3.0 | N/A | **Medium** — sentence list for coverage testing or future recording; not a TTS. | Keep as reference data |
| **AlmaReader** | Online text-to-speech service for Hebrew | https://app.almareader.com/ | No (web service) | No (cloud) | Unknown | Yes | Unknown / commercial service terms | Unknown | N/A | N/A (cloud) | **Low** — produces speech, but not offline, not open, no pronunciation control, and not integrable into MindTune Lab. | Not a candidate |

## Rejected or not-suitable entries

| Name | Reason for rejection |
|------|----------------------|
| **CoSIH — Corpus of Spoken Hebrew** | Relevant spoken-Hebrew dataset, but license is marked `?` in the index; too risky for commercial use without clarification. |
| **HaArchion** | Recordings of Hebrew prose/poetry; no code, no weights, no license, not a TTS. |
| **Nakdan (DICTA)** | Web-only nikud service; not offline, not controllable, not a voice. |
| **The Automatic Hebrew Transcriber** | ASR-only (speech-to-text), not TTS. |
| **Hebrew OCR with Nikud** | 2012 BSc project that trains Tesseract OCR on nikud; no pretrained weights, unknown license, not maintained, not a practical TTS/nikud tool. |
| **MILA Morphological Analysis / Disambiguation Tools** | Morphology analysis only; GPLv3 + non-commercial; no pronunciation or speech output. |
| **AlephBERT** | General-purpose Hebrew language model; no pronunciation or speech function. |
| **Hebrew-Sentiment-Data / HeBERT emotion data** | Sentiment/classification datasets; not relevant. |
| **NEMO / MDTEL / Ben-Mordecai corpora** | NER/text datasets; not pronunciation or speech. |
| **Hebrew Wikipedia / OSCAR / CC100 / JPress** | Raw text corpora; no speech, no pronunciation annotations. |
| **Commercial entries in Industry.rst** (Melingo, over.ai, Genius, Hebrew NLP, etc.) | Not open-source / not locally runnable / not integrable. |

## Observations

- The index does **not** list modern Hebrew TTS projects such as Phonikud-TTS, HebTTS, BlueTTS, F5-TTS Hebrew, Voxtream2-he, or Facebook MMS-TTS-Heb. It predates the current wave of open Hebrew TTS work.
- The only directly actionable items are the **vocalized verb data** (for pronunciation verification) and **AlmaReader** (a closed online TTS service).
- For the MindTune Lab Mantra pipeline, the index does not change the previously identified voice-layer conclusion: the only viable offline, phoneme-controllable voices known so far are **Piper/Phonikud-TTS (`shaul`, CC-BY-NC)** and the newer **BlueTTS (`blue-onnx`, MIT)**; both must be evaluated outside this index.
