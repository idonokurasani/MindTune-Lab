"""Shared data models for the Hebrew linguistic engine.

Includes explicit approval layers, source filtering, consensus, usage
classification and shva diagnosis fields.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class MorphologicalFeatures:
    root: str = ""
    binyan: str = ""
    tense: str = ""  # past, present, future, imperative, infinitive
    mood: str = ""
    person: str = ""  # first, second, third
    gender: str = ""  # masculine, feminine, masculine+feminine
    number: str = ""  # singular, plural
    completeness: str = ""  # complete, missing
    pattern: str = ""  # Verb Inflector pattern letter
    table_number: int = 0

    def as_dict(self) -> dict[str, Any]:
        return {
            "root": self.root,
            "binyan": self.binyan,
            "tense": self.tense,
            "mood": self.mood,
            "person": self.person,
            "gender": self.gender,
            "number": self.number,
            "completeness": self.completeness,
            "pattern": self.pattern,
            "table_number": self.table_number,
        }


@dataclass
class SourceEvidence:
    source_id: str = ""  # registered source id
    source: str = ""  # legacy display name
    source_eligibility: str = "unknown"  # production_approved, private_research_only, reference_only, blocked, unknown
    record: dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    trust_tier: int = 3  # 1=manual, 2=approved, 3=verified, 4=candidate

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "source": self.source,
            "source_eligibility": self.source_eligibility,
            "record": self.record,
            "confidence": self.confidence,
            "trust_tier": self.trust_tier,
        }


@dataclass
class SourceDisagreement:
    field_name: str
    values: dict[str, Any]  # source_id -> value
    severity: str = "minor"  # minor, major, blocking
    resolution: str = "unresolved"  # unresolved, override, accepted

    def as_dict(self) -> dict[str, Any]:
        return {
            "field_name": self.field_name,
            "values": self.values,
            "severity": self.severity,
            "resolution": self.resolution,
        }


@dataclass
class ShvaDiagnosis:
    shva_status: str = "not_applicable"  # vocal, silent, ambiguous, not_applicable
    shva_source: str = ""
    shva_confidence: float = 0.0
    shva_reason: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "shva_status": self.shva_status,
            "shva_source": self.shva_source,
            "shva_confidence": self.shva_confidence,
            "shva_reason": self.shva_reason,
        }


@dataclass
class PronunciationRecord:
    phonemes_raw: str = ""
    phonemes_corrected: str = ""
    transliteration: str = ""
    lexical_stress: int = 0
    vocal_shva: bool = False
    shva: ShvaDiagnosis = field(default_factory=ShvaDiagnosis)
    source: str = ""
    source_id: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "phonemes_raw": self.phonemes_raw,
            "phonemes_corrected": self.phonemes_corrected,
            "transliteration": self.transliteration,
            "lexical_stress": self.lexical_stress,
            "vocal_shva": self.vocal_shva,
            "shva": self.shva.as_dict(),
            "source": self.source,
            "source_id": self.source_id,
        }


@dataclass
class LinguisticOverride:
    scope: str  # verb, form, sentence, global
    target: str  # lemma or surface form or pattern
    field: str  # phonemes, stress, vocal_shva, transliteration, spelling, etc.
    value: Any
    reason: str = ""
    author: str = ""
    timestamp: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "scope": self.scope,
            "target": self.target,
            "field": self.field,
            "value": self.value,
            "reason": self.reason,
            "author": self.author,
            "timestamp": self.timestamp,
        }


@dataclass
class ConsensusInfo:
    canonical_vocalized: str = ""
    canonical_plain: str = ""
    agreement_count: int = 0
    disagreement_count: int = 0
    source_forms: dict[str, str] = field(default_factory=dict)
    confidence: float = 0.0

    def as_dict(self) -> dict[str, Any]:
        return {
            "canonical_vocalized": self.canonical_vocalized,
            "canonical_plain": self.canonical_plain,
            "agreement_count": self.agreement_count,
            "disagreement_count": self.disagreement_count,
            "source_forms": self.source_forms,
            "confidence": self.confidence,
        }


@dataclass
class VerbForm:
    # Identifiers
    form_key: str = ""
    lemma_vocalized: str = ""  # e.g. "לִכְתֹּב"
    lemma_plain: str = ""  # e.g. "לכתוב"
    surface_vocalized: str = ""  # e.g. "כּוֹתֵב"
    surface_plain: str = ""  # e.g. "כותב"
    root: str = ""
    binyan: str = ""

    # Morphology
    tense: str = ""
    mood: str = ""
    person: str = ""
    gender: str = ""
    number: str = ""

    # Approval layers
    linguistic_status: str = "raw"  # raw, normalized, candidate, validated, disputed, rejected
    curriculum_status: str = "not_reviewed"  # not_reviewed, approved, restricted, rejected
    validation_evidence: List[str] = field(default_factory=list)
    source_agreement: str = "none"  # none, partial, full
    reviewer_status: str = "none"  # none, pending, reviewed
    confidence: float = 0.0
    rejection_reason: str = ""
    usage_classification: str = "unknown"  # core_modern, common_modern, valid_but_rare, literary, archaic, disputed, unattested, unknown

    # Pronunciation
    transliteration: str = ""
    phonemes_raw: str = ""
    phonemes_corrected: str = ""
    lexical_stress: int = 0
    vocal_shva: bool = False
    shva: ShvaDiagnosis = field(default_factory=ShvaDiagnosis)
    preferred_pronunciation: str = ""

    # Consensus / corpus
    consensus: ConsensusInfo = field(default_factory=ConsensusInfo)
    corpus_attestation_count: int = 0

    # Provenance and quality
    source_evidence: List[SourceEvidence] = field(default_factory=list)
    applied_overrides: List[LinguisticOverride] = field(default_factory=list)
    approval_status: str = "candidate"  # candidate, reviewed, approved, rejected
    unresolved_conflicts: List[SourceDisagreement] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "form_key": self.form_key,
            "lemma_vocalized": self.lemma_vocalized,
            "lemma_plain": self.lemma_plain,
            "surface_vocalized": self.surface_vocalized,
            "surface_plain": self.surface_plain,
            "root": self.root,
            "binyan": self.binyan,
            "tense": self.tense,
            "mood": self.mood,
            "person": self.person,
            "gender": self.gender,
            "number": self.number,
            "linguistic_status": self.linguistic_status,
            "curriculum_status": self.curriculum_status,
            "validation_evidence": self.validation_evidence,
            "source_agreement": self.source_agreement,
            "reviewer_status": self.reviewer_status,
            "confidence": self.confidence,
            "rejection_reason": self.rejection_reason,
            "usage_classification": self.usage_classification,
            "transliteration": self.transliteration,
            "phonemes_raw": self.phonemes_raw,
            "phonemes_corrected": self.phonemes_corrected,
            "lexical_stress": self.lexical_stress,
            "vocal_shva": self.vocal_shva,
            "shva": self.shva.as_dict(),
            "preferred_pronunciation": self.preferred_pronunciation,
            "consensus": self.consensus.as_dict(),
            "corpus_attestation_count": self.corpus_attestation_count,
            "source_evidence": [e.as_dict() for e in self.source_evidence],
            "applied_overrides": [o.as_dict() for o in self.applied_overrides],
            "approval_status": self.approval_status,
            "unresolved_conflicts": [c.as_dict() for c in self.unresolved_conflicts],
        }


@dataclass
class VerbLemma:
    lemma_vocalized: str = ""
    lemma_plain: str = ""
    root: str = ""
    binyan: str = ""
    infinitive_form: Optional[VerbForm] = None
    forms: Dict[str, VerbForm] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "lemma_vocalized": self.lemma_vocalized,
            "lemma_plain": self.lemma_plain,
            "root": self.root,
            "binyan": self.binyan,
            "infinitive_form": self.infinitive_form.as_dict() if self.infinitive_form else None,
            "forms": {k: v.as_dict() for k, v in self.forms.items()},
        }


@dataclass
class ConjugationParadigm:
    lemma: VerbLemma = field(default_factory=VerbLemma)
    forms: Dict[str, VerbForm] = field(default_factory=dict)
    paradigm_status: str = "candidate"  # candidate, validated, approved, rejected
    source_agreement: str = "none"

    def as_dict(self) -> dict[str, Any]:
        return {
            "lemma": self.lemma.as_dict(),
            "forms": {k: v.as_dict() for k, v in self.forms.items()},
            "paradigm_status": self.paradigm_status,
            "source_agreement": self.source_agreement,
        }


@dataclass
class HebrewVerb:
    lemma: VerbLemma = field(default_factory=VerbLemma)
    paradigms: Dict[str, ConjugationParadigm] = field(default_factory=dict)
    sources: List[SourceEvidence] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "lemma": self.lemma.as_dict(),
            "paradigms": {k: v.as_dict() for k, v in self.paradigms.items()},
            "sources": [s.as_dict() for s in self.sources],
        }


@dataclass
class ExampleSentence:
    sentence_id: str = ""
    original_hebrew: str = ""
    normalized_hebrew: str = ""
    token_count: int = 0
    detected_lemmas: List[str] = field(default_factory=list)
    detected_roots: List[str] = field(default_factory=list)
    phonemes: str = ""
    phoneme_inventory: List[str] = field(default_factory=list)
    coverage_score: float = 0.0
    complexity_score: float = 0.0

    # Target-form checks
    target_form: str = ""
    target_form_present: bool = False
    target_form_exact_match: bool = False
    target_form_morphological_match: bool = False

    # Quality checks
    punctuation_quality_ok: bool = True
    suspected_noise: bool = False
    ambiguity_score: float = 0.0
    vocabulary_complexity: float = 0.0

    # Source / approval
    source_id: str = "svlm"
    source_eligibility: str = "private_research_only"
    licensing_eligibility: str = "private_research_only"
    curriculum_suitability: str = "unknown"
    curriculum_status: str = "not_reviewed"
    approved: bool = False
    rejection_reason: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "sentence_id": self.sentence_id,
            "original_hebrew": self.original_hebrew,
            "normalized_hebrew": self.normalized_hebrew,
            "token_count": self.token_count,
            "detected_lemmas": self.detected_lemmas,
            "detected_roots": self.detected_roots,
            "phonemes": self.phonemes,
            "phoneme_inventory": self.phoneme_inventory,
            "coverage_score": self.coverage_score,
            "complexity_score": self.complexity_score,
            "target_form": self.target_form,
            "target_form_present": self.target_form_present,
            "target_form_exact_match": self.target_form_exact_match,
            "target_form_morphological_match": self.target_form_morphological_match,
            "punctuation_quality_ok": self.punctuation_quality_ok,
            "suspected_noise": self.suspected_noise,
            "ambiguity_score": self.ambiguity_score,
            "vocabulary_complexity": self.vocabulary_complexity,
            "source_id": self.source_id,
            "source_eligibility": self.source_eligibility,
            "licensing_eligibility": self.licensing_eligibility,
            "curriculum_suitability": self.curriculum_suitability,
            "curriculum_status": self.curriculum_status,
            "approved": self.approved,
            "rejection_reason": self.rejection_reason,
        }


@dataclass
class ValidationResult:
    status: str = "unknown"
    submitted: str = ""
    expected: str = ""
    accepted_variants: List[str] = field(default_factory=list)
    details: List[str] = field(default_factory=list)
    score: float = 0.0
    diagnosis_type: str = "unknown"
    affected_feature: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "submitted": self.submitted,
            "expected": self.expected,
            "accepted_variants": self.accepted_variants,
            "details": self.details,
            "score": self.score,
            "diagnosis_type": self.diagnosis_type,
            "affected_feature": self.affected_feature,
        }


@dataclass
class ManifestEntry:
    resource_name: str = ""
    upstream_url: str = ""
    version_or_commit: str = ""
    license: str = ""
    import_date: str = ""
    file_hashes: Dict[str, str] = field(default_factory=dict)
    total_records: int = 0
    accepted_records: int = 0
    rejected_records: int = 0
    normalization_rules: List[str] = field(default_factory=list)
    parser_version: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "resource_name": self.resource_name,
            "upstream_url": self.upstream_url,
            "version_or_commit": self.version_or_commit,
            "license": self.license,
            "import_date": self.import_date,
            "file_hashes": self.file_hashes,
            "total_records": self.total_records,
            "accepted_records": self.accepted_records,
            "rejected_records": self.rejected_records,
            "normalization_rules": self.normalization_rules,
            "parser_version": self.parser_version,
        }
