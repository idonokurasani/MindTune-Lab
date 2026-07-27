"""Operational metrics collection."""

from __future__ import annotations

import json
import time
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class MetricsStore:
    """In-memory operational metrics store."""

    counters: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    histograms: dict[str, list[float]] = field(default_factory=lambda: defaultdict(list))
    gauges: dict[str, float] = field(default_factory=dict)
    start_time: float = field(default_factory=time.time)

    def inc(self, name: str, value: int = 1) -> None:
        self.counters[name] += value

    def observe(self, name: str, value: float) -> None:
        self.histograms[name].append(value)

    def set_gauge(self, name: str, value: float) -> None:
        self.gauges[name] = value

    def uptime_seconds(self) -> float:
        return time.time() - self.start_time

    @staticmethod
    def _is_sensitive(name: str) -> bool:
        lower = name.lower()
        return any(
            k in lower
            for k in ("participant", "cognitive", "hebrew_performance", "participant_identity")
        )

    def to_prometheus(self) -> str:
        lines = ["# CLM-09 operational metrics"]
        lines.append(f"clm09_process_uptime_seconds {self.uptime_seconds():.3f}")
        for name, value in self.counters.items():
            if self._is_sensitive(name):
                continue
            safe = name.replace("-", "_").replace(" ", "_")
            lines.append(f"clm09_{safe}_total {value}")
        for name, values in self.histograms.items():
            if not values or self._is_sensitive(name):
                continue
            safe = name.replace("-", "_").replace(" ", "_")
            lines.append(f"clm09_{safe}_sum {sum(values):.6f}")
            lines.append(f"clm09_{safe}_count {len(values)}")
        for name, value in self.gauges.items():  # type: ignore[assignment]
            if self._is_sensitive(name):
                continue
            safe = name.replace("-", "_").replace(" ", "_")
            lines.append(f"clm09_{safe} {value}")
        return "\n".join(lines) + "\n"

    def to_dict(self) -> dict[str, Any]:
        return {
            "counters": dict(self.counters),
            "gauges": self.gauges,
            "histograms": {k: {"count": len(v), "sum": sum(v), "avg": sum(v) / len(v) if v else 0.0} for k, v in self.histograms.items()},
            "uptime_seconds": self.uptime_seconds(),
        }

    def dump(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, sort_keys=True, default=str)
