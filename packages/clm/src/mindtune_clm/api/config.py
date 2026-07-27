"""CLM-05 API configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CLM05APIConfig:
    """Runtime configuration for the CLM-05 experimental API."""

    app_name: str = "CLM-05 Experimental API"
    api_version: str = "v1"
    host: str = "127.0.0.1"
    port: int = 8005
    bearer_token: str | None = field(default=None)
    store_path: str | None = None
    max_request_bytes: int = 1_000_000
    allowed_origins: list[str] = field(default_factory=list)
    csp_enabled: bool = True
    shutdown_timeout_s: float = 5.0
    sse_heartbeat_interval_s: float = 15.0

    @classmethod
    def from_env(cls, overrides: dict[str, Any] | None = None) -> "CLM05APIConfig":
        """Load configuration from environment and optional overrides."""
        overrides = overrides or {}
        token = os.environ.get("CLM05_API_TOKEN", overrides.get("bearer_token"))
        if not token:
            token = None
        store = os.environ.get("CLM05_STORE_PATH", overrides.get("store_path"))
        if not store:
            store = None
        raw_origins = os.environ.get("CLM05_CORS_ORIGINS", "")
        origins = [o.strip() for o in raw_origins.split(",") if o.strip()]
        if not origins:
            origins = ["http://localhost:8005", "http://127.0.0.1:8005"]
        return cls(
            app_name=str(overrides.get("app_name", cls.app_name)),
            api_version=str(overrides.get("api_version", cls.api_version)),
            host=str(overrides.get("host", cls.host)),
            port=int(overrides.get("port", int(os.environ.get("CLM05_PORT", "8005")))),
            bearer_token=token,
            store_path=store,
            max_request_bytes=int(
                overrides.get(
                    "max_request_bytes",
                    os.environ.get("CLM05_MAX_REQUEST_BYTES", str(cls.max_request_bytes)),
                )
            ),
            allowed_origins=origins,
            csp_enabled=bool(
                overrides.get("csp_enabled", os.environ.get("CLM05_CSP_ENABLED", "true").lower() == "true")
            ),
            shutdown_timeout_s=float(
                overrides.get(
                    "shutdown_timeout_s",
                    os.environ.get("CLM05_SHUTDOWN_TIMEOUT_S", str(cls.shutdown_timeout_s)),
                )
            ),
            sse_heartbeat_interval_s=float(
                overrides.get(
                    "sse_heartbeat_interval_s",
                    os.environ.get("CLM05_SSE_HEARTBEAT_S", str(cls.sse_heartbeat_interval_s)),
                )
            ),
        )

    def store_path_for(self, session_id: str) -> Path | None:
        """Return a per-session store path when persistence is enabled."""
        if not self.store_path:
            return None
        base = Path(self.store_path)
        return base / f"{session_id}.sqlite"
