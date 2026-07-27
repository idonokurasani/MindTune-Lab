"""Baseline estimation and stability validation."""

from __future__ import annotations

from mindtune_clm.calibration.models import (
    CalibrationBlock,
    FeatureBaseline,
    QualitySummary,
    StabilitySummary,
)
from mindtune_clm.calibration.protocol import CalibrationProtocol
from mindtune_clm.calibration.robust_stats import (
    compute_baseline_stats,
    iqr,
    median,
)


class BaselineEstimator:
    """Compute per-feature baselines and stability metrics."""

    ALGORITHM_VERSION = "clm07.robust.v1"

    def estimate_feature(
        self,
        feature_name: str,
        modality: str,
        unit: str,
        values: list[float],
        block_medians: list[float] | None = None,
        block_iqrs: list[float] | None = None,
    ) -> FeatureBaseline:
        """Return a FeatureBaseline from accepted values."""
        accepted_values = [v for v in values if v is not None]
        stats = compute_baseline_stats(accepted_values)

        # Stability metrics
        stability: dict[str, float] = {}
        if block_medians and len(block_medians) >= 2:
            overall = median(accepted_values) if accepted_values else 0.0
            deviations = [abs(b - overall) for b in block_medians if b is not None]
            within_drift = max(deviations) if deviations else 0.0
            overall_iqr = stats["distribution_shape"].get("iqr", 0.0)
            # Agreement: low per-block dispersion relative to overall dispersion is stable.
            block_dispersions = [iq for iq in (block_iqrs or []) if iq is not None]
            median_block_iqr = median(block_dispersions) if block_dispersions else 0.0
            agreement = 1.0 if overall_iqr == 0 else max(0.0, 1.0 - median_block_iqr / overall_iqr)
            stability["within_block_drift"] = within_drift
            stability["block_agreement"] = agreement

        quality_status = "sufficient" if len(accepted_values) >= 10 else "insufficient"
        if stats["dispersion"] == 0.0 and len(accepted_values) > 1:
            quality_status = "zero_dispersion"

        return FeatureBaseline(
            feature_name=feature_name,
            modality=modality,
            unit=unit,
            sample_count=len(accepted_values),
            accepted_count=len(accepted_values),
            rejected_count=0,
            missing_count=0,
            central_tendency=stats["central_tendency"],
            dispersion=stats["dispersion"],
            robust_min=stats["robust_min"],
            robust_max=stats["robust_max"],
            selected_quantiles=stats["selected_quantiles"],
            outlier_policy="iqr_1.5",
            distribution_shape=stats["distribution_shape"],
            stability_metrics=stability,
            quality_status=quality_status,
            transformation_recommendation="robust_z",
            algorithm_version=self.ALGORITHM_VERSION,
        )

    def estimate_session(
        self,
        blocks: list[CalibrationBlock],
        protocol: CalibrationProtocol,
        quality_summary: QualitySummary,
    ) -> tuple[dict[str, FeatureBaseline], StabilitySummary]:
        """Return feature baselines and a stability summary for the session."""
        per_feature_values: dict[str, list[float]] = {}
        per_feature_modality: dict[str, str] = {}
        per_feature_unit: dict[str, str] = {}
        block_medians: dict[str, list[float]] = {}
        block_iqrs: dict[str, list[float]] = {}

        for block in blocks:
            for feature, observations in block.accepted_feature_observations.items():
                values = [float(o.value) for o in observations if o.value is not None]
                per_feature_values.setdefault(feature, []).extend(values)
                if feature not in per_feature_modality and observations:
                    per_feature_modality[feature] = observations[0].modality
                    per_feature_unit[feature] = ""
                block_medians.setdefault(feature, []).append(median(values))
                block_iqrs.setdefault(feature, []).append(iqr(values))

        baselines: dict[str, FeatureBaseline] = {}
        for feature, values in per_feature_values.items():
            baselines[feature] = self.estimate_feature(
                feature,
                per_feature_modality.get(feature, "unknown"),
                per_feature_unit.get(feature, ""),
                values,
                block_medians=block_medians.get(feature, []),
                block_iqrs=block_iqrs.get(feature, []),
            )

        # Global stability validation
        drifts = []
        agreements = []
        for baseline in baselines.values():
            drift = baseline.stability_metrics.get("within_block_drift", 0.0)
            agreement = baseline.stability_metrics.get("block_agreement", 1.0)
            drifts.append(drift)
            agreements.append(agreement)

        max_drift = max(drifts) if drifts else 0.0
        min_agreement = min(agreements) if agreements else 1.0
        sample_rate_stability = 1.0  # Placeholder; would be derived from actual timestamps.
        convergence = len(baselines) > 0 and all(
            b.sample_count >= protocol.min_accepted_observations for b in baselines.values()
        )

        reasons: list[str] = []
        if max_drift > protocol.max_within_block_drift:
            reasons.append("excessive_within_block_drift")
        if min_agreement < protocol.min_block_agreement:
            reasons.append("low_block_agreement")

        stability = StabilitySummary(
            within_block_drift=max_drift,
            block_agreement=min_agreement,
            sample_rate_stability=sample_rate_stability,
            convergence=convergence,
            reason_codes=reasons,
        )
        return baselines, stability


def validate_stability(stability: StabilitySummary, protocol: CalibrationProtocol) -> bool:
    """Return True when the stability summary passes protocol thresholds."""
    if not stability.convergence:
        return False
    if stability.within_block_drift > protocol.max_within_block_drift:
        return False
    if stability.block_agreement < protocol.min_block_agreement:
        return False
    if stability.sample_rate_stability < 0.9:
        return False
    return True
