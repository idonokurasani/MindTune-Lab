"""Pedagogical adaptation for Hebrew adaptive slice."""

from __future__ import annotations

from typing import Any

from mindtune_clm.hebrew_slice.error_taxonomy import (
    is_morphology_error,
    is_pointing_error,
)
from mindtune_clm.hebrew_slice.models import (
    HebrewAdaptiveItem,
    HebrewItemLearningState,
    HebrewPedagogicalDecision,
    HebrewScore,
)
from mindtune_clm.state import MantraControlState


class HebrewAdaptationPolicy:
    """Bounded pedagogical selector: learning state and CLM safety, no raw EEG."""

    def __init__(
        self,
        max_repeats: int = 3,
        interleave_interval: int = 3,
        min_mastery_for_advance: float = 0.5,
    ) -> None:
        self.max_repeats = max_repeats
        self.interleave_interval = interleave_interval
        self.min_mastery_for_advance = min_mastery_for_advance

    def decide(
        self,
        current_item: HebrewAdaptiveItem,
        score: HebrewScore,
        learning_state: HebrewItemLearningState,
        control_state: MantraControlState,
        recent_item_ids: list[str],
        trial_index: int,
    ) -> HebrewPedagogicalDecision:
        """Return the next bounded pedagogical action."""
        reasons: list[str] = []
        if control_state.assistance_level >= 0.8:
            reasons.append("clm_high_assistance_force_baseline")
            return HebrewPedagogicalDecision(
                action="force_baseline",
                next_item_id=current_item.item_id,
                next_trial_type="italian_to_hebrew",
                assistance_delta=-0.5,
                reason_codes=reasons,
                repeat_same_item=False,
            )

        if score.overall == "correct":
            reasons.append("correct")
            next_item_id = self._choose_next_item(
                current_item, learning_state, recent_item_ids, reasons
            )
            return HebrewPedagogicalDecision(
                action="continue",
                next_item_id=next_item_id,
                next_trial_type="italian_to_hebrew",
                assistance_delta=-0.1,
                reason_codes=reasons,
            )

        if score.overall == "correct_unpointed" or score.overall == "accepted_alternate":
            reasons.append("needs_pointing_support")
            return HebrewPedagogicalDecision(
                action="repeat_with_greater_assistance",
                next_item_id=current_item.item_id,
                next_trial_type="immediate_repetition",
                assistance_delta=0.1,
                reason_codes=reasons,
                repeat_same_item=True,
            )

        # Incorrect or invalid branch.
        reasons.append(f"incorrect:{score.overall}")
        if learning_state.consecutive_failures >= self.max_repeats:
            reasons.append("max_repeats_exceeded_interleave")
            next_id = self._pick_interleave(recent_item_ids, reasons)
            return HebrewPedagogicalDecision(
                action="interleave_another_item",
                next_item_id=next_id or current_item.item_id,
                next_trial_type="hebrew_recognition",
                assistance_delta=0.0,
                reason_codes=reasons,
                interleave_item_id=next_id,
            )

        if any(is_pointing_error(c) for c in score.error_codes):
            reasons.append("pointing_error")
            return HebrewPedagogicalDecision(
                action="show_isolated_form",
                next_item_id=current_item.item_id,
                next_trial_type="immediate_repetition",
                assistance_delta=0.15,
                reason_codes=reasons,
                repeat_same_item=True,
            )

        if any(is_morphology_error(c) for c in score.error_codes):
            reasons.append("morphology_error")
            return HebrewPedagogicalDecision(
                action="switch_recall_to_recognition",
                next_item_id=current_item.item_id,
                next_trial_type="hebrew_recognition",
                assistance_delta=0.2,
                reason_codes=reasons,
                repeat_same_item=True,
            )

        # Generic fallback.
        reasons.append("general_incorrect")
        return HebrewPedagogicalDecision(
            action="repeat_with_greater_assistance",
            next_item_id=current_item.item_id,
            next_trial_type="italian_to_hebrew",
            assistance_delta=0.1,
            reason_codes=reasons,
            repeat_same_item=True,
        )

    def _choose_next_item(
        self,
        current_item: HebrewAdaptiveItem,
        current_state: HebrewItemLearningState,
        recent_item_ids: list[str],
        reasons: list[str],
    ) -> str | None:
        """Stub for next-item selection; overridden by the session using a learner model."""
        reasons.append("next_item_selected_by_session")
        return current_item.item_id

    def _pick_interleave(self, recent_item_ids: list[str], reasons: list[str]) -> str | None:
        reasons.append("no_interleave_available")
        return recent_item_ids[0] if recent_item_ids else None

    def select_next_item(
        self,
        all_items: list[HebrewAdaptiveItem],
        learning_states: dict[str, HebrewItemLearningState],
        recent_item_ids: list[str],
        current_item_id: str,
    ) -> HebrewAdaptiveItem:
        """Choose the next eligible item with bounded interleaving."""
        eligible = [
            i for i in all_items
            if i.item_id != current_item_id and i.linguistic_validation_status in ("approved", "validated")
        ]
        if not eligible:
            eligible = [i for i in all_items if i.item_id == current_item_id] or all_items

        def sort_key(item: HebrewAdaptiveItem) -> tuple[float, int, float]:
            state = learning_states.get(item.item_id)
            if state is None:
                return (1.0, 0, 0.0)
            return (
                -state.current_mastery_estimate,
                state.consecutive_failures,
                state.last_seen_semantic_time or 0.0,
            )

        eligible.sort(key=sort_key)
        # Avoid the two most recent items if possible.
        for item in eligible:
            if item.item_id not in recent_item_ids[-2:]:
                return item
        return eligible[0]

    def stop_requested(
        self,
        learning_states: dict[str, HebrewItemLearningState],
        trial_index: int,
        max_trials: int,
    ) -> bool:
        """Return True when the session should stop gracefully."""
        if trial_index >= max_trials:
            return True
        all_mastered = all(
            s.current_mastery_estimate >= self.min_mastery_for_advance
            for s in learning_states.values()
        )
        return all_mastered and len(learning_states) > 0

    def as_dict(self) -> dict[str, Any]:
        return {
            "max_repeats": self.max_repeats,
            "interleave_interval": self.interleave_interval,
            "min_mastery_for_advance": self.min_mastery_for_advance,
        }
