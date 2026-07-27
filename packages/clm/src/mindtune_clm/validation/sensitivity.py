"""Sensitivity analysis templates and execution for CLM-08."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from mindtune_clm.validation.analysis_plan import (
    AnalysisPlan,
    AnalysisResult,
    SensitivitySpec,
    run_primary_analysis,
)
from mindtune_clm.validation.datasets import AnalysisDataset
from mindtune_clm.validation.hypotheses import Hypothesis


@dataclass(frozen=True)
class SensitivityResult:
    """A labelled sensitivity-analysis result."""

    label: str
    description: str
    result: AnalysisResult

    def as_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "description": self.description,
            "result": self.result.as_dict(),
        }


def apply_sensitivity_filter(
    dataset: AnalysisDataset, spec: SensitivitySpec
) -> AnalysisDataset:
    """Return a dataset filtered according to a sensitivity spec."""
    rows = list(dataset.rows)
    if spec.exclude_first_period:
        rows = [r for r in rows if r.period != 1]
    if spec.trim_threshold_ms is not None:
        rows = [r for r in rows if r.response_time_ms <= spec.trim_threshold_ms]
    if spec.population_filter == "per-protocol":
        rows = [r for r in rows if not r.deviation_flags]
    elif spec.population_filter == "complete-case":
        rows = [r for r in rows if r.correct is not None]
    elif spec.population_filter == "high-sensor-quality":
        rows = [r for r in rows if r.sensor_quality_summary.get("quality", "low") != "low"]
    return AnalysisDataset.build(
        rows,
        population=f"{dataset.population}-{spec.name}",
        study_id=dataset.study_id,
        study_version=dataset.study_version,
    )


def run_sensitivity_analysis(
    dataset: AnalysisDataset,
    spec: SensitivitySpec,
    plan: AnalysisPlan,
    hypothesis: Hypothesis,
    seed: int | None = None,
    code_sha: str = "",
) -> SensitivityResult:
    """Run a prespecified sensitivity analysis."""
    filtered = apply_sensitivity_filter(dataset, spec)
    result = run_primary_analysis(
        filtered,
        plan,
        hypothesis,
        seed=seed,
        code_sha=code_sha,
        sensitivity_label=spec.name,
    )
    return SensitivityResult(
        label=spec.name,
        description=spec.description,
        result=result,
    )
