"""Typed errors for the CLM-05 experimental API."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from fastapi import HTTPException


@dataclass
class APIErrorDetail:
    """Stable, safe error detail returned to API clients."""

    code: str
    message: str
    request_id: str
    resource_id: str | None
    retryable: bool
    details: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "request_id": self.request_id,
            "resource_id": self.resource_id,
            "retryable": self.retryable,
            "details": self.details,
        }


class CLM05APIError(Exception):
    """Base exception for the CLM-05 API."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 500,
        request_id: str = "",
        resource_id: str | None = None,
        retryable: bool = False,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.request_id = request_id
        self.resource_id = resource_id
        self.retryable = retryable
        self.details = details or {}

    def to_http(self) -> HTTPException:
        detail = APIErrorDetail(
            code=self.code,
            message=self.message,
            request_id=self.request_id,
            resource_id=self.resource_id,
            retryable=self.retryable,
            details=self.details,
        )
        return HTTPException(status_code=self.status_code, detail=detail.as_dict())


class NotFoundError(CLM05APIError):
    def __init__(self, resource_id: str, request_id: str = "") -> None:
        super().__init__(
            code="resource_not_found",
            message=f"Resource {resource_id} not found",
            status_code=404,
            request_id=request_id,
            resource_id=resource_id,
            retryable=False,
        )


class ConflictError(CLM05APIError):
    def __init__(self, resource_id: str, message: str, request_id: str = "") -> None:
        super().__init__(
            code="resource_conflict",
            message=message,
            status_code=409,
            request_id=request_id,
            resource_id=resource_id,
            retryable=False,
        )


class IdempotencyConflictError(CLM05APIError):
    def __init__(self, idempotency_key: str, request_id: str = "") -> None:
        super().__init__(
            code="idempotency_conflict",
            message=f"Idempotency key {idempotency_key} reused with a different payload",
            status_code=422,
            request_id=request_id,
            resource_id=idempotency_key,
            retryable=False,
        )


class StateMachineError(CLM05APIError):
    def __init__(self, resource_id: str, transition: str, request_id: str = "") -> None:
        super().__init__(
            code="invalid_state_transition",
            message=f"Cannot perform {transition} on {resource_id}",
            status_code=400,
            request_id=request_id,
            resource_id=resource_id,
            retryable=False,
        )


class ResourceLockedError(CLM05APIError):
    def __init__(self, resource: str, owner: str, request_id: str = "") -> None:
        super().__init__(
            code="resource_locked",
            message=f"Resource {resource} is held by {owner}",
            status_code=423,
            request_id=request_id,
            resource_id=resource,
            retryable=True,
        )


class AuthorizationError(CLM05APIError):
    def __init__(self, request_id: str = "") -> None:
        super().__init__(
            code="unauthorized",
            message="Mutation requires a valid bearer token",
            status_code=401,
            request_id=request_id,
            resource_id=None,
            retryable=False,
        )
