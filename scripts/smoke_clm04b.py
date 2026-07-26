#!/usr/bin/env python3
"""Manual non-CI smoke test for CLM-04B on macOS with real speakers.

This script is intentionally not run by the test suite. It exercises the
MacOSPlaybackBackend and Giuseppe/Aaron synthetic assets without calling
SpeechGen or any external service.
"""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

from mindtune_clm.audio.renderer import AudioRenderer
from mindtune_clm.live_loop import LiveClosedLoopOrchestrator, MacOSPlaybackBackend
from mindtune_clm.live_loop.fixture_clm04b import (
    build_voice_cache_and_registry,
    make_synthetic_frames,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="CLM-04B manual smoke test")
    parser.add_argument("--scenario", default="stable", help="stable|deterioration|escalation|recovery")
    parser.add_argument("--frames", type=int, default=3, help="number of frames to run")
    parser.add_argument("--cache-dir", type=Path, default=None, help="voice cache directory")
    args = parser.parse_args()

    cache_dir = args.cache_dir or Path(tempfile.mkdtemp(prefix="clm04b_smoke_"))
    cache, registry = build_voice_cache_and_registry(cache_dir)

    orchestrator = LiveClosedLoopOrchestrator(
        cache=cache,
        asset_registry=registry,
        playback_backend=MacOSPlaybackBackend(),
        renderer=AudioRenderer(asset_registry=registry),
    )

    frames = make_synthetic_frames(
        session_id="smoke",
        scenario=args.scenario,
        count=args.frames,
        timestamp_step=2.5,
    )

    orchestrator.start()
    for frame in frames:
        if orchestrator.state.killed:
            break
        receipt = orchestrator.run_step(frame)
        print(receipt.as_dict())
    orchestrator.complete()


if __name__ == "__main__":
    main()
