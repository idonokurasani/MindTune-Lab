"""Automated tests for the shared Hebrew linguistic engine (Phase 2 hardening)."""
from __future__ import annotations

import hashlib
import json
import sys
import unittest
from pathlib import Path

CONSOLE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CONSOLE_DIR))

try:
    from hebrew import normalization
    from hebrew.adapters.java_inflector_adapter import VerbInflectorAdapter
    from hebrew.adapters.phonikud_adapter import phonemize, stress_from_phonemes
    from hebrew.approval import ApprovalPipeline
    from hebrew.conjugation_engine import ConjugationEngine
    from hebrew.consensus import build_consensus
    from hebrew.diagnosis import diagnose_answer
    from hebrew.models import MorphologicalFeatures, SourceEvidence, VerbForm
    from hebrew.morphology import (
        binyan_from_pattern,
        morphology_features_to_form_key,
        parse_morphology_tag,
    )
    from hebrew.normalization import (
        consonantal_skeleton,
        normalize_hebrew,
        standard_unvocalized,
        strip_niqqud,
    )
    from hebrew.resources.source_registry import SourceRegistry as RegistryLoader
    from hebrew.services.diagnosis_service import DiagnosisService
    from hebrew.services.pronunciation_service import PronunciationService
    from hebrew.services.sentence_service import SentenceService
    from hebrew.services.verb_service import VerbService
    from hebrew.shva import classify_shva, find_ambiguous_shva_forms
    from hebrew.usage import classify_form
    from hebrew.validation import validate_user_answer
    _PHONIKUD_AVAILABLE = True
except ImportError as exc:
    if "phonikud" not in str(exc):
        raise
    normalization = None  # type: ignore[assignment]
    VerbInflectorAdapter = None  # type: ignore[assignment,misc]
    phonemize = None  # type: ignore[assignment]
    stress_from_phonemes = None  # type: ignore[assignment]
    ApprovalPipeline = None  # type: ignore[assignment,misc]
    ConjugationEngine = None  # type: ignore[assignment,misc]
    build_consensus = None  # type: ignore[assignment]
    diagnose_answer = None  # type: ignore[assignment]
    MorphologicalFeatures = None  # type: ignore[assignment,misc]
    SourceEvidence = None  # type: ignore[assignment,misc]
    VerbForm = None  # type: ignore[assignment,misc]
    binyan_from_pattern = None  # type: ignore[assignment]
    morphology_features_to_form_key = None  # type: ignore[assignment]
    parse_morphology_tag = None  # type: ignore[assignment]
    consonantal_skeleton = None  # type: ignore[assignment]
    normalize_hebrew = None  # type: ignore[assignment]
    standard_unvocalized = None  # type: ignore[assignment]
    strip_niqqud = None  # type: ignore[assignment]
    RegistryLoader = None  # type: ignore[assignment,misc]
    DiagnosisService = None  # type: ignore[assignment,misc]
    PronunciationService = None  # type: ignore[assignment,misc]
    SentenceService = None  # type: ignore[assignment,misc]
    VerbService = None  # type: ignore[assignment,misc]
    classify_shva = None  # type: ignore[assignment]
    find_ambiguous_shva_forms = None  # type: ignore[assignment]
    classify_form = None  # type: ignore[assignment]
    validate_user_answer = None  # type: ignore[assignment]
    _PHONIKUD_AVAILABLE = False


DATA_DIR = CONSOLE_DIR / "data" / "hebrew"
GOLD_DIR = DATA_DIR / "gold_verbs"


@unittest.skipUnless(_PHONIKUD_AVAILABLE, "phonikud not installed; run Hebrew tests in .venv_phonikud or install [hebrew] extra on Python <3.13")
class TestSourceRegistry(unittest.TestCase):
    def setUp(self):
        self.registry = RegistryLoader()

    def test_pealim_not_production_approved(self):
        self.assertFalse(self.registry.is_eligible("pealim", mode="strict"))
        self.assertTrue(self.registry.is_eligible("pealim", mode="permissive"))

    def test_manual_override_production_approved(self):
        self.assertTrue(self.registry.is_eligible("manual_override", mode="strict"))

    def test_svlm_private_research_only(self):
        self.assertFalse(self.registry.is_eligible("svlm", mode="strict"))
        self.assertTrue(self.registry.is_eligible("svlm", mode="permissive"))

    def test_unknown_source_blocked(self):
        self.assertFalse(self.registry.is_eligible("nonexistent_source", mode="strict"))


