"""Deterministic HeLP data loader with reconciliation and import summaries."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .models import HeLPFormEvidence, HeLPImportReport, HeLPVerbSummary
from .validation import (
    load_help_enrichment_json,
    load_validated_help_audit,
    load_validated_help_forms,
)


class HeLPLoader:
    """Load, validate and reconcile HeLP lexical and psycholinguistic evidence."""

    def __init__(
        self,
        forms_path: Path | None = None,
        audit_path: Path | None = None,
        enrichment_path: Path | None = None,
        dataset_version: str = "",
    ) -> None:
        repo_root = Path(__file__).resolve().parents[7]
        self.forms_path = forms_path or (repo_root / "data" / "hebrew_verbs_help_forms.csv")
        self.audit_path = audit_path or (repo_root / "data" / "hebrew_verbs_help_audit.csv")
        self.enrichment_path = enrichment_path or (repo_root / "data" / "hebrew_verbs_help_enrichment.json")
        self.dataset_version = dataset_version
        self._forms: list[HeLPFormEvidence] | None = None
        self._summaries: list[HeLPVerbSummary] | None = None
        self._forms_report: HeLPImportReport | None = None
        self._audit_report: HeLPImportReport | None = None
        self._enrichment: dict[str, Any] | None = None

    def load(self) -> "HeLPLoader":
        """Deterministically load all configured HeLP datasets."""
        self._forms, self._forms_report = load_validated_help_forms(
            self.forms_path, dataset_version=self.dataset_version
        )
        self._summaries, self._audit_report = load_validated_help_audit(
            self.audit_path, dataset_version=self.dataset_version
        )
        self._enrichment = load_help_enrichment_json(self.enrichment_path)
        return self

    @property
    def forms(self) -> list[HeLPFormEvidence]:
        if self._forms is None:
            self.load()
        return self._forms or []

    @property
    def summaries(self) -> list[HeLPVerbSummary]:
        if self._summaries is None:
            self.load()
        return self._summaries or []

    @property
    def enrichment(self) -> dict[str, Any]:
        if self._enrichment is None:
            self.load()
        return self._enrichment or {}

    @property
    def forms_report(self) -> HeLPImportReport:
        if self._forms_report is None:
            self.load()
        return self._forms_report or HeLPImportReport(input_rows=0, valid_rows=0, invalid_rows=0, duplicate_rows=0, normalized_rows=0, unmatched_rows=0, linked_records=0, manual_review_records=0)

    @property
    def audit_report(self) -> HeLPImportReport:
        if self._audit_report is None:
            self.load()
        return self._audit_report or HeLPImportReport(input_rows=0, valid_rows=0, invalid_rows=0, duplicate_rows=0, normalized_rows=0, unmatched_rows=0, linked_records=0, manual_review_records=0)

    def combined_report(self) -> dict[str, Any]:
        """Return a deterministic, human-readable import summary."""
        forms = self.forms_report
        audit = self.audit_report
        return {
            "forms": forms.as_dict(),
            "audit": audit.as_dict(),
            "enrichment_verbs": len(self.enrichment.get("verbs", [])),
            "schema_version": self.enrichment.get("schema_version"),
            "dataset_version": self.dataset_version or "auto",
        }
