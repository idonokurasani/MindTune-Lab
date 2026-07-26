"""Deterministic sensor replay runner for CLM-02."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from mindtune_clm.loop import ControlLoop, ControlLoopResult
from mindtune_clm.policy import ControlPolicy
from mindtune_clm.replay.adapter import to_observation_frame
from mindtune_clm.replay.clock import ReplayClock
from mindtune_clm.replay.manifest import make_manifest
from mindtune_clm.replay.models import (
    NormalizedSensorSample,
    QualityAssessment,
    ReplayDigest,
    ReplayResult,
)
from mindtune_clm.replay.normalization import NormalizationPolicy
from mindtune_clm.replay.parser import SensorSourceParser
from mindtune_clm.replay.quality import QualityPolicy
from mindtune_clm.replay.source import RecordedSensorSource
from mindtune_clm.replay.windows import WindowPolicy, make_windows
from mpe.enums import DataClassification
from mpe.event_store import InMemoryEventStore
from mpe.types import ProgramVersionID, ProtocolVersionID, SessionID


def _canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _cycle_to_dict(cycle: Any) -> dict[str, Any]:
    """Serialize a ControlCycleResult into a deterministic dict for the digest."""
    return {
        "control_cycle_id": cycle.control_cycle_id,
        "render_cycle_id": cycle.render_cycle_id,
        "cognitive_state": cycle.estimate.cognitive_state.value,
        "cognitive_load": round(cycle.estimate.cognitive_load, 5),
        "decision_kind": cycle.decision.decision_kind.value,
        "previous_control_state": cycle.decision.previous_control_state.as_dict(),
        "proposed_control_state": cycle.decision.proposed_control_state.as_dict(),
        "applied_state": cycle.receipt.applied_state.as_dict(),
        "rendered_control_state": cycle.rendered_control_state.as_dict(),
    }


def canonical_replay_dict(result: ReplayResult) -> dict[str, Any]:
    """Return a stable, deterministic representation of a replay result."""
    manifest = result.replay_manifest
    return {
        "source_checksum": result.source_checksum,
        "manifest": {
            "replay_id": manifest.replay_id,
            "source_id": manifest.source_id,
            "source_checksum": manifest.source_checksum,
            "parser_id": manifest.parser_id,
            "parser_version": manifest.parser_version,
            "normalization_policy_id": manifest.normalization_policy_id,
            "normalization_policy_version": manifest.normalization_policy_version,
            "quality_policy_id": manifest.quality_policy_id,
            "quality_policy_version": manifest.quality_policy_version,
            "window_policy_id": manifest.window_policy_id,
            "window_policy_version": manifest.window_policy_version,
            "clm_policy_id": manifest.clm_policy_id,
            "clm_policy_version": manifest.clm_policy_version,
            "deterministic_seed": manifest.deterministic_seed,
            "replay_clock_config": manifest.replay_clock_config,
            "requested_time_interval": manifest.requested_time_interval,
            "creation_timestamp": manifest.creation_timestamp,
            "metadata": dict(manifest.metadata),
        },
        "normalized_samples": [
            {
                "normalized_sample_id": s.normalized_sample_id,
                "source_sample_index": s.source_sample_index,
                "source_timestamp": s.source_timestamp,
                "replay_relative_timestamp": s.replay_relative_timestamp,
                "channel_values": dict(sorted(s.channel_values.items())),
                "missing_channel_indicators": dict(sorted(s.missing_channel_indicators.items())),
                "normalization_operations": s.normalization_operations,
                "source_provenance": s.source_provenance,
            }
            for s in result.normalized_samples
        ],
        "quality_assessments": [
            {
                "assessment_id": a.assessment_id,
                "accepted": a.accepted,
                "sample_id": a.sample_id,
                "window_id": a.window_id,
                "quality_score": a.quality_score,
                "reason_codes": a.reason_codes,
                "detected_artifacts": a.detected_artifacts,
                "missingness": a.missingness,
                "policy_version": a.policy_version,
                "source_ids": a.source_ids,
            }
            for a in result.quality_assessments
        ],
        "windows": [
            {
                "window_id": w.window_id,
                "start_replay_timestamp": w.start_replay_timestamp,
                "end_replay_timestamp": w.end_replay_timestamp,
                "accepted_sample_count": w.accepted_sample_count,
                "rejected_sample_count": w.rejected_sample_count,
                "channel_coverage": w.channel_coverage,
                "aggregate_quality": w.aggregate_quality,
                "deterministic_feature_values": w.deterministic_feature_values,
                "accepted": w.accepted,
                "reason_codes": w.reason_codes,
            }
            for w in result.windows
        ],
        "observation_frames": [
            {
                "observation_frame_id": f.observation_frame_id,
                "control_cycle_id": f.control_cycle_id,
                "session_id": f.session_id,
                "sequence_number": f.sequence_number,
                "observation_timestamp": f.observation_timestamp,
                "eeg_stability": f.eeg_stability,
                "eeg_quality": f.eeg_quality,
                "available_modalities": f.available_modalities,
                "source_event_ids": f.source_event_ids,
            }
            for f in result.observation_frames
        ],
        "clm_cycles": [_cycle_to_dict(c) for c in result.clm_session_result.cycles],
        "final_control_state": result.clm_session_result.final_control_state.as_dict(),
        "warnings": result.warnings,
        "rejected_data_summary": result.rejected_data_summary,
    }


def compute_replay_digest(result: ReplayResult) -> ReplayDigest:
    """Compute a canonical deterministic digest of a replay result."""
    canonical = _canonical_json(canonical_replay_dict(result))
    return ReplayDigest(
        digest_hex=_sha256_hex(canonical.encode("utf-8")),
        canonical_json=canonical,
    )


EVENT_NAMESPACES: dict[str, dict[str, str]] = {
    "clm02": {
        "source_registered": "sensor_source_registered",
        "manifest_created": "replay_manifest_created",
        "samples_parsed": "sensor_sample_parsed",
        "samples_normalized": "sensor_sample_normalized",
        "quality_assessed": "sensor_quality_assessed",
        "window_created": "replay_window_created",
        "window_rejected": "replay_window_rejected",
        "observation_frame_generated": "observation_frame_generated_from_replay",
        "replay_completed": "sensor_replay_completed",
        "replay_failed": "sensor_replay_failed",
        "digest_computed": "replay_digest_computed",
    },
    "fc11": {
        "source_registered": "fc11_source_registered",
        "manifest_created": "fc11_metadata_parsed",
        "samples_parsed": "fc11_record_parsed",
        "samples_normalized": "fc11_sample_normalized",
        "quality_assessed": "fc11_quality_assessed",
        "window_created": "fc11_window_created",
        "window_rejected": "fc11_window_rejected",
        "observation_frame_generated": "fc11_observation_frame_generated",
        "replay_completed": "fc11_sensor_replay_completed",
        "replay_failed": "fc11_sensor_replay_failed",
        "digest_computed": "fc11_replay_digest_computed",
    },
}


@dataclass
class ReplayRunner:
    """Replay a recorded sensor source through the CLM-01 closed-loop kernel."""

    fixture_root: Path | None = None
    event_namespace: str = "clm02"
    program_version_id: ProgramVersionID = field(default_factory=lambda: ProgramVersionID("clm-02-program-v1.0.0"))
    protocol_version_id: ProtocolVersionID = field(default_factory=lambda: ProtocolVersionID("clm-02-protocol-v1.0.0"))
    learner_id: str = "learner_clm02_replay"

    def _event(self, key: str) -> str:
        if self.event_namespace not in EVENT_NAMESPACES:
            return self.event_namespace + "_" + key
        return EVENT_NAMESPACES[self.event_namespace][key]

    def run(  # noqa: C901
        self,
        replay_id: str,
        source: RecordedSensorSource,
        content: str,
        parser: SensorSourceParser,
        normalization_policy: NormalizationPolicy,
        quality_policy: QualityPolicy,
        window_policy: WindowPolicy,
        clm_policy: Any,
        deterministic_seed: str = "clm02_seed_0",
        requested_time_interval: tuple[float, float] | None = None,
        clock_scale: float = 1.0,
    ) -> ReplayResult:
        """Execute the full replay pipeline deterministically."""
        if source.source_format.startswith("fc11"):
            self.event_namespace = "fc11"
        if clm_policy is None:
            clm_policy = ControlPolicy()
        sample_interval = 1.0 / max(1.0, source.source_sampling_rate_hz)
        clock = ReplayClock(
            source_start_timestamp=source.source_start_timestamp,
            sample_interval=sample_interval,
            scale=clock_scale,
        )

        # ``clock_scale`` is not part of the manifest because it is an external
        # execution-speed knob and must not change the canonical replay digest.
        clock_config = {
            "source_start_timestamp": source.source_start_timestamp,
            "sample_interval": sample_interval,
        }

        manifest = make_manifest(
            replay_id=replay_id,
            source=source,
            parser_id=parser.parser_id,
            parser_version=parser.version,
            normalization_policy_id=normalization_policy.policy_id,
            normalization_policy_version=normalization_policy.version,
            quality_policy_id=quality_policy.policy_id,
            quality_policy_version=quality_policy.version,
            window_policy_id=window_policy.policy_id,
            window_policy_version=window_policy.version,
            clm_policy_id="mindtune_clm.clm01.progressive",
            clm_policy_version="1.0.0",
            replay_clock_config=clock_config,
            deterministic_seed=deterministic_seed,
            requested_time_interval=requested_time_interval,
            creation_timestamp=clock.now(),
        )

        store = InMemoryEventStore()
        loop = ControlLoop(
            store=store,
            clock=clock,
            policy=clm_policy,
            session_id=SessionID(f"replay-{replay_id}"),
        )
        loop.runtime.create_session(
            program_version_id=self.program_version_id,
            protocol_version_id=self.protocol_version_id,
            learner_id=self.learner_id,
            session_id=loop.session_id,
        )
        loop.runtime.start_session(
            random_seed=deterministic_seed,
            start_parameters={"replay_id": replay_id, "source_id": source.source_id},
        )

        last_event = loop.runtime.state.events[-1]
        loop.runtime.emit(
            self._event("source_registered"),
            {
                "source_id": source.source_id,
                "source_format": source.source_format,
                "fixture_handle": source.fixture_handle,
                "content_checksum": source.content_checksum,
                "sensor_type": source.sensor_type,
                "source_sampling_rate_hz": source.source_sampling_rate_hz,
                "channel_names": source.channel_names,
            },
            component="clm02_replay",
            component_version="1.0.0",
            provenance=[last_event.event_id],
            data_classification=DataClassification.INTERNAL,
        )
        last_event = loop.runtime.state.events[-1]
        loop.runtime.emit(
            self._event("manifest_created"),
            {
                "replay_id": manifest.replay_id,
                "manifest_checksum": manifest.manifest_checksum,
                "parser_id": manifest.parser_id,
                "parser_version": manifest.parser_version,
                "normalization_policy_id": manifest.normalization_policy_id,
                "quality_policy_id": manifest.quality_policy_id,
                "window_policy_id": manifest.window_policy_id,
                "clm_policy_id": manifest.clm_policy_id,
                "deterministic_seed": manifest.deterministic_seed,
            },
            component="clm02_replay",
            component_version="1.0.0",
            provenance=[last_event.event_id],
            data_classification=DataClassification.INTERNAL,
        )

        raw_samples = parser.parse(source, content)
        last_event = loop.runtime.state.events[-1]
        loop.runtime.emit(
            self._event("samples_parsed"),
            {
                "source_id": source.source_id,
                "sample_count": len(raw_samples),
            },
            component="clm02_replay",
            component_version="1.0.0",
            provenance=[last_event.event_id],
            data_classification=DataClassification.INTERNAL,
        )

        if not raw_samples:
            fail_event = loop.runtime.emit(
                self._event("replay_failed"),
                {
                    "replay_id": replay_id,
                    "reason": "no_samples_parsed",
                    "source_id": source.source_id,
                },
                component="clm02_replay",
                component_version="1.0.0",
                provenance=[last_event.event_id],
                data_classification=DataClassification.INTERNAL,
            )
            events = store.read(loop.session_id)
            clm_result = ControlLoopResult(
                session_id=loop.session_id,
                events=events,
                cycles=[],
                final_control_state=loop.actuator.current_state,
            )
            empty_result = ReplayResult(
                replay_manifest=manifest,
                source_checksum=source.content_checksum,
                normalized_samples=[],
                quality_assessments=[],
                windows=[],
                observation_frames=[],
                clm_session_result=clm_result,
                canonical_replay_digest=ReplayDigest(digest_hex="", canonical_json=""),
                warnings=["no_samples_parsed"],
                rejected_data_summary={},
            )
            digest = compute_replay_digest(empty_result)
            empty_result.canonical_replay_digest = digest
            loop.runtime.emit(
                self._event("digest_computed"),
                {
                    "replay_id": replay_id,
                    "digest_hex": digest.digest_hex,
                    "canonical_json_length": len(digest.canonical_json),
                },
                component="clm02_replay",
                component_version="1.0.0",
                provenance=[fail_event.event_id],
                data_classification=DataClassification.INTERNAL,
            )
            return empty_result

        normalized = normalization_policy.normalize(raw_samples, source)
        last_event = loop.runtime.state.events[-1]
        loop.runtime.emit(
            self._event("samples_normalized"),
            {
                "source_id": source.source_id,
                "normalized_sample_count": len(normalized),
            },
            component="clm02_replay",
            component_version="1.0.0",
            provenance=[last_event.event_id],
            data_classification=DataClassification.INTERNAL,
        )

        sample_assessments: list[QualityAssessment] = []
        previous: NormalizedSensorSample | None = None
        for s in normalized:
            assessment = quality_policy.assess(s, previous)
            sample_assessments.append(assessment)
            previous = s
        accepted_count = sum(1 for a in sample_assessments if a.accepted)
        last_event = loop.runtime.state.events[-1]
        loop.runtime.emit(
            self._event("quality_assessed"),
            {
                "source_id": source.source_id,
                "sample_count": len(sample_assessments),
                "accepted_sample_count": accepted_count,
                "rejected_sample_count": len(sample_assessments) - accepted_count,
            },
            component="clm02_replay",
            component_version="1.0.0",
            provenance=[last_event.event_id],
            data_classification=DataClassification.INTERNAL,
        )

        windows = make_windows(replay_id, normalized, sample_assessments, window_policy, quality_policy)
        sample_by_id = {s.normalized_sample_id: s for s in normalized}

        for window in windows:
            last_event = loop.runtime.state.events[-1]
            event_type = (
                self._event("window_created")
                if window.accepted
                else self._event("window_rejected")
            )
            loop.runtime.emit(
                event_type,
                {
                    "window_id": window.window_id,
                    "start_replay_timestamp": window.start_replay_timestamp,
                    "end_replay_timestamp": window.end_replay_timestamp,
                    "accepted_sample_count": window.accepted_sample_count,
                    "rejected_sample_count": window.rejected_sample_count,
                    "accepted": window.accepted,
                    "reason_codes": window.reason_codes,
                },
                component="clm02_replay",
                component_version="1.0.0",
                provenance=[last_event.event_id],
                data_classification=DataClassification.INTERNAL,
            )

        observation_frames: list[Any] = []
        for idx, window in enumerate(windows, start=1):
            if not window.accepted:
                continue
            if source.source_format.startswith("fc11"):
                frame = to_observation_frame(
                    window,
                    sample_by_id,
                    replay_id=replay_id,
                    sequence_number=idx,
                    eeg_channel="eeg_scaled",
                    eeg_stability_feature="signal_stability",
                )
            else:
                frame = to_observation_frame(
                    window,
                    sample_by_id,
                    replay_id=replay_id,
                    sequence_number=idx,
                )
            observation_frames.append(frame)

        last_event = loop.runtime.state.events[-1]
        loop.runtime.emit(
            self._event("replay_completed"),
            {
                "replay_id": replay_id,
                "window_count": len(windows),
                "observation_frame_count": len(observation_frames),
            },
            component="clm02_replay",
            component_version="1.0.0",
            provenance=[last_event.event_id],
            data_classification=DataClassification.INTERNAL,
        )

        cycles: list[Any] = []
        if observation_frames:
            last_event = loop.runtime.state.events[-1]
            loop._render_stimulus(
                loop.actuator.current_state,
                None,
                [last_event.event_id],
                render_cycle_id="rc-1",
            )
            for cycle_index, frame in enumerate(observation_frames, start=1):
                last_event = loop.runtime.state.events[-1]
                loop.runtime.emit(
                    self._event("observation_frame_generated"),
                    {
                        "observation_frame_id": frame.observation_frame_id,
                        "control_cycle_id": frame.control_cycle_id,
                        "window_id": frame.control_cycle_id[3:],  # strip cc-
                        "eeg_stability": frame.eeg_stability,
                        "eeg_quality": frame.eeg_quality,
                        "available_modalities": frame.available_modalities,
                    },
                    component="clm02_replay",
                    component_version="1.0.0",
                    provenance=[last_event.event_id],
                    data_classification=DataClassification.INTERNAL,
                )
                cycle = loop._run_cycle(frame, cycle_index)
                cycles.append(cycle)

        events = store.read(loop.session_id)
        clm_result = ControlLoopResult(
            session_id=loop.session_id,
            events=events,
            cycles=cycles,
            final_control_state=loop.actuator.current_state,
        )

        warnings: list[str] = []
        for s in normalized:
            for op in s.normalization_operations:
                if any(token in op for token in ["rejected", "failed", "malformed", "regression", "missing_required"]):
                    warnings.append(f"{s.normalized_sample_id}:{op}")

        rejected_summary: dict[str, int] = {}
        for w in windows:
            if not w.accepted:
                rejected_summary[w.window_id] = w.rejected_sample_count

        result = ReplayResult(
            replay_manifest=manifest,
            source_checksum=source.content_checksum,
            normalized_samples=normalized,
            quality_assessments=sample_assessments,
            windows=windows,
            observation_frames=observation_frames,
            clm_session_result=clm_result,
            canonical_replay_digest=ReplayDigest(digest_hex="", canonical_json=""),
            warnings=warnings,
            rejected_data_summary=rejected_summary,
        )

        digest = compute_replay_digest(result)
        result.canonical_replay_digest = digest

        last_event = loop.runtime.state.events[-1]
        loop.runtime.emit(
            self._event("digest_computed"),
            {
                "replay_id": replay_id,
                "digest_hex": digest.digest_hex,
                "canonical_json_length": len(digest.canonical_json),
            },
            component="clm02_replay",
            component_version="1.0.0",
            provenance=[last_event.event_id],
            data_classification=DataClassification.INTERNAL,
        )

        return result
