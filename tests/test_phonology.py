"""Tests for the Hebrew phonological validation module (Phase 3)."""

from __future__ import annotations

import csv
import json
import sys
import unittest
from pathlib import Path

CONSOLE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CONSOLE_DIR))

try:
    from hebrew.normalization import decompose
    from hebrew.phonology import (
        PronunciationValidator,
        begadkefat_realization,
        extract_syllables,
    )
    from hebrew.shva import classify_shva

    _PHONIKUD_AVAILABLE = True
except ImportError as exc:
    if "phonikud" not in str(exc):
        raise
    decompose = None  # type: ignore[assignment,misc]
    PronunciationValidator = None  # type: ignore[assignment,misc]
    begadkefat_realization = None  # type: ignore[assignment,misc]
    extract_syllables = None  # type: ignore[assignment,misc]
    classify_shva = None  # type: ignore[assignment,misc]
    _PHONIKUD_AVAILABLE = False


DATA_DIR = CONSOLE_DIR / "data"
EVAL_PATH = DATA_DIR / "phonikud_eval" / "phonikud_evaluation.json"
GOLD_DIR = DATA_DIR / "hebrew" / "gold_verbs"
CSV_PATH = DATA_DIR / "hebrew" / "resources" / "eran_tomer" / "InflectedVerbsExtended.csv"

REQUIRED_KEYS = {
    "phonemic",
    "practical",
    "syllabification",
    "lexical_stress",
    "shva_status",
    "dagesh_status",
    "begadkefat",
    "variants",
    "rule_trace",
    "phonikud_proposal",
    "override_comparison",
    "confidence",
    "unresolved",
}


def _has_sheva(text: str) -> bool:
    return "\u05b0" in decompose(text)


