"""Prespecified analysis plan, multiplicity handling, and execution for CLM-08."""

from __future__ import annotations

import hashlib
import json
import math
import statistics
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from mindtune_clm.validation.datasets import AnalysisDataset
from mindtune_clm.validation.hypotheses import Hypothesis
from mindtune_clm.validation.statistics import (
    bootstrap_ci,
    paired_mean_difference,
    paired_median_difference,
    permutation_test,
    risk_difference,
)


def _stable_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _sd(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    return statistics.stdev(values)


class MultiplicityMethod(str, Enum):
    NONE = "none"
    HIERARCHICAL = "hierarchical"
    HOLM = "holm"
    FDR = "fdr"


class MissingDataPolicy(str, Enum):
    NO_IMPUTATION = "no_imputation"
    CONSERVATIVE_FAILURE = "conservative_failure"
    SENSITIVITY_BOUNDS = "sensitivity_bounds"


class Population(str, Enum):
    INTENTION_TO_TREAT = "intention-to-treat"
    MODIFIED_INTENTION_TO_TREAT = "modified-intention-to-treat"
    PER_PROTOCOL = "per-protocol"
    SAFETY = "safety"
    COMPLETE_CASE = "complete-case"
    HIGH_QUALITY_SENSOR = "high-quality-sensor"


@dataclass(frozen=True)
class SensitivitySpec:
    name: str
    description: str
    population_filter: str = "all"
    missing_data_variant: str | None = None
    trim_threshold_ms: float | None = None
    exclude_first_period: bool = False
    adjust_carryover: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "population_filter": self.population_filter,
            "missing_data_variant": self.missing_data_variant,
            "trim_threshold_ms": self.trim_threshold_ms,
            "exclude_first_period": self.exclude_first_period,
            "adjust_carryover": self.adjust_carryover,
        }


@dataclass(frozen=True)
class AnalysisPlan:
    """Prespecified, versioned analysis plan for a study."""

    plan_id: str
    study_id: str
    study_version: int
    primary_hypothesis_id: str
    population: str
    missing_data_policy: str
    multiplicity_method: str
    alpha: float = 0.05
    sensitivity_specs: list[SensitivitySpec] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)

    def as_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "study_id": self.study_id,
            "study_version": self.study_version,
            "primary_hypothesis_id": self.primary_hypothesis_id,
            "population": self.population,
            "missing_data_policy": self.missing_data_policy,
            "multiplicity_method": self.multiplicity_method,
            "alpha": self.alpha,
            "sensitivity_specs": [s.as_dict() for s in self.sensitivity_specs],
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class AnalysisResult:
    """Immutable result of one prespecified analysis."""

    analysis_id: str
    study_id: str
    study_version: int
    plan_id: str
    hypothesis_id: str
    dataset_checksum: str
    population: str
    estimand_summary: str
    effect_estimate: float
    confidence_interval: tuple[float, float]
    p_value: float | None
    raw_p_value: float | None
    adjusted_p_value: float | None
    multiplicity_method: str
    method: str
    included_sessions: list[str] = field(default_factory=list)
    excluded_sessions: list[str] = field(default_factory=list)
    seed: int | None = None
    code_sha: str = ""
    limitations: list[str] = field(default_factory=list)
    sensitivity_label: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "analysis_id": self.analysis_id,
            "study_id": self.study_id,
            "study_version": self.study_version,
            "plan_id": self.plan_id,
            "hypothesis_id": self.hypothesis_id,
            "dataset_checksum": self.dataset_checksum,
            "population": self.population,
            "estimand_summary": self.estimand_summary,
            "effect_estimate": self.effect_estimate,
            "confidence_interval": list(self.confidence_interval),
            "p_value": self.p_value,
            "raw_p_value": self.raw_p_value,
            "adjusted_p_value": self.adjusted_p_value,
            "multiplicity_method": self.multiplicity_method,
            "method": self.method,
            "included_sessions": list(self.included_sessions),
            "excluded_sessions": list(self.excluded_sessions),
            "seed": self.seed,
            "code_sha": self.code_sha,
            "limitations": list(self.limitations),
            "sensitivity_label": self.sensitivity_label,
        }

    def checksum(self) -> str:
        return hashlib.sha256(_stable_json(self.as_dict()).encode("utf-8")).hexdigest()


def _participant_level_means(rows: list[Any]) -> dict[str, float]:
    by_participant: dict[str, list[float]] = {}
    for r in rows:
        if r.correct is not None:
            by_participant.setdefault(r.participant_id, []).append(float(r.correct))
    return {p: sum(v) / len(v) for p, v in by_participant.items() if v}


def _group_means(rows: list[Any], condition: str) -> list[float]:
    participant_means: dict[str, list[float]] = {}
    for r in rows:
        if r.condition == condition and r.correct is not None:
            participant_means.setdefault(r.participant_id, []).append(float(r.correct))
    return [sum(v) / len(v) for v in participant_means.values() if v]


def _paired_participant_values(rows: list[Any], cond_a: str, cond_b: str) -> list[tuple[float, float]]:
    a_by_p: dict[str, list[float]] = {}
    b_by_p: dict[str, list[float]] = {}
    for r in rows:
        if r.correct is None:
            continue
        if r.condition == cond_a:
            a_by_p.setdefault(r.participant_id, []).append(float(r.correct))
        if r.condition == cond_b:
            b_by_p.setdefault(r.participant_id, []).append(float(r.correct))
    pairs = []
    for p in set(a_by_p) & set(b_by_p):
        pairs.append((_mean(a_by_p[p]), _mean(b_by_p[p])))
    return pairs


