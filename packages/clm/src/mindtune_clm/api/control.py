"""Control-plane routes for the CLM-05 API."""

from __future__ import annotations

from typing import Any, cast

from fastapi import APIRouter, Depends, Request

from mindtune_clm.api.config import CLM05APIConfig
from mindtune_clm.api.dependencies import get_service
from mindtune_clm.api.models import ControlCommand as ControlCommandModel
from mindtune_clm.api.models import ControlResponse
from mindtune_clm.api.security import require_mutation_auth
from mindtune_clm.api.services import CLM05Service

router = APIRouter(tags=["control"])


def _config(request: Request) -> CLM05APIConfig:
    return cast(CLM05APIConfig, request.app.state.config)


@router.post("/sessions/{session_id}/control", response_model=ControlResponse)
def control_session(
    session_id: str,
    data: ControlCommandModel,
    request: Request,
    service: CLM05Service = Depends(get_service),
    config: CLM05APIConfig = Depends(_config),
) -> dict[str, Any]:
    require_mutation_auth(request, config)
    return service.control_session(
        session_id,
        data.command,
        data.parameters,
        data.idempotency_key,
    )


@router.post("/control/sessions/{session_id}/control", response_model=ControlResponse)
def control_session_alias(
    session_id: str,
    data: ControlCommandModel,
    request: Request,
    service: CLM05Service = Depends(get_service),
    config: CLM05APIConfig = Depends(_config),
) -> dict[str, Any]:
    require_mutation_auth(request, config)
    return service.control_session(
        session_id,
        data.command,
        data.parameters,
        data.idempotency_key,
    )
