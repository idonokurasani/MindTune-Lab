"""Deterministic verb readiness evaluator.

Combines curriculum, specification, audio profile, and inventory into a typed
readiness report.  Distinguishes learner-execution eligibility from
asset-preparation eligibility.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from mantra.domain.audio_profile import AudioProfile
from mantra.domain.hebrew.specification import (
    EntryRole,
    HebrewVerbSpecification,
    LinguisticReviewStatus,
)
from mantra.domain.hebrew.specification_repository import (
    HebrewSpecificationError,
    HebrewSpecificationRepository,
)

from .asset_contract import (
    AssetAvailabilityClass,
    AssetAvailabilityReport,
    AudioAssetInventory,
    build_asset_requirements,
)
from .curriculum import CurriculumVerb


class LearnerExecutionEligibility(str, Enum):
    """Reason codes for learner-execution eligibility."""

    ELIGIBLE = "eligible"
    INELIGIBLE_MISSING_SPECIFICATION = "ineligible_missing_specification"
    INELIGIBLE_INVALID_SPECIFICATION = "ineligible_invalid_specification"
    INELIGIBLE_MISSING_ASSETS = "ineligible_missing_assets"
    INELIGIBLE_INCOMPATIBLE_ASSETS = "ineligible_incompatible_assets"
    INELIGIBLE_UNREVIEWED_AUDIO = "ineligible_unreviewed_audio"
    INELIGIBLE_UNREVIEWED_LINGUISTICS = "ineligible_unreviewed_linguistics"
    INELIGIBLE_CURRICULUM_ISSUE = "ineligible_curriculum_issue"


class AssetPreparationEligibility(str, Enum):
    """Reason codes for asset-preparation eligibility."""

    ELIGIBLE = "eligible"
    INELIGIBLE_MISSING_SPECIFICATION = "ineligible_missing_specification"
    INELIGIBLE_INVALID_SPECIFICATION = "ineligible_invalid_specification"
    INELIGIBLE_UNSYNTHESIZABLE_REQUIREMENT = "ineligible_unsynthesizable_requirement"
    INELIGIBLE_CURRICULUM_ISSUE = "ineligible_curriculum_issue"


@dataclass(frozen=True)
class VerbReadinessReport:
    """Readiness of a verb for learner execution and asset preparation."""

    verb_id: str
    learner_execution_eligibility: LearnerExecutionEligibility
    asset_preparation_eligibility: AssetPreparationEligibility
    learner_reasons: tuple[str, ...]
    preparation_reasons: tuple[str, ...]
    asset_report: AssetAvailabilityReport | None
    specification: HebrewVerbSpecification | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "verb_id": self.verb_id,
            "learner_execution_eligibility": self.learner_execution_eligibility.value,
            "asset_preparation_eligibility": self.asset_preparation_eligibility.value,
            "learner_reasons": list(self.learner_reasons),
            "preparation_reasons": list(self.preparation_reasons),
            "asset_report": self.asset_report.to_dict() if self.asset_report else None,
            "specification": self.specification.to_dict() if self.specification else None,
        }


class ReadinessEvaluator:
    """Convenience wrapper that evaluates readiness for a curriculum verb."""

    def __init__(
        self,
        specification_repository: HebrewSpecificationRepository,
        audio_profile: AudioProfile,
        asset_inventory: AudioAssetInventory,
    ) -> None:
        self.specification_repository = specification_repository
        self.audio_profile = audio_profile
        self.asset_inventory = asset_inventory

    def evaluate(
        self,
        curriculum_verb: CurriculumVerb,
        *,
        asset_preparation_mode: bool = False,
        curriculum_blocks_asset_generation: bool = False,
    ) -> VerbReadinessReport:
        """Return a readiness report for the given curriculum verb."""
        return evaluate_verb_readiness(
            curriculum_verb,
            self.specification_repository,
            self.audio_profile,
            self.asset_inventory,
            curriculum_blocks_asset_generation=curriculum_blocks_asset_generation,
        )


def _has_unreviewed_linguistics(spec: HebrewVerbSpecification) -> bool:
    return any(
        entry.linguistic_review_status != LinguisticReviewStatus.VERIFIED_CONSENSUS
        and entry.role != EntryRole.REJECTED
        for entry in spec.entries
    )


def _missing_has_unsynthesizable(
    asset_report: AssetAvailabilityReport,
) -> bool:
    return any(
        c == AssetAvailabilityClass.MISSING_NOT_SYNTHESIZABLE
        for c in asset_report.classifications.values()
    )


def _evaluate_assets(
    spec: HebrewVerbSpecification,
    audio_profile: AudioProfile,
    asset_inventory: AudioAssetInventory,
    learner_eligibility: LearnerExecutionEligibility,
) -> tuple[
    AssetAvailabilityReport,
    LearnerExecutionEligibility,
    list[str],
    AssetPreparationEligibility,
    list[str],
]:
    learner_reasons: list[str] = []
    preparation_reasons: list[str] = []

    requirements = build_asset_requirements(spec, audio_profile)
    asset_report = asset_inventory.inspect(requirements)

    if asset_report.missing:
        learner_reasons.append(f"missing_assets:{asset_report.missing}")
        if learner_eligibility == LearnerExecutionEligibility.ELIGIBLE:
            learner_eligibility = LearnerExecutionEligibility.INELIGIBLE_MISSING_ASSETS

    if asset_report.incompatible:
        learner_reasons.append(f"incompatible_assets:{asset_report.incompatible}")
        if learner_eligibility == LearnerExecutionEligibility.ELIGIBLE:
            learner_eligibility = LearnerExecutionEligibility.INELIGIBLE_INCOMPATIBLE_ASSETS

    if asset_report.available_unreviewed:
        learner_reasons.append(f"unreviewed_audio:{asset_report.available_unreviewed}")
        if learner_eligibility == LearnerExecutionEligibility.ELIGIBLE:
            learner_eligibility = LearnerExecutionEligibility.INELIGIBLE_UNREVIEWED_AUDIO

    if not requirements:
        preparation_eligibility = AssetPreparationEligibility.INELIGIBLE_UNSYNTHESIZABLE_REQUIREMENT
        preparation_reasons.append("no_asset_requirements")
    elif asset_report.incompatible and _missing_has_unsynthesizable(asset_report):
        preparation_eligibility = AssetPreparationEligibility.INELIGIBLE_UNSYNTHESIZABLE_REQUIREMENT
        preparation_reasons.append("missing_not_synthesizable_requirement")
    else:
        preparation_eligibility = AssetPreparationEligibility.ELIGIBLE

    return (
        asset_report,
        learner_eligibility,
        learner_reasons,
        preparation_eligibility,
        preparation_reasons,
    )


def _report_for_spec_error(verb_id: str, exc: HebrewSpecificationError) -> VerbReadinessReport:
    reason = f"specification_error:{exc}"
    return VerbReadinessReport(
        verb_id=verb_id,
        learner_execution_eligibility=LearnerExecutionEligibility.INELIGIBLE_MISSING_SPECIFICATION,
        asset_preparation_eligibility=AssetPreparationEligibility.INELIGIBLE_MISSING_SPECIFICATION,
        learner_reasons=(reason,),
        preparation_reasons=(reason,),
        asset_report=None,
        specification=None,
    )


def evaluate_verb_readiness(
    curriculum_verb: CurriculumVerb,
    specification_repository: HebrewSpecificationRepository,
    audio_profile: AudioProfile,
    asset_inventory: AudioAssetInventory,
    *,
    curriculum_blocks_asset_generation: bool = False,
) -> VerbReadinessReport:
    """Return a typed readiness report for a curriculum verb."""
    verb_id = curriculum_verb.verb_id

    if curriculum_blocks_asset_generation:
        return VerbReadinessReport(
            verb_id=verb_id,
            learner_execution_eligibility=LearnerExecutionEligibility.INELIGIBLE_CURRICULUM_ISSUE,
            asset_preparation_eligibility=AssetPreparationEligibility.INELIGIBLE_CURRICULUM_ISSUE,
            learner_reasons=("curriculum_entry_blocks_asset_generation",),
            preparation_reasons=("curriculum_entry_blocks_asset_generation",),
            asset_report=None,
            specification=None,
        )

    try:
        spec = specification_repository.get(verb_id)
    except HebrewSpecificationError as exc:
        return _report_for_spec_error(verb_id, exc)

    if _has_unreviewed_linguistics(spec):
        learner_eligibility = LearnerExecutionEligibility.INELIGIBLE_UNREVIEWED_LINGUISTICS
        learner_reasons = ["unreviewed_linguistic_content"]
    else:
        learner_eligibility = LearnerExecutionEligibility.ELIGIBLE
        learner_reasons = []

    (
        asset_report,
        learner_eligibility,
        learner_reasons,
        preparation_eligibility,
        preparation_reasons,
    ) = _evaluate_assets(spec, audio_profile, asset_inventory, learner_eligibility)

    return VerbReadinessReport(
        verb_id=verb_id,
        learner_execution_eligibility=learner_eligibility,
        asset_preparation_eligibility=preparation_eligibility,
        learner_reasons=tuple(learner_reasons),
        preparation_reasons=tuple(preparation_reasons),
        asset_report=asset_report,
        specification=spec,
    )
