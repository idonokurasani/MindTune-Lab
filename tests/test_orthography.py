"""Tests for the normative Hebrew orthography module."""
from __future__ import annotations

import unittest

from hebrew.orthography import canonical_unvocalized, classify_root_orthographic_class, spelling_variants


class TestRootOrthographicClass(unittest.TestCase):
    def test_regular_pa_al(self):
        rc = classify_root_orthographic_class("כ-ת-ב")
        self.assertFalse(rc["guttural"])
        self.assertFalse(rc["initial_nun"])
        self.assertFalse(rc["contains_yod_vav"])
        self.assertFalse(rc["final_he"])
        self.assertFalse(rc["hollow"])
        self.assertFalse(rc["geminate"])
        self.assertFalse(rc["quadriliteral"])
        self.assertFalse(rc["irregular"])

    def test_guttural(self):
        rc = classify_root_orthographic_class("כ-ע-ס")
        self.assertTrue(rc["guttural"])
        self.assertFalse(rc["hollow"])

    def test_final_he(self):
        rc = classify_root_orthographic_class("ב-נ-ה")
        self.assertTrue(rc["final_he"])

    def test_hollow(self):
        rc = classify_root_orthographic_class("ב-ו-שׁ")
        self.assertTrue(rc["hollow"])
        self.assertTrue(rc["contains_yod_vav"])

    def test_initial_nun(self):
        rc = classify_root_orthographic_class("נ-פ-ל")
        self.assertTrue(rc["initial_nun"])

    def test_geminate(self):
        rc = classify_root_orthographic_class("ש-ב-ב")
        self.assertTrue(rc["geminate"])

    def test_quadriliteral(self):
        rc = classify_root_orthographic_class("ב-ד-ק-ר")
        self.assertTrue(rc["quadriliteral"])

    def test_irregular(self):
        rc = classify_root_orthographic_class("ה-י-ה")
        self.assertTrue(rc["irregular"])


