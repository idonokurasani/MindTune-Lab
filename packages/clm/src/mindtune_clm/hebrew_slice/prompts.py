"""Hebrew adaptive trial prompts and cue builders."""

from __future__ import annotations

from mindtune_clm.hebrew_slice.models import HebrewAdaptiveItem, HebrewTrial

TRIAL_PROMPT_TEMPLATES = {
    "hebrew_to_italian": "What does this Hebrew word mean?",
    "italian_to_hebrew": "Type the Hebrew form for: {italian}",
    "hebrew_recognition": "Select the correct Hebrew word for: {italian}",
    "morphological_decomposition": "Break this Hebrew form into its grammatical parts.",
    "context_completion": "Complete the Hebrew sentence with the correct word form.",
    "immediate_repetition": "Repeat or type the Hebrew form you just heard.",
}


def build_prompt(item: HebrewAdaptiveItem, trial_type: str, direction: str = "italian_to_hebrew") -> str:
    """Return the user-facing prompt text for a trial."""
    template = TRIAL_PROMPT_TEMPLATES.get(trial_type, TRIAL_PROMPT_TEMPLATES["italian_to_hebrew"])
    if "{italian}" in template:
        return template.format(italian=item.natural_italian)
    return template


def build_choices(item: HebrewAdaptiveItem, trial_type: str, distractors: list[str]) -> tuple[str, ...]:
    """Build controlled-choice options for recognition trials."""
    choices = [item.canonical_unpointed] + list(distractors)
    return tuple(sorted(set(choices)))


def trial_to_prompt_payload(trial: HebrewTrial) -> dict[str, object]:
    """Return a serializable prompt payload for the console / API."""
    return {
        "prompt_id": trial.prompt_id,
        "presentation_id": trial.presentation_id,
        "trial_id": trial.trial_id,
        "trial_type": trial.trial_type,
        "direction": trial.direction,
        "prompt_text": trial.prompt_text,
        "pointed_hebrew": trial.item.canonical_pointed,
        "unpointed_hebrew": trial.item.canonical_unpointed,
        "italian_meaning": trial.item.natural_italian,
        "choices": list(trial.choices) if trial.choices is not None else None,
    }
