"""Answer validation and error diagnosis."""
from __future__ import annotations

from .models import ValidationResult
from .normalization import strip_niqqud


def validate_user_answer(
    submitted_form: str,
    expected_form: str,
    accepted_variants: list[str] | None = None,
) -> ValidationResult:
    """Compare a user-submitted Hebrew form against the expected form."""
    variants = accepted_variants or []
    submitted = submitted_form.strip()
    expected = expected_form.strip()
    submitted_plain = strip_niqqud(submitted)
    expected_plain = strip_niqqud(expected)

    result = ValidationResult(
        submitted=submitted,
        expected=expected,
        accepted_variants=variants,
    )

    if submitted == expected:
        result.status = "fully_correct"
        result.score = 1.0
        return result

    if submitted_plain == expected_plain:
        if submitted == submitted_plain and expected != expected_plain:
            result.status = "niqqud-only error"
        else:
            result.status = "spelling-only error"
        result.score = 0.8
        result.details.append("plain forms match but vocalization differs")
        return result

    if any(submitted == v or submitted_plain == strip_niqqud(v) for v in variants):
        result.status = "valid alternative form"
        result.score = 1.0
        return result

    # More advanced morphology diagnosis would require paradigm context.
    result.status = "spelling/vocalization mismatch"
    result.score = 0.0
    result.details.append("submitted form does not match expected or accepted variants")
    return result
