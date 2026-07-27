"""Deterministic robust statistics for personal calibration baselines."""

from __future__ import annotations

import math
from typing import Any


def _sorted_values(values: list[float]) -> list[float]:
    """Return a sorted list of finite floats."""
    return sorted(v for v in values if v is not None and not math.isnan(v))


def median(values: list[float]) -> float:
    """Deterministic median."""
    ordered = _sorted_values(values)
    n = len(ordered)
    if n == 0:
        return 0.0
    if n % 2 == 1:
        return ordered[n // 2]
    return (ordered[n // 2 - 1] + ordered[n // 2]) / 2.0


def quantile(values: list[float], q: float) -> float:
    """Deterministic linear-interpolation quantile."""
    ordered = _sorted_values(values)
    n = len(ordered)
    if n == 0:
        return 0.0
    if n == 1:
        return ordered[0]
    pos = q * (n - 1)
    low = int(math.floor(pos))
    high = int(math.ceil(pos))
    if low == high:
        return ordered[low]
    frac = pos - low
    return ordered[low] + frac * (ordered[high] - ordered[low])


def quantiles(values: list[float], names: list[str], qs: list[float]) -> dict[str, float]:
    """Return named quantiles."""
    return {name: quantile(values, q) for name, q in zip(names, qs, strict=True)}


def mad(values: list[float]) -> float:
    """Median absolute deviation scaled to be comparable to std-dev."""
    m = median(values)
    abs_devs = [abs(v - m) for v in values if v is not None and not math.isnan(v)]
    return 1.4826 * median(abs_devs) if abs_devs else 0.0


def iqr(values: list[float]) -> float:
    """Interquartile range (Q3 - Q1)."""
    return quantile(values, 0.75) - quantile(values, 0.25)


def robust_min(values: list[float]) -> float:
    """Lower 2.5% bounded quantile."""
    return quantile(values, 0.025)


def robust_max(values: list[float]) -> float:
    """Upper 97.5% bounded quantile."""
    return quantile(values, 0.975)


def compute_baseline_stats(values: list[float]) -> dict[str, Any]:
    """Compute central tendency, dispersion, and bounded quantiles."""
    clean = [v for v in values if v is not None and not math.isnan(v)]
    if not clean:
        return {
            "central_tendency": 0.0,
            "dispersion": 0.0,
            "robust_min": 0.0,
            "robust_max": 0.0,
            "selected_quantiles": {},
            "distribution_shape": {"empty": True},
        }
    m = median(clean)
    dispersion = mad(clean)
    if dispersion < 1e-12:
        dispersion = 0.0
    return {
        "central_tendency": m,
        "dispersion": dispersion,
        "robust_min": robust_min(clean),
        "robust_max": robust_max(clean),
        "selected_quantiles": quantiles(
            clean,
            ["q0.025", "q0.25", "q0.50", "q0.75", "q0.975"],
            [0.025, 0.25, 0.50, 0.75, 0.975],
        ),
        "distribution_shape": {"iqr": iqr(clean), "count": len(clean)},
    }


def percentile_rank(values: list[float], value: float) -> float:
    """Return the percentile position of `value` in `values`."""
    clean = _sorted_values(values)
    n = len(clean)
    if n == 0:
        return 0.0
    below = sum(1 for v in clean if v < value)
    equal = sum(1 for v in clean if v == value)
    return (below + 0.5 * equal) / n


def zero_dispersion(value: float) -> bool:
    """Return True when dispersion is effectively zero."""
    return abs(value) < 1e-12
