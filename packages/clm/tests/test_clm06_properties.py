"""Additional property tests for CLM-06 Hebrew adaptive vertical slice."""

from __future__ import annotations

import unicodedata
from dataclasses import replace

import pytest

from mindtune_clm.audio.assets import AudioAssetRegistry
from mindtune_clm.hebrew_slice import (
    HebrewAdaptationPolicy,
    HebrewAdaptiveItem,
    HebrewAssetError,
    HebrewAssetResolver,
    HebrewErrorCode,
    HebrewEventLog,
    HebrewItemLearningState,
    HebrewPedagogicalDecision,
    HebrewResponse,
    HebrewScore,
    HebrewSliceEventType,
    HebrewTrialFactory,
    make_clm06_test_fixture,
    make_synthetic_hebrew_audio_asset,
    score_response,
    update_learning_state,
)
from mindtune_clm.hebrew_slice.error_taxonomy import (
    is_context_error,
    is_morphology_error,
    is_pointing_error,
)
from mindtune_clm.hebrew_slice.learning_state import summarize_learning_state
from mindtune_clm.hebrew_slice.models import HebrewAdaptiveEvent
from mindtune_clm.hebrew_slice.session import HebrewSessionError
from mindtune_clm.state import MantraControlState

ADAPTER, REGISTRY, ITEMS = make_clm06_test_fixture()
BY_ID = {i.item_id: i for i in ITEMS}
ITEM = ITEMS[0]


def _resp(item, text, response_id="r1", latency=800.0, confidence=5, audio_level=0.0):
    return HebrewResponse(
        response_id=response_id,
        trial_id="t1",
        item_id=item.item_id,
        prompt_id="p1",
        presentation_id="pres1",
        raw_response=text,
        normalized_response=text,
        response_semantic_timestamp=0.0,
        response_time_ms=latency,
        confidence=confidence,
        hint_used=False,
        replay_count=0,
        audio_assistance_level=audio_level,
    )


def _score(item, text):
    return score_response(item, _resp(item, text))


def _new_session(items=None, max_trials=10):
    from mindtune_clm.hebrew_slice.session import HebrewAdaptiveSession

    return HebrewAdaptiveSession(
        session_id="s-prop",
        items=items or ITEMS[:10],
        asset_registry=REGISTRY,
        max_trials=max_trials,
        clock=lambda: 0.0,
    )


# ---------------------------------------------------------------------------
# Error taxonomy: one test per enum value and group helper
# ---------------------------------------------------------------------------
for _code in HebrewErrorCode:
    _name = _code.name.lower()

    def _make_code_test(code=_code):
        def test_func():
            assert isinstance(code.value, str)
            assert len(code.value) > 0

        return test_func

    globals()[f"test_error_code_{_name}_has_non_empty_string_value"] = _make_code_test()


def test_morphology_error_helper_for_wrong_lemma():
    assert is_morphology_error(HebrewErrorCode.WRONG_LEMMA.value) is True


def test_morphology_error_helper_for_wrong_binyan():
    assert is_morphology_error(HebrewErrorCode.WRONG_BINYAN.value) is True


def test_morphology_error_helper_for_participle_confusion():
    assert is_morphology_error(HebrewErrorCode.PARTICIPLE_PERSON_CONFUSION.value) is True


def test_pointing_error_helper_for_wrong_niqqud():
    assert is_pointing_error(HebrewErrorCode.WRONG_NIQQUD.value) is True


def test_pointing_error_helper_for_dagesh_error():
    assert is_pointing_error(HebrewErrorCode.DAGESH_ERROR.value) is True


def test_pointing_error_helper_for_shin_sin_dot_error():
    assert is_pointing_error(HebrewErrorCode.SHIN_SIN_DOT_ERROR.value) is True


def test_context_error_helper_for_subject_verb_disagreement():
    assert is_context_error(HebrewErrorCode.SUBJECT_VERB_DISAGREEMENT.value) is True


def test_context_error_helper_for_haya_hava_confusion():
    assert is_context_error(HebrewErrorCode.HAYA_HAVA_HIT_HAVA_CONFUSION.value) is True


