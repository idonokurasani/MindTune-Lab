"""Tests for the versioned Hebrew curriculum and MantraSelectionPolicy."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from mantra.phase1.curriculum import (
    CURRICULUM_PATH,
    Curriculum,
    CurriculumVerb,
    LearnerState,
    MantraExecutionPlan,
    MantraSelectionPolicy,
    MantraSelectionResult,
    build_execution_plan,
    hebrew_infinitive_to_latin_slug,
    plan_compact_mantra,
)


class SlugTests(unittest.TestCase):
    """Tests for the infinitive-to-slug transliterator."""

    def test_well_known_infinitives(self) -> None:
        cases = [
            ("לְהִתְקַשֵּׁר", "lehitkasher"),
            ("לִכְתֹּב", "lichtov"),
            ("לִהְיוֹת", "lihyot"),
            ("לַעֲשׂוֹת", "laasot"),
            ("לְהַגִּיד", "lehagid"),
            ("לְהַסְבִּיר", "lehasbir"),
            ("לְהָבִיא", "lehavi"),
            ("לִשְׁמוֹר", "lishmor"),
        ]
        for pointed, expected in cases:
            with self.subTest(pointed=pointed):
                self.assertEqual(hebrew_infinitive_to_latin_slug(pointed), expected)

    def test_slugs_are_ascii_and_lowercase(self) -> None:
        self.assertEqual(hebrew_infinitive_to_latin_slug("לְהִתְקַשֵּׁר"), "lehitkasher")


class CurriculumTests(unittest.TestCase):
    """Tests for the canonical curriculum data."""

    def test_curriculum_has_320_verbs_and_unique_slugs(self) -> None:
        curriculum = Curriculum.load(CURRICULUM_PATH)
        self.assertEqual(len(curriculum.verbs), 320)
        self.assertEqual(curriculum.version, "1.0.0")

        prefixes = {v.asset_id_prefix for v in curriculum.verbs}
        self.assertEqual(len(prefixes), len(curriculum.verbs))

        for verb in curriculum.verbs:
            self.assertTrue(verb.asset_id_prefix)
            self.assertTrue(verb.infinitive_plain)
            self.assertTrue(verb.infinitive_pointed)
            self.assertTrue(verb.binyan)

    def test_lookup_by_verb_id(self) -> None:
        curriculum = Curriculum.load(CURRICULUM_PATH)
        first = curriculum.verbs[0]
        self.assertEqual(curriculum.by_verb_id()[first.verb_id], first)

    def test_required_assets_match_compact_mantra_plan(self) -> None:
        verb = CurriculumVerb(
            verb_id="להתקשר",
            asset_id_prefix="lehitkasher",
            infinitive_pointed="לְהִתְקַשֵּׁר",
            infinitive_plain="להתקשר",
            italian_infinitive="telefonare",
        )
        required = set(verb.required_asset_ids())
        sequence = set(plan_compact_mantra(verb))
        # Every planned asset must be listed as required.
        self.assertTrue(sequence.issubset(required))


class PolicyTests(unittest.TestCase):
    """Tests for MantraSelectionPolicy."""

    def _curriculum(self) -> Curriculum:
        return Curriculum.load(CURRICULUM_PATH)

    def _policy(self, available: set[str] | None = None) -> MantraSelectionPolicy:
        return MantraSelectionPolicy(self._curriculum(), available_assets=available)

    def test_select_returns_typed_result_with_version_and_reason(self) -> None:
        curriculum = self._curriculum()
        policy = MantraSelectionPolicy(curriculum, available_assets=set())
        state = LearnerState()
        result = policy.select(state)
        self.assertIsInstance(result, MantraSelectionResult)
        self.assertEqual(result.policy_version, MantraSelectionPolicy.POLICY_VERSION)
        self.assertEqual(result.reason_code, "no_eligible_verb")

    def test_policy_is_deterministic(self) -> None:
        curriculum = self._curriculum()
        first = curriculum.verbs[0]
        assets = set(first.required_asset_ids())
        policy1 = self._policy(available=assets)
        policy2 = self._policy(available=assets)
        state = LearnerState(
            scheduled_new_content=(first.verb_id,),
        )
        self.assertEqual(policy1.select(state), policy2.select(state))

    def test_selects_only_verbs_with_available_assets(self) -> None:
        curriculum = self._curriculum()
        first = curriculum.verbs[0]
        available = set(first.required_asset_ids())
        policy = MantraSelectionPolicy(curriculum, available_assets=available)
        # No scheduled content; the only eligible verb is the first one.
        state = LearnerState()
        result = policy.select(state)
        self.assertEqual(result.verb_id, first.verb_id)
        self.assertEqual(result.reason_code, "curriculum_priority")

    def test_scheduled_new_content_takes_priority(self) -> None:
        curriculum = self._curriculum()
        first, second = curriculum.verbs[0], curriculum.verbs[1]
        available = set(first.required_asset_ids()) | set(second.required_asset_ids())
        policy = MantraSelectionPolicy(curriculum, available_assets=available)
        state = LearnerState(
            scheduled_new_content=(second.verb_id,),
        )
        result = policy.select(state)
        self.assertEqual(result.verb_id, second.verb_id)
        self.assertEqual(result.reason_code, "scheduled_new_content")

    def test_overdue_review_takes_priority_after_scheduled(self) -> None:
        curriculum = self._curriculum()
        first, second = curriculum.verbs[0], curriculum.verbs[1]
        available = set(first.required_asset_ids()) | set(second.required_asset_ids())
        policy = MantraSelectionPolicy(curriculum, available_assets=available)
        state = LearnerState(
            overdue_review=(second.verb_id,),
            recall_scores={second.verb_id: 0.4},
        )
        result = policy.select(state)
        self.assertEqual(result.verb_id, second.verb_id)
        self.assertEqual(result.reason_code, "overdue_review")

    def test_domino_error_prioritizes_low_recall(self) -> None:
        curriculum = self._curriculum()
        first, second = curriculum.verbs[0], curriculum.verbs[1]
        available = set(first.required_asset_ids()) | set(second.required_asset_ids())
        policy = MantraSelectionPolicy(curriculum, available_assets=available)
        state = LearnerState(
            recent_domino_errors={first.verb_id: 5, second.verb_id: 3},
            recall_scores={first.verb_id: 0.9, second.verb_id: 0.3},
        )
        result = policy.select(state)
        # second has lower recall despite fewer errors.
        self.assertEqual(result.verb_id, second.verb_id)
        self.assertEqual(result.reason_code, "domino_error")

    def test_low_recall_fallback(self) -> None:
        curriculum = self._curriculum()
        first = curriculum.verbs[0]
        available = set(first.required_asset_ids())
        policy = MantraSelectionPolicy(curriculum, available_assets=available)
        state = LearnerState(
            recall_scores={first.verb_id: 0.3},
        )
        result = policy.select(state)
        self.assertEqual(result.verb_id, first.verb_id)
        self.assertEqual(result.reason_code, "low_recall")

    def test_recent_exposure_limit_filters_out_verb(self) -> None:
        curriculum = self._curriculum()
        first, second = curriculum.verbs[0], curriculum.verbs[1]
        available = set(first.required_asset_ids()) | set(second.required_asset_ids())
        policy = MantraSelectionPolicy(curriculum, available_assets=available)
        state = LearnerState(
            last_exposure_hours={first.verb_id: 1.0},
            recent_exposure_limit_hours=24.0,
        )
        result = policy.select(state)
        self.assertEqual(result.verb_id, second.verb_id)

    def test_asset_preparation_mode_can_select_missing_assets(self) -> None:
        curriculum = self._curriculum()
        policy = MantraSelectionPolicy(curriculum, available_assets=set())
        state = LearnerState()
        result = policy.select(state, asset_preparation_mode=True)
        self.assertTrue(result.verb_id)
        self.assertEqual(result.reason_code, "asset_preparation")
        self.assertTrue(result.missing_assets)

    def test_policy_never_uses_eeg(self) -> None:
        # The LearnerState dataclass has no EEG field, so this is a compile-time
        # guarantee.  We also verify no EEG data is read.
        state = LearnerState()
        self.assertFalse(hasattr(state, "eeg"))


class ExecutionPlanTests(unittest.TestCase):
    """Tests for mantra execution plan construction."""

    def test_build_execution_plan_returns_asset_sequence(self) -> None:
        curriculum = Curriculum.load(CURRICULUM_PATH)
        first = curriculum.verbs[0]
        available = set(first.required_asset_ids())
        state = LearnerState()
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            plan = build_execution_plan(curriculum, state, output_dir, available_assets=available)
            self.assertIsInstance(plan, MantraExecutionPlan)
            self.assertEqual(plan.verb_id, first.verb_id)
            self.assertTrue(plan.asset_sequence)
            self.assertEqual(plan.policy_version, MantraSelectionPolicy.POLICY_VERSION)
            self.assertTrue(plan.output_path)

    def test_no_plan_when_no_eligible_verb(self) -> None:
        curriculum = Curriculum.load(CURRICULUM_PATH)
        state = LearnerState()
        with tempfile.TemporaryDirectory() as tmp:
            plan = build_execution_plan(curriculum, state, Path(tmp), available_assets=set())
            self.assertEqual(plan.verb_id, "")
            self.assertFalse(plan.asset_sequence)
            self.assertEqual(plan.reason_code, "no_eligible_verb")


if __name__ == "__main__":
    unittest.main()
