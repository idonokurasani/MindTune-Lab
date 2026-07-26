"""Offline deterministic audio rendering for CLM-03."""

from __future__ import annotations

import hashlib
import wave
from dataclasses import dataclass, field
from io import BytesIO
from typing import Any

from mindtune_clm.audio.assets import AudioAssetRegistry
from mindtune_clm.audio.events import CLM03EventType
from mindtune_clm.audio.plan import UtterancePlanner
from mindtune_clm.audio.transforms import (
    compute_peak,
    compute_rms,
    gain_and_emphasis,
    silence_transform,
    tempo_transform,
)
from mindtune_clm.state import MantraControlState


class AudioRenderError(Exception):
    """Raised when the deterministic renderer cannot produce a valid artifact."""

    def __init__(self, reason: str, fallback_triggered: bool = True) -> None:
        super().__init__(reason)
        self.reason = reason
        self.fallback_triggered = fallback_triggered


@dataclass(frozen=True)
class RenderedAudioArtifact:
    """A deterministic, validated audio artifact ready for playback scheduling."""

    artifact_id: str
    plan_id: str
    render_cycle_id: str
    audio_checksum: str
    canonical_bytes: bytes
    frame_count: int
    duration: float
    sample_rate: int
    channels: int
    sample_width: int
    peak_amplitude: float
    rms_amplitude: float
    clipping_count: int
    applied_control_state_id: str
    source_actuation_receipt_id: str
    renderer_id: str
    renderer_version: str
    render_digest: str
    fallback_used: bool = False
    fallback_reason: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "plan_id": self.plan_id,
            "render_cycle_id": self.render_cycle_id,
            "audio_checksum": self.audio_checksum,
            "frame_count": self.frame_count,
            "duration": self.duration,
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "sample_width": self.sample_width,
            "peak_amplitude": round(self.peak_amplitude, 6),
            "rms_amplitude": round(self.rms_amplitude, 6),
            "clipping_count": self.clipping_count,
            "applied_control_state_id": self.applied_control_state_id,
            "source_actuation_receipt_id": self.source_actuation_receipt_id,
            "renderer_id": self.renderer_id,
            "renderer_version": self.renderer_version,
            "render_digest": self.render_digest,
            "fallback_used": self.fallback_used,
            "fallback_reason": self.fallback_reason,
        }


def _build_wav(pcm: bytes, sample_rate: int, channels: int = 1, sample_width: int = 2) -> bytes:
    """Wrap raw 16-bit little-endian PCM in a canonical WAV container."""
    with BytesIO() as bio:
        with wave.open(bio, "wb") as w:
            w.setnchannels(channels)
            w.setsampwidth(sample_width)
            w.setframerate(sample_rate)
            w.writeframes(pcm)
        return bio.getvalue()


def _validate_artifact(canonical_bytes: bytes) -> None:
    """Validate a WAV container against canonical CLM-03 requirements."""
    with BytesIO(canonical_bytes) as bio:
        with wave.open(bio, "rb") as w:
            if w.getnchannels() != 1:
                raise AudioRenderError("invalid channel count")
            if w.getsampwidth() != 2:
                raise AudioRenderError("invalid sample width")
            if w.getframerate() not in (16000, 24000):
                raise AudioRenderError("non-canonical sample rate")
            if w.getnframes() == 0:
                raise AudioRenderError("empty audio artifact")


