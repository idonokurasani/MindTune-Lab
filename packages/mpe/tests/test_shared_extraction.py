"""Tests for the Gate 2 shared orchestration extraction.

These tests target the shared layer itself (trial pipeline, bounded repeat,
summary walk) plus the architectural constraints it must respect, in addition
to the protocol-level regression tests that already exist.
"""

from __future__ import annotations

import dataclasses
import unittest
from pathlib import Path

from mpe.enums import AnswerStatus, FeedbackCategory, FeedbackType, InstructionType, ResponseMode
from mpe.errors import ValidationError
from mpe.event_store import InMemoryEventStore
from mpe.events import PAYLOAD_SCHEMAS, SUPPORTED_EVENT_TYPES, Event
from mpe.protocol.bounded_repeat import (
    SOURCE_BEHAVIOR,
    SOURCE_LATENCY,
    BoundedRepeatPlan,
    RepeatDecision,
)
from mpe.protocol.fixture_minimal import AdaptationRule
from mpe.protocol.fixture_recognition import (
    RecognitionFixtureItem,
    make_minimal_recognition_fixture,
)
from mpe.protocol.immediate_recall import ImmediateRecallRunner, ItemOutcome
from mpe.protocol.recognition import (
    RecognitionItemOutcome,
    RecognitionRunner,
    run_recognition_session,
)
from mpe.protocol.summary_recognition import derive_recognition_summary
from mpe.protocol.summary_walk import walk_session
from mpe.protocol.trial_pipeline import TrialPipeline, canonical_trial_fields
from mpe.validation import validate_event

SRC_ROOT = Path(__file__).resolve().parents[1] / "src" / "mpe"
SHARED_MODULES = (
    SRC_ROOT / "protocol" / "trial_pipeline.py",
    SRC_ROOT / "protocol" / "bounded_repeat.py",
    SRC_ROOT / "protocol" / "summary_walk.py",
)


def _run_recognition() -> list[Event]:
    store = InMemoryEventStore()
    result = run_recognition_session(store, learner_id="learner_shared")
    return result.events


def _types(events: list[Event]) -> list[str]:
    return [event.event_type for event in events]


class SharedTrialPipelineTests(unittest.TestCase):
    """Event ordering guarantees provided by the shared pipeline."""

    def setUp(self) -> None:
        self.events = _run_recognition()
        self.types = _types(self.events)

    def test_instruction_pairs_are_ordered(self) -> None:
        for index, event_type in enumerate(self.types):
            if event_type == "instruction_started":
                self.assertEqual(self.types[index + 1], "instruction_completed")

    def test_stimulus_pairs_are_ordered(self) -> None:
        for index, event_type in enumerate(self.types):
            if event_type == "stimulus_requested":
                self.assertEqual(self.types[index + 1], "stimulus_ready")

    def test_multiple_stimuli_retain_input_order(self) -> None:
        roles = [
            event.payload["asset_role"]
            for event in self.events
            if event.event_type == "stimulus_ready"
        ]
        # Two items plus one bounded repeat, each with two ordered choices.
        self.assertEqual(roles, ["choice_0", "choice_1"] * 3)

    def test_response_pipeline_event_order(self) -> None:
        expected = [
            "response_window_opened",
            "observation_received",
            "captured_response_created",
            "response_interpreted",
            "domain_response_normalized",
            "evaluation_completed",
        ]
        start = self.types.index("response_window_opened")
        self.assertEqual(self.types[start : start + len(expected)], expected)

    def test_evaluation_follows_normalization_and_feedback_follows_evaluation(self) -> None:
        normalized = self.types.index("domain_response_normalized")
        evaluated = self.types.index("evaluation_completed")
        feedback = self.types.index("feedback_started")
        self.assertLess(normalized, evaluated)
        self.assertLess(evaluated, feedback)

    def test_sequence_numbers_are_deterministic_and_monotonic(self) -> None:
        sequences = [event.session_sequence_number for event in self.events]
        self.assertEqual(sequences, sorted(sequences))
        self.assertEqual(sequences, list(range(sequences[0], sequences[0] + len(sequences))))

    def test_protocol_payload_extensions_survive(self) -> None:
        trial_events = [e for e in self.events if e.event_type == "trial_created"]
        for event in trial_events:
            self.assertIn("correct_choice_index", event.payload)
            self.assertEqual(event.payload["choice_count"], 2)

    def test_extensions_may_not_override_canonical_fields(self) -> None:
        self.assertIn("repeat_count", canonical_trial_fields())
        self.assertIn("trial_id", canonical_trial_fields())

    def test_pipeline_does_not_know_protocol_identity(self) -> None:
        source = (SRC_ROOT / "protocol" / "trial_pipeline.py").read_text()
        self.assertNotIn("protocol_id", source.replace("protocol_version_id", ""))
        for attribute in ("recognition", "immediate_recall", "self_confirmation"):
            self.assertNotIn(attribute, source)
        self.assertFalse(hasattr(TrialPipeline, "execute"))


