"""Experiment routes for the CLM-05 API."""

from __future__ import annotations

from typing import Any, cast

from fastapi import APIRouter, Depends, Request

from mindtune_clm.api.config import CLM05APIConfig
from mindtune_clm.api.dependencies import get_service
from mindtune_clm.api.models import ExperimentCreate, ExperimentList, ExperimentResponse
from mindtune_clm.api.security import require_mutation_auth
from mindtune_clm.api.services import CLM05Service

router = APIRouter(tags=["experiments"])


def _config(request: Request) -> CLM05APIConfig:
    return cast(CLM05APIConfig, request.app.state.config)


@router.post("/experiments", response_model=ExperimentResponse, status_code=201)
def create_experiment(
    data: ExperimentCreate,
    request: Request,
    service: CLM05Service = Depends(get_service),
    config: CLM05APIConfig = Depends(_config),
) -> dict[str, Any]:
    require_mutation_auth(request, config)
    return service.create_experiment(data.model_dump())


@router.get("/experiments", response_model=ExperimentList)
def list_experiments(service: CLM05Service = Depends(get_service)) -> dict[str, Any]:
    return {"items": service.list_experiments()}


@router.get("/experiments/{experiment_id}", response_model=ExperimentResponse)
def get_experiment(
    experiment_id: str,
    service: CLM05Service = Depends(get_service),
) -> dict[str, Any]:
    return service.get_experiment(experiment_id)


@router.delete("/experiments/{experiment_id}")
def delete_experiment(
    experiment_id: str,
    request: Request,
    service: CLM05Service = Depends(get_service),
    config: CLM05APIConfig = Depends(_config),
) -> dict[str, Any]:
    require_mutation_auth(request, config)
    return service.delete_experiment(experiment_id)
