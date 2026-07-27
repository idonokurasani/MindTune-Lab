"""Deterministic Hebrew adaptive trial factory."""

from __future__ import annotations

import hashlib
from dataclasses import asdict
from typing import Any

from mindtune_clm.hebrew_slice.models import HebrewAdaptiveItem, HebrewTrial
from mindtune_clm.hebrew_slice.prompts import build_choices, build_prompt
from mindtune_clm.state import MantraControlState


def _deterministic_id(seed: str) -> str:
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:24]


def _control_snapshot(control_state: MantraControlState) -> dict[str, Any]:
    return asdict(control_state)


class HebrewTrialFactory:
    """Build deterministic, typed Hebrew adaptive trials."""

    def __init__(self, curriculum_version: str = "clm06-hebrew-v1") -> None:
        self.curriculum_version = curriculum_version

    def make_trial(
        self,
        item: HebrewAdaptiveItem,
        trial_type: str,
        sequence: int,
        control_state: MantraControlState,
        *,
        direction: str | None = None,
        distractors: list[str] | None = None,
    ) -> HebrewTrial:
        """Return a prepared trial for the given item and type."""
        direction = direction or _default_direction(trial_type)
        prompt_text = build_prompt(item, trial_type, direction)
        seed = f"{self.curriculum_version}-{item.item_id}-{trial_type}-{direction}-{sequence}"
        trial_id = f"clm06-trial-{_deterministic_id(seed)}"
        prompt_id = f"clm06-prompt-{_deterministic_id(seed + '-prompt')}"
        presentation_id = f"clm06-pres-{_deterministic_id(seed + '-presentation')}"

        expected = _expected_answer(item, trial_type, direction)
        choices: tuple[str, ...] | None = None
        if "recognition" in trial_type or trial_type == "hebrew_recognition":
            choices = build_choices(item, trial_type, distractors or [])

        return HebrewTrial(
            trial_id=trial_id,
            presentation_id=presentation_id,
            prompt_id=prompt_id,
            item=item,
            trial_type=trial_type,
            direction=direction,
            prompt_text=prompt_text,
            choices=choices,
            expected=expected,
            control_state_id=control_state.control_state_id,
            control_state_snapshot=_control_snapshot(control_state),
            metadata={
                "sequence": sequence,
                "curriculum_version": self.curriculum_version,
                "item_source_id": item.source_id,
            },
        )


def _default_direction(trial_type: str) -> str:
    return "italian_to_hebrew" if "recall" in trial_type or "repetition" in trial_type else "hebrew_to_italian"


def _expected_answer(item: HebrewAdaptiveItem, trial_type: str, direction: str) -> str:
    if direction == "italian_to_hebrew":
        return item.canonical_unpointed
    if trial_type == "immediate_repetition":
        return item.canonical_unpointed
    return item.natural_italian