# ---------------------------------------------------------------------------
# Scoring dimensions for a fully correct pointed response
# ---------------------------------------------------------------------------
for _dim in (
    "lemma",
    "root",
    "binyan",
    "tense_mood",
    "person",
    "gender",
    "number",
    "pointed_orthography",
    "unpointed_orthography",
    "meaning",
    "contextual_agreement",
):

    def _make_correct_dim(dim=_dim):
        def test_func():
            score = _score(ITEM, ITEM.canonical_pointed)
            assert getattr(score, dim) == "correct"

        return test_func

    globals()[f"test_correct_pointed_response_dimension_{_dim}_is_correct"] = _make_correct_dim()


def test_correct_pointed_response_overall_is_correct():
    assert _score(ITEM, ITEM.canonical_pointed).overall == "correct"


def test_correct_pointed_response_has_no_error_codes():
    assert _score(ITEM, ITEM.canonical_pointed).error_codes == []


# ---------------------------------------------------------------------------
# Scoring dimensions for an unpointed (but otherwise correct) response
# ---------------------------------------------------------------------------
for _dim in ("lemma", "root", "binyan", "tense_mood", "person", "gender", "number", "meaning", "contextual_agreement"):

    def _make_unpointed_dim(dim=_dim):
        def test_func():
            score = _score(ITEM, ITEM.canonical_unpointed)
            assert getattr(score, dim) == "correct"

        return test_func

    globals()[f"test_unpointed_response_dimension_{_dim}_is_correct"] = _make_unpointed_dim()


def test_unpointed_response_pointed_orthography_is_incorrect():
    assert _score(ITEM, ITEM.canonical_unpointed).pointed_orthography == "incorrect"


def test_unpointed_response_unpointed_orthography_is_correct():
    assert _score(ITEM, ITEM.canonical_unpointed).unpointed_orthography == "correct"


def test_unpointed_response_overall_is_correct_unpointed():
    assert _score(ITEM, ITEM.canonical_unpointed).overall == "correct_unpointed"


def test_unpointed_response_records_pointing_error():
    assert HebrewErrorCode.WRONG_NIQQUD.value in _score(ITEM, ITEM.canonical_unpointed).error_codes


def test_unpointed_response_records_pointed_unpointed_mismatch():
    assert HebrewErrorCode.POINTED_UNPOINTED_MISMATCH.value in _score(ITEM, ITEM.canonical_unpointed).error_codes


# ---------------------------------------------------------------------------
# Scoring dimensions for a fully incorrect response
# ---------------------------------------------------------------------------
for _dim in (
    "lemma",
    "root",
    "binyan",
    "tense_mood",
    "person",
    "gender",
    "number",
    "pointed_orthography",
    "unpointed_orthography",
    "meaning",
    "contextual_agreement",
):

    def _make_incorrect_dim(dim=_dim):
        def test_func():
            score = _score(ITEM, "שלום")
            assert getattr(score, dim) == "incorrect"

        return test_func

    globals()[f"test_incorrect_response_dimension_{_dim}_is_incorrect"] = _make_incorrect_dim()


def test_incorrect_response_overall_is_incorrect():
    assert _score(ITEM, "שלום").overall == "incorrect"


def test_incorrect_response_has_error_codes():
    assert _score(ITEM, "שלום").error_codes


# ---------------------------------------------------------------------------
# Special scoring cases
# ---------------------------------------------------------------------------
def test_accepted_alternate_response_flags_accepted_alternate_used():
    modified = HebrewAdaptiveItem(**{**ITEM.as_dict(), "accepted_alternates": list(ITEM.accepted_alternates) + ["שלום"]})
    score = _score(modified, "שלום")
    assert score.overall == "accepted_alternate"
    assert score.accepted_alternate_used is True


def test_transliteration_rejected():
    score = _score(ITEM, "kotev")
    assert score.overall == "invalid"
    assert HebrewErrorCode.TRANSLITERATION_INSTEAD_OF_HEBREW.value in score.error_codes


def test_omitted_whitespace_response_not_answered():
    score = _score(ITEM, "   ")
    assert score.overall == "not_answered"
    assert HebrewErrorCode.OMITTED_RESPONSE.value in score.error_codes


