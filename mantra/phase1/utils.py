"""Shared utilities for Phase 1 Mantra engine."""
from __future__ import annotations

import hashlib
import json
import unicodedata
from pathlib import Path
from typing import Any


def normalize_unicode(text: str) -> str:
    """Deterministic NFC Unicode normalization."""
    return unicodedata.normalize("NFC", text)


def sha256_hex(data: bytes | str) -> str:
    """Return a deterministic SHA-256 hex digest for bytes or UTF-8 text."""
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def canonical_json(obj: Any) -> str:
    """Return a deterministic JSON representation with sorted keys."""
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def load_json(path: Path) -> Any:
    """Load JSON from a file path."""
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: Any) -> None:
    """Save JSON to a file path atomically."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)
