"""Restore for CLM-09."""

from __future__ import annotations

import json
import tarfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast


@dataclass(frozen=True)
class RestoreReceipt:
    """Receipt for a restore operation."""

    backup_id: str
    dry_run: bool
    target: str
    success: bool
    message: str
    files_restored: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "backup_id": self.backup_id,
            "dry_run": self.dry_run,
            "target": self.target,
            "success": self.success,
            "message": self.message,
            "files_restored": self.files_restored,
        }


def _manifest_from_archive(archive_path: Path) -> dict[str, Any]:
    with tarfile.open(str(archive_path), "r:gz") as tar:
        member = tar.getmember("manifest.json")
        f = tar.extractfile(member)
        if f is None:
            raise ValueError("manifest.json missing in archive")
        with f:
            return cast(dict[str, Any], json.loads(f.read().decode("utf-8")))


def validate_restore(
    archive_path: Path,
    expected_release_id: str | None = None,
    expected_schema_versions: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Validate a backup archive without changing anything."""
    manifest = _manifest_from_archive(archive_path)
    if expected_release_id and manifest.get("release_id") != expected_release_id:
        return {"ok": False, "message": "release_id mismatch"}
    if expected_schema_versions and manifest.get("schema_versions") != expected_schema_versions:
        return {"ok": False, "message": "schema version mismatch"}
    return {"ok": True, "manifest": manifest}


def restore_backup(
    archive_path: Path,
    target_root: Path,
    dry_run: bool = False,
    overwrite: bool = False,
) -> RestoreReceipt:
    """Restore a backup archive into a target directory."""
    validation = validate_restore(archive_path)
    if not validation["ok"]:
        return RestoreReceipt(
            backup_id="unknown",
            dry_run=dry_run,
            target=str(target_root),
            success=False,
            message=validation["message"],
            files_restored=0,
        )

    manifest = cast(dict[str, Any], validation["manifest"])
    backup_id = manifest.get("backup_id", "unknown")

    if target_root.exists() and any(target_root.iterdir()) and not overwrite:
        return RestoreReceipt(
            backup_id=backup_id,
            dry_run=dry_run,
            target=str(target_root),
            success=False,
            message="target not empty and overwrite=False",
            files_restored=0,
        )

    if dry_run:
        files = list(manifest.get("files", {}).keys())
        return RestoreReceipt(
            backup_id=backup_id,
            dry_run=True,
            target=str(target_root),
            success=True,
            message="dry-run validation passed",
            files_restored=len(files),
        )

    target_root.mkdir(parents=True, exist_ok=True)
    files_restored = 0
    with tarfile.open(str(archive_path), "r:gz") as tar:
        for member in tar.getmembers():
            if member.name == "manifest.json" or member.issym():
                continue
            tar.extract(member, path=target_root)
            files_restored += 1

    return RestoreReceipt(
        backup_id=backup_id,
        dry_run=False,
        target=str(target_root),
        success=True,
        message="restore completed",
        files_restored=files_restored,
    )
