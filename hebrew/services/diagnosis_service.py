"""Learner-answer diagnosis service."""

from __future__ import annotations

from ..diagnosis import diagnose_answer
from ..models import ValidationResult, VerbForm


class DiagnosisService:
    """Diagnose learner answers against gold forms."""

    def diagnose(
        self,
        submitted: str,
        expected_form: VerbForm,
        accepted_variants: list[str] | None = None,
        known_forms: dict[str, VerbForm] | None = None,
    ) -> ValidationResult:
        return diagnose_answer(submitted, expected_form, accepted_variants, known_forms)
