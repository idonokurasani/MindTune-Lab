"""Versioned Hebrew immediate-recall content fixture.

Italian is the mediation language.  The fixture is small, deterministic, and
self-contained; no external resources are fetched at runtime.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from mpe.domains.hebrew.models import HebrewContentItem


FIXTURE_VERSION: str = "1.0.0"
FIXTURE_ID: str = "hebrew-immediate-recall-v1"


@dataclass(frozen=True)
class HebrewFixture:
    """Immutable Hebrew content fixture for a deterministic run."""

    fixture_id: str
    version: str
    items: tuple[HebrewContentItem, ...]
    source_note: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def item_by_id(self, content_item_id: str) -> HebrewContentItem | None:
        """Return the content item with the given id, or None."""
        for item in self.items:
            if item.content_item_id == content_item_id:
                return item
        return None


def _item(
    item_id: str,
    italian: str,
    hebrew: str,
    accepted: tuple[str, ...],
    transliteration: str | None = None,
    source: str = "mindtune_console local test fixture",
) -> HebrewContentItem:
    """Build one fixture item with explicit provenance."""
    return HebrewContentItem(
        content_item_id=item_id,
        hebrew_target=hebrew,
        accepted_answers=accepted,
        italian_cue=italian,
        transliteration=transliteration,
        source_reference=source,
        content_version=FIXTURE_VERSION,
    )


def make_hebrew_immediate_recall_fixture() -> HebrewFixture:
    """Return the versioned Hebrew immediate-recall fixture.

    The fixture contains eight simple modern-Hebrew items.  They are selected
    to exercise correct answers, incorrect answers, omitted answers,
    whitespace/Unicode normalisation, and accepted variants.
    """
    items: tuple[HebrewContentItem, ...] = (
        _item(
            item_id="he.word.house",
            italian="casa",
            hebrew="בית",
            accepted=("בית", "בַּיִת"),
            transliteration="bayit",
        ),
        _item(
            item_id="he.word.water",
            italian="acqua",
            hebrew="מים",
            accepted=("מים", "מַיִם"),
            transliteration="mayim",
        ),
        _item(
            item_id="he.word.book",
            italian="libro",
            hebrew="ספר",
            accepted=("ספר", "סֵפֶר"),
            transliteration="sefer",
        ),
        _item(
            item_id="he.word.tree",
            italian="albero",
            hebrew="עץ",
            accepted=("עץ", "עֵץ"),
            transliteration="etz",
        ),
        _item(
            item_id="he.word.sun",
            italian="sole",
            hebrew="שמש",
            accepted=("שמש", "שֶׁמֶשׁ"),
            transliteration="shemesh",
        ),
        _item(
            item_id="he.word.moon",
            italian="luna",
            hebrew="ירח",
            accepted=("ירח", "יָרֵחַ"),
            transliteration="yareach",
        ),
        _item(
            item_id="he.word.hello",
            italian="ciao",
            hebrew="שלום",
            accepted=("שלום", "שָׁלוֹם"),
            transliteration="shalom",
        ),
        _item(
            item_id="he.word.love",
            italian="amore",
            hebrew="אהבה",
            accepted=("אהבה", "אַהֲבָה"),
            transliteration="ahava",
        ),
        _item(
            item_id="he.word.friend",
            italian="amico",
            hebrew="חבר",
            accepted=("חבר", "חָבֵר"),
            transliteration="chaver",
        ),
    )
    return HebrewFixture(
        fixture_id=FIXTURE_ID,
        version=FIXTURE_VERSION,
        items=items,
        source_note="Local test fixture for Phase 4D Hebrew immediate-recall vertical slice.",
        metadata={
            "language_pair": "it-he",
            "direction": "italian_cue_to_hebrew_target",
            "mediation_language": "it",
        },
    )
