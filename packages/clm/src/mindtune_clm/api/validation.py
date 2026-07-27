"""CLM-08 scientific-validation API routes."""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Callable, cast

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict

from mindtune_clm.api.config import CLM05APIConfig
from mindtune_clm.api.security import require_mutation_auth
from mindtune_clm.validation.analysis_plan import AnalysisResult, run_primary_analysis
from mindtune_clm.validation.assignment import Assignment, assign_conditions
from mindtune_clm.validation.datasets import AnalysisDataset, apply_deviation_flags
from mindtune_clm.validation.designs import StudyDefinition, StudyStatus
from mindtune_clm.validation.deviations import ProtocolDeviation
from mindtune_clm.validation.events import CLM08EventType, ValidationEvent, ValidationEventLog
from mindtune_clm.validation.fixture_clm08 import (
    build_adaptive_vs_fixed_study,
    build_default_plan,
    build_synthetic_dataset,
)
from mindtune_clm.validation.reports import StudyReport, generate_study_report
from mindtune_clm.validation.sensitivity import run_sensitivity_analysis

router = APIRouter(tags=["studies"])


def _config(request: Request) -> CLM05APIConfig:
    return cast(CLM05APIConfig, request.app.state.config)


class StudyCreate(BaseModel):
    title: str
    research_question: str
    model_config = ConfigDict(extra="allow")


class ParticipantsCreate(BaseModel):
    participant_ids: list[str]
    seed: int = 42
    idempotency_key: str | None = None


class AnalysisCreate(BaseModel):
    hypothesis_id: str = "h1-adaptive-fixed"
    seed: int | None = None
    idempotency_key: str | None = None


class ReportCreate(BaseModel):
    analysis_id: str
    idempotency_key: str | None = None