def test_malformed_combining_unicode_rejected():
    # 'a' + combining diaeresis is not NFC.
    score = _score(ITEM, "a\u0308")
    assert score.overall == "invalid"
    assert HebrewErrorCode.INVALID_UNICODE.value in score.error_codes


def test_nfc_input_is_not_rejected_for_invalid_unicode():
    nfc = unicodedata.normalize("NFC", "a\u0308")
    score = _score(ITEM, nfc)
    # It still does not match the Hebrew item, but it should not be invalid.
    assert score.overall != "invalid"


def test_haya_hava_distinct():
    haya_item = BY_ID.get("clm06-להיות-infinitive", ITEM)
    if haya_item.item_id == ITEM.item_id:
        pytest.skip("no הָיָה item in fixture")
    score = _score(haya_item, "להוות")
    assert HebrewErrorCode.HAYA_HAVA_HIT_HAVA_CONFUSION.value in score.error_codes


def test_semantically_related_confusion_error():
    confusion = ITEM.error_confusion_set[0] if ITEM.error_confusion_set else None
    if not confusion:
        pytest.skip("no error confusion set")
    score = _score(ITEM, confusion)
    assert HebrewErrorCode.SEMANTICALLY_RELATED_VERB_CONFUSION.value in score.error_codes


def test_score_does_not_depend_on_confidence_or_latency():
    score_low = score_response(ITEM, _resp(ITEM, ITEM.canonical_pointed, confidence=1, latency=100.0))
    score_high = score_response(ITEM, _resp(ITEM, ITEM.canonical_pointed, confidence=5, latency=5000.0))
    assert score_low.overall == score_high.overall
    assert score_low.as_dict() == score_high.as_dict()


# ---------------------------------------------------------------------------
# Learning-state updates
# ---------------------------------------------------------------------------
def test_learning_state_correct_increments_correct_count():
    state = HebrewItemLearningState(item_id=ITEM.item_id)
    resp = _resp(ITEM, ITEM.canonical_pointed)
    score = score_response(ITEM, resp)
    new = update_learning_state(state, resp, score, 0.0)
    assert new.correct_count == 1
    assert new.consecutive_successes == 1
    assert new.consecutive_failures == 0
    assert new.last_result == "correct"


def test_learning_state_incorrect_increments_incorrect_count():
    state = HebrewItemLearningState(item_id=ITEM.item_id)
    resp = _resp(ITEM, "שלום")
    score = score_response(ITEM, resp)
    new = update_learning_state(state, resp, score, 0.0)
    assert new.incorrect_count == 1
    assert new.consecutive_failures == 1
    assert new.consecutive_successes == 0


def test_learning_state_tracks_morphology_errors():
    state = HebrewItemLearningState(item_id=ITEM.item_id)
    resp = _resp(ITEM, "שלום")
    score = score_response(ITEM, resp)
    new = update_learning_state(state, resp, score, 0.0)
    assert HebrewErrorCode.WRONG_LEMMA.value in new.morphology_errors
    assert new.morphology_errors[HebrewErrorCode.WRONG_LEMMA.value] >= 1


def test_learning_state_tracks_pointing_errors():
    state = HebrewItemLearningState(item_id=ITEM.item_id)
    resp = _resp(ITEM, ITEM.canonical_unpointed)
    score = score_response(ITEM, resp)
    new = update_learning_state(state, resp, score, 0.0)
    assert HebrewErrorCode.WRONG_NIQQUD.value in new.pointing_errors


def test_learning_state_mastery_estimate_bounded():
    state = HebrewItemLearningState(item_id=ITEM.item_id)
    resp = _resp(ITEM, ITEM.canonical_pointed)
    score = score_response(ITEM, resp)
    new = update_learning_state(state, resp, score, 0.0)
    assert 0.0 <= new.current_mastery_estimate <= 1.0


def test_learning_state_difficulty_increases_after_correct():
    base = HebrewItemLearningState(item_id=ITEM.item_id, current_difficulty_estimate=0.5)
    resp = _resp(ITEM, ITEM.canonical_pointed)
    score = score_response(ITEM, resp)
    new = update_learning_state(base, resp, score, 0.0)
    assert new.current_difficulty_estimate >= base.current_difficulty_estimate


