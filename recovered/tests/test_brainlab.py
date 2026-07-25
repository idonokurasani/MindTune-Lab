"""Tests for BrainLab delegation and event ordering."""

from uuid import uuid4

import pytest

from mlf.core import (
    BrainLab,
    LearningSession,
    LearningUnit,
    M0Scheduler,
    M0Transformation,
    MinimalProtocolRunner,
    ProtocolSpec,
    Recommendation,
    Response,
    Score,
    Student,
)
from tests.fixtures.mock import MockDomainAdapter, MockScorer


def test_brainlab_defaults_to_m0():
    lab = BrainLab()
    assert isinstance(lab.transformation, M0Transformation)
    assert isinstance(lab.scheduler, M0Scheduler)


def test_brainlab_delegates_prompt_to_domain_adapter():
    lab = BrainLab(domain_adapter=MockDomainAdapter())
    student = Student.create(name="Test")
    session = lab.start_session(student)
    unit = LearningUnit.create(canonical="target", allowed_trial_types=["recall"])
    trial = lab.start_trial(session, unit, "recall", "retrieval")
    assert trial.stimulus == "prompt:target:recall:retrieval"


def test_brainlab_start_trial_requires_stimulus_or_adapter():
    lab = BrainLab()
    student = Student.create(name="Test")
    session = lab.start_session(student)
    unit = LearningUnit.create(canonical="target", allowed_trial_types=["recall"])
    with pytest.raises(ValueError):
        lab.start_trial(session, unit, "recall", "retrieval")


def test_brainlab_delegates_score_to_scorer():
    lab = BrainLab(scorer=MockScorer())
    student = Student.create(name="Test")
    session = lab.start_session(student)
    unit = LearningUnit.create(canonical="target", allowed_trial_types=["recall"])
    trial = lab.start_trial(session, unit, "recall", "retrieval", stimulus="target")
    response = Response(raw="target", normalized="target")
    trial = lab.submit_response(session, trial, response, monotonic_response_ns=1000)
    trial = lab.score_trial(session, trial, unit=unit)

    score_events = list(lab.get_event_stream(session_id=session.session_id).for_type("trial.score"))
    assert len(score_events) == 1
    assert score_events[0].payload["outcome"] == "correct"
    assert score_events[0].payload["scorer"] == "mock"
    assert score_events[0].payload["source_response_event_id"] is not None


def test_brainlab_enforces_trial_event_order():
    lab = BrainLab()
    student = Student.create(name="Test")
    session = lab.start_session(student)
    unit = LearningUnit.create(canonical="target", allowed_trial_types=["recall"])

    # Cannot score before response
    trial = lab.start_trial(session, unit, "recall", "retrieval", stimulus="target")
    with pytest.raises(ValueError):
        lab.score_trial(session, trial, Score(outcome="correct"))


def test_brainlab_enforces_session_start_before_trial():
    lab = BrainLab()
    session = LearningSession.create(student_id=uuid4(), protocol_id="pilot-a", protocol_version="1.0")
    unit = LearningUnit.create(canonical="target", allowed_trial_types=["recall"])
    with pytest.raises(ValueError):
        lab.start_trial(session, unit, "recall", "retrieval", stimulus="target")


def test_brainlab_enforces_trial_order_after_response():
    lab = BrainLab()
    student = Student.create(name="Test")
    session = lab.start_session(student)
    unit = LearningUnit.create(canonical="target", allowed_trial_types=["recall"])
    trial = lab.start_trial(session, unit, "recall", "retrieval", stimulus="target")
    response = Response(raw="x", normalized="x")
    lab.submit_response(session, trial, response, monotonic_response_ns=1000)

    # Cannot start the same trial again
    with pytest.raises(ValueError):
        lab._emit_trial_start(session, trial)


def test_brainlab_uses_experiment_engine():
    runner = MinimalProtocolRunner()
    runner.register(ProtocolSpec(protocol_id="custom", protocol_version="2.0", condition="AC"))
    lab = BrainLab(experiment_engine=runner)
    student = Student.create(name="Test")
    session = lab.start_session(student, protocol_id="custom")
    assert session.protocol_id == "custom"
    assert session.protocol_version == "2.0"
    assert session.condition == "AC"


def test_brainlab_recommend_uses_scheduler():
    lab = BrainLab()
    student = Student.create(name="Test")
    unit = LearningUnit.create(canonical="target", allowed_trial_types=["recall"])
    rec = lab.recommend(student, [unit])
    assert isinstance(rec, Recommendation)
    assert rec.scheduler_id == "m0"