class ValidationService:
    """In-memory service for CLM-08 study lifecycle."""

    def __init__(self) -> None:
        self.studies: dict[str, StudyDefinition] = {}
        self.assignments: dict[str, list[Assignment]] = {}
        self.deviations: dict[str, list[ProtocolDeviation]] = {}
        self.analyses: dict[str, AnalysisResult] = {}
        self.reports: dict[str, StudyReport] = {}
        self.idempotency: dict[str, Any] = {}
        self.event_log = ValidationEventLog()
        self.datasets: dict[str, AnalysisDataset] = {}

    def _log(
        self, event_type: str, study_id: str, study_version: int, payload: dict[str, Any]
    ) -> None:
        event = ValidationEvent.create(
            event_type=event_type,
            component="validation_api",
            component_version="1.0",
            study_id=study_id,
            study_version=study_version,
            payload=payload,
        )
        self.event_log.append(event)

    def _idempotent(self, key: str | None, factory: Callable[[], Any]) -> Any:
        if key and key in self.idempotency:
            return self.idempotency[key]
        result = factory()
        if key:
            self.idempotency[key] = result
        return result

    def create_study(self, payload: dict[str, Any]) -> StudyDefinition:
        study = build_adaptive_vs_fixed_study()
        title = payload.get("title", study.title)
        research_question = payload.get("research_question", study.research_question)
        study = replace(study, title=title, research_question=research_question)
        self.studies[study.study_id] = study
        self._log(
            CLM08EventType.STUDY_DEFINITION_CREATED,
            study.study_id,
            study.study_version,
            {"title": title},
        )
        return study

    def get_study(self, study_id: str) -> StudyDefinition:
        if study_id not in self.studies:
            raise HTTPException(status_code=404, detail="study not found")
        return self.studies[study_id]

    def list_studies(self) -> list[StudyDefinition]:
        return list(self.studies.values())

    def validate_study(self, study_id: str) -> dict[str, Any]:
        study = self.get_study(study_id)
        issues: list[str] = []
        if not study.hypotheses:
            issues.append("no hypotheses")
        if not study.conditions:
            issues.append("no conditions")
        if not study.primary_endpoint_id:
            issues.append("no primary endpoint")
        if not study.sample_size_rationale:
            issues.append("no sample size rationale")
        if not issues:
            new = replace(study, status=StudyStatus.VALIDATED.value)
            self.studies[study_id] = new
            self._log(CLM08EventType.STUDY_DEFINITION_VALIDATED, study.study_id, study.study_version, {})
        return {"study_id": study_id, "valid": len(issues) == 0, "issues": issues}

    def preregister_study(self, study_id: str) -> StudyDefinition:
        study = self.get_study(study_id)
        if study.status == StudyStatus.PREREGISTERED.value:
            return study
        new = replace(study, status=StudyStatus.PREREGISTERED.value)
        self.studies[study_id] = new
        self._log(CLM08EventType.STUDY_PREREGISTERED, new.study_id, new.study_version, {})
        return new

    def close_study(self, study_id: str) -> StudyDefinition:
        study = self.get_study(study_id)
        new = replace(study, status=StudyStatus.CLOSED.value)
        self.studies[study_id] = new
        self._log(CLM08EventType.STUDY_CLOSED, new.study_id, new.study_version, {})
        return new

    def create_assignments(
        self, study_id: str, participant_ids: list[str], seed: int
    ) -> list[Assignment]:
        study = self.get_study(study_id)
        assignments = assign_conditions(study, participant_ids, seed)
        self.assignments[study_id] = assignments
        self._log(
            CLM08EventType.CONDITION_RANDOMIZED,
            study.study_id,
            study.study_version,
            {"participants": len(participant_ids), "seed": seed},
        )
        return assignments

    def get_assignment(self, study_id: str, participant_id: str) -> Assignment | None:
        for a in self.assignments.get(study_id, []):
            if a.participant_id == participant_id:
                return a
        return None

    def record_deviation(self, study_id: str, deviation: ProtocolDeviation) -> ProtocolDeviation:
        self.deviations.setdefault(study_id, []).append(deviation)
        study = self.get_study(study_id)
        self._log(
            CLM08EventType.PROTOCOL_DEVIATION_RECORDED,
            study.study_id,
            study.study_version,
            {"deviation_id": deviation.deviation_id, "category": deviation.category},
        )
        return deviation

    def build_analysis_dataset(
        self,
        study_id: str,
        seed: int = 42,
        include_deviation: bool = False,
    ) -> AnalysisDataset:
        study = self.get_study(study_id)
        participants = [a.participant_id for a in self.assignments.get(study_id, [])]
        if not participants:
            participants = [f"p-{i:03d}" for i in range(12)]
        dataset, deviations = build_synthetic_dataset(
            study, participants, seed=seed, include_deviation=include_deviation
        )
        for d in deviations:
            self.record_deviation(study_id, d)
        dataset_rows = apply_deviation_flags(list(dataset.rows), self.deviations.get(study_id, []))
        dataset = AnalysisDataset.build(dataset_rows, population="intention-to-treat", study_id=study_id, study_version=study.study_version)
        self.datasets[study_id] = dataset
        self._log(
            CLM08EventType.ANALYSIS_DATASET_BUILT,
            study.study_id,
            study.study_version,
            {"checksum": dataset.checksum, "rows": len(dataset.rows)},
        )
        return dataset

    def run_analysis(
        self,
        study_id: str,
        hypothesis_id: str,
        seed: int | None = None,
    ) -> AnalysisResult:
        study = self.get_study(study_id)
        dataset = self.datasets.get(study_id) or self.build_analysis_dataset(study_id, seed=seed or 42)
        hypothesis = next((h for h in study.hypotheses if h.hypothesis_id == hypothesis_id), None)
        if not hypothesis:
            raise HTTPException(status_code=404, detail="hypothesis not found")
        plan = build_default_plan(study)
        self._log(
            CLM08EventType.ANALYSIS_RUN_STARTED,
            study.study_id,
            study.study_version,
            {"hypothesis_id": hypothesis_id, "seed": seed},
        )
        result = run_primary_analysis(dataset, plan, hypothesis, seed=seed)
        self.analyses[result.analysis_id] = result
        self._log(
            CLM08EventType.ANALYSIS_RUN_COMPLETED,
            study.study_id,
            study.study_version,
            {"analysis_id": result.analysis_id, "checksum": result.checksum()},
        )
        return result

    def run_sensitivity(
        self,
        study_id: str,
        spec_name: str,
        hypothesis_id: str,
        seed: int | None = None,
    ) -> Any:
        study = self.get_study(study_id)
        dataset = self.datasets.get(study_id) or self.build_analysis_dataset(study_id, seed=seed or 42)
        hypothesis = next((h for h in study.hypotheses if h.hypothesis_id == hypothesis_id), None)
        if not hypothesis:
            raise HTTPException(status_code=404, detail="hypothesis not found")
        plan = build_default_plan(study)
        spec = next((s for s in plan.sensitivity_specs if s.name == spec_name), None)
        if not spec:
            raise HTTPException(status_code=404, detail="sensitivity spec not found")
        result = run_sensitivity_analysis(dataset, spec, plan, hypothesis, seed=seed)
        self._log(
            CLM08EventType.SENSITIVITY_ANALYSIS_COMPLETED,
            study.study_id,
            study.study_version,
            {"spec": spec_name, "analysis_id": result.result.analysis_id},
        )
        return result

    def generate_report(
        self, study_id: str, analysis_id: str
    ) -> StudyReport:
        study = self.get_study(study_id)
        result = self.analyses.get(analysis_id)
        if not result:
            raise HTTPException(status_code=404, detail="analysis not found")
        dataset = self.datasets.get(study_id) or self.build_analysis_dataset(study_id)
        report = generate_study_report(study, dataset, result)
        self.reports[report.report_id] = report
        self._log(
            CLM08EventType.STUDY_REPORT_GENERATED,
            study.study_id,
            study.study_version,
            {"report_id": report.report_id, "checksum": report.checksum()},
        )
        return report


