"""Conjugation engine that aggregates sources, builds consensus and runs approval."""

from __future__ import annotations

from typing import Any

from .adapters.java_inflector_adapter import VerbInflectorAdapter
from .approval import ApprovalPipeline
from .consensus import build_consensus
from .models import ConjugationParadigm, MorphologicalFeatures, SourceEvidence, VerbForm, VerbLemma
from .morphology import morphology_features_to_form_key, binyan_from_pattern, parse_morphology_tag
from .normalization import normalize_hebrew, standard_unvocalized, strip_niqqud
from .pronunciation_engine import PronunciationEngine
from .resources.source_registry import SourceRegistry
from .shva import classify_shva
from .usage import classify_form


SOURCE_ELIGIBILITY = {
    "eran_tomer": "production_approved",
    "verb_inflector": "production_approved",
    "pealim": "reference_only",
    "pealim_audit": "reference_only",
    "manual_override": "production_approved",
    "phonikud": "private_research_only",
}


def _source_id_to_eligibility(source_id: str) -> str:
    return SOURCE_ELIGIBILITY.get(source_id, "unknown")


class ConjugationEngine:
    """Build and compare conjugation paradigms from multiple sources."""

    def __init__(
        self,
        eran_tomer_records: list[dict[str, Any]] | None = None,
        eran_tomer_indexes: dict[str, Any] | None = None,
        pealim_records: list[dict[str, Any]] | None = None,
        pronunciation_engine: PronunciationEngine | None = None,
        inflector: VerbInflectorAdapter | None = None,
        corpus_counts: dict[str, int] | None = None,
    ):
        self.eran_records = eran_tomer_records or []
        self.eran_indexes = eran_tomer_indexes or {}
        self.pealim_records = pealim_records or []
        self.pronunciation = pronunciation_engine or PronunciationEngine()
        self.inflector = inflector or VerbInflectorAdapter()
        self.corpus_counts = corpus_counts or {}
        self.registry = SourceRegistry()
        self.approval = ApprovalPipeline(self.registry)

    def _pealim_records_for_verb(self, lemma_plain: str) -> list[dict[str, Any]]:
        target = strip_niqqud(lemma_plain).strip()
        return [
            r
            for r in self.pealim_records
            if strip_niqqud(r.get("verb_query", "")).strip() == target
        ]

    def _eran_records_for_base(self, base_plain: str) -> list[dict[str, Any]]:
        return [
            r
            for r in self.eran_records
            if strip_niqqud(r.get("base_form_vocalized", "")) == base_plain
        ]

    def _inflector_records_for_base(
        self, base_form: str, pattern: str, table_number: int
    ) -> list[dict[str, Any]]:
        try:
            return self.inflector.generate(base_form, pattern, table_number)
        except Exception:
            return []

    def _make_source_evidence(
        self, source_id: str, record: dict[str, Any], confidence: float = 1.0, trust_tier: int = 3
    ) -> SourceEvidence:
        return SourceEvidence(
            source_id=source_id,
            source=source_id,
            source_eligibility=_source_id_to_eligibility(source_id),
            record=record,
            confidence=confidence,
            trust_tier=trust_tier,
        )

    def _build_form_from_pealim(
        self, rec: dict[str, Any], lemma_vocalized: str, lemma_plain: str
    ) -> VerbForm:
        surface = normalize_hebrew(rec["surface_vocalized"])
        features = MorphologicalFeatures(**rec.get("morphology", {}))
        canonical_key = rec.get("canonical_form_key") or rec["form_key"]
        form = VerbForm(
            form_key=canonical_key,
            lemma_vocalized=lemma_vocalized,
            lemma_plain=lemma_plain,
            surface_vocalized=surface,
            surface_plain=standard_unvocalized(surface),
            root=rec.get("root", ""),
            binyan=rec.get("binyan", ""),
            tense=features.tense,
            person=features.person,
            gender=features.gender,
            number=features.number,
            transliteration=rec.get("transliteration", ""),
            phonemes_raw=rec.get("phonemes_raw", ""),
            phonemes_corrected=rec.get("phonemes_corrected", ""),
            lexical_stress=rec.get("lexical_stress", 0),
            vocal_shva=rec.get("vocal_shva", False),
            shva=classify_shva(surface, manual_override=rec.get("vocal_shva_override")),
            source_evidence=[self._make_source_evidence("pealim", rec, trust_tier=3)],
            approval_status=rec.get("approval_status", "candidate"),
        )
        self.approval.normalize(form, ["normalized from Pealim reference"])
        return form

    def _build_form_from_eran(
        self, rec: dict[str, Any], lemma_vocalized: str, lemma_plain: str
    ) -> VerbForm:
        surface = normalize_hebrew(rec["surface_vocalized"])
        features = parse_morphology_tag(
            rec["morphology"], rec.get("pattern", ""), rec.get("table_number", 0)
        )
        pron = self.pronunciation.get_pronunciation(surface)
        form = VerbForm(
            form_key=morphology_features_to_form_key(features),
            lemma_vocalized=lemma_vocalized,
            lemma_plain=lemma_plain,
            surface_vocalized=surface,
            surface_plain=standard_unvocalized(surface),
            root=rec.get("root", ""),
            binyan=rec.get("binyan", ""),
            tense=features.tense,
            person=features.person,
            gender=features.gender,
            number=features.number,
            phonemes_raw=pron.phonemes_raw,
            phonemes_corrected=pron.phonemes_corrected,
            lexical_stress=pron.lexical_stress,
            shva=pron.shva,
            source_evidence=[self._make_source_evidence("eran_tomer", rec, trust_tier=4)],
        )
        self.approval.normalize(form, ["normalized from Eran Tomer"])
        return form

    def _build_form_from_inflector(
        self, rec: dict[str, Any], lemma_vocalized: str, lemma_plain: str
    ) -> VerbForm:
        surface = normalize_hebrew(rec["surface_vocalized"])
        features = MorphologicalFeatures(**rec.get("features", {}))
        pron = self.pronunciation.get_pronunciation(surface)
        form = VerbForm(
            form_key=morphology_features_to_form_key(features),
            lemma_vocalized=lemma_vocalized,
            lemma_plain=lemma_plain,
            surface_vocalized=surface,
            surface_plain=standard_unvocalized(surface),
            root=rec.get("root", ""),
            binyan=rec.get("binyan", ""),
            tense=features.tense,
            person=features.person,
            gender=features.gender,
            number=features.number,
            phonemes_raw=pron.phonemes_raw,
            phonemes_corrected=pron.phonemes_corrected,
            lexical_stress=pron.lexical_stress,
            shva=pron.shva,
            source_evidence=[self._make_source_evidence("verb_inflector", rec, trust_tier=4)],
        )
        self.approval.normalize(form, ["normalized from Verb Inflector"])
        return form

    def _build_infinitive_form(
        self, lemma_vocalized: str, lemma_plain: str, root: str, binyan: str
    ) -> VerbForm:
        pron = self.pronunciation.get_pronunciation(lemma_vocalized)
        form = VerbForm(
            form_key="infinitive",
            lemma_vocalized=lemma_vocalized,
            lemma_plain=lemma_plain,
            surface_vocalized=lemma_vocalized,
            surface_plain=lemma_plain,
            root=root,
            binyan=binyan,
            tense="infinitive",
            phonemes_raw=pron.phonemes_raw,
            phonemes_corrected=pron.phonemes_corrected,
            lexical_stress=pron.lexical_stress,
            shva=pron.shva,
            source_evidence=[
                self._make_source_evidence(
                    "manual_override", {"lemma": lemma_vocalized}, trust_tier=1
                )
            ],
        )
        self.approval.normalize(form, ["infinitive supplied by curriculum"])
        return form

    def build_paradigm(
        self,
        lemma_vocalized: str,
        lemma_plain: str,
        root: str,
        binyan: str,
        inflector_base_form: str | None = None,
        inflector_pattern: str | None = None,
        inflector_table: int | None = None,
    ) -> ConjugationParadigm:
        """Build a consensus paradigm from Pealim, Eran Tomer and Verb Inflector."""
        lemma = VerbLemma(
            lemma_vocalized=lemma_vocalized,
            lemma_plain=lemma_plain,
            root=root,
            binyan=binyan,
        )
        paradigm = ConjugationParadigm(lemma=lemma)

        # Collect source forms keyed by form_key, merging by surface or plain form.
        source_forms: dict[str, dict[str, VerbForm]] = {}
        surface_to_key: dict[str, str] = {}
        plain_to_key: dict[str, str] = {}

        def add_form(form: VerbForm, source_id: str, record: dict[str, Any]) -> None:
            """Add a form, merging with an existing form if the surface or plain form matches."""
            surf_key = form.surface_vocalized
            plain_key = form.surface_plain
            if surf_key in surface_to_key:
                existing_key = surface_to_key[surf_key]
                source_forms[existing_key].setdefault(source_id, form)
                return
            if plain_key in plain_to_key:
                existing_key = plain_to_key[plain_key]
                existing = source_forms[existing_key].setdefault(source_id, form)
                if existing is not form:
                    existing.source_evidence.append(
                        self._make_source_evidence(source_id, record, trust_tier=4)
                    )
                return
            if form.form_key in source_forms and source_id not in source_forms[form.form_key]:
                source_forms[form.form_key][source_id] = form
            else:
                source_forms.setdefault(form.form_key, {})[source_id] = form
            surface_to_key[surf_key] = form.form_key
            plain_to_key[plain_key] = form.form_key

        # Pealim
        for rec in self._pealim_records_for_verb(lemma_plain):
            form = self._build_form_from_pealim(rec, lemma_vocalized, lemma_plain)
            add_form(form, "pealim", rec)

        # Infinitive: always add the manual override as an authority.
        inf = self._build_infinitive_form(lemma_vocalized, lemma_plain, root, binyan)
        add_form(inf, "manual_override", {"lemma": lemma_vocalized})

        # Eran Tomer (base form lookup)
        base_plain = standard_unvocalized(lemma_vocalized).lstrip("ל")
        if inflector_base_form:
            base_plain = strip_niqqud(inflector_base_form)
        for rec in self._eran_records_for_base(base_plain):
            form = self._build_form_from_eran(rec, lemma_vocalized, lemma_plain)
            add_form(form, "eran_tomer", rec)

        # Verb Inflector
        if inflector_base_form and inflector_pattern and inflector_table:
            try:
                for rec in self._inflector_records_for_base(
                    inflector_base_form, inflector_pattern, inflector_table
                ):
                    form = self._build_form_from_inflector(rec, lemma_vocalized, lemma_plain)
                    add_form(form, "verb_inflector", rec)
            except Exception:
                pass

        # Consensus and approval
        all_disagreements: list = []
        for form_key, forms_by_source in source_forms.items():
            if len(forms_by_source) == 1:
                consensus = next(iter(forms_by_source.values()))
            else:
                consensus, disagreements = build_consensus(forms_by_source)
                all_disagreements.extend(disagreements)

            # Corpus attestation count for plain form
            plain = consensus.surface_plain
            corpus_count = self.corpus_counts.get(plain, 0)
            consensus.corpus_attestation_count = corpus_count
            consensus.usage_classification = classify_form(consensus, corpus_count)

            # Approval
            if consensus.source_evidence:
                if any(ev.source_id == "manual_override" for ev in consensus.source_evidence):
                    self.approval.validate(consensus, 1.0, ["manual override present"])
                    self.approval.approve_for_curriculum(
                        consensus, "consensus_engine", ["manual override"]
                    )
                elif any(ev.source_id == "pealim" for ev in consensus.source_evidence):
                    self.approval.candidate(
                        consensus, consensus.consensus.confidence, ["Pealim reference"]
                    )
                    self.approval.validate(
                        consensus, consensus.consensus.confidence, ["Pealim reference"]
                    )
                else:
                    self.approval.candidate(
                        consensus, consensus.consensus.confidence, ["single/computed source"]
                    )

            paradigm.forms[form_key] = consensus

        # Paradigm-level agreement
        if not all_disagreements:
            paradigm.source_agreement = "full"
        else:
            paradigm.source_agreement = "partial"

        return paradigm

    def compare_sources(self, lemma_plain: str) -> dict[str, Any]:
        """Return form-by-form source comparison for a verb."""
        pealim_by_form: dict[str, dict[str, Any]] = {}
        for rec in self._pealim_records_for_verb(lemma_plain):
            pealim_by_form[rec["form_key"]] = {
                "surface_vocalized": rec["surface_vocalized"],
                "surface_plain": standard_unvocalized(rec["surface_vocalized"]),
                "lexical_stress": rec["lexical_stress"],
                "phonemes_corrected": rec["phonemes_corrected"],
            }
        return {
            "lemma": lemma_plain,
            "approved_source": "pealim",
            "form_reports": pealim_by_form,
        }
