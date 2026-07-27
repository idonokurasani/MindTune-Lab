"""Release manifest construction for CLM-10 release candidate."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ReleaseManifest:
    """Immutable release-candidate manifest."""

    release_id: str
    semantic_version: str
    release_candidate_number: int
    git_commit_sha: str
    base_sha: str
    dirty_tree: bool
    build_timestamp: str
    python_version: str
    node_version: str | None
    package_versions: dict[str, str]
    frontend_build_checksum: str | None
    backend_package_checksum: str | None
    configuration_schema_version: str
    event_schema_versions: dict[str, str]
    protocol_versions: dict[str, str]
    curriculum_versions: dict[str, str]
    calibration_algorithm_versions: dict[str, str]
    estimator_version: str
    control_policy_version: str
    safety_policy_version: str
    voice_cache_contract_version: str
    audio_renderer_version: str
    api_version: str
    research_console_version: str
    storage_migration_version: str
    supported_deployment_modes: list[str]
    known_limitations: list[str]
    container_image_digest: str | None
    provenance: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def checksum(self) -> str:
        payload = json.dumps(self.to_dict(), sort_keys=True, ensure_ascii=True, default=str)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[5]


def _read_known_limitations() -> list[str]:
    limitations_file = _repo_root() / "docs" / "release" / "CLM_10_KNOWN_LIMITATIONS.md"
    if not limitations_file.exists():
        return []
    limitations: list[str] = []
    in_section = False
    for line in limitations_file.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            in_section = bool(stripped[3:].strip())
            continue
        if in_section and stripped.startswith("- "):
            limitations.append(stripped[2:].strip())
    return limitations


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
    status = _git_output(["status", "--porcelain", "--untracked-files=no"])
    return bool(status)


def _get_base_sha(override: str | None = None) -> str:
    if override:
        return override
    env = os.environ.get("CLM10_BASE_SHA")
    if env:
        return env
    return _git_output(["rev-parse", "HEAD"])


def _get_package_versions() -> dict[str, str]:
    versions: dict[str, str] = {
        "mindtune_clm": "0.10.0-rc.1",
        "mpe": "0.8.0",
    }
    try:
        import importlib.metadata

        for dist in importlib.metadata.distributions():
            name = dist.metadata["Name"]
            if name.lower() in {
                "pydantic",
                "fastapi",
                "uvicorn",
                "numpy",
                "mindtune-console",
                "mpe",
            }:
                versions[name] = dist.version
    except Exception:
        pass
    return versions


def _directory_checksum(root: Path) -> str | None:
    if not root.exists():
        return None
    hasher = hashlib.sha256()
    files = sorted(
        p for p in root.rglob("*")
        if p.is_file()
        and "__pycache__" not in p.parts
        and not p.name.endswith(".pyc")
        and not p.name.endswith(".pyo")
    )
    for path in files:
        try:
            hasher.update(path.read_bytes())
        except OSError:
            pass
    digest = hasher.hexdigest()
    return digest if digest else None


def _backend_package_checksum() -> str | None:
    repo_root = _repo_root()
    roots = [
        repo_root / "packages" / "clm" / "src" / "mindtune_clm",
        repo_root / "packages" / "mpe" / "src" / "mpe",
    ]
    hasher = hashlib.sha256()
    any_files = False
    for root in roots:
        digest = _directory_checksum(root)
        if digest:
            any_files = True
            hasher.update(digest.encode("utf-8"))
    return hasher.hexdigest() if any_files else None


def _frontend_build_checksum(frontend_build_dir: str | None = None) -> str | None:
    if frontend_build_dir:
        root = Path(frontend_build_dir)
    else:
        root = _repo_root() / "apps" / "research-console" / "dist"
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


def _node_version() -> str | None:
    if not shutil.which("node"):
        return None
    try:
        return (
            subprocess.run(
                ["node", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            .stdout.strip()
            .lstrip("v")
        )
    except Exception:
        return None


def _release_candidate_number(semantic_version: str) -> int:
    if "-rc." in semantic_version:
        try:
            return int(semantic_version.split("-rc.")[-1].split("+")[0].split("-")[0])
        except ValueError:
            pass
    return 0


def build_release_manifest(
    release_id: str | None = None,
    semantic_version: str = "0.10.0-rc.1",
    base_sha: str | None = None,
    frontend_build_dir: str | None = None,
    container_image_digest: str | None = None,
    known_limitations: list[str] | None = None,
) -> ReleaseManifest:
    """Build an immutable CLM-10 release-candidate manifest."""
    return ReleaseManifest(
        release_id=release_id or f"clm10-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}",
        semantic_version=semantic_version,
        release_candidate_number=_release_candidate_number(semantic_version),
        git_commit_sha=_get_git_sha(),
        base_sha=_get_base_sha(base_sha),
        dirty_tree=_is_tree_dirty(),
        build_timestamp=datetime.now(timezone.utc).isoformat(),
        python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        node_version=_node_version(),
        package_versions=_get_package_versions(),
        frontend_build_checksum=_frontend_build_checksum(frontend_build_dir),
        backend_package_checksum=_backend_package_checksum(),
        configuration_schema_version="1.0.0",
        event_schema_versions={"event": "1.0.0", "profile": "1.0.0"},
        protocol_versions={"mpe": "1.1.0", "clm_control": "1.0.0"},
        curriculum_versions={"hebrew_320": "v1_320"},
        calibration_algorithm_versions={"robust_stats": "1.0.0", "profiles": "1.0.0"},
        estimator_version="1.0.0",
        control_policy_version="1.0.0",
        safety_policy_version="1.0.0",
        voice_cache_contract_version="1.0.0",
        audio_renderer_version="1.0.0",
        api_version="v1",
        research_console_version="0.10.0-rc.1",
        storage_migration_version="0001",
        supported_deployment_modes=[
            "macos_development",
            "container_local",
            "replay_offline",
            "raspberry_pi_5_optional",
            "ci_validation",
        ],
        known_limitations=known_limitations if known_limitations is not None else _read_known_limitations(),
        container_image_digest=container_image_digest,
        provenance="local_build",
    )
