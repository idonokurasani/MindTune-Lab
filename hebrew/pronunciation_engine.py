"""Shared pronunciation and phonemization engine with central override layer."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .adapters.phonikud_adapter import phonemize, stress_from_phonemes
from .models import LinguisticOverride, PronunciationRecord
from .normalization import normalize_hebrew
from .shva import classify_shva


@dataclass
class PronunciationEngine:
    overrides: dict[str, dict[str, Any]] = field(default_factory=dict)
    override_path: Path | None = None

    def load_overrides(self, path: Path) -> None:
        self.override_path = path
        if path.exists():
            self.overrides = json.loads(path.read_text(encoding="utf-8"))
        else:
            self.overrides = {}

    def save_overrides(self) -> None:
        if self.override_path:
            self.override_path.parent.mkdir(parents=True, exist_ok=True)
            self.override_path.write_text(
                json.dumps(self.overrides, ensure_ascii=False, indent=2), encoding="utf-8"
            )

    def add_override(
        self,
        target: str,
        field: str,
        value: Any,
        reason: str = "",
        author: str = "",
    ) -> None:
        """Add a central pronunciation override."""
        if target not in self.overrides:
            self.overrides[target] = {}
        self.overrides[target][field] = {
            "value": value,
            "reason": reason,
            "author": author,
        }
        self.save_overrides()

    def get_pronunciation(
        self, text: str, context: dict[str, Any] | None = None
    ) -> PronunciationRecord:
        """Phonemize text and apply any central overrides."""
        text = normalize_hebrew(text)
        raw_phonemes = phonemize(text)
        stress = stress_from_phonemes(raw_phonemes)

        # Look up overrides by surface form or by context target
        target = text
        if context and "target" in context:
            target = context["target"]

        corrected = raw_phonemes
        stress_override = None
        shva_override = None
        applied: list[LinguisticOverride] = []
        if target in self.overrides:
            for field, override in self.overrides[target].items():
                if field == "phonemes":
                    corrected = override["value"]
                elif field == "stress":
                    stress = int(override["value"])
                    stress_override = int(override["value"])
                elif field == "vocal_shva":
                    shva_override = bool(override["value"])
                applied.append(
                    LinguisticOverride(
                        scope="form",
                        target=target,
                        field=field,
                        value=override["value"],
                        reason=override.get("reason", ""),
                        author=override.get("author", ""),
                    )
                )

        shva = classify_shva(text, manual_override=shva_override)

        return PronunciationRecord(
            phonemes_raw=raw_phonemes,
            phonemes_corrected=corrected,
            lexical_stress=stress,
            vocal_shva=(shva.shva_status == "vocal"),
            shva=shva,
            source="phonikud+overrides",
            source_id=(
                "manual_override"
                if shva_override is not None or stress_override is not None
                else "phonikud"
            ),
        )

    def apply_overrides(self, record: PronunciationRecord, target: str) -> PronunciationRecord:
        """Apply overrides to an existing PronunciationRecord in place."""
        if target in self.overrides:
            for field, override in self.overrides[target].items():
                if field == "phonemes":
                    record.phonemes_corrected = override["value"]
                elif field == "stress":
                    record.lexical_stress = int(override["value"])
        return record

    def validate_pronunciation(self, record: PronunciationRecord) -> list[str]:
        """Basic sanity checks on a pronunciation record."""
        issues: list[str] = []
        if not record.phonemes_corrected:
            issues.append("corrected phonemes are empty")
        if record.lexical_stress < 0:
            issues.append("lexical stress cannot be negative")
        return issues
