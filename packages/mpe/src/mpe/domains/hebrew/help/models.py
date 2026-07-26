"""HeLP data models (Hebrew Lexicon Project evidence)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class HeLPProvenance:
    """Provenance for a single HeLP-derived value or record."""

    source_name: str = "HeLP"
    dataset_version: str = ""
    source_row_id: str = ""
    import_timestamp: str = ""
    original_lexical_form: str = ""
    normalized_lexical_form: str = ""
    lemma: str = ""
    root: str = ""
    morphological_analysis: str = ""
    original_measurement_name: str = ""
    original_measurement_value: str = ""
    units: str = ""
    missing_value: bool = False
    transformation: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_name": self.source_name,
            "dataset_version": self.dataset_version,
            "source_row_id": self.source_row_id,
            "import_timestamp": self.import_timestamp,
            "original_lexical_form": self.original_lexical_form,
            "normalized_lexical_form": self.normalized_lexical_form,
            "lemma": self.lemma,
            "root": self.root,
            "morphological_analysis": self.morphological_analysis,
            "original_measurement_name": self.original_measurement_name,
            "original_measurement_value": self.original_measurement_value,
            "units": self.units,
            "missing_value": self.missing_value,
            "transformation": self.transformation,
        }


@dataclass(frozen=True)
class HeLPFormEvidence:
    """Psycholinguistic evidence for a specific Hebrew form."""

    verb_id: str
    root: str
    binyan: str
    italian_cue: str
    slot: str
    prompt: str
    form: str
    word_key: str
    help_matched: bool
    frequency: float | None
    ld_mean_rt: float | None
    ld_accuracy: float | None
    naming_mean_rt: float | None
    naming_accuracy: float | None
    provenance: HeLPProvenance = field(default_factory=HeLPProvenance)

    @property
    def lexical_surface(self) -> str:
        return self.form or self.word_key


@dataclass(frozen=True)
class HeLPVerbSummary:
    """Aggregated HeLP evidence at the verb/root level."""

    verb_id: str
    root: str
    binyan: str
    italian_cue: str
    forms_total: int
    forms_unique: int
    help_matched_unique: int
    help_match_ratio: float
    median_frequency: float | None
    median_ld_mean_rt: float | None
    median_ld_accuracy: float | None
    median_naming_mean_rt: float | None
    median_naming_accuracy: float | None
    flags: tuple[str, ...] = field(default_factory=tuple)
    matched_forms: tuple[str, ...] = field(default_factory=tuple)
    missing_from_help_forms: tuple[str, ...] = field(default_factory=tuple)
    provenance: HeLPProvenance = field(default_factory=HeLPProvenance)


@dataclass(frozen=True)
class HeLPImportReport:
    """Result of a deterministic HeLP data import."""

    input_rows: int
    valid_rows: int
    invalid_rows: int
    duplicate_rows: int
    normalized_rows: int
    unmatched_rows: int
    linked_records: int
    manual_review_records: int
    errors: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "input_rows": self.input_rows,
            "valid_rows": self.valid_rows,
            "invalid_rows": self.invalid_rows,
            "duplicate_rows": self.duplicate_rows,
            "normalized_rows": self.normalized_rows,
            "unmatched_rows": self.unmatched_rows,
            "linked_records": self.linked_records,
            "manual_review_records": self.manual_review_records,
            "errors": self.errors,
        }
