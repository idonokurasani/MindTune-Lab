"""Production pipeline for a single Hebrew mantra package."""
from __future__ import annotations

from collections import OrderedDict
from pathlib import Path
from typing import Any

import phonikud

from .models import Conjugations, CorrectionEntry, MantraForm, MantraMetadata, MantraPackage
from .phonikud_adapter import phonemize
from .piper_adapter import PiperVoice, render_mantra_mp3
from .stress_override import OverrideRegistry
from .utils import (
    load_json,
    save_json,
    standard_unvocalized,
    transliteration_from_html,
)

APP = Path(__file__).resolve().parents[1]
DATA_DIR = APP / "data" / "mantra"
PEALIM_FILE = APP / "data" / "phonikud_eval" / "pealim_forms.json"
AUDIT_FILE = APP / "data" / "phonikud_eval" / "phonikud_evaluation.json"
PIPER_MODEL = APP / "data" / "phonikud_models" / "shaul.onnx"
PIPER_CONFIG = APP / "data" / "phonikud_models" / "shaul.config.json"

FORM_LAYOUT = OrderedDict(
    [
        (
            "present",
            [
                ("present_masculine_singular", "masculine_singular"),
                ("present_feminine_singular", "feminine_singular"),
                ("present_masculine_plural", "masculine_plural"),
                ("present_feminine_plural", "feminine_plural"),
            ],
        ),
        (
            "past",
            [
                ("past_1_singular", "אני"),
                ("past_2_masculine_singular", "אתה"),
                ("past_2_feminine_singular", "את"),
                ("past_3_masculine_singular", "הוא"),
                ("past_3_feminine_singular", "היא"),
                ("past_1_plural", "אנחנו"),
                ("past_2_masculine_plural", "אתם"),
                ("past_2_feminine_plural", "אתן"),
                ("past_3_plural", "הם/הן"),
            ],
        ),
        (
            "future",
            [
                ("future_1_singular", "אני"),
                ("future_2_masculine_singular", "אתה"),
                ("future_2_feminine_singular", "את"),
                ("future_3_masculine_singular", "הוא"),
                ("future_3_feminine_singular", "היא"),
                ("future_1_plural", "אנחנו"),
                ("future_2_plural", "אתם/אתן"),
                ("future_3_plural", "הם/הן"),
            ],
        ),
    ]
)

# Italian glosses for verb 001 לכתוב / scrivere.
ITALIAN_GLOSSES: dict[str, str] = {
    "infinitive": "scrivere",
    "example": "Scrivo una lettera.",
    "present_masculine_singular": "io scrivo",
    "present_feminine_singular": "io scrivo (f.)",
    "present_masculine_plural": "noi/voi/loro scrivono",
    "present_feminine_plural": "noi/voi/loro scrivono (f.)",
    "past_1_singular": "io scrissi",
    "past_2_masculine_singular": "tu scrivesti",
    "past_2_feminine_singular": "tu scrivesti (f.)",
    "past_3_masculine_singular": "lui scrisse",
    "past_3_feminine_singular": "lei scrisse",
    "past_1_plural": "noi scrivemmo",
    "past_2_masculine_plural": "voi scriveste",
    "past_2_feminine_plural": "voi scriveste (f.)",
    "past_3_plural": "loro scrissero",
    "future_1_singular": "io scriverò",
    "future_2_masculine_singular": "tu scriverai",
    "future_2_feminine_singular": "tu scriverai (f.)",
    "future_3_masculine_singular": "lui scriverà",
    "future_3_feminine_singular": "lei scriverà",
    "future_1_plural": "noi scriveremo",
    "future_2_plural": "voi scriverete",
    "future_3_plural": "loro scriveranno",
}

HEBREW_SECTION_HEADINGS = {
    "present": "בַּהוֹוֶה",
    "past": "בָּעָבָר",
    "future": "בָּעָתִיד",
}


def get_pealim_verb(query: str) -> dict[str, Any]:
    data = load_json(PEALIM_FILE)
    for v in data:
        if v["query"] == query:
            return v
    raise RuntimeError(f"Verb {query} not found in {PEALIM_FILE}")


