# Mantra Phase 1 — uncertain linguistic decisions

1. **Infinitive spelling of לִכְתֹּב vs לִכְתּוֹב**
   Pealim lists the defective spelling `לִכְתֹּב` (without vav) as the primary menukad form; the full spelling with vav is acceptable in unvowelled text. For TTS we use the vowelled form.

2. **Stress in past 2nd-person plural**
   Pealim gives two variants (e.g., `כְּתַבְתֶּם` and `כָּתַבְתֶּם`). We selected the reduced-vowel form `ktavtem`/`ktavten` as the common spoken form, matching the user's mantra example.

3. **Transliteration of silent/glottal alef**
   We represent a pronounced glottal stop with `'` (e.g., `le'echol`). In rapid speech the stop may be barely audible; this is marked in metadata but does not affect Azure TTS, which receives Hebrew script.

4. **Italian glosses for gender/number**
   The Hebrew present tense is a participle covering multiple persons. Italian glosses note the gender only when the Hebrew form itself is marked for gender (feminine singular/plural).

5. **Future feminine plural**
   We use the common modern masculine plural future forms (`tichte'vu`, `yichte'vu`) for plural address, as instructed. The classical feminine plural forms (`tichtovna` etc.) are omitted from the recitation.

6. **Voice selection**
   SSML uses `he-IL-AvriNeural`. If a different voice is preferred, update `scripts/generate_mantra_audio.py` and regenerate.
