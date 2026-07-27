"""Explicit confirmatory and exploratory hypothesis representations."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from mindtune_clm.validation.endpoints import Endpoint
from mindtune_clm.validation.estimands import Estimand


class HypothesisType(str, Enum):
    CONFIRMATORY = "confirmatory"
    EXPLORATORY = "exploratory"


class Directionality(str, Enum):
    SUPERIORITY = "superiority"
    NON_INFERIORITY = "non-inferiority"
    EQUIVALENCE = "equivalence"
    TWO_SIDED = "two-sided"


@dataclass(frozen=True)
class Hypothesis:
    """A preregistered hypothesis with a concrete estimand and endpoint."""

    hypothesis_id: str
    type: str  # confirmatory or exploratory
    null_statement: str
    alternative_statement: str
    estimand: Estimand
    endpoint: Endpoint
    population: str
    comparison: str
    directionality: str
    significance_threshold: float | None
    multiplicity_family: str
    analysis_method: str
    missing_data_handling: str
    sensitivity_analyses: list[str] = field(default_factory=list)
    interpretation_limits: str = ""

    def is_confirmatory(self) -> bool:
        return self.type == HypothesisType.CONFIRMATORY

    def is_exploratory(self) -> bool:
        return self.type == HypothesisType.EXPLORATORY

    def as_dict(self) -> dict[str, Any]:
        return {
            "hypothesis_id": self.hypothesis_id,
            "type": self.type,
            "null_statement": self.null_statement,
            "alternative_statement": self.alternative_statement,
            "estimand": self.estimand.as_dict(),
            "endpoint": self.endpoint.as_dict(),
            "population": self.population,
            "comparison": self.comparison,
            "directionality": self.directionality,
            "significance_threshold": self.significance_threshold,
            "multiplicity_family": self.multiplicity_family,
            "analysis_method": self.analysis_method,
            "missing_data_handling": self.missing_data_handling,
            "sensitivity_analyses": list(self.sensitivity_analyses),
            "interpretation_limits": self.interpretation_limits,
        }
