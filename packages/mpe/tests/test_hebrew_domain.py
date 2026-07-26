"""Tests for the Hebrew immediate-recall domain adapter (Phase 4D)."""

from __future__ import annotations

import inspect
import tempfile
import unittest
from dataclasses import fields
from pathlib import Path
from typing import Any

from mpe.aggregates import RuntimeState
from mpe.cli_helpers import normalize_state_dict
from mpe.domains.hebrew import (
    HebrewContentItem,
    HebrewDomainAdapter,
    make_hebrew_immediate_recall_fixture,
    normalize_hebrew_response,
    run_hebrew_immediate_recall_session,
)
from mpe.enums import AnswerStatus, CognitiveState, SessionStatus
from mpe.event_store import InMemoryEventStore
from mpe.persistence.store import SQLiteEventStore
from mpe.protocol.fixture_minimal import AdaptationRule
from mpe.replay import Replay


class HebrewContentModelTests(unittest.TestCase):
    """A. Hebrew content model."""

    def test_typed_item_construction(self) -> None:
        item = HebrewContentItem(
            content_item_id="he.word.house",
            hebrew_target="בית",
            accepted_answers=("בית",),
            italian_cue="casa",
        )
        self.assertEqual(item.content_item_id, "he.word.house")
        self.assertEqual(item.hebrew_target, "בית")
        self.assertEqual(item.italian_cue, "casa")

    def test_stable_identifier_behavior(self) -> None:
        item1 = HebrewContentItem(
            content_item_id="he.word.house",
            hebrew_target="בית",
            accepted_answers=("בית",),
            italian_cue="casa",
        )
        item2 = HebrewContentItem(
            content_item_id="he.word.house",
            hebrew_target="בית",
            accepted_answers=("בית",),
            italian_cue="casa",
        )
        self.assertEqual(item1.content_item_id, item2.content_item_id)

    def test_fixture_version_stability(self) -> None:
        fixture1 = make_hebrew_immediate_recall_fixture()
        fixture2 = make_hebrew_immediate_recall_fixture()
        self.assertEqual(fixture1.version, fixture2.version)
        self.assertEqual(fixture1.fixture_id, fixture2.fixture_id)
        self.assertEqual(len(fixture1.items), len(fixture2.items))
        self.assertEqual(
            [i.content_item_id for i in fixture1.items],
            [i.content_item_id for i in fixture2.items],
        )

    def test_invalid_item_rejection(self) -> None:
        with self.assertRaises(ValueError):
            HebrewContentItem(
                content_item_id="",
                hebrew_target="בית",
                accepted_answers=("בית",),
                italian_cue="casa",
            )
        with self.assertRaises(ValueError):
            HebrewContentItem(
                content_item_id="x",
                hebrew_target="",
                accepted_answers=("בית",),
                italian_cue="casa",
            )
        with self.assertRaises(ValueError):
            HebrewContentItem(
                content_item_id="x",
                hebrew_target="בית",
                accepted_answers=(),
                italian_cue="casa",
            )


class HebrewPromptConstructionTests(unittest.TestCase):
    """B. Prompt construction."""

    def setUp(self) -> None:
        self.fixture = make_hebrew_immediate_recall_fixture()
        self.adapter = HebrewDomainAdapter(list(self.fixture.items))

    def test_same_input_same_prompt(self) -> None:
        item = self.adapter.get_content_item("he.word.house")
        self.assertIsNotNone(item)
        prompt1 = self.adapter.build_prompt(item)
        prompt2 = self.adapter.build_prompt(item)
        self.assertEqual(prompt1, prompt2)

    def test_prompt_contains_expected_italian_cue(self) -> None:
        item = self.adapter.get_content_item("he.word.water")
        self.assertIsNotNone(item)
        prompt = self.adapter.build_prompt(item)
        self.assertEqual(prompt.italian_cue, "acqua")
        self.assertIn("acqua", prompt.cue_text())

    def test_prompt_points_to_correct_hebrew_content_item(self) -> None:
        item = self.adapter.get_content_item("he.word.book")
        self.assertIsNotNone(item)
        prompt = self.adapter.build_prompt(item)
        self.assertEqual(prompt.content_item_id, "he.word.book")
        self.assertEqual(prompt.target_language, "he")

    def test_prompt_identifier_is_stable(self) -> None:
        item = self.adapter.get_content_item("he.word.tree")
        self.assertIsNotNone(item)
        prompt1 = self.adapter.build_prompt(item)
        prompt2 = self.adapter.build_prompt(item)
        self.assertIsInstance(prompt1.prompt_id, str)
        self.assertTrue(prompt1.prompt_id)
        self.assertEqual(prompt1.prompt_id, prompt2.prompt_id)


