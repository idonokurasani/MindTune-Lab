"""Phase 4D tests for specification-driven asset contract, readiness, and runtime."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from mantra.domain.audio_profile import AudioProfile
from mantra.domain.hebrew.specification_repository import (
    HebrewSpecificationError,
    HebrewSpecificationRepository,
)
from mantra.phase1.asset_contract import (
    AssetAvailabilityClass,
    AudioAssetInventory,
    AudioAssetRequirement,
    build_asset_requirements,
    build_compact_mantra_requirements,
)
from mantra.phase1.assets import AudioAssetRegistry
from mantra.phase1.curriculum import (
    Curriculum,
    CurriculumVerb,
    LearnerState,
    MantraExecutionPlan,
    MantraSelectionPolicy,
    build_execution_plan,
)
from mantra.phase1.eligibility import ReadinessEvaluator
from mantra.phase1.runtime import (
    execute_asset_preparation_plan,
    execute_mantra_plan,
)
from mantra.phase1.tts import FakeTTSProvider, TTSRuntimeError


class _Phase4DTestBase(unittest.TestCase):
    """Provide a temporary global cache and a fake audio profile."""

    TEST_PROFILE = AudioProfile(
        profile_id="test",
        profile_version="1.0.0",
        provider="fake",
        italian_locale="it-IT",
        italian_voice_id="fake_it",
        hebrew_locale="he-IL",
        hebrew_voice_id="fake_he",
        hebrew_text_policy="source_niqqud_preserved_tts_same",
        output_format="wav",
        sample_rate=22050,
        channel_count=1,
        synthesis_parameters={"rate": 1.0, "pitch": 0.0},
        silence_durations={"inter_item_default": 0.3, "section_boundary": 0.0},
        cache_key_version="1",
    )

    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)
        self.cache_dir = Path(self.tmpdir.name) / "cache"
        self.registry_path = Path(self.tmpdir.name) / "assets.json"

        # Patch the global cache directory used by both asset registry and
        # asset inventory for the duration of each test.
        import mantra.phase1.asset_contract as asset_contract_module
        import mantra.phase1.assets as assets_module

        self._orig_cache_dir = assets_module.GLOBAL_CACHE_DIR
        assets_module.GLOBAL_CACHE_DIR = self.cache_dir
        asset_contract_module.GLOBAL_CACHE_DIR = self.cache_dir
        self.addCleanup(lambda: setattr(assets_module, "GLOBAL_CACHE_DIR", self._orig_cache_dir))
        self.addCleanup(
            lambda: setattr(asset_contract_module, "GLOBAL_CACHE_DIR", self._orig_cache_dir)
        )

    def make_registry(self) -> AudioAssetRegistry:
        return AudioAssetRegistry(self.registry_path)

    def make_inventory(self) -> AudioAssetInventory:
        return AudioAssetInventory(
            self.make_registry(), self.TEST_PROFILE, cache_dir=self.cache_dir
        )

    def make_readiness(self) -> ReadinessEvaluator:
        return ReadinessEvaluator(
            HebrewSpecificationRepository(),
            self.TEST_PROFILE,
            self.make_inventory(),
        )


class AssetContractTests(_Phase4DTestBase):
    """Tests for typed asset requirements and inventory classification."""

    def test_build_asset_requirements_deterministic(self) -> None:
        repo = HebrewSpecificationRepository()
        spec = repo.get("lichtov")
        req1 = build_asset_requirements(spec, self.TEST_PROFILE)
        req2 = build_asset_requirements(spec, self.TEST_PROFILE)
        self.assertEqual(req1, req2)
        self.assertTrue(all(isinstance(r, AudioAssetRequirement) for r in req1))
        self.assertTrue(all(r.cache_key for r in req1))

    def test_compact_mantra_requirements_order(self) -> None:
        repo = HebrewSpecificationRepository()
        spec = repo.get("lichtov")
        reqs = build_compact_mantra_requirements(spec, self.TEST_PROFILE)
        self.assertTrue(reqs)
        # Italian infinitive introduction is first when include_italian_intro=True.
        self.assertEqual(reqs[0].asset_kind.value, "italian_prompt")
        self.assertEqual(reqs[0].section.value, "infinitive")
        # Hebrew infinitive follows.
        self.assertEqual(reqs[1].section.value, "infinitive")
        self.assertEqual(reqs[1].asset_kind.value, "tts_input")

    def test_inventory_classifies_missing_synthesizable(self) -> None:
        repo = HebrewSpecificationRepository()
        spec = repo.get("lichtov")
        reqs = build_asset_requirements(spec, self.TEST_PROFILE)
        inventory = self.make_inventory()
        for req in reqs:
            self.assertEqual(inventory.classify(req), AssetAvailabilityClass.MISSING_SYNTHESIZABLE)


class ReadinessTests(_Phase4DTestBase):
    """Tests for the readiness evaluator and selection policy integration."""

    def _lichtov_verb(self) -> CurriculumVerb:
        return CurriculumVerb(
            verb_id="lichtov",
            asset_id_prefix="lichtov",
            infinitive_pointed="לִכְתֹּב",
            infinitive_plain="לכתוב",
            italian_infinitive="scrivere",
            root="כ-ת-ב",
            binyan="PA'AL",
            pattern="",
        )

    def test_readiness_blocks_learner_execution_without_assets(self) -> None:
        readiness = self.make_readiness()
        report = readiness.evaluate(self._lichtov_verb())
        self.assertEqual(
            report.learner_execution_eligibility.value,
            "ineligible_missing_assets",
        )
        self.assertEqual(report.asset_preparation_eligibility.value, "eligible")

    def test_policy_with_readiness_source_filters_unready_verbs(self) -> None:
        verb = self._lichtov_verb()
        curriculum = Curriculum(
            version="test",
            generated_at="",
            source="",
            verbs=[verb],
        )
        readiness = self.make_readiness()
        policy = MantraSelectionPolicy(curriculum, readiness_source=readiness)
        state = LearnerState()
        result = policy.select(state)
        # No assets present, so the only verb is not eligible for execution.
        self.assertEqual(result.reason_code, "no_eligible_verb")

    def test_execution_plan_with_readiness_includes_requirements(self) -> None:
        verb = self._lichtov_verb()
        curriculum = Curriculum(
            version="test",
            generated_at="",
            source="",
            verbs=[verb],
        )
        readiness = self.make_readiness()
        output_dir = Path(self.tmpdir.name) / "out"
        plan = build_execution_plan(
            curriculum,
            LearnerState(),
            output_dir,
            readiness_source=readiness,
            audio_profile=self.TEST_PROFILE,
        )
        self.assertIsInstance(plan, MantraExecutionPlan)
        # Without assets no verb can be selected for execution.
        self.assertEqual(plan.verb_id, "")

        prep_plan = build_execution_plan(
            curriculum,
            LearnerState(),
            output_dir,
            readiness_source=readiness,
            audio_profile=self.TEST_PROFILE,
            asset_preparation_mode=True,
        )
        self.assertIsNotNone(prep_plan.requirements)
        self.assertTrue(prep_plan.asset_sequence)
        self.assertTrue(prep_plan.requirements)


class RuntimeTests(_Phase4DTestBase):
    """Tests for the audio runtime boundary."""

    def test_execute_mantra_plan_raises_on_missing_assets(self) -> None:
        repo = HebrewSpecificationRepository()
        spec = repo.get("lichtov")
        reqs = build_compact_mantra_requirements(spec, self.TEST_PROFILE)
        plan = MantraExecutionPlan(
            verb_id="lichtov",
            asset_id_prefix="lichtov",
            asset_sequence=[r.asset_id for r in reqs],
            reason_code="test",
            policy_version="test",
            output_path=Path(self.tmpdir.name) / "out.wav",
            requirements=list(reqs),
        )
        registry = self.make_registry()
        with self.assertRaises(TTSRuntimeError):
            execute_mantra_plan(plan, registry)

    def test_end_to_end_prepare_and_execute(self) -> None:
        repo = HebrewSpecificationRepository()
        spec = repo.get("lichtov")
        reqs = build_compact_mantra_requirements(spec, self.TEST_PROFILE)
        registry = self.make_registry()
        # Prepare all missing requirements with the fake provider.
        provider = FakeTTSProvider(sample_rate=22050)
        missing = list(reqs)
        execute_asset_preparation_plan(missing, registry, provider=provider)

        # After preparation, the inventory no longer sees them as missing.
        inventory = self.make_inventory()
        for req in reqs:
            classification = inventory.classify(req)
            self.assertNotEqual(
                classification,
                AssetAvailabilityClass.MISSING_SYNTHESIZABLE,
                f"{req.asset_id} should not be missing after preparation",
            )

        plan = MantraExecutionPlan(
            verb_id="lichtov",
            asset_id_prefix="lichtov",
            asset_sequence=[r.asset_id for r in reqs],
            reason_code="test",
            policy_version="test",
            output_path=Path(self.tmpdir.name) / "out.wav",
            requirements=list(reqs),
        )
        manifest = execute_mantra_plan(plan, registry)
        self.assertTrue(Path(manifest["file"]).exists())
        self.assertEqual(manifest["sample_rate"], 22050)


class VerticalSliceReconciliationTests(_Phase4DTestBase):
    """Tests reconciling the reviewed vertical-slice specifications.

    `lehavot` was an invalid planning-document alias for `lihyot` and has
    been removed from the approved specification directory. These tests
    ensure `lichtov` and `lihyot` remain authoritative and `lehavot` cannot
    be silently loaded as `lihyot`.
    """

    def _lihyot_verb(self) -> CurriculumVerb:
        return CurriculumVerb(
            verb_id="lihyot",
            asset_id_prefix="lihyot",
            infinitive_pointed="לִהְיוֹת",
            infinitive_plain="להיות",
            italian_infinitive="essere",
            root="ה-י-ה",
            binyan="PA'AL",
            pattern="",
        )

    def test_lichtov_retained_and_valid(self) -> None:
        repo = HebrewSpecificationRepository()
        spec = repo.get("lichtov")
        self.assertEqual(spec.verb_id, "lichtov")
        self.assertEqual(spec.approved_lemma.source_text, "לִכְתֹּב")
        self.assertEqual(spec.approved_lemma.tts_text, "לכתוב")
        result = repo.validate("lichtov")
        self.assertTrue(result.valid)
        self.assertTrue(result.checksum_match)

    def test_lihyot_retained_and_valid(self) -> None:
        repo = HebrewSpecificationRepository()
        spec = repo.get("lihyot")
        self.assertEqual(spec.verb_id, "lihyot")
        self.assertEqual(spec.approved_lemma.source_text, "לִהְיוֹת")
        self.assertEqual(spec.approved_lemma.tts_text, "להיות")
        result = repo.validate("lihyot")
        self.assertTrue(result.valid)
        self.assertTrue(result.checksum_match)

    def test_lehavot_is_not_found_and_not_lihyot(self) -> None:
        """Regression: lehavot must not be an approved lihyot alias."""
        repo = HebrewSpecificationRepository()
        self.assertFalse(repo.has("lehavot"))
        result = repo.validate("lehavot")
        self.assertFalse(result.valid)
        self.assertIn("no specification for verb 'lehavot'", result.errors)
        with self.assertRaises(HebrewSpecificationError):
            repo.get("lehavot")

    def test_lihyot_and_lichtov_specs_are_distinct(self) -> None:
        repo = HebrewSpecificationRepository()
        lichtov = repo.get("lichtov")
        lihyot = repo.get("lihyot")
        self.assertNotEqual(lichtov.verb_id, lihyot.verb_id)
        self.assertNotEqual(lichtov.approved_lemma.source_text, lihyot.approved_lemma.source_text)
        self.assertNotEqual(lichtov.root, lihyot.root)

    def test_lihyot_asset_requirements_use_lihyot_prefix(self) -> None:
        repo = HebrewSpecificationRepository()
        spec = repo.get("lihyot")
        reqs = build_asset_requirements(spec, self.TEST_PROFILE)
        self.assertTrue(reqs)
        for req in reqs:
            self.assertTrue(
                req.asset_id.startswith("he.lihyot.") or req.asset_id.startswith("it.lihyot.")
            )
            self.assertIsNotNone(req.section)

    def test_lihyot_end_to_end_prepare_and_execute(self) -> None:
        repo = HebrewSpecificationRepository()
        spec = repo.get("lihyot")
        reqs = build_compact_mantra_requirements(spec, self.TEST_PROFILE)
        registry = self.make_registry()
        provider = FakeTTSProvider(sample_rate=22050)
        execute_asset_preparation_plan(list(reqs), registry, provider=provider)

        plan = MantraExecutionPlan(
            verb_id="lihyot",
            asset_id_prefix="lihyot",
            asset_sequence=[r.asset_id for r in reqs],
            reason_code="test",
            policy_version="test",
            output_path=Path(self.tmpdir.name) / "lihyot.wav",
            requirements=list(reqs),
        )
        manifest = execute_mantra_plan(plan, registry)
        self.assertTrue(Path(manifest["file"]).exists())
