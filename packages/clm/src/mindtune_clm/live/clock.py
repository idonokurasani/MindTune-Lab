"""Semantic and wall-clock tracking for the CLM-04 live gateway.

The gateway is driven by semantic packet timestamps so that tests and hardware
smoke runs are deterministic and wall-clock independent.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class LiveClock:
    """A live clock that exposes both wall-clock and semantic time.

    ``semantic_time`` is advanced explicitly by the gateway and never drifts
    with the host clock.  ``wall_time`` is captured once at reset for logging
    only.
    """

    start_semantic: float = 0.0
    _semantic: float = field(default=0.0, init=False, repr=False)
    _wall_start: float | None = field(default=None, init=False, repr=False)

    def reset(self, start_semantic: float = 0.0) -> None:
        """Reset semantic time to the first packet timestamp."""
        self.start_semantic = start_semantic
        self._semantic = start_semantic
        self._wall_start = None

    def start_wall(self) -> None:
        """Capture the host wall-clock start reference."""
        self._wall_start = time.monotonic()

    def advance(self, step: float) -> None:
        """Advance semantic time by ``step`` seconds."""
        self._semantic += step

    def set_semantic(self, t: float) -> None:
        """Set semantic time directly (monotonicity is the caller's duty)."""
        self._semantic = t

    @property
    def semantic_time(self) -> float:
        """Return the current semantic time."""
        return self._semantic

    @property
    def wall_elapsed(self) -> float | None:
        """Return elapsed wall-clock seconds since reset, or None if not started."""
        if self._wall_start is None:
            return None
        return time.monotonic() - self._wall_start