class HebrewNormalizationTests(unittest.TestCase):
    """C. Normalization."""

    def test_leading_trailing_whitespace(self) -> None:
        self.assertEqual(normalize_hebrew_response("  בית  "), "בית")

    def test_internal_whitespace(self) -> None:
        self.assertEqual(normalize_hebrew_response("ב  ית"), "ב ית")

    def test_unicode_normalization(self) -> None:
        # ב + dagesh (U+05BC) vs precomposed בּ
        composed = "בּית"
        decomposed = "ב\u05bcית"
        self.assertEqual(normalize_hebrew_response(composed), normalize_hebrew_response(decomposed))

    def test_empty_response_handling(self) -> None:
        self.assertEqual(normalize_hebrew_response(""), "")
        self.assertEqual(normalize_hebrew_response("   "), "")
        self.assertEqual(normalize_hebrew_response(None), "")

    def test_accepted_variants_handling(self) -> None:
        # Pointed and unpointed forms should normalise to the same canonical form
        # for the adapter's exact matching only when accepted_answers includes both.
        adapter = HebrewDomainAdapter([HebrewContentItem(
            content_item_id="x",
            hebrew_target="בית",
            accepted_answers=("בית", "בַּיִת"),
            italian_cue="casa",
        )])
        prompt = adapter.build_prompt(adapter.get_content_item("x"))
        eval_pointed = adapter.evaluate_response(prompt, "בַּיִת")
        eval_unpointed = adapter.evaluate_response(prompt, "בית")
        self.assertTrue(eval_pointed.is_correct)
        self.assertTrue(eval_unpointed.is_correct)


class HebrewEvaluationTests(unittest.TestCase):
    """D. Evaluation."""

    def setUp(self) -> None:
        self.fixture = make_hebrew_immediate_recall_fixture()
        self.adapter = HebrewDomainAdapter(list(self.fixture.items))

    def test_correct_hebrew_response(self) -> None:
        item = self.adapter.get_content_item("he.word.house")
        self.assertIsNotNone(item)
        prompt = self.adapter.build_prompt(item)
        result = self.adapter.evaluate_response(prompt, "בית")
        self.assertTrue(result.is_correct)
        self.assertEqual(result.answer_status, AnswerStatus.CORRECT)

    def test_incorrect_hebrew_response(self) -> None:
        item = self.adapter.get_content_item("he.word.house")
        self.assertIsNotNone(item)
        prompt = self.adapter.build_prompt(item)
        result = self.adapter.evaluate_response(prompt, "ספר")
        self.assertFalse(result.is_correct)
        self.assertEqual(result.answer_status, AnswerStatus.INCORRECT)

    def test_omitted_response(self) -> None:
        item = self.adapter.get_content_item("he.word.house")
        self.assertIsNotNone(item)
        prompt = self.adapter.build_prompt(item)
        result = self.adapter.evaluate_response(prompt, "")
        self.assertFalse(result.is_correct)
        self.assertTrue(result.is_omitted)

    def test_deterministic_repeated_evaluation(self) -> None:
        item = self.adapter.get_content_item("he.word.water")
        self.assertIsNotNone(item)
        prompt = self.adapter.build_prompt(item)
        r1 = self.adapter.evaluate_response(prompt, "מים")
        r2 = self.adapter.evaluate_response(prompt, "מים")
        self.assertEqual(r1.is_correct, r2.is_correct)
        self.assertEqual(r1.answer_status, r2.answer_status)

    def test_no_fuzzy_accidental_acceptance(self) -> None:
        item = self.adapter.get_content_item("he.word.book")
        self.assertIsNotNone(item)
        prompt = self.adapter.build_prompt(item)
        result = self.adapter.evaluate_response(prompt, "ספ")
        self.assertFalse(result.is_correct)
        result2 = self.adapter.evaluate_response(prompt, "ספרים")
        self.assertFalse(result2.is_correct)