def get_audit_rows(verb: str) -> list[dict[str, Any]]:
    data = load_json(AUDIT_FILE)
    return [r for r in data if r.get("verb") == verb]


def build_form(
    verb: str,
    form_key: str,
    display_key: str,
    pealim_form: dict[str, Any],
    override: OverrideRegistry,
) -> MantraForm:
    """Build one MantraForm through Phonikud + override."""
    hebrew_with_niqqud = pealim_form["hebrew_with_niqqud"]
    hebrew_plain = standard_unvocalized(
        hebrew_with_niqqud,
        chaser=pealim_form.get("chaser", ""),
        hebrew_without_niqqud=pealim_form.get("hebrew_without_niqqud", ""),
    )
    transliteration = transliteration_from_html(pealim_form.get("transcription_html", ""))

    # Phonikud
    phonikud_result = phonemize(hebrew_with_niqqud)
    raw_phonemes = phonikud_result.phonemes
    raw_stress = phonikud_result.stress
    raw_vocal_shva = False

    # Override
    corrected_phonemes, corrected_stress, corrected_vocal_shva, correction_entry = override.apply(
        verb,
        form_key,
        raw_phonemes,
        raw_stress,
        raw_vocal_shva,
        hebrew_with_niqqud,
    )

    return MantraForm(
        form_key=display_key,
        hebrew_with_niqqud=hebrew_with_niqqud,
        hebrew_plain=hebrew_plain,
        transliteration=transliteration,
        ipa_phonemes=raw_phonemes,
        corrected_phonemes=corrected_phonemes,
        lexical_stress=corrected_stress,
        vocal_shva=corrected_vocal_shva,
        italian_gloss=ITALIAN_GLOSSES.get(form_key, ""),
        tts_input=corrected_phonemes,
    ), correction_entry


def build_conjugations(
    verb: str, pealim_forms: dict[str, Any], override: OverrideRegistry
) -> tuple[Conjugations, list[CorrectionEntry]]:
    """Build all conjugated forms grouped by tense."""
    conjugations = Conjugations()
    corrections: list[CorrectionEntry] = []

    for tense, mapping in FORM_LAYOUT.items():
        target = getattr(conjugations, tense)
        for form_key, display_key in mapping:
            pealim_form = pealim_forms[form_key]
            form, correction = build_form(verb, form_key, display_key, pealim_form, override)
            target[display_key] = form
            corrections.append(correction)

    return conjugations, corrections


def build_example_sentence(pealim_verb: dict[str, Any]) -> tuple[str, str, str, str]:
    """Return (hebrew_with_niqqud, hebrew_plain, italian, transliteration) for the example."""
    # The fixed example for לכתוב, taken from the verified Phase 1 content.
    hebrew = "אֲנִי כּוֹתֵב מִכְתָּב"
    plain = standard_unvocalized(hebrew)
    italian = "Scrivo una lettera."
    transliteration = "ani kotev mikhtav"
    return hebrew, plain, italian, transliteration


def build_example_phonemes(hebrew_with_niqqud: str) -> str:
    """Phonemize the example sentence (no manual override exists for it)."""
    return phonikud.phonemize(
        hebrew_with_niqqud,
        preserve_punctuation=True,
        preserve_stress=True,
        use_expander=True,
        use_post_normalize=True,
        predict_stress=True,
        predict_vocal_shva=True,
        schema="modern",
    )


def build_metadata(
    pealim_verb: dict[str, Any],
    infinitive_form: MantraForm,
    example_hebrew: str,
    example_plain: str,
    example_italian: str,
    example_transliteration: str,
) -> MantraMetadata:
    return MantraMetadata(
        order=1,
        hebrew_infinitive_with_niqqud=infinitive_form.hebrew_with_niqqud,
        hebrew_infinitive_plain=infinitive_form.hebrew_plain,
        italian_translation="scrivere",
        transliteration=infinitive_form.transliteration,
        root=pealim_verb.get("root", ""),
        binyan=pealim_verb.get("binyan", ""),
        lexical_stress=infinitive_form.lexical_stress,
        source="Pealim",
        verification_status="verified",
        example_hebrew_with_niqqud=example_hebrew,
        example_hebrew_plain=example_plain,
        example_italian=example_italian,
        example_transliteration=example_transliteration,
    )


