"""Manifest generation for a built mantra artifact."""

from __future__ import annotations

import datetime
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .assembly import AssemblyResult
from .events import EventEmitter
from .spec import MantraSpecification
from .timeline import TimelineSegment
from .utils import canonical_json, save_json, sha256_hex


@dataclass
class MantraManifest:
    """Machine-readable provenance record for one built mantra."""

    specification: MantraSpecification
    specification_version: str
    build_timestamp: str
    build_identity: str
    source_verb: str
    source_root: str
    source_binyan: str
    timeline: list[TimelineSegment]
    planned_duration: float
    actual_duration: float
    total_segments: int
    provider: str
    voice: str
    italian_provider: str
    italian_voice: str
    speech_rate: float
    speech_pitch: float
    pause_configuration: dict[str, Any]
    output_artifact_path: str
    segments_directory: str
    cache_directory: str
    event_log_path: str
    warnings: list[str]
    validation_results: dict[str, Any]
    status: str
    format: str
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "specification": self.specification.to_dict(),
            "specification_version": self.specification_version,
            "build_timestamp": self.build_timestamp,
            "build_identity": self.build_identity,
            "source_verb": self.source_verb,
            "source_root": self.source_root,
            "source_binyan": self.source_binyan,
            "timeline": [s.to_dict() for s in self.timeline],
            "planned_duration": self.planned_duration,
            "actual_duration": self.actual_duration,
            "total_segments": self.total_segments,
            "provider": self.provider,
            "voice": self.voice,
            "italian_provider": self.italian_provider,
            "italian_voice": self.italian_voice,
            "speech_rate": self.speech_rate,
            "speech_pitch": self.speech_pitch,
            "pause_configuration": self.pause_configuration,
            "output_artifact_path": self.output_artifact_path,
            "segments_directory": self.segments_directory,
            "cache_directory": self.cache_directory,
            "event_log_path": self.event_log_path,
            "warnings": self.warnings,
            "validation_results": self.validation_results,
            "status": self.status,
            "format": self.format,
            "metadata": self.metadata,
        }


def _build_identity(spec: MantraSpecification) -> str:
    canonical = canonical_json(spec.to_dict())
    return f"{spec.id}@{spec.version}#{sha256_hex(canonical + spec.build_seed)}"


def _validate_manifest(manifest: MantraManifest) -> dict[str, Any]:
    results: dict[str, Any] = {
        "artifact_exists": Path(manifest.output_artifact_path).exists(),
        "timeline_matches_segment_count": len(manifest.timeline) == manifest.total_segments,
        "actual_duration_positive": manifest.actual_duration > 0.0,
        "planned_duration_positive": manifest.planned_duration > 0.0,
        "provider_set": bool(manifest.provider),
        "voice_set": bool(manifest.voice),
        "italian_provider_set": bool(manifest.italian_provider),
        "italian_voice_set": bool(manifest.italian_voice),
    }
    results["valid"] = all(results.values()) and not manifest.warnings
    return results


def write_manifest(
    spec: MantraSpecification,
    timeline: list[TimelineSegment],
    assembly: AssemblyResult,
    events: EventEmitter,
    output_dir: Path,
    cache_dir: Path,
) -> Path:
    """Write the manifest and event log for a built mantra."""
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    identity = _build_identity(spec)
    planned = sum(s.planned_duration for s in timeline)
    manifest = MantraManifest(
        specification=spec,
        specification_version=spec.version,
        build_timestamp=now,
        build_identity=identity,
        source_verb=spec.hebrew_infinitive,
        source_root=spec.lexical_root,
        source_binyan=spec.binyan,
        timeline=timeline,
        planned_duration=planned,
        actual_duration=assembly.total_duration,
        total_segments=len(timeline),
        provider=spec.speech.provider,
        voice=spec.speech.voice,
        italian_provider=spec.italian_speech.provider,
        italian_voice=spec.italian_speech.voice,
        speech_rate=spec.speech.rate,
        speech_pitch=spec.speech.pitch,
        pause_configuration=spec.pauses.to_dict(),
        output_artifact_path=str(assembly.output_path),
        segments_directory=str(assembly.segments_dir),
        cache_directory=str(cache_dir),
        event_log_path=str(assembly.events_path),
        warnings=assembly.warnings,
        validation_results={},
        status="pending_validation",
        format=spec.output_format,
        metadata={"build_engine_version": "1.0.0"},
    )
    manifest.validation_results = _validate_manifest(manifest)
    manifest.status = (
        "completed" if manifest.validation_results["valid"] else "completed_with_warnings"
    )

    save_json(assembly.manifest_path, manifest.to_dict())
    events.save(assembly.events_path)
    return assembly.manifest_path
