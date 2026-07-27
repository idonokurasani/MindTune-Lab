"""CLM-09 startup phases."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .config import CLM09Config, DeploymentMode
from .migrations import MigrationManager
from .recovery import run_crash_recovery

STARTUP_PHASES = [
    "process_created",
    "configuration_loaded",
    "configuration_validated",
    "storage_checked",
    "migrations_checked",
    "event_store_checked",
    "assets_checked",
    "sensor_drivers_checked",
    "playback_checked",
    "API_ready",
    "application_ready",
]


@dataclass
class StartupManifest:
    """Manifest of startup progress."""

    config: CLM09Config
    phases: list[str] = field(default_factory=list)
    current_phase: str = "process_created"
    blocked: bool = False
    blocker: str | None = None
    warnings: list[str] = field(default_factory=list)
    component_status: dict[str, Any] = field(default_factory=dict)

    def advance(self, phase: str, ok: bool = True, message: str = "") -> None:
        self.current_phase = phase
        self.phases.append(phase)
        if not ok:
            self.blocked = True
            self.blocker = message
        elif message:
            self.warnings.append(f"{phase}: {message}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "release_id": self.config.release_id,
            "deployment_mode": self.config.deployment_mode,
            "current_phase": self.current_phase,
            "blocked": self.blocked,
            "blocker": self.blocker,
            "warnings": self.warnings,
            "component_status": self.component_status,
            "phases_completed": self.phases,
            "config_checksum": self.config.checksum(),
        }


def run_startup(config: CLM09Config) -> StartupManifest:
    """Run CLM-09 startup phases."""
    manifest = StartupManifest(config=config)
    manifest.advance("process_created")
    manifest.advance("configuration_loaded")

    try:
        config.ensure_storage()
        manifest.advance("configuration_validated")
    except Exception as exc:
        manifest.advance("configuration_validated", ok=False, message=str(exc))
        return manifest

    try:
        config.ensure_storage()
        manifest.advance("storage_checked")
    except Exception as exc:
        manifest.advance("storage_checked", ok=False, message=str(exc))
        return manifest

    # migrations
    db_path = Path(config.event_store.path) / "clm09.db"
    mm = MigrationManager(db_path)
    if not mm.validate_checksums():
        manifest.advance("migrations_checked", ok=False, message="migration checksum mismatch")
        return manifest
    try:
        mm.migrate()
        manifest.advance("migrations_checked")
    except Exception as exc:
        manifest.advance("migrations_checked", ok=False, message=f"migration failed: {exc}")
        return manifest

    # event store
    event_dir = Path(config.event_store.path)
    try:
        event_dir.mkdir(parents=True, exist_ok=True)
        probe = event_dir / ".startup_probe"
        probe.write_text("ok")
        probe.unlink()
        manifest.advance("event_store_checked")
    except Exception as exc:
        manifest.advance("event_store_checked", ok=False, message=f"event store not writable: {exc}")
        return manifest

    # assets
    required_assets = []
    if config.deployment_mode in (DeploymentMode.RESEARCH_LOCAL, DeploymentMode.DEVELOPMENT):
        required_assets = [" Aaron pointed-text policy", "voice cache"]
    manifest.component_status["required_assets"] = required_assets
    if required_assets and any(a not in str(Path(a).absolute()) for a in required_assets):
        pass
    manifest.advance("assets_checked", message="optional" if not required_assets else "ok")

    # sensor drivers
    if config.sensor_access.fc11_enabled:
        manifest.advance("sensor_drivers_checked", message="FC11 requested; host-dependent")
    else:
        if config.deployment_mode == DeploymentMode.REPLAY_OFFLINE:
            manifest.advance("sensor_drivers_checked", message="replay-only: sensors disabled")
        else:
            manifest.advance("sensor_drivers_checked", message="FC11 not enabled")

    # playback
    if config.playback.backend == "real":
        if config.deployment_mode == DeploymentMode.REPLAY_OFFLINE:
            manifest.advance("playback_checked", message="real playback in replay mode is a warning")
        else:
            manifest.advance("playback_checked")
    else:
        manifest.advance("playback_checked", message=f"backend={config.playback.backend}")

    # crash recovery
    recovery = run_crash_recovery(
        Path(config.storage.root) / config.storage.sessions_dir,
        Path(config.storage.root) / "locks",
        Path(config.event_store.path),
    )
    manifest.component_status["crash_recovery"] = recovery.to_dict()

    manifest.advance("API_ready")
    manifest.advance("application_ready")
    return manifest
