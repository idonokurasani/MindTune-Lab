"""FC11-specific ObservationFrame mapping for CLM-02B."""

from __future__ import annotations

from mindtune_clm.observations import ObservationFrame
from mindtune_clm.replay.adapter import to_observation_frame as _generic_to_observation_frame
from mindtune_clm.replay.models import NormalizedSensorSample, ReplayWindow


def to_observation_frame(
    window: ReplayWindow,
    samples: dict[str, NormalizedSensorSample],
    replay_id: str,
    sequence_number: int,
) -> ObservationFrame:
    """Map an FC11 replay window to an ObservationFrame.

    EEG stability is taken from the ``signal_stability`` deterministic feature
    computed from the ``eeg_scaled`` primary channel.  No behavioral evidence is
    fabricated.
    """
    return _generic_to_observation_frame(
        window,
        samples,
        replay_id,
        sequence_number,
        eeg_channel="eeg_scaled",
        eeg_stability_feature="signal_stability",
    )
