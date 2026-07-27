"""CLM-05 FastAPI application factory."""

from __future__ import annotations

import asyncio
import uuid
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from mindtune_clm.api import (
    __version__,
    control,
    events,
    experiments,
    exports,
    health,
    protocols,
    sensors,
    sessions,
    stimuli,
)
from mindtune_clm.api.config import CLM05APIConfig
from mindtune_clm.api.errors import CLM05APIError
from mindtune_clm.api.security import RequestSizeLimitMiddleware
from mindtune_clm.api.services import CLM05Service


def _setup_middlewares(app: FastAPI, config: CLM05APIConfig) -> None:
    app.add_middleware(RequestSizeLimitMiddleware, max_bytes=config.max_request_bytes)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.allowed_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )


def _setup_routers(app: FastAPI) -> None:
    app.include_router(health.router, prefix="/api/v1")
    app.include_router(experiments.router, prefix="/api/v1")
    app.include_router(protocols.router, prefix="/api/v1")
    app.include_router(sessions.router, prefix="/api/v1")
    app.include_router(sensors.router, prefix="/api/v1")
    app.include_router(stimuli.router, prefix="/api/v1")
    app.include_router(control.router, prefix="/api/v1")
    app.include_router(events.router, prefix="/api/v1")
    app.include_router(exports.router, prefix="/api/v1")


def _setup_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(CLM05APIError)
    async def handle_clm05_error(request: Request, exc: CLM05APIError) -> JSONResponse:
        detail = {
            "code": exc.code,
            "message": exc.message,
            "request_id": exc.request_id or str(uuid.uuid4()),
            "resource_id": exc.resource_id,
            "retryable": exc.retryable,
            "details": exc.details,
        }
        return JSONResponse(status_code=exc.status_code, content=detail)

    @app.exception_handler(HTTPException)
    async def handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
        if isinstance(exc.detail, dict):
            return JSONResponse(status_code=exc.status_code, content=exc.detail)
        return JSONResponse(status_code=exc.status_code, content={"message": str(exc.detail)})


def create_app(config: CLM05APIConfig | None = None) -> FastAPI:
    """Create and configure the CLM-05 FastAPI application."""
    config = config or CLM05APIConfig.from_env()
    service = CLM05Service(config)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        service.accepting_mutations = True
        try:
            yield
        finally:
            service.accepting_mutations = False
            await asyncio.to_thread(service.shutdown)

    app = FastAPI(
        title=config.app_name,
        version=__version__,
        lifespan=lifespan,
    )
    app.state.config = config
    app.state.service = service

    _setup_middlewares(app, config)
    _setup_routers(app)
    _setup_exception_handlers(app)

    @app.get("/")
    async def root() -> dict[str, Any]:
        return {
            "name": config.app_name,
            "api_version": config.api_version,
            "version": __version__,
        }

    return app
