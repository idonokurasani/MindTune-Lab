"""Deterministic, auditable randomization for CLM-08."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from itertools import permutations
from typing import Any


@dataclass(frozen=True)
class Allocation:
    """One unit-level treatment allocation."""

    unit_id: str
    condition_id: str
    period: int
    sequence_order: int
    stratum: str | None = None
    seed: int | None = None
    algorithm: str = ""
    algorithm_version: str = "1.0"

    def as_dict(self) -> dict[str, Any]:
        return {
            "unit_id": self.unit_id,
            "condition_id": self.condition_id,
            "period": self.period,
            "sequence_order": self.sequence_order,
            "stratum": self.stratum,
            "seed": self.seed,
            "algorithm": self.algorithm,
            "algorithm_version": self.algorithm_version,
        }


def _weights_from_ratio(
    conditions: list[str], ratio: dict[str, float] | None
) -> list[float]:
    if not ratio:
        return [1.0] * len(conditions)
    return [ratio.get(c, 1.0) for c in conditions]


def simple_randomization(
    units: list[str],
    conditions: list[str],
    seed: int,
    allocation_ratio: dict[str, float] | None = None,
) -> list[Allocation]:
    """Simple randomization with a reproducible seed."""
    rng = random.Random(seed)
    weights = _weights_from_ratio(conditions, allocation_ratio)
    total = sum(weights)
    weighted = [(u, w / total) for u, w in zip(conditions, weights, strict=True)]
    allocations: list[Allocation] = []
    for idx, unit in enumerate(units):
        condition = rng.choices([c for c, _ in weighted], [w for _, w in weighted], k=1)[0]
        allocations.append(
            Allocation(
                unit_id=unit,
                condition_id=condition,
                period=1,
                sequence_order=idx,
                seed=seed,
                algorithm="simple",
            )
        )
    return allocations


def blocked_randomization(
    units: list[str],
    conditions: list[str],
    seed: int,
    block_size: int | None = None,
    allocation_ratio: dict[str, float] | None = None,
) -> list[Allocation]:
    """Blocked randomization; block size defaults to LCM of weights."""
    rng = random.Random(seed)
    weights = _weights_from_ratio(conditions, allocation_ratio)
    if block_size is None:
        block_size = math.lcm(*[int(w * 100) for w in weights]) if any(w != int(w) for w in weights) else math.lcm(*[int(w) for w in weights])
        if not block_size or block_size > len(units):
            block_size = len(conditions)
    allocations: list[Allocation] = []
    block: list[str] = []
    for idx, unit in enumerate(units):
        if not block:
            block = []
            for cond, w in zip(conditions, weights, strict=True):
                block.extend([cond] * int(w))
            while len(block) < block_size:
                block.extend(block)
            block = block[:block_size]
            rng.shuffle(block)
        condition = block.pop()
        allocations.append(
            Allocation(
                unit_id=unit,
                condition_id=condition,
                period=1,
                sequence_order=idx,
                seed=seed,
                algorithm="blocked",
            )
        )
    return allocations


def stratified_randomization(
    units: list[str],
    conditions: list[str],
    seed: int,
    strata: dict[str, str] | None = None,
    allocation_ratio: dict[str, float] | None = None,
) -> list[Allocation]:
    """Stratified randomization within named strata."""
    strata = strata or dict.fromkeys(units, "all")
    allocations: list[Allocation] = []
    grouped: dict[str, list[str]] = {}
    for unit in units:
        grouped.setdefault(strata.get(unit, "all"), []).append(unit)
    for stratum, stratum_units in grouped.items():
        for alloc in simple_randomization(
            stratum_units,
            conditions,
            seed + hash(stratum) % (2**31),
            allocation_ratio=allocation_ratio,
        ):
            allocations.append(
                Allocation(
                    unit_id=alloc.unit_id,
                    condition_id=alloc.condition_id,
                    period=1,
                    sequence_order=alloc.sequence_order,
                    stratum=stratum,
                    seed=seed,
                    algorithm="stratified",
                )
            )
    return allocations


def latin_square_ordering(conditions: list[str], seed: int) -> list[list[str]]:
    """Generate a Latin square sequence of condition orders."""
    rng = random.Random(seed)
    base = list(conditions)
    n = len(base)
    rows = [[base[(i + j) % n] for i in range(n)] for j in range(n)]
    rng.shuffle(rows)
    return rows


def crossover_sequence_randomization(
    units: list[str],
    conditions: list[str],
    seed: int,
    periods: int | None = None,
) -> list[Allocation]:
    """Randomized crossover sequence assignment."""
    rng = random.Random(seed)
    if periods is None:
        periods = len(conditions)
    sequences = list(permutations(conditions))
    rng.shuffle(sequences)
    allocations: list[Allocation] = []
    for idx, unit in enumerate(units):
        seq = sequences[idx % len(sequences)]
        for period in range(periods):
            condition = seq[period % len(seq)]
            allocations.append(
                Allocation(
                    unit_id=unit,
                    condition_id=condition,
                    period=period + 1,
                    sequence_order=idx,
                    seed=seed,
                    algorithm="crossover",
                )
            )
    return allocations
