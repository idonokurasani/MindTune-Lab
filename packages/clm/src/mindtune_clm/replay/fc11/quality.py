"""FC11 deterministic quality gating for CLM-02B."""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from mindtune_clm.replay.models import NormalizedSensorSample, QualityAssessment, ReplayWindow
from mindtune_clm.replay.quality import QualityPolicy


@dataclass(frozen=True)
class FC11QualityPolicy(QualityPolicy):
    """FC11-specific deterministic quality policy.

    Inherits generic thresholds and adds FC11 reason-code naming so the
    replay payloads preserve provenance.
    """

    policy_id: str = "mindtune_clm.replay.fc11.quality.v1"
    version: str = "1.0.0"
    signal_quality_good_labels: set[str] = field(
        default_factory=lambda: {"good", "ok", "excellent"}
    )
    amplitude_min: float = -1.0e6
    amplitude_max: float = 1.0e6
    flatline_tolerance: float = 0.0
    discontinuity_threshold: float = 1.0e6
    max_missingness: float = 1.0
    min_accepted_sample_count: int = 1
    min_channel_coverage: int = 1

    def assess(  # noqa: C901
        self,
        sample: NormalizedSensorSample,
        previous: NormalizedSensorSample | None = None,
    ) -> QualityAssessment:
        reason_codes: list[str] = []
        artifacts: list[str] = []
        missing_channels = 0
        total_channels = len(sample.channel_values)

        if sample.source_timestamp is None:
            reason_codes.append("fc11_missing_timestamp")

        if sample.replay_relative_timestamp is None:
            reason_codes.append("fc11_timestamp_regression")

        for op in sample.normalization_operations:
            if op == "fc11_duplicate_timestamp":
                reason_codes.append("fc11_duplicate_timestamp")
            elif op.startswith("parse_failed:"):
                reason_codes.append("fc11_malformed_record")
            elif op == "fc11_missing_required_channel":
                reason_codes.append("fc11_missing_required_channel")
            elif op == "fc11_poor_signal":
                reason_codes.append("fc11_poor_signal")
            elif op == "fc11_artifact_flag":
                reason_codes.append("fc11_artifact_flag")
                artifacts.append("artifact")
            elif op == "fc11_movement_detected":
                reason_codes.append("fc11_movement_detected")
                artifacts.append("movement")
            elif op == "fc11_packet_loss":
                reason_codes.append("fc11_packet_loss")
                artifacts.append("packet_loss")

        flatline_channels = 0
        for ch, value in sample.channel_values.items():
            if value is None:
                missing_channels += 1
                continue
            if not math.isfinite(value):
                reason_codes.append("fc11_malformed_record")
                continue
            if value < self.amplitude_min or value > self.amplitude_max:
                reason_codes.append("fc11_amplitude_out_of_range")
                artifacts.append(f"amplitude_out_of_range:{ch}")
            if previous is not None:
                prev_value = previous.channel_values.get(ch)
                if prev_value is not None and math.isfinite(prev_value):
                    if self.flatline_tolerance is not None and abs(value - prev_value) <= self.flatline_tolerance:
                        flatline_channels += 1
                    if abs(value - prev_value) > self.discontinuity_threshold:
                        reason_codes.append("fc11_amplitude_out_of_range")
                        artifacts.append(f"abrupt_discontinuity:{ch}")

        if flatline_channels >= total_channels and total_channels > 0:
            reason_codes.append("fc11_flatline")

        missingness = missing_channels / max(1, total_channels)
        if missingness > self.max_missingness:
            reason_codes.append("fc11_unknown_quality_code")

        accepted_sample = len(reason_codes) == 0
        quality_score = max(0.0, 1.0 - len(reason_codes) * 0.1)

        return QualityAssessment(
            assessment_id=f"qa-{sample.normalized_sample_id}",
            sample_id=sample.normalized_sample_id,
            accepted=accepted_sample,
            quality_score=round(quality_score, 3),
            reason_codes=list(dict.fromkeys(reason_codes)),
            detected_artifacts=artifacts,
            missingness=round(missingness, 3),
            policy_version=self.version,
            source_ids=list(sample.source_provenance),
        )

    def assess_window(
        self,
        window: ReplayWindow,
        sample_assessments: dict[str, QualityAssessment],
    ) -> QualityAssessment:
        reason_codes: list[str] = []
        accepted = 0
        rejected = 0
        accepted_scores: list[float] = []
        accepted_ids: list[str] = []

        for sample_id in window.ordered_sample_ids:
            assessment = sample_assessments.get(sample_id)
            if assessment is None:
                rejected += 1
                continue
            if assessment.accepted:
                accepted += 1
                accepted_scores.append(assessment.quality_score)
                accepted_ids.extend(assessment.source_ids)
            else:
                rejected += 1
                for code in assessment.reason_codes:
                    if code.startswith("fc11_"):
                        reason_codes.append(code)

        total = accepted + rejected
        if accepted < self.min_accepted_sample_count:
            reason_codes.append("fc11_insufficient_window_coverage")

        accepted_window = accepted >= self.min_accepted_sample_count
        quality_score = 0.0 if not accepted else _mean(accepted_scores)
        return QualityAssessment(
            assessment_id=f"wa-{window.window_id}",
            window_id=window.window_id,
            accepted=accepted_window,
            quality_score=round(quality_score, 3),
            reason_codes=list(dict.fromkeys(reason_codes)),
            detected_artifacts=[],
            missingness=round(rejected / max(1, total), 3),
            policy_version=self.version,
            source_ids=accepted_ids,
        )


def _mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)
