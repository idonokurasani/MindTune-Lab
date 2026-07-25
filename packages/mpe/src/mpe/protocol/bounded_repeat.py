"""Bounded-repeat mechanics shared by protocol runners.

The mechanics (repeat counting, requeue position, cap enforcement, repeat
metadata propagation) are invariant.  The decision of *whether* a trial must
be repeated stays protocol-specific and is supplied as a `RepeatDecision`.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")

REASON_NONE = "none"
SOURCE_BEHAVIOR = "behavior"
SOURCE_LATENCY = "latency"


@dataclass(frozen=True)
class RepeatDecision:
    """Protocol-specific verdict about repeating the trial that just ran."""

    should_repeat: bool
    adaptation_source: str | None = None
    reason_code: str = REASON_NONE

    @staticmethod
    def none() -> RepeatDecision:
        return RepeatDecision(should_repeat=False)


@dataclass(frozen=True)
class RepeatMetadata:
    """Repeat information carried on the `trial_created` payload."""

    repeat_count: int
    adaptation_source: str | None
    cap: int


class BoundedRepeatStep(Generic[T]):
    """One planned execution of an item, awaiting a repeat decision."""

    def __init__(self, item: T, metadata: RepeatMetadata, repeats_used: int) -> None:
        self.item = item
        self.metadata = metadata
        self.repeats_used = repeats_used
        self.decision: RepeatDecision = RepeatDecision.none()

    def record(self, decision: RepeatDecision) -> None:
        """Record the protocol-specific repeat decision for this step."""
        self.decision = decision


class BoundedRepeatPlan(Generic[T]):
    """Deterministic item plan with at most `cap` repeats per item.

    A repeat is requeued immediately after the trial that triggered it, which
    guarantees termination once the cap is reached.
    """

    def __init__(self, items: Sequence[T], cap: int, key: Callable[[T], str]) -> None:
        self._plan: list[T] = list(items)
        self._cap = cap
        self._key = key
        self._executed: dict[str, int] = {}

    @property
    def planned_items(self) -> list[T]:
        """The plan as expanded so far (repeats included)."""
        return list(self._plan)

    def __iter__(self) -> Iterator[BoundedRepeatStep[T]]:
        index = 0
        pending: RepeatDecision | None = None
        while index < len(self._plan):
            item = self._plan[index]
            item_key = self._key(item)
            repeats_used = self._executed.get(item_key, 0)
            metadata = RepeatMetadata(
                repeat_count=repeats_used,
                adaptation_source=pending.adaptation_source if pending is not None else None,
                cap=self._cap,
            )
            step: BoundedRepeatStep[T] = BoundedRepeatStep(item, metadata, repeats_used)
            yield step

            self._executed[item_key] = repeats_used + 1
            decision = step.decision
            if decision.should_repeat and repeats_used < self._cap:
                self._plan.insert(index + 1, item)
                pending = decision
            else:
                pending = None
            index += 1
