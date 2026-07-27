"""CLM-06B Hebrew curriculum and adaptive progression API routes.

These routes extend the CLM-05/CLM-06 Hebrew surface with versioned curriculum
readiness, skill graph, learner-state, and deterministic progression.  They do
not replace the existing CLM-06 adaptive routes; they sit alongside them under
/api/v1/hebrew/...
"""

from __future__ import annotations

import uuid
from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from mindtune_clm.hebrew_slice import (
    HebrewCurriculumReadinessEvaluator,
    HebrewLearnerModel,
    HebrewPrerequisiteGraph,
    HebrewProgressionEngine,
    build_clm06b_curriculum,
    make_clm06_test_fixture,
)
from mindtune_clm.hebrew_slice.models import HebrewResponse
from mindtune_clm.hebrew_slice.scoring import score_response
from mpe.domains.hebrew.normalization import normalize_hebrew_response

router = APIRouter(tags=["hebrew"])


class HebrewCurriculumAPIService:
    """In-memory CLM-06B curriculum service pinned to a single curriculum version."""

    def __init__(self) -> None:
        self._curriculum = build_clm06b_curriculum()
        _, registry, _ = make_clm06_test_fixture(point_duration=0.3)
        self._asset_inventory = {a.asset_id for a in registry.assets()}
        self._evaluator = HebrewCurriculumReadinessEvaluator(self._curriculum, self._asset_inventory)
        self._sessions: dict[str, dict[str, Any]] = {}
        self._processed_keys: set[str] = set()
        self._engine = HebrewProgressionEngine()
        self._prereq_graph = HebrewPrerequisiteGraph(self._curriculum)

    def _first_active_item(self) -> str | None:
        for item in self._curriculum.items:
            if item.active_learning_eligible and not item.reference_only:
                return item.item_id
        return None

    def _ensure_session(self, session_id: str, learner_id: str = "anonymous") -> dict[str, Any]:
        if session_id not in self._sessions:
            first = self._first_active_item()
            if first is None:
                raise HTTPException(status_code=503, detail="no_active_curriculum_items")
            self._sessions[session_id] = {
                "session_id": session_id,
                "learner_id": learner_id,
                "pinned_curriculum_version": self._curriculum.version,
                "learner": HebrewLearnerModel(
                    learner_id=learner_id,
                    session_id=session_id,
                    pinned_curriculum_version=self._curriculum.version,
                ),
                "current_item_id": first,
                "semantic_time": 0.0,
                "last_decision": None,
            }
        return self._sessions[session_id]

    def list_curricula(self) -> list[dict[str, Any]]:
        return [
            {
                "curriculum_id": self._curriculum.curriculum_id,
                "version": self._curriculum.version,
                "base_version": self._curriculum.base_version,
            }
        ]

    def get_curriculum(self, curriculum_id: str) -> dict[str, Any]:
        if curriculum_id != self._curriculum.curriculum_id:
            raise HTTPException(status_code=404, detail="curriculum_not_found")
        return self._curriculum.as_dict()

    def curriculum_versions(self, curriculum_id: str) -> list[dict[str, Any]]:
        if curriculum_id != self._curriculum.curriculum_id:
            raise HTTPException(status_code=404, detail="curriculum_not_found")
        return [
            {
                "version": self._curriculum.version,
                "base_version": self._curriculum.base_version,
                "source_provenance": self._curriculum.source_provenance,
                "immutable": True,
            }
        ]

    def curriculum_readiness(self, curriculum_id: str) -> dict[str, Any]:
        if curriculum_id != self._curriculum.curriculum_id:
            raise HTTPException(status_code=404, detail="curriculum_not_found")
        return self._evaluator.evaluate().as_dict()

    def list_units(self) -> dict[str, Any]:
        return {"units": [u.as_dict() for u in self._curriculum.units]}

    def get_unit(self, unit_id: str) -> dict[str, Any]:
        unit = self._curriculum.unit_by_id.get(unit_id)
        if unit is None:
            raise HTTPException(status_code=404, detail="unit_not_found")
        return unit.as_dict()

    def list_skills(self) -> dict[str, Any]:
        return {"skills": [s.as_dict() for s in self._curriculum.skills]}

    def get_learner_state(self, session_id: str) -> dict[str, Any]:
        session = self._ensure_session(session_id)
        return cast(dict[str, Any], session["learner"].as_dict())

    def get_progression(self, session_id: str) -> dict[str, Any]:
        session = self._ensure_session(session_id)
        item = self._curriculum.item_by_id.get(session["current_item_id"])
        if item is None:
            raise HTTPException(status_code=404, detail="current_item_not_found")
        decision = self._engine.decide(
            self._curriculum,
            session["learner"],
            item,
            score_response(item.item, self._stub_response(item.item)),
            self._stub_response(item.item),
            control_state={"assistance_level": 0.0},
        )
        return {
            "session_id": session_id,
            "curriculum_version": session["pinned_curriculum_version"],
            "current_item_id": session["current_item_id"],
            "decision": decision.as_dict(),
        }

    def next_progression(self, session_id: str, request_data: "NextProgressionRequest") -> dict[str, Any]:
        session = self._ensure_session(session_id)
        # Idempotency: a processed key returns the same deterministic decision.
        idem_key = request_data.idempotency_key or f"{session_id}-{request_data.response_text}-{request_data.confidence}"
        if idem_key in self._processed_keys:
            cached = session.get("last_decision")
            if cached is not None:
                return {"session_id": session_id, "curriculum_version": session["pinned_curriculum_version"], "decision": cached, "idempotent": True}

        item = self._curriculum.item_by_id.get(session["current_item_id"])
        if item is None:
            raise HTTPException(status_code=404, detail="current_item_not_found")

        session["semantic_time"] += 1.0
        response = HebrewResponse(
            response_id=f"resp-{uuid.uuid4().hex[:12]}",
            trial_id="trial-0",
            item_id=item.item_id,
            prompt_id="prompt-0",
            presentation_id="pres-0",
            raw_response=request_data.response_text,
            normalized_response=normalize_hebrew_response(request_data.response_text),
            response_semantic_timestamp=session["semantic_time"],
            response_time_ms=request_data.response_time_ms,
            confidence=request_data.confidence,
            hint_used=False,
            replay_count=0,
            audio_assistance_level=request_data.audio_assistance_level,
        )
        score = score_response(item.item, response)
        session["learner"].update(self._curriculum, item, response, score, session["semantic_time"])

        decision = self._engine.decide(
            self._curriculum,
            session["learner"],
            item,
            score,
            response,
            control_state={"assistance_level": request_data.audio_assistance_level},
        )
        session["last_decision"] = decision.as_dict()
        self._processed_keys.add(idem_key)

        # Move to the decided next item when one is supplied and eligible.
        if decision.next_item_id and decision.next_item_id in self._curriculum.item_by_id:
            next_item = self._curriculum.item_by_id[decision.next_item_id]
            eligible, _ = session["learner"].is_eligible(next_item, self._prereq_graph)
            if eligible or decision.action in ("baseline_lock_progression", "continue"):
                session["current_item_id"] = next_item.item_id

        return {
            "session_id": session_id,
            "curriculum_version": session["pinned_curriculum_version"],
            "decision": decision.as_dict(),
            "score": score.as_dict(),
            "idempotent": False,
        }

    @staticmethod
    def _stub_response(item: Any) -> HebrewResponse:
        return HebrewResponse(
            response_id="stub",
            trial_id="trial-stub",
            item_id=getattr(item, "item_id", ""),
            prompt_id="prompt-stub",
            presentation_id="pres-stub",
            raw_response="",
            normalized_response="",
            response_semantic_timestamp=0.0,
            response_time_ms=1500.0,
            confidence=5,
            hint_used=False,
            replay_count=0,
            audio_assistance_level=0.0,
        )