def generate_mantra_txt(package: MantraPackage) -> str:
    """Generate the educational mantra.txt content."""
    meta = package.metadata
    lines: list[str] = []
    lines.append(meta.hebrew_infinitive_with_niqqud)
    lines.append(meta.italian_translation)
    lines.append(meta.example_hebrew_with_niqqud)
    lines.append("")

    for tense in ["present", "past", "future"]:
        lines.append(HEBREW_SECTION_HEADINGS[tense] + ":")
        section = getattr(package.conjugations, tense)
        for form in section.values():
            lines.append(form.hebrew_with_niqqud)
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def _ssml_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def generate_ssml(package: MantraPackage) -> str:
    """Generate an Azure-compatible SSML record of the mantra audio."""
    meta = package.metadata
    rate = "-15%"
    between_forms = "500ms"
    section_break = "900ms"
    after_example = "700ms"

    def prosody(text: str) -> str:
        return f'<prosody rate="{rate}">{_ssml_escape(text)}</prosody>'

    def break_ms(ms: str) -> str:
        return f'<break time="{ms}"/>'

    parts: list[str] = []
    parts.append(prosody(meta.hebrew_infinitive_with_niqqud))
    parts.append(break_ms(between_forms))
    parts.append(f'<lang xml:lang="it-IT">{_ssml_escape(meta.italian_translation)}.</lang>')
    parts.append(break_ms(after_example))
    parts.append(prosody(meta.example_hebrew_with_niqqud))
    parts.append(break_ms(after_example))
    parts.append(break_ms(section_break))

    for idx, tense in enumerate(["present", "past", "future"]):
        section = getattr(package.conjugations, tense)
        for form in section.values():
            parts.append(prosody(form.hebrew_with_niqqud))
            parts.append(break_ms(between_forms))
        # extra section break except after future
        if idx < 2:
            parts.append(break_ms(section_break))

    body = "\n    ".join(parts)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xml:lang="he-IL">\n'
        '  <voice name="he-IL-HilaNeural">\n'
        f"    {body}\n"
        "  </voice>\n"
        "</speak>\n"
    )


def generate_audio(package: MantraPackage, mp3_path: Path) -> Path:
    """Generate mantra.mp3 from corrected phonemes using Piper/Phonikud-TTS."""
    voice = PiperVoice(PIPER_MODEL, PIPER_CONFIG)

    # Audio order: infinitive, example, present forms, past forms, future forms.
    # Section breaks after example (index 1), present last (index 5), past last (index 14).
    phoneme_segments: list[str] = [package.infinitive.tts_input]
    # Example sentence
    phoneme_segments.append(
        build_example_phonemes(package.metadata.example_hebrew_with_niqqud)
    )

    section_end_indices: list[int] = [1]
    for tense in ["present", "past", "future"]:
        section = getattr(package.conjugations, tense)
        for form in section.values():
            phoneme_segments.append(form.tts_input)
        section_end_indices.append(len(phoneme_segments) - 1)

    return render_mantra_mp3(
        voice,
        phoneme_segments,
        mp3_path,
        break_seconds=0.5,
        section_break_seconds=0.9,
        section_end_indices=section_end_indices,
    )


def generate_audit(package: MantraPackage) -> dict[str, Any]:
    """Generate audit.json with every manual pronunciation correction."""
    return {
        "verb": package.metadata.hebrew_infinitive_with_niqqud,
        "source": "phonikud_evaluation.json",
        "correction_count": sum(1 for c in package.corrections if c.correction_applied),
        "corrections": [c.as_dict() for c in package.corrections],
    }


