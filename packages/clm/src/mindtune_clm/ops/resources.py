"""Resource limits and ownership."""

from __future__ import annotations

from typing import Any

from .metrics import MetricsStore


class ResourceLimitExceeded(Exception):
    """Raised when a resource limit is exceeded."""

    def __init__(self, resource: str, limit: int, current: int) -> None:
        self.resource = resource
        self.limit = limit
        self.current = current
        super().__init__(f"Resource {resource} exceeded limit {limit} (current {current})")


class ResourceManager:
    """Tracks active resource ownership."""

    def __init__(self, limits: dict[str, int], metrics: MetricsStore | None = None) -> None:
        self.limits = limits
        self._owned: dict[str, str | None] = dict.fromkeys(limits)
        self._counts: dict[str, int] = dict.fromkeys(limits, 0)
        self.metrics = metrics or MetricsStore()

    def acquire(self, resource: str, owner: str) -> None:
        if resource not in self.limits:
            raise KeyError(f"Unknown resource {resource}")
        if self._owned.get(resource) and self._owned[resource] != owner:
            raise ResourceLimitExceeded(resource, 1, 1)
        if self._counts[resource] >= self.limits[resource]:
            self.metrics.inc(f"resource_limit_exceeded:{resource}")
            raise ResourceLimitExceeded(resource, self.limits[resource], self._counts[resource])
        self._owned[resource] = owner
        self._counts[resource] += 1
        self.metrics.inc(f"resource_acquired:{resource}")

    def release(self, resource: str, owner: str) -> None:
        if resource not in self.limits:
            return
        if self._owned.get(resource) == owner:
            self._owned[resource] = None
        if self._counts[resource] > 0:
            self._counts[resource] -= 1

    def available(self, resource: str) -> int:
        return self.limits.get(resource, 0) - self._counts.get(resource, 0)

    def status(self) -> dict[str, Any]:
        return {
            "limits": self.limits,
            "counts": dict(self._counts),
            "owners": dict(self._owned),
        }