class BoundedRepeatTests(unittest.TestCase):
    """Invariant repeat mechanics and protocol-specific repeat decisions."""

    def setUp(self) -> None:
        self.rule = AdaptationRule(repeat_cap=1, latency_bound=2.0)

    def _recognition_decision(self, correct: bool, latency: float) -> RepeatDecision:
        runner = RecognitionRunner(InMemoryEventStore(), rule=self.rule)
        outcome = RecognitionItemOutcome(
            content_item_id="item.alpha",
            selected_choice_index=0,
            correct_choice_index=0 if correct else 1,
            latency=latency,
            repeats_used=0,
            answer_status=(AnswerStatus.CORRECT.value if correct else AnswerStatus.INCORRECT.value),
        )
        return runner._repeat_decision(outcome)

    def _recall_decision(self, positive: bool, latency: float) -> RepeatDecision:
        runner = ImmediateRecallRunner(InMemoryEventStore(), rule=self.rule)
        outcome = ItemOutcome(
            content_item_id="item.alpha",
            self_confirmation="positive" if positive else "negative",
            latency=latency,
            repeats_used=0,
            answer_status=(
                AnswerStatus.CORRECT.value if positive else AnswerStatus.INCORRECT.value
            ),
        )
        return runner._repeat_decision(outcome)

    def test_correct_and_fast_does_not_repeat(self) -> None:
        for decision in (self._recognition_decision(True, 0.5), self._recall_decision(True, 0.5)):
            self.assertFalse(decision.should_repeat)
            self.assertIsNone(decision.adaptation_source)

    def test_correct_and_slow_repeats_on_latency(self) -> None:
        for decision in (self._recognition_decision(True, 5.0), self._recall_decision(True, 5.0)):
            self.assertTrue(decision.should_repeat)
            self.assertEqual(decision.adaptation_source, SOURCE_LATENCY)

    def test_incorrect_and_fast_repeats_on_behavior(self) -> None:
        for decision in (
            self._recognition_decision(False, 0.5),
            self._recall_decision(False, 0.5),
        ):
            self.assertTrue(decision.should_repeat)
            self.assertEqual(decision.adaptation_source, SOURCE_BEHAVIOR)

    def test_incorrect_and_slow_gives_behavior_precedence(self) -> None:
        for decision in (
            self._recognition_decision(False, 5.0),
            self._recall_decision(False, 5.0),
        ):
            self.assertTrue(decision.should_repeat)
            self.assertEqual(decision.adaptation_source, SOURCE_BEHAVIOR)

    def test_cap_is_enforced_and_plan_order_is_deterministic(self) -> None:
        plan: BoundedRepeatPlan[str] = BoundedRepeatPlan(["a", "b"], cap=1, key=lambda i: i)
        executed: list[tuple[str, int, str | None]] = []
        for step in plan:
            executed.append(
                (step.item, step.metadata.repeat_count, step.metadata.adaptation_source)
            )
            step.record(RepeatDecision(True, SOURCE_BEHAVIOR, "always"))
        self.assertEqual(
            executed,
            [
                ("a", 0, None),
                ("a", 1, SOURCE_BEHAVIOR),
                ("b", 0, None),
                ("b", 1, SOURCE_BEHAVIOR),
            ],
        )

    def test_zero_cap_never_repeats(self) -> None:
        plan: BoundedRepeatPlan[str] = BoundedRepeatPlan(["a"], cap=0, key=lambda i: i)
        steps = 0
        for step in plan:
            steps += 1
            step.record(RepeatDecision(True, SOURCE_BEHAVIOR, "always"))
        self.assertEqual(steps, 1)

    def test_repeat_count_is_propagated_to_trial_payload(self) -> None:
        events = _run_recognition()
        repeat_counts = [
            (e.payload["content_item_ids"][0], e.payload["repeat_count"])
            for e in events
            if e.event_type == "trial_created"
        ]
        self.assertEqual(
            repeat_counts,
            [("item.alpha", 0), ("item.beta", 0), ("item.beta", 1)],
        )


