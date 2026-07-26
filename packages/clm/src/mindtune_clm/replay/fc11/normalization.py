"""FC11 deterministic normalization and unit conversion for CLM-02B."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from mindtune_clm.replay.models import NormalizedSensorSample, SensorSample
from mindtune_clm.replay.normalization import NormalizationPolicy
from mindtune_clm.replay.source import RecordedSensorSource


def _is_missing_value(cell: Any) -> bool:
    if cell is None:
        return True
    if isinstance(cell, str):
        return cell == "" or cell.lower() in {"nan", "null", "none", "na"}
    if isinstance(cell, float) and math.isnan(cell):
        return True
    return False


def _normalize_quality_label(raw: str | None) -> str | None:
    """Map FC11 numeric signal quality to stable labels.

    Empty values are treated as not reported.  Numeric 0-2 poor, 3 fair, 4-5 good.
    """
    if raw is None or raw == "":
        return None
    if raw.isdigit():
        code = int(raw)
        if code <= 2:
            return "poor"
        if code == 3:
            return "fair"
        return "good"
    return raw.lower()


def _scale_value(raw: Any, ch: str) -> tuple[float | None, str]:
    """Convert a raw FC11 channel string to a normalized float.

    Returns (value, operation).  Percentage channels are mapped to [0, 1].
    """
    if _is_missing_value(raw):
        return None, f"missing_channel:{ch}"
    try:
        numeric = float(raw)
    except (ValueError, TypeError):
        return None, f"malformed_value:{ch}"
    if ch in ("attention_score_smoothed", "meditation_score_smoothed"):
        return numeric / 100.0, f"percentage_to_unit:{ch}"
    if ch in ("artifact_flag", "movement_flag", "packet_loss"):
        return 1.0 if numeric >= 1.0 else 0.0, f"boolean:{ch}"
    if ch == "packet_index":
        return numeric, f"integer:{ch}"
    return numeric, f"scaled:{ch}"


@dataclass(frozen=True)
class FC11NormalizationPolicy(NormalizationPolicy):
    """FC11-specific normalization policy that preserves provenance."""

    policy_id: str = "mindtune_clm.replay.fc11.normalization.v1"
    version: str = "1.0.0"
    required_channels: list[str] = field(default_factory=lambda: ["eeg_scaled"])

    def normalize(  # noqa: C901
        self,
        raw_samples: list[SensorSample],
        source: RecordedSensorSource,
    ) -> list[NormalizedSensorSample]:
        normalized: list[NormalizedSensorSample] = []
        seen_timestamps: set[float] = set()
        last_timestamp: float | None = None

        for sample in raw_samples:
            ops: list[str] = []
            source_ts = sample.source_timestamp
            missing_indicators: dict[str, bool] = {}
            channel_values: dict[str, float | None] = {}

            if not sample.parsed:
                ops.append(f"parse_failed:{sample.parse_reason or 'unknown'}")
            else:
                ops.append("parsed")

            quality_label = _normalize_quality_label(sample.raw_quality)
            if quality_label in ("poor", "bad"):
                ops.append("fc11_poor_signal")
            elif quality_label == "fair":
                ops.append("fc11_fair_signal")
            elif quality_label == "good":
                ops.append("fc11_good_signal")

            replay_ts: float | None = None
            if source_ts is not None:
                replay_ts = source_ts - source.source_start_timestamp

                if last_timestamp is not None and source_ts < last_timestamp:
                    ops.append("fc11_timestamp_regression")
                    source_ts = None
                    replay_ts = None
                elif source_ts in seen_timestamps:
                    ops.append("fc11_duplicate_timestamp")
                    source_ts = None
                    replay_ts = None
                else:
                    seen_timestamps.add(source_ts)
                    last_timestamp = source_ts

            if source_ts is None and replay_ts is None:
                ops.append("fc11_missing_timestamp")

            for ch in source.channel_names:
                raw = sample.channel_values.get(ch)
                value, op = _scale_value(raw, ch)
                missing_indicators[ch] = value is None
                channel_values[ch] = value
                ops.append(op)

                if ch in self.required_channels and value is None:
                    ops.append("fc11_missing_required_channel")

                if ch == "artifact_flag" and value == 1.0:
                    ops.append("fc11_artifact_flag")
                if ch == "movement_flag" and value == 1.0:
                    ops.append("fc11_movement_detected")
                if ch == "packet_loss" and value == 1.0:
                    ops.append("fc11_packet_loss")

            ns_id = f"ns-{source.source_id}-{sample.source_sample_index}"
            normalized.append(
                NormalizedSensorSample(
                    normalized_sample_id=ns_id,
                    source_sample_index=sample.source_sample_index,
                    source_timestamp=sample.source_timestamp,
                    replay_relative_timestamp=replay_ts,
                    channel_values=channel_values,
                    raw_quality=quality_label,
                    units="normalized",
                    missing_channel_indicators=missing_indicators,
                    normalization_operations=ops,
                    source_provenance=[source.source_id, str(sample.source_sample_index)],
                )
            )

        return normalized
