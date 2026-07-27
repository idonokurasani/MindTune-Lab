"""Explicit estimand definitions for CLM-08."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Estimand:
    """Concrete estimand for a study hypothesis."""

    estimand_id: str
    population: str
    treatment_condition: str
    comparator: str
    outcome_variable: str
    intercurrent_event_handling: str
    summary_measure: str
    directionality: str = "two-sided"
    notes: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "estimand_id": self.estimand_id,
            "population": self.population,
            "treatment_condition": self.treatment_condition,
            "comparator": self.comparator,
            "outcome_variable": self.outcome_variable,
            "intercurrent_event_handling": self.intercurrent_event_handling,
            "summary_measure": self.summary_measure,
            "directionality": self.directionality,
            "notes": self.notes,
        }