def validate_package(
    package: MantraPackage,
    pealim_verb: dict[str, Any],
    audit_rows: list[dict[str, Any]],
) -> None:
    """Ensure the generated package matches Pealim and the previous audit."""
    audit_map = {(r["verb"], r["form_key"]): r for r in audit_rows}

    # Infinitive validation
    inf_entry = audit_map.get(("לכתוב", "infinitive"))
    if inf_entry:
        inf = package.infinitive
        if inf.hebrew_with_niqqud != inf_entry["hebrew_with_niqqud"]:
            raise ValueError(
                f"Infinitive mismatch: {inf.hebrew_with_niqqud} vs {inf_entry['hebrew_with_niqqud']}"
            )
        expected_phonemes = inf_entry.get("manual_override") or inf_entry.get("phonikud_phonemes", "")
        if inf.corrected_phonemes != expected_phonemes:
            raise ValueError(
                f"Infinitive corrected phoneme mismatch: {inf.corrected_phonemes} vs {expected_phonemes}"
            )

    # Validate every conjugated form
    for tense in ["present", "past", "future"]:
        mapping = FORM_LAYOUT[tense]
        section = getattr(package.conjugations, tense)
        for form_key, display_key in mapping:
            audit = audit_map.get(("לכתוב", form_key))
            if not audit:
                continue
            form = section[display_key]
            pealim_form = pealim_verb["forms"][form_key]

            if form.hebrew_with_niqqud != pealim_form["hebrew_with_niqqud"]:
                raise ValueError(
                    f"{form_key} Hebrew mismatch: {form.hebrew_with_niqqud} vs {pealim_form['hebrew_with_niqqud']}"
                )

            expected_phonemes = audit.get("manual_override") or audit.get("phonikud_phonemes", "")
            if form.corrected_phonemes != expected_phonemes:
                raise ValueError(
                    f"{form_key} corrected phoneme mismatch: {form.corrected_phonemes} vs {expected_phonemes}"
                )

            expected_stress = int(audit.get("override_stress") or audit.get("expected_stress") or 0)
            if form.lexical_stress != expected_stress:
                raise ValueError(
                    f"{form_key} stress mismatch: {form.lexical_stress} vs {expected_stress}"
                )

            expected_vocal_shva = bool(audit.get("vocal_shva_override", False))
            if form.vocal_shva != expected_vocal_shva:
                raise ValueError(
                    f"{form_key} vocal shva mismatch: {form.vocal_shva} vs {expected_vocal_shva}"
                )

    print("Validation passed: all forms match Pealim and the previous audit.")


def generate_verb_001() -> MantraPackage:
    """Build the complete production package for verb 001 / לִכְתּוֹב."""
    verb_query = "לכתוב"
    pealim_verb = get_pealim_verb(verb_query)
    audit_rows = get_audit_rows(verb_query)
    override = OverrideRegistry.from_phonikud_evaluation(AUDIT_FILE)

    pealim_forms = pealim_verb["forms"]

    # Infinitive (needed for metadata, not part of conjugations JSON)
    infinitive_form, inf_correction = build_form(
        verb_query, "infinitive", "infinitive", pealim_forms["infinitive"], override
    )

    # Conjugations
    conjugations, corrections = build_conjugations(verb_query, pealim_forms, override)
    all_corrections = [inf_correction] + corrections

    # Example sentence
    example_hebrew, example_plain, example_italian, example_transliteration = build_example_sentence(
        pealim_verb
    )

    metadata = build_metadata(
        pealim_verb,
        infinitive_form,
        example_hebrew,
        example_plain,
        example_italian,
        example_transliteration,
    )

    package = MantraPackage(
        metadata=metadata,
        infinitive=infinitive_form,
        conjugations=conjugations,
        example_sentence=example_hebrew,
        corrections=all_corrections,
    )

    # Phase 3 validation before writing
    validate_package(package, pealim_verb, audit_rows)

    return package


def write_package(package: MantraPackage, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    save_json(output_dir / "metadata.json", package.metadata.as_dict())
    save_json(output_dir / "conjugations.json", package.conjugations.as_dict())
    (output_dir / "mantra.txt").write_text(generate_mantra_txt(package), encoding="utf-8")
    (output_dir / "mantra.ssml").write_text(generate_ssml(package), encoding="utf-8")
    save_json(output_dir / "audit.json", generate_audit(package))

    mp3_path = output_dir / "mantra.mp3"
    generate_audio(package, mp3_path)


def main() -> int:
    package = generate_verb_001()
    output_dir = DATA_DIR / "001_lichtov"
    write_package(package, output_dir)
    print(f"Mantra package written to {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
