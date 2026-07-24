# Unresolved Linguistic and Licensing Issues

## Licensing

| Resource | License | Notes |
|----------|---------|-------|
| Eran Tomer Vocalized Verb Dataset | CC BY 4.0 | Attribution required; included in `data/hebrew/resources/eran_tomer/LICENSE`. |
| Verb Inflector (Java) | Apache 2.0 | Recompiled from source; license included with source. |
| SVLM Hebrew Wikipedia Corpus | CC-BY-SA 3.0 | Share-alike; the Wikimedia foundation license text is in `data/hebrew/resources/svlm/LICENSE`. Commercial downstream use of derived works must be checked. |
| Pealim reference data | **Unclear** | Scraped conjugation tables for internal research/evaluation. No explicit license from pealim.com. Must be replaced with an explicitly licensed source or direct licensing before redistribution. |
| Phonikud library | No license field in `pip show` | PyPI package `phonikud 0.4.1` did not expose a license. Used as a pronunciation utility; consider pinning and asking the author for clarification. |
| `shaul.onnx` / Phonikud-TTS voice | CC BY-NC 4.0? | `shaul.config.json` must be inspected; the voice was accepted as the current production voice but its commercial status should be verified before deployment. |

## Linguistic / technical unresolved issues

1. **Standard unvocalized spelling heuristic** — `standard_unvocalized` handles the common infinitive/future `o`/`u` patterns (לכתוב, אכתוב) but is not a full G2P/orthographic model. Exceptions like `רֹאשׁ` > `ראש` (no vav) and guttural contexts may need overrides.
2. **Root extraction** — The engine does not yet derive a triliteral root automatically from a base form. Roots are taken from Pealim or supplied manually.
3. **Imperative forms** — Pealim snapshots do not contain imperatives; Verb Inflector can generate them but they have not been manually validated.
4. **Vocal shva detection** — The authoritative vocal-shva flag comes from manual audit/overrides, not from Phonikud output. A deterministic classifier for vocal shva would reduce manual work.
5. **Sin/shin apostrophe handling** — The Verb Inflector index uses an ASCII apostrophe (e.g. `עש'ה`) to encode sin. This must be normalized consistently when linking to vocalized Pealim forms.
6. **Defective/irregular verbs** — The current validation covers three regular-ish verbs. Weak roots (initial/final `א`, `ה`, `י`, `נ`) and hollow verbs need systematic testing.
7. **SVLM sentence pedagogy** — Sentences are filtered/ranked by token count and phoneme coverage, not by didactic suitability. No manual approval workflow exists yet.
8. **Answer validation depth** — `validate_user_answer` distinguishes exact, niqqud-only and spelling-only matches. It does not yet diagnose wrong tense, person, gender, number, binyan or lemma; that requires paradigm context.
9. **Java Verb Inflector base-form mapping** — Mapping an infinitive to the base form expected by the inflector is not fully automated. A lookup table or morphological analyzer is needed.
10. **Piper voice replaceability** — The shared `PiperAdapter` is isolated, but only one voice (`shaul`) is configured. Adding `blue` or other voices requires voice-selection config and per-voice phoneme checks.
