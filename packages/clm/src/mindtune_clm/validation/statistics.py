"""Transparent, dependency-light statistical methods for CLM-08."""

from __future__ import annotations

import math
import random
import statistics
from typing import Any, Callable


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _sd(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    return statistics.stdev(values)


def descriptive_summary(values: list[float]) -> dict[str, Any]:
    if not values:
        return {"n": 0, "mean": 0.0, "median": 0.0, "sd": 0.0, "min": 0.0, "max": 0.0}
    return {
        "n": len(values),
        "mean": _mean(values),
        "median": statistics.median(values),
        "sd": _sd(values),
        "min": min(values),
        "max": max(values),
    }


def paired_mean_difference(pairs: list[tuple[float, float]]) -> tuple[float, float]:
    """Mean and standard error of paired differences."""
    diffs = [a - b for a, b in pairs]
    if not diffs:
        return (0.0, 0.0)
    mean = _mean(diffs)
    se = _sd(diffs) / math.sqrt(len(diffs)) if len(diffs) > 1 else 0.0
    return (mean, se)


def paired_median_difference(pairs: list[tuple[float, float]]) -> float:
    diffs = [a - b for a, b in pairs]
    if not diffs:
        return 0.0
    return statistics.median(diffs)


def risk_difference(group1: list[int], group2: list[int]) -> tuple[float, float]:
    """Risk difference with normal-approximation SE."""
    n1, n2 = len(group1), len(group2)
    if n1 == 0 or n2 == 0:
        return (0.0, 0.0)
    r1 = sum(group1) / n1
    r2 = sum(group2) / n2
    rd = r1 - r2
    se = math.sqrt((r1 * (1 - r1) / n1) + (r2 * (1 - r2) / n2))
    return (rd, se)


def odds_ratio(group1: list[int], group2: list[int]) -> tuple[float, float, float]:
    """Odds ratio with 95% log-CI using 0.5 continuity correction."""
    a = sum(group1) + 0.5
    b = len(group1) - sum(group1) + 0.5
    c = sum(group2) + 0.5
    d = len(group2) - sum(group2) + 0.5
    or_value = (a * d) / (b * c)
    se_log = math.sqrt(1 / a + 1 / b + 1 / c + 1 / d)
    log_or = math.log(or_value)
    ci_low = math.exp(log_or - 1.96 * se_log)
    ci_high = math.exp(log_or + 1.96 * se_log)
    return (or_value, ci_low, ci_high)


def bootstrap_ci(
    data: list[float],
    statistic: Callable[[list[float]], float] | None = None,
    n_boot: int = 2000,
    ci: float = 0.95,
    seed: int | None = None,
) -> tuple[float, float, float]:
    """Percentile bootstrap confidence interval."""
    rng = random.Random(seed)
    stat = statistic or _mean
    if not data:
        return (0.0, 0.0, 0.0)
    estimates = []
    for _ in range(n_boot):
        sample = [rng.choice(data) for _ in data]
        estimates.append(stat(sample))
    estimates.sort()
    alpha = 1 - ci
    lower_idx = int(alpha / 2 * n_boot)
    upper_idx = int((1 - alpha / 2) * n_boot) - 1
    lower_idx = max(0, min(lower_idx, n_boot - 1))
    upper_idx = max(0, min(upper_idx, n_boot - 1))
    return (stat(data), estimates[lower_idx], estimates[upper_idx])


def permutation_test(
    group1: list[float], group2: list[float], n_perm: int = 2000, seed: int | None = None
) -> tuple[float, float]:
    """Permutation p-value for the difference in means."""
    rng = random.Random(seed)
    pooled = list(group1) + list(group2)
    if not pooled:
        return (0.0, 1.0)
    observed = _mean(group1) - _mean(group2)
    n1 = len(group1)
    count = 0
    for _ in range(n_perm):
        rng.shuffle(pooled)
        perm1 = pooled[:n1]
        perm2 = pooled[n1:]
        diff = _mean(perm1) - _mean(perm2)
        if abs(diff) >= abs(observed):
            count += 1
    p = count / n_perm
    return (observed, p)


def exact_binomial(k: int, n: int, p: float = 0.5) -> tuple[float, float]:
    """Exact two-sided p-value for binomial test."""
    if n == 0:
        return (0.0, 1.0)
    prob_tail = 0.0
    for i in range(k + 1):
        prob_tail += math.comb(n, i) * (p ** i) * ((1 - p) ** (n - i))
    p_value = 2 * min(prob_tail, 1 - prob_tail + math.comb(n, k) * (p ** k) * ((1 - p) ** (n - k)))
    return (k / n, min(1.0, p_value))


def proportion_ci(k: int, n: int, method: str = "wilson", ci: float = 0.95) -> tuple[float, float, float]:
    """Wilson score interval for a proportion."""
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = k / n
    z = 1.96 if ci == 0.95 else 2.576
    if method == "wilson":
        denom = 1 + z * z / n
        centre = (p + z * z / (2 * n)) / denom
        width = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n) / denom
        return (p, max(0.0, centre - width), min(1.0, centre + width))
    # Wald fallback
    se = math.sqrt(p * (1 - p) / n)
    return (p, max(0.0, p - z * se), min(1.0, p + z * se))


def standardized_effect_size(group1: list[float], group2: list[float]) -> float:
    """Cohen's d for two independent groups."""
    return cohens_d(group1, group2)


def cohens_d(group1: list[float], group2: list[float]) -> float:
    n1, n2 = len(group1), len(group2)
    if n1 == 0 or n2 == 0:
        return 0.0
    m1, m2 = _mean(group1), _mean(group2)
    sd1, sd2 = _sd(group1), _sd(group2)
    pooled = math.sqrt(((n1 - 1) * sd1 ** 2 + (n2 - 1) * sd2 ** 2) / (n1 + n2 - 2)) if (n1 + n2 - 2) > 0 else 0.0
    if pooled == 0:
        return 0.0
    return (m1 - m2) / pooled


def within_participant_aggregation(rows: list[Any], participant_id: str, value_field: str) -> float:
    """Return the participant-level mean of a value field."""
    values = [getattr(r, value_field) for r in rows if r.participant_id == participant_id and getattr(r, value_field) is not None]
    if not values:
        return 0.0
    return _mean([float(v) for v in values])


def cluster_aware_bootstrap(
    clusters: dict[str, list[float]],
    statistic: Callable[[list[float]], float],
    n_boot: int = 2000,
    seed: int | None = None,
) -> tuple[float, float, float]:
    """Bootstrap by resampling clusters (e.g. participants) with replacement."""
    rng = random.Random(seed)
    cluster_names = list(clusters.keys())
    values = [v for lst in clusters.values() for v in lst]
    point = statistic(values)
    estimates = []
    for _ in range(n_boot):
        sample: list[float] = []
        for _ in range(len(cluster_names)):
            chosen = rng.choice(cluster_names)
            sample.extend(clusters[chosen])
        estimates.append(statistic(sample))
    estimates.sort()
    lower_idx = int(0.025 * n_boot)
    upper_idx = int(0.975 * n_boot) - 1
    lower_idx = max(0, min(lower_idx, n_boot - 1))
    upper_idx = max(0, min(upper_idx, n_boot - 1))
    return (point, estimates[lower_idx], estimates[upper_idx])
