"""Approval-layer transitions for Hebrew linguistic records."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from .models import ExampleSentence, VerbForm
from .resources.source_registry import SourceRegistry


class ApprovalPipeline:
    """Move records through the raw -> normalized -> candidate -> validated
    -> curriculum-approved pipeline.
    """

    def __init__(self, registry: SourceRegistry | None = None):
        self.registry = registry or SourceRegistry()

    def _source_evidence_eligibility(self, form: VerbForm) -> str:
        """Return the eligibility tier for the form.

        If any source is production-approved, the form is production-eligible.
        Otherwise return the most restrictive tier found.
        """
        restrictive_order = [
            "blocked",
            "unknown",
            "reference_only",
            "private_research_only",
            "production_approved",
        ]
        values = set()
        for ev in form.source_evidence:
            try:
                rec = self.registry.get(ev.source_id or ev.source)
                values.add(rec.production_eligibility)
            except Exception:
                values.add("unknown")
        if "production_approved" in values:
            return "production_approved"
        for tier in restrictive_order:
            if tier in values:
                return tier
        return "unknown"

    def _any_reference_only(self, form: VerbForm) -> bool:
        for ev in form.source_evidence:
            try:
                if (
                    self.registry.get(ev.source_id or ev.source).production_eligibility
                    == "reference_only"
                ):
                    return True
            except Exception:
                pass
        return False

    def normalize(self, form: VerbForm, validation_notes: list[str] | None = None) -> VerbForm:
        """Transition a raw record to normalized."""
        form.linguistic_status = "normalized"
        form.validation_evidence.extend(validation_notes or [])
        return form

    def candidate(
        self, form: VerbForm, confidence: float, notes: list[str] | None = None
    ) -> VerbForm:
        form.linguistic_status = "candidate"
        form.confidence = confidence
        if notes:
            form.validation_evidence.extend(notes)
        return form

    def validate(
        self, form: VerbForm, confidence: float, notes: list[str] | None = None
    ) -> VerbForm:
        """Validate a candidate; reference sources may validate but not be curriculum-approved."""
        eligibility = self._source_evidence_eligibility(form)
        if eligibility in ("blocked", "unknown"):
            form.linguistic_status = "rejected"
            form.rejection_reason = f"source eligibility: {eligibility}"
            return form
        form.linguistic_status = "validated"
        form.confidence = confidence
        form.source_agreement = "full" if not form.unresolved_conflicts else "partial"
        if notes:
            form.validation_evidence.extend(notes)
        return form

    def approve_for_curriculum(
        self, form: VerbForm, reviewer: str, notes: list[str] | None = None
    ) -> VerbForm:
        """Approve a validated record for curriculum use."""
        if form.linguistic_status != "validated":
            form.curriculum_status = "rejected"
            form.rejection_reason = f"cannot approve {form.linguistic_status} record"
            return form
        eligibility = self._source_evidence_eligibility(form)
        if eligibility != "production_approved":
            form.curriculum_status = "restricted"
            form.rejection_reason = f"source not production-approved: {eligibility}"
            return form
        form.curriculum_status = "approved"
        form.reviewer_status = f"reviewed by {reviewer}"
        if notes:
            form.validation_evidence.extend(notes)
        return form

    def evaluate_sentence(self, sentence: ExampleSentence) -> ExampleSentence:
        """Sentence candidates remain unapproved until explicit review."""
        if sentence.source_eligibility in ("blocked", "unknown"):
            sentence.curriculum_status = "rejected"
            sentence.rejection_reason = "source not eligible"
        elif sentence.suspected_noise or not sentence.punctuation_quality_ok:
            sentence.curriculum_status = "rejected"
            sentence.rejection_reason = "quality check failed"
        elif not sentence.target_form_exact_match and not sentence.target_form_morphological_match:
            sentence.curriculum_status = "not_reviewed"
            sentence.curriculum_suitability = "target_not_verified"
        else:
            sentence.curriculum_suitability = "pending_review"
            sentence.curriculum_status = "not_reviewed"
        sentence.approved = sentence.curriculum_status == "approved"
        return sentence