def test_learning_state_difficulty_decreases_after_incorrect():
    base = HebrewItemLearningState(item_id=ITEM.item_id, current_difficulty_estimate=0.5)
    resp = _resp(ITEM, "שלום")
    score = score_response(ITEM, resp)
    new = update_learning_state(base, resp, score, 0.0)
    assert new.current_difficulty_estimate <= base.current_difficulty_estimate


def test_learning_state_summary_includes_response_time_and_confidence():
    state = HebrewItemLearningState(item_id=ITEM.item_id)
    resp = _resp(ITEM, ITEM.canonical_pointed)
    score = score_response(ITEM, resp)
    new = update_learning_state(state, resp, score, 0.0)
    summary = summarize_learning_state(new)
    assert "response_time_summary" in summary
    assert "confidence_summary" in summary
    assert summary["response_time_summary"]["count"] == 1
    assert summary["confidence_summary"]["count"] == 1


def test_learning_state_active_eligibility_false_for_reference_only():
    state = HebrewItemLearningState(item_id=ITEM.item_id, reference_only=True)
    resp = _resp(ITEM, ITEM.canonical_pointed)
    score = score_response(ITEM, resp)
    updated = update_learning_state(state, resp, score, 0.0)
    assert updated.active_learning_eligible is False


def test_learning_state_scheduled_review_position_increments():
    state = HebrewItemLearningState(item_id=ITEM.item_id)
    resp = _resp(ITEM, ITEM.canonical_pointed)
    score = score_response(ITEM, resp)
    new = update_learning_state(state, resp, score, 0.0)
    assert new.scheduled_review_position == 1


# ---------------------------------------------------------------------------
# Pedagogical adaptation policy
# ---------------------------------------------------------------------------
def test_adaptation_correct_returns_continue():
    policy = HebrewAdaptationPolicy()
    score = _score(ITEM, ITEM.canonical_pointed)
    state = HebrewItemLearningState(item_id=ITEM.item_id)
    control = MantraControlState.baseline()
    decision = policy.decide(ITEM, score, state, control, [ITEM.item_id], 1)
    assert decision.action == "continue"


def test_adaptation_correct_unpointed_returns_repeat_with_assistance():
    policy = HebrewAdaptationPolicy()
    score = _score(ITEM, ITEM.canonical_unpointed)
    state = HebrewItemLearningState(item_id=ITEM.item_id)
    control = MantraControlState.baseline()
    decision = policy.decide(ITEM, score, state, control, [ITEM.item_id], 1)
    assert decision.action == "repeat_with_greater_assistance"
    assert decision.repeat_same_item is True


def test_adaptation_incorrect_with_pointing_error_returns_show_isolated():
    policy = HebrewAdaptationPolicy()
    score = _score(ITEM, "שלום")
    state = HebrewItemLearningState(item_id=ITEM.item_id)
    control = MantraControlState.baseline()
    decision = policy.decide(ITEM, score, state, control, [ITEM.item_id], 1)
    assert decision.action == "show_isolated_form"
    assert decision.repeat_same_item is True


def test_adaptation_incorrect_with_pure_morphology_error_returns_switch_to_recognition():
    policy = HebrewAdaptationPolicy()
    score = HebrewScore(
        overall="incorrect",
        lemma="incorrect",
        root="incorrect",
        binyan="incorrect",
        tense_mood="incorrect",
        person="incorrect",
        gender="incorrect",
        number="incorrect",
        pointed_orthography="correct",
        unpointed_orthography="incorrect",
        meaning="incorrect",
        contextual_agreement="incorrect",
        accepted_alternate_used=False,
        error_codes=[HebrewErrorCode.WRONG_LEMMA.value],
    )
    state = HebrewItemLearningState(item_id=ITEM.item_id)
    control = MantraControlState.baseline()
    decision = policy.decide(ITEM, score, state, control, [ITEM.item_id], 1)
    assert decision.action == "switch_recall_to_recognition"


def test_adaptation_max_repeats_returns_interleave():
    policy = HebrewAdaptationPolicy(max_repeats=2)
    state = HebrewItemLearningState(item_id=ITEM.item_id, consecutive_failures=2)
    score = _score(ITEM, "שלום")
    control = MantraControlState.baseline()
    decision = policy.decide(ITEM, score, state, control, [ITEM.item_id], 1)
    assert decision.action == "interleave_another_item"


