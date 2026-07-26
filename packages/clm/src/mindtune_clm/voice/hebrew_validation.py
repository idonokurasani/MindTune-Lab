"""Typed production validation exceptions for CLM-03B Hebrew reconciliation."""

from __future__ import annotations


class HebrewValidationError(Exception):
    """Base exception for validated Hebrew item failures."""


class UnresolvedMorphologyConflictError(HebrewValidationError):
    """Raised when a form has unresolved source conflicts."""


class MissingCanonicalHebrewError(HebrewValidationError):
    """Raised when canonical pointed Hebrew text is missing."""


class MalformedUnicodeError(HebrewValidationError):
    """Raised when Hebrew Unicode normalization is not stable."""


class InconsistentMorphologyError(HebrewValidationError):
    """Raised when lemma/root/binyan/gender/number fields disagree."""


class RejectedCurriculumError(HebrewValidationError):
    """Raised when a form is not approved for curriculum production."""


class UnvalidatedGeneratedFormError(HebrewValidationError):
    """Raised when a form has not passed linguistic validation."""


class PointingProvenanceError(HebrewValidationError):
    """Raised when pointing provenance is missing or unauthorized."""


class HumanReviewPendingError(HebrewValidationError):
    """Raised when human audio review is rejected or blocked."""
