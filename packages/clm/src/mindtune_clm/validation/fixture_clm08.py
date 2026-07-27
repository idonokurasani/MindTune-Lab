"""Synthetic scenarios and fixtures for CLM-08 testing."""

from __future__ import annotations

import random
import uuid
from dataclasses import replace

from mindtune_clm.validation.analysis_plan import (
    AnalysisPlan,
    MissingDataPolicy,
    MultiplicityMethod,
    Population,
    SensitivitySpec,
)
from mindtune_clm.validation.assignment import assign_conditions
from mindtune_clm.validation.datasets import AnalysisDataset, AnalysisRow
from mindtune_clm.validation.designs import Condition, ConditionType, StudyDefinition, StudyStatus
from mindtune_clm.validation.deviations import (
    DeviationCategory,
    DeviationSeverity,
    ProtocolDeviation,
)
from mindtune_clm.validation.endpoints import Endpoint, EndpointDirection, EndpointType
from mindtune_clm.validation.estimands import Estimand
from mindtune_clm.validation.hypotheses import Hypothesis


def _make_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def immediate_recall_endpoint() -> Endpoint:
    return Endpoint(
        endpoint_id="ep-immediate-recall",
        name="Immediate recall accuracy",
        endpoint_type=EndpointType.PRIMARY,
        metric="proportion correct",
        timepoint="immediate",
        expected_direction=EndpointDirection.HIGHER,
    )


def response_time_endpoint() -> Endpoint:
    return Endpoint(
        endpoint_id="ep-rt-correct",
        name="Response time among correct responses",
        endpoint_type=EndpointType.SECONDARY,
        metric="median response time ms",
        timepoint="immediate",
        expected_direction=EndpointDirection.LOWER,
    )


def adaptive_fixed_estimand() -> Estimand:
    return Estimand(
        estimand_id="est-adaptive-vs-fixed",
        population="eligible Hebrew-learning sessions",
        treatment_condition="adaptive",
        comparator="fixed",
        outcome_variable="immediate recall accuracy",
        intercurrent_event_handling="no imputation; missing treated as conservative failure",
        summary_measure="participant-level mean difference",
        directionality="superiority",
    )


def primary_hypothesis() -> Hypothesis:
    return Hypothesis(
        hypothesis_id="h1-adaptive-fixed",
        type="confirmatory",
        null_statement="adaptive CLM presentation does not improve immediate recall accuracy relative to fixed baseline",
        alternative_statement="adaptive CLM presentation improves immediate recall accuracy relative to fixed baseline",
        estimand=adaptive_fixed_estimand(),
        endpoint=immediate_recall_endpoint(),
        population="eligible Hebrew-learning sessions",
        comparison="adaptive vs fixed",
        directionality="superiority",
        significance_threshold=0.05,
        multiplicity_family="primary",
        analysis_method="paired permutation test with bootstrap CI",
        missing_data_handling="no imputation",
        sensitivity_analyses=["per-protocol", "complete-case"],
    )


