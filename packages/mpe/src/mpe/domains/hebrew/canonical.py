"""Canonical Hebrew lexical entity model, enriched by HeLP evidence."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from mpe.domains.hebrew.help.models import HeLPFormEvidence, HeLPVerbSummary


@dataclass(frozen=True)
class HebrewLexicalEntity:
    """A canonical Hebrew lexical unit that can carry HeLP psycholinguistic evidence.

    This model is deliberately separate from learner state. HeLP evidence is
    attached as read-only enrichment; behavioural history remains the
    authoritative source of learning progress.
    """

    entity_id: str
    surface_form: str
    lemma: str
    root: str
    binyan: str = ""
    part_of_speech: str = ""
    morphology: str = ""
    grammatical_features: dict[str, str] = field(default_factory=dict)
    pronunciation: str = ""
    stress: str = ""
    meaning: str = ""
    usage_context: str = ""
    curriculum_membership: tuple[str, ...] = field(default_factory=tuple)
    help_form_evidence: tuple[HeLPFormEvidence, ...] = field(default_factory=tuple)
    help_verb_summary: HeLPVerbSummary | None = None

    @property
    def has_help_evidence(self) -> bool:
        return bool(self.help_form_evidence) or self.help_verb_summary is not None

    def help_difficulty_summary(self) -> dict[str, Any]:
        if not self.help_form_evidence:
            return {"available": False}
        return {
            "available": True,
            "forms_with_frequency": sum(1 for ev in self.help_form_evidence if ev.frequency is not None),
            "forms_with_ld_rt": sum(1 for ev in self.help_form_evidence if ev.ld_mean_rt is not None),
            "forms_with_naming_rt": sum(1 for ev in self.help_form_evidence if ev.naming_mean_rt is not None),
            "mean_ld_accuracy": self._mean([ev.ld_accuracy for ev in self.help_form_evidence if ev.ld_accuracy is not None]),
        }

    @staticmethod
    def _mean(values: list[float]) -> float | None:
        return sum(values) / len(values) if values else None

    def as_dict(self) -> dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "surface_form": self.surface_form,
            "lemma": self.lemma,
            "root": self.root,
            "binyan": self.binyan,
            "part_of_speech": self.part_of_speech,
            "morphology": self.morphology,
            "grammatical_features": dict(self.grammatical_features),
            "pronunciation": self.pronunciation,
            "stress": self.stress,
            "meaning": self.meaning,
            "usage_context": self.usage_context,
            "curriculum_membership": list(self.curriculum_membership),
            "help_form_evidence_count": len(self.help_form_evidence),
            "help_difficulty_summary": self.help_difficulty_summary(),
            "has_help_evidence": self.has_help_evidence,
        }
