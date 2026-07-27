"""FastAPI dependency providers for the CLM-05 API."""

from __future__ import annotations

from typing import cast

from fastapi import Request

from mindtune_clm.api.services import CLM05Service


def get_service(request: Request) -> CLM05Service:
    """Return the CLM-05 service instance attached to the app."""
    return cast(CLM05Service, request.app.state.service)