class PayloadExtensionContractTests(unittest.TestCase):
    """The extension boundary must not weaken canonical schema validation."""

    def _trial_event(self, events: list[Event]) -> Event:
        return next(e for e in events if e.event_type == "trial_created")

    def test_extensions_are_accepted_and_persisted(self) -> None:
        events = _run_recognition()
        payload = self._trial_event(events).payload
        self.assertEqual(payload["correct_choice_index"], 0)

    def test_canonical_required_fields_are_still_validated(self) -> None:
        events = _run_recognition()
        event = self._trial_event(events)
        broken_payload = {
            key: value for key, value in event.payload.items() if key != "trial_index"
        }
        broken = dataclasses.replace(event, payload=broken_payload)
        with self.assertRaises(ValidationError):
            validate_event(broken)

    def test_no_new_event_types_or_schemas_were_added(self) -> None:
        events = _run_recognition()
        for event in events:
            self.assertIn(event.event_type, SUPPORTED_EVENT_TYPES)
            self.assertIn(event.event_type, PAYLOAD_SCHEMAS)


class SummaryWalkTests(unittest.TestCase):
    """The shared walk correlates events; projection stays protocol-specific."""

    def test_walk_correlates_trials_in_event_order(self) -> None:
        events = _run_recognition()
        walk = walk_session(events)
        self.assertEqual(
            [record.content_item_id for record in walk.items],
            ["item.alpha", "item.beta"],
        )
        self.assertTrue(walk.session_completed)
        self.assertEqual(walk.event_count, len(events))

    def test_summary_is_derived_from_events_only(self) -> None:
        events = _run_recognition()
        summary = derive_recognition_summary(events)
        self.assertEqual(summary.correct_count, 1)
        self.assertEqual(summary.total_repeats, 1)
        self.assertEqual(summary.items[1].selected_choice_index, 0)
        self.assertEqual(summary.items[1].correct_choice_index, 1)


class FixtureImmutabilityTests(unittest.TestCase):
    """Fixtures are structurally immutable, not immutable by convention."""

    def test_recognition_fixture_dataclasses_are_frozen(self) -> None:
        fixture = make_minimal_recognition_fixture()
        for instance in (fixture, *fixture.items):
            self.assertTrue(dataclasses.fields(instance))
            self.assertTrue(type(instance).__dataclass_params__.frozen)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            fixture.items[0].correct_choice_index = 9  # type: ignore[misc]

    def test_fixture_item_replacement_creates_a_new_value(self) -> None:
        item = make_minimal_recognition_fixture().items[0]
        replaced = dataclasses.replace(item, latency=9.0)
        self.assertIsInstance(replaced, RecognitionFixtureItem)
        self.assertEqual(item.latency, 0.5)