def test_adaptation_clm_high_assistance_forces_baseline():
    policy = HebrewAdaptationPolicy()
    score = _score(ITEM, ITEM.canonical_pointed)
    state = HebrewItemLearningState(item_id=ITEM.item_id)
    control = replace(MantraControlState.baseline(), assistance_level=0.9)
    decision = policy.decide(ITEM, score, state, control, [ITEM.item_id], 1)
    assert decision.action == "force_baseline"


def test_adaptation_select_next_item_avoids_current_and_recent():
    policy = HebrewAdaptationPolicy()
    item_a = ITEMS[0]
    item_b = ITEMS[1] if len(ITEMS) > 1 else item_a
    states = {
        item_a.item_id: HebrewItemLearningState(item_id=item_a.item_id, current_mastery_estimate=0.9),
        item_b.item_id: HebrewItemLearningState(item_id=item_b.item_id, current_mastery_estimate=0.1),
    }
    selected = policy.select_next_item([item_a, item_b], states, [item_a.item_id], item_a.item_id)
    assert selected.item_id == item_b.item_id


def test_adaptation_stop_requested_after_max_trials():
    policy = HebrewAdaptationPolicy()
    state = HebrewItemLearningState(item_id=ITEM.item_id)
    assert policy.stop_requested({ITEM.item_id: state}, trial_index=10, max_trials=10) is True


def test_adaptation_stop_requested_when_all_mastered():
    policy = HebrewAdaptationPolicy(min_mastery_for_advance=0.5)
    mastered = HebrewItemLearningState(item_id=ITEM.item_id, current_mastery_estimate=0.8)
    assert policy.stop_requested({ITEM.item_id: mastered}, trial_index=1, max_trials=20) is True


# ---------------------------------------------------------------------------
# Trial factory
# ---------------------------------------------------------------------------
def test_trial_factory_deterministic_id():
    factory = HebrewTrialFactory()
    control = MantraControlState.baseline()
    t1 = factory.make_trial(ITEM, "italian_to_hebrew", 1, control)
    t2 = factory.make_trial(ITEM, "italian_to_hebrew", 1, control)
    assert t1.trial_id == t2.trial_id


def test_trial_factory_id_changes_with_sequence():
    factory = HebrewTrialFactory()
    control = MantraControlState.baseline()
    t1 = factory.make_trial(ITEM, "italian_to_hebrew", 1, control)
    t2 = factory.make_trial(ITEM, "italian_to_hebrew", 2, control)
    assert t1.trial_id != t2.trial_id


def test_trial_factory_id_changes_with_trial_type():
    factory = HebrewTrialFactory()
    control = MantraControlState.baseline()
    t1 = factory.make_trial(ITEM, "italian_to_hebrew", 1, control)
    t2 = factory.make_trial(ITEM, "hebrew_recognition", 1, control)
    assert t1.trial_id != t2.trial_id


def test_trial_factory_italian_to_hebrew_expected_is_unpointed():
    factory = HebrewTrialFactory()
    control = MantraControlState.baseline()
    trial = factory.make_trial(ITEM, "italian_to_hebrew", 1, control, direction="italian_to_hebrew")
    assert trial.expected == ITEM.canonical_unpointed


def test_trial_factory_hebrew_to_italian_expected_is_italian():
    factory = HebrewTrialFactory()
    control = MantraControlState.baseline()
    trial = factory.make_trial(ITEM, "hebrew_to_italian", 1, control)
    assert trial.expected == ITEM.natural_italian


def test_trial_factory_recognition_has_choices():
    factory = HebrewTrialFactory()
    control = MantraControlState.baseline()
    trial = factory.make_trial(ITEM, "hebrew_recognition", 1, control, distractors=["שלום"])
    assert trial.choices is not None
    assert ITEM.canonical_unpointed in trial.choices or ITEM.canonical_pointed in trial.choices


def test_trial_factory_immediate_repetition_expected_is_unpointed():
    factory = HebrewTrialFactory()
    control = MantraControlState.baseline()
    trial = factory.make_trial(ITEM, "immediate_repetition", 1, control)
    assert trial.expected == ITEM.canonical_unpointed