def build_adaptive_vs_fixed_study(study_id: str | None = None) -> StudyDefinition:
    study_id = study_id or _make_id("study")
    return StudyDefinition(
        study_id=study_id,
        study_version=1,
        title="CLM-08 adaptive versus fixed presentation",
        research_question="Does adaptive CLM presentation improve immediate Hebrew recall accuracy relative to fixed baseline presentation?",
        confirmatory=True,
        status=StudyStatus.DRAFT.value,
        hypotheses=[primary_hypothesis()],
        conditions=[
            Condition(
                condition_id="adaptive",
                name="Adaptive CLM",
                description="State estimator, personal calibration, control policy, adaptive audio active",
                condition_type=ConditionType.ADAPTIVE.value,
                components={"state_estimator": True, "control_policy": True},
            ),
            Condition(
                condition_id="fixed",
                name="Fixed baseline",
                description="Same curriculum and items; fixed baseline audio; no adaptive control-state changes",
                condition_type=ConditionType.FIXED.value,
                components={"state_estimator": False, "control_policy": False},
            ),
        ],
        target_population="Adults learning Hebrew via MindTune CLM",
        inclusion_criteria=["adult", "Hebrew-learning session", "valid calibration if required"],
        exclusion_criteria=["missing required calibration", "non-consent"],
        randomization_method="simple",
        blinding_level="participant-blinded",
        allocation_ratio={"adaptive": 1.0, "fixed": 1.0},
        unit_of_randomization="participant",
        primary_endpoint_id="ep-immediate-recall",
        secondary_endpoint_ids=["ep-rt-correct"],
        exploratory_endpoint_ids=[],
        analysis_population=Population.INTENTION_TO_TREAT.value,
        sample_size_rationale={"alpha": 0.05, "power": 0.8, "target_effect": 0.2, "baseline_rate": 0.55},
        stopping_rules=["safety-only interim monitoring"],
        missing_data_policy=MissingDataPolicy.NO_IMPUTATION.value,
        protocol_deviation_policy="record all prespecified deviations; do not delete",
        analysis_plan_version="1.0",
        curriculum_version="curriculum_v1_320",
        protocol_version="clm-08-validation.v1",
        calibration_requirement="required",
        clm_component_versions={"clm": "0.1.0", "mpe": "1.1"},
        safety_policy_version="clm-04b.v1.0.0",
        registration_status="not_registered",
    )


def build_sham_study(study_id: str | None = None) -> StudyDefinition:
    study_id = study_id or _make_id("sham-study")
    study = build_adaptive_vs_fixed_study(study_id)
    conditions = [
        c for c in study.conditions if c.condition_id == "adaptive"
    ] + [
        Condition(
            condition_id="sham",
            name="Sham adaptation",
            description="Apparent audio variation independent of participant state; no live cognitive-state estimate",
            condition_type=ConditionType.SHAM.value,
            components={"sham": True},
        ),
    ]
    return replace(
        study,
        study_id=study_id,
        title="CLM-08 adaptive versus sham adaptation",
        research_question="Does adaptive CLM presentation differ from sham adaptation?",
        conditions=conditions,
        randomization_method="blocked",
    )


def build_crossover_study(study_id: str | None = None) -> StudyDefinition:
    study_id = study_id or _make_id("crossover-study")
    study = build_adaptive_vs_fixed_study(study_id)
    return replace(
        study,
        study_id=study_id,
        title="CLM-08 adaptive versus fixed crossover",
        research_question="Within participants, does adaptive presentation improve immediate recall?",
        randomization_method="crossover",
        blinding_level="assessor-blinded",
    )


def build_default_plan(study: StudyDefinition) -> AnalysisPlan:
    return AnalysisPlan(
        plan_id=_make_id("plan"),
        study_id=study.study_id,
        study_version=study.study_version,
        primary_hypothesis_id="h1-adaptive-fixed",
        population=study.analysis_population,
        missing_data_policy=MissingDataPolicy.NO_IMPUTATION.value,
        multiplicity_method=MultiplicityMethod.NONE.value,
        alpha=0.05,
        sensitivity_specs=[
            SensitivitySpec(
                name="per-protocol",
                description="Exclude protocol-deviation rows",
                population_filter="per-protocol",
            ),
            SensitivitySpec(
                name="high-sensor-quality",
                description="Exclude low sensor-quality rows",
                population_filter="high-sensor-quality",
            ),
            SensitivitySpec(
                name="exclude-first-period",
                description="Exclude first crossover period",
                exclude_first_period=True,
            ),
        ],
    )


def build_participants(n: int = 12, seed: int = 42) -> list[str]:
    rng = random.Random(seed)
    return [f"p-{i:03d}-{rng.randint(1000, 9999)}" for i in range(n)]


