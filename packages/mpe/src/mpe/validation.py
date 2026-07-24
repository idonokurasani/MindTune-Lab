"""Validation for events, identifiers, enums, ordering, and state transitions."""

from __future__ import annotations

from typing import Any

from mpe.enums import SESSION_TRANSITIONS, SessionStatus
from mpe.errors import (
    EventOrderingError,
    IllegalStateTransitionError,
    UnknownEventTypeError,
    UnknownSchemaVersionError,
    ValidationError,
)
from mpe.events import PAYLOAD_SCHEMAS, SUPPORTED_EVENT_TYPES, Event
from mpe.types import Identifier

SUPPORTED_SCHEMA_VERSIONS = frozenset({"1.1"})


def validate_event(event: Event, *, previous_events: list[Event] | None = None) -> None:
    """Validate an event envelope and payload.

    Raises typed ValidationError, UnknownEventTypeError, UnknownSchemaVersionError,
    or EventOrderingError.
    """
    if event.event_type not in SUPPORTED_EVENT_TYPES:
        raise UnknownEventTypeError(f"Unknown event_type: {event.event_type!r}")

    if event.schema_version not in SUPPORTED_SCHEMA_VERSIONS:
        raise UnknownSchemaVersionError(
            f"Unsupported schema_version: {event.schema_version!r} for {event.event_type}"
        )

    if event.session_sequence_number < 1:
        raise ValidationError("session_sequence_number must be >= 1")

    if previous_events:
        last = previous_events[-1]
        if event.session_sequence_number <= last.session_sequence_number:
            raise EventOrderingError(
                f"session_sequence_number {event.session_sequence_number} is not greater than "
                f"previous {last.session_sequence_number}"
            )
        if event.timestamp < last.timestamp:
            raise EventOrderingError(
                f"timestamp {event.timestamp} is earlier than previous {last.timestamp}"
            )
        _validate_provenance(event, previous_events)

    _validate_payload(event)


def _validate_provenance(event: Event, previous_events: list[Event]) -> None:
    known = {e.event_id for e in previous_events}
    for prov in event.provenance:
        if prov not in known:
            raise ValidationError(
                f"provenance event_id {prov!r} does not exist in session before this event"
            )
        # Causal ordering: provenance events must have lower sequence numbers.
        for prev in previous_events:
            if prev.event_id == prov and prev.session_sequence_number >= event.session_sequence_number:
                raise EventOrderingError(
                    f"provenance event {prov} has sequence {prev.session_sequence_number} "
                    f">= current {event.session_sequence_number}"
                )


def _validate_payload(event: Event) -> None:
    rules = PAYLOAD_SCHEMAS.get(event.event_type)
    if rules is None:
        # Event type is known but no detailed schema yet; envelope validation is enough.
        return

    for rule in rules:
        value = event.payload.get(rule.name)
        if rule.required and (value is None or value == ""):
            raise ValidationError(
                f"{event.event_type} payload missing required field: {rule.name!r}"
            )
        if value is None:
            continue
        _validate_field(event.event_type, rule, value)


def _validate_field(event_type: str, rule: Any, value: Any) -> None:
    kind = rule.kind
    if kind == "id":
        _check_id(event_type, rule.name, value)
    elif kind == "str":
        _check_str(event_type, rule.name, value)
    elif kind == "number":
        _check_number(event_type, rule.name, value)
    elif kind == "int":
        _check_int(event_type, rule.name, value)
    elif kind == "bool":
        _check_bool(event_type, rule.name, value)
    elif kind == "enum":
        assert rule.enum is not None
        rule.enum.validate(value)
    elif kind == "list":
        _check_list(event_type, rule, value)
    elif kind == "dict":
        _check_dict(event_type, rule.name, value)


def _check_id(event_type: str, name: str, value: Any) -> None:
    if not isinstance(value, str) or not value:
        raise ValidationError(
            f"{event_type}.{name} must be a non-empty string identifier"
        )


def _check_str(event_type: str, name: str, value: Any) -> None:
    if not isinstance(value, str):
        raise ValidationError(f"{event_type}.{name} must be a string")


def _check_number(event_type: str, name: str, value: Any) -> None:
    if not isinstance(value, (int, float)):
        raise ValidationError(f"{event_type}.{name} must be a number")


def _check_int(event_type: str, name: str, value: Any) -> None:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValidationError(f"{event_type}.{name} must be an integer")


def _check_bool(event_type: str, name: str, value: Any) -> None:
    if not isinstance(value, bool):
        raise ValidationError(f"{event_type}.{name} must be a boolean")


def _check_list(event_type: str, rule: Any, value: Any) -> None:
    if not isinstance(value, list):
        raise ValidationError(f"{event_type}.{rule.name} must be a list")
    for item in value:
        _validate_list_item(event_type, rule, item)


def _check_dict(event_type: str, name: str, value: Any) -> None:
    if not isinstance(value, dict):
        raise ValidationError(f"{event_type}.{name} must be a dict")


def _validate_list_item(event_type: str, rule: Any, item: Any) -> None:
    if rule.item_kind == "id":
        if not isinstance(item, str) or not item:
            raise ValidationError(
                f"{event_type}.{rule.name} items must be non-empty string identifiers"
            )
    elif rule.item_kind == "enum":
        assert rule.enum is not None
        rule.enum.validate(item)
    elif rule.item_kind == "str":
        if not isinstance(item, str):
            raise ValidationError(f"{event_type}.{rule.name} items must be strings")
    elif rule.item_kind == "any":
        pass


def validate_session_transition(
    current: SessionStatus | None,
    target: SessionStatus,
) -> None:
    """Validate a session status transition."""
    allowed = SESSION_TRANSITIONS.get(current, set())
    if target not in allowed:
        current_label = current.value if current else "<none>"
        raise IllegalStateTransitionError(
            f"Illegal session transition: {current_label} -> {target.value}"
        )


def validate_identifier_type(value: Any, expected: type[Identifier]) -> None:
    """Validate that a value is an Identifier of the expected type."""
    if not isinstance(value, expected):
        raise ValidationError(
            f"Expected {expected.__name__}, got {type(value).__name__}"
        )
