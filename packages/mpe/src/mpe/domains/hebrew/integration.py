"""Integration glue for running Hebrew immediate recall through the MPE runtime.

This module maps a ``HebrewFixture`` into the generic ``ImmediateRecallFixture``
and a Hebrew-aware provider set, then invokes the existing
``ImmediateRecallRunner`` unchanged.
"""

from __future__ import annotations

from mpe.domains.hebrew.adapter import HebrewDomainAdapter
from mpe.domains.hebrew.fixtures import HebrewFixture
from mpe.domains.hebrew.models import HebrewContentItem
from mpe.event_store import EventStore
from mpe.protocol.fixture_minimal import FixtureAsset, FixtureItem, ImmediateRecallFixture
from mpe.protocol.immediate_recall import run_immediate_recall_session
from mpe.protocol.providers_hebrew import HebrewFixtureProviderSet
from mpe.runtime import Clock
from mpe.types import SessionID


def _make_fixture_asset(item_id: str, role: str) -> FixtureAsset:
    return FixtureAsset(
        asset_id=f"{item_id}.{role}",
        role=role,
        media_handle=f"fixture://{item_id}/{role}",
        version="v1.0.0",
    )


def hebrew_fixture_to_immediate_recall_fixture(
    hebrew_fixture: HebrewFixture,
    typed_responses: dict[str, str] | None = None,
    eeg_overrides: dict[str, dict[str, object]] | None = None,
) -> ImmediateRecallFixture:
    """Convert a Hebrew fixture into the generic ImmediateRecallFixture shape.

    Each Hebrew content item becomes a typed-recall fixture item.  The typed
    response for each item is taken from ``typed_responses`` when supplied, or
    defaults to the expected Hebrew target.
    """
    items: list[FixtureItem] = []
    for item in hebrew_fixture.items:
        item_id = item.content_item_id
        typed = typed_responses.get(item_id, item.hebrew_target) if typed_responses else item.hebrew_target
        overrides = eeg_overrides.get(item_id, {}) if eeg_overrides else {}
        items.append(
            FixtureItem(
                content_item_id=item_id,
                expected_relation=f"italian_cue({item.italian_cue}) -> hebrew_target({item.hebrew_target})",
                self_confirmation="positive",
                typed_response=typed,
                response_mode="typed",
                latency=float(overrides.get("latency", 1.0)),
                eeg_load=float(overrides.get("eeg_load", 0.0)),
                eeg_quality_flags=list(overrides.get("eeg_quality_flags", [])),
                assets={
                    "prompt": _make_fixture_asset(item_id, "prompt"),
                    "confirmation": _make_fixture_asset(item_id, "confirmation"),
                },
            )
        )
    return ImmediateRecallFixture(
        fixture_id=hebrew_fixture.fixture_id,
        protocol_id="hebrew-immediate-recall",
        protocol_version_id="hebrew-immediate-recall-v1.0.0",
        program_id="mindtune-lab-hebrew",
        program_version_id="mindtune-lab-hebrew-v1.0.0",
        task_definition_id="hebrew_immediate_recall_typed",
        block_id="hebrew-block-001",
        block_type="practice",
        items=items,
    )


def run_hebrew_immediate_recall_session(
    store: EventStore,
    hebrew_fixture: HebrewFixture,
    typed_responses: dict[str, str] | None = None,
    eeg_overrides: dict[str, dict[str, object]] | None = None,
    learner_id: str = "learner_001",
    random_seed: str = "seed_0",
    session_id: SessionID | None = None,
    clock: Clock | None = None,
) -> tuple[ImmediateRecallFixture, object]:
    """Run a Hebrew immediate-recall session through the existing MPE runtime.

    Returns the generic fixture and the ``ImmediateRecallResult`` produced by
    the runner.  The result can be inspected for events, state, and outcomes.
    """
    fixture = hebrew_fixture_to_immediate_recall_fixture(
        hebrew_fixture,
        typed_responses=typed_responses,
        eeg_overrides=eeg_overrides,
    )
    provider_set = HebrewFixtureProviderSet(
        fixture=fixture,
        hebrew_fixture_items=list(hebrew_fixture.items),
    ).set
    return fixture, run_immediate_recall_session(
        store,
        fixture=fixture,
        learner_id=learner_id,
        random_seed=random_seed,
        session_id=session_id,
        clock=clock,
        provider_set=provider_set,
    )
