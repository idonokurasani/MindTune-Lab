"""Deterministic utterance planning for CLM-03."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from mindtune_clm.audio.assets import AudioRole
from mindtune_clm.audio.transforms import ms_to_frames
from mindtune_clm.state import MantraControlState


@dataclass(frozen=True)
class UtteranceSegment:
    """One deterministic segment inside an utterance plan."""

    segment_id: str
    asset_id: str | None
    segment_role: str
    sequence_index: int
    source_start_frame: int
    source_end_frame: int
    target_tempo_ratio: float
    target_gain: float
    target_prosodic_emphasis: float
    pre_silence_duration_ms: int
    post_silence_duration_ms: int
    repetition_index: int
    control_state_id: str
    source_decision_id: str
    source_actuation_receipt_id: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "segment_id": self.segment_id,
            "asset_id": self.asset_id,
            "segment_role": self.segment_role,
            "sequence_index": self.sequence_index,
            "source_start_frame": self.source_start_frame,
            "source_end_frame": self.source_end_frame,
            "target_tempo_ratio": self.target_tempo_ratio,
            "target_gain": self.target_gain,
            "target_prosodic_emphasis": self.target_prosodic_emphasis,
            "pre_silence_duration_ms": self.pre_silence_duration_ms,
            "post_silence_duration_ms": self.post_silence_duration_ms,
            "repetition_index": self.repetition_index,
            "control_state_id": self.control_state_id,
            "source_decision_id": self.source_decision_id,
            "source_actuation_receipt_id": self.source_actuation_receipt_id,
        }


@dataclass(frozen=True)
class UtterancePlan:
    """A deterministic plan describing how a control state becomes audio."""

    plan_id: str
    render_cycle_id: str
    ordered_segments: list[UtteranceSegment]
    canonical_audio_config: dict[str, Any]
    source_control_state: dict[str, Any]
    source_decision_id: str
    source_actuation_receipt_id: str
    safe_application_boundary: str
    expected_duration: float
    planner_id: str
    planner_version: str
    plan_digest: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "render_cycle_id": self.render_cycle_id,
            "ordered_segments": [s.as_dict() for s in self.ordered_segments],
            "canonical_audio_config": self.canonical_audio_config,
            "source_control_state": self.source_control_state,
            "source_decision_id": self.source_decision_id,
            "source_actuation_receipt_id": self.source_actuation_receipt_id,
            "safe_application_boundary": self.safe_application_boundary,
            "expected_duration": self.expected_duration,
            "planner_id": self.planner_id,
            "planner_version": self.planner_version,
            "plan_digest": self.plan_digest,
        }


def _canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def _plan_digest(plan_dict: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(plan_dict).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class UtterancePlanner:
    """Deterministic planner mapping ``MantraControlState`` to ``UtterancePlan``."""

    planner_id: str = "mindtune_clm.audio.planner.v1"
    version: str = "1.0.0"
    speech_asset_id: str = "speech_segment"
    breathing_asset_id: str = "breathing_cue"
    sample_rate: int = 16000
    sample_width: int = 2
    channels: int = 1

    def plan(
        self,
        control_state: MantraControlState,
        actuation_receipt_id: str,
        decision_id: str,
        render_cycle_id: str,
    ) -> UtterancePlan:
        """Create a deterministic utterance plan from the applied control state."""
        segments: list[UtteranceSegment] = []
        seq = 0
        reps = max(1, control_state.repetition_count)

        for r in range(reps):
            pre = control_state.pre_stimulus_pause_ms if r == 0 else 0
            post = control_state.post_stimulus_pause_ms if r == reps - 1 else 0
            gain = 1.0 + 0.5 * control_state.vocal_energy
            segment = UtteranceSegment(
                segment_id=f"seg-{render_cycle_id}-{r}",
                asset_id=self.speech_asset_id,
                segment_role=AudioRole.SPEECH_SEGMENT.value,
                sequence_index=seq,
                source_start_frame=0,
                source_end_frame=-1,
                target_tempo_ratio=control_state.tempo_ratio,
                target_gain=gain,
                target_prosodic_emphasis=control_state.prosodic_emphasis,
                pre_silence_duration_ms=pre,
                post_silence_duration_ms=post,
                repetition_index=r,
                control_state_id=control_state.control_state_id,
                source_decision_id=decision_id,
                source_actuation_receipt_id=actuation_receipt_id,
            )
            segments.append(segment)
            seq += 1

        if control_state.breathing_cue:
            segments.append(
                UtteranceSegment(
                    segment_id=f"seg-{render_cycle_id}-breath",
                    asset_id=self.breathing_asset_id,
                    segment_role=AudioRole.BREATHING_CUE.value,
                    sequence_index=seq,
                    source_start_frame=0,
                    source_end_frame=-1,
                    target_tempo_ratio=1.0,
                    target_gain=1.0,
                    target_prosodic_emphasis=0.0,
                    pre_silence_duration_ms=0,
                    post_silence_duration_ms=0,
                    repetition_index=0,
                    control_state_id=control_state.control_state_id,
                    source_decision_id=decision_id,
                    source_actuation_receipt_id=actuation_receipt_id,
                )
            )
            seq += 1

        config = {
            "sample_rate": self.sample_rate,
            "sample_width": self.sample_width,
            "channels": self.channels,
        }

        # Expected duration estimate: speech frames per rep adjusted by tempo.
        speech_asset_frames = self._speech_frame_estimate()
        speech_frames = int(speech_asset_frames / control_state.tempo_ratio) * reps
        silence_frames = ms_to_frames(
            control_state.pre_stimulus_pause_ms + control_state.post_stimulus_pause_ms,
            self.sample_rate,
        )
        breath_frames = self._breath_frame_estimate() if control_state.breathing_cue else 0
        expected_duration = (speech_frames + silence_frames + breath_frames) / self.sample_rate

        plan_id = f"plan-{render_cycle_id}-{control_state.control_state_id}"
        plan_dict = {
            "plan_id": plan_id,
            "render_cycle_id": render_cycle_id,
            "ordered_segments": [s.as_dict() for s in segments],
            "canonical_audio_config": config,
            "source_control_state": control_state.as_dict(),
            "source_decision_id": decision_id,
            "source_actuation_receipt_id": actuation_receipt_id,
            "safe_application_boundary": "between_mantra_cycles",
            "expected_duration": expected_duration,
            "planner_id": self.planner_id,
            "planner_version": self.version,
        }
        digest = _plan_digest(plan_dict)

        return UtterancePlan(
            plan_id=plan_id,
            render_cycle_id=render_cycle_id,
            ordered_segments=segments,
            canonical_audio_config=config,
            source_control_state=control_state.as_dict(),
            source_decision_id=decision_id,
            source_actuation_receipt_id=actuation_receipt_id,
            safe_application_boundary="between_mantra_cycles",
            expected_duration=expected_duration,
            planner_id=self.planner_id,
            planner_version=self.version,
            plan_digest=digest,
        )

    def _speech_frame_estimate(self) -> int:
        # 0.5s default speech fixture at 16kHz
        return 8000

    def _breath_frame_estimate(self) -> int:
        # 0.3s default breath fixture at 16kHz
        return 4800
