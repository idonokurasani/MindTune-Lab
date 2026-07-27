"""Backup creation for CLM-09."""

from __future__ import annotations

import hashlib
import json
import tarfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class BackupReceipt:
    """Receipt for a completed backup."""

    backup_id: str
    destination: str
    timestamp: str
    files: list[str]
    checksums: dict[str, str]
    success: bool
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "backup_id": self.backup_id,
            "destination": self.destination,
            "timestamp": self.timestamp,
            "files": self.files,
            "checksums": self.checksums,
            "success": self.success,
            "message": self.message,
        }


def _file_checksum(path: Path) -> str:
    hasher = hashlib.sha256()
    if path.is_dir():
        for child in sorted(path.rglob("*")):
            if child.is_file():
                hasher.update(child.read_bytes())
        return hasher.hexdigest()
    hasher.update(path.read_bytes())
    return hasher.hexdigest()


def create_backup(
    source_roots: dict[str, Path],
    destination: Path,
    release_id: str,
    schema_versions: dict[str, str],
    include_cache: bool = False,
    include_secrets: bool = False,
) -> BackupReceipt:
    """Create a versioned backup archive."""
    destination.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    backup_id = f"{release_id}-{timestamp}"
    archive_path = destination / f"{backup_id}.tar.gz"
    manifest: dict[str, Any] = {
        "backup_id": backup_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "release_id": release_id,
        "schema_versions": schema_versions,
        "files": {},
    }
    checksums: dict[str, str] = {}
    files: list[str] = []

    with tarfile.open(archive_path, "w:gz") as tar:
        for label, root in source_roots.items():
            if not root.exists():
                continue
            if label == "cache" and not include_cache:
                continue
            if label == "secrets" and not include_secrets:
                continue
            for path in sorted(root.rglob("*")):
                if path.is_file():
                    arcname = f"{label}/{path.relative_to(root)}"
                    tar.add(path, arcname=arcname)
                    checksum = _file_checksum(path)
                    checksums[arcname] = checksum
                    manifest["files"][arcname] = checksum
                    files.append(arcname)

        manifest_bytes = json.dumps(manifest, sort_keys=True, ensure_ascii=True).encode("utf-8")
        manifest_path = destination / f"{backup_id}.manifest.json"
        manifest_path.write_bytes(manifest_bytes)
        tar.add(manifest_path, arcname="manifest.json")

    return BackupReceipt(
        backup_id=backup_id,
        destination=str(destination),
        timestamp=manifest["timestamp"],
        files=files,
        checksums=checksums,
        success=True,
        message="Backup completed",
    )