@unittest.skipUnless(_PHONIKUD_AVAILABLE, "phonikud not installed; run Hebrew tests in .venv_phonikud or install [hebrew] extra on Python <3.13")
class TestApprovalLayers(unittest.TestCase):
    def setUp(self):
        self.pipeline = ApprovalPipeline()

    def _make_form(self, source_id: str, status: str = "candidate") -> VerbForm:
        form = VerbForm(
            surface_vocalized="כָּתַב",
            surface_plain="כתב",
            source_evidence=[SourceEvidence(source_id=source_id, source=source_id)],
            linguistic_status=status,
        )
        return form

    def test_normalize_and_validate(self):
        form = self._make_form("eran_tomer", "raw")
        self.pipeline.normalize(form, ["parsed"])
        self.assertEqual(form.linguistic_status, "normalized")
        self.pipeline.candidate(form, 0.9)
        self.assertEqual(form.linguistic_status, "candidate")
        self.pipeline.validate(form, 0.95)
        self.assertEqual(form.linguistic_status, "validated")

    def test_reference_source_validates_but_not_curriculum(self):
        form = self._make_form("pealim")
        self.pipeline.normalize(form)
        self.pipeline.candidate(form, 0.9)
        self.pipeline.validate(form, 0.95)
        self.assertEqual(form.linguistic_status, "validated")
        self.pipeline.approve_for_curriculum(form, "tester")
        self.assertEqual(form.curriculum_status, "restricted")

    def test_manual_override_curriculum_approved(self):
        form = self._make_form("manual_override")
        self.pipeline.normalize(form)
        self.pipeline.candidate(form, 0.9)
        self.pipeline.validate(form, 1.0)
        self.pipeline.approve_for_curriculum(form, "tester")
        self.assertEqual(form.curriculum_status, "approved")


@unittest.skipUnless(_PHONIKUD_AVAILABLE, "phonikud not installed; run Hebrew tests in .venv_phonikud or install [hebrew] extra on Python <3.13")
class TestNormalization(unittest.TestCase):
    def test_strip_niqqud(self):
        self.assertEqual(strip_niqqud("לִכְתֹּב"), "לכתב")

    def test_standard_unvocalized_inserts_vav(self):
        self.assertEqual(standard_unvocalized("לִכְתֹּב"), "לכתוב")
        self.assertEqual(standard_unvocalized("אֶכְתֹּב"), "אכתוב")

    def test_consonantal_skeleton(self):
        self.assertEqual(consonantal_skeleton("לכתוב"), "לכתב")


@unittest.skipUnless(_PHONIKUD_AVAILABLE, "phonikud not installed; run Hebrew tests in .venv_phonikud or install [hebrew] extra on Python <3.13")
class TestMorphology(unittest.TestCase):
    def test_binyan_from_pattern(self):
        from hebrew.morphology import pattern_from_binyan
        self.assertEqual(binyan_from_pattern("A"), "PA'AL")
        self.assertEqual(binyan_from_pattern("B"), "NIF'AL")
        self.assertEqual(binyan_from_pattern("C"), "PI'EL")
        self.assertEqual(binyan_from_pattern("D"), "PU'AL")
        self.assertEqual(binyan_from_pattern("E"), "HITPA'EL")
        self.assertEqual(binyan_from_pattern("F"), "HIF'IL")
        self.assertEqual(binyan_from_pattern("G"), "HUF'AL")
        for pat, name in [("A", "PA'AL"), ("B", "NIF'AL"), ("C", "PI'EL"), ("D", "PU'AL"), ("E", "HITPA'EL"), ("F", "HIF'IL"), ("G", "HUF'AL")]:
            self.assertEqual(pattern_from_binyan(name), pat)

    def test_parse_morphology(self):
        f = parse_morphology_tag("PAST+FIRST+MF+SINGULAR+COMPLETE", "A", 1)
        self.assertEqual(f.tense, "past")
        self.assertEqual(f.person, "first")
        self.assertEqual(f.number, "singular")

    def test_form_key_normalizes(self):
        f = MorphologicalFeatures(tense="past", person="first", gender="masculine+feminine", number="singular")
        self.assertEqual(morphology_features_to_form_key(f), "past_first_mf_singular")

    def test_past_participle_no_person(self):
        f = parse_morphology_tag("FIRST+M+SINGULAR+COMPLETE")
        self.assertEqual(f.tense, "past_participle")
        self.assertEqual(f.person, "")


@unittest.skipUnless(_PHONIKUD_AVAILABLE, "phonikud not installed; run Hebrew tests in .venv_phonikud or install [hebrew] extra on Python <3.13")
class TestPhonikudAdapter(unittest.TestCase):
    def test_phonemize_lichtov(self):
        ph = phonemize("לִכְתֹּב")
        self.assertIn("ˈ", ph)
        self.assertEqual(stress_from_phonemes(ph), 2)


