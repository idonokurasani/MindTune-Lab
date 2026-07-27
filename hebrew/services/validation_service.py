"""High-level validation service."""

from __future__ import annotations

from ..models import ValidationResult
from ..validation import validate_user_answer


class ValidationService:
    """Validate user Hebrew answers and classify errors."""

    def validate(
        self,
        submitted: str,
        expected: str,
        accepted_variants: list[str] | None = None,
    ) -> ValidationResult:
        return validate_user_answer(submitted, expected, accepted_variants)
