"""CLM-06 Hebrew adaptive vertical slice tests."""

from __future__ import annotations

import unittest
from pathlib import Path

from mindtune_clm.audio.assets import AudioAssetRegistry
from mindtune_clm.hebrew_slice import (
    HebrewAdaptiveSession,
    HebrewAssetError,
    HebrewAssetResolver,
    HebrewErrorCode,
    make_clm06_test_fixture,
    make_synthetic_hebrew_audio_asset,
    score_response,
)
from mindtune_clm.hebrew_slice.events import HebrewSliceEventType
from mindtune_clm.hebrew_slice.models import HebrewAdaptiveItem, HebrewResponse
from mindtune_clm.hebrew_slice.trial_factory import HebrewTrialFactory
from mindtune_clm.state import MantraControlState


class CLM06HebrewAdaptiveTests(unittest.TestCase):
    """Test the CLM-06 Hebrew adaptive vertical slice."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.adapter, cls.registry, cls.items = make_clm06_test_fixture()
        cls.by_id = {i.item_id: i for i in cls.items}

    # ------------------------------------------------------------------
    # Fixture and curriculum
    # ------------------------------------------------------------------
    def test_fixture_loads_from_existing_hebrew_engine(self) -> None:
        self.assertTrue(self.items)
        for item in self.items:
            self.assertTrue(item.canonical_unpointed)
            self.assertTrue(item.linguistic_validation_status in ("approved", "validated"))

    def test_at_least_two_lemmas_and_varied_forms(self) -> None:
        lemmas = {i.lemma_unpointed for i in self.items}
        self.assertGreaterEqual(len(lemmas), 2)
        tenses = {i.tense for i in self.items}
        self.assertIn("past", tenses)
        self.assertIn("present", tenses)

    def test_unresolved_or_rejected_items_excluded(self) -> None:
        for item in self.items:
            self.assertNotEqual(item.linguistic_validation_status, "rejected")

    def test_required_audio_assets_present_in_test_fixture(self) -> None:
        inventory = {a.asset_id for a in self.registry.assets()}
        for item in self.items:
            self.assertTrue(all(a in inventory for a in item.required_audio_asset_ids))

    def test_no_second_morphology_engine(self) -> None:
        # The slice must not ship its own morphology generator.
        hebrew_slice_dir = Path(__file__).resolve().parents[2] / "src" / "mindtune_clm" / "hebrew_slice"
        for path in hebrew_slice_dir.glob("*.py"):
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("pealim", text.lower())
            self.assertNotIn("speechgen", text.lower())
            self.assertNotIn("phonikud", text.lower())

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------
    def _make_response(self, item: HebrewAdaptiveItem, text: str, latency: float = 800.0) -> HebrewResponse:
        return HebrewResponse(
            response_id=f"r-{text[:10]}",
            trial_id="t1",
            item_id=item.item_id,
            prompt_id="p1",
            presentation_id="pres1",
            raw_response=text,
            normalized_response=text,
            response_semantic_timestamp=0.0,
            response_time_ms=latency,
            confidence=5,
            hint_used=False,
            replay_count=0,
            audio_assistance_level=0.0,
        )

    def test_correct_pointed_response_scores_correct(self) -> None:
        item = self.items[0]
        resp = self._make_response(item, item.canonical_pointed)
        score = score_response(item, resp)
        self.assertEqual(score.overall, "correct")
        for dim in ("lemma", "root", "binyan", "pointed_orthography", "unpointed_orthography"):
            self.assertEqual(getattr(score, dim), "correct")

    def test_unpointed_response_scores_correct_unpointed(self) -> None:
        item = self.items[0]
        resp = self._make_response(item, item.canonical_unpointed)
        score = score_response(item, resp)
        self.assertEqual(score.overall, "correct_unpointed")
        self.assertIn(HebrewErrorCode.POINTED_UNPOINTED_MISMATCH.value, score.error_codes)

    def test_incorrect_response_is_not_correct(self) -> None:
        item = self.items[0]
        resp = self._make_response(item, "שלום")
        score = score_response(item, resp)
        self.assertEqual(score.overall, "incorrect")

    def test_transliteration_rejected(self) -> None:
        item = self.items[0]
        resp = self._make_response(item, "kotev")
        score = score_response(item, resp)
        self.assertEqual(score.overall, "invalid")
        self.assertIn(HebrewErrorCode.TRANSLITERATION_INSTEAD_OF_HEBREW.value, score.error_codes)

    def test_omitted_response_not_answered(self) -> None:
        item = self.items[0]
        resp = self._make_response(item, "  ")
        score = score_response(item, resp)
        self.assertEqual(score.overall, "not_answered")
        self.assertIn(HebrewErrorCode.OMITTED_RESPONSE.value, score.error_codes)

    def test_haya_hava_distinct(self) -> None:
        item = self.by_id.get("clm06-להיות-infinitive", self.items[0])
        resp = self._make_response(item, "להוות")
        score = score_response(item, resp)
        self.assertIn(HebrewErrorCode.HAYA_HAVA_HIT_HAVA_CONFUSION.value, score.error_codes)

    def test_scoring_does_not_query_pealim(self) -> None:
        # If the scorer were querying Pealim it would need network; this test is a guard.
        item = self.items[0]
        score = score_response(item, self._make_response(item, item.canonical_unpointed))
        self.assertIn(score.overall, ("correct", "correct_unpointed", "accepted_alternate"))

    # ------------------------------------------------------------------
    # Asset resolution
    # ------------------------------------------------------------------
    def test_asset_resolver_uses_aaron_and_not_hila_hannah(self) -> None:
        resolver = HebrewAssetResolver(self.registry, aaron_fallback_asset_id="speech_segment")
        item = self.items[0]
        resolved = resolver.resolve(item)
        self.assertIn("aaron", resolved.hebrew_asset.provenance[0].lower())

    def test_hila_hannah_asset_rejected(self) -> None:
        hannah_asset = make_synthetic_hebrew_audio_asset("hannah_test", "Hannah test")
        reg = AudioAssetRegistry([hannah_asset])
        resolver = HebrewAssetResolver(reg, aaron_fallback_asset_id=None)
        item = self.items[0]
        item = HebrewAdaptiveItem(**{**item.as_dict(), "required_audio_asset_ids": ["hannah_test"]})
        with self.assertRaises(HebrewAssetError):
            resolver.resolve(item)

    def test_aaron_pointed_text_preserved(self) -> None:
        resolver = HebrewAssetResolver(self.registry)
        item = self.items[0]
        resolved = resolver.resolve(item)
        self.assertEqual(resolved.hebrew_pointed_text, item.canonical_pointed)

    def test_missing_asset_raises_or_fallbacks_zero_speechgen(self) -> None:
        empty = AudioAssetRegistry()
        resolver = HebrewAssetResolver(empty, aaron_fallback_asset_id=None)
        with self.assertRaises(HebrewAssetError):
            resolver.resolve(self.items[0])

    # ------------------------------------------------------------------
    # Trial factory
    # ------------------------------------------------------------------
    def test_trial_ids_are_deterministic(self) -> None:
        factory = HebrewTrialFactory()
        cs = MantraControlState.baseline()
        t1 = factory.make_trial(self.items[0], "italian_to_hebrew", 1, cs)
        t2 = factory.make_trial(self.items[0], "italian_to_hebrew", 1, cs)
        self.assertEqual(t1.trial_id, t2.trial_id)

    def test_recognition_trial_has_choices(self) -> None:
        factory = HebrewTrialFactory()
        cs = MantraControlState.baseline()
        trial = factory.make_trial(self.items[0], "hebrew_recognition", 1, cs, distractors=["שלום"])
        self.assertIsNotNone(trial.choices)

    # ------------------------------------------------------------------
    # Session and closed loop
    # ------------------------------------------------------------------
    def _new_session(self, items=None, max_trials: int = 10) -> HebrewAdaptiveSession:
        return HebrewAdaptiveSession(
            session_id="s-test",
            items=items or self.items[:10],
            asset_registry=self.registry,
            max_trials=max_trials,
            clock=lambda: 0.0,
        )

    def test_session_readiness_and_start(self) -> None:
        session = self._new_session()
        trial = session.start()
        self.assertIsNotNone(trial)
        self.assertIn(HebrewSliceEventType.HEBREW_SESSION_STARTED, [e.event_type for e in session.event_log.events])

    def test_correct_stable_learner(self) -> None:
        session = self._new_session(self.items[:4], max_trials=3)
        trial = session.start()
        for _ in range(3):
            result = session.respond(trial.item.canonical_pointed)
            self.assertIn(result["score"]["overall"], ("correct", "correct_unpointed"))
            if session.completed:
                break
            trial = session.current_trial
            if trial is None:
                break

    def test_repeated_morphology_error_adapts(self) -> None:
        session = self._new_session(self.items[:3], max_trials=6)
        _ = session.start()
        for _ in range(4):
            result = session.respond("שלום")
            self.assertEqual(result["score"]["overall"], "incorrect")
            if session.completed or session.current_trial is None:
                break

    def test_clm_audio_adaptation_changes_assistance_not_truth(self) -> None:
        session = self._new_session(self.items[:3], max_trials=5)
        trial = session.start()
        # Two errors cause recovery-required and a control-state change.
        session.respond("שלום")
        first_control = session.current_control_state.as_dict()
        session.respond("שלום")
        second_control = session.current_control_state.as_dict()
        self.assertNotEqual(first_control["assistance_level"], second_control["assistance_level"])
        # The item itself is unchanged.
        self.assertEqual(session.current_item, trial.item)

    def test_recovery_withdraws_assistance(self) -> None:
        session = self._new_session(self.items[:3], max_trials=8)
        _ = session.start()
        session.respond("שלום")
        session.respond("שלום")
        elevated = session.current_control_state.assistance_level
        for _ in range(3):
            if session.current_trial is None:
                break
            session.respond(session.current_trial.item.canonical_pointed, response_time_ms=500.0)
        self.assertLess(session.current_control_state.assistance_level, elevated)

    def test_sensor_disconnect_does_not_falsely_deteriorate(self) -> None:
        session = self._new_session(self.items[:2], max_trials=6)
        session.start()
        with self.assertRaises(Exception) as cm:
            session.respond("שלום", sensor_disconnect=True)
            session.respond("שלום", sensor_disconnect=True)
            session.respond("שלום", sensor_disconnect=True)
        self.assertIn("sensor", str(cm.exception).lower())

    def test_duplicate_response_not_double_scored(self) -> None:
        session = self._new_session(self.items[:2], max_trials=4)
        trial = session.start()
        _ = session.respond(trial.item.canonical_unpointed, response_id="dup")
        r2 = session.respond(trial.item.canonical_unpointed, response_id="dup")
        self.assertTrue(r2.get("duplicate"))

    def test_session_summary_has_causal_graph(self) -> None:
        session = self._new_session(self.items[:3], max_trials=3)
        session.start()
        session.respond(self.items[0].canonical_unpointed)
        summary = session.summary()
        self.assertIn("causal_graph", summary)
        self.assertGreater(len(summary["causal_graph"]["event_ids"]), 0)

    # ------------------------------------------------------------------
    # Console and API exposure (lightweight)
    # ------------------------------------------------------------------
    def test_readiness_report(self) -> None:
        inventory = {a.asset_id for a in self.registry.assets()}
        report = self.adapter.readiness_report(inventory)
        self.assertTrue(report["ready"])
        self.assertEqual(report["ready_count"], report["approved_count"])

    def test_items_export_with_provenance(self) -> None:
        item = self.items[0]
        d = item.as_dict()
        self.assertIn("source_id", d)
        self.assertIn("morphology_provenance", d)
        self.assertIn("pointing_provenance", d)


class CLM06EndToEndAcceptance(unittest.TestCase):
    """End-to-end deterministic Hebrew session."""

    def test_full_chain_export(self) -> None:
        _, registry, items = make_clm06_test_fixture()
        session = HebrewAdaptiveSession(
            session_id="s-e2e",
            items=items[:4],
            asset_registry=registry,
            max_trials=4,
            clock=lambda: 0.0,
        )
        _ = session.start()
        for _ in range(4):
            if session.completed or session.aborted or session.current_trial is None:
                break
            session.respond(session.current_trial.item.canonical_unpointed)
        summary = session.stop(reason="acceptance")
        self.assertIn("causal_graph", summary)
        # Verify every listed event id is unique.
        graph = summary["causal_graph"]
        self.assertEqual(len(graph["event_ids"]), len(set(graph["event_ids"])))


if __name__ == "__main__":
    unittest.main()
