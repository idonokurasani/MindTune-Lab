"""Diagnostics bundle generation."""

from __future__ import annotations

import io
import json
import platform
import tarfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import CLM09Config
from .readiness import check_readiness
from .release import build_release_manifest


@dataclass(frozen=True)
class DiagnosticsBundle:
    """A safe diagnostics bundle."""

    bundle_id: str
    path: str
    included: list[str]
    excluded: list[str]
    summary: dict[str, Any]


def create_diagnostics_bundle(
    config: CLM09Config,
    output_dir: Path,
    include_logs: bool = True,
    max_log_lines: int = 1000,
) -> DiagnosticsBundle:
    """Create a redacted diagnostics bundle."""
    output_dir.mkdir(parents=True, exist_ok=True)
    bundle_id = f"diagnostics-{config.release_id}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}"
    archive_path = output_dir / f"{bundle_id}.tar.gz"

    manifest: dict[str, Any] = {
        "bundle_id": bundle_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "release": build_release_manifest().to_dict(),
        "redacted_config": config.redacted().model_dump(mode="json"),
        "readiness": check_readiness(config).to_dict(),
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
        },
    }

    included = ["manifest.json"]
    excluded = ["secrets", "raw_recordings", "participant_identity", "voice_assets"]

    with tarfile.open(archive_path, "w:gz") as tar:
        manifest_bytes = json.dumps(manifest, sort_keys=True, ensure_ascii=True, default=str).encode("utf-8")
        info = tarfile.TarInfo(name="manifest.json")
        info.size = len(manifest_bytes)
        tar.addfile(info, io.BytesIO(manifest_bytes))

    return DiagnosticsBundle(
        bundle_id=bundle_id,
        path=str(archive_path),
        included=included,
        excluded=excluded,
        summary=manifest,
    )