class TestPhonologicalValidator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not _PHONIKUD_AVAILABLE:
            raise unittest.SkipTest(
                "phonikud not installed; run Hebrew tests in .venv_phonikud "
                "or install the [hebrew] extra on Python <3.13"
            )
        cls.validator = PronunciationValidator()
        with EVAL_PATH.open(encoding="utf-8") as f:
            cls.eval_data = json.load(f)

    def test_result_schema(self):
        """All returned dicts contain the expected phonological fields."""
        result = self.validator.validate("לִכְתֹּב")
        self.assertTrue(REQUIRED_KEYS.issubset(result.keys()))
        self.assertIsInstance(result["syllabification"], list)
        self.assertIsInstance(result["dagesh_status"], list)
        self.assertIsInstance(result["begadkefat"], dict)
        self.assertIsInstance(result["rule_trace"], list)
        self.assertIsInstance(result["unresolved"], bool)

    def test_evaluation_stress_matches_expected(self):
        """Stress positions match the verified evaluation overrides."""
        for entry in self.eval_data:
            context = {"verb": entry["verb"], "form_key": entry["form_key"]}
            result = self.validator.validate(entry["hebrew_with_niqqud"], context)
            self.assertEqual(
                result["lexical_stress"],
                entry["expected_stress"],
                f"{entry['verb']} {entry['form_key']} stress mismatch",
            )

    def test_phonikud_disagreements_flagged_unresolved(self):
        """When Phonikud diverges from the manual override, unresolved is True."""
        for entry in self.eval_data:
            context = {"verb": entry["verb"], "form_key": entry["form_key"]}
            result = self.validator.validate(entry["hebrew_with_niqqud"], context)
            phonikud_ok = (
                result["phonikud_proposal"] == entry["manual_override"]
                and entry["phonikud_stress"] == entry["override_stress"]
            )
            self.assertEqual(
                result["override_comparison"],
                phonikud_ok,
                f"{entry['verb']} {entry['form_key']} override comparison mismatch",
            )
            if not phonikud_ok:
                self.assertTrue(
                    result["unresolved"],
                    f"{entry['verb']} {entry['form_key']} should be unresolved",
                )

    def test_shva_classification(self):
        """Shva status reflects the manual override when a sheva is present."""
        for entry in self.eval_data:
            if not _has_sheva(entry["hebrew_with_niqqud"]):
                continue
            context = {"verb": entry["verb"], "form_key": entry["form_key"]}
            result = self.validator.validate(entry["hebrew_with_niqqud"], context)
            expected = "vocal" if entry["vocal_shva_override"] else "silent"
            self.assertEqual(
                result["shva_status"],
                expected,
                f"shva mismatch for {entry['hebrew_with_niqqud']}",
            )

    def test_shva_classifier_reuse(self):
        """The public classify_shva helper is reused and returns a dataclass."""
        diag = classify_shva("לִכְתֹּב", manual_override=False)
        self.assertEqual(diag.shva_status, "silent")
        diag2 = classify_shva("תִּכְתְּבוּ", manual_override=True)
        self.assertEqual(diag2.shva_status, "vocal")

    def test_extract_syllables(self):
        """Syllabification returns a non-empty list of strings."""
        for entry in self.eval_data[:10]:
            syllables = extract_syllables(entry["hebrew_with_niqqud"])
            self.assertIsInstance(syllables, list)
            self.assertGreater(len(syllables), 0)
            for syl in syllables:
                self.assertIsInstance(syl, str)

    def test_begadkefat_realization(self):
        """Begedkefet letters realize as plosive or spirant correctly."""
        # ב spirant after a vowel, plosive initially
        self.assertEqual(begadkefat_realization("ב", None, 0)["realized"], "b")
        self.assertEqual(begadkefat_realization("ב", "qamats", 1)["realized"], "v")
        # כ plosive initially, spirant after a vowel, dagesh overrides
        self.assertEqual(begadkefat_realization("כ", "qamats", 0)["realized"], "k")
        self.assertEqual(begadkefat_realization("כְ", "hiriq", 1)["realized"], "χ")
        self.assertEqual(begadkefat_realization("כְּ", "hiriq", 1)["realized"], "k")
        # פ spirant after a vowel, plosive with dagesh
        self.assertEqual(begadkefat_realization("פְ", "patah", 2)["realized"], "f")
        self.assertEqual(begadkefat_realization("פּ", "qamats", 0)["realized"], "p")
        # ג, ד, ת remain plosive in modern Hebrew
        self.assertEqual(begadkefat_realization("ג", "qamats", 1)["realized"], "g")
        self.assertEqual(begadkefat_realization("דְ", "segol", 2)["realized"], "d")
        self.assertEqual(begadkefat_realization("ת", "qamats", 3)["realized"], "t")

    def test_gold_verbs(self):
        """The three Phase 2 verified verbs validate without exceptions."""
        for name in ("lihyot", "lichtov", "laasot"):
            with (GOLD_DIR / f"{name}.json").open(encoding="utf-8") as f:
                data = json.load(f)
            for key, form in data["full_approved_paradigm"].items():
                surface = form["surface_vocalized"]
                context = {"verb": data["lemma_plain"], "form_key": key}
                result = self.validator.validate(surface, context)
                self.assertTrue(REQUIRED_KEYS.issubset(result.keys()))
                self.assertGreaterEqual(result["lexical_stress"], 1)
                self.assertLessEqual(result["lexical_stress"], len(result["syllabification"]) or 1)

    def test_eran_tomer_csv_forms(self):
        """CSV inflected forms produce valid phonological records."""
        with CSV_PATH.open(encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        self.assertGreaterEqual(len(rows), 30, "CSV should have at least 30 rows")
        for row in rows[:35]:
            with self.subTest(vocalized=row["vocalized_inflection"]):
                result = self.validator.validate(row["vocalized_inflection"], row["morphology"])
                self.assertTrue(REQUIRED_KEYS.issubset(result.keys()))
                self.assertIsInstance(result["phonemic"], str)
                self.assertIsInstance(result["practical"], str)
                self.assertGreater(len(result["syllabification"]), 0)
                self.assertTrue(0 <= result["confidence"] <= 1)


if __name__ == "__main__":
    unittest.main()
