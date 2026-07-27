"""Typed CLM-09 configuration layer."""

from __future__ import annotations

import argparse
import json
import os
import re
import secrets
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator


class DeploymentMode(StrEnum):
    """Operational deployment modes."""

    DEVELOPMENT = "development"
    RESEARCH_LOCAL = "research_local"
    REPLAY_OFFLINE = "replay_offline"
    RASPBERRY_SERVICE = "raspberry_service"
    CONTAINER = "container"


class APIConfig(BaseModel):
    """API runtime configuration."""

    host: str = "127.0.0.1"
    port: int = 8005
    api_version: str = "v1"
    max_request_bytes: int = 1_000_000
    bearer_token: str | None = None
    allowed_origins: list[str] = Field(default_factory=lambda: ["http://localhost:8005"])
    enable_ops_endpoints: bool = False
    enable_restore: bool = False
    enable_shutdown: bool = False

    model_config = ConfigDict(extra="forbid")


class ResearchConsoleConfig(BaseModel):
    """Research Console serving configuration."""

    enabled: bool = True
    static_path: str | None = None
    build_dir: str | None = None

    model_config = ConfigDict(extra="forbid")


class StorageConfig(BaseModel):
    """Storage layout configuration."""

    root: str = "data"
    events_dir: str = "events"
    sessions_dir: str = "sessions"
    profiles_dir: str = "profiles"
    studies_dir: str = "studies"
    exports_dir: str = "exports"
    cache_dir: str = "cache"
    logs_dir: str = "logs"
    backups_dir: str = "backups"
    tmp_dir: str = "tmp"
    permissions: int = 0o755

    model_config = ConfigDict(extra="forbid")

    @field_validator("permissions", mode="before")
    @classmethod
    def _permissions_int(cls, v: Any) -> int:
        if isinstance(v, str):
            return int(v, 8)
        return int(v)


class EventStoreConfig(BaseModel):
    """Event store configuration."""

    engine: str = "file"
    path: str = "data/events"
    page_size: int = 1000
    wal_enabled: bool = True
    busy_timeout_ms: int = 5000
    checksum_chain: bool = True
    flush_on_shutdown: bool = True

    model_config = ConfigDict(extra="forbid")


class SensorAccessConfig(BaseModel):
    """Sensor and hardware configuration."""

    fc11_enabled: bool = False
    fc11_address: str | None = None
    replay_mode: bool = True
    synthetic: bool = True

    model_config = ConfigDict(extra="forbid")


class PlaybackConfig(BaseModel):
    """Audio playback configuration."""

    backend: str = "deterministic"
    device: str | None = None
    max_buffer_ms: int = 5000

    model_config = ConfigDict(extra="forbid")


class VoiceCacheConfig(BaseModel):
    """Voice cache configuration."""

    path: str = "data/cache/voice"
    max_size_mb: int = 1024
    allow_network: bool = True

    model_config = ConfigDict(extra="forbid")


class CalibrationConfig(BaseModel):
    """Calibration configuration."""

    profile_dir: str = "data/profiles"
    min_duration_s: float = 60.0

    model_config = ConfigDict(extra="forbid")


class ScientificValidationConfig(BaseModel):
    """Scientific validation configuration."""

    enabled: bool = True
    require_peer_review: bool = False

    model_config = ConfigDict(extra="forbid")


class LoggingConfig(BaseModel):
    """Structured logging configuration."""

    level: str = "INFO"
    format: str = "json"
    output: str = "data/logs/clm09.jsonl"
    max_payload_bytes: int = 8192
    include_tracebacks: bool = False
    retention_days: int = 30

    model_config = ConfigDict(extra="forbid")


class MetricsConfig(BaseModel):
    """Metrics configuration."""

    enabled: bool = True
    prometheus_path: str = "/metrics"
    output: str = "data/logs/metrics.jsonl"

    model_config = ConfigDict(extra="forbid")


class SecurityConfig(BaseModel):
    """Security configuration."""

    cors_origins: list[str] = Field(default_factory=list)
    secret_paths: list[str] = Field(default_factory=list)
    require_auth_for_ops: bool = False
    loopback_only: bool = True

    model_config = ConfigDict(extra="forbid")


class ResourceLimitsConfig(BaseModel):
    """Resource limits configuration."""

    max_active_sessions: int = 10
    max_replay_sessions: int = 5
    max_sse_clients: int = 50
    max_request_size: int = 1_000_000
    max_upload_size: int = 10_000_000
    max_buffer_capacity: int = 10_000
    max_log_payload_bytes: int = 8192
    max_export_size: int = 100_000_000
    max_cache_size_mb: int = 1024
    max_tmp_size_mb: int = 512
    shutdown_timeout_s: float = 10.0
    subprocess_timeout_s: float = 60.0
    backup_concurrency: int = 1

    model_config = ConfigDict(extra="forbid")


class ShutdownConfig(BaseModel):
    """Shutdown configuration."""

    timeout_s: float = 10.0
    phases: list[str] = Field(
        default_factory=lambda: [
            "stop_mutations",
            "stop_sessions",
            "freeze_adaptive",
            "stop_playback",
            "disconnect_sensors",
            "flush_events",
            "finish_exports",
            "release_locks",
            "close_storage",
            "emit_receipt",
        ]
    )

    model_config = ConfigDict(extra="forbid")


class BackupConfig(BaseModel):
    """Backup configuration."""

    enabled: bool = True
    destination: str = "data/backups"
    retention_count: int = 7
    include_cache: bool = False
    include_secrets: bool = False

    model_config = ConfigDict(extra="forbid")


