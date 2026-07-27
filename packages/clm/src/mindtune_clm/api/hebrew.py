"""CLM-06 Hebrew adaptive API routes."""

from __future__ import annotations

import time
import uuid
from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from mindtune_clm.hebrew_slice import (
    HebrewAdaptiveSession,
    HebrewSessionError,
    make_clm06_test_fixture,
)
from mindtune_clm.hebrew_slice.curriculum_adapter import HebrewCurriculumAdapter
from mindtune_clm.hebrew_slice.models import HebrewAdaptiveItem

router = APIRouter(tags=["hebrew"])


class HebrewAPIService:
    """In-memory service for the Hebrew adaptive vertical slice."""

    def __init__(self) -> None:
        self._adapter = HebrewCurriculumAdapter()
        self._approved = self._adapter.approved_items()
        _, self._registry, _ = make_clm06_test_fixture(point_duration=0.3)
        self._asset_inventory = {a.asset_id for a in self._registry.assets()}
        self._items: dict[str, HebrewAdaptiveItem] = {i.item_id: i for i in self._approved}
        self._sessions: dict[str, HebrewAdaptiveSession] = {}
        self._responses: set[str] = set()

    def readiness(self) -> dict[str, Any]:
        return self._adapter.readiness_report(self._asset_inventory)

    def list_items(self) -> dict[str, Any]:
        return {"items": [i.as_dict() for i in self._approved], "count": len(self._approved)}

    def get_item(self, item_id: str) -> dict[str, Any]:
        item = self._items.get(item_id)
        if item is None:
            raise HTTPException(status_code=404, detail="hebrew_item_not_found")
        return item.as_dict()

    def item_readiness(self, item_id: str) -> dict[str, Any]:
        item = self._items.get(item_id)
        if item is None:
            raise HTTPException(status_code=404, detail="hebrew_item_not_found")
        missing = [a for a in item.required_audio_asset_ids if a not in self._asset_inventory]
        return {
            "item_id": item_id,
            "ready": not missing,
            "missing_audio_assets": missing,
            "blocking_reasons": [f"missing: {missing}"] if missing else [],
        }

    def create_session(self, learner_id: str = "anonymous", parameters: dict[str, Any] | None = None) -> str:
        session_id = f"heb-{uuid.uuid4().hex[:16]}"
        session = HebrewAdaptiveSession(
            session_id=session_id,
            items=self._approved,
            asset_registry=self._registry,
            max_trials=int((parameters or {}).get("max_trials", 20)),
            clock=time.time,
        )
        session.start()
        self._sessions[session_id] = session
        return session_id

    def get_session_state(self, session_id: str) -> dict[str, Any]:
        session = self._sessions.get(session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="hebrew_session_not_found")
        return session.summary()

    def current_trial(self, session_id: str) -> dict[str, Any]:
        session = self._sessions.get(session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="hebrew_session_not_found")
        if session.current_trial is None:
            return {"status": "no_active_trial", "session_summary": session.summary()}
        return session.current_trial.as_dict()

    def submit_response(
        self,
        session_id: str,
        trial_id: str,
        response_text: str,
        response_time_ms: float,
        confidence: int,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        session = self._sessions.get(session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="hebrew_session_not_found")
        if session.current_trial is None or session.current_trial.trial_id != trial_id:
            raise HTTPException(status_code=400, detail="trial_id_mismatch")
        response_id = idempotency_key or f"{session_id}-{trial_id}-{uuid.uuid4().hex[:8]}"
        if response_id in self._responses:
            return session._duplicate_response_result(response_id)
        self._responses.add(response_id)
        try:
            return session.respond(
                raw_response=response_text,
                response_time_ms=response_time_ms,
                confidence=confidence,
                response_id=response_id,
            )
        except HebrewSessionError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    def learning_summary(self, session_id: str) -> dict[str, Any]:
        session = self._sessions.get(session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="hebrew_session_not_found")
        return {
            "session_id": session_id,
            "learning_states": {k: v.as_dict() for k, v in session.learning_states.items()},
            "event_count": len(session.event_log.events),
        }

    def shutdown(self) -> None:
        for session in self._sessions.values():
            if not session.completed and not session.aborted:
                session.stop(reason="api_shutdown")


def _service(request: Request) -> HebrewAPIService:
    if not hasattr(request.app.state, "hebrew_service"):
        request.app.state.hebrew_service = HebrewAPIService()
    return cast(HebrewAPIService, request.app.state.hebrew_service)


class HebrewSessionCreate(BaseModel):
    learner_id: str = "anonymous"
    parameters: dict[str, Any] = Field(default_factory=dict)


class HebrewResponseSubmit(BaseModel):
    response_text: str
    response_time_ms: float = 1500.0
    confidence: int = 5
    idempotency_key: str | None = None


@router.get("/hebrew/readiness")
def hebrew_readiness(service: HebrewAPIService = Depends(_service)) -> dict[str, Any]:
    return service.readiness()


@router.get("/hebrew/items")
def list_hebrew_items(service: HebrewAPIService = Depends(_service)) -> dict[str, Any]:
    return service.list_items()


@router.get("/hebrew/items/{item_id}")
def get_hebrew_item(item_id: str, service: HebrewAPIService = Depends(_service)) -> dict[str, Any]:
    return service.get_item(item_id)


@router.get("/hebrew/items/{item_id}/readiness")
def hebrew_item_readiness(item_id: str, service: HebrewAPIService = Depends(_service)) -> dict[str, Any]:
    return service.item_readiness(item_id)


@router.post("/hebrew/sessions")
def create_hebrew_session(data: HebrewSessionCreate, service: HebrewAPIService = Depends(_service)) -> dict[str, Any]:
    session_id = service.create_session(data.learner_id, data.parameters)
    return {"session_id": session_id, "status": "created"}


@router.get("/sessions/{session_id}/hebrew/state")
def hebrew_session_state(session_id: str, service: HebrewAPIService = Depends(_service)) -> dict[str, Any]:
    return service.get_session_state(session_id)


@router.get("/sessions/{session_id}/trials/current")
def hebrew_current_trial(session_id: str, service: HebrewAPIService = Depends(_service)) -> dict[str, Any]:
    return service.current_trial(session_id)


@router.post("/sessions/{session_id}/trials/{trial_id}/response")
def submit_hebrew_response(
    session_id: str,
    trial_id: str,
    data: HebrewResponseSubmit,
    service: HebrewAPIService = Depends(_service),
) -> dict[str, Any]:
    return service.submit_response(
        session_id=session_id,
        trial_id=trial_id,
        response_text=data.response_text,
        response_time_ms=data.response_time_ms,
        confidence=data.confidence,
        idempotency_key=data.idempotency_key,
    )


@router.get("/sessions/{session_id}/learning-summary")
def hebrew_learning_summary(session_id: str, service: HebrewAPIService = Depends(_service)) -> dict[str, Any]:
    return service.learning_summary(session_id)
