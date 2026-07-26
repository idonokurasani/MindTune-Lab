"""In-memory repository for HeLP evidence, keyed by root, verb, form and slot."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .loader import HeLPLoader
from .models import HeLPFormEvidence, HeLPVerbSummary

if False:  # type checking only to avoid runtime import cycles
    from mpe.domains.hebrew.canonical import HebrewLexicalEntity


@dataclass
class HeLPRepository:
    """Read-only repository over loaded HeLP evidence.

    The repository does not mutate source records and preserves provenance on
    every returned value.
    """

    loader: HeLPLoader = field(default_factory=lambda: HeLPLoader().load())

    def by_form(self, hebrew_form: str) -> list[HeLPFormEvidence]:
        return [ev for ev in self.loader.forms if ev.form == hebrew_form]

    def by_word_key(self, word_key: str) -> list[HeLPFormEvidence]:
        return [ev for ev in self.loader.forms if ev.word_key == word_key]

    def by_verb(self, verb_id: str) -> HeLPVerbSummary | None:
        for summary in self.loader.summaries:
            if summary.verb_id == verb_id:
                return summary
        return None

    def by_root(self, root: str) -> list[HeLPVerbSummary]:
        return [s for s in self.loader.summaries if s.root == root]

    def by_binyan(self, binyan: str) -> list[HeLPVerbSummary]:
        return [s for s in self.loader.summaries if s.binyan == binyan]

    def forms_for_verb(self, verb_id: str) -> list[HeLPFormEvidence]:
        return [ev for ev in self.loader.forms if ev.verb_id == verb_id]

    def slot_options(self, verb_id: str, slot: str) -> list[HeLPFormEvidence]:
        return [ev for ev in self.forms_for_verb(verb_id) if ev.slot == slot]

    def enrich_entity(self, entity: "HebrewLexicalEntity") -> "HebrewLexicalEntity":
        """Return a new entity with attached HeLP evidence for its surface form/verb."""
        from dataclasses import replace

        form_evidence = tuple(self.by_form(entity.surface_form))
        verb_summary = None
        if entity.help_verb_summary:
            verb_summary = self.by_verb(entity.help_verb_summary.verb_id)
        return replace(
            entity,
            help_form_evidence=form_evidence,
            help_verb_summary=verb_summary,
        )

    def difficulty_profile(
        self,
        verb_id: str,
        metric: str = "ld_mean_rt",
    ) -> dict[str, Any]:
        """Return a per-slot difficulty profile for a verb using HeLP evidence."""
        forms = self.forms_for_verb(verb_id)
        values: dict[str, list[float]] = {}
        for ev in forms:
            value = getattr(ev, metric)
            if value is not None:
                values.setdefault(ev.slot, []).append(value)
        return {
            "verb_id": verb_id,
            "metric": metric,
            "slots": {
                slot: {
                    "count": len(vals),
                    "mean": sum(vals) / len(vals),
                    "min": min(vals),
                    "max": max(vals),
                }
                for slot, vals in values.items()
            },
        }
