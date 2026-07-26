"""Reusable deterministic fixtures for CLM-04 live gateway tests."""

from __future__ import annotations


def make_synthetic_csv(
    duration: float = 2.5,
    packet_interval: float = 0.1,
    base_eeg: float = 78.5,
) -> str:
    """Return a short deterministic CSV string compatible with FC11LiveSource.

    The header matches the FC11 EEG fixture schema so the same parser can be
    reused for live smoke tests.
    """
    lines = [
        "timestamp,packet_index,eeg_scaled,attention_score_smoothed,meditation_score_smoothed,signal_quality,artifact_flag,movement_flag,packet_loss"
    ]
    count = int(duration / packet_interval)
    for i in range(count):
        t = round(i * packet_interval, 3)
        noise = 0.0 if i % 2 == 0 else 0.02
        eeg = round(base_eeg + noise, 3)
        lines.append(
            f"{t:.3f},{i},{eeg},48.0,55.0,5,0,0,0"
        )
    return "\n".join(lines) + "\n"


def make_synthetic_source_kwargs(
    duration: float = 2.5,
    packet_interval: float = 0.1,
    seed: int = 0,
) -> dict:
    """Return kwargs for a deterministic SyntheticLiveSource fixture."""
    return {
        "source_id": "fixture-synthetic",
        "duration": duration,
        "packet_interval": packet_interval,
        "seed": seed,
        "source_start_timestamp": 0.0,
    }
