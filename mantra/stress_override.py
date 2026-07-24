"""Deterministic stress / vocal-shva correction layer.

The override registry is the authoritative place for manual pronunciation
adjustments. It can be loaded from the previous audit JSON or from any future
override file with the same schema.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .models import CorrectionEntry
from .utils import load_json, stress_from_phonemes


@dataclass
class OverrideRule:
    verb: str
    form_key: str
    hebrew_with_niqqud: str
    corrected_phonemes: str
    corrected_stress: int
    corrected_vocal_shva: bool
    raw_phonikud_phonemes: str = ""
    raw_phonikud_stress: int = 0
    raw_vocal_shva: bool = False
    reason: str = ""

    def to_correction_entry(self, applied: bool) -> CorrectionEntry:
        return CorrectionEntry(
            form_key=self.form_key,
            hebrew_with_niqqud=self.hebrew_with_niqqud,
            raw_phonikud_phonemes=self.raw_phonikud_phonemes or self.corrected_phonemes,
            corrected_phonemes=self.corrected_phonemes,
            raw_stress=self.raw_phonikud_stress or self.corrected_stress,
            corrected_stress=self.corrected_stress,
            raw_vocal_shva=self.raw_vocal_shva,
            corrected_vocal_shva=self.corrected_vocal_shva,
            correction_applied=applied,
            reason=self.reason,
        )


class OverrideRegistry:
    """Map (verb, form_key) → pronunciation override."""

    def __init__(self, rules: dict[tuple[str, str], OverrideRule] | None = None):
        self.rules: dict[tuple[str, str], OverrideRule] = rules or {}

    @classmethod
    def from_phonikud_evaluation(cls, path: Path) -> "OverrideRegistry":
        """Load the registry from the phonikud evaluation audit file."""
        data = load_json(path)
        rules: dict[tuple[str, str], OverrideRule] = {}
        for row in data:
            verb = row.get("verb", "")
            form_key = row.get("form_key", "")
            if not verb or not form_key:
                continue
            raw_phonemes = row.get("phonikud_phonemes", "")
            corrected_phonemes = row.get("manual_override") or raw_phonemes
            raw_stress = int(row.get("phonikud_stress") or 1)
            corrected_stress = int(row.get("override_stress") or row.get("expected_stress") or raw_stress)
            raw_vocal_shva = bool(row.get("vocal_shva_phonikud", False))
            corrected_vocal_shva = bool(row.get("vocal_shva_override", raw_vocal_shva))

            reasons: list[str] = []
            if raw_phonemes and corrected_phonemes and raw_phonemes != corrected_phonemes:
                reasons.append("phoneme correction")
            if raw_stress != corrected_stress:
                reasons.append("stress correction")
            if raw_vocal_shva != corrected_vocal_shva:
                reasons.append("vocal-shva correction")

            rules[(verb, form_key)] = OverrideRule(
                verb=verb,
                form_key=form_key,
                hebrew_with_niqqud=row.get("hebrew_with_niqqud", ""),
                corrected_phonemes=corrected_phonemes,
                corrected_stress=corrected_stress,
                corrected_vocal_shva=corrected_vocal_shva,
                raw_phonikud_phonemes=raw_phonemes,
                raw_phonikud_stress=raw_stress,
                raw_vocal_shva=raw_vocal_shva,
                reason="; ".join(reasons) if reasons else "verified (no correction)",
            )
        return cls(rules)

    def apply(
        self,
        verb: str,
        form_key: str,
        raw_phonemes: str,
        raw_stress: int,
        raw_vocal_shva: bool,
        hebrew_with_niqqud: str,
    ) -> tuple[str, int, bool, CorrectionEntry]:
        """Return corrected (phonemes, stress, vocal_shva) and an audit entry."""
        key = (verb, form_key)
        if key in self.rules:
            rule = self.rules[key]
            entry = CorrectionEntry(
                form_key=form_key,
                hebrew_with_niqqud=hebrew_with_niqqud,
                raw_phonikud_phonemes=rule.raw_phonikud_phonemes,
                corrected_phonemes=rule.corrected_phonemes,
                raw_stress=rule.raw_phonikud_stress,
                corrected_stress=rule.corrected_stress,
                raw_vocal_shva=rule.raw_vocal_shva,
                corrected_vocal_shva=rule.corrected_vocal_shva,
                correction_applied=rule.corrected_phonemes != rule.raw_phonikud_phonemes
                or rule.corrected_stress != rule.raw_phonikud_stress
                or rule.corrected_vocal_shva != rule.raw_vocal_shva,
                reason=rule.reason,
            )
            return (
                rule.corrected_phonemes,
                rule.corrected_stress,
                rule.corrected_vocal_shva,
                entry,
            )

        # No override: pass through raw phonikud output
        entry = CorrectionEntry(
            form_key=form_key,
            hebrew_with_niqqud=hebrew_with_niqqud,
            raw_phonikud_phonemes=raw_phonemes,
            corrected_phonemes=raw_phonemes,
            raw_stress=raw_stress,
            corrected_stress=raw_stress,
            raw_vocal_shva=raw_vocal_shva,
            corrected_vocal_shva=raw_vocal_shva,
            correction_applied=False,
            reason="no override found; passed through",
        )
        return raw_phonemes, raw_stress, raw_vocal_shva, entry
