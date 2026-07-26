"""Deterministic six-cycle fixture for CLM-01."""

from __future__ import annotations

from mindtune_clm.observations import ObservationFrame


def make_clm01_fixture(session_id: str = "clm01-session-001") -> list[ObservationFrame]:
    """Return the six deterministic control-cycle observation frames for CLM-01.

    The execution model produces six control cycles and seven rendered mantra
    cycles (one initial baseline render plus one render after each control cycle).

    Control cycles:
      1. stable
      2. possible deterioration (one rejected EEG artifact)
      3. sustained deterioration
      4. impaired, no further escalation (poor-signal EEG rejected)
      5. first recovery evidence (EEG absent)
      6. sustained recovery
    """
    frames = [
        ObservationFrame(
            observation_frame_id=f"{session_id}-obs-1",
            control_cycle_id=f"{session_id}-cc-1",
            session_id=session_id,
            sequence_number=1,
            observation_timestamp=1.0,
            behavioral_latency_ms=400.0,
            hesitation_score=0.1,
            error_score=0.0,
            eeg_stability=0.9,
            eeg_quality="good",
            respiration_stability=0.95,
            voice_stability=0.95,
            available_modalities=["behavioral", "eeg", "respiration", "voice"],
            source_event_ids=["source-stable"],
        ),
        ObservationFrame(
            observation_frame_id=f"{session_id}-obs-2",
            control_cycle_id=f"{session_id}-cc-2",
            session_id=session_id,
            sequence_number=2,
            observation_timestamp=2.0,
            behavioral_latency_ms=1500.0,
            hesitation_score=0.6,
            error_score=0.0,
            eeg_stability=0.2,
            eeg_quality="artifact",
            respiration_stability=0.8,
            voice_stability=0.8,
            available_modalities=["behavioral", "eeg", "respiration", "voice"],
            source_event_ids=["source-drift"],
        ),
        ObservationFrame(
            observation_frame_id=f"{session_id}-obs-3",
            control_cycle_id=f"{session_id}-cc-3",
            session_id=session_id,
            sequence_number=3,
            observation_timestamp=3.0,
            behavioral_latency_ms=2200.0,
            hesitation_score=0.8,
            error_score=0.0,
            eeg_stability=0.4,
            eeg_quality="good",
            respiration_stability=0.6,
            voice_stability=0.6,
            available_modalities=["behavioral", "eeg", "respiration", "voice"],
            source_event_ids=["source-sustained"],
        ),
        ObservationFrame(
            observation_frame_id=f"{session_id}-obs-4",
            control_cycle_id=f"{session_id}-cc-4",
            session_id=session_id,
            sequence_number=4,
            observation_timestamp=4.0,
            behavioral_latency_ms=2100.0,
            hesitation_score=0.7,
            error_score=0.0,
            eeg_stability=0.9,
            eeg_quality="poor_signal",
            respiration_stability=0.6,
            voice_stability=0.6,
            available_modalities=["behavioral", "eeg", "respiration", "voice"],
            source_event_ids=["source-impaired"],
        ),
        ObservationFrame(
            observation_frame_id=f"{session_id}-obs-5",
            control_cycle_id=f"{session_id}-cc-5",
            session_id=session_id,
            sequence_number=5,
            observation_timestamp=5.0,
            behavioral_latency_ms=600.0,
            hesitation_score=0.1,
            error_score=0.0,
            eeg_stability=None,
            eeg_quality=None,
            respiration_stability=0.9,
            voice_stability=0.9,
            available_modalities=["behavioral", "respiration", "voice"],
            source_event_ids=["source-recovery-1"],
        ),
        ObservationFrame(
            observation_frame_id=f"{session_id}-obs-6",
            control_cycle_id=f"{session_id}-cc-6",
            session_id=session_id,
            sequence_number=6,
            observation_timestamp=6.0,
            behavioral_latency_ms=500.0,
            hesitation_score=0.0,
            error_score=0.0,
            eeg_stability=0.9,
            eeg_quality="good",
            respiration_stability=0.95,
            voice_stability=0.95,
            available_modalities=["behavioral", "eeg", "respiration", "voice"],
            source_event_ids=["source-recovery-2"],
        ),
    ]
    return frames