@router.post("/studies", status_code=201)
def create_study(
    data: StudyCreate,
    request: Request,
    config: CLM05APIConfig = Depends(_config),
) -> dict[str, Any]:
    require_mutation_auth(request, config)
    service: ValidationService = request.app.state.validation_service
    return service.create_study(data.model_dump()).as_dict()


@router.get("/studies")
def list_studies(request: Request) -> dict[str, Any]:
    service: ValidationService = request.app.state.validation_service
    return {"items": [s.as_dict() for s in service.list_studies()]}


@router.get("/studies/{study_id}")
def get_study(study_id: str, request: Request) -> dict[str, Any]:
    service: ValidationService = request.app.state.validation_service
    return service.get_study(study_id).as_dict()


@router.post("/studies/{study_id}/validate")
def validate_study(
    study_id: str,
    request: Request,
    config: CLM05APIConfig = Depends(_config),
) -> dict[str, Any]:
    require_mutation_auth(request, config)
    service: ValidationService = request.app.state.validation_service
    return service.validate_study(study_id)


@router.post("/studies/{study_id}/preregister")
def preregister_study(
    study_id: str,
    request: Request,
    config: CLM05APIConfig = Depends(_config),
) -> dict[str, Any]:
    require_mutation_auth(request, config)
    service: ValidationService = request.app.state.validation_service
    return service.preregister_study(study_id).as_dict()


@router.post("/studies/{study_id}/close")
def close_study(
    study_id: str,
    request: Request,
    config: CLM05APIConfig = Depends(_config),
) -> dict[str, Any]:
    require_mutation_auth(request, config)
    service: ValidationService = request.app.state.validation_service
    return service.close_study(study_id).as_dict()


@router.post("/studies/{study_id}/assignments")
def create_assignments(
    study_id: str,
    data: ParticipantsCreate,
    request: Request,
    config: CLM05APIConfig = Depends(_config),
) -> dict[str, Any]:
    require_mutation_auth(request, config)
    service: ValidationService = request.app.state.validation_service
    key = data.idempotency_key
    if key and key in service.idempotency:
        return cast(dict[str, Any], service.idempotency[key])
    assignments = service.create_assignments(study_id, data.participant_ids, data.seed)
    result = {"items": [a.as_dict() for a in assignments]}
    if key:
        service.idempotency[key] = result
    return result


@router.get("/studies/{study_id}/assignments/{participant_id}")
def get_assignment(
    study_id: str,
    participant_id: str,
    request: Request,
    viewer_role: str = "analyst",
) -> dict[str, Any]:
    service: ValidationService = request.app.state.validation_service
    assignment = service.get_assignment(study_id, participant_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="assignment not found")
    return assignment.public_view(viewer_role)


@router.get("/studies/{study_id}/quality")
def get_quality(study_id: str, request: Request) -> dict[str, Any]:
    service: ValidationService = request.app.state.validation_service
    dataset = service.build_analysis_dataset(study_id)
    return dataset.quality.as_dict()


@router.get("/studies/{study_id}/deviations")
def list_deviations(study_id: str, request: Request) -> dict[str, Any]:
    service: ValidationService = request.app.state.validation_service
    items = service.deviations.get(study_id, [])
    return {"items": [d.as_dict() for d in items]}


@router.post("/studies/{study_id}/analyses")
def create_analysis(
    study_id: str,
    data: AnalysisCreate,
    request: Request,
    config: CLM05APIConfig = Depends(_config),
) -> dict[str, Any]:
    require_mutation_auth(request, config)
    service: ValidationService = request.app.state.validation_service
    key = data.idempotency_key
    if key and key in service.idempotency:
        return cast(dict[str, Any], service.idempotency[key])
    result = service.run_analysis(study_id, data.hypothesis_id, seed=data.seed).as_dict()
    if key:
        service.idempotency[key] = result
    return result


@router.get("/studies/{study_id}/analyses")
def list_analyses(study_id: str, request: Request) -> dict[str, Any]:
    service: ValidationService = request.app.state.validation_service
    items = [a.as_dict() for a in service.analyses.values() if a.study_id == study_id]
    return {"items": items}


@router.get("/studies/{study_id}/analyses/{analysis_id}")
def get_analysis(study_id: str, analysis_id: str, request: Request) -> dict[str, Any]:
    service: ValidationService = request.app.state.validation_service
    result = service.analyses.get(analysis_id)
    if not result or result.study_id != study_id:
        raise HTTPException(status_code=404, detail="analysis not found")
    return result.as_dict()


@router.post("/studies/{study_id}/reports")
def create_report(
    study_id: str,
    data: ReportCreate,
    request: Request,
    config: CLM05APIConfig = Depends(_config),
) -> dict[str, Any]:
    require_mutation_auth(request, config)
    service: ValidationService = request.app.state.validation_service
    key = data.idempotency_key
    if key and key in service.idempotency:
        return cast(dict[str, Any], service.idempotency[key])
    report = service.generate_report(study_id, data.analysis_id)
    result = {"report_id": report.report_id, "markdown": report.to_markdown(), "checksum": report.checksum()}
    if key:
        service.idempotency[key] = result
    return result
