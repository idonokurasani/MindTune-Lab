"""Pydantic v2 request/response models for CLM-05."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    ready: bool = False
    blocking_reasons: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    version: str = "0.1.0"


class ReadinessResponse(BaseModel):
    ready: bool
    blocking_reasons: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ExperimentCreate(BaseModel):
    name: str
    protocol_version_id: str | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str | None = None


class ExperimentResponse(BaseModel):
    id: str
    name: str
    protocol_version_id: str | None = None
    parameters: dict[str, Any]
    created_at: float


class ExperimentList(BaseModel):
    items: list[ExperimentResponse]


class ProtocolReference(BaseModel):
    protocol_version_id: str
    name: str
    description: str = ""


class ProtocolList(BaseModel):
    items: list[ProtocolReference]


class SessionCreate(BaseModel):
    experiment_id: str | None = None
    learner_id: str = "anonymous"
    mode: str = "synthetic"  # synthetic, live, replay
    parameters: dict[str, Any] = Field(default_factory=dict)
    protocol_version_id: str = "clm-05-experimental.v1"
    idempotency_key: str | None = None


class SessionResponse(BaseModel):
    id: str
    experiment_id: str | None
    learner_id: str
    mode: str
    status: str
    protocol_version_id: str
    created_at: float
    updated_at: float


class SessionList(BaseModel):
    items: list[SessionResponse]


class ReadinessReport(BaseModel):
    ready: bool
    blocking_reasons: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class SessionTransition(BaseModel):
    target: str
    idempotency_key: str | None = None


class TransitionResponse(BaseModel):
    session_id: str
    previous_status: str
    status: str


class SensorRegister(BaseModel):
    sensor_id: str
    sensor_type: str = "synthetic"
    idempotency_key: str | None = None


class SensorResponse(BaseModel):
    sensor_id: str
    sensor_type: str
    connected: bool
    session_id: str | None = None
    lock_owner: str | None = None


class SensorList(BaseModel):
    items: list[SensorResponse]


class StimulusResponse(BaseModel):
    stimulus_id: str
    label: str
    source_text: str | None = None
    tts_text: str | None = None
    locale: str | None = None
    duration_ms: int | None = None
    available: bool


class StimulusList(BaseModel):
    items: list[StimulusResponse]


class ControlCommand(BaseModel):
    command: str
    idempotency_key: str | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)


class ControlResponse(BaseModel):
    session_id: str
    command: str
    status: str
    details: dict[str, Any] = Field(default_factory=dict)


class EventSummary(BaseModel):
    event_id: str
    event_type: str
    session_sequence_number: int
    timestamp: float
    component: str


class EventList(BaseModel):
    session_id: str
    page: int
    page_size: int
    total: int
    items: list[EventSummary]


class ExportRequest(BaseModel):
    idempotency_key: str | None = None
    format: str = "json"  # json, jsonl


class ExportResponse(BaseModel):
    session_id: str
    export_id: str
    format: str
    download_url: str
    checksum: str
    record_count: int
    redacted: bool


class ErrorResponse(BaseModel):
    code: str
    message: str
    request_id: str
    resource_id: str | None
    retryable: bool
    details: dict[str, Any] = Field(default_factory=dict)


class IdempotencyRecord(BaseModel):
    key: str
    request_id: str
    response: dict[str, Any]
    created_at: float

    model_config = ConfigDict(arbitrary_types_allowed=True)
