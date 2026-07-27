"""Engine-specific exceptions."""

from __future__ import annotations


class HebrewEngineError(Exception):
    """Base class for Hebrew engine errors."""


class ResourceNotFoundError(HebrewEngineError):
    """Raised when a requested linguistic resource is missing."""


class SourceConflictError(HebrewEngineError):
    """Raised when source evidence cannot be reconciled."""


class InflectorError(HebrewEngineError):
    """Raised when the Java Verb Inflector fails."""


class PronunciationError(HebrewEngineError):
    """Raised when phonemization or TTS fails."""


class ValidationError(HebrewEngineError):
    """Raised when answer validation cannot be performed."""
