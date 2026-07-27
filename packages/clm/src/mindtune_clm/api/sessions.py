"""Session routes for the CLM-05 API."""

from __future__ import annotations

from typing import Any, cast

from fastapi import APIRouter, Depends, Request

from mindtune_clm.api.config import CLM05APIConfig
from mindtune_clm.api.dependencies import get_service
from mindtune_clm.api.models import SessionCreate, SessionList, SessionResponse
from mindtune_clm.api.security import require_mutation_auth
from mindtune_clm.api.services import CLM05Service

router = APIRouter(tags=["sessions"])


def _config(request: Request) -> CLM05APIConfig:
    return cast(CLM05APIConfig, request.app.state.config)


@router.post("/sessions", response_model=SessionResponse, status_code=201)
def create_session(
    data: SessionCreate,
    request: Request,
    service: CLM05Service = Depends(get_service),
    config: CLM05APIConfig = Depends(_config),
) -> dict[str, Any]:
    require_mutation_auth(request, config)
    return service.create_session(data.model_dump())


@router.get("/sessions", response_model=SessionList)
def list_sessions(service: CLM05Service = Depends(get_service)) -> dict[str, Any]:
    return {"items": service.list_sessions()}


@router.get("/sessions/{session_id}", response_model=SessionResponse)
def get_session(
    session_id: str,
    service: CLM05Service = Depends(get_service),
) -> dict[str, Any]:
    return service.get_session(session_id).response_dict()


@router.delete("/sessions/{session_id}")
def delete_session(
    session_id: str,
    request: Request,
    service: CLM05Service = Depends(get_service),
    config: CLM05APIConfig = Depends(_config),
) -> dict[str, Any]:
    require_mutation_auth(request, config)
    return service.delete_session(session_id)
