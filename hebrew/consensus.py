"""Form consensus across source evidence and overrides."""

from __future__ import annotations

from typing import Any

from .models import ConsensusInfo, SourceDisagreement, VerbForm


def _surface_plain_key(form: VerbForm) -> str:
    return form.surface_vocalized


def build_consensus(
    forms: dict[str, VerbForm],
    override_source: str = "manual_override",
) -> tuple[VerbForm, list[SourceDisagreement]]:
    """Build a consensus form from source-specific forms.

    `forms` maps source_id -> VerbForm.
    Approved local overrides are authoritative but disagreements are preserved.
    """
    disagreements: list[SourceDisagreement] = []

    # Plain form consensus first; used to downgrade vocalized variants.
    plain_values = {sid: f.surface_plain for sid, f in forms.items() if f.surface_plain}
    canonical_plain = _resolve_value(plain_values, override_source)
    if len(set(plain_values.values())) > 1:
        disagreements.append(
            SourceDisagreement(field_name="surface_plain", values=plain_values, severity="major")
        )

    # Surface vocalized consensus
    surface_values = {sid: f.surface_vocalized for sid, f in forms.items() if f.surface_vocalized}
    canonical_surface = _resolve_value(surface_values, override_source)
    if len(set(surface_values.values())) > 1:
        # If the plain forms agree, the vocalized difference is an orthographic variant.
        plain_agree = len(set(plain_values.values())) <= 1
        disagreements.append(
            SourceDisagreement(
                field_name="surface_vocalized",
                values=surface_values,
                severity="minor" if plain_agree else "major",
            )
        )

    # Stress consensus
    stress_values = {sid: f.lexical_stress for sid, f in forms.items() if f.lexical_stress}
    canonical_stress = _resolve_int(stress_values, override_source)
    if len(set(stress_values.values())) > 1:
        disagreements.append(
            SourceDisagreement(field_name="lexical_stress", values=stress_values, severity="major")
        )

    # Corrected phonemes consensus
    phoneme_values = {sid: f.phonemes_corrected for sid, f in forms.items() if f.phonemes_corrected}
    canonical_phonemes = _resolve_value(phoneme_values, override_source)
    if len(set(phoneme_values.values())) > 1:
        disagreements.append(
            SourceDisagreement(
                field_name="phonemes_corrected", values=phoneme_values, severity="major"
            )
        )

    # Shva consensus
    shva_values = {
        sid: f.shva.shva_status
        for sid, f in forms.items()
        if f.shva.shva_status not in ("", "not_applicable")
    }
    canonical_shva = _resolve_value(shva_values, override_source) if shva_values else "ambiguous"
    if len(set(shva_values.values())) > 1:
        disagreements.append(
            SourceDisagreement(field_name="shva_status", values=shva_values, severity="minor")
        )

    # Pick base morphology from most trusted source (override > pealim > others)
    preferred_source = _preferred_source(forms, override_source)
    base_form = forms[preferred_source]

    # Aggregate source evidence from all contributing forms
    aggregated_evidence = []
    for sid, f in forms.items():
        aggregated_evidence.extend(f.source_evidence)

    # Shva: if sources disagree, keep the base form but mark ambiguous
    shva = base_form.shva
    if len(set(shva_values.values())) > 1:
        from .models import ShvaDiagnosis

        shva = ShvaDiagnosis(
            shva_status="ambiguous",
            shva_source="consensus",
            shva_confidence=1.0,
            shva_reason="sources disagree on shva classification",
        )

    consensus = VerbForm(
        form_key=base_form.form_key,
        lemma_vocalized=base_form.lemma_vocalized,
        lemma_plain=base_form.lemma_plain,
        surface_vocalized=canonical_surface,
        surface_plain=canonical_plain,
        root=base_form.root,
        binyan=base_form.binyan,
        tense=base_form.tense,
        mood=base_form.mood,
        person=base_form.person,
        gender=base_form.gender,
        number=base_form.number,
        phonemes_corrected=canonical_phonemes,
        lexical_stress=canonical_stress,
        shva=shva,
        preferred_pronunciation=canonical_phonemes,
        source_evidence=aggregated_evidence,
    )
    consensus.consensus = ConsensusInfo(
        canonical_vocalized=canonical_surface,
        canonical_plain=canonical_plain,
        agreement_count=len(forms) - len(disagreements),
        disagreement_count=len(disagreements),
        source_forms={sid: f.surface_vocalized for sid, f in forms.items()},
        confidence=_confidence(len(forms), len(disagreements)),
    )
    consensus.unresolved_conflicts = disagreements
    return consensus, disagreements


def _resolve_value(values: dict[str, Any], override_source: str) -> Any:
    if not values:
        return ""
    if override_source in values:
        return values[override_source]
    for source in ("pealim", "eran_tomer", "verb_inflector"):
        if source in values:
            return values[source]
    return list(values.values())[0]


def _resolve_int(values: dict[str, int], override_source: str) -> int:
    if not values:
        return 0
    if override_source in values:
        return int(values[override_source])
    for source in ("pealim", "eran_tomer", "verb_inflector"):
        if source in values:
            return int(values[source])
    return int(list(values.values())[0])


def _preferred_source(forms: dict[str, VerbForm], override_source: str) -> str:
    if override_source in forms:
        return override_source
    for source in ("pealim", "eran_tomer", "verb_inflector"):
        if source in forms:
            return source
    return next(iter(forms))


def _confidence(total: int, disagreements: int) -> float:
    if total == 0:
        return 0.0
    return max(0.0, (total - disagreements) / total)
