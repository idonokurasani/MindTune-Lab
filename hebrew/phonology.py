"""Phonological validation module for Modern Israeli Hebrew verb forms.

This module is intentionally deterministic: it may consult the Phonikud
adapter, but Phonikud remains an advisory source.  Final decisions are
derived from manual overrides (when available) and from rule-based
phonology, with disagreements flagged as ``unresolved``.

Conventions
-----------
* ``lexical_stress`` is 1-indexed from the left (beginning of the word).
* ``syllabification`` currently returns phonetic syllable strings derived
  from the chosen phoneme string.
* ``phonemic`` is an IPA-style phonemic string.  ``practical`` is a
  simplified Israeli Hebrew respelling in Latin characters.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .adapters.phonikud_adapter import phonemize, stress_from_phonemes
from .models import MorphologicalFeatures
from .morphology import parse_morphology_tag
from .normalization import decompose, is_hebrew_letter, is_niqqud, normalize_hebrew
from .shva import classify_shva


# Niqqud code points -> human-readable names used by the rule engine.
NIQQUD_NAME: dict[str, str] = {
    "\u05b0": "sheva",
    "\u05b1": "hataf_segol",
    "\u05b2": "hataf_patah",
    "\u05b3": "hataf_qamats",
    "\u05b4": "hiriq",
    "\u05b5": "tsere",
    "\u05b6": "segol",
    "\u05b7": "patah",
    "\u05b8": "qamats",
    "\u05b9": "holam",
    "\u05bb": "qubuts",
    "\u05bc": "dagesh",
    "\u05c7": "qamats_qatan",
}

_VOWEL_POINTS = frozenset(c for c in NIQQUD_NAME if NIQQUD_NAME[c] not in ("dagesh",))

# Begedkefet mapping: base letter -> (plosive IPA, spirant IPA).
# In Modern Israeli Hebrew ג, ד, ת do not consistently spirantize,
# so their spirant is the same as the plosive.
BEGADKEFAT: dict[str, tuple[str, str]] = {
    "ב": ("b", "v"),
    "ג": ("g", "g"),
    "ד": ("d", "d"),
    "כ": ("k", "χ"),
    "פ": ("p", "f"),
    "ת": ("t", "t"),
}

# Simplified mapping from IPA-ish phonemes to a practical Israeli respelling.
# Ordered from longest to shortest to avoid partial replacements.
_PRACTICAL_REPLACEMENTS = [
    ("t͡s", "ts"),
    ("d͡ʒ", "j"),
    ("ˈ", ""),
    ("ː", ""),
    ("χ", "ch"),
    ("ʔ", "'"),
    ("j", "y"),
    ("ʃ", "sh"),
    ("ʒ", "zh"),
    ("ɡ", "g"),
    ("ɛ", "e"),
    ("ɔ", "o"),
    ("ə", "e"),
]


def _vowel_name(marks: list[str]) -> str | None:
    """Return the first meaningful vowel name in a list of combining marks."""
    for m in marks:
        if m in _VOWEL_POINTS:
            return NIQQUD_NAME[m]
    return None


def _letter_clusters(vocalized: str) -> list[tuple[str, list[str], int]]:
    """Split normalized vocalized text into Hebrew base-letter clusters.

    Returns a list of (base_letter, marks, index) tuples. Non-letter
    characters are skipped.
    """
    text = normalize_hebrew(vocalized)
    chars = list(decompose(text))
    clusters: list[tuple[str, list[str], int]] = []
    i = 0
    n = len(chars)
    while i < n:
        c = chars[i]
        if not is_hebrew_letter(c):
            i += 1
            continue
        marks: list[str] = []
        j = i + 1
        while j < n and is_niqqud(chars[j]):
            marks.append(chars[j])
            j += 1
        clusters.append((c, marks, len(clusters)))
        i = j
    return clusters


def extract_syllables(vocalized: str) -> list[str]:
    """Return syllable strings for a vocalized Hebrew form.

    The current implementation derives syllabification from the Phonikud
    phoneme string.  It therefore returns phonetic syllable strings.  The
    ``vocalized`` argument is normalized before being phonemized.
    """
    text = normalize_hebrew(vocalized)
    try:
        phonemes = phonemize(text)
    except Exception:
        return []
    return _phoneme_syllables(phonemes)


def _phoneme_syllables(phonemes: str) -> list[str]:
    """Extract syllables from an IPA-style phoneme string.

    A vowel (optionally preceded by the stress marker ``ˈ``) is taken as
    the syllable nucleus.  Consonants between two nuclei are split so that
    the last consonant forms the onset of the next syllable; any preceding
    consonants close the current syllable.  Word-final consonants form the
    coda of the last syllable.
    """
    if not phonemes:
        return []
    pattern = re.compile(r"ˈ?[aeiouAEIOU]")
    matches = list(pattern.finditer(phonemes))
    if not matches:
        return [phonemes]

    syllables: list[str] = []
    onset = phonemes[: matches[0].start()]
    for i, m in enumerate(matches):
        vowel = m.group()
        end = m.end()
        if i + 1 < len(matches):
            tail = phonemes[end : matches[i + 1].start()]
            if len(tail) <= 1:
                coda = ""
                next_onset = tail
            else:
                coda = tail[:-1]
                next_onset = tail[-1:]
        else:
            coda = phonemes[end:]
            next_onset = ""
        syllables.append(onset + vowel + coda)
        onset = next_onset
    return syllables


def _phonemes_with_stress(phonemes: str, stress: int) -> str:
    """Return ``phonemes`` with the stress marker on the ``stress``-th vowel."""
    if not phonemes:
        return phonemes
    flat = phonemes.replace("ˈ", "")
    matches = list(re.finditer(r"[aeiouAEIOU]", flat))
    if not matches or stress < 1 or stress > len(matches):
        return flat
    pos = matches[stress - 1].start()
    return flat[:pos] + "ˈ" + flat[pos:]


def _is_full_vowel(name: str | None) -> bool:
    """True for independent vowel names (not sheva or hataf reductions)."""
    if name is None:
        return False
    return name not in ("sheva", "hataf_segol", "hataf_patah", "hataf_qamats")


def begadkefat_realization(
    letter: str, following_vowel: str | None, position: int
) -> dict[str, Any]:
    """Return the realized consonant for a Begedkefet letter.

    ``letter`` may be the base Hebrew letter or the base letter plus
    combining marks (e.g. ``"כְּ"``).  ``following_vowel`` is the name of
    the nearest full vowel that *precedes* this consonant in the word
    (``None`` for a word-initial consonant).  ``position`` is the
    0-indexed position of the letter in the word.

    In Modern Israeli Hebrew the spirantization rule is simplified:

    * a dagesh mark forces the plosive;
    * ב, כ, פ are plosives at the beginning of a word or when no vowel
      precedes them;
    * ב, כ, פ that follow a full vowel in the word are spirants;
    * ג, ד, ת remain plosive in all positions in the modern language.
    """
    has_dagesh = "\u05bc" in letter
    base = letter[0] if letter else ""
    mapping = BEGADKEFAT.get(base)
    if mapping is None:
        return {
            "letter": base,
            "position": position,
            "realized": base,
            "is_spirant": False,
            "following_vowel": following_vowel,
            "dagesh": has_dagesh,
            "reason": "not_begedkefat",
        }

    plosive, spirant = mapping
    preceding_vowel = following_vowel

    if has_dagesh:
        realized = plosive
        reason = "dagesh_forte_plosive"
    elif base in ("ב", "כ", "פ"):
        if position == 0 or not _is_full_vowel(preceding_vowel):
            realized = plosive
            reason = "initial_or_no_preceding_vowel"
        else:
            realized = spirant
            reason = "post_vocalic_spirant"
    else:
        realized = plosive
        reason = "gdl_t_modern_plosive"

    return {
        "letter": base,
        "position": position,
        "realized": realized,
        "is_spirant": (realized == spirant and base in ("ב", "כ", "פ")),
        "following_vowel": following_vowel,
        "dagesh": has_dagesh,
        "reason": reason,
    }


def _to_practical(phonemes: str) -> str:
    """Convert an IPA-style phoneme string to a practical respelling."""
    result = phonemes
    for old, new in _PRACTICAL_REPLACEMENTS:
        result = result.replace(old, new)
    return result


def _context_to_features(context: Any) -> dict[str, Any]:
    """Normalize a morphological context into a plain dict."""
    if context is None:
        return {}
    if isinstance(context, MorphologicalFeatures):
        return context.as_dict()
    if isinstance(context, str):
        return parse_morphology_tag(context).as_dict()
    if isinstance(context, dict):
        return dict(context)
    if hasattr(context, "as_dict"):
        return context.as_dict()
    return {}


class PronunciationValidator:
    """Validate the pronunciation of a vocalized Modern Israeli Hebrew verb form.

    The validator loads manual overrides from evaluation files and applies
    rule-based phonology.  Phonikud is used as an advisory source and is
    recorded separately in ``phonikud_proposal``.
    """

    DEFAULT_OVERRIDE_PATHS: tuple[Path, ...] = (
        Path(__file__).resolve().parents[1] / "data" / "phonikud_eval" / "phonikud_evaluation.json",
        Path(__file__).resolve().parents[1]
        / "data"
        / "hebrew"
        / "resources"
        / "pealim"
        / "phonikud_evaluation.json",
        Path(__file__).resolve().parents[1]
        / "data"
        / "hebrew"
        / "overrides"
        / "pronunciation.json",
    )

    def __init__(self, override_paths: list[Path] | tuple[Path, ...] | None = None):
        self.override_paths = override_paths or self.DEFAULT_OVERRIDE_PATHS
        self._overrides: dict[Any, dict[str, Any]] = {}
        self._load_overrides()

    def _load_overrides(self) -> None:
        for path in self.override_paths:
            if not path.exists():
                continue
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if isinstance(raw, list):
                for entry in raw:
                    self._index_list_entry(entry)
            elif isinstance(raw, dict):
                for key, value in raw.items():
                    self._overrides[key] = value if isinstance(value, dict) else {"value": value}

    def _index_list_entry(self, entry: dict[str, Any]) -> None:
        key = normalize_hebrew(entry.get("hebrew_with_niqqud", ""))
        if key:
            self._overrides[key] = entry
        plain = entry.get("hebrew_without_niqqud", "")
        if plain:
            self._overrides[plain] = entry
        verb = entry.get("verb", "")
        form_key = entry.get("form_key", "")
        if verb and form_key:
            self._overrides[(verb, form_key)] = entry

    def _find_override(self, text: str, context: dict[str, Any]) -> dict[str, Any] | None:
        text = normalize_hebrew(text)
        if text in self._overrides:
            return self._overrides[text]
        if context:
            target = context.get("target")
            if target and target in self._overrides:
                return self._overrides[target]
            verb = context.get("verb") or context.get("lemma_plain")
            form_key = context.get("form_key")
            if verb and form_key and (verb, form_key) in self._overrides:
                return self._overrides[(verb, form_key)]
            surface_plain = context.get("surface_plain")
            if surface_plain and surface_plain in self._overrides:
                return self._overrides[surface_plain]
        return None

    @staticmethod
    def _derive_rule_stress(features: dict[str, Any], n_syllables: int) -> int:
        """Predict stress position from morphological context.

        Defaults to ultimate stress.  Two main systematic exceptions in
        Modern Israeli Hebrew verb inflection are handled:

        * present tense feminine singular (e.g. כּוֹתֶבֶת) is penultimate;
        * past 1st/2nd masculine singular and 1st plural are penultimate
          (e.g. כָּתַבְתִּי, כָּתַבְנוּ).
        """
        if n_syllables <= 1:
            return max(1, n_syllables)

        tense = (features.get("tense") or "").lower()
        person = (features.get("person") or "").lower()
        number = (features.get("number") or "").lower()
        gender = (features.get("gender") or "").lower()

        if tense == "present" and gender == "feminine" and number == "singular":
            return max(1, n_syllables - 1)

        if tense == "past":
            if person == "first" and number == "plural":
                return max(1, n_syllables - 1)
            if number == "singular" and person in ("first", "second") and gender != "feminine":
                return max(1, n_syllables - 1)

        return n_syllables

    def validate(self, vocalized: str, context: Any | None = None) -> dict[str, Any]:
        """Validate a vocalized Hebrew verb form.

        Returns a dict with phonemic, practical, syllabification,
        lexical_stress, shva_status, dagesh_status, begadkefat, variants,
        rule_trace, phonikud_proposal, override_comparison, confidence and
        unresolved.
        """
        text = normalize_hebrew(vocalized)
        features = _context_to_features(context)
        rule_trace: list[str] = ["normalize_hebrew"]

        # Phonikud advisory output
        phonikud_phonemes = ""
        try:
            phonikud_phonemes = phonemize(text)
            rule_trace.append("phonikud_phonemize")
        except Exception as exc:
            rule_trace.append(f"phonikud_error:{exc}")

        phonikud_stress = stress_from_phonemes(phonikud_phonemes)

        # Manual override lookup
        override = self._find_override(text, features)
        if override:
            rule_trace.append("manual_override_lookup")

        manual_phonemes = override.get("manual_override", "") if override else ""
        manual_stress = override.get("override_stress") if override else None
        manual_vocal_shva = override.get("vocal_shva_override") if override else None
        phonikud_vocal_shva = override.get("vocal_shva_phonikud") if override else None
        manual_transliteration = override.get("transliteration", "") if override else ""

        # Sheva classification (reuses hebrew.shva)
        shva_diag = classify_shva(
            text,
            phonikud_vocal_shva=phonikud_vocal_shva,
            manual_override=manual_vocal_shva,
            manual_source="phonology_evaluation" if override else "",
        )
        rule_trace.append("classify_shva")

        # Syllabification is based on the best available phoneme string.
        base_phonemes = manual_phonemes or phonikud_phonemes
        pre_syllables = _phoneme_syllables(base_phonemes)
        n_syllables = len(pre_syllables)
        rule_trace.append("syllable_extraction")

        rule_stress = self._derive_rule_stress(features, n_syllables)
        rule_trace.append("rule_based_stress")

        # Determine the chosen phonemic output and stress.
        chosen_source = "phonikud"
        if manual_phonemes:
            chosen_source = "manual_override"
            chosen_stress = (
                int(manual_stress)
                if manual_stress is not None
                else stress_from_phonemes(manual_phonemes)
            )
            phonemic = manual_phonemes
        else:
            if rule_stress and rule_stress != phonikud_stress:
                chosen_source = "rule_based"
                chosen_stress = rule_stress
                phonemic = _phonemes_with_stress(phonikud_phonemes, chosen_stress)
            else:
                chosen_stress = phonikud_stress
                phonemic = phonikud_phonemes

        syllables = _phoneme_syllables(phonemic)

        rule_trace.append(f"chosen_source:{chosen_source}")

        # Practical respelling
        if manual_transliteration:
            practical = manual_transliteration
            rule_trace.append("manual_transliteration")
        else:
            practical = _to_practical(phonemic)

        # Dagesh status and begedkefat realization
        clusters = _letter_clusters(text)
        dagesh_status: list[tuple[int, str]] = []
        begadkefat: dict[int, str] = {}
        for base, marks, idx in clusters:
            status = "dagesh" if "\u05bc" in marks else "plain"
            dagesh_status.append((idx, status))
            if base in BEGADKEFAT or "\u05bc" in marks:
                # Find the nearest preceding full vowel; skip silent sheva/hataf
                preceding_vowel: str | None = None
                for prev_base, prev_marks, _ in reversed(clusters[:idx]):
                    name = _vowel_name(prev_marks)
                    if name is None and "\u05b0" in prev_marks:
                        name = "sheva"
                    if _is_full_vowel(name):
                        preceding_vowel = name
                        break
                letter_with_marks = base + "".join(marks)
                realization = begadkefat_realization(letter_with_marks, preceding_vowel, idx)
                if base in BEGADKEFAT:
                    begadkefat[idx] = realization["realized"]
        rule_trace.append("dagesh_scan")
        rule_trace.append("begadkefat_map")

        # Variants and unresolved decision
        variants: list[str] = []
        if practical:
            variants.append(practical)
        if phonikud_phonemes and phonikud_phonemes != phonemic:
            variants.append(phonikud_phonemes)
        if manual_phonemes and manual_phonemes != phonemic:
            variants.append(manual_phonemes)

        override_comparison = False
        unresolved = False

        if override:
            override_comparison = (
                phonikud_phonemes == manual_phonemes
                and phonikud_stress
                == (manual_stress if manual_stress is not None else phonikud_stress)
                and (manual_vocal_shva is None or phonikud_vocal_shva == manual_vocal_shva)
            )
            if phonikud_phonemes and (
                phonikud_phonemes != manual_phonemes
                or phonikud_stress != chosen_stress
                or (manual_vocal_shva is not None and phonikud_vocal_shva != manual_vocal_shva)
            ):
                unresolved = True
                rule_trace.append(
                    f"phonikud_override_disagreement:phonikud_stress={phonikud_stress}"
                    f",manual_stress={manual_stress}"
                )
        else:
            if rule_stress and rule_stress != phonikud_stress:
                unresolved = True
                rule_trace.append(
                    f"rule_phonikud_disagreement:rule_stress={rule_stress}"
                    f",phonikud_stress={phonikud_stress}"
                )

        # Confidence
        if override:
            confidence = 0.95 if override_comparison else 0.65
        elif not phonikud_phonemes:
            confidence = 0.4
        elif not unresolved:
            confidence = 0.85
        else:
            confidence = 0.5

        return {
            "phonemic": phonemic,
            "practical": practical,
            "syllabification": syllables,
            "lexical_stress": chosen_stress,
            "shva_status": shva_diag.shva_status,
            "dagesh_status": dagesh_status,
            "begadkefat": begadkefat,
            "variants": variants,
            "rule_trace": rule_trace,
            "phonikud_proposal": phonikud_phonemes,
            "override_comparison": override_comparison,
            "confidence": confidence,
            "unresolved": unresolved,
        }
