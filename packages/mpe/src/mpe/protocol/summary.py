"""Protocol summary derived exclusively from persisted Immediate Recall events."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from mpe.events import Event
from mpe.types import SessionID


@dataclass(frozen=True)
class ItemSummary:
    """Per-item summary derived from the event stream."""

    content_item_id: str
    self_confirmation: str | None
    latency: float | None
    repeats_used: int
    outcome: str
    completed: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "content_item_id": self.content_item_id,
            "self_confirmation": self.self_confirmation,
            "latency": self.latency,
            "repeats_used": self.repeats_used,
            "outcome": self.outcome,
            "completed": self.completed,
        }


@dataclass(frozen=True)
class ProtocolSummary:
    """Summary of an Immediate Recall session derived from events."""

    session_id: str
    protocol_id: str | None
    fixture_id: str | None
    status: str | None
    event_count: int
    item_count: int
    completed_item_count: int
    unresolved_count: int
    total_repeats: int
    items: list[ItemSummary] = field(default_factory=list)
    latency_bound: float | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "protocol_id": self.protocol_id,
            "fixture_id": self.fixture_id,
            "status": self.status,
            "event_count": self.event_count,
            "item_count": self.item_count,
            "completed_item_count": self.completed_item_count,
            "unresolved_count": self.unresolved_count,
            "total_repeats": self.total_repeats,
            "items": [item.as_dict() for item in self.items],
            "latency_bound": self.latency_bound,
        }


def _outcome_from(self_confirmation: str | None, repeats_used: int, cap: int) -> str:
    """Map a self-confirmation and repeat usage to a terminal outcome."""
    if self_confirmation is None:
        return "incomplete"
    if self_confirmation == "positive":
        return "positive"
    if self_confirmation == "negative":
        if repeats_used >= cap:
            return "unresolved"
        return "negative"
    return "unknown"


def derive_protocol_summary(  # noqa: C901
    events: list[Event],
    latency_bound: float | None = None,
    repeat_cap: int = 1,
) -> ProtocolSummary:
    """Derive an Immediate Recall protocol summary from a persisted event stream.

    The summary is computed entirely from events; no live state or side channel is
    consulted.  Deterministic event ordering is preserved by reading the stream
    in sequence order.
    """
    if not events:
        raise ValueError("Cannot derive summary from empty event stream")

    first = events[0]
    session_id = str(first.session_id)
    protocol_id: str | None = None
    fixture_id: str | None = None

    # Per-item state accumulated as we walk through events.
    item_state: dict[str, dict[str, Any]] = {}

    for event in events:
        payload = dict(event.payload)
        event_type = event.event_type

        if event_type == "session_started":
            # protocol_version_id is the best authoritative protocol identifier in this slice.
            protocol_id = str(event.protocol_version_id)
            start_params = payload.get("start_parameters") or {}
            fixture_id = start_params.get("fixture_id")

        elif event_type == "trial_created":
            item_id = _first_content_item_id(payload)
            if item_id:
                if item_id not in item_state:
                    item_state[item_id] = {
                        "self_confirmation": None,
                        "latency": None,
                        "repeats_used": 0,
                        "completed": False,
                    }
                # repeat_count is authoritative for this trial; for the first trial it is 0,
                # for the bounded repeat it is 1. It is carried on the trial directly.
                item_state[item_id]["repeats_used"] = payload.get("repeat_count", 0)

        elif event_type == "observation_received":
            item_id = _content_item_id_for_trial(event.trial_id, events)
            if item_id and item_id in item_state:
                raw_payload = payload.get("payload")
                if isinstance(raw_payload, str):
                    item_state[item_id]["self_confirmation"] = raw_payload
                # Latency proxy may be carried as an explicit observation field or payload key.
                latency = payload.get("latency")
                if latency is None and isinstance(raw_payload, dict):
                    latency = raw_payload.get("latency")
                if latency is not None:
                    try:
                        item_state[item_id]["latency"] = float(latency)
                    except (TypeError, ValueError):
                        pass

        elif event_type == "evaluation_completed":
            item_id = payload.get("expected_content_item_id")
            if item_id and item_id in item_state:
                # If the observation payload was missing, infer from answer_status.
                if item_state[item_id]["self_confirmation"] is None:
                    answer_status = payload.get("answer_status")
                    if answer_status == "correct":
                        item_state[item_id]["self_confirmation"] = "positive"
                    elif answer_status == "incorrect":
                        item_state[item_id]["self_confirmation"] = "negative"

        elif event_type == "feedback_completed":
            item_id = _content_item_id_for_trial(event.trial_id, events)
            if item_id and item_id in item_state:
                item_state[item_id]["completed"] = True

    items: list[ItemSummary] = []
    completed_count = 0
    unresolved_count = 0
    total_repeats = 0

    # Deterministic item ordering: sort by first appearance in the event stream.
    seen_order: list[str] = []
    for event in events:
        if event.event_type == "trial_created":
            item_id = _first_content_item_id(event.payload)
            if item_id and item_id not in seen_order:
                seen_order.append(item_id)

    for item_id in seen_order:
        state = item_state.get(item_id, {})
        repeats_used = int(state.get("repeats_used", 0))
        self_confirmation = state.get("self_confirmation")
        latency = state.get("latency")
        completed = bool(state.get("completed", False))
        if completed:
            completed_count += 1
        outcome = _outcome_from(self_confirmation, repeats_used, repeat_cap)
        if outcome == "unresolved":
            unresolved_count += 1
        total_repeats += repeats_used
        items.append(
            ItemSummary(
                content_item_id=item_id,
                self_confirmation=self_confirmation,
                latency=latency,
                repeats_used=repeats_used,
                outcome=outcome,
                completed=completed,
            )
        )

    status = events[-1].event_type if events else None
    if status != "session_completed":
        status = events[-1].event_type

    return ProtocolSummary(
        session_id=session_id,
        protocol_id=protocol_id,
        fixture_id=fixture_id,
        status=status,
        event_count=len(events),
        item_count=len(items),
        completed_item_count=completed_count,
        unresolved_count=unresolved_count,
        total_repeats=total_repeats,
        items=items,
        latency_bound=latency_bound,
    )


def summarize_session(
    session_id: SessionID,
    store: Any,
    latency_bound: float | None = None,
) -> ProtocolSummary:
    """Read a session from an event store and derive its Immediate Recall summary."""
    events = store.read(session_id)
    return derive_protocol_summary(events, latency_bound=latency_bound)


def _first_content_item_id(payload: dict[str, Any]) -> str | None:
    content_item_ids = payload.get("content_item_ids")
    if isinstance(content_item_ids, list) and content_item_ids:
        first = content_item_ids[0]
        if isinstance(first, str):
            return first
    return None


def _content_item_id_for_trial(trial_id: Any, events: list[Event]) -> str | None:
    """Locate the content_item_id associated with a trial_id by scanning events."""
    if trial_id is None:
        return None
    trial_id_str = str(trial_id)
    for event in events:
        if event.event_type == "trial_created" and event.payload.get("trial_id") == trial_id_str:
            return _first_content_item_id(event.payload)
    return None
