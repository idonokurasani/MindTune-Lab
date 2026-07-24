"""Command-line interface for the Phase 1 Mantra engine."""
from __future__ import annotations

import argparse
import dataclasses
import sys
from pathlib import Path
from typing import Any

from .assembly import assemble_audio
from .events import EventEmitter, MantraEventType
from .fixtures import load_fixture_001_lichtov
from .manifest import write_manifest
from .playback import NullAudioPlayer, PlaybackController, SubprocessAudioPlayer
from .spec import MantraSpecification
from .timeline import compile_timeline
from .tts import FakeTTSProvider, SpeechGenTTSProvider, TTSProvider
from .utils import load_json


def _resolve_spec(args: argparse.Namespace) -> MantraSpecification:
    if args.fixture:
        if args.fixture == "001_lichtov":
            return load_fixture_001_lichtov()
        raise SystemExit(f"Unknown fixture: {args.fixture}")
    if args.input:
        data = load_json(Path(args.input))
        return MantraSpecification.from_dict(data)
    raise SystemExit("Either --input or --fixture is required")


def _resolve_provider(spec: MantraSpecification, args: argparse.Namespace) -> TTSProvider:
    provider_name = args.provider or spec.speech.provider
    if provider_name == "speechgen":
        return SpeechGenTTSProvider(
            voice=args.voice or spec.speech.voice,
            rate=args.rate or spec.speech.rate,
            pitch=args.pitch or spec.speech.pitch,
            fmt=args.format or spec.speech.format,
        )
    if provider_name == "fake":
        return FakeTTSProvider()
    raise SystemExit(f"Unknown TTS provider: {provider_name}")


def cmd_build(args: argparse.Namespace) -> int:
    """Build a mantra from a specification and write the artifact and manifest."""
    output_dir = Path(args.output_dir)
    cache_dir = Path(args.cache_dir) if args.cache_dir else output_dir / "cache"

    events = EventEmitter()
    events.emit(MantraEventType.BUILD_STARTED, {"output_dir": str(output_dir)})

    try:
        spec = _resolve_spec(args)
    except Exception as exc:
        events.emit(MantraEventType.SPEC_VALIDATED, {"valid": False, "error": str(exc)})
        print(f"Error: invalid specification: {exc}", file=sys.stderr)
        return 2

    events.emit(MantraEventType.SPEC_VALIDATED, {"valid": True, "id": spec.id, "version": spec.version})

    if args.validate_only:
        print(f"Specification {spec.id} is valid.")
        return 0

    # Apply CLI speech overrides to the immutable specification.
    speech = dataclasses.replace(
        spec.speech,
        provider=args.provider or spec.speech.provider,
        voice=args.voice or spec.speech.voice,
        rate=args.rate or spec.speech.rate,
        pitch=args.pitch or spec.speech.pitch,
        format=args.format or spec.speech.format,
    )
    spec = dataclasses.replace(spec, speech=speech)

    timeline = compile_timeline(spec)
    events.emit(
        MantraEventType.TIMELINE_COMPILED,
        {"segment_count": len(timeline), "planned_duration": sum(s.planned_duration for s in timeline)},
    )

    provider = _resolve_provider(spec, args)
    try:
        assembly = assemble_audio(
            spec,
            timeline,
            provider,
            output_dir,
            cache_dir=cache_dir,
            events=events,
            target_sample_rate=args.sample_rate,
        )
    except Exception as exc:
        print(f"Error: audio assembly failed: {exc}", file=sys.stderr)
        return 1

    manifest_path = write_manifest(spec, timeline, assembly, events, output_dir, cache_dir)
    events.emit(
        MantraEventType.BUILD_COMPLETED,
        {"manifest_path": str(manifest_path), "output_path": str(assembly.output_path)},
    )

    print(f"Built mantra: {assembly.output_path}")
    print(f"Manifest: {manifest_path}")
    print(f"Events: {assembly.events_path}")
    print(f"Duration: {assembly.total_duration:.3f}s")
    if assembly.warnings:
        for warning in assembly.warnings:
            print(f"Warning: {warning}")
    return 0


def cmd_play(args: argparse.Namespace) -> int:
    """Play a built mantra from its manifest."""
    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        print(f"Error: manifest not found: {manifest_path}", file=sys.stderr)
        return 2
    manifest = load_json(manifest_path)
    timeline = compile_timeline(MantraSpecification.from_dict(manifest["specification"]))
    segments_dir = manifest_path.parent / manifest["segments_directory"]

    events = EventEmitter()
    player: Any = SubprocessAudioPlayer()
    if args.fake_audio:
        player = NullAudioPlayer()
    controller = PlaybackController(timeline, segments_dir, player, events)
    controller.start()
    print("Playing... press Ctrl-C to stop")
    try:
        controller.wait_until_complete()
    except KeyboardInterrupt:
        controller.stop()
    print(f"Playback finished. Events: {len(events.events)}")
    if args.event_log:
        events.save(Path(args.event_log))
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Validate a Mantra specification file."""
    try:
        data = load_json(Path(args.input))
        spec = MantraSpecification.from_dict(data)
        print(f"Specification {spec.id}@{spec.version} is valid.")
        return 0
    except Exception as exc:
        print(f"Invalid specification: {exc}", file=sys.stderr)
        return 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="mantra-phase1",
        description="MindTune Mantra Engine Phase 1 CLI",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_p = subparsers.add_parser("build", help="Build a mantra audio artifact")
    build_p.add_argument("--input", "-i", help="Path to a Mantra specification JSON")
    build_p.add_argument("--fixture", "-f", help="Use a built-in fixture (001_lichtov)")
    build_p.add_argument("--output-dir", "-o", required=True, help="Output directory")
    build_p.add_argument("--cache-dir", "-c", help="TTS cache directory")
    build_p.add_argument("--provider", help="TTS provider (speechgen, fake)")
    build_p.add_argument("--voice", help="TTS voice")
    build_p.add_argument("--rate", type=float, help="Speech rate (0.5-2.0)")
    build_p.add_argument("--pitch", type=float, help="Speech pitch (-20..20)")
    build_p.add_argument("--format", help="Output audio format (wav, mp3, ogg)")
    build_p.add_argument("--sample-rate", type=int, default=22050, help="Target sample rate")
    build_p.add_argument("--validate-only", action="store_true", help="Validate spec only")
    build_p.add_argument("--force-rebuild", action="store_true", help="Ignore cache and rebuild")
    build_p.set_defaults(func=cmd_build)

    play_p = subparsers.add_parser("play", help="Play a built mantra")
    play_p.add_argument("manifest", help="Path to the manifest JSON")
    play_p.add_argument("--fake-audio", action="store_true", help="Use null audio player for testing")
    play_p.add_argument("--event-log", help="Path to write playback events")
    play_p.set_defaults(func=cmd_play)

    val_p = subparsers.add_parser("validate", help="Validate a specification JSON")
    val_p.add_argument("input", help="Path to the specification JSON")
    val_p.set_defaults(func=cmd_validate)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
