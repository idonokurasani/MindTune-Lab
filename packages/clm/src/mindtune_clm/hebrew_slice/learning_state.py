"""Learning-state update for Hebrew adaptive items."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from mindtune_clm.hebrew_slice.error_taxonomy import (
    is_context_error,
    is_morphology_error,
    is_pointing_error,
)
from mindtune_clm.hebrew_slice.models import (
    HebrewItemLearningState,
    HebrewResponse,
    HebrewScore,
)


def _summarize(values: list[float]) -> dict[str, float | int]:
    if not values:
        return {"mean": 0.0, "min": 0.0, "max": 0.0, "count": 0}
    return {
        "mean": round(sum(values) / len(values), 3),
        "min": round(min(values), 3),
        "max": round(max(values), 3),
        "count": len(values),
    }


def update_learning_state(
    state: HebrewItemLearningState,
    response: HebrewResponse,
    score: HebrewScore,
    semantic_time: float,
) -> HebrewItemLearningState:
    """Return an updated item-level learning state (immutable update)."""
    data = asdict(state)
    data["attempts"] += 1
    data["presentations"] += 1
    data["last_seen_semantic_time"] = semantic_time
    data["response_times_ms"].append(response.response_time_ms)
    data["confidence_values"].append(response.confidence)
    data["assistance_history"].append(response.audio_assistance_level)

    is_correct = score.overall == "correct"
    data["last_result"] = score.overall
    if is_correct:
        data["correct_count"] += 1
        data["consecutive_successes"] += 1
        data["consecutive_failures"] = 0
    else:
        data["incorrect_count"] += 1
        data["consecutive_failures"] += 1
        data["consecutive_successes"] = 0

    for code in score.error_codes:
        if is_morphology_error(code):
            data["morphology_errors"][code] = data["morphology_errors"].get(code, 0) + 1
        if is_pointing_error(code):
            data["pointing_errors"][code] = data["pointing_errors"].get(code, 0) + 1
        if is_context_error(code):
            data["morphology_errors"][code] = data["morphology_errors"].get(code, 0) + 1

    mastery = data["correct_count"] / max(1, data["attempts"])
    recent_weight = max(0.0, 1.0 - 0.1 * data["consecutive_failures"])
    data["current_mastery_estimate"] = round(mastery * recent_weight, 3)
    data["current_difficulty_estimate"] = max(
        0.0,
        min(1.0, data["current_difficulty_estimate"] + (0.05 if is_correct else -0.05)),
    )
    data["scheduled_review_position"] += 1
    data["active_learning_eligible"] = not data["reference_only"]

    return HebrewItemLearningState(**data)


def summarize_learning_state(state: HebrewItemLearningState) -> dict[str, Any]:
    """Return a JSON-serializable summary of an item learning state."""
    base = state.as_dict()
    base["response_time_summary"] = _summarize(state.response_times_ms)
    base["confidence_summary"] = _summarize([float(v) for v in state.confidence_values])
    return base