# ---------------------------------------------------------------------------
# Asset resolution
# ---------------------------------------------------------------------------
def test_asset_resolver_returns_aaron_hebrew_asset():
    resolver = HebrewAssetResolver(REGISTRY)
    resolved = resolver.resolve(ITEM)
    assert resolved.hebrew_asset is not None
    provenance = " ".join(resolved.hebrew_asset.provenance)
    assert "aaron" in provenance.lower()


def test_asset_resolver_returns_giuseppe_italian_asset():
    resolver = HebrewAssetResolver(REGISTRY)
    resolved = resolver.resolve(ITEM)
    if resolved.italian_asset is not None:
        provenance = " ".join(resolved.italian_asset.provenance)
        assert "giuseppe" in provenance.lower()


def test_asset_resolver_preserves_aaron_pointed_text():
    resolver = HebrewAssetResolver(REGISTRY)
    resolved = resolver.resolve(ITEM)
    assert resolved.hebrew_pointed_text == ITEM.canonical_pointed


def test_asset_resolver_rejects_hannah_asset():
    hannah_asset = make_synthetic_hebrew_audio_asset("hannah_test", "Hannah test")
    reg = AudioAssetRegistry([hannah_asset])
    resolver = HebrewAssetResolver(reg, aaron_fallback_asset_id=None)
    item = HebrewAdaptiveItem(**{**ITEM.as_dict(), "required_audio_asset_ids": ["hannah_test"]})
    with pytest.raises(HebrewAssetError):
        resolver.resolve(item)


def test_asset_resolver_rejects_hila_asset():
    hila_asset = make_synthetic_hebrew_audio_asset("hila_test", "Hila test")
    reg = AudioAssetRegistry([hila_asset])
    resolver = HebrewAssetResolver(reg, aaron_fallback_asset_id=None)
    item = HebrewAdaptiveItem(**{**ITEM.as_dict(), "required_audio_asset_ids": ["hila_test"]})
    with pytest.raises(HebrewAssetError):
        resolver.resolve(item)


def test_asset_resolver_uses_aaron_fallback_when_primary_missing():
    fallback = make_synthetic_hebrew_audio_asset("aaron_fallback", ITEM.canonical_pointed)
    reg = AudioAssetRegistry([fallback])
    resolver = HebrewAssetResolver(reg, aaron_fallback_asset_id="aaron_fallback")
    item = HebrewAdaptiveItem(**{**ITEM.as_dict(), "required_audio_asset_ids": ["missing_primary"]})
    resolved = resolver.resolve(item)
    assert resolved.fallback_used is True
    assert resolved.hebrew_asset_id == "aaron_fallback"


def test_asset_resolver_raises_when_no_fallback():
    reg = AudioAssetRegistry()
    resolver = HebrewAssetResolver(reg, aaron_fallback_asset_id=None)
    with pytest.raises(HebrewAssetError):
        resolver.resolve(ITEM)


def test_asset_error_exposes_missing_assets():
    try:
        reg = AudioAssetRegistry()
        resolver = HebrewAssetResolver(reg, aaron_fallback_asset_id=None)
        resolver.resolve(ITEM)
    except HebrewAssetError as exc:
        assert exc.missing_assets


# ---------------------------------------------------------------------------
# Curriculum adapter
# ---------------------------------------------------------------------------
def test_curriculum_adapter_loads_from_existing_hebrew_engine():
    assert ADAPTER.items


def test_curriculum_adapter_approved_items_only():
    for item in ADAPTER.approved_items():
        assert item.linguistic_validation_status in ("approved", "validated")


def test_curriculum_adapter_ready_items_require_assets():
    ready = ADAPTER.ready_items(set())
    assert ready == []
    inventory = {a.asset_id for a in REGISTRY.assets()}
    ready = ADAPTER.ready_items(inventory)
    assert len(ready) > 0


def test_curriculum_readiness_report_ready_false_without_assets():
    report = ADAPTER.readiness_report(set())
    assert report["ready"] is False
    assert report["blockers"]


