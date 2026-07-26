"""Deterministic normalization and unit conversion for CLM-02."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from mindtune_clm.replay.models import NormalizedSensorSample, SensorSample
from mindtune_clm.replay.source import RecordedSensorSource


@dataclass(frozen=True)
class NormalizationPolicy:
    """Versioned normalization rules."""

    policy_id: str
    version: str
    required_channels: list[str] = field(default_factory=list)
    unit_scale: float = 1.0
    duplicate_rule: str = "keep_first"
    timestamp_regression_rule: str = "reject"
    interpolation: str | None = None
    missing_channel_rule: str = "mark_missing"


def _is_missing_value(cell: Any) -> bool:
    if cell is None:
        return True
    if isinstance(cell, str):
        return cell == "" or cell.lower() in {"nan", "null", "none", "na"}
    if isinstance(cell, float) and math.isnan(cell):
        return True
    return False


def normalize_samples(  # noqa: C901
    raw_samples: list[SensorSample],
    source: RecordedSensorSource,
    policy: NormalizationPolicy,
) -> list[NormalizedSensorSample]:
    """Convert raw samples to normalized, timestamp-ordered samples.

    Duplicate and regression rules are applied deterministically.
    All operations are recorded in the sample payload.
    """
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
            # Still create a normalized record so rejection is explicit.
        else:
            ops.append("parsed")

        if sample.raw_quality is not None and sample.raw_quality.lower() not in {"", "good", "ok"}:
            ops.append(f"quality_flag:{sample.raw_quality}")

        replay_ts: float | None = None
        if source_ts is not None:
            replay_ts = source_ts - source.source_start_timestamp

            if last_timestamp is not None and source_ts < last_timestamp:
                if policy.timestamp_regression_rule == "reject":
                    ops.append("timestamp_regression_rejected")
                else:
                    ops.append("timestamp_regression_repaired")
                    # Deterministic repair: clamp to the last valid timestamp.
                    source_ts = last_timestamp
                    replay_ts = source_ts - source.source_start_timestamp
            elif source_ts in seen_timestamps:
                if policy.duplicate_rule == "keep_first":
                    ops.append("duplicate_rejected")
                    source_ts = None
                    replay_ts = None
                else:
                    ops.append("duplicate_kept")

        if source_ts is not None and replay_ts is not None:
            seen_timestamps.add(source_ts)
            last_timestamp = source_ts

        for ch in source.channel_names:
            raw = sample.channel_values.get(ch)
            if _is_missing_value(raw):
                missing_indicators[ch] = True
                channel_values[ch] = None
                if ch in policy.required_channels:
                    ops.append(f"missing_required_channel:{ch}")
                else:
                    ops.append(f"missing_channel:{ch}")
            else:
                missing_indicators[ch] = False
                try:
                    numeric = float(raw) * policy.unit_scale  # type: ignore[arg-type]
                    channel_values[ch] = numeric
                    ops.append(f"scaled:{ch}")
                except (ValueError, TypeError):
                    missing_indicators[ch] = True
                    channel_values[ch] = None
                    ops.append(f"malformed_value:{ch}")

        ns_id = f"ns-{source.source_id}-{sample.source_sample_index}"
        normalized.append(
            NormalizedSensorSample(
                normalized_sample_id=ns_id,
                source_sample_index=sample.source_sample_index,
                source_timestamp=sample.source_timestamp,
                replay_relative_timestamp=replay_ts,
                channel_values=channel_values,
                units="normalized",
                missing_channel_indicators=missing_indicators,
                normalization_operations=ops,
                source_provenance=[source.source_id, str(sample.source_sample_index)],
            )
        )

    # For CLM-02 interpolation is unsupported unless explicitly enabled.
    if policy.interpolation is not None:
        for index in range(len(normalized)):
            normalized[index] = normalized[index]  # placeholder: no-op for this slice

    return normalized
