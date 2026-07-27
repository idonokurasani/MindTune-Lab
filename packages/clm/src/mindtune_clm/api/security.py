"""Security utilities for the CLM-05 API."""

from __future__ import annotations

import hmac
from typing import Any

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from mindtune_clm.api.config import CLM05APIConfig
from mindtune_clm.api.errors import AuthorizationError


def is_loopback(request: Request) -> bool:
    """Return True when the request originates from a loopback address."""
    host = request.client.host if request.client else None
    if not host:
        return False
    return host in ("127.0.0.1", "::1", "localhost")


def require_mutation_auth(request: Request, config: CLM05APIConfig) -> None:
    """Enforce bearer token for mutating requests when configured."""
    if not config.bearer_token:
        return
    if is_loopback(request):
        return
    header = request.headers.get("authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise AuthorizationError()
    if not hmac.compare_digest(token, config.bearer_token):
        raise AuthorizationError()


def constant_time_compare(provided: str, expected: str) -> bool:
    """Constant-time string comparison."""
    return hmac.compare_digest(provided, expected)


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Reject requests whose bodies exceed the configured byte limit."""

    def __init__(self, app: Any, max_bytes: int) -> None:
        super().__init__(app)
        self.max_bytes = max_bytes

    async def dispatch(self, request: Request, call_next: Any) -> Any:
        from starlette.responses import Response

        content_length = request.headers.get("content-length")
        if content_length:
            try:
                length = int(content_length)
            except ValueError:
                length = 0
            if length > self.max_bytes:
                return Response("request too large", status_code=413, media_type="text/plain")
        body = await request.body()
        if len(body) > self.max_bytes:
            return Response("request too large", status_code=413, media_type="text/plain")
        return await call_next(request)
