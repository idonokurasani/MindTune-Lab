"""Validate the shared Hebrew engine with לכתוב, להיות, לעשות."""
from __future__ import annotations

import json
from pathlib import Path

from .adapters.java_inflector_adapter import VerbInflectorAdapter
from .adapters.phonikud_adapter import phonemize
from .normalization import strip_niqqud
from .pronunciation_engine import PronunciationEngine
from .resources.pealim_reference import load_approved_verbs
from .services.audit_service import AuditService
from .services.verb_service import VerbService
from .services.sentence_service import SentenceService
from .services.pronunciation_service import PronunciationService
from .services.validation_service import ValidationService


VERB_DATA = [
    ("לִכְתֹּב", "לכתוב", "כ-ת-ב", "PA'AL"),
    ("לִהְיוֹת", "להיות", "ה-י-ה", "PA'AL"),
    ("לַעֲשׂוֹת", "לעשות", "ע-ש-ה", "PA'AL"),
]


def main() -> int:
    data_dir = Path(__file__).resolve().parents[1] / "data" / "hebrew"
    approved_dir = data_dir / "approved"
    approved_dir.mkdir(parents=True, exist_ok=True)
    audit = AuditService(audit_dir=data_dir / "audits")
    verb_service = VerbService(data_dir=data_dir)
    sentence_service = SentenceService(data_dir=data_dir)
    pronunciation_service = PronunciationService()
    validation_service = ValidationService()
    inflector = VerbInflectorAdapter()

    reports: list[dict] = []

    for lemma_vocalized, lemma_plain, root, binyan in VERB_DATA:
        print(f"Validating {lemma_plain} ...")

        # Full paradigm
        paradigm = verb_service.get_full_paradigm(lemma_vocalized, lemma_plain, root, binyan)

        # Verb Inflector: base forms are not always the infinitive minus the ל prefix.
        base_form_map = {
            "לכתוב": "כתב",
            "להיות": "היה",
            "לעשות": "עש'ה",
        }
        base_form = base_form_map.get(lemma_plain, strip_niqqud(lemma_vocalized).lstrip("ל"))
        pattern, table_number = inflector._resolve_pattern_table(base_form, binyan)
        inflected_rows = inflector.generate(base_form, pattern, table_number)

        # Sentence candidates
        sentences = sentence_service.get_example_sentences(lemma_plain, limit=3)

        # Pronunciation for infinitive
        pron = pronunciation_service.get_pronunciation(lemma_vocalized)

        # Source comparison
        comparison = verb_service.compare_sources(lemma_plain)

        # Audit disagreements
        audit.log_disagreement(lemma_plain, comparison)

        report = {
            "lemma_vocalized": lemma_vocalized,
            "lemma_plain": lemma_plain,
            "root": root,
            "binyan": binyan,
            "paradigm_form_count": len(paradigm.forms),
            "inflector_form_count": len(inflected_rows),
            "sentence_candidates": [s.as_dict() for s in sentences],
            "infinitive_pronunciation": pron.as_dict(),
            "source_comparison": comparison,
        }
        reports.append(report)

        out_path = approved_dir / f"{strip_niqqud(lemma_plain)}.json"
        out_path.write_text(
            json.dumps(
                {
                    "paradigm": paradigm.as_dict(),
                    "inflector_forms": inflected_rows[:10],  # sample
                    "report": report,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        print(f"  wrote {out_path}")

    summary_path = data_dir / "approved" / "validation_summary.json"
    summary_path.write_text(json.dumps(reports, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Validation summary: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