def apply_multiplicity(raw_p_values: list[float], method: str, alpha: float = 0.05) -> list[float]:
    """Adjust p-values using the named multiplicity method."""
    if method == MultiplicityMethod.NONE.value or len(raw_p_values) <= 1:
        return list(raw_p_values)
    indexed = sorted(enumerate(raw_p_values), key=lambda x: x[1])
    n = len(raw_p_values)
    adjusted: list[float] = [0.0] * n
    if method == MultiplicityMethod.HOLM.value:
        prev = 0.0
        for rank, (orig_idx, p) in enumerate(indexed, start=1):
            adjusted_p = min(1.0, max(p * (n - rank + 1), prev))
            adjusted[orig_idx] = adjusted_p
            prev = adjusted_p
    elif method == MultiplicityMethod.FDR.value:
        # Benjamini-Hochberg
        for rank, (orig_idx, p) in enumerate(indexed, start=1):
            adjusted[orig_idx] = min(1.0, p * n / rank)
        # enforce monotonicity
        max_adj = 0.0
        sorted_adjs = sorted((indexed[i][0], adjusted[indexed[i][0]]) for i in range(n))
        for orig_idx, adj in sorted_adjs:
            max_adj = max(max_adj, adj)
            adjusted[orig_idx] = min(max_adj, 1.0)
    else:
        return list(raw_p_values)
    return adjusted


def run_primary_analysis(
    dataset: AnalysisDataset,
    plan: AnalysisPlan,
    hypothesis: Hypothesis,
    seed: int | None = None,
    code_sha: str = "",
    sensitivity_label: str | None = None,
) -> AnalysisResult:
    """Run the prespecified primary or sensitivity analysis for a hypothesis."""
    estimand = hypothesis.estimand
    treatment = estimand.treatment_condition
    comparator = estimand.comparator

    included = list({r.session_id for r in dataset.rows})
    excluded: list[str] = []

    if plan.missing_data_policy == MissingDataPolicy.CONSERVATIVE_FAILURE.value:
        rows = [
            r if r.correct is not None else r.__class__(
                **{**r.as_dict(), "correct": False, "response_time_ms": r.response_time_ms or 0.0}
            )
            for r in dataset.rows
        ]
    else:
        rows = list(dataset.rows)

    if estimand.summary_measure == "participant-level mean difference":
        pairs = _paired_participant_values(rows, treatment, comparator)
        if pairs:
            effect, se = paired_mean_difference(pairs)
            ci_low = effect - 1.96 * se
            ci_high = effect + 1.96 * se
            _, p = permutation_test([a for a, _ in pairs], [b for _, b in pairs], seed=seed)
        else:
            g1 = _group_means(rows, treatment)
            g2 = _group_means(rows, comparator)
            effect = _mean(g1) - _mean(g2)
            n1 = len(g1)
            n2 = len(g2)
            se = math.sqrt((_sd(g1) ** 2 / max(n1, 1)) + (_sd(g2) ** 2 / max(n2, 1)))
            ci_low = effect - 1.96 * se
            ci_high = effect + 1.96 * se
            _, p = permutation_test(g1, g2, seed=seed) if g1 and g2 else (0.0, 1.0)
    elif estimand.summary_measure == "median difference":
        pairs = _paired_participant_values(rows, treatment, comparator)
        effect = paired_median_difference(pairs)
        ci = bootstrap_ci([a - b for a, b in pairs], statistic=lambda x: statistics.median(x) if x else 0.0, seed=seed)
        ci_low, ci_high = ci[1], ci[2]
        if pairs:
            _, p = permutation_test([a for a, _ in pairs], [b for _, b in pairs], seed=seed)
        else:
            p = 1.0
    elif estimand.summary_measure == "risk difference":
        g1 = _group_means(rows, treatment)
        g2 = _group_means(rows, comparator)
        effect, se = risk_difference([1 if x > 0.5 else 0 for x in g1], [1 if x > 0.5 else 0 for x in g2])
        ci_low = effect - 1.96 * se
        ci_high = effect + 1.96 * se
        _, p = permutation_test(g1, g2, seed=seed)
    else:
        g1 = _group_means(rows, treatment)
        g2 = _group_means(rows, comparator)
        effect = _mean(g1) - _mean(g2)
        ci = bootstrap_ci(
            [a - b for a, b in zip(g1, g2, strict=True)] if len(g1) == len(g2) else g1 + [-v for v in g2],
            seed=seed,
        )
        ci_low, ci_high = ci[1], ci[2]
        _, p = permutation_test(g1, g2, seed=seed) if g1 and g2 else (0.0, 1.0)

    raw_p = float(p) if p is not None else None
    adjusted = None
    if plan.multiplicity_method != MultiplicityMethod.NONE.value and raw_p is not None:
        adjusted = apply_multiplicity([raw_p], plan.multiplicity_method, alpha=plan.alpha)[0]

    return AnalysisResult(
        analysis_id=str(uuid.uuid4()),
        study_id=plan.study_id,
        study_version=plan.study_version,
        plan_id=plan.plan_id,
        hypothesis_id=hypothesis.hypothesis_id,
        dataset_checksum=dataset.checksum,
        population=dataset.population,
        estimand_summary=f"{estimand.summary_measure} of {estimand.outcome_variable}",
        effect_estimate=effect,
        confidence_interval=(ci_low, ci_high),
        p_value=raw_p,
        raw_p_value=raw_p,
        adjusted_p_value=adjusted,
        multiplicity_method=plan.multiplicity_method,
        method=hypothesis.analysis_method,
        included_sessions=included,
        excluded_sessions=excluded,
        seed=seed,
        code_sha=code_sha,
        limitations=["synthetic_fixture"],
        sensitivity_label=sensitivity_label,
    )