class TestCanonicalUnvocalized(unittest.TestCase):
    """Verify canonical spelling for Phase 2 verbs and common CSV forms."""

    def _assert_canonical(self, vocalized, expected, root, binyan, form_key):
        result = canonical_unvocalized(vocalized, root=root, binyan=binyan, form_key=form_key)
        self.assertEqual(
            result["spelling"],
            expected,
            f"{vocalized} (root {root}, form {form_key}): expected {expected}, got {result}",
        )
        self.assertFalse(result["unresolved"])
        self.assertGreaterEqual(result["confidence"], 0.9)
        self.assertEqual(result["class"], "canonical")

    def test_lichtov_paradigm(self):
        cases = [
            ("לִכְתֹּב", "לכתוב", "INFINITIVE+E+E+E+MISSING"),
            ("אֶכְתֹּב", "אכתוב", "FUTURE+FIRST+MF+SINGULAR+MISSING"),
            ("נִכְתֹּב", "נכתוב", "FUTURE+FIRST+MF+PLURAL+MISSING"),
            ("תִּכְתְּבִי", "תכתבי", "FUTURE+SECOND+F+SINGULAR+COMPLETE"),
            ("כָּתַב", "כתב", "PAST+THIRD+M+SINGULAR+COMPLETE"),
            ("כָּתַבְתִּי", "כתבתי", "PAST+FIRST+MF+SINGULAR+COMPLETE"),
            ("כּוֹתֵב", "כותב", "PRESENT+FIRST+M+SINGULAR+COMPLETE"),
            ("כָּתוּב", "כתוב", "BEINONI+FIRST+M+SINGULAR+COMPLETE"),
            ("כִּתְבוּ", "כתבו", "IMPERATIVE+SECOND+M+PLURAL+COMPLETE"),
        ]
        for voc, expected, morph in cases:
            with self.subTest(voc=voc):
                self._assert_canonical(voc, expected, "כ-ת-ב", "PA'AL", morph)

    def test_lihyot_paradigm(self):
        cases = [
            ("לִהְיוֹת", "להיות", "INFINITIVE+E+E+E+COMPLETE"),
            ("אֶהְיֶה", "אהיה", "FUTURE+FIRST+MF+SINGULAR+COMPLETE"),
            ("הָיִיתִי", "הייתי", "PAST+FIRST+MF+SINGULAR+COMPLETE"),
            ("הָיָה", "היה", "PAST+THIRD+M+SINGULAR+COMPLETE"),
            ("הוֹוֶה", "הווה", "PRESENT+FIRST+M+SINGULAR+COMPLETE"),
            ("הָיוּ", "היו", "PAST+THIRD+M+PLURAL+COMPLETE"),
            ("הָיְתָה", "היתה", "PAST+THIRD+F+SINGULAR+MISSING"),
            ("הוֹווֹת", "הווות", "PRESENT+FIRST+F+PLURAL+COMPLETE"),
        ]
        for voc, expected, morph in cases:
            with self.subTest(voc=voc):
                self._assert_canonical(voc, expected, "ה-י-ה", "PA'AL", morph)

    def test_laasot_paradigm(self):
        cases = [
            ("לַעֲשׂוֹת", "לעשות", "INFINITIVE+E+E+E+COMPLETE"),
            ("יַעֲשֶׂה", "יעשה", "FUTURE+THIRD+M+SINGULAR+COMPLETE"),
            ("עָשִׂיתִי", "עשיתי", "PAST+FIRST+MF+SINGULAR+COMPLETE"),
            ("עָשָׂה", "עשה", "PAST+THIRD+M+SINGULAR+COMPLETE"),
            ("עוֹשֶׂה", "עושה", "PRESENT+FIRST+M+SINGULAR+COMPLETE"),
            ("עָשׂוּ", "עשו", "PAST+THIRD+M+PLURAL+COMPLETE"),
        ]
        for voc, expected, morph in cases:
            with self.subTest(voc=voc):
                self._assert_canonical(voc, expected, "ע-ש-ה", "PA'AL", morph)

    def test_csv_common_beged(self):
        cases = [
            ("אֶבְגֹּד", "אבגוד", "FUTURE+FIRST+MF+SINGULAR+MISSING"),
            ("בְּגֹד", "בגוד", "IMPERATIVE+SECOND+M+SINGULAR+MISSING"),
            ("לִבְגֹּד", "לבגוד", "INFINITIVE+E+E+E+MISSING"),
            ("בּוֹגֵד", "בוגד", "PRESENT+FIRST+M+SINGULAR+COMPLETE"),
            ("בָּגַד", "בגד", "PAST+THIRD+M+SINGULAR+COMPLETE"),
        ]
        for voc, expected, morph in cases:
            with self.subTest(voc=voc):
                self._assert_canonical(voc, expected, "ב-ג-ד", "PA'AL", morph)

    def test_csv_hufal_and_piel(self):
        cases = [
            ("אֻבַּקְתְּ", "אובקת", "PAST+SECOND+F+SINGULAR+MISSING"),
            ("מְאֻבָּק", "מאובק", "PRESENT+FIRST+M+SINGULAR+MISSING"),
            ("אִיבַּקְתִּי", "איבקתי", "PAST+FIRST+MF+SINGULAR+COMPLETE"),
            ("מְאַבֵּק", "מאבק", "PRESENT+FIRST+M+SINGULAR+COMPLETE"),
        ]
        for voc, expected, morph in cases:
            with self.subTest(voc=voc):
                self._assert_canonical(voc, expected, "א-ב-ק", "", morph)

    def test_guttural_past_unresolved(self):
        result = canonical_unvocalized(
            "כָּעֹסְתְּ",
            root="כ-ע-ס",
            binyan="PA'AL",
            form_key="PAST+SECOND+F+SINGULAR+MISSING",
        )
        self.assertTrue(result["unresolved"])
        self.assertEqual(result["spelling"], "כעסת")
        self.assertEqual(result["class"], "unresolved")
        self.assertLess(result["confidence"], 0.6)
        variants = result["variants"]
        self.assertEqual(variants["full"], "כעוסת")
        self.assertEqual(variants["defective"], "כעסת")
        self.assertIn("כעוסת", variants["common_nonstandard"])

    def test_stative_past_unresolved(self):
        result = canonical_unvocalized(
            "קָטֹנְתְּ",
            root="ק-ט-ן",
            binyan="PA'AL",
            form_key="PAST+SECOND+F+SINGULAR+MISSING",
        )
        self.assertTrue(result["unresolved"])
        self.assertEqual(result["spelling"], "קטנת")
        variants = result["variants"]
        self.assertEqual(variants["full"], "קטונת")
        self.assertEqual(variants["defective"], "קטנת")

    def test_rejected_spellings_flagged(self):
        result = canonical_unvocalized(
            "לִכְתֹּב",
            root="כ-ת-ב",
            binyan="PA'AL",
            form_key="INFINITIVE+E+E+E+MISSING",
        )
        self.assertTrue(result["variants"]["rejected"])
        for bad in result["variants"]["rejected"]:
            self.assertNotEqual(bad, result["spelling"])

    def test_spelling_variants(self):
        result = canonical_unvocalized(
            "לִכְתֹּב",
            root="כ-ת-ב",
            binyan="PA'AL",
            form_key="INFINITIVE+E+E+E+MISSING",
        )
        variants = result["variants"]
        self.assertEqual(variants["full"], "לכתוב")
        self.assertEqual(variants["defective"], "לכתב")
        self.assertIn("לכתב", variants["common_nonstandard"])


if __name__ == "__main__":
    unittest.main()
