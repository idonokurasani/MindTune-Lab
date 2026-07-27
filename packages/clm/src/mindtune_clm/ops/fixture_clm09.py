"""CLM-09 test and operational fixtures."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from .backup import create_backup
from .config import CLM09Config, DeploymentMode
from .migrations import Migration, MigrationManager
from .readiness import check_readiness
from .release import ReleaseManifest, build_release_manifest
from .startup import run_startup


def minimal_config(tmp_path: Path | None = None, **overrides: Any) -> CLM09Config:
    """Return a minimal CLM-09 config for tests."""
    if tmp_path is None:
        tmp_path = Path(tempfile.mkdtemp(prefix="clm09_"))
    base: dict[str, Any] = {
        "release_id": "clm09-test",
        "deployment_mode": DeploymentMode.RESEARCH_LOCAL,
        "storage": {"root": str(tmp_path / "data")},
        "event_store": {"path": str(tmp_path / "data" / "events")},
        "logging": {"output": str(tmp_path / "data" / "logs" / "clm09.jsonl")},
        "metrics": {"output": str(tmp_path / "data" / "logs" / "metrics.jsonl")},
    }
    merged: dict[str, Any] = _deep_merge(base, overrides)
    return CLM09Config(**merged)


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def sample_migration() -> Migration:
    return Migration(
        version="0001",
        name="initial",
        sql="CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, data TEXT);",
    )


def apply_fixture_migrations(db_path: Path) -> None:
    mm = MigrationManager(db_path)
    mm.register(sample_migration())
    mm.migrate()


__all__ = [
    "minimal_config",
    "sample_migration",
    "apply_fixture_migrations",
    "CLM09Config",
    "DeploymentMode",
    "ReleaseManifest",
    "build_release_manifest",
    "run_startup",
    "check_readiness",
    "create_backup",
    "MigrationManager",
    "Migration",
]
