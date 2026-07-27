"""Stimulus asset routes for the CLM-05 API."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query

from mindtune_clm.api.dependencies import get_service
from mindtune_clm.api.models import StimulusList, StimulusResponse
from mindtune_clm.api.services import CLM05Service

router = APIRouter(tags=["stimuli"])


@router.get("/stimuli", response_model=StimulusList)
def list_stimuli(
    session_id: str | None = Query(None),
    service: CLM05Service = Depends(get_service),
) -> dict[str, Any]:
    return {"items": service.list_stimuli(session_id)}


@router.get("/stimuli/{stimulus_id}", response_model=StimulusResponse)
def get_stimulus(
    stimulus_id: str,
    session_id: str | None = Query(None),
    service: CLM05Service = Depends(get_service),
) -> dict[str, Any]:
    return service.get_stimulus(stimulus_id, session_id)
