"""Conservative vocal-shva diagnosis.

Do not treat this as a general automatic vocal-shva detector.  It records
explicit decisions, manual overrides, and confidence levels, and defaults to
'ambiguous' whenever the evidence is unclear.
"""

from __future__ import annotations

import re

from .models import ShvaDiagnosis
from .normalization import decompose


def has_shva(text: str) -> bool:
    """True if the vocalized text contains a sheva point."""
    return "\u05b0" in decompose(text)


def classify_shva(
    text: str,
    phonikud_vocal_shva: bool | None = None,
    manual_override: bool | None = None,
    manual_source: str = "",
) -> ShvaDiagnosis:
    """Return a conservative shva diagnosis for a word.

    Priority:
      1. manual override
      2. explicit phonikud prediction (treated as low-confidence)
      3. 'ambiguous' default
    """
    if not has_shva(text):
        return ShvaDiagnosis(
            shva_status="not_applicable",
            shva_source="",
            shva_confidence=1.0,
            shva_reason="no sheva point in form",
        )

    if manual_override is not None:
        status = "vocal" if manual_override else "silent"
        return ShvaDiagnosis(
            shva_status=status,
            shva_source=manual_source or "manual_override",
            shva_confidence=0.95,
            shva_reason="manual override",
        )

    if phonikud_vocal_shva is not None:
        status = "vocal" if phonikud_vocal_shva else "silent"
        return ShvaDiagnosis(
            shva_status=status,
            shva_source="phonikud",
            shva_confidence=0.5,
            shva_reason="Phonikud prediction only; not authoritative",
        )

    return ShvaDiagnosis(
        shva_status="ambiguous",
        shva_source="",
        shva_confidence=1.0,
        shva_reason="no explicit shva information; conservative default",
    )


def find_ambiguous_shva_forms(forms: list) -> list[tuple[str, str]]:
    """Return (form_key, surface) for every form with ambiguous shva."""
    ambiguous: list[tuple[str, str]] = []
    for form in forms:
        if hasattr(form, "shva") and form.shva.shva_status == "ambiguous":
            ambiguous.append(
                (getattr(form, "form_key", ""), getattr(form, "surface_vocalized", str(form)))
            )
    return ambiguous
