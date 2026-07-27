"""CLM-09 operational endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from mindtune_clm.api.dependencies import get_service
from mindtune_clm.api.services import CLM05Service
from mindtune_clm.ops.backup import create_backup
from mindtune_clm.ops.config import CLM09Config, load_config
from mindtune_clm.ops.diagnostics import create_diagnostics_bundle
from mindtune_clm.ops.release import build_release_manifest
from mindtune_clm.ops.shutdown import ShutdownController

router = APIRouter(tags=["ops"])


def _get_clm09_config(request: Request) -> CLM09Config:
    return getattr(request.app.state, "clm09_config", None) or load_config()


def _ops_enabled(config: CLM09Config = Depends(_get_clm09_config)) -> CLM09Config:
    if not config.api.enable_ops_endpoints:
        raise HTTPException(status_code=404, detail="operational endpoints disabled")
    return config


def _auth_ops(
    request: Request,
    service: CLM05Service = Depends(get_service),
    config: CLM09Config = Depends(_get_clm09_config),
) -> None:
    if not config.api.bearer_token:
        return
    header = request.headers.get("authorization", "")
    if not header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing bearer token")
    from mindtune_clm.ops.security import constant_time_compare

    if not constant_time_compare(header[7:], config.api.bearer_token):
        raise HTTPException(status_code=403, detail="invalid bearer token")


@router.get("/version")
def get_version() -> dict[str, Any]:
    manifest = build_release_manifest()
    return {
        "release_id": manifest.release_id,
        "semantic_version": manifest.semantic_version,
        "git_commit_sha": manifest.git_commit_sha,
        "dirty_tree": manifest.dirty_tree,
        "build_timestamp": manifest.build_timestamp,
    }


@router.get("/health/components")
def get_components(
    config: CLM09Config = Depends(_ops_enabled),
) -> dict[str, Any]:
    from mindtune_clm.ops.startup import run_startup

    manifest = run_startup(config)
    return manifest.to_dict()


@router.get("/ops/configuration")
def get_configuration(config: CLM09Config = Depends(_ops_enabled)) -> dict[str, Any]:
    return config.redacted().model_dump(mode="json")


@router.get("/ops/storage")
def get_storage(config: CLM09Config = Depends(_ops_enabled)) -> dict[str, Any]:
    return {
        label: str(path) for label, path in config.storage_paths().items()
    }


@router.get("/ops/migrations")
def get_migrations(config: CLM09Config = Depends(_ops_enabled)) -> dict[str, Any]:
    from mindtune_clm.ops.migrations import MigrationManager

    db_path = config.storage_paths()["events"] / "clm09.db"
    return MigrationManager(db_path).current()


@router.post("/ops/backups")
def post_backup(
    request: Request,
    config: CLM09Config = Depends(_ops_enabled),
    _=Depends(_auth_ops),
) -> dict[str, Any]:
    paths = config.storage_paths()
    receipt = create_backup(
        source_roots=paths,
        destination=paths["backups"],
        release_id=config.release_id,
        schema_versions={"event": "1.0.0", "profile": "1.0.0"},
        include_cache=False,
        include_secrets=False,
    )
    return receipt.to_dict()


@router.get("/ops/backups")
def list_backups(config: CLM09Config = Depends(_ops_enabled)) -> list[str]:
    backups_dir = config.storage_paths()["backups"]
    if not backups_dir.exists():
        return []
    return sorted([p.name for p in backups_dir.glob("*.tar.gz")])


@router.post("/ops/restores/validate")
def validate_restore(
    body: dict[str, Any],
    config: CLM09Config = Depends(_ops_enabled),
    _=Depends(_auth_ops),
) -> dict[str, Any]:
    from mindtune_clm.ops.restore import validate_restore as validate

    archive = config.storage_paths()["backups"] / body.get("archive", "")
    if not archive.exists():
        raise HTTPException(status_code=404, detail="archive not found")
    return validate(archive, expected_release_id=config.release_id)


@router.post("/ops/diagnostics")
def post_diagnostics(
    config: CLM09Config = Depends(_ops_enabled),
    _=Depends(_auth_ops),
) -> dict[str, Any]:
    bundle = create_diagnostics_bundle(config, config.storage_paths()["backups"])
    return {"bundle_id": bundle.bundle_id, "path": bundle.path, "excluded": bundle.excluded}


@router.post("/ops/shutdown")
def post_shutdown(
    request: Request,
    config: CLM09Config = Depends(_ops_enabled),
    _=Depends(_auth_ops),
) -> dict[str, Any]:
    if not config.api.enable_shutdown:
        raise HTTPException(status_code=403, detail="shutdown endpoint disabled")
    import threading

    def _stop() -> None:
        controller = ShutdownController(
            phases=config.shutdown.phases,
            timeout_s=config.shutdown.timeout_s,
        )
        controller.shutdown(config.storage_paths()["logs"] / "shutdown_receipt.json")

    threading.Thread(target=_stop, daemon=True).start()
    return {"status": "shutdown_requested"}
