"""Manifest registry utilities."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def save_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def merge_manifests(paths: list[Path]) -> dict[str, Any]:
    merged: dict[str, Any] = {"resources": []}
    for p in paths:
        merged["resources"].append(load_manifest(p))
    return merged
