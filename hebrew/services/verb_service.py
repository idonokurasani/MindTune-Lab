"""Verb lookup and paradigm service."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..adapters.java_inflector_adapter import VerbInflectorAdapter
from ..conjugation_engine import ConjugationEngine
from ..models import ConjugationParadigm, VerbForm
from ..morphology import morphology_features_to_form_key
from ..normalization import normalize_hebrew, standard_unvocalized, strip_niqqud
from ..shva import classify_shva


# Base forms expected by the Java Verb Inflector for the initial validation verbs.
INFLECTOR_BASE_FORMS = {
    "לכתוב": ("כתב", "A", 1),
    "להיות": ("היה", "A", 56),
    "לעשות": ("עש'ה", "A", 50),
}


class VerbService:
    """Shared service for verb retrieval, paradigms and source comparison."""

    def __init__(
        self,
        data_dir: Path | None = None,
        pealim_forms_path: Path | None = None,
        pealim_audit_path: Path | None = None,
    ):
        self.data_dir = data_dir or (Path(__file__).resolve().parents[2] / "data" / "hebrew")
        self.pealim_forms_path = pealim_forms_path or (self.data_dir / "resources" / "pealim" / "pealim_forms.json")
        self.pealim_audit_path = pealim_audit_path or (self.data_dir / "resources" / "pealim" / "phonikud_evaluation.json")
        self.eran_records: list[dict[str, Any]] = []
        self.eran_indexes: dict[str, Any] = {}
        self.pealim_records: list[dict[str, Any]] = []
        self.corpus_counts: dict[str, int] = {}
        self.inflector = VerbInflectorAdapter()
        self._load_indexes()

    def _load_indexes(self) -> None:
        eran_records_path = self.data_dir / "indexes" / "eran_tomer" / "records.json"
        eran_indexes_path = self.data_dir / "indexes" / "eran_tomer" / "indexes.json"
        svlm_indexes_path = self.data_dir / "indexes" / "svlm" / "indexes.json"
        if eran_records_path.exists():
            self.eran_records = json.loads(eran_records_path.read_text(encoding="utf-8"))
        if eran_indexes_path.exists():
            self.eran_indexes = json.loads(eran_indexes_path.read_text(encoding="utf-8"))
        if svlm_indexes_path.exists():
            svlm_indexes = json.loads(svlm_indexes_path.read_text(encoding="utf-8"))
            for surface, indices in svlm_indexes.get("by_surface", {}).items():
                self.corpus_counts[surface] = len(indices)
        if self.pealim_forms_path.exists() and self.pealim_audit_path.exists():
            from ..resources.pealim_reference import load_approved_verbs

            self.pealim_records = load_approved_verbs(self.pealim_forms_path, self.pealim_audit_path)

    def get_engine(self) -> ConjugationEngine:
        return ConjugationEngine(
            eran_tomer_records=self.eran_records,
            eran_tomer_indexes=self.eran_indexes,
            pealim_records=self.pealim_records,
            corpus_counts=self.corpus_counts,
            inflector=self.inflector,
        )

    def get_verb(self, lemma_plain: str) -> dict[str, Any] | None:
        """Return basic information about a verb."""
        target = strip_niqqud(lemma_plain).strip()
        for rec in self.pealim_records:
            if strip_niqqud(rec.get("verb_query", "")).strip() == target:
                return {
                    "lemma_plain": lemma_plain,
                    "root": rec.get("root"),
                    "binyan": rec.get("binyan"),
                }
        return None

    def _inflector_args(self, lemma_plain: str) -> tuple[str, str, int]:
        target = strip_niqqud(lemma_plain).strip()
        if target in INFLECTOR_BASE_FORMS:
            return INFLECTOR_BASE_FORMS[target]
        # Fallback: lookup from TheVerbIndex.csv
        base = target.lstrip("ל")
        return self.inflector._resolve_pattern_table(base, None)

    def get_full_paradigm(
        self,
        lemma_vocalized: str,
        lemma_plain: str,
        root: str,
        binyan: str,
    ) -> ConjugationParadigm:
        base, pattern, table = self._inflector_args(lemma_plain)
        return self.get_engine().build_paradigm(
            lemma_vocalized,
            lemma_plain,
            root,
            binyan,
            inflector_base_form=base,
            inflector_pattern=pattern,
            inflector_table=table,
        )

    def get_conjugation(
        self,
        lemma_plain: str,
        tense: str | None = None,
        mood: str | None = None,
        person: str | None = None,
        gender: str | None = None,
        number: str | None = None,
    ) -> list[VerbForm]:
        """Return matching forms from Pealim-approved data."""
        forms: list[VerbForm] = []
        target = strip_niqqud(lemma_plain).strip()
        for rec in self.pealim_records:
            if strip_niqqud(rec.get("verb_query", "")).strip() != target:
                continue
            morph = rec.get("morphology", {})
            if tense and morph.get("tense") != tense:
                continue
            if person and morph.get("person") != person:
                continue
            if gender and morph.get("gender") != gender:
                continue
            if number and morph.get("number") != number:
                continue
            surface = normalize_hebrew(rec["surface_vocalized"])
            canonical_key = rec.get("canonical_form_key") or rec["form_key"]
            forms.append(
                VerbForm(
                    form_key=canonical_key,
                    surface_vocalized=surface,
                    surface_plain=standard_unvocalized(surface),
                    root=rec.get("root", ""),
                    binyan=rec.get("binyan", ""),
                    tense=morph.get("tense", ""),
                    person=morph.get("person", ""),
                    gender=morph.get("gender", ""),
                    number=morph.get("number", ""),
                    transliteration=rec.get("transliteration", ""),
                    phonemes_raw=rec.get("phonemes_raw", ""),
                    phonemes_corrected=rec.get("phonemes_corrected", ""),
                    lexical_stress=rec.get("lexical_stress", 0),
                    vocal_shva=rec.get("vocal_shva", False),
                    shva=classify_shva(surface, manual_override=rec.get("vocal_shva_override")),
                    approval_status=rec.get("approval_status", "candidate"),
                )
            )
        return forms

    def analyze_form(self, surface_form: str) -> list[dict[str, Any]]:
        """Reverse lookup: find Eran Tomer entries matching a surface form."""
        plain = strip_niqqud(surface_form)
        matches: list[dict[str, Any]] = []
        for rec in self.eran_records:
            if strip_niqqud(rec.get("surface_vocalized", "")) == plain:
                matches.append(rec)
        return matches

    def find_lemma(self, surface_form: str) -> list[str]:
        """Return candidate base forms for a surface form."""
        return list({r["base_form_vocalized"] for r in self.analyze_form(surface_form)})

    def compare_sources(self, lemma_plain: str) -> dict[str, Any]:
        return self.get_engine().compare_sources(lemma_plain)

    def inflector_generate(self, base_form: str, pattern: str, table_number: int) -> list[dict[str, Any]]:
        return self.inflector.generate(base_form, pattern, table_number)