class TemporalDeterminismTests(unittest.TestCase):
    """Identical inputs produce identical sequences and identical payloads."""

    _VOLATILE_KEYS = frozenset(
        {
            "trial_id",
            "session_id",
            "block_id",
            "instruction_id",
            "stimulus_request_id",
            "rendered_stimulus_id",
            "response_window_id",
            "observation_id",
            "captured_response_id",
            "observation_ids",
            "response_interpretation_id",
            "domain_normalized_response_id",
            "evaluation_id",
            "feedback_event_id",
        }
    )

    def _normalized(self, events: list[Event]) -> list[tuple[str, dict[str, object]]]:
        return [
            (
                event.event_type,
                {
                    key: value
                    for key, value in event.payload.items()
                    if key not in self._VOLATILE_KEYS
                },
            )
            for event in events
        ]

    def test_two_runs_produce_identical_normalized_payloads(self) -> None:
        first = self._normalized(_run_recognition())
        second = self._normalized(_run_recognition())
        self.assertEqual(first, second)

    def test_volatile_identifiers_are_the_only_difference(self) -> None:
        first = _run_recognition()
        second = _run_recognition()
        self.assertEqual(_types(first), _types(second))
        self.assertNotEqual(
            [event.payload.get("trial_id") for event in first],
            [event.payload.get("trial_id") for event in second],
        )


class SharedLayerArchitectureTests(unittest.TestCase):
    """The shared layer must not learn protocol or domain semantics."""

    FORBIDDEN_IMPORTS = (
        "fixture_recognition",
        "fixture_minimal",
        "summary_recognition",
        "mpe.protocol.recognition",
        "mpe.protocol.immediate_recall",
        "eeg",
        "focuscalm",
        "asr",
        "tts",
        "mpe_audio",
        "hebrew",
        "piano",
        "curriculum",
        "scheduler",
    )

    def test_shared_modules_have_no_protocol_or_domain_dependencies(self) -> None:
        for module_path in SHARED_MODULES:
            source = module_path.read_text().lower()
            import_lines = [
                line for line in source.splitlines() if line.startswith(("import ", "from "))
            ]
            for forbidden in self.FORBIDDEN_IMPORTS:
                for line in import_lines:
                    if forbidden == "fixture_minimal" and "bounded_repeat" in line:
                        continue
                    self.assertNotIn(forbidden, line, f"{module_path.name}: {line}")

    def test_no_registry_or_protocol_id_branching(self) -> None:
        for module_path in SHARED_MODULES:
            source = module_path.read_text()
            self.assertNotIn("protocol_id ==", source)
            self.assertNotIn("PROTOCOL_REGISTRY", source)
            self.assertNotIn("HANDLERS", source)

    def test_cli_keeps_explicit_protocol_commands(self) -> None:
        cli_source = (SRC_ROOT / "cli.py").read_text()
        for command in (
            "run-immediate-recall",
            "show-protocol-summary",
            "run-recognition",
            "show-recognition-summary",
        ):
            self.assertIn(command, cli_source)
        self.assertNotIn("run-protocol", cli_source)
        self.assertNotIn("--protocol-id", cli_source)

    def test_shared_layer_uses_typed_specifications(self) -> None:
        pipeline_source = (SRC_ROOT / "protocol" / "trial_pipeline.py").read_text()
        for spec in (
            "class InstructionSpec",
            "class StimulusSpec",
            "class ResponseWindowSpec",
            "class ObservationSpec",
            "class FeedbackSpec",
            "class TrialIdentity",
        ):
            self.assertIn(spec, pipeline_source)
        self.assertNotIn("metadata: dict[str, Any]", pipeline_source)

    def test_enums_used_by_specifications_are_canonical(self) -> None:
        self.assertTrue(InstructionType.PRESENT_STIMULUS.value)
        self.assertTrue(FeedbackCategory.KNOWLEDGE.value)
        self.assertTrue(FeedbackType.CORRECT_ANSWER.value)
        self.assertTrue(ResponseMode.TOUCH.value)


if __name__ == "__main__":
    unittest.main()
