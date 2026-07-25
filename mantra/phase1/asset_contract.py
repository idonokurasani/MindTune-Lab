"""Typed audio asset requirement and inventory contracts.

This module is the deterministic bridge between a reviewed linguistic
specification and the actual audio assets.  It builds requirements, computes
cache keys, and inspects the inventory without calling SpeechGen.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from mantra.domain.audio_profile import AudioProfile
from mantra.domain.hebrew.specification import (
    AssetKind,
    EntryRole,
    GrammaticalGender,
    GrammaticalNumber,
    GrammaticalPerson,
    GrammaticalSection,
    HebrewVerbSpecification,
    HumanAudioReviewStatus,
    PedagogicalEntry,
)

from .assets import GLOBAL_CACHE_DIR, AudioAssetRegistry
from .tts import TTSCache, TTSResult, _cache_key
from .utils import normalize_unicode

ASSET_CONTRACT_VERSION = "1.0.0"


class AssetAvailabilityClass(str, Enum):
    """Classification of an AudioAssetRequirement against the inventory."""

    AVAILABLE_VALID = "available_valid"
    AVAILABLE_UNREVIEWED = "available_unreviewed"
    MISSING_SYNTHESIZABLE = "missing_synthesizable"
    MISSING_NOT_SYNTHESIZABLE = "missing_not_synthesizable"
    INVALID_METADATA = "invalid_metadata"
    CHECKSUM_MISMATCH = "checksum_mismatch"
    INCOMPATIBLE_PROFILE = "incompatible_profile"
    INCOMPATIBLE_FORMAT = "incompatible_format"
    LEGACY_UNVERSIONED = "legacy_unversioned"
    REJECTED = "rejected"


@dataclass(frozen=True)
class AudioAssetRequirement:
    """A single required audio asset derived from a specification entry."""

    asset_id: str
    asset_contract_version: str
    verb_id: str
    entry_id: str
    section: GrammaticalSection
    sequence_index: int
    asset_kind: AssetKind
    language: str
    locale: str
    provider: str
    voice_id: str
    source_text: str
    tts_text: str
    expected_audio_format: str
    expected_sample_rate: int
    expected_channels: int
    synthesis_parameters: dict[str, Any]
    cache_key: str
    target_relative_path: str
    required_for_core_execution: bool
    human_audio_review_status: HumanAudioReviewStatus

    def to_dict(self) -> dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "asset_contract_version": self.asset_contract_version,
            "verb_id": self.verb_id,
            "entry_id": self.entry_id,
            "section": self.section.value,
            "sequence_index": self.sequence_index,
            "asset_kind": self.asset_kind.value,
            "language": self.language,
            "locale": self.locale,
            "provider": self.provider,
            "voice_id": self.voice_id,
            "source_text": self.source_text,
            "tts_text": self.tts_text,
            "expected_audio_format": self.expected_audio_format,
            "expected_sample_rate": self.expected_sample_rate,
            "expected_channels": self.expected_channels,
            "synthesis_parameters": self.synthesis_parameters,
            "cache_key": self.cache_key,
            "target_relative_path": self.target_relative_path,
            "required_for_core_execution": self.required_for_core_execution,
            "human_audio_review_status": self.human_audio_review_status.value,
        }


@dataclass
class AssetAvailabilityReport:
    """Result of classifying all requirements for a verb."""

    verb_id: str
    requirements: tuple[AudioAssetRequirement, ...]
    classifications: dict[str, AssetAvailabilityClass]
    available_valid: tuple[str, ...]
    available_unreviewed: tuple[str, ...]
    missing: tuple[str, ...]
    incompatible: tuple[str, ...]
    unreviewed: tuple[str, ...]
    blocking_reasons: tuple[str, ...]
    ready_for_core_execution: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "verb_id": self.verb_id,
            "requirements": [r.to_dict() for r in self.requirements],
            "classifications": {k: v.value for k, v in self.classifications.items()},
            "available_valid": list(self.available_valid),
            "available_unreviewed": list(self.available_unreviewed),
            "missing": list(self.missing),
            "incompatible": list(self.incompatible),
            "unreviewed": list(self.unreviewed),
            "blocking_reasons": list(self.blocking_reasons),
            "ready_for_core_execution": self.ready_for_core_execution,
        }


def _asset_id_for_entry(verb_id: str, entry: PedagogicalEntry, asset_kind: AssetKind) -> str:
    if asset_kind == AssetKind.ITALIAN_PROMPT:
        return f"it.{verb_id}.{entry.section.value}.{entry.entry_id}"
    return f"he.{verb_id}.{entry.section.value}.{entry.entry_id}"


def _section_order(section: GrammaticalSection) -> int:
    return {
        GrammaticalSection.INFINITIVE: 0,
        GrammaticalSection.PRESENT: 1,
        GrammaticalSection.PAST: 2,
        GrammaticalSection.FUTURE: 3,
        GrammaticalSection.IMPERATIVE: 4,
        GrammaticalSection.PAST_PARTICIPLE: 5,
        GrammaticalSection.NOT_APPLICABLE: 6,
    }.get(section, 7)


def _person_order(person: GrammaticalPerson) -> int:
    return {
        GrammaticalPerson.FIRST: 0,
        GrammaticalPerson.SECOND: 1,
        GrammaticalPerson.THIRD: 2,
        GrammaticalPerson.NOT_APPLICABLE: 3,
    }.get(person, 4)


def _gender_order(gender: GrammaticalGender) -> int:
    return {
        GrammaticalGender.MASCULINE: 0,
        GrammaticalGender.FEMININE: 1,
        GrammaticalGender.COMMON: 2,
        GrammaticalGender.NOT_APPLICABLE: 3,
    }.get(gender, 4)


def _number_order(number: GrammaticalNumber) -> int:
    return {
        GrammaticalNumber.SINGULAR: 0,
        GrammaticalNumber.PLURAL: 1,
        GrammaticalNumber.DUAL: 2,
        GrammaticalNumber.NOT_APPLICABLE: 3,
    }.get(number, 4)


def _role_order(role: EntryRole) -> int:
    return {
        EntryRole.CORE: 0,
        EntryRole.ALTERNATE: 1,
        EntryRole.REFERENCE: 2,
        EntryRole.REJECTED: 3,
    }.get(role, 4)


def _sorted_entries(spec: HebrewVerbSpecification) -> tuple[PedagogicalEntry, ...]:
    return tuple(
        sorted(
            spec.entries,
            key=lambda e: (
                _section_order(e.section),
                _person_order(e.person),
                _gender_order(e.gender),
                _number_order(e.number),
                _role_order(e.role),
                e.entry_id,
            ),
        )
    )


def _build_hebrew_requirement(
    spec: HebrewVerbSpecification,
    entry: PedagogicalEntry,
    sequence_index: int,
    profile: AudioProfile,
) -> AudioAssetRequirement:
    voice_id, locale = profile.voice_for("he")
    asset_id = _asset_id_for_entry(spec.verb_id, entry, AssetKind.TTS_INPUT)
    tts_text = entry.hebrew.tts_text
    cache_key = _cache_key(
        tts_text,
        profile.provider,
        voice_id,
        profile.synthesis_parameters.get("rate", 1.0),
        profile.synthesis_parameters.get("pitch", 0.0),
        profile.output_format,
        "",
        locale=locale,
    )
    return AudioAssetRequirement(
        asset_id=asset_id,
        asset_contract_version=ASSET_CONTRACT_VERSION,
        verb_id=spec.verb_id,
        entry_id=entry.entry_id,
        section=entry.section,
        sequence_index=sequence_index,
        asset_kind=AssetKind.TTS_INPUT,
        language="he",
        locale=locale,
        provider=profile.provider,
        voice_id=voice_id,
        source_text=entry.hebrew.source_text,
        tts_text=tts_text,
        expected_audio_format=profile.output_format,
        expected_sample_rate=profile.sample_rate,
        expected_channels=profile.channel_count,
        synthesis_parameters=profile.synthesis_parameters,
        cache_key=cache_key,
        target_relative_path=f"mantra_global_tts_cache/{cache_key}.wav",
        required_for_core_execution=(entry.role == EntryRole.CORE),
        human_audio_review_status=entry.human_audio_review_status,
    )


def _build_italian_requirement(
    spec: HebrewVerbSpecification,
    entry: PedagogicalEntry,
    sequence_index: int,
    profile: AudioProfile,
) -> AudioAssetRequirement | None:
    is_core_infinitive = entry.section == GrammaticalSection.INFINITIVE and entry.role == EntryRole.CORE
    if not is_core_infinitive:
        return None
    voice_id, locale = profile.voice_for("it")
    asset_id = _asset_id_for_entry(spec.verb_id, entry, AssetKind.ITALIAN_PROMPT)
    tts_text = entry.italian.text
    cache_key = _cache_key(
        tts_text,
        profile.provider,
        voice_id,
        profile.synthesis_parameters.get("rate", 1.0),
        profile.synthesis_parameters.get("pitch", 0.0),
        profile.output_format,
        "",
        locale=locale,
    )
    return AudioAssetRequirement(
        asset_id=asset_id,
        asset_contract_version=ASSET_CONTRACT_VERSION,
        verb_id=spec.verb_id,
        entry_id=entry.entry_id,
        section=entry.section,
        sequence_index=sequence_index,
        asset_kind=AssetKind.ITALIAN_PROMPT,
        language="it",
        locale=locale,
        provider=profile.provider,
        voice_id=voice_id,
        source_text=entry.italian.text,
        tts_text=tts_text,
        expected_audio_format=profile.output_format,
        expected_sample_rate=profile.sample_rate,
        expected_channels=profile.channel_count,
        synthesis_parameters=profile.synthesis_parameters,
        cache_key=cache_key,
        target_relative_path=f"mantra_global_tts_cache/{cache_key}.wav",
        required_for_core_execution=is_core_infinitive,
        human_audio_review_status=entry.human_audio_review_status,
    )


def build_asset_requirements(
    spec: HebrewVerbSpecification,
    audio_profile: AudioProfile,
) -> tuple[AudioAssetRequirement, ...]:
    """Return the deterministic ordered tuple of AudioAssetRequirements."""
    requirements: list[AudioAssetRequirement] = []
    sequence_index = 0
    for entry in _sorted_entries(spec):
        requirements.append(
            _build_hebrew_requirement(spec, entry, sequence_index, audio_profile)
        )
        sequence_index += 1
        italian_req = _build_italian_requirement(spec, entry, sequence_index, audio_profile)
        if italian_req is not None:
            requirements.append(italian_req)
            sequence_index += 1
    return tuple(requirements)


_ALLOWED_COMPACT_SECTIONS = frozenset({
    GrammaticalSection.INFINITIVE,
    GrammaticalSection.PRESENT,
    GrammaticalSection.PAST,
    GrammaticalSection.FUTURE,
    GrammaticalSection.IMPERATIVE,
})

_KIND_ORDER = {
    AssetKind.ITALIAN_PROMPT: 0,
    AssetKind.TTS_INPUT: 1,
}


def build_compact_mantra_requirements(
    spec: HebrewVerbSpecification,
    audio_profile: AudioProfile,
    *,
    include_italian_intro: bool = True,
) -> list[AudioAssetRequirement]:
    """Return the ordered AudioAssetRequirements for a compact mantra."""
    all_reqs = build_asset_requirements(spec, audio_profile)
    filtered: list[AudioAssetRequirement] = []
    for req in all_reqs:
        if req.section not in _ALLOWED_COMPACT_SECTIONS:
            continue
        if req.required_for_core_execution:
            filtered.append(req)
        elif include_italian_intro and req.asset_kind == AssetKind.ITALIAN_PROMPT and req.section == GrammaticalSection.INFINITIVE:
            filtered.append(req)
    filtered.sort(key=lambda r: (
        _section_order(r.section),
        _KIND_ORDER.get(r.asset_kind, 2),
        r.sequence_index,
    ))
    return filtered


class AudioAssetInventory:
    """Read-only inventory inspector for audio assets."""

    def __init__(
        self,
        registry: AudioAssetRegistry,
        audio_profile: AudioProfile,
        cache_dir: Path | None = None,
    ) -> None:
        self.registry = registry
        self.audio_profile = audio_profile
        self._cache = TTSCache(cache_dir or GLOBAL_CACHE_DIR)

    def _load_result(self, requirement: AudioAssetRequirement) -> TTSResult | None:
        asset = self.registry.get(requirement.asset_id)
        if asset is None:
            return None
        return self._cache.get(asset.cache_key)

    def _text_matches(self, cached_text: str, required_text: str) -> bool:
        if cached_text == required_text:
            return True
        return normalize_unicode(cached_text) == normalize_unicode(required_text)

    def _profiles_match(self, requirement: AudioAssetRequirement, result: TTSResult) -> bool:
        return (
            result.voice == requirement.voice_id
            and result.provider == requirement.provider
            and result.locale == requirement.locale
        )

    def _classify_present(
        self,
        requirement: AudioAssetRequirement,
        result: TTSResult,
    ) -> AssetAvailabilityClass:
        if not self._profiles_match(requirement, result):
            return AssetAvailabilityClass.INCOMPATIBLE_PROFILE
        if result.format != requirement.expected_audio_format:
            return AssetAvailabilityClass.INCOMPATIBLE_FORMAT
        if not self._text_matches(result.text, requirement.tts_text):
            return AssetAvailabilityClass.CHECKSUM_MISMATCH
        if requirement.human_audio_review_status != HumanAudioReviewStatus.APPROVED:
            return AssetAvailabilityClass.AVAILABLE_UNREVIEWED
        return AssetAvailabilityClass.AVAILABLE_VALID

    def classify(self, requirement: AudioAssetRequirement) -> AssetAvailabilityClass:
        """Classify a single requirement against the inventory."""
        if self.registry.get(requirement.asset_id) is None:
            if requirement.asset_kind in (AssetKind.TTS_INPUT, AssetKind.ITALIAN_PROMPT):
                return AssetAvailabilityClass.MISSING_SYNTHESIZABLE
            return AssetAvailabilityClass.MISSING_NOT_SYNTHESIZABLE

        result = self._load_result(requirement)
        if result is None:
            return AssetAvailabilityClass.INVALID_METADATA

        return self._classify_present(requirement, result)

    def inspect(
        self,
        requirements: tuple[AudioAssetRequirement, ...],
    ) -> AssetAvailabilityReport:
        """Inspect all requirements and return a typed report."""
        classifications: dict[str, AssetAvailabilityClass] = {}
        available_valid: list[str] = []
        available_unreviewed: list[str] = []
        missing: list[str] = []
        incompatible: list[str] = []
        unreviewed: list[str] = []
        blocking_reasons: list[str] = []

        for req in requirements:
            classification = self.classify(req)
            classifications[req.asset_id] = classification
            if classification == AssetAvailabilityClass.AVAILABLE_VALID:
                available_valid.append(req.asset_id)
            elif classification == AssetAvailabilityClass.AVAILABLE_UNREVIEWED:
                available_unreviewed.append(req.asset_id)
                unreviewed.append(req.asset_id)
                if req.required_for_core_execution:
                    blocking_reasons.append(
                        f"{req.asset_id}: unreviewed audio for core requirement"
                    )
            elif classification in (
                AssetAvailabilityClass.MISSING_SYNTHESIZABLE,
                AssetAvailabilityClass.MISSING_NOT_SYNTHESIZABLE,
            ):
                missing.append(req.asset_id)
                if req.required_for_core_execution:
                    blocking_reasons.append(f"{req.asset_id}: missing core asset")
            else:
                incompatible.append(req.asset_id)
                if req.required_for_core_execution:
                    blocking_reasons.append(f"{req.asset_id}: incompatible core asset")

        ready = not missing and not incompatible and not available_unreviewed and not blocking_reasons
        if not requirements:
            ready = False
            blocking_reasons.append("no_asset_requirements")

        return AssetAvailabilityReport(
            verb_id=requirements[0].verb_id if requirements else "",
            requirements=requirements,
            classifications=classifications,
            available_valid=tuple(available_valid),
            available_unreviewed=tuple(available_unreviewed),
            missing=tuple(missing),
            incompatible=tuple(incompatible),
            unreviewed=tuple(unreviewed),
            blocking_reasons=tuple(blocking_reasons),
            ready_for_core_execution=ready,
        )

