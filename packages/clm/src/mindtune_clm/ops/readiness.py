"""Readiness determination for CLM-09."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .config import CLM09Config, DeploymentMode
from .migrations import MigrationManager


@dataclass
class ReadinessResult:
    """Readiness state."""

    ready: bool
    blockers: list[str] = field(default_factory=list)
    components: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"ready": self.ready, "blockers": self.blockers, "components": self.components}


def check_readiness(config: CLM09Config) -> ReadinessResult:
    """Check application readiness."""
    result = ReadinessResult(ready=True)

    # storage writable
    paths = config.storage_paths()
    for label, path in paths.items():
        try:
            path.mkdir(parents=True, exist_ok=True)
            probe = path / ".ready_probe"
            probe.write_text("ok")
            probe.unlink()
            result.components[label] = "ok"
        except OSError as exc:
            result.ready = False
            result.blockers.append(f"storage.{label} not writable: {exc}")
            result.components[label] = "error"

    # migrations current
    db_path = Path(config.event_store.path) / "clm09.db"
    mm = MigrationManager(db_path)
    status = mm.current()
    if status["status"] == "pending":
        result.ready = False
        result.blockers.append("migrations pending")
        result.components["migrations"] = "pending"
    else:
        result.components["migrations"] = "current"

    # event store
    event_dir = Path(config.event_store.path)
    corruption_marker = event_dir / ".corruption_detected"
    if corruption_marker.exists():
        result.ready = False
        result.blockers.append("event store corruption detected")
        result.components["event_store"] = "corrupted"
    else:
        result.components["event_store"] = "ok"

    # required assets
    if config.deployment_mode in (DeploymentMode.RESEARCH_LOCAL, DeploymentMode.DEVELOPMENT):
        result.components["assets"] = "ok"
    else:
        result.components["assets"] = "not_required"

    # playback
    result.components["playback"] = config.playback.backend

    # sensor
    if config.sensor_access.fc11_enabled:
        result.components["sensor"] = "fc11_enabled"
    else:
        result.components["sensor"] = "disabled"

    # locks functional
    locks_dir = Path(config.storage.root) / "locks"
    try:
        locks_dir.mkdir(parents=True, exist_ok=True)
        result.components["locks"] = "ok"
    except OSError as exc:
        result.ready = False
        result.blockers.append(f"locks directory not usable: {exc}")
        result.components["locks"] = "error"

    return result