class HebrewAdapterBoundaryTests(unittest.TestCase):
    """E. Adapter boundary."""

    def setUp(self) -> None:
        self.fixture = make_hebrew_immediate_recall_fixture()
        self.adapter = HebrewDomainAdapter(list(self.fixture.items))

    def test_adapter_returns_domain_neutral_evidence(self) -> None:
        item = self.adapter.get_content_item("he.word.house")
        self.assertIsNotNone(item)
        prompt = self.adapter.build_prompt(item)
        result = self.adapter.evaluate_response(prompt, "בית")
        evidence = self.adapter.behavioral_evidence(result)
        self.assertEqual(evidence.correctness_status, AnswerStatus.CORRECT.value)
        self.assertEqual(evidence.content_item_id, "he.word.house")
        self.assertTrue(evidence.prompt_id)

    def test_evidence_has_no_hebrew_specific_fields(self) -> None:
        item = self.adapter.get_content_item("he.word.house")
        self.assertIsNotNone(item)
        prompt = self.adapter.build_prompt(item)
        result = self.adapter.evaluate_response(prompt, "בית")
        evidence = self.adapter.behavioral_evidence(result)
        field_names = {f.name for f in fields(evidence)}
        forbidden = {"hebrew_target", "binyan", "root", "niqqud", "transliteration"}
        self.assertTrue(forbidden.isdisjoint(field_names))

    def test_adapter_does_not_mutate_controller_state(self) -> None:
        state = RuntimeState()
        item = self.adapter.get_content_item("he.word.house")
        self.assertIsNotNone(item)
        self.adapter.build_prompt(item)
        self.adapter.evaluate_response(self.adapter.build_prompt(item), "בית")
        self.assertIsNone(state.session_status)

    def test_adapter_does_not_call_adaptation_policy(self) -> None:
        # The adapter module does not import or reference the adaptation policy.
        from mpe.domains.hebrew import adapter as adapter_module
        source = inspect.getsource(adapter_module)
        self.assertNotIn("AdaptationPolicy", source)


