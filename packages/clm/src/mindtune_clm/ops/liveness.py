"""Liveness probes for CLM-09."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class LivenessProbe:
    """Simple liveness probe."""

    heartbeat_interval_s: float = 5.0
    _last_heartbeat: float = field(init=False, default_factory=time.time)
    _lock: threading.Lock = field(init=False, default_factory=threading.Lock)

    def __post_init__(self) -> None:
        self._last_heartbeat = time.time()

    def beat(self) -> None:
        with self._lock:
            self._last_heartbeat = time.monotonic()

    def is_alive(self) -> bool:
        with self._lock:
            return (time.monotonic() - self._last_heartbeat) < self.heartbeat_interval_s * 3

    def to_dict(self) -> dict[str, Any]:
        return {
            "alive": self.is_alive(),
            "last_heartbeat_age_s": round(time.monotonic() - self._last_heartbeat, 3),
            "heartbeat_interval_s": self.heartbeat_interval_s,
        }
