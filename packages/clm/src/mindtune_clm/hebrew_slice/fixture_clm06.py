"""Bounded, deterministic CLM-06 Hebrew fixture with synthetic test assets."""

from __future__ import annotations

from mindtune_clm.audio.assets import AudioAssetRegistry
from mindtune_clm.audio.fixture_clm03 import default_registry
from mindtune_clm.hebrew_slice.asset_resolution import (
    make_synthetic_giuseppe_audio_asset,
    make_synthetic_hebrew_audio_asset,
)
from mindtune_clm.hebrew_slice.curriculum_adapter import HebrewCurriculumAdapter
from mindtune_clm.hebrew_slice.models import HebrewAdaptiveItem


def make_clm06_test_fixture(
    *,
    point_duration: float = 0.3,
    include_giuseppe: bool = True,
) -> tuple[HebrewCurriculumAdapter, AudioAssetRegistry, list[HebrewAdaptiveItem]]:
    """Return a validated curriculum adapter and matching synthetic audio registry."""
    adapter = HebrewCurriculumAdapter()
    approved = adapter.approved_items()
    registry = default_registry()
    asset_inventory = {a.asset_id for a in registry.assets()}
    kept_items: list[HebrewAdaptiveItem] = []

    for item in approved:
        for aid in item.required_audio_asset_ids:
            if aid not in asset_inventory:
                registry.register(make_synthetic_hebrew_audio_asset(aid, item.canonical_pointed, duration=point_duration))
                asset_inventory.add(aid)
        if include_giuseppe:
            italian_id = f"clm06.giuseppe.{item.lemma_unpointed}"
            if italian_id not in asset_inventory:
                registry.register(make_synthetic_giuseppe_audio_asset(italian_id, item.italian_gloss, duration=point_duration))
                asset_inventory.add(italian_id)
        kept_items.append(item)

    return adapter, registry, kept_items


def clm06_test_asset_inventory() -> set[str]:
    """Return the set of asset ids available in the test fixture."""
    _, _, items = make_clm06_test_fixture()
    return {aid for i in items for aid in i.required_audio_asset_ids}
