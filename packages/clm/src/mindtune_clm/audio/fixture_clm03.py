"""Synthetic CLM-03 audio fixtures and control states for tests."""

from __future__ import annotations

from pathlib import Path

from mindtune_clm.audio.assets import AudioAssetRegistry, AudioRole, load_wav_asset
from mindtune_clm.state import MantraControlState


def _fixture_dir() -> Path:
    """Return the repository-relative audio fixture directory."""
    # packages/clm/src/mindtune_clm/audio/fixture_clm03.py -> repo root
    return Path(__file__).resolve().parents[5] / "packages" / "clm" / "tests" / "fixtures" / "audio"


def default_registry() -> AudioAssetRegistry:
    """Return a registry populated with the synthetic CLM-03 audio fixtures."""
    directory = _fixture_dir()
    assets = [
        load_wav_asset(
            path=directory / "speech_segment.wav",
            asset_id="speech_segment",
            role=AudioRole.SPEECH_SEGMENT,
            label="Om-like synthetic tone",
            source_type="synthetic_fixture",
            provenance=["speech_segment.wav"],
            semantic_tags=frozenset({"baseline", "mantra"}),
        ),
        load_wav_asset(
            path=directory / "breathing_cue.wav",
            asset_id="breathing_cue",
            role=AudioRole.BREATHING_CUE,
            label="Synthetic inhalation tone",
            source_type="synthetic_fixture",
            provenance=["breathing_cue.wav"],
            semantic_tags=frozenset({"breath", "cue"}),
        ),
    ]
    return AudioAssetRegistry(assets)


def state_baseline() -> MantraControlState:
    """Fixture A — canonical baseline."""
    return MantraControlState(
        tempo_ratio=1.0,
        pre_stimulus_pause_ms=0,
        post_stimulus_pause_ms=0,
        repetition_count=1,
        prosodic_emphasis=0.0,
        vocal_energy=0.0,
        breathing_cue=False,
        assistance_level=0.0,
        control_state_id="baseline",
    )


def state_first_intervention() -> MantraControlState:
    """Fixture B — first bounded CLM-01 intervention."""
    return MantraControlState(
        tempo_ratio=0.95,
        post_stimulus_pause_ms=300,
        repetition_count=1,
        prosodic_emphasis=0.1,
        vocal_energy=0.0,
        breathing_cue=False,
        assistance_level=0.2,
        control_state_id="first_intervention",
    )


def state_escalated() -> MantraControlState:
    """Fixture C — escalated intervention with repetition and breathing cue."""
    return MantraControlState(
        tempo_ratio=0.85,
        post_stimulus_pause_ms=500,
        repetition_count=2,
        prosodic_emphasis=0.15,
        vocal_energy=0.3,
        breathing_cue=True,
        assistance_level=0.5,
        control_state_id="escalated",
    )


def state_withdrawal_step_1() -> MantraControlState:
    """Fixture D — first withdrawal step."""
    return MantraControlState(
        tempo_ratio=0.95,
        post_stimulus_pause_ms=200,
        repetition_count=1,
        prosodic_emphasis=0.05,
        vocal_energy=0.0,
        breathing_cue=False,
        assistance_level=0.1,
        control_state_id="withdrawal_step_1",
    )


def state_withdrawal_step_2() -> MantraControlState:
    """Fixture D — second withdrawal step back to byte-equivalent baseline."""
    return MantraControlState(
        tempo_ratio=1.0,
        post_stimulus_pause_ms=0,
        repetition_count=1,
        prosodic_emphasis=0.0,
        vocal_energy=0.0,
        breathing_cue=False,
        assistance_level=0.0,
        control_state_id="withdrawal_step_2",
    )
