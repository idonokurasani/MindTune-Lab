"""Test fixtures for the CLM-05 experimental API."""

from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

from mindtune_clm.api.app import create_app
from mindtune_clm.api.config import CLM05APIConfig

TEST_TOKEN = "test-clm05-token-12345"


def test_config(store_path: Path | None = None, token: str | None = TEST_TOKEN) -> CLM05APIConfig:
    """Return a test-safe API configuration."""
    if store_path is None:
        store_path = Path(tempfile.mkdtemp(prefix="clm05_test_store_"))
    return CLM05APIConfig(
        host="127.0.0.1",
        port=8005,
        bearer_token=token,
        store_path=str(store_path),
        max_request_bytes=1_000_000,
        allowed_origins=["http://localhost:8005"],
        csp_enabled=False,
    )


def make_test_client(store_path: Path | None = None, token: str | None = TEST_TOKEN) -> TestClient:
    """Return a configured TestClient for CLM-05."""
    config = test_config(store_path, token)
    app = create_app(config)
    return TestClient(app)


def auth_headers(token: str = TEST_TOKEN) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
