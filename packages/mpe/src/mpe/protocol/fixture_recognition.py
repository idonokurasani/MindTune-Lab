"""Domain-neutral deterministic fixture for the Recognition comparative probe."""

from __future__ import annotations

from dataclasses import dataclass, field

from mpe.protocol.fixture_minimal import FixtureAsset


@dataclass(frozen=True)
class RecognitionFixtureItem:
    """A single Recognition item with deterministic choice outcomes."""

    content_item_id: str
    correct_choice_index: int
    selected_choice_index: int
    latency: float
    assets: dict[str, FixtureAsset] = field(default_factory=dict)


@dataclass(frozen=True)
class RecognitionFixture:
    """The minimal fixture definition for the Recognition probe."""

    fixture_id: str
    protocol_id: str
    protocol_version_id: str
    program_id: str
    program_version_id: str
    task_definition_id: str
    block_id: str
    block_type: str
    items: list[RecognitionFixtureItem] = field(default_factory=list)

    def item_by_id(self, content_item_id: str) -> RecognitionFixtureItem | None:
        """Return the fixture item with the given id, or None."""
        for item in self.items:
            if item.content_item_id == content_item_id:
                return item
        return None


def make_minimal_recognition_fixture() -> RecognitionFixture:
    """Return the domain-neutral 'minimal' Recognition fixture.

    item.alpha is answered correctly and quickly (no repeat).
    item.beta is answered incorrectly and slowly, triggering one bounded
    repeat; the repeated answer remains incorrect, so the cap of 1 is
    reached and the item is marked incorrect.
    """
    alpha_choice_0 = FixtureAsset(
        asset_id="item.alpha.choice_0",
        role="choice_0",
        media_handle="fixture://item.alpha/choice_0",
        version="v1.0.0",
    )
    alpha_choice_1 = FixtureAsset(
        asset_id="item.alpha.choice_1",
        role="choice_1",
        media_handle="fixture://item.alpha/choice_1",
        version="v1.0.0",
    )
    beta_choice_0 = FixtureAsset(
        asset_id="item.beta.choice_0",
        role="choice_0",
        media_handle="fixture://item.beta/choice_0",
        version="v1.0.0",
    )
    beta_choice_1 = FixtureAsset(
        asset_id="item.beta.choice_1",
        role="choice_1",
        media_handle="fixture://item.beta/choice_1",
        version="v1.0.0",
    )

    return RecognitionFixture(
        fixture_id="minimal-recognition",
        protocol_id="recognition",
        protocol_version_id="recognition-v1.0.0",
        program_id="recognition-program",
        program_version_id="recognition-program-v1.0.0",
        task_definition_id="recognition_discrete_choice",
        block_id="minimal-recognition-block",
        block_type="practice",
        items=[
            RecognitionFixtureItem(
                content_item_id="item.alpha",
                correct_choice_index=0,
                selected_choice_index=0,
                latency=0.5,
                assets={
                    "choice_0": alpha_choice_0,
                    "choice_1": alpha_choice_1,
                },
            ),
            RecognitionFixtureItem(
                content_item_id="item.beta",
                correct_choice_index=1,
                selected_choice_index=0,
                latency=5.0,
                assets={
                    "choice_0": beta_choice_0,
                    "choice_1": beta_choice_1,
                },
            ),
        ],
    )
