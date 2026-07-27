"""Export routes for the CLM-05 API."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse

from mindtune_clm.api.dependencies import get_service
from mindtune_clm.api.models import ExportRequest, ExportResponse
from mindtune_clm.api.services import CLM05Service

router = APIRouter(tags=["exports"])


@router.post("/sessions/{session_id}/exports", response_model=ExportResponse)
def request_export(
    session_id: str,
    data: ExportRequest,
    service: CLM05Service = Depends(get_service),
) -> dict[str, Any]:
    return service.request_export(session_id, data.format)


@router.get("/sessions/{session_id}/export/events")
def export_events(
    session_id: str,
    format: str = Query("json"),
    service: CLM05Service = Depends(get_service),
) -> PlainTextResponse:
    body, media = service.export_events(session_id, format)
    return PlainTextResponse(content=body, media_type=media)


@router.get("/sessions/{session_id}/export/summary")
def export_summary(
    session_id: str,
    format: str = Query("json"),
    service: CLM05Service = Depends(get_service),
) -> PlainTextResponse:
    body, media = service.export_summary(session_id, format)
    return PlainTextResponse(content=body, media_type=media)


@router.get("/sessions/{session_id}/export/manifest")
def export_manifest(
    session_id: str,
    format: str = Query("json"),
    service: CLM05Service = Depends(get_service),
) -> PlainTextResponse:
    body, media = service.export_manifest(session_id, format)
    return PlainTextResponse(content=body, media_type=media)
