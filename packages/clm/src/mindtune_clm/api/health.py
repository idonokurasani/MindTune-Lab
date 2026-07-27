"""Health and readiness routes for the CLM-05 API."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from mindtune_clm.api.dependencies import get_service
from mindtune_clm.api.models import HealthResponse, ReadinessResponse
from mindtune_clm.api.services import CLM05Service

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def get_health(service: CLM05Service = Depends(get_service)) -> dict[str, Any]:
    return service.health()


@router.get("/health/live")
def get_liveness() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/sessions/{session_id}/readiness", response_model=ReadinessResponse)
def get_session_readiness(
    session_id: str,
    service: CLM05Service = Depends(get_service),
) -> dict[str, Any]:
    return service.get_readiness(session_id)
