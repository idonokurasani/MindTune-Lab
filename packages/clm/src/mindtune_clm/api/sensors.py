"""Sensor routes for the CLM-05 API."""

from __future__ import annotations

from typing import Any, cast

from fastapi import APIRouter, Depends, Request

from mindtune_clm.api.config import CLM05APIConfig
from mindtune_clm.api.dependencies import get_service
from mindtune_clm.api.errors import NotFoundError
from mindtune_clm.api.models import SensorList, SensorRegister, SensorResponse
from mindtune_clm.api.security import require_mutation_auth
from mindtune_clm.api.services import CLM05Service

router = APIRouter(tags=["sensors"])


def _config(request: Request) -> CLM05APIConfig:
    return cast(CLM05APIConfig, request.app.state.config)


@router.post("/sensors", response_model=SensorResponse, status_code=201)
def register_sensor(
    data: SensorRegister,
    request: Request,
    service: CLM05Service = Depends(get_service),
    config: CLM05APIConfig = Depends(_config),
) -> dict[str, Any]:
    require_mutation_auth(request, config)
    return service.register_sensor(data.model_dump())


@router.get("/sensors", response_model=SensorList)
def list_sensors(service: CLM05Service = Depends(get_service)) -> dict[str, Any]:
    return {"items": service.list_sensors()}


@router.get("/sensors/{sensor_id}", response_model=SensorResponse)
def get_sensor(
    sensor_id: str,
    service: CLM05Service = Depends(get_service),
) -> dict[str, Any]:
    sensor = service.sensors.get(sensor_id)
    if not sensor:
        raise NotFoundError(sensor_id)
    return sensor


@router.post("/sensors/{sensor_id}/connect", response_model=SensorResponse)
def connect_sensor(
    sensor_id: str,
    request: Request,
    payload: dict[str, Any],
    service: CLM05Service = Depends(get_service),
    config: CLM05APIConfig = Depends(_config),
) -> dict[str, Any]:
    require_mutation_auth(request, config)
    return service.sensor_command(sensor_id, {**payload, "command": "connect"})


@router.post("/sensors/{sensor_id}/disconnect", response_model=SensorResponse)
def disconnect_sensor(
    sensor_id: str,
    request: Request,
    payload: dict[str, Any],
    service: CLM05Service = Depends(get_service),
    config: CLM05APIConfig = Depends(_config),
) -> dict[str, Any]:
    require_mutation_auth(request, config)
    return service.sensor_command(sensor_id, {**payload, "command": "disconnect"})