def _service(request: Request) -> HebrewCurriculumAPIService:
    service = getattr(request.app.state, "hebrew_clm06b_service", None)
    if service is None:
        service = HebrewCurriculumAPIService()
        request.app.state.hebrew_clm06b_service = service
    return service


class CurriculaListResponse(BaseModel):
    curricula: list[dict[str, Any]]


class NextProgressionRequest(BaseModel):
    response_text: str = ""
    response_time_ms: float = 1500.0
    confidence: int = 5
    trial_type: str = "italian_to_hebrew"
    audio_assistance_level: float = 0.0
    idempotency_key: str | None = Field(default=None)


@router.get("/hebrew/curricula")
def list_curricula(service: HebrewCurriculumAPIService = Depends(_service)) -> CurriculaListResponse:
    return CurriculaListResponse(curricula=service.list_curricula())


@router.get("/hebrew/curricula/{curriculum_id}")
def get_curriculum(curriculum_id: str, service: HebrewCurriculumAPIService = Depends(_service)) -> dict[str, Any]:
    return service.get_curriculum(curriculum_id)


@router.get("/hebrew/curricula/{curriculum_id}/versions")
def get_curriculum_versions(curriculum_id: str, service: HebrewCurriculumAPIService = Depends(_service)) -> list[dict[str, Any]]:
    return service.curriculum_versions(curriculum_id)


@router.get("/hebrew/curricula/{curriculum_id}/readiness")
def get_curriculum_readiness(curriculum_id: str, service: HebrewCurriculumAPIService = Depends(_service)) -> dict[str, Any]:
    return service.curriculum_readiness(curriculum_id)


@router.get("/hebrew/units")
def list_units(service: HebrewCurriculumAPIService = Depends(_service)) -> dict[str, Any]:
    return service.list_units()


@router.get("/hebrew/units/{unit_id}")
def get_unit(unit_id: str, service: HebrewCurriculumAPIService = Depends(_service)) -> dict[str, Any]:
    return service.get_unit(unit_id)


@router.get("/hebrew/skills")
def list_skills(service: HebrewCurriculumAPIService = Depends(_service)) -> dict[str, Any]:
    return service.list_skills()


@router.get("/hebrew/learner-state/{session_id}")
def get_learner_state(session_id: str, service: HebrewCurriculumAPIService = Depends(_service)) -> dict[str, Any]:
    return service.get_learner_state(session_id)


@router.get("/hebrew/progression/{session_id}")
def get_progression(session_id: str, service: HebrewCurriculumAPIService = Depends(_service)) -> dict[str, Any]:
    return service.get_progression(session_id)


@router.post("/hebrew/progression/{session_id}/next")
def post_next_progression(
    session_id: str,
    data: NextProgressionRequest,
    service: HebrewCurriculumAPIService = Depends(_service),
) -> dict[str, Any]:
    return service.next_progression(session_id, data)
