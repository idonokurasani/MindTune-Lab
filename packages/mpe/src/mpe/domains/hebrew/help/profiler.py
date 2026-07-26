"""HeLP-based lexical difficulty and selection profiler."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .models import HeLPFormEvidence
from .repository import HeLPRepository


@dataclass
class HeLPPriorityItem:
    """A Hebrew form ranked for selection using HeLP-derived difficulty evidence."""

    form: str
    verb_id: str
    root: str
    binyan: str
    slot: str
    frequency: float | None
    ld_mean_rt: float | None
    ld_accuracy: float | None
    priority_score: float
    rationale: str = ""


@dataclass
class HeLPProfiler:
    """Rank Hebrew forms and verbs for item selection and difficulty profiling."""

    repository: HeLPRepository = field(default_factory=HeLPRepository)

    def difficulty_for_form(self, form: str) -> dict[str, Any]:
        matches = self.repository.by_form(form)
        if not matches:
            return {"form": form, "known": False, "evidence": []}
        return {
            "form": form,
            "known": True,
            "evidence": [
                {
                    "verb_id": ev.verb_id,
                    "root": ev.root,
                    "binyan": ev.binyan,
                    "slot": ev.slot,
                    "frequency": ev.frequency,
                    "ld_mean_rt": ev.ld_mean_rt,
                    "ld_accuracy": ev.ld_accuracy,
                    "naming_mean_rt": ev.naming_mean_rt,
                    "naming_accuracy": ev.naming_accuracy,
                }
                for ev in matches
            ],
        }

    def priority_queue(
        self,
        verb_ids: list[str] | None = None,
        slots: list[str] | None = None,
        require_help_match: bool = True,
        top_n: int = 20,
    ) -> list[HeLPPriorityItem]:
        """Return forms ranked by a simple difficulty/priority score.

        Lower frequency + higher lexical decision RT => higher priority for
        focused practice. Accuracy above 0.95 is considered mastered.
        """
        forms = self.repository.loader.forms
        candidates: list[HeLPFormEvidence] = []
        for ev in forms:
            if verb_ids and ev.verb_id not in verb_ids:
                continue
            if slots and ev.slot not in slots:
                continue
            if require_help_match and not ev.help_matched:
                continue
            candidates.append(ev)

        ranked: list[HeLPPriorityItem] = []
        for ev in candidates:
            freq = ev.frequency or 0.0
            rt = ev.ld_mean_rt or 0.0
            acc = ev.ld_accuracy or 0.0
            score = (1.0 / (1.0 + freq)) + (rt / 1000.0) - acc
            ranked.append(
                HeLPPriorityItem(
                    form=ev.form,
                    verb_id=ev.verb_id,
                    root=ev.root,
                    binyan=ev.binyan,
                    slot=ev.slot,
                    frequency=ev.frequency,
                    ld_mean_rt=ev.ld_mean_rt,
                    ld_accuracy=ev.ld_accuracy,
                    priority_score=round(score, 4),
                    rationale=f"freq={freq:.2f}, ld_rt={rt:.1f}, ld_acc={acc:.3f}",
                )
            )
        ranked.sort(key=lambda item: item.priority_score, reverse=True)
        return ranked[:top_n]

    def compare_observed_with_help(
        self,
        verb_id: str,
        observed_accuracy: float,
        observed_rt_ms: float | None = None,
        slot: str = "",
    ) -> dict[str, Any]:
        """Compare a MindTune-derived observation with HeLP norms."""
        summary = self.repository.by_verb(verb_id)
        norm_accuracy = summary.median_ld_accuracy if summary else None
        norm_rt = summary.median_ld_mean_rt if summary else None
        return {
            "verb_id": verb_id,
            "slot": slot,
            "observed": {
                "accuracy": observed_accuracy,
                "rt_ms": observed_rt_ms,
            },
            "help_norm": {
                "median_ld_accuracy": norm_accuracy,
                "median_ld_mean_rt": norm_rt,
            },
            "interpretation": {
                "accuracy_lower_than_norm": norm_accuracy is not None and observed_accuracy < norm_accuracy,
                "rt_slower_than_norm": observed_rt_ms is not None and norm_rt is not None and observed_rt_ms > norm_rt,
            },
        }