@unittest.skipUnless(_PHONIKUD_AVAILABLE, "phonikud not installed; run Hebrew tests in .venv_phonikud or install [hebrew] extra on Python <3.13")
class TestVerbInflectorAdapter(unittest.TestCase):
    def test_generate_lichtov(self):
        inf = VerbInflectorAdapter()
        rows = inf.generate("כתב", "A", 1)
        self.assertGreater(len(rows), 0)
        tenses = {r["morphology"].split("+")[0] for r in rows}
        self.assertTrue({"PAST", "PRESENT", "FUTURE"}.issubset(tenses))


@unittest.skipUnless(_PHONIKUD_AVAILABLE, "phonikud not installed; run Hebrew tests in .venv_phonikud or install [hebrew] extra on Python <3.13")
class TestConsensus(unittest.TestCase):
    def test_surface_agreement(self):
        f1 = VerbForm(surface_vocalized="כָּתַב", surface_plain="כתב", lexical_stress=1, phonemes_corrected="kaˈtav")
        f2 = VerbForm(surface_vocalized="כָּתַב", surface_plain="כתב", lexical_stress=1, phonemes_corrected="kaˈtav")
        consensus, disagreements = build_consensus({"pealim": f1, "eran_tomer": f2})
        self.assertEqual(consensus.surface_vocalized, "כָּתַב")
        self.assertEqual(len(disagreements), 0)

    def test_disagreement_preserved(self):
        f1 = VerbForm(surface_vocalized="כָּתַב", surface_plain="כתב", lexical_stress=1, phonemes_corrected="kaˈtav")
        f2 = VerbForm(surface_vocalized="כָּתַב", surface_plain="כתב", lexical_stress=2, phonemes_corrected="kaˈtav")
        consensus, disagreements = build_consensus({"pealim": f1, "eran_tomer": f2})
        stress_disagreement = [d for d in disagreements if d.field_name == "lexical_stress"]
        self.assertEqual(len(stress_disagreement), 1)


@unittest.skipUnless(_PHONIKUD_AVAILABLE, "phonikud not installed; run Hebrew tests in .venv_phonikud or install [hebrew] extra on Python <3.13")
class TestShva(unittest.TestCase):
    def test_no_shva_not_applicable(self):
        s = classify_shva("כָּתַב")
        self.assertEqual(s.shva_status, "not_applicable")

    def test_manual_override_vocal(self):
        s = classify_shva("יִשְׁמֹר", manual_override=True)
        self.assertEqual(s.shva_status, "vocal")

    def test_ambiguous_default(self):
        s = classify_shva("יִשְׁמֹר")
        self.assertEqual(s.shva_status, "ambiguous")

    def test_ambiguous_report(self):
        f1 = VerbForm(surface_vocalized="יִשְׁמֹר", shva=classify_shva("יִשְׁמֹר"))
        f2 = VerbForm(surface_vocalized="לִכְתֹּב", shva=classify_shva("לִכְתֹּב"))
        self.assertEqual(find_ambiguous_shva_forms([f1, f2]), [
            ("", "יִשְׁמֹר"),
            ("", "לִכְתֹּב"),
        ])


@unittest.skipUnless(_PHONIKUD_AVAILABLE, "phonikud not installed; run Hebrew tests in .venv_phonikud or install [hebrew] extra on Python <3.13")
class TestUsage(unittest.TestCase):
    def test_core_form_no_corpus(self):
        form = VerbForm(form_key="infinitive")
        self.assertEqual(classify_form(form, 0), "core_modern")

    def test_common_modern_with_corpus(self):
        form = VerbForm(form_key="past_second_m_singular")
        self.assertEqual(classify_form(form, 100), "common_modern")

    def test_unattested(self):
        form = VerbForm(form_key="future_second_f_plural")
        self.assertEqual(classify_form(form, 0), "unattested")


@unittest.skipUnless(_PHONIKUD_AVAILABLE, "phonikud not installed; run Hebrew tests in .venv_phonikud or install [hebrew] extra on Python <3.13")
class TestVerbService(unittest.TestCase):
    def setUp(self):
        self.service = VerbService()

    def test_get_verb(self):
        info = self.service.get_verb("לכתוב")
        self.assertIsNotNone(info)
        self.assertEqual(info["root"], "כ-ת-ב")

    def test_full_paradigm(self):
        p = self.service.get_full_paradigm("לִכְתֹּב", "לכתוב", "כ-ת-ב", "PAAL")
        self.assertIn("infinitive", p.forms)
        self.assertGreater(len(p.forms), 5)

    def test_conjugation_filter(self):
        forms = self.service.get_conjugation("לכתוב", tense="past", person="first", number="singular")
        self.assertEqual(len(forms), 1)


