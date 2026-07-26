"""Deterministic replay clock for CLM-02."""

from __future__ import annotations

from dataclasses import dataclass

from mpe.runtime import Clock


@dataclass
class ReplayClock(Clock):
    """A deterministic clock that advances only from manifest/source timestamps.

    No wall-clock call is made.  The clock starts at ``source_start_timestamp``
    and advances by ``sample_interval`` on each ``advance()`` call.  ``scale``
    supports accelerated replay without changing semantic event times.
    """

    source_start_timestamp: float = 0.0
    sample_interval: float = 0.1
    scale: float = 1.0

    def __post_init__(self) -> None:
        self._time = self.source_start_timestamp
        self._step = self.sample_interval * self.scale

    def set_time(self, t: float) -> None:
        """Set the replay time deterministically; never uses wall-clock time."""
        self._time = t

    def advance(self, steps: float = 1.0) -> None:
        """Advance by ``sample_interval * scale * steps``."""
        self._time += self._step * steps

    def now(self) -> float:
        return self._time
