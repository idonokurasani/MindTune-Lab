"""Domain-neutral deterministic fixture for the Immediate Recall vertical slice."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class FixtureAsset:
    """A version-pinned fixture media asset."""

    asset_id: str
    role: str
    media_handle: str
    version: str


@dataclass(frozen=True)
class FixtureItem:
    """A single item in the Immediate Recall fixture."""

    content_item_id: str
    expected_relation: str
    self_confirmation: str
    latency: float
    assets: dict[str, FixtureAsset] = field(default_factory=dict)
    eeg_load: float = 0.0
    eeg_quality_flags: list[str] = field(default_factory=list)
    # Optional typed-response value.  When provided, the runner treats the item
    # as a typed recall trial; otherwise it falls back to self-confirmation.
    typed_response: str | None = None
    response_mode: str = "touch"


@dataclass(frozen=True)
class ImmediateRecallFixture:
    """The minimal fixture definition for Immediate Recall."""

    fixture_id: str
    protocol_id: str
    protocol_version_id: str
    program_id: str
    program_version_id: str
    task_definition_id: str
    block_id: str
    block_type: str
    items: list[FixtureItem] = field(default_factory=list)

    def item_by_id(self, content_item_id: str) -> FixtureItem | None:
        """Return the fixture item with the given id, or None."""
        for item in self.items:
            if item.content_item_id == content_item_id:
                return item
        return None


def make_minimal_fixture() -> ImmediateRecallFixture:
    """Return the domain-neutral 'minimal' fixture.

    item.alpha produces a positive, fast self-confirmation (no repeat).
    item.beta produces a negative, slow self-confirmation that triggers one
    bounded repeat; on the repeat it is still negative, so the cap of 1 is
    reached and the item is marked unresolved.
    """
    alpha_prompt = FixtureAsset(
        asset_id="item.alpha.prompt",
        role="prompt",
        media_handle="fixture://item.alpha/prompt",
        version="v1.0.0",
    )
    alpha_confirmation = FixtureAsset(
        asset_id="item.alpha.confirmation",
        role="confirmation",
        media_handle="fixture://item.alpha/confirmation",
        version="v1.0.0",
    )
    beta_prompt = FixtureAsset(
        asset_id="item.beta.prompt",
        role="prompt",
        media_handle="fixture://item.beta/prompt",
        version="v1.0.0",
    )
    beta_confirmation = FixtureAsset(
        asset_id="item.beta.confirmation",
        role="confirmation",
        media_handle="fixture://item.beta/confirmation",
        version="v1.0.0",
    )

    return ImmediateRecallFixture(
        fixture_id="minimal",
        protocol_id="immediate-recall",
        protocol_version_id="immediate-recall-v1.0.0",
        program_id="immediate-recall-program",
        program_version_id="immediate-recall-program-v1.0.0",
        task_definition_id="immediate_recall_self_confirm",
        block_id="minimal-block",
        block_type="practice",
        items=[
            FixtureItem(
                content_item_id="item.alpha",
                expected_relation="associate(item.alpha.prompt, item.alpha.target)",
                self_confirmation="positive",
                latency=0.5,
                assets={
                    "prompt": alpha_prompt,
                    "confirmation": alpha_confirmation,
                },
            ),
            FixtureItem(
                content_item_id="item.beta",
                expected_relation="associate(item.beta.prompt, item.beta.target)",
                self_confirmation="negative",
                latency=5.0,
                assets={
                    "prompt": beta_prompt,
                    "confirmation": beta_confirmation,
                },
            ),
        ],
    )


@dataclass(frozen=True)
class AdaptationRule:
    """A single bounded adaptation rule for Immediate Recall."""

    repeat_cap: int
    latency_bound: float
    response_deadline: float = 10.0
    max_response_deadline: float = 20.0
    deadline_step: float = 0.5


def default_adaptation_rule() -> AdaptationRule:
    """Return the default bounded adaptation rule."""
    return AdaptationRule(repeat_cap=1, latency_bound=2.0)