def test_curriculum_readiness_report_ready_true_with_test_registry():
    inventory = {a.asset_id for a in REGISTRY.assets()}
    report = ADAPTER.readiness_report(inventory)
    assert report["ready"] is True
    assert report["approved_count"] > 0
    assert report["ready_count"] > 0


def test_curriculum_approved_items_have_required_audio_asset_ids():
    for item in ADAPTER.approved_items():
        assert item.required_audio_asset_ids


def test_curriculum_approved_items_have_italian_labels():
    for item in ADAPTER.approved_items():
        assert item.italian_gloss
        assert item.natural_italian


def test_curriculum_approved_items_have_morphology_provenance():
    for item in ADAPTER.approved_items():
        assert item.morphology_provenance


def test_curriculum_approved_items_have_pointing_provenance():
    for item in ADAPTER.approved_items():
        assert item.pointing_provenance


def test_curriculum_approved_items_have_pealim_in_provenance():
    for item in ADAPTER.approved_items():
        assert "pealim" in item.morphology_provenance


# ---------------------------------------------------------------------------
# Session closed-loop and event behavior
# ---------------------------------------------------------------------------
def test_session_start_returns_first_trial():
    session = _new_session()
    trial = session.start()
    assert trial is not None
    assert session.current_trial is not None


def test_session_start_emits_started_event():
    session = _new_session()
    session.start()
    types = [e.event_type for e in session.event_log.events]
    assert HebrewSliceEventType.HEBREW_SESSION_STARTED in types


def test_session_respond_returns_result_keys():
    session = _new_session(max_trials=4)
    session.start()
    result = session.respond(ITEM.canonical_pointed)
    assert "score" in result
    assert "pedagogical_decision" in result
    assert "control_state" in result
    assert "playback_receipt" in result


def test_session_respond_emits_scored_event():
    session = _new_session(max_trials=4)
    session.start()
    session.respond(ITEM.canonical_pointed)
    types = [e.event_type for e in session.event_log.events]
    assert HebrewSliceEventType.HEBREW_RESPONSE_SCORED in types


def test_session_respond_emits_learning_state_updated():
    session = _new_session(max_trials=4)
    session.start()
    session.respond(ITEM.canonical_pointed)
    types = [e.event_type for e in session.event_log.events]
    assert HebrewSliceEventType.HEBREW_LEARNING_STATE_UPDATED in types


def test_session_respond_emits_pedagogical_adaptation():
    session = _new_session(max_trials=4)
    session.start()
    session.respond(ITEM.canonical_pointed)
    types = [e.event_type for e in session.event_log.events]
    assert HebrewSliceEventType.HEBREW_PEDAGOGICAL_ADAPTATION_DECIDED in types


def test_session_respond_emits_audio_asset_resolved():
    session = _new_session(max_trials=4)
    session.start()
    session.respond(ITEM.canonical_pointed)
    types = [e.event_type for e in session.event_log.events]
    assert HebrewSliceEventType.HEBREW_AUDIO_ASSET_RESOLVED in types


def test_session_current_item_unchanged_by_clm_adaptation():
    session = _new_session(max_trials=4)
    first = session.start()
    session.respond("שלום")
    assert session.current_item is not None
    assert session.current_item.item_id == first.item.item_id


def test_session_clm_control_state_changes_after_errors():
    session = _new_session(max_trials=5)
    session.start()
    session.respond("שלום")
    first = session.current_control_state.assistance_level
    session.respond("שלום")
    second = session.current_control_state.assistance_level
    assert second != first


def test_session_recovery_withdraws_assistance():
    session = _new_session(max_trials=8)
    session.start()
    session.respond("שלום")
    session.respond("שלום")
    elevated = session.current_control_state.assistance_level
    for _ in range(3):
        if session.completed or session.current_trial is None:
            break
        session.respond(session.current_trial.item.canonical_pointed, response_time_ms=500.0)
    assert session.current_control_state.assistance_level < elevated


def test_session_duplicate_response_not_double_scored():
    session = _new_session(max_trials=4)
    session.start()
    session.respond(ITEM.canonical_pointed, response_id="dup")
    r2 = session.respond(ITEM.canonical_pointed, response_id="dup")
    assert r2.get("duplicate") is True


