"""Provider mock contract tests."""

from __future__ import annotations

import unittest

from mpe.enums import AnswerStatus, EvaluationStatus
from mpe.errors import ProviderFailureError, ProviderTimeoutError
from mpe.providers import (
    ContentItem,
    MockDomainNormalizer,
    MockEvaluator,
    MockKeyboardObservationProvider,
    MockRenderer,
    MockResponseInterpreter,
    MockScheduler,
    SchedulingContext,
    TrialContext,
)


class ProviderTests(unittest.TestCase):
    def test_renderer_deterministic_output(self) -> None:
        renderer = MockRenderer()
        request = {
            "stimulus_request_id": "sr",
            "trial_id": "t",
            "content_item_id": "c",
        }
        result = renderer.render(request)
        self.assertEqual(result["stimulus_request_id"], "sr")
        self.assertEqual(result["renderer_id"], "mock_renderer")
        self.assertTrue(result["media_handle"].startswith("media://mock/c"))

    def test_renderer_failure(self) -> None:
        renderer = MockRenderer()
        renderer.failing = True
        with self.assertRaises(ProviderFailureError):
            renderer.render({"stimulus_request_id": "sr", "trial_id": "t", "content_item_id": "c"})

    def test_keyboard_observation_deterministic(self) -> None:
        provider = MockKeyboardObservationProvider()
        provider.inject("typed answer")
        observations = provider.poll()
        self.assertEqual(len(observations), 1)
        self.assertEqual(observations[0]["payload"], "typed answer")
        self.assertEqual(observations[0]["observation_type"], "typed_input")

    def test_keyboard_timeout(self) -> None:
        provider = MockKeyboardObservationProvider()
        provider.set_timeout(True)
        with self.assertRaises(ProviderTimeoutError):
            provider.poll()

    def test_interpreter_typed_output(self) -> None:
        interpreter = MockResponseInterpreter()
        result = interpreter.interpret({
            "captured_response_id": "cr",
            "response_window_id": "rw",
            "response_mode": "typed",
            "captured_payload": "hello",
            "captured_at": 1.0,
        })
        self.assertEqual(result["interpreted_payload"], "hello")
        self.assertEqual(result["interpretation_type"], "typed_text")

    def test_normalizer_passes_through(self) -> None:
        normalizer = MockDomainNormalizer()
        interpretation = {
            "response_interpretation_id": "ri",
            "response_window_id": "rw",
            "interpreted_payload": "hello",
            "component_timestamp": 1.0,
        }
        result = normalizer.normalize(interpretation)
        self.assertEqual(result["normalized_payload"], "hello")
        self.assertEqual(result["normalizer_id"], "mock_normalizer")

    def test_evaluator_correct_when_matching(self) -> None:
        evaluator = MockEvaluator()
        content = ContentItem(
            content_item_id="c",
            provider_id="p",
            provider_version="1.0.0",
            content_type="mock_word",
            checksum="x",
            surface_form="hello",
            normalized_form="hello",
        )
        result = evaluator.evaluate(
            {"normalized_payload": "hello"},
            content,
            TrialContext("t", "s", "typed", "pv"),
        )
        self.assertEqual(result["answer_status"], AnswerStatus.CORRECT.value)
        self.assertEqual(result["evaluation_status"], EvaluationStatus.COMPLETED.value)

    def test_evaluator_incorrect_when_mismatch(self) -> None:
        evaluator = MockEvaluator()
        content = ContentItem(
            content_item_id="c",
            provider_id="p",
            provider_version="1.0.0",
            content_type="mock_word",
            checksum="x",
            surface_form="hello",
            normalized_form="hello",
        )
        result = evaluator.evaluate(
            {"normalized_payload": "world"},
            content,
            TrialContext("t", "s", "typed", "pv"),
        )
        self.assertEqual(result["answer_status"], AnswerStatus.INCORRECT.value)

    def test_evaluator_abstention(self) -> None:
        evaluator = MockEvaluator()
        evaluator.abstain = True
        content = ContentItem(
            content_item_id="c",
            provider_id="p",
            provider_version="1.0.0",
            content_type="mock_word",
            checksum="x",
            surface_form="hello",
            normalized_form="hello",
        )
        result = evaluator.evaluate(
            {"normalized_payload": "hello"},
            content,
            TrialContext("t", "s", "typed", "pv"),
        )
        self.assertEqual(result["evaluation_status"], EvaluationStatus.ABSTAINED.value)

    def test_scheduler_single_item_then_end(self) -> None:
        scheduler = MockScheduler()
        first = scheduler.select_next(SchedulingContext(
            protocol_version_id="pv",
            session_id="s",
            trial_index=1,
            protocol_policy={"item_sequence": ["i1"]},
        ))
        self.assertEqual(first["decision_type"], "next_trial")
        self.assertEqual(first["selected_item_ids"], ["i1"])

        second = scheduler.select_next(SchedulingContext(
            protocol_version_id="pv",
            session_id="s",
            trial_index=2,
            protocol_policy={"item_sequence": ["i1"]},
        ))
        self.assertEqual(second["decision_type"], "session_end")
        self.assertEqual(second["selected_item_ids"], [])

    def test_scheduler_failure(self) -> None:
        scheduler = MockScheduler()
        scheduler.fail = True
        with self.assertRaises(ProviderFailureError):
            scheduler.select_next(SchedulingContext(
                protocol_version_id="pv",
                session_id="s",
                trial_index=1,
                protocol_policy={"item_sequence": ["i1"]},
            ))
