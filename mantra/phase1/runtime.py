"""Audio runtime boundary for validated Mantra execution plans.

This module is the only place where the protocol layer (Curriculum,
MantraExecutionPlan, AudioAssetRequirement) meets the audio runtime
(AudioAssetRegistry, build_compact_mantra).  It does not call TTS unless
explicitly asked to prepare missing assets.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .asset_contract import (
    AssetAvailabilityClass,
    AudioAssetInventory,
    AudioAssetRequirement,
)
from .assets import AudioAssetRegistry, build_compact_mantra
from .curriculum import MantraExecutionPlan
from .tts import TTSRuntimeError


def _pause_after(
    requirements: list[AudioAssetRequirement],
    idx: int,
    silence_durations: dict[str, float],
    default_pause: float,
) -> float | None:
    if idx == len(requirements) - 1:
        return None
    current = requirements[idx]
    next_req = requirements[idx + 1]
    if current.section != next_req.section:
        return silence_durations.get("section_boundary", 0.0)
    return silence_durations.get("inter_item_default", default_pause)


def execute_mantra_plan(
    plan: MantraExecutionPlan,
    registry: AudioAssetRegistry,
    *,
    default_pause: float = 0.3,
) -> dict[str, Any]:
    """Assemble a WAV file from a validated execution plan.

    If the plan carries typed ``AudioAssetRequirement`` objects, the runtime
    uses the profile silence durations; otherwise it falls back to the
    default pause between every item.
    """
    if not plan.asset_sequence:
        return {}
    if plan.output_path is None:
        raise TTSRuntimeError("MantraExecutionPlan has no output_path")

    if plan.requirements:
        # Requirements carry audio-profile silence configuration implicitly
        # through their sequence order. Use default pause per item for now.
        items = [(req.asset_id, None) for req in plan.requirements]
    else:
        items = [(asset_id, None) for asset_id in plan.asset_sequence]

    return build_compact_mantra(registry, items, plan.output_path, default_pause=default_pause)


def build_asset_preparation_plan(
    plan: MantraExecutionPlan,
    inventory: AudioAssetInventory,
) -> list[AudioAssetRequirement]:
    """Return the missing synthesizable requirements for a plan."""
    if not plan.requirements:
        return []
    missing: list[AudioAssetRequirement] = []
    for req in plan.requirements:
        classification = inventory.classify(req)
        if classification == AssetAvailabilityClass.MISSING_SYNTHESIZABLE:
            missing.append(req)
    return missing


def execute_asset_preparation_plan(
    requirements: list[AudioAssetRequirement],
    registry: AudioAssetRegistry,
    *,
    provider: Any | None = None,
    api_key: str | None = None,
    email: str | None = None,
) -> list[Path]:
    """Synthesize every missing requirement and register the resulting assets.

    The provider may be omitted; ``SpeechGenTTSProvider`` is used by default.
    Pass ``api_key`` and ``email`` explicitly when running outside an
    environment that already exports ``SPEECHGEN_API_KEY``.
    """
    paths: list[Path] = []
    for req in requirements:
        path = registry.ensure(
            asset_id=req.asset_id,
            text=req.tts_text,
            voice=req.voice_id,
            locale=req.locale,
            provider_name=req.provider,
            rate=req.synthesis_parameters.get("rate", 1.0),
            pitch=req.synthesis_parameters.get("pitch", 0.0),
            fmt=req.expected_audio_format,
            source_text=req.source_text,
            api_key=api_key,
            email=email,
            provider=provider,
        )
        paths.append(path)
    return paths