def build_synthetic_dataset(
    study: StudyDefinition,
    participants: list[str],
    seed: int = 42,
    include_deviation: bool = False,
    include_corrupted: bool = False,
) -> tuple[AnalysisDataset, list[ProtocolDeviation]]:
    rng = random.Random(seed)
    assignments = assign_conditions(study, participants, seed)
    condition_accuracy = {"adaptive": 0.72, "fixed": 0.55, "sham": 0.56}
    rows: list[AnalysisRow] = []
    session_map: dict[str, str] = {}
    deviations: list[ProtocolDeviation] = []

    base_timestamp = 1_700_000_000.0 + float(seed)
    for a in assignments:
        session_id = f"sess-{a.participant_id}-{a.period}-{seed}"
        session_map[a.participant_id] = session_id
        acc = condition_accuracy.get(a.condition_id, 0.55)
        n_trials = 10
        for t in range(n_trials):
            correct = rng.random() < acc
            rt = rng.gauss(1500, 400) if correct else rng.gauss(2200, 600)
            rt = max(100.0, rt)
            rows.append(
                AnalysisRow(
                    study_id=study.study_id,
                    study_version=study.study_version,
                    participant_id=a.participant_id,
                    session_id=session_id,
                    period=a.period,
                    sequence_order=a.sequence_order,
                    condition=a.condition_id,
                    protocol_version=study.protocol_version,
                    curriculum_version=study.curriculum_version,
                    calibration_profile=study.calibration_requirement,
                    trial_id=f"t-{t:03d}",
                    item_id=f"item-{rng.randint(1, 320):03d}",
                    response="correct" if correct else "incorrect",
                    correct=correct,
                    response_time_ms=rt,
                    confidence=rng.uniform(1, 5),
                    error_types=[] if correct else ["form_error"],
                    clm_state={"control_state": "adaptive" if a.condition_id == "adaptive" else "fixed"},
                    intervention_exposure=1.0,
                    audio_artifact=None,
                    safety_events=[],
                    sensor_quality_summary={"quality": "high"},
                    inclusion_flags={"assigned": True, "protocol_adherent": True},
                    deviation_flags=[],
                    timestamp=base_timestamp + t,
                )
            )

    if include_corrupted and rows:
        first = rows[0]
        rows[0] = AnalysisRow(
            **{
                **first.as_dict(),
                "event_chain_corrupted": True,
            }
        )

    if include_deviation and session_map:
        victim_session = list(session_map.values())[0]
        victim_participant = list(session_map.keys())[0]
        deviation = ProtocolDeviation.create(
            session_id=victim_session,
            participant_pseudonym=victim_participant,
            study_id=study.study_id,
            study_version=study.study_version,
            category=DeviationCategory.WRONG_VOICE_ASSET.value,
            severity=DeviationSeverity.MAJOR.value,
            description="Wrong Aaron asset used for one trial",
            prespecified_consequence="report and retain",
            inclusion_impact="may exclude from per-protocol",
        )
        deviations.append(deviation)
        # tag rows in that session
        new_rows: list[AnalysisRow] = []
        for r in rows:
            if r.session_id == victim_session:
                new_rows.append(
                    AnalysisRow(
                        **{
                            **r.as_dict(),
                            "deviation_flags": [DeviationCategory.WRONG_VOICE_ASSET.value],
                        }
                    )
                )
            else:
                new_rows.append(r)
        rows = new_rows

    return AnalysisDataset.build(rows, population="intention-to-treat", study_id=study.study_id, study_version=study.study_version), deviations


def make_protocol_deviation(
    session_id: str, participant_pseudonym: str, study: StudyDefinition
) -> ProtocolDeviation:
    return ProtocolDeviation.create(
        session_id=session_id,
        participant_pseudonym=participant_pseudonym,
        study_id=study.study_id,
        study_version=study.study_version,
        category=DeviationCategory.SENSOR_UNAVAILABLE.value,
        severity=DeviationSeverity.CRITICAL.value,
        description="Sensor unavailable during session",
        prespecified_consequence="exclude from per-protocol sensor-quality subset",
        inclusion_impact="sensor-quality subset exclusion",
    )
