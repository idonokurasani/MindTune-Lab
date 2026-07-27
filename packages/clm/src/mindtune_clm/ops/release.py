"""Release manifest construction."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ReleaseManifest:
    """Immutable release manifest."""

    release_id: str
    semantic_version: str
    git_commit_sha: str
    dirty_tree: bool
    python_version: str
    node_version: str | None
    package_versions: dict[str, str]
    schema_versions: dict[str, str]
    protocol_versions: dict[str, str]
    clm_component_versions: dict[str, str]
    hebrew_engine_versions: dict[str, str]
    feature_schema_versions: dict[str, str]
    migration_versions: dict[str, str]
    frontend_build_checksum: str | None
    container_image_digest: str | None
    build_timestamp: str
    supported_deployment_targets: list[str]
    provenance: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def checksum(self) -> str:
        payload = json.dumps(self.to_dict(), sort_keys=True, ensure_ascii=True, default=str)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _git_output(args: list[str]) -> str:
    git = shutil.which("git")
    if not git:
        return "unknown"
    try:
        result = subprocess.run(
            [git] + args,
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.stdout.strip() if result.returncode == 0 else "unknown"
    except Exception:
        return "unknown"


def _get_git_sha() -> str:
    return _git_output(["rev-parse", "HEAD"])


def _is_tree_dirty() -> bool:
    status = _git_output(["status", "--porcelain"])
    return bool(status)


def _get_package_versions() -> dict[str, str]:
    versions = {
        "mindtune_clm": "0.9.0",
        "mpe": "0.8.0",
    }
    try:
        import importlib.metadata

        for dist in importlib.metadata.distributions():
            if dist.metadata["Name"].lower() in {
                "pydantic",
                "fastapi",
                "uvicorn",
                "numpy",
            }:
                versions[dist.metadata["Name"]] = dist.version
    except Exception:
        pass
    return versions


def _frontend_build_checksum(frontend_build_dir: str | None = None) -> str | None:
    root = Path(frontend_build_dir) if frontend_build_dir else Path("dist")
    if not root.exists():
        return None
    hasher = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if path.is_file():
            try:
                hasher.update(path.read_bytes())
            except OSError:
                pass
    digest = hasher.hexdigest()
    return digest if digest else None


def build_release_manifest(
    release_id: str | None = None,
    semantic_version: str = "0.9.0",
    frontend_build_dir: str | None = None,
    container_image_digest: str | None = None,
) -> ReleaseManifest:
    """Build an immutable release manifest from the current environment."""
    node_version = None
    if shutil.which("node"):
        try:
            node_version = subprocess.run(
                ["node", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            ).stdout.strip().lstrip("v")
        except Exception:
            pass

    return ReleaseManifest(
        release_id=release_id or "clm09-local",
        semantic_version=semantic_version,
        git_commit_sha=_get_git_sha(),
        dirty_tree=_is_tree_dirty(),
        python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        node_version=node_version,
        package_versions=_get_package_versions(),
        schema_versions={"event": "1.0.0", "profile": "1.0.0"},
        protocol_versions={"mpe": "1.0.0", "clm_control": "1.0.0"},
        clm_component_versions={"clm01": "1.0", "clm05": "1.0", "clm09": "0.9.0"},
        hebrew_engine_versions={"phonikud": "0.4.1"},
        feature_schema_versions={"curriculum": "1.0.0"},
        migration_versions={"sqlite": "0001"},
        frontend_build_checksum=_frontend_build_checksum(frontend_build_dir),
        container_image_digest=container_image_digest,
        build_timestamp=datetime.now(timezone.utc).isoformat(),
        supported_deployment_targets=[
            "macos_development",
            "container_local",
            "replay_offline",
            "raspberry_pi_5_optional",
            "ci_validation",
        ],
        provenance="local_build",
    )
