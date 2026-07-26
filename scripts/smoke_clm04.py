#!/usr/bin/env python3
"""Manual non-CI smoke test for the CLM-04 live FC11 sensor gateway.

This script is intentionally simple: it exercises the live gateway with a
deterministic synthetic source and prints the resulting observation frames.
It does not contact hardware and does not require SpeechGen or audio playback.
"""

from __future__ import annotations

import argparse

from mindtune_clm.live import LiveGateway, SyntheticLiveSource


def main() -> None:
    parser = argparse.ArgumentParser(description="CLM-04 live gateway smoke test")
    parser.add_argument(
        "--duration",
        type=float,
        default=2.5,
        help="Synthetic stream duration in seconds",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=0.1,
        help="Packet interval in seconds",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Deterministic seed for the synthetic source",
    )
    args = parser.parse_args()

    source = SyntheticLiveSource(
        source_id="smoke-synthetic",
        duration=args.duration,
        packet_interval=args.interval,
        seed=args.seed,
    )
    gateway = LiveGateway(source=source)
    result = gateway.run()

    print(f"Session ID : {result.session_id}")
    print(f"Source ID  : {result.source_id}")
    print(f"Frames     : {len(result.observation_frames)}")
    print(f"Samples    : {len(result.normalized_samples)}")
    print(f"Windows    : {len(result.windows)}")
    print(f"Health     : {result.health.status if result.health else None}")
    print(f"Events     : {len(result.event_ids)}")

    for frame in result.observation_frames:
        print(
            f"  frame {frame.sequence_number}: "
            f"eeg_stability={frame.eeg_stability}, "
            f"eeg_quality={frame.eeg_quality}, "
            f"modalities={frame.available_modalities}"
        )


if __name__ == "__main__":
    main()
