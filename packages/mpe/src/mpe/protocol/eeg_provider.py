"""Deterministic mock EEG provider for closed-loop integration testing."""

from __future__ import annotations

from typing import Any

from mpe.providers import EEGProvider
from mpe.types import ObservationID, make_id


class MockEEGProvider(EEGProvider):
    """Deterministic EEG provider driven by fixture item fields.

    The fixture item may declare ``eeg_load`` (0.0-1.0 cognitive-load index)
    and ``eeg_quality_flags`` (e.g. ``["artifact"]``) to exercise signal-quality
    gating without requiring real hardware.
    """

    observation_type: str = "eeg_burst"
    provider_id: str = "mock_eeg"
    provider_version: str = "1.0.0"
    quality_model_id: str = "mock_eeg_quality"
    quality_model_version: str = "1.0.0"

    def __init__(self, fixture: Any | None = None) -> None:
        self.fixture = fixture

    def capabilities(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "provider_version": self.provider_version,
            "observation_types_supported": [self.observation_type],
            "quality_dimensions_supported": {"alpha_power": "0-1", "beta_power": "0-1"},
            "quality_flags_supported": ["good", "artifact", "poor_signal"],
            "quality_model_id": self.quality_model_id,
            "quality_model_version": self.quality_model_version,
        }

    def poll(self, content_item_id: str) -> dict[str, Any]:
        eeg_load = 0.0
        quality_flags: list[str] = []
        if self.fixture is not None:
            item = self.fixture.item_by_id(content_item_id)
            if item is not None:
                eeg_load = float(getattr(item, "eeg_load", 0.0) or 0.0)
                flags = getattr(item, "eeg_quality_flags", None) or []
                quality_flags = list(flags)
        alpha_power = max(0.0, 1.0 - eeg_load)
        beta_power = max(0.0, eeg_load)
        return {
            "observation_id": str(make_id(ObservationID)),
            "provider_id": self.provider_id,
            "provider_version": self.provider_version,
            "observation_type": self.observation_type,
            "payload": {
                "alpha_power": round(alpha_power, 3),
                "beta_power": round(beta_power, 3),
                "cognitive_load_index": round(eeg_load, 3),
            },
            "quality_dimensions": {"alpha_power": round(alpha_power, 3), "beta_power": round(beta_power, 3)},
            "quality_flags": quality_flags,
            "quality_model_id": self.quality_model_id,
            "quality_model_version": self.quality_model_version,
        }
