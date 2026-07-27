"""CLM-06 Hebrew adaptive vertical slice."""

from __future__ import annotations

__version__ = "1.0.0"

from mindtune_clm.hebrew_slice.adaptation import HebrewAdaptationPolicy
from mindtune_clm.hebrew_slice.asset_resolution import (
    HebrewAssetError,
    HebrewAssetResolver,
    HebrewResolvedAssets,
    make_synthetic_giuseppe_audio_asset,
    make_synthetic_hebrew_audio_asset,
)
from mindtune_clm.hebrew_slice.curriculum_adapter import HebrewCurriculumAdapter
from mindtune_clm.hebrew_slice.error_taxonomy import HebrewErrorCode
from mindtune_clm.hebrew_slice.events import HebrewEventLog, HebrewSliceEventType
from mindtune_clm.hebrew_slice.fixture_clm06 import make_clm06_test_fixture
from mindtune_clm.hebrew_slice.learning_state import update_learning_state
from mindtune_clm.hebrew_slice.models import (
    HebrewAdaptiveEvent,
    HebrewAdaptiveItem,
    HebrewItemLearningState,
    HebrewPedagogicalDecision,
    HebrewResponse,
    HebrewScore,
    HebrewTrial,
)
from mindtune_clm.hebrew_slice.scoring import score_response
from mindtune_clm.hebrew_slice.session import (
    HebrewAdaptiveSession,
    HebrewSessionError,
)
from mindtune_clm.hebrew_slice.trial_factory import HebrewTrialFactory

__all__ = [
    "HebrewAdaptationPolicy",
    "HebrewAdaptiveItem",
    "HebrewAdaptiveSession",
    "HebrewAdaptiveEvent",
    "HebrewAssetError",
    "HebrewAssetResolver",
    "HebrewCurriculumAdapter",
    "HebrewErrorCode",
    "HebrewEventLog",
    "HebrewItemLearningState",
    "HebrewPedagogicalDecision",
    "HebrewResolvedAssets",
    "HebrewResponse",
    "HebrewScore",
    "HebrewSessionError",
    "HebrewSliceEventType",
    "HebrewTrial",
    "HebrewTrialFactory",
    "make_clm06_test_fixture",
    "make_synthetic_giuseppe_audio_asset",
    "make_synthetic_hebrew_audio_asset",
    "score_response",
    "update_learning_state",
    "__version__",
]