def _canonical_json(obj: Any) -> str:
    import json

    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def _render_digest(artifact_dict: dict[str, Any], canonical_bytes: bytes) -> str:
    payload = _canonical_json(artifact_dict) + hashlib.sha256(canonical_bytes).hexdigest()
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass
class AudioRenderer:
    """Deterministic offline renderer: control state → validated WAV artifact."""

    asset_registry: AudioAssetRegistry
    planner: UtterancePlanner = field(default_factory=UtterancePlanner)
    renderer_id: str = "mindtune_clm.audio.renderer.v1"
    version: str = "1.0.0"
    last_valid_artifact: RenderedAudioArtifact | None = None
    fallback_asset_id: str = "speech_segment"

    def render(  # noqa: C901
        self,
        control_state: MantraControlState,
        actuation_receipt_id: str,
        decision_id: str,
        render_cycle_id: str,
        runtime: Any | None = None,
    ) -> RenderedAudioArtifact:
        """Render the applied control state into a canonical WAV artifact."""
        start_event_id: str | None = None
        if runtime is not None:
            start_event_id = runtime.emit(
                CLM03EventType.AUDIO_RENDER_STARTED,
                {
                    "render_cycle_id": render_cycle_id,
                    "control_state_id": control_state.control_state_id,
                    "actuation_receipt_id": actuation_receipt_id,
                    "decision_id": decision_id,
                },
                component="clm03_audio",
                component_version=self.version,
            ).event_id

        plan = self.planner.plan(
            control_state,
            actuation_receipt_id,
            decision_id,
            render_cycle_id,
        )
        if runtime is not None:
            runtime.emit(
                CLM03EventType.UTTERANCE_PLAN_CREATED,
                plan.as_dict(),
                component="clm03_audio",
                component_version=self.version,
                provenance=[start_event_id] if start_event_id else [],
            )

        pcm_parts: list[bytes] = []
        fallback_used = False
        fallback_reason: str | None = None

        for segment in plan.ordered_segments:
            asset = None
            if segment.asset_id is not None:
                asset = self.asset_registry.get(segment.asset_id)
            if asset is None and segment.asset_id is not None:
                fallback_used = True
                fallback_reason = f"missing_asset:{segment.asset_id}"
                asset = self.asset_registry.get(self.fallback_asset_id)

            if asset is None and self.last_valid_artifact is not None:
                fallback_used = True
                fallback_reason = f"{fallback_reason};last_valid_fallback"
                segment_pcm = self.last_valid_artifact.canonical_bytes[44:]  # strip WAV header
                pcm_parts.append(silence_transform(segment.pre_silence_duration_ms, plan.canonical_audio_config["sample_rate"]))
                pcm_parts.append(segment_pcm)
                pcm_parts.append(silence_transform(segment.post_silence_duration_ms, plan.canonical_audio_config["sample_rate"]))
                continue

            if asset is None:
                raise AudioRenderError("no audio asset available for rendering", fallback_triggered=False)

            asset_pcm = asset.canonical_pcm
            segment_pcm = tempo_transform(asset_pcm, segment.target_tempo_ratio, plan.canonical_audio_config["sample_rate"])
            transformed, clip_count, peak, rms = gain_and_emphasis(
                segment_pcm, control_state.vocal_energy, segment.target_prosodic_emphasis
            )

            pcm_parts.append(silence_transform(segment.pre_silence_duration_ms, plan.canonical_audio_config["sample_rate"]))
            pcm_parts.append(transformed)
            pcm_parts.append(silence_transform(segment.post_silence_duration_ms, plan.canonical_audio_config["sample_rate"]))

            if runtime is not None:
                runtime.emit(
                    CLM03EventType.AUDIO_SEGMENT_TRANSFORMED,
                    {
                        "segment_id": segment.segment_id,
                        "asset_id": asset.asset_id,
                        "clip_count": clip_count,
                        "peak_amplitude": round(peak, 6),
                        "rms_amplitude": round(rms, 6),
                    },
                    component="clm03_audio",
                    component_version=self.version,
                )

        full_pcm = b"".join(pcm_parts)
        canonical_bytes = _build_wav(
            full_pcm,
            plan.canonical_audio_config["sample_rate"],
            plan.canonical_audio_config["channels"],
            plan.canonical_audio_config["sample_width"],
        )

        try:
            _validate_artifact(canonical_bytes)
        except AudioRenderError as exc:
            if runtime is not None:
                runtime.emit(
                    CLM03EventType.AUDIO_RENDER_FAILED,
                    {"reason": exc.reason, "render_cycle_id": render_cycle_id},
                    component="clm03_audio",
                    component_version=self.version,
                )
            raise

        frame_count = len(full_pcm) // 2
        duration = frame_count / plan.canonical_audio_config["sample_rate"]
        peak = compute_peak(full_pcm)
        rms = compute_rms(full_pcm)

        applied_control_state_id = control_state.control_state_id
        if fallback_used:
            if self.last_valid_artifact is not None:
                applied_control_state_id = self.last_valid_artifact.applied_control_state_id
            else:
                applied_control_state_id = MantraControlState.baseline().control_state_id

        artifact_id = f"artifact-{render_cycle_id}-{control_state.control_state_id}"
        artifact_dict = {
            "artifact_id": artifact_id,
            "plan_id": plan.plan_id,
            "render_cycle_id": render_cycle_id,
            "frame_count": frame_count,
            "duration": duration,
            "sample_rate": plan.canonical_audio_config["sample_rate"],
            "channels": plan.canonical_audio_config["channels"],
            "sample_width": plan.canonical_audio_config["sample_width"],
            "peak_amplitude": peak,
            "rms_amplitude": rms,
            "clipping_count": 0,
            "applied_control_state_id": applied_control_state_id,
            "source_actuation_receipt_id": actuation_receipt_id,
            "renderer_id": self.renderer_id,
            "renderer_version": self.version,
            "fallback_used": fallback_used,
            "fallback_reason": fallback_reason,
        }
        digest = _render_digest(artifact_dict, canonical_bytes)

        artifact = RenderedAudioArtifact(
            artifact_id=artifact_id,
            plan_id=plan.plan_id,
            render_cycle_id=render_cycle_id,
            audio_checksum=hashlib.sha256(canonical_bytes).hexdigest(),
            canonical_bytes=canonical_bytes,
            frame_count=frame_count,
            duration=duration,
            sample_rate=plan.canonical_audio_config["sample_rate"],
            channels=plan.canonical_audio_config["channels"],
            sample_width=plan.canonical_audio_config["sample_width"],
            peak_amplitude=peak,
            rms_amplitude=rms,
            clipping_count=0,
            applied_control_state_id=applied_control_state_id,
            source_actuation_receipt_id=actuation_receipt_id,
            renderer_id=self.renderer_id,
            renderer_version=self.version,
            render_digest=digest,
            fallback_used=fallback_used,
            fallback_reason=fallback_reason,
        )

        self.last_valid_artifact = artifact

        if runtime is not None:
            runtime.emit(
                CLM03EventType.AUDIO_ARTIFACT_RENDERED,
                artifact.as_dict(),
                component="clm03_audio",
                component_version=self.version,
                provenance=[start_event_id] if start_event_id else [],
            )
            runtime.emit(
                CLM03EventType.AUDIO_ARTIFACT_VALIDATED,
                {"artifact_id": artifact_id, "audio_checksum": artifact.audio_checksum},
                component="clm03_audio",
                component_version=self.version,
            )
            runtime.emit(
                CLM03EventType.AUDIO_DIGEST_COMPUTED,
                {
                    "artifact_id": artifact_id,
                    "render_digest": digest,
                    "audio_checksum": artifact.audio_checksum,
                },
                component="clm03_audio",
                component_version=self.version,
            )
            if fallback_used:
                runtime.emit(
                    CLM03EventType.AUDIO_FALLBACK_APPLIED,
                    {
                        "artifact_id": artifact_id,
                        "fallback_reason": fallback_reason,
                        "source_actuation_receipt_id": actuation_receipt_id,
                    },
                    component="clm03_audio",
                    component_version=self.version,
                )

        return artifact
