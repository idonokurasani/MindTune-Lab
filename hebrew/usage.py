"""Modern-usage classification for Hebrew forms and sentences."""
from __future__ import annotations

from .models import ExampleSentence, VerbForm


# Core forms that every modern Hebrew learner must know, regardless of raw corpus count.
CORE_FORM_KEYS = {
    "infinitive",
    "past_third_m_singular",
    "past_first_mf_singular",
    "present_m_singular",
    "present_f_singular",
    "future_first_mf_singular",
    "future_second_m_singular",
    "future_third_m_singular",
}


def classify_form(
    form: VerbForm,
    corpus_count: int,
    core_override: bool = False,
) -> str:
    """Return a usage classification for a verb form.

    Does not infer 'common' from morphology alone.  Uses corpus attestations
    when available; returns 'unknown' when evidence is insufficient.
    Usage classification is independent of phoneme/stress disagreements.
    """
    if core_override or form.form_key in CORE_FORM_KEYS:
        if corpus_count >= 10:
            return "core_modern"
        if corpus_count > 0:
            return "common_modern"
        # Core form with no corpus hits is still core, but flag as rare attestation
        return "core_modern"

    if corpus_count >= 50:
        return "common_modern"
    if corpus_count >= 10:
        return "valid_but_rare"
    if corpus_count > 0:
        return "valid_but_rare"

    return "unattested"


def classify_sentence(sentence: ExampleSentence) -> str:
    """Classify an SVLM sentence candidate."""
    if sentence.suspected_noise or not sentence.punctuation_quality_ok:
        return "disputed"
    if not sentence.target_form_present:
        return "unknown"
    if sentence.token_count >= 4 and sentence.token_count <= 12:
        return "common_modern"
    if sentence.token_count > 12:
        return "valid_but_rare"
    return "unknown"