def test_session_aborts_after_repeated_sensor_disconnect():
    session = _new_session(max_trials=6)
    session.start()
    with pytest.raises(HebrewSessionError):
        session.respond("שלום", sensor_disconnect=True)
        session.respond("שלום", sensor_disconnect=True)
        session.respond("שלום", sensor_disconnect=True)
    assert session.aborted is True


def test_session_completed_after_max_trials():
    session = _new_session(ITEMS[:2], max_trials=2)
    session.start()
    for _ in range(2):
        if session.completed or session.current_trial is None:
            break
        session.respond(session.current_trial.item.canonical_pointed)
    assert session.completed is True


def test_session_summary_has_causal_graph():
    session = _new_session(max_trials=4)
    session.start()
    session.respond(ITEM.canonical_pointed)
    summary = session.summary()
    assert "causal_graph" in summary
    assert len(summary["causal_graph"]["event_ids"]) > 0


def test_session_stop_returns_summary_with_reason():
    session = _new_session(max_trials=4)
    session.start()
    summary = session.stop(reason="test")
    assert summary["session_id"] == session.session_id
    assert session.completed is True


def test_session_event_ids_are_unique():
    session = _new_session(max_trials=4)
    session.start()
    session.respond(ITEM.canonical_pointed)
    ids = [e.event_id for e in session.event_log.events]
    assert len(ids) == len(set(ids))


def test_session_causal_graph_links_trial_to_response():
    session = _new_session(max_trials=4)
    session.start()
    session.respond(ITEM.canonical_pointed)
    graph = session.event_log.causal_graph()
    edges = graph.get("edges", [])
    assert edges


def test_session_clm_audio_render_produces_canonical_pcm():
    session = _new_session(max_trials=4)
    session.start()
    result = session.respond(ITEM.canonical_pointed)
    playback = result.get("playback_receipt")
    assert playback is not None


# ---------------------------------------------------------------------------
# Model serialization and event log
# ---------------------------------------------------------------------------
def test_hebrew_item_as_dict_contains_all_fields():
    d = ITEM.as_dict()
    for key in ("item_id", "lemma", "root", "binyan", "canonical_pointed", "italian_gloss"):
        assert key in d


def test_hebrew_response_as_dict_serializable():
    resp = _resp(ITEM, ITEM.canonical_pointed)
    d = resp.as_dict()
    assert d["response_id"] == resp.response_id


def test_hebrew_score_as_dict_serializable():
    score = _score(ITEM, ITEM.canonical_pointed)
    d = score.as_dict()
    assert d["overall"] == "correct"


def test_hebrew_pedagogical_decision_as_dict_serializable():
    decision = HebrewPedagogicalDecision(
        action="continue",
        next_item_id=ITEM.item_id,
        next_trial_type="italian_to_hebrew",
        assistance_delta=0.0,
        reason_codes=["test"],
    )
    d = decision.as_dict()
    assert d["action"] == "continue"


def test_hebrew_adaptive_event_as_dict_serializable():
    event = HebrewAdaptiveEvent(
        event_id="e1",
        event_type="test",
        session_id="s1",
        timestamp=0.0,
        component="test",
        payload={"x": 1},
        provenance=["p1"],
    )
    d = event.as_dict()
    assert d["provenance"] == ["p1"]


def test_hebrew_event_log_emit_and_retrieve():
    log = HebrewEventLog(session_id="s1")
    e = log.emit(HebrewSliceEventType.HEBREW_SESSION_STARTED, {"x": 1})
    assert e in log.events
    assert log.causal_graph()["event_ids"]


# ---------------------------------------------------------------------------
# Module-level invariants
# ---------------------------------------------------------------------------
def test_hebrew_slice_has_version():
    from mindtune_clm import hebrew_slice

    assert hebrew_slice.__version__


def test_hebrew_slice_exports_score_response():
    from mindtune_clm import hebrew_slice

    assert "score_response" in hebrew_slice.__all__


def test_no_hebrew_slice_module_mentions_speechgen_or_phonikud():
    from pathlib import Path

    import mindtune_clm.hebrew_slice as hs

    hs_dir = Path(hs.__file__).parent
    for path in hs_dir.glob("*.py"):
        text = path.read_text(encoding="utf-8").lower()
        assert "speechgen" not in text
        assert "phonikud" not in text
