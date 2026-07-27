"""Protocol routes for the CLM-05 API."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from mindtune_clm.api.dependencies import get_service
from mindtune_clm.api.models import ProtocolList, ProtocolReference
from mindtune_clm.api.services import CLM05Service

router = APIRouter(tags=["protocols"])


@router.get("/protocols", response_model=ProtocolList)
def list_protocols(service: CLM05Service = Depends(get_service)) -> dict[str, Any]:
    return {"items": service.list_protocols()}


@router.get("/protocols/{protocol_version_id}", response_model=ProtocolReference)
def get_protocol(
    protocol_version_id: str,
    service: CLM05Service = Depends(get_service),
) -> dict[str, Any]:
    return service.get_protocol(protocol_version_id)