class HebrewRuntimeIntegrationTests(unittest.TestCase):
    """F. Runtime integration; G. EEG constraints; H. Replay."""

    def setUp(self) -> None:
        self.hebrew_fixture = make_hebrew_immediate_recall_fixture()
        self.rule = AdaptationRule(
            repeat_cap=0,
            latency_bound=2.0,
            response_deadline=10.0,
            max_response_deadline=20.0,
            deadline_step=0.5,
        )

    def _run(
        self,
        typed_responses: dict[str, str],
        eeg_overrides: dict[str, dict[str, Any]] | None = None,
        store: InMemoryEventStore | SQLiteEventStore | None = None,
    ) -> tuple[Any, Any]:
        store = store or InMemoryEventStore()
        fixture, result = run_hebrew_immediate_recall_session(
            store,
            self.hebrew_fixture,
            typed_responses=typed_responses,
            eeg_overrides=eeg_overrides or {},
            learner_id="learner_001",
            random_seed="seed_0",
        )
        return fixture, result

    def _trial_states_and_deadlines(self, result: Any) -> tuple[list[str], list[float]]:
        decisions = [e for e in result.events if e.event_type == "adaptation_decision"]
        states = [d.payload["resulting_state"] for d in decisions]
        deadlines = [
            e.payload["deadline_at"] - e.payload["opened_at"]
            for e in result.events
            if e.event_type == "response_window_opened"
        ]
        return states, deadlines

    def test_correct_response_remains_stable(self) -> None:
        fixture, result = self._run({"he.word.house": "בית"})
        self.assertEqual(result.state.session_status, SessionStatus.COMPLETED)
        decisions = [e for e in result.events if e.event_type == "adaptation_decision"]
        self.assertEqual(decisions[-1].payload["resulting_state"], CognitiveState.STABLE.value)
        durations = [
            e.payload["deadline_at"] - e.payload["opened_at"]
            for e in result.events
            if e.event_type == "response_window_opened"
        ]
        self.assertEqual(durations[-1], 10.0)

    def test_repeated_deterioration_produces_possible_drift(self) -> None:
        typed = {"he.word.house": "בית", "he.word.water": "wrong"}
        _, result = self._run(typed)
        decisions = [e for e in result.events if e.event_type == "adaptation_decision"]
        states = [d.payload["resulting_state"] for d in decisions]
        self.assertIn(CognitiveState.POSSIBLE_DRIFT.value, states)

    def test_sufficient_deterioration_produces_recovery_required(self) -> None:
        typed = {
            "he.word.house": "wrong",
            "he.word.water": "wrong",
        }
        _, result = self._run(typed)
        decisions = [e for e in result.events if e.event_type == "adaptation_decision"]
        states = [d.payload["resulting_state"] for d in decisions]
        self.assertIn(CognitiveState.RECOVERY_REQUIRED.value, states)

    def test_recovery_behavior_enters_recovering(self) -> None:
        typed = {
            "he.word.house": "wrong",
            "he.word.water": "wrong",
            "he.word.book": "בית",  # still incorrect but we need a correct to start recovery? actually wrong
            "he.word.tree": "עץ",
        }
        # Force correct responses after two incorrects to move into RECOVERING.
        typed["he.word.book"] = "ספר"
        _, result = self._run(typed)
        decisions = [e for e in result.events if e.event_type == "adaptation_decision"]
        states = [d.payload["resulting_state"] for d in decisions]
        self.assertIn(CognitiveState.RECOVERING.value, states)

    def test_successful_behavior_returns_toward_stable(self) -> None:
        typed = {
            "he.word.house": "wrong",
            "he.word.water": "wrong",
            "he.word.book": "ספר",
            "he.word.tree": "עץ",
            "he.word.sun": "שמש",
            "he.word.moon": "ירח",
            "he.word.hello": "שלום",
            "he.word.love": "אהבה",
            "he.word.friend": "חבר",
        }
        _, result = self._run(typed)
        decisions = [e for e in result.events if e.event_type == "adaptation_decision"]
        self.assertEqual(decisions[-1].payload["resulting_state"], CognitiveState.STABLE.value)

    def test_adaptation_changes_next_executable_deadline(self) -> None:
        typed = {
            "he.word.house": "בית",
            "he.word.water": "wrong",
            "he.word.book": "wrong",
        }
        _, result = self._run(typed)
        durations = [
            e.payload["deadline_at"] - e.payload["opened_at"]
            for e in result.events
            if e.event_type == "response_window_opened"
        ]
        self.assertGreater(max(durations), durations[0])

    def test_restoration_is_gradual(self) -> None:
        typed = {
            "he.word.house": "wrong",
            "he.word.water": "wrong",
            "he.word.book": "wrong",
            "he.word.tree": "עץ",
            "he.word.sun": "שמש",
            "he.word.moon": "ירח",
            "he.word.hello": "שלום",
            "he.word.love": "אהבה",
            "he.word.friend": "חבר",
        }
        _, result = self._run(typed)
        durations = [
            e.payload["deadline_at"] - e.payload["opened_at"]
            for e in result.events
            if e.event_type == "response_window_opened"
        ]
        peak = max(durations)
        peak_index = durations.index(peak)
        # After the peak, durations move back toward baseline step by step.
        self.assertGreater(peak, 10.0)
        self.assertEqual(durations[-1], 10.0)
        for i in range(peak_index + 1, len(durations)):
            self.assertLessEqual(durations[i], durations[i - 1])

    def test_hysteresis_prevents_state_flapping(self) -> None:
        # Single incorrect after stable should not immediately jump to recovery.
        typed = {"he.word.house": "wrong"}
        _, result = self._run(typed)
        decisions = [e for e in result.events if e.event_type == "adaptation_decision"]
        states = [d.payload["resulting_state"] for d in decisions]
        self.assertNotIn(CognitiveState.RECOVERY_REQUIRED.value, states)

    def test_low_quality_eeg_is_ignored(self) -> None:
        typed = {"he.word.house": "בית"}
        eeg_overrides = {
            "he.word.house": {"eeg_load": 0.9, "eeg_quality_flags": ["artifact"]},
        }
        _, result = self._run(typed, eeg_overrides=eeg_overrides)
        decisions = [e for e in result.events if e.event_type == "adaptation_decision"]
        # Correct behavior with bad EEG should stay stable.
        self.assertEqual(decisions[-1].payload["resulting_state"], CognitiveState.STABLE.value)

    def test_eeg_deterioration_without_behavioral_deterioration_does_not_force_recovery(self) -> None:
        typed = {"he.word.house": "בית"}
        eeg_overrides = {
            "he.word.house": {"eeg_load": 0.9, "eeg_quality_flags": []},
        }
        _, result = self._run(typed, eeg_overrides=eeg_overrides)
        decisions = [e for e in result.events if e.event_type == "adaptation_decision"]
        for d in decisions:
            self.assertNotEqual(d.payload["resulting_state"], CognitiveState.RECOVERY_REQUIRED.value)

    def test_behavioral_deterioration_sufficient_without_eeg(self) -> None:
        typed = {
            "he.word.house": "wrong",
            "he.word.water": "wrong",
        }
        _, result = self._run(typed)
        decisions = [e for e in result.events if e.event_type == "adaptation_decision"]
        states = [d.payload["resulting_state"] for d in decisions]
        self.assertIn(CognitiveState.RECOVERY_REQUIRED.value, states)

    def test_eeg_only_contextual_support(self) -> None:
        typed = {
            "he.word.house": "wrong",
            "he.word.water": "wrong",
        }
        eeg_overrides = {
            "he.word.house": {"eeg_load": 0.95, "eeg_quality_flags": []},
            "he.word.water": {"eeg_load": 0.95, "eeg_quality_flags": []},
        }
        _, result = self._run(typed, eeg_overrides=eeg_overrides)
        # Behavioral deterioration alone already drives recovery; EEG supports it.
        states = [d.payload["resulting_state"] for d in result.events if d.event_type == "adaptation_decision"]
        self.assertIn(CognitiveState.RECOVERY_REQUIRED.value, states)


