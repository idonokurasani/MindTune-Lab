"""CLM-07 calibration API routes."""

from __future__ import annotations

from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException, Request

from mindtune_clm.api.calibration_service import CalibrationAPIService
from mindtune_clm.api.config import CLM05APIConfig
from mindtune_clm.api.models import (
    CalibrationProfileAction,
    CalibrationProfileList,
    CalibrationProfileResponse,
    CalibrationReadinessResponse,
    CalibrationSelectionResponse,
    CalibrationSessionCreate,
    CalibrationSessionResponse,
)
from mindtune_clm.api.security import require_mutation_auth

router = APIRouter(tags=["calibrations"])


def _config(request: Request) -> CLM05APIConfig:
    return cast(CLM05APIConfig, request.app.state.config)


def _service(request: Request) -> CalibrationAPIService:
    return cast(CalibrationAPIService, request.app.state.calibration_service)


@router.post("/calibrations", response_model=CalibrationSessionResponse, status_code=201)
def create_calibration(
    data: CalibrationSessionCreate,
    request: Request,
    service: CalibrationAPIService = Depends(_service),
    config: CLM05APIConfig = Depends(_config),
) -> dict[str, Any]:
    require_mutation_auth(request, config)
    payload = data.model_dump()
    return service._idempotent(
        data.idempotency_key,
        payload,
        lambda: service.create_session(payload),
    )


@router.get("/calibrations", response_model=CalibrationSessionResponse)
def list_calibrations(
    service: CalibrationAPIService = Depends(_service),
) -> dict[str, Any]:
    return {"items": service.list_sessions()}


@router.get("/calibrations/{calibration_id}", response_model=CalibrationSessionResponse)
def get_calibration(
    calibration_id: str,
    service: CalibrationAPIService = Depends(_service),
) -> dict[str, Any]:
    return service._session_response(service.get_session(calibration_id))


@router.post("/calibrations/{calibration_id}/prepare")
def prepare_calibration(
    calibration_id: str,
    request: Request,
    service: CalibrationAPIService = Depends(_service),
    config: CLM05APIConfig = Depends(_config),
) -> dict[str, Any]:
    require_mutation_auth(request, config)
    readiness = service.prepare(calibration_id)
    return readiness.as_dict()


@router.post("/calibrations/{calibration_id}/start")
def start_calibration(
    calibration_id: str,
    request: Request,
    service: CalibrationAPIService = Depends(_service),
    config: CLM05APIConfig = Depends(_config),
) -> dict[str, Any]:
    require_mutation_auth(request, config)
    return service.start(calibration_id, {})


@router.post("/calibrations/{calibration_id}/pause")
def pause_calibration(
    calibration_id: str,
    request: Request,
    service: CalibrationAPIService = Depends(_service),
    config: CLM05APIConfig = Depends(_config),
) -> dict[str, Any]:
    require_mutation_auth(request, config)
    return service.pause(calibration_id)


@router.post("/calibrations/{calibration_id}/resume")
def resume_calibration(
    calibration_id: str,
    request: Request,
    service: CalibrationAPIService = Depends(_service),
    config: CLM05APIConfig = Depends(_config),
) -> dict[str, Any]:
    require_mutation_auth(request, config)
    return service.resume(calibration_id)


@router.post("/calibrations/{calibration_id}/stop")
def stop_calibration(
    calibration_id: str,
    request: Request,
    service: CalibrationAPIService = Depends(_service),
    config: CLM05APIConfig = Depends(_config),
) -> dict[str, Any]:
    require_mutation_auth(request, config)
    return service.stop(calibration_id)


@router.post("/calibrations/{calibration_id}/abort")
def abort_calibration(
    calibration_id: str,
    request: Request,
    service: CalibrationAPIService = Depends(_service),
    config: CLM05APIConfig = Depends(_config),
) -> dict[str, Any]:
    require_mutation_auth(request, config)
    return service.abort(calibration_id, "api_request")


@router.get("/calibrations/{calibration_id}/readiness", response_model=CalibrationReadinessResponse)
def calibration_readiness(
    calibration_id: str,
    service: CalibrationAPIService = Depends(_service),
) -> dict[str, Any]:
    readiness = service.readiness(calibration_id).as_dict()
    print("DEBUG readiness", readiness)
    return readiness


@router.get("/calibrations/{calibration_id}/health")
def calibration_health(
    calibration_id: str,
    service: CalibrationAPIService = Depends(_service),
) -> dict[str, Any]:
    return service.health(calibration_id)


@router.get("/calibrations/{calibration_id}/summary")
def calibration_summary(
    calibration_id: str,
    service: CalibrationAPIService = Depends(_service),
) -> dict[str, Any]:
    return service.summary(calibration_id)


@router.get("/participants/{participant_id}/calibration-profiles", response_model=CalibrationProfileList)
def list_profiles(
    participant_id: str,
    service: CalibrationAPIService = Depends(_service),
) -> dict[str, Any]:
    return {"items": service.list_profiles(participant_id)}


@router.get("/participants/{participant_id}/calibration-profiles/{profile_id}", response_model=CalibrationProfileResponse)
def get_profile(
    participant_id: str,
    profile_id: str,
    service: CalibrationAPIService = Depends(_service),
) -> dict[str, Any]:
    return service.get_profile(participant_id, profile_id)


@router.post("/participants/{participant_id}/calibration-profiles/{profile_id}/validate")
def validate_profile(
    participant_id: str,
    profile_id: str,
    request: Request,
    service: CalibrationAPIService = Depends(_service),
    config: CLM05APIConfig = Depends(_config),
) -> dict[str, Any]:
    require_mutation_auth(request, config)
    return service.validate_profile(participant_id, profile_id)


@router.post("/participants/{participant_id}/calibration-profiles/{profile_id}/invalidate")
def invalidate_profile(
    participant_id: str,
    profile_id: str,
    request: Request,
    data: CalibrationProfileAction,
    service: CalibrationAPIService = Depends(_service),
    config: CLM05APIConfig = Depends(_config),
) -> dict[str, Any]:
    require_mutation_auth(request, config)
    if not data.reason:
        raise HTTPException(status_code=400, detail="invalidation requires a reason")
    return service.invalidate_profile(participant_id, profile_id, data.reason)


@router.post("/participants/{participant_id}/calibration-profiles/{profile_id}/select", response_model=CalibrationSelectionResponse)
def select_profile(
    participant_id: str,
    profile_id: str,
    request: Request,
    service: CalibrationAPIService = Depends(_service),
    config: CLM05APIConfig = Depends(_config),
) -> dict[str, Any]:
    require_mutation_auth(request, config)
    result = service.select_profile(
        participant_id,
        profile_id=profile_id,
    )
    return {
        "profile_id": result.profile_id,
        "profile_version": result.profile_version,
        "reason": result.reason,
    }


@router.get("/participants/{participant_id}/calibration-status")
def calibration_status(
    participant_id: str,
    service: CalibrationAPIService = Depends(_service),
) -> dict[str, Any]:
    return service.calibration_status(participant_id)
