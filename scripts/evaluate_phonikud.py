#!/usr/bin/env python3
"""Evaluate Phonikud/Renikud for לכתוב, להיות, לעשות."""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

from phonikud import phonemize
from phonikud_onnx import Phonikud
from renikud_onnx import G2P

APP = Path(__file__).resolve().parents[1]
DATA = APP / "data" / "phonikud_eval"
PEALIM_JSON = DATA / "pealim_forms.json"
OUTPUT_JSON = DATA / "phonikud_evaluation.json"
OUTPUT_CSV = DATA / "phonikud_evaluation.csv"

STRESS_MARK = "ˈ"
IPA_VOWEL_SET = {
    "a", "e", "i", "o", "u", "ə", "ɛ", "ɪ", "ʊ", "ɔ", "æ", "ɑ", "ɒ",
    "ɜ", "ɘ", "ɨ", "ʉ", "ɵ", "ɤ", "ɯ", "ɐ", "ɞ", "ɚ", "ɝ",
}

def strip_niqqud(text: str) -> str:
    return "".join(c for c in text if ord(c) < 0x0591 or ord(c) > 0x05C7)

def clean_transliteration(html_text: str) -> str:
    return re.sub(r"<[^>]+>", "", html_text)

def stress_from_phonemes(ph: str) -> int:
    """Return 1-indexed stressed vowel position, or 0 if no stress mark."""
    if STRESS_MARK not in ph:
        return 0
    before = ph.split(STRESS_MARK, 1)[0]
    return sum(1 for c in before if c in IPA_VOWEL_SET) + 1

def vowels_of(ph: str) -> list[str]:
    return [c for c in ph if c in IPA_VOWEL_SET]

def vowel_sequence(ph: str) -> str:
    """Approximate ASCII vowel sequence for comparison with Pealim Latin."""
    mapping = {
        "a": "a", "ɑ": "a", "æ": "a", "ɐ": "a", "ɒ": "a",
        "e": "e", "ɛ": "e", "ɜ": "e", "ɘ": "e", "ɚ": "e", "ɝ": "e", "ə": "e",
        "i": "i", "ɪ": "i", "ɨ": "i",
        "o": "o", "ɔ": "o", "ɵ": "o", "ɤ": "o",
        "u": "u", "ʊ": "u", "ʉ": "u",
    }
    return "".join(mapping.get(v, "") for v in vowels_of(ph))

def latin_vowel_sequence(text: str) -> str:
    return "".join(c for c in text.lower() if c in "aeiou")

def fix_stress(ph: str, target: int) -> str:
    """Move the stress mark so that it precedes the target-th vowel."""
    if STRESS_MARK not in ph:
        return ph
    no_stress = ph.replace(STRESS_MARK, "")
    chars = list(no_stress)
    count = 0
    for i, c in enumerate(chars):
        if c in IPA_VOWEL_SET:
            count += 1
            if count == target:
                return "".join(chars[:i] + [STRESS_MARK] + chars[i:])
    return ph

def manual_override(phonikud_ph: str, renikud_ph: str, transliteration: str, expected_stress: int) -> str:
    """Choose/correct phonemes based on Pealim transliteration and stress."""
    expected_vowels = latin_vowel_sequence(transliteration)
    p_vowels = vowel_sequence(phonikud_ph)
    r_vowels = vowel_sequence(renikud_ph)

    # Candidate 1: Phonikud (trust vowels), fixing stress if needed.
    p_fixed = phonikud_ph
    p_stress = stress_from_phonemes(p_fixed)
    if expected_stress > 0 and p_stress != expected_stress:
        p_fixed = fix_stress(p_fixed, expected_stress)
    # If after stress fix the vowel sequence still matches expected, use it.
    if p_vowels == expected_vowels:
        return p_fixed

    # Candidate 2: Renikud if it has the right vowel sequence and stress.
    r_stress = stress_from_phonemes(renikud_ph)
    if r_vowels == expected_vowels:
        if expected_stress > 0 and r_stress != expected_stress:
            return fix_stress(renikud_ph, expected_stress)
        return renikud_ph

    # Candidate 3: whichever has right vowel count + right stress, even if vowel quality differs.
    for cand, cand_vowels in [(p_fixed, p_vowels), (renikud_ph, r_vowels)]:
        if len(cand_vowels) == len(expected_vowels):
            if expected_stress > 0 and stress_from_phonemes(cand) == expected_stress:
                return cand

    # Fallback: original Phonikud (flagged by caller).
    return phonikud_ph

def vocal_shva_present(ph: str) -> bool:
    return "ə" in ph or re.search(r"[ptkbdgʃʒχxʁfvθðszʨʥmnŋlrwj]e[ptkbdgʃʒχxʁfvθðszʨʥmnŋlrwj]", ph) is not None

def main() -> int:
    DATA.mkdir(parents=True, exist_ok=True)
    phonikud = Phonikud(str(APP / "data" / "phonikud_models" / "phonikud-1.0.int8.onnx"))
    renikud = G2P(str(APP / "data" / "phonikud_models" / "renikud.onnx"))

    pealim = json.loads(PEALIM_JSON.read_text(encoding="utf-8"))
    rows = []
    for verb in pealim:
        for form_key, form in verb["forms"].items():
            menukad = form["hebrew_with_niqqud"]
            chaser = form["hebrew_without_niqqud"]
            translit = clean_transliteration(form.get("transcription_html", ""))
            pealim_stress = form.get("pealim_stress_syllable", 0)

            phonikud_ph = phonemize(menukad, schema="modern", predict_stress=True, predict_vocal_shva=True)
            renikud_ph = renikud.phonemize(chaser)
            override = manual_override(phonikud_ph, renikud_ph, translit, pealim_stress)
            override_stress = stress_from_phonemes(override)
            override_vowels = vowel_sequence(override)
            expected_vowels = latin_vowel_sequence(translit)

            if override == phonikud_ph and override_stress == pealim_stress and override_vowels == expected_vowels:
                status = "verified"
            elif override_vowels != expected_vowels or override_stress != pealim_stress:
                status = "manual override required"
            else:
                status = "corrected by manual override"

            row = {
                "verb": verb["query"],
                "form_key": form_key,
                "hebrew_with_niqqud": menukad,
                "hebrew_without_niqqud": chaser,
                "transliteration": translit,
                "expected_stress": pealim_stress,
                "phonikud_phonemes": phonikud_ph,
                "phonikud_stress": stress_from_phonemes(phonikud_ph),
                "renikud_phonemes": renikud_ph,
                "renikud_stress": stress_from_phonemes(renikud_ph),
                "manual_override": override,
                "override_stress": override_stress,
                "vocal_shva_phonikud": vocal_shva_present(phonikud_ph),
                "vocal_shva_renikud": vocal_shva_present(renikud_ph),
                "vocal_shva_override": vocal_shva_present(override),
                "azure_status": "not generated",
                "phonikud_tts_status": "not generated",
                "mic_tts_status": "not generated",
                "linguistic_status": status,
            }
            rows.append(row)

    # Write JSON
    OUTPUT_JSON.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

    # Write CSV
    if rows:
        keys = list(rows[0].keys())
        with OUTPUT_CSV.open("w", encoding="utf-8", newline="") as fp:
            writer = csv.DictWriter(fp, fieldnames=keys)
            writer.writeheader()
            writer.writerows(rows)
    print(f"Wrote {OUTPUT_JSON} and {OUTPUT_CSV} ({len(rows)} rows)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
