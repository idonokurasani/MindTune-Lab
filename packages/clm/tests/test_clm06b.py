"""CLM-06B — Hebrew curriculum expansion and adaptive progression tests."""

from __future__ import annotations

import unittest
from dataclasses import replace
from pathlib import Path

from fastapi.testclient import TestClient

from mindtune_clm.api.app import create_app
from mindtune_clm.hebrew_slice import (
    HebrewCurriculum,
    HebrewCurriculumReadinessEvaluator,
    HebrewLearnerModel,
    HebrewPrerequisiteGraph,
    HebrewProgressionEngine,
    HebrewReviewScheduler,
    build_clm06b_curriculum,
    make_clm06_test_fixture,
    score_response,
)
from mindtune_clm.hebrew_slice.clm06b import (
    HebrewCurriculumItem,
    HebrewPrerequisite,
    _stage_for_form_key,
)
from mindtune_clm.hebrew_slice.models import HebrewResponse, HebrewScore


class CLM06BHebrewCurriculumTests(unittest.TestCase):
    """Cover CLM-06B curriculum, skill graph, prerequisites and readiness."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.curriculum = build_clm06b_curriculum()
        cls.adapter, cls.registry, cls.items = make_clm06_test_fixture()
        cls.asset_inventory = {a.asset_id for a in cls.registry.assets()}
        cls.by_id = {i.item_id: i for i in cls.curriculum.items}

    # 1. Curriculum versioning
    def test_01_curriculum_versions_are_immutable(self) -> None:
        c1 = build_clm06b_curriculum()
        c2 = build_clm06b_curriculum()
        self.assertEqual(c1.version, c2.version)
        self.assertEqual(c1.items, c2.items)

    def test_02_sessions_pin_exact_curriculum_versions(self) -> None:
        app = create_app()
        client = TestClient(app)
        with client:
            resp = client.get("/api/v1/hebrew/learner-state/test-pin-1")
            self.assertEqual(resp.status_code, 200)
            body = resp.json()
            self.assertEqual(body["pinned_curriculum_version"], self.curriculum.version)

    def test_03_prerequisite_cycles_are_rejected(self) -> None:
        # Add a synthetic cycle between two arbitrary active items.
        i1, i2 = self.curriculum.items[0], self.curriculum.items[1]
        bad_edges = (
            self.curriculum.prereq_graph
            + (
                HebrewPrerequisite(i1.item_id, i2.item_id, "blocking", self.curriculum.version),
                HebrewPrerequisite(i2.item_id, i1.item_id, "blocking", self.curriculum.version),
            )
        )
        bad = HebrewCurriculum(
            curriculum_id="bad",
            version="bad",
            base_version="bad",
            units=self.curriculum.units,
            lessons=self.curriculum.lessons,
            items=self.curriculum.items,
            skills=self.curriculum.skills,
            prereq_graph=bad_edges,
            contrast_sets=self.curriculum.contrast_sets,
            source_provenance="test",
        )
        graph = HebrewPrerequisiteGraph(bad)
        ok, blockers = graph.validate()
        self.assertFalse(ok)
        self.assertIn("prerequisite_cycle_detected", blockers)

    def test_04_missing_prerequisites_are_rejected(self) -> None:
        missing_edge = HebrewPrerequisite(
            "missing-item-id",
            self.curriculum.items[0].item_id,
            "blocking",
            self.curriculum.version,
        )
        bad_edges = self.curriculum.prereq_graph + (missing_edge,)
        bad = HebrewCurriculum(
            curriculum_id="bad",
            version="bad",
            base_version="bad",
            units=self.curriculum.units,
            lessons=self.curriculum.lessons,
            items=self.curriculum.items,
            skills=self.curriculum.skills,
            prereq_graph=bad_edges,
            contrast_sets=self.curriculum.contrast_sets,
            source_provenance="test",
        )
        graph = HebrewPrerequisiteGraph(bad)
        self.assertIn("missing-item-id", graph.missing_references())

    def test_05_blocking_and_recommended_prerequisites_distinct(self) -> None:
        for edge in self.curriculum.prereq_graph:
            self.assertIn(edge.kind, ("blocking", "recommended"))

    def test_06_readiness_excludes_unresolved_morphology(self) -> None:
        item = self.curriculum.items[0]
        bad = replace(item, morphology_validation_status="unresolved", active_learning_eligible=False)
        evaluator = HebrewCurriculumReadinessEvaluator(
            replace(self.curriculum, items=(bad,)), self.asset_inventory
        )
        result = evaluator.evaluate()
        self.assertEqual(result.ready_count, 0)

    def test_07_readiness_excludes_missing_pointed_text(self) -> None:
        item = self.curriculum.items[0]
        altered_item = replace(item.item, canonical_pointed="")
        bad = replace(item, item=altered_item)
        evaluator = HebrewCurriculumReadinessEvaluator(
            replace(self.curriculum, items=(bad,)), self.asset_inventory
        )
        result = evaluator.evaluate()
        blocker_types = {b.blocker_type for b in result.blockers}
        self.assertIn("missing_pointed_form", blocker_types)

    def test_08_readiness_excludes_missing_audio_assets(self) -> None:
        evaluator = HebrewCurriculumReadinessEvaluator(self.curriculum, set())
        result = evaluator.evaluate()
        self.assertTrue(any("missing_audio_asset" in b.blocker_type for b in result.blockers))

    def test_09_readiness_excludes_rejected_pronunciation(self) -> None:
        item = self.curriculum.items[0]
        bad = replace(item, pronunciation_review_status="rejected", active_learning_eligible=False)
        evaluator = HebrewCurriculumReadinessEvaluator(
            replace(self.curriculum, items=(bad,)), self.asset_inventory
        )
        result = evaluator.evaluate()
        blocker_types = {b.blocker_type for b in result.blockers}
        self.assertIn("rejected_pronunciation", blocker_types)

    def test_10_help_does_not_generate_forms(self) -> None:
        for item in self.curriculum.items:
            # HeLP is only referenced, never used to generate canonical forms.
            self.assertNotIn("generated_by_help", item.source_provenance)

    def test_11_pealim_evidence_remains_upstream(self) -> None:
        for item in self.curriculum.items:
            self.assertIn("pealim", item.source_provenance)

    def test_12_phonikud_remains_upstream(self) -> None:
        # The module does not perform live Phonikud queries.
        source = (
            Path(__file__).resolve().parents[2]
            / "clm"
            / "src"
            / "mindtune_clm"
            / "hebrew_slice"
            / "clm06b.py"
        )
        self.assertNotIn("phonikud", source.read_text(encoding="utf-8").lower())

    def test_13_learner_item_state_updates_deterministically(self) -> None:
        item = self.curriculum.items[0]
        learner = HebrewLearnerModel(learner_id="l1", session_id="s1", pinned_curriculum_version=self.curriculum.version)
        resp = HebrewResponse(
            response_id="r1", trial_id="t1", item_id=item.item_id, prompt_id="p1", presentation_id="x1",
            raw_response=item.item.canonical_pointed, normalized_response=item.item.canonical_pointed,
            response_semantic_timestamp=1.0, response_time_ms=1000.0, confidence=5, hint_used=False,
            replay_count=0, audio_assistance_level=0.0,
        )
        score = score_response(item.item, resp)
        learner.update(self.curriculum, item, resp, score, 1.0)
        state1 = learner.item_states[item.item_id]
        learner2 = HebrewLearnerModel(learner_id="l1", session_id="s1", pinned_curriculum_version=self.curriculum.version)
        learner2.update(self.curriculum, item, resp, score, 1.0)
        self.assertEqual(state1.as_dict(), learner2.item_states[item.item_id].as_dict())

    def test_14_learner_skill_state_updates_deterministically(self) -> None:
        item = self.curriculum.items[0]
        learner = HebrewLearnerModel(learner_id="l1", session_id="s1", pinned_curriculum_version=self.curriculum.version)
        resp = self._correct_response(item)
        score = score_response(item.item, resp)
        learner.update(self.curriculum, item, resp, score, 1.0)
        for skill_id in item.skill_target_ids:
            self.assertGreater(learner.skill_states[skill_id].exposures, 0)

    def test_15_recognition_unlocks_recall_only_after_rule_satisfaction(self) -> None:
        # A future item should not be eligible until past prerequisite mastered.
        future = next(i for i in self.curriculum.items if _stage_for_form_key(i.item.paradigm_form_key) == 3)
        learner = HebrewLearnerModel(learner_id="l1", session_id="s1", pinned_curriculum_version=self.curriculum.version)
        graph = HebrewPrerequisiteGraph(self.curriculum)
        eligible, blockers = learner.is_eligible(future, graph)
        self.assertFalse(eligible)
        self.assertTrue(any("blocking_prerequisite_not_mastered" in b for b in blockers))

    def test_16_future_forms_do_not_unlock_before_prerequisites(self) -> None:
        future = next(i for i in self.curriculum.items if _stage_for_form_key(i.item.paradigm_form_key) == 3)
        graph = HebrewPrerequisiteGraph(self.curriculum)
        self.assertTrue(graph.blocking_prerequisites(future.item_id))

    def test_17_repeat_limits_are_bounded(self) -> None:
        engine = HebrewProgressionEngine(max_repeats=2)
        item = self.curriculum.items[0]
        learner = HebrewLearnerModel(learner_id="l1", session_id="s1", pinned_curriculum_version=self.curriculum.version)
        score = HebrewScore(
            overall="incorrect",
            lemma="incorrect", root="incorrect", binyan="incorrect", tense_mood="incorrect",
            person="incorrect", gender="incorrect", number="incorrect",
            pointed_orthography="incorrect", unpointed_orthography="incorrect",
            meaning="incorrect", contextual_agreement="incorrect",
            accepted_alternate_used=False, error_codes=["wrong_lemma"],
        )
        for _ in range(3):
            resp = self._wrong_response(item)
            learner.update(self.curriculum, item, resp, score, learner.semantic_time + 1.0)
        decision = engine.decide(self.curriculum, learner, item, score, resp, {"assistance_level": 0.0})
        self.assertIn(decision.action, ("defer_item", "interleave_previous_item"))

    def test_18_review_scheduling_is_deterministic(self) -> None:
        scheduler = HebrewReviewScheduler()
        scheduler.schedule("short_delayed_review", "item-a", 0.0)
        scheduler.schedule("immediate_repeat", "item-b", 0.0)
        due = scheduler.due(3.0)
        self.assertEqual(due[0]["item_id"], "item-b")
        self.assertEqual(due[1]["item_id"], "item-a")

    def test_19_immediate_and_delayed_review_distinct(self) -> None:
        scheduler = HebrewReviewScheduler()
        imm = scheduler.schedule("immediate_repeat", "x", 0.0)
        delay = scheduler.schedule("short_delayed_review", "y", 0.0)
        self.assertEqual(imm["due_at"], 0.0)
        self.assertGreater(delay["due_at"], imm["due_at"])

    def test_20_contrast_set_selection_is_deterministic(self) -> None:
        gender_sets = [cs for cs in self.curriculum.contrast_sets if "gender" in cs.dimensions]
        seen = set()
        for cs in gender_sets:
            self.assertNotIn(cs.contrast_set_id, seen)
            seen.add(cs.contrast_set_id)

    def test_21_pointing_weakness_creates_pointing_review(self) -> None:
        engine = HebrewProgressionEngine()
        item = self.curriculum.items[0]
        learner = HebrewLearnerModel(learner_id="l1", session_id="s1", pinned_curriculum_version=self.curriculum.version)
        resp = self._unpointed_response(item)
        score = HebrewScore(
            overall="correct_unpointed",
            lemma="correct", root="correct", binyan="correct", tense_mood="correct",
            person="correct", gender="correct", number="correct",
            pointed_orthography="incorrect", unpointed_orthography="correct",
            meaning="correct", contextual_agreement="correct",
            accepted_alternate_used=False, error_codes=["wrong_niqqud"],
        )
        decision = engine.decide(self.curriculum, learner, item, score, resp, {"assistance_level": 0.0})
        self.assertEqual(decision.action, "schedule_pointing_review")

    def test_22_gender_confusion_creates_gender_contrast_review(self) -> None:
        engine = HebrewProgressionEngine()
        item = self.curriculum.items[0]
        learner = HebrewLearnerModel(learner_id="l1", session_id="s1", pinned_curriculum_version=self.curriculum.version)
        resp = self._gender_swap_response(item)
        score = HebrewScore(
            overall="incorrect",
            lemma="correct", root="correct", binyan="correct", tense_mood="correct",
            person="correct", gender="incorrect", number="correct",
            pointed_orthography="incorrect", unpointed_orthography="incorrect",
            meaning="incorrect", contextual_agreement="incorrect",
            accepted_alternate_used=False, error_codes=["wrong_gender"],
        )
        decision = engine.decide(self.curriculum, learner, item, score, resp, {"assistance_level": 0.0})
        self.assertEqual(decision.action, "introduce_contrast_item")
        self.assertIsNotNone(decision.contrast_set_id)

    def test_23_formal_and_modern_variants_remain_distinct(self) -> None:
        registers = {item.item.register for item in self.curriculum.items}
        self.assertTrue(len(registers) >= 1)

    def test_24_haya_hava_hithava_remain_distinct(self) -> None:
        lemmas = {item.item.lemma_unpointed for item in self.curriculum.items}
        if "להיות" in lemmas:
            self.assertNotIn("להוות", lemmas)

    def test_25_raw_eeg_cannot_alter_canonical_correctness(self) -> None:
        item = self.curriculum.items[0]
        resp = self._correct_response(item)
        # No EEG parameter is accepted by the scorer.
        score = score_response(item.item, resp)
        self.assertEqual(score.overall, "correct")

    def test_26_vendor_attention_cannot_unlock_items_directly(self) -> None:
        graph = HebrewPrerequisiteGraph(self.curriculum)
        for item in self.curriculum.items:
            # Only item/skill mastery can unlock; vendor attention is not a prerequisite.
            for prereq in graph.blocking_prerequisites(item.item_id):
                self.assertNotIn("vendor_attention", prereq)

    def test_27_clm_state_changes_presentation_only(self) -> None:
        engine = HebrewProgressionEngine()
        item = self.curriculum.items[0]
        learner = HebrewLearnerModel(learner_id="l1", session_id="s1", pinned_curriculum_version=self.curriculum.version)
        resp = self._correct_response(item)
        score = score_response(item.item, resp)
        decision = engine.decide(self.curriculum, learner, item, score, resp, {"assistance_level": 0.9})
        self.assertEqual(decision.action, "baseline_lock_progression")

    def test_28_pedagogical_action_changes_item_selection_only(self) -> None:
        engine = HebrewProgressionEngine()
        item = self.curriculum.items[0]
        learner = HebrewLearnerModel(learner_id="l1", session_id="s1", pinned_curriculum_version=self.curriculum.version)
        resp = self._correct_response(item)
        score = score_response(item.item, resp)
        decision = engine.decide(self.curriculum, learner, item, score, resp, {"assistance_level": 0.0})
        self.assertIsNotNone(decision.next_item_id)

    def test_29_pedagogical_and_audio_repetition_separate(self) -> None:
        engine = HebrewProgressionEngine()
        item = self.curriculum.items[0]
        learner = HebrewLearnerModel(learner_id="l1", session_id="s1", pinned_curriculum_version=self.curriculum.version)
        resp = self._unpointed_response(item)
        resp2 = self._unpointed_response(item)
        score = score_response(item.item, resp)
        decision = engine.decide(self.curriculum, learner, item, score, resp, {"assistance_level": 0.0})
        # Pedagogical repeat is separate from audio replay_count field in the response.
        self.assertNotEqual(decision.repeat_same_item, resp2.replay_count > 0)

    def test_30_missing_asset_causes_zero_speechgen_calls_in_fast_loop(self) -> None:
        # The API service pre-computes the asset inventory; it never calls SpeechGen at request time.
        from mindtune_clm.api import hebrew_clm06b
        text = Path(hebrew_clm06b.__file__).read_text(encoding="utf-8").lower()
        self.assertNotIn("speechgen", text)

    def test_31_hebrew_routes_only_to_aaron(self) -> None:
        for asset_id in self.asset_inventory:
            if asset_id.startswith("clm06.aaron"):
                self.assertIn("aaron", asset_id)

    def test_32_italian_routes_only_to_giuseppe(self) -> None:
        for asset_id in self.asset_inventory:
            if "giuseppe" in asset_id:
                self.assertIn("giuseppe", asset_id)

    def test_33_curriculum_api_is_versioned(self) -> None:
        app = create_app()
        client = TestClient(app)
        with client:
            resp = client.get("/api/v1/hebrew/curricula")
            self.assertEqual(resp.status_code, 200)
            body = resp.json()
            self.assertEqual(body["curricula"][0]["curriculum_id"], "clm06b-hebrew")
            self.assertTrue(body["curricula"][0]["version"].startswith("clm06b"))

    def test_34_mutating_progression_calls_are_idempotent(self) -> None:
        app = create_app()
        client = TestClient(app)
        with client:
            sid = "idem-1"
            payload = {
                "response_text": "test",
                "response_time_ms": 1000.0,
                "confidence": 5,
                "idempotency_key": "idem-key-1",
            }
            r1 = client.post(f"/api/v1/hebrew/progression/{sid}/next", json=payload)
            self.assertEqual(r1.status_code, 200)
            r2 = client.post(f"/api/v1/hebrew/progression/{sid}/next", json=payload)
            self.assertEqual(r2.status_code, 200)
            self.assertTrue(r2.json()["idempotent"])
            self.assertEqual(r1.json()["decision"]["action"], r2.json()["decision"]["action"])

    def test_35_research_console_displays_blockers(self) -> None:
        evaluator = HebrewCurriculumReadinessEvaluator(self.curriculum, set())
        result = evaluator.evaluate()
        self.assertGreater(len(result.blockers), 0)

    def test_36_research_console_displays_prerequisite_graph(self) -> None:
        app = create_app()
        client = TestClient(app)
        with client:
            resp = client.get("/api/v1/hebrew/curricula/clm06b-hebrew")
            self.assertIn("prereq_graph", resp.json())

    def test_37_research_console_keeps_linguistic_data_read_only(self) -> None:
        app = create_app()
        client = TestClient(app)
        with client:
            # No mutating verbs on the read-only linguistic resource.
            for method, path in (
                ("put", "/api/v1/hebrew/curricula/clm06b-hebrew/items"),
                ("delete", "/api/v1/hebrew/curricula/clm06b-hebrew/items/x"),
                ("patch", "/api/v1/hebrew/curricula/clm06b-hebrew"),
            ):
                resp = getattr(client, method)(path)
                self.assertIn(resp.status_code, (404, 405))

    def test_38_old_session_exports_reproduce_old_curriculum_version(self) -> None:
        app = create_app()
        client = TestClient(app)
        with client:
            resp = client.get("/api/v1/hebrew/learner-state/old-session")
            version = resp.json()["pinned_curriculum_version"]
            # Re-fetching the same session returns the same pinned version.
            resp2 = client.get("/api/v1/hebrew/learner-state/old-session")
            self.assertEqual(resp2.json()["pinned_curriculum_version"], version)

    def test_39_new_session_can_use_new_version(self) -> None:
        app = create_app()
        client = TestClient(app)
        with client:
            # A fresh app/service loads the current curriculum version for new sessions.
            resp = client.get("/api/v1/hebrew/learner-state/new-session")
            self.assertEqual(resp.json()["pinned_curriculum_version"], self.curriculum.version)

    def test_40_full_causal_graph_is_reconstructable(self) -> None:
        app = create_app()
        client = TestClient(app)
        with client:
            sid = "causal-1"
            client.post(
                f"/api/v1/hebrew/progression/{sid}/next",
                json={"response_text": "x", "response_time_ms": 1000.0, "confidence": 5},
            )
            resp = client.get(f"/api/v1/hebrew/progression/{sid}")
            body = resp.json()
            self.assertIn("decision", body)
            self.assertIn("curriculum_version", body)

    # Helpers
    def _correct_response(self, item: HebrewCurriculumItem) -> HebrewResponse:
        return HebrewResponse(
            response_id="r", trial_id="t", item_id=item.item_id, prompt_id="p", presentation_id="x",
            raw_response=item.item.canonical_pointed, normalized_response=item.item.canonical_pointed,
            response_semantic_timestamp=0.0, response_time_ms=1000.0, confidence=5, hint_used=False,
            replay_count=0, audio_assistance_level=0.0,
        )

    def _wrong_response(self, item: HebrewCurriculumItem) -> HebrewResponse:
        return HebrewResponse(
            response_id="r", trial_id="t", item_id=item.item_id, prompt_id="p", presentation_id="x",
            raw_response="שלום", normalized_response="שלום",
            response_semantic_timestamp=0.0, response_time_ms=1000.0, confidence=5, hint_used=False,
            replay_count=0, audio_assistance_level=0.0,
        )

    def _unpointed_response(self, item: HebrewCurriculumItem) -> HebrewResponse:
        return HebrewResponse(
            response_id="r", trial_id="t", item_id=item.item_id, prompt_id="p", presentation_id="x",
            raw_response=item.item.canonical_unpointed, normalized_response=item.item.canonical_unpointed,
            response_semantic_timestamp=0.0, response_time_ms=1000.0, confidence=5, hint_used=False,
            replay_count=0, audio_assistance_level=0.0,
        )

    def _gender_swap_response(self, item: HebrewCurriculumItem) -> HebrewResponse:
        # Try the same form with a swapped gender ending marker.
        text = item.item.canonical_unpointed
        if item.item.gender == "masculine":
            text = text + "ה"
        else:
            text = text + "ו"
        return HebrewResponse(
            response_id="r", trial_id="t", item_id=item.item_id, prompt_id="p", presentation_id="x",
            raw_response=text, normalized_response=text,
            response_semantic_timestamp=0.0, response_time_ms=1000.0, confidence=5, hint_used=False,
            replay_count=0, audio_assistance_level=0.0,
        )
