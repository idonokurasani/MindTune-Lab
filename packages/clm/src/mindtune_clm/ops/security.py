"""Security helpers for CLM-09."""

from __future__ import annotations

import hmac
import os
import re
from pathlib import Path
from typing import Any


def redact(value: Any) -> Any:
    """Recursively redact secret-like values."""
    if isinstance(value, dict):
        return {k: redact(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [redact(v) for v in value]
    if isinstance(value, str):
        lower = value.lower()
        if any(k in lower for k in ("token", "secret", "password", "api_key", "apikey", "bearer")):
            if len(value) > 6:
                return value[:2] + "***" + value[-2:]
            return "***"
        return value
    return value


def constant_time_compare(a: str, b: str) -> bool:
    """Constant-time string comparison."""
    return hmac.compare_digest(a.encode("utf-8"), b.encode("utf-8"))


def safe_filename(name: str) -> str:
    """Sanitize a filename to prevent traversal."""
    safe = re.sub(r"[^\w.\-]", "_", name)
    if "/" in safe or "\\" in safe or safe.startswith(".."):
        raise ValueError(f"Unsafe filename: {name}")
    return safe


def validate_path(path: Path, allowed_roots: set[Path]) -> Path:
    """Validate that a path is within an allowed root."""
    resolved = path.resolve()
    for root in allowed_roots:
        try:
            resolved.relative_to(root.resolve())
            return resolved
        except ValueError:
            continue
    raise ValueError(f"Path {resolved} outside allowed roots")


def load_secret_file(path: Path) -> str:
    """Load a secret from an external file with permission checks."""
    if not path.exists():
        raise FileNotFoundError(f"Secret file not found: {path}")
    stat = path.stat()
    perms = stat.st_mode & 0o777
    if perms & 0o044:
        raise PermissionError(f"Secret file {path} is readable by group or others")
    return path.read_text(encoding="utf-8").strip()


def check_secret_environment() -> dict[str, Any]:
    """Check that secrets are sourced from environment/files, not config."""
    found = {}
    for key in ["SPEECHGEN_API_KEY", "SPEECHGEN_EMAIL", "CLM05_API_TOKEN", "CLM09_API_TOKEN"]:
        value = os.environ.get(key)
        if value:
            found[key] = "present"
    return found
