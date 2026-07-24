"""Typed errors for MPE v1.1 runtime."""

from __future__ import annotations


class MPEError(Exception):
    """Base class for all MPE runtime errors."""


class ValidationError(MPEError):
    """Raised when an event or payload fails validation."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class IllegalStateTransitionError(MPEError):
    """Raised when an event would cause an illegal state transition."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class EventOrderingError(MPEError):
    """Raised when event ordering constraints are violated."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class ConcurrencyError(MPEError):
    """Raised when optimistic concurrency checks fail."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class UnknownEventTypeError(MPEError):
    """Raised when an event type is not recognized."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class UnknownSchemaVersionError(MPEError):
    """Raised when an event schema version is not supported."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class ProviderFailureError(MPEError):
    """Raised when a provider fails to produce a valid result."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class ProviderTimeoutError(MPEError):
    """Raised when a provider does not respond within the configured timeout."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class ProviderNotFoundError(MPEError):
    """Raised when a required provider is not registered."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class UnsupportedProviderVersionError(MPEError):
    """Raised when a provider's declared version does not match the dependency."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class ProviderVersionMismatchError(MPEError):
    """Raised when a provider's declared version does not match the protocol dependency."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class ReplayError(MPEError):
    """Raised when deterministic replay fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
