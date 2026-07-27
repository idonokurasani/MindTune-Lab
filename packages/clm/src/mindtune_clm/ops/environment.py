"""Dependency and environment checks."""

from __future__ import annotations

import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class DependencyCheck:
    """Result of a dependency check."""

    name: str
    available: bool
    version: str | None
    message: str


def get_python_version() -> str:
    """Return current Python version string."""
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


def get_node_version() -> str | None:
    """Return installed Node version or None."""
    node = shutil.which("node")
    if not node:
        return None
    try:
        result = subprocess.run(
            [node, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.stdout.strip().lstrip("v")
    except Exception:
        return None


def get_platform_info() -> dict[str, Any]:
    """Return sanitized platform information."""
    return {
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "python_version": get_python_version(),
        "node_version": get_node_version(),
    }


def check_executable(name: str, *aliases: str) -> DependencyCheck:
    """Check whether an executable is present."""
    for alias in (name,) + aliases:
        path = shutil.which(alias)
        if path:
            return DependencyCheck(name=name, available=True, version=path, message="found")
    return DependencyCheck(name=name, available=False, version=None, message="not found")


def check_secret_file(path: Path, expected_owner: int | None = None) -> dict[str, Any]:
    """Check secret file permissions."""
    if not path.exists():
        return {"ok": False, "path": str(path), "message": "missing"}
    stat = path.stat()
    perms = stat.st_mode & 0o777
    issues = []
    if perms & 0o044:
        issues.append("readable by group/others")
    if perms & 0o011:
        issues.append("executable")
    return {
        "ok": not issues,
        "path": str(path),
        "permissions": oct(perms),
        "message": "; ".join(issues) if issues else "ok",
    }


def check_directory_writable(path: Path) -> bool:
    """Return True if the directory is writable."""
    try:
        probe = path / ".clm09_write_probe"
        probe.write_text("ok")
        probe.unlink()
        return True
    except OSError:
        return False