class CLM09Config(BaseModel):
    """Top-level typed CLM-09 configuration."""

    release_id: str = Field(default_factory=lambda: f"clm09-{secrets.token_hex(8)}")
    semantic_version: str = "0.9.0"
    deployment_mode: DeploymentMode = DeploymentMode.DEVELOPMENT
    api: APIConfig = Field(default_factory=APIConfig)
    research_console: ResearchConsoleConfig = Field(default_factory=ResearchConsoleConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    event_store: EventStoreConfig = Field(default_factory=EventStoreConfig)
    sensor_access: SensorAccessConfig = Field(default_factory=SensorAccessConfig)
    playback: PlaybackConfig = Field(default_factory=PlaybackConfig)
    voice_cache: VoiceCacheConfig = Field(default_factory=VoiceCacheConfig)
    calibration: CalibrationConfig = Field(default_factory=CalibrationConfig)
    scientific_validation: ScientificValidationConfig = Field(
        default_factory=ScientificValidationConfig
    )
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    metrics: MetricsConfig = Field(default_factory=MetricsConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    resource_limits: ResourceLimitsConfig = Field(default_factory=ResourceLimitsConfig)
    shutdown: ShutdownConfig = Field(default_factory=ShutdownConfig)
    backup: BackupConfig = Field(default_factory=BackupConfig)

    model_config = ConfigDict(extra="forbid")

    def checksum(self) -> str:
        """Return a deterministic SHA-256 checksum of the redacted configuration."""
        import hashlib

        redacted = self.redacted().model_dump(mode="json", exclude_none=True)
        payload = json.dumps(redacted, sort_keys=True, ensure_ascii=True, default=str)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]

    def redacted(self) -> "CLM09Config":
        """Return a copy with secrets replaced."""
        data = self.model_dump()
        api = data.get("api", {})
        if api.get("bearer_token"):
            api["bearer_token"] = "***REDACTED***"
        data["api"] = api
        return CLM09Config(**data)

    def storage_paths(self) -> dict[str, Path]:
        """Return all configured storage paths."""
        root = Path(self.storage.root)
        return {
            "root": root,
            "events": root / self.storage.events_dir,
            "sessions": root / self.storage.sessions_dir,
            "profiles": root / self.storage.profiles_dir,
            "studies": root / self.storage.studies_dir,
            "exports": root / self.storage.exports_dir,
            "cache": root / self.storage.cache_dir,
            "logs": root / self.storage.logs_dir,
            "backups": root / self.storage.backups_dir,
            "tmp": root / self.storage.tmp_dir,
        }

    def ensure_storage(self) -> None:
        """Create storage directories and validate permissions."""
        for path in self.storage_paths().values():
            path.mkdir(parents=True, exist_ok=True)
            mode = path.stat().st_mode & 0o777
            if mode & 0o022:
                path.chmod(self.storage.permissions)


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Deterministically merge override into base."""
    merged = dict(base)
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _env_to_nested_dict(prefix: str = "CLM09_") -> dict[str, Any]:
    """Convert CLM09_* environment variables into a nested dict."""
    result: dict[str, Any] = {}
    for key, value in os.environ.items():
        if not key.startswith(prefix):
            continue
        rest = key[len(prefix) :].lower()
        parts = rest.split("__")
        current = result
        for part in parts[:-1]:
            current = current.setdefault(part, {})
        last = parts[-1]
        if last in current and isinstance(current[last], dict):
            raise ValueError(f"Environment key {key} conflicts with existing dict")
        current[last] = value
    return result


def _coerce_types(raw: dict[str, Any]) -> dict[str, Any]:
    """Best-effort type coercion for environment overrides."""
    for key, value in list(raw.items()):
        if isinstance(value, dict):
            raw[key] = _coerce_types(value)
        elif isinstance(value, str):
            if value.lower() in ("true", "false"):
                raw[key] = value.lower() == "true"
            elif re.fullmatch(r"-?\d+", value):
                raw[key] = int(value)
            elif re.fullmatch(r"-?\d+\.\d+", value):
                raw[key] = float(value)
            elif value.startswith("[") and value.endswith("]"):
                raw[key] = [item.strip() for item in value[1:-1].split(",") if item.strip()]
    return raw


def load_config(
    config_path: str | Path | None = None,
    cli_args: list[str] | None = None,
    overrides: dict[str, Any] | None = None,
) -> CLM09Config:
    """Load configuration with deterministic precedence.

    Precedence: defaults -> config file -> env -> CLI args -> explicit overrides.
    """
    base: dict[str, Any] = {}

    if config_path:
        path = Path(config_path)
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                file_data = json.load(f)
            base = _deep_merge(base, file_data)

    env_data = _coerce_types(_env_to_nested_dict())
    base = _deep_merge(base, env_data)

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--deployment-mode", dest="deployment_mode")
    parser.add_argument("--host", dest="api.host")
    parser.add_argument("--port", dest="api.port", type=int)
    parser.add_argument("--config-file", dest="config_file")
    parser.add_argument("--release-id", dest="release_id")
    parsed, _ = parser.parse_known_args(cli_args or [])
    cli_data = {}
    if parsed.deployment_mode:
        cli_data["deployment_mode"] = parsed.deployment_mode
    if getattr(parsed, "api.host", None):
        cli_data.setdefault("api", {})["host"] = getattr(parsed, "api.host")
    if getattr(parsed, "api.port", None):
        cli_data.setdefault("api", {})["port"] = getattr(parsed, "api.port")
    if parsed.release_id:
        cli_data["release_id"] = parsed.release_id

    base = _deep_merge(base, cli_data)

    if overrides:
        base = _deep_merge(base, overrides)

    try:
        return CLM09Config(**base)
    except ValidationError as exc:
        raise ConfigRejectedError(str(exc)) from exc


class ConfigRejectedError(Exception):
    """Raised when configuration is invalid and must block startup."""
