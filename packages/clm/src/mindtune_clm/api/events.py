"""Event and SSE routes for the CLM-05 API."""

from __future__ import annotations

import json
import queue
import time
from typing import Any, cast

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse

from mindtune_clm.api.config import CLM05APIConfig
from mindtune_clm.api.dependencies import get_service
from mindtune_clm.api.models import EventList
from mindtune_clm.api.security import require_mutation_auth
from mindtune_clm.api.services import CLM05Service

router = APIRouter(tags=["events"])


def _config(request: Request) -> CLM05APIConfig:
    return cast(CLM05APIConfig, request.app.state.config)


def _to_sse(data: dict[str, Any]) -> str:
    return f"data: {json.dumps(data, separators=(',', ':'), default=str)}\n\n"


@router.get("/events", response_model=EventList)
def get_events(
    session_id: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: CLM05Service = Depends(get_service),
) -> dict[str, Any]:
    if session_id:
        return service.list_events(session_id, page, page_size)
    # Global events: flatten across sessions if no session filter.
    all_items: list[dict[str, Any]] = []
    for sid in service.sessions:
        result = service.list_events(sid, page, page_size)
        all_items.extend(result["items"])
    return {
        "session_id": "*",
        "page": page,
        "page_size": page_size,
        "total": len(all_items),
        "items": all_items,
    }


@router.get("/sessions/{session_id}/events", response_model=EventList)
def get_session_events(
    session_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: CLM05Service = Depends(get_service),
) -> dict[str, Any]:
    return service.list_events(session_id, page, page_size)


@router.get("/sessions/{session_id}/events/stream")
def get_session_events_stream(
    session_id: str,
    request: Request,
    last_event_id: str | None = Query(None),
    service: CLM05Service = Depends(get_service),
    config: CLM05APIConfig = Depends(_config),
) -> StreamingResponse:
    require_mutation_auth(request, config)

    def generator() -> Any:
        q = service.sse_event_stream(session_id, last_event_id)
        # Yield queued events.
        while True:
            try:
                event = q.get(block=False)
                if event is None:
                    break
                yield _to_sse(event)
            except queue.Empty:
                break
        # Heartbeats and a brief wait for new events.
        for _ in range(5):
            yield ":heartbeat\n\n"
            try:
                event = q.get(timeout=0.1)
                if event is not None:
                    yield _to_sse(event)
            except queue.Empty:
                pass
            time.sleep(0.01)

    return StreamingResponse(generator(), media_type="text/event-stream")