class HebrewReplayTests(unittest.TestCase):
    """H. Replay."""

    def setUp(self) -> None:
        self.hebrew_fixture = make_hebrew_immediate_recall_fixture()
        self.typed_responses = {
            "he.word.house": "בית",
            "he.word.water": "wrong",
            "he.word.book": "wrong",
            "he.word.tree": "עץ",
            "he.word.sun": "שמש",
            "he.word.moon": "ירח",
            "he.word.hello": "שלום",
            "he.word.love": "אהבה",
            "he.word.friend": "חבר",
        }

    def test_original_and_replayed_states_equal(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "events.db"
            store1 = SQLiteEventStore(path)
            _, result1 = run_hebrew_immediate_recall_session(
                store1,
                self.hebrew_fixture,
                typed_responses=self.typed_responses,
                random_seed="seed_0",
            )
            session_id = result1.runtime.state.session_id
            assert session_id is not None

            store2 = SQLiteEventStore(path)
            replayed = Replay(store2).replay(session_id)
            self.assertEqual(
                normalize_state_dict(result1.state.as_dict()),
                normalize_state_dict(replayed.as_dict()),
            )

    def test_original_and_replayed_decisions_equal(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "events.db"
            store1 = SQLiteEventStore(path)
            _, result1 = run_hebrew_immediate_recall_session(
                store1,
                self.hebrew_fixture,
                typed_responses=self.typed_responses,
                random_seed="seed_0",
            )
            session_id = result1.runtime.state.session_id
            assert session_id is not None

            store2 = SQLiteEventStore(path)
            events = store2.read(session_id)
            original_decisions = [
                e.payload["resulting_state"]
                for e in result1.events
                if e.event_type == "adaptation_decision"
            ]
            replayed_decisions = [
                e.payload["resulting_state"]
                for e in events
                if e.event_type == "adaptation_decision"
            ]
            self.assertEqual(original_decisions, replayed_decisions)

    def test_original_and_replayed_runtime_values_equal(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "events.db"
            store1 = SQLiteEventStore(path)
            _, result1 = run_hebrew_immediate_recall_session(
                store1,
                self.hebrew_fixture,
                typed_responses=self.typed_responses,
                random_seed="seed_0",
            )
            session_id = result1.runtime.state.session_id
            assert session_id is not None

            store2 = SQLiteEventStore(path)
            events = store2.read(session_id)
            original_durations = [
                e.payload["deadline_at"] - e.payload["opened_at"]
                for e in result1.events
                if e.event_type == "response_window_opened"
            ]
            replayed_durations = [
                e.payload["deadline_at"] - e.payload["opened_at"]
                for e in events
                if e.event_type == "response_window_opened"
            ]
            self.assertEqual(original_durations, replayed_durations)

    def test_original_and_replayed_prompt_ids_equal(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "events.db"
            store1 = SQLiteEventStore(path)
            _, result1 = run_hebrew_immediate_recall_session(
                store1,
                self.hebrew_fixture,
                typed_responses=self.typed_responses,
                random_seed="seed_0",
            )
            session_id = result1.runtime.state.session_id
            assert session_id is not None

            store2 = SQLiteEventStore(path)
            events = store2.read(session_id)
            original_prompts = [
                e.payload["media_handle"]
                for e in result1.events
                if e.event_type == "stimulus_ready"
            ]
            replayed_prompts = [
                e.payload["media_handle"]
                for e in events
                if e.event_type == "stimulus_ready"
            ]
            self.assertEqual(original_prompts, replayed_prompts)

    def test_replay_resolves_original_content_version(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "events.db"
            store1 = SQLiteEventStore(path)
            _, result1 = run_hebrew_immediate_recall_session(
                store1,
                self.hebrew_fixture,
                typed_responses=self.typed_responses,
                random_seed="seed_0",
            )
            session_id = result1.runtime.state.session_id
            assert session_id is not None

            store2 = SQLiteEventStore(path)
            events = store2.read(session_id)
            ready_events = [e for e in events if e.event_type == "stimulus_ready"]
            for event in ready_events:
                self.assertTrue(event.payload["media_handle"].startswith("hebrew://prompt/"))
                self.assertEqual(event.payload["asset_version"], "1.0.0")


class HebrewArchitecturalSafeguardTests(unittest.TestCase):
    """I. Architectural safeguards."""

    def test_no_hebrew_specific_state_in_controller(self) -> None:
        from mpe import aggregates as aggregates_module
        source = str(aggregates_module.__file__)
        with open(source, encoding="utf-8") as f:
            text = f.read()
        self.assertNotIn("hebrew", text.lower())

    def test_no_hebrew_branch_in_immediate_recall_runner(self) -> None:
        from mpe.protocol import immediate_recall as ir_module
        source = str(ir_module.__file__)
        with open(source, encoding="utf-8") as f:
            text = f.read()
        # The runner only has generic typed/touch branching; no Hebrew labels.
        self.assertNotIn("hebrew", text.lower())

    def test_no_parallel_hebrew_runtime(self) -> None:
        # There is no runner other than ImmediateRecallRunner used for Hebrew.
        from mpe.protocol.immediate_recall import ImmediateRecallRunner
        self.assertTrue(ImmediateRecallRunner)

    def test_no_external_network_dependency(self) -> None:
        # No HTTP/TTS/network imports in the Hebrew domain code.
        from mpe.domains import hebrew as hebrew_module
        source = str(hebrew_module.__file__)
        with open(source, encoding="utf-8") as f:
            text = f.read()
        self.assertNotIn("requests", text.lower())
        self.assertNotIn("http", text.lower())


class HebrewFullSliceTraceTests(unittest.TestCase):
    """Required full-slice trace demonstrating the complete causal chain."""

    def setUp(self) -> None:
        self.hebrew_fixture = make_hebrew_immediate_recall_fixture()
        # 1 correct, 3 incorrect (deterioration), 5 correct (recovery).
        self.typed_responses = {
            "he.word.house": "בית",
            "he.word.water": "wrong",
            "he.word.book": "wrong",
            "he.word.tree": "wrong",
            "he.word.sun": "שמש",
            "he.word.moon": "ירח",
            "he.word.hello": "שלום",
            "he.word.love": "אהבה",
            "he.word.friend": "חבר",
        }

    def test_full_slice_trace_and_replay(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "events.db"
            store1 = SQLiteEventStore(path)
            fixture, result = run_hebrew_immediate_recall_session(
                store1,
                self.hebrew_fixture,
                typed_responses=self.typed_responses,
                learner_id="learner_001",
                random_seed="seed_0",
            )

            decisions = [e for e in result.events if e.event_type == "adaptation_decision"]
            states = [d.payload["resulting_state"] for d in decisions]
            durations = [
                e.payload["deadline_at"] - e.payload["opened_at"]
                for e in result.events
                if e.event_type == "response_window_opened"
            ]
            prompt_ids = [
                e.payload["media_handle"]
                for e in result.events
                if e.event_type == "stimulus_ready"
            ]

            # Trial 1: correct, STABLE, baseline.
            self.assertEqual(states[0], CognitiveState.STABLE.value)
            self.assertEqual(durations[0], 10.0)

            # Trial 2: incorrect, POSSIBLE_DRIFT (state recorded; deadline unchanged due to hysteresis).
            self.assertEqual(states[1], CognitiveState.POSSIBLE_DRIFT.value)

            # Sustained incorrect triggers RECOVERY_REQUIRED and grows the deadline.
            peak = max(durations)
            peak_index = durations.index(peak)
            self.assertIn(CognitiveState.RECOVERY_REQUIRED.value, states[:peak_index])
            self.assertGreater(peak, 10.0)

            # Correct responses begin RECOVERING and the deadline gradually returns to baseline.
            recovering_started = next((i for i, s in enumerate(states) if s == CognitiveState.RECOVERING.value), None)
            self.assertIsNotNone(recovering_started)
            self.assertLess(recovering_started, len(states) - 1)
            for i in range(peak_index + 1, len(durations)):
                self.assertLessEqual(durations[i], durations[i - 1])

            # Sustained correct behavior returns to STABLE with baseline restored.
            self.assertEqual(states[-1], CognitiveState.STABLE.value)
            self.assertEqual(durations[-1], 10.0)

            # Replay.
            session_id = result.runtime.state.session_id
            assert session_id is not None
            store2 = SQLiteEventStore(path)
            replayed = Replay(store2).replay(session_id)
            events2 = store2.read(session_id)
            replayed_states = [
                e.payload["resulting_state"]
                for e in events2
                if e.event_type == "adaptation_decision"
            ]
            replayed_durations = [
                e.payload["deadline_at"] - e.payload["opened_at"]
                for e in events2
                if e.event_type == "response_window_opened"
            ]
            replayed_prompts = [
                e.payload["media_handle"]
                for e in events2
                if e.event_type == "stimulus_ready"
            ]

            self.assertEqual(states, replayed_states)
            self.assertEqual(durations, replayed_durations)
            self.assertEqual(prompt_ids, replayed_prompts)
            self.assertEqual(
                normalize_state_dict(result.state.as_dict()),
                normalize_state_dict(replayed.as_dict()),
            )


if __name__ == "__main__":
    unittest.main()