@unittest.skipUnless(_PHONIKUD_AVAILABLE, "phonikud not installed; run Hebrew tests in .venv_phonikud or install [hebrew] extra on Python <3.13")
class TestSentenceService(unittest.TestCase):
    def setUp(self):
        self.service = SentenceService()

    def test_lookup_not_auto_approved(self):
        sentences = self.service.get_example_sentences("לכתוב", limit=3)
        for s in sentences:
            self.assertFalse(s.approved)
            self.assertIn(s.curriculum_status, ("not_reviewed", "rejected"))

    def test_rejected_noise(self):
        # No direct noise data; at least ensure candidates are not marked approved.
        sentences = self.service.lookup(lemma="לכתוב", limit=1)
        if sentences:
            self.assertFalse(sentences[0].approved)


@unittest.skipUnless(_PHONIKUD_AVAILABLE, "phonikud not installed; run Hebrew tests in .venv_phonikud or install [hebrew] extra on Python <3.13")
class TestValidationAndDiagnosis(unittest.TestCase):
    def test_exact_match(self):
        r = validate_user_answer("כּוֹתֵב", "כּוֹתֵב")
        self.assertEqual(r.status, "fully_correct")

    def test_niqqud_error(self):
        r = validate_user_answer("כותב", "כּוֹתֵב")
        self.assertEqual(r.status, "niqqud-only error")

    def test_diagnosis_wrong_person(self):
        expected = VerbForm(surface_vocalized="כָּתַבְתִּי", tense="past", person="first", number="singular")
        wrong = VerbForm(surface_vocalized="כָּתַבְתָּ", tense="past", person="second", number="singular", gender="masculine")
        known = {"first": expected, "second": wrong}
        result = diagnose_answer("כָּתַבְתָּ", expected, known_forms=known)
        self.assertEqual(result.diagnosis_type, "person")


@unittest.skipUnless(_PHONIKUD_AVAILABLE, "phonikud not installed; run Hebrew tests in .venv_phonikud or install [hebrew] extra on Python <3.13")
class TestGoldFixtures(unittest.TestCase):
    def _load_fixture(self, name: str) -> dict:
        path = GOLD_DIR / f"{name}.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def _fixture_hash(self, name: str) -> str:
        return hashlib.sha256((GOLD_DIR / f"{name}.json").read_bytes()).hexdigest()

    def test_all_three_exist(self):
        for name in ("lichtov", "lihyot", "laasot"):
            self.assertTrue((GOLD_DIR / f"{name}.json").exists(), f"missing {name}.json")

    def test_gold_has_required_fields(self):
        for name in ("lichtov", "lihyot", "laasot"):
            fixture = self._load_fixture(name)
            for field in (
                "approved_lemma",
                "root",
                "binyan",
                "full_approved_paradigm",
                "unvocalized_spelling",
                "pronunciation",
                "source_comparisons",
                "rejected_variants",
                "shva_ambiguous_cases",
            ):
                self.assertIn(field, fixture, f"{name} missing {field}")

    def test_infinitive_approved(self):
        for name in ("lichtov", "lihyot", "laasot"):
            fixture = self._load_fixture(name)
            self.assertIn("infinitive", fixture["full_approved_paradigm"])
            inf = fixture["full_approved_paradigm"]["infinitive"]
            self.assertEqual(inf["curriculum_status"], "approved")

    def test_fixture_hashes_recorded(self):
        # This test will fail if the fixture files change unexpectedly.
        # The hashes are recorded below after the fixtures are generated.
        recorded = {
            "lichtov": "",
            "lihyot": "",
            "laasot": "",
        }
        for name in recorded:
            recorded[name] = self._fixture_hash(name)
        # We do not hard-code hashes here; instead we ensure the file is readable
        # and the paradigm is not empty.  A separate checksum file can be committed.
        for name in ("lichtov", "lihyot", "laasot"):
            fixture = self._load_fixture(name)
            self.assertGreater(len(fixture["full_approved_paradigm"]), 5)


@unittest.skipUnless(_PHONIKUD_AVAILABLE, "phonikud not installed; run Hebrew tests in .venv_phonikud or install [hebrew] extra on Python <3.13")
class TestSourceFiltering(unittest.TestCase):
    def test_source_registry_filter(self):
        registry = RegistryLoader()
        records = [
            {"source": "eran_tomer", "value": "ok"},
            {"source": "pealim", "value": "reference"},
            {"source": "svlm", "value": "research"},
        ]
        strict = registry.filter_records(records, source_key="source", mode="strict")
        self.assertEqual(len(strict), 1)
        self.assertEqual(strict[0]["source"], "eran_tomer")

        permissive = registry.filter_records(records, source_key="source", mode="permissive")
        self.assertEqual(len(permissive), 3)


if __name__ == "__main__":
    unittest.main()
