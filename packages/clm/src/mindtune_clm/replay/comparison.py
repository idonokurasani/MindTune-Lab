"""Offline policy comparison over the same replay windows for CLM-02."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from mindtune_clm.loop import ControlLoop
from mindtune_clm.policy import ControlPolicy
from mindtune_clm.replay.adapter import to_observation_frame
from mindtune_clm.replay.clock import ReplayClock
from mindtune_clm.replay.models import NormalizedSensorSample, QualityAssessment, ReplayWindow
from mpe.event_store import InMemoryEventStore


def _canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _trajectory_digest(states: list[str], decisions: list[str], params: list[dict[str, Any]]) -> str:
    payload = {
        "state_sequence": states,
        "decision_sequence": decisions,
        "parameter_trajectory": params,
    }
    return _sha256_hex(_canonical_json(payload).encode("utf-8"))


@dataclass(frozen=True)
class PolicyTrajectory:
    """Deterministic trajectory of one CLM policy over the same replay windows."""

    policy_id: str
    replay_digest: str
    state_sequence: list[str]
    decision_sequence: list[str]
    intervention_count: int
    abstention_count: int
    withdrawal_count: int
    max_assistance: float
    time_above_baseline_assistance: float
    parameter_trajectory: list[dict[str, Any]]
    rejected_window_count: int


@dataclass(frozen=True)
class PolicyComparisonResult:
    """Comparison of two or more policies on the same replay data."""

    policy_trajectories: list[PolicyTrajectory]
    first_divergence_index: int | None
    divergence_field: str | None


def _state_at_assistance_level_zero(state: dict[str, Any]) -> bool:
    return float(state.get("assistance_level", 0.0)) == 0.0


def _run_policy_on_frames(
    policy: ControlPolicy,
    frames: list[Any],
    source_start_timestamp: float,
    sample_interval: float,
) -> tuple[list[Any], dict[str, Any]]:
    """Run one CLM policy on a pre-built list of ObservationFrames."""
    clock = ReplayClock(
        source_start_timestamp=source_start_timestamp,
        sample_interval=sample_interval,
        scale=1.0,
    )
    store = InMemoryEventStore()
    loop = ControlLoop(store=store, clock=clock, policy=policy)
    loop.runtime.create_session(
        program_version_id="clm-02-compare-v1.0.0",
        protocol_version_id="clm-02-protocol-v1.0.0",
        learner_id="learner_clm02_compare",
        session_id=loop.session_id,
    )
    loop.runtime.start_session(
        random_seed="clm02_compare_seed_0",
        start_parameters={"policy_id": "compared"},
    )
    cycles: list[Any] = []
    if frames:
        last_event = loop.runtime.state.events[-1]
        loop._render_stimulus(
            loop.actuator.current_state,
            None,
            [last_event.event_id],
            render_cycle_id="rc-1",
        )
        for cycle_index, frame in enumerate(frames, start=1):
            cycles.append(loop._run_cycle(frame, cycle_index))
    return cycles, {"store": store, "session_id": loop.session_id}


def _build_frames(
    windows: list[ReplayWindow],
    samples: dict[str, NormalizedSensorSample],
    replay_id: str,
) -> list[Any]:
    frames = []
    for idx, window in enumerate(windows, start=1):
        if not window.accepted:
            continue
        frame = to_observation_frame(window, samples, replay_id=replay_id, sequence_number=idx)
        frames.append(frame)
    return frames


def compare_policies(  # noqa: C901
    replay_id: str,
    windows: list[ReplayWindow],
    samples: list[NormalizedSensorSample],
    sample_assessments: list[QualityAssessment],
    policies: list[ControlPolicy],
    source_start_timestamp: float = 0.0,
    sample_interval: float = 0.1,
) -> PolicyComparisonResult:
    """Apply multiple CLM policies to the same replay windows and report divergences."""
    sample_by_id = {s.normalized_sample_id: s for s in samples}
    frames = _build_frames(windows, sample_by_id, replay_id)
    rejected_window_count = sum(1 for w in windows if not w.accepted)

    trajectories: list[PolicyTrajectory] = []
    for policy in policies:
        cycles, _ = _run_policy_on_frames(policy, frames, source_start_timestamp, sample_interval)
        states = [c.estimate.cognitive_state.value for c in cycles]
        decisions = [c.decision.decision_kind.value for c in cycles]
        params = [c.receipt.applied_state.as_dict() for c in cycles]
        assistance_values = [p["assistance_level"] for p in params]
        max_assistance = max(assistance_values) if assistance_values else 0.0
        time_above = sum(1.0 for a in assistance_values if a > 1e-9) * sample_interval
        digest = _trajectory_digest(states, decisions, params)
        traj = PolicyTrajectory(
            policy_id=getattr(policy, "policy_id", "unknown"),
            replay_digest=digest,
            state_sequence=states,
            decision_sequence=decisions,
            intervention_count=decisions.count("apply"),
            abstention_count=decisions.count("abstain"),
            withdrawal_count=decisions.count("withdraw"),
            max_assistance=max_assistance,
            time_above_baseline_assistance=time_above,
            parameter_trajectory=params,
            rejected_window_count=rejected_window_count,
        )
        trajectories.append(traj)

    first_divergence: int | None = None
    divergence_field: str | None = None
    if len(trajectories) >= 2:
        t0 = trajectories[0]
        for t in trajectories[1:]:
            for i, (d0, d1) in enumerate(zip(t0.decision_sequence, t.decision_sequence, strict=False)):
                if d0 != d1:
                    first_divergence = i
                    divergence_field = "decision_kind"
                    break
            if first_divergence is not None:
                break
            if len(t0.parameter_trajectory) != len(t.parameter_trajectory):
                first_divergence = min(len(t0.parameter_trajectory), len(t.parameter_trajectory))
                divergence_field = "parameter_trajectory_length"
            else:
                for i, (p0, p1) in enumerate(zip(t0.parameter_trajectory, t.parameter_trajectory, strict=True)):
                    for key in set(p0) | set(p1):
                        if p0.get(key) != p1.get(key):
                            first_divergence = i
                            divergence_field = f"parameter.{key}"
                            break
                    if first_divergence is not None:
                        break

    return PolicyComparisonResult(
        policy_trajectories=trajectories,
        first_divergence_index=first_divergence,
        divergence_field=divergence_field,
    )
