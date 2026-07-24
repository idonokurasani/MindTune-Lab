"""Canonical enum validation tests."""

from __future__ import annotations

import unittest

from mpe.enums import (
    AnswerStatus,
    DecisionStatus,
    DecisionType,
    EvaluationStatus,
    ResponseMode,
    ResponseRequirement,
    SessionStatus,
)


class EnumTests(unittest.TestCase):
    def test_valid_canonical_values_accepted(self) -> None:
        self.assertEqual(SessionStatus.validate("started"), SessionStatus.STARTED)
        self.assertEqual(ResponseRequirement.validate("required"), ResponseRequirement.REQUIRED)
        self.assertEqual(AnswerStatus.validate("correct"), AnswerStatus.CORRECT)
        self.assertEqual(EvaluationStatus.validate("completed"), EvaluationStatus.COMPLETED)
        self.assertEqual(DecisionStatus.validate("made"), DecisionStatus.MADE)
        self.assertEqual(DecisionType.validate("next_trial"), DecisionType.NEXT_TRIAL)

    def test_invalid_values_rejected(self) -> None:
        with self.assertRaises(ValueError):
            SessionStatus.validate("running")
        with self.assertRaises(ValueError):
            ResponseMode.validate("telepathy")

    def test_required_enum_cannot_be_none(self) -> None:
        with self.assertRaises(ValueError):
            DecisionStatus.validate(None)

    def test_optional_enum_allows_none(self) -> None:
        result = DecisionStatus.validate(None, required=False)
        self.assertIsNone(result)

    def test_enum_values_list(self) -> None:
        self.assertIn("started", SessionStatus.values())
        self.assertIn("completed", EvaluationStatus.values())
