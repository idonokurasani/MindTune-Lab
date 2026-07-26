"""Deterministic replay clock for CLM-02."""

from __future__ import annotations

from dataclasses import dataclass

from mpe.runtime import Clock


@dataclass
class ReplayClock(Clock):
    """A deterministic clock that advances only by source/manifest time.

    ``now()`` returns the semantic replay time.  It starts at
    ``source_start_timestamp`` and advances by ``sample_interval`` on each
    ``advance()`` call.  ``scale`` is an execution-speed hint for an external
    playback scheduler and never affects values returned by ``now()``.
    """

    source_start_timestamp: float = 0.0
    sample_interval: float = 0.1
    scale: float = 1.0

    def __post_init__(self) -> None:
        self._time = self.source_start_timestamp
        self._step = self.sample_interval

    def set_time(self, t: float) -> None:
        """Set the replay time deterministically; never uses wall-clock time."""
        self._time = t

    def advance(self, steps: float = 1.0) -> None:
        """Advance the semantic time by ``sample_interval * steps``.

        ``scale`` is intentionally not used here; it belongs to an external
        execution scheduler, not the semantic replay clock.
        """
        self._time += self.sample_interval * steps

    def now(self) -> float:
        return self._time
