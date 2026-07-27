"""Per-occurrence Hebrew sheva (U+05B0) classification and TTS variants.

The classifier is intentionally conservative.  It uses explicit morphology rules,
an optional Phonikud G2P signal, and an optional manual lexicon, and falls back
to ``UNCERTAIN`` whenever the evidence is unclear.  Uncertain cases must be
reviewed before a sheva is used to select a production TTS variant.
"""

from __future__ import annotations

import enum
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .utils import normalize_unicode

SHEVA = "\u05b0"
DAGESH = "\u05bc"
# Includes all Hebrew letters, including final forms.
HEBREW_LETTERS = "".join(chr(c) for c in range(0x05D0, 0x05EB))
DIACRITICS = "".join(chr(c) for c in range(0x0591, 0x05C8))


class ShevaStatus(str, enum.Enum):
    VOCALIC = "vocalic"
    SILENT = "silent"
    UNCERTAIN = "uncertain"


class ShevaSource(str, enum.Enum):
    LEXICAL_DATA = "lexical_data"
    MORPHOLOGY_RULE = "morphology_rule"
    G2P = "g2p"
    MANUAL_OVERRIDE = "manual_override"


@dataclass(frozen=True)
class ShevaAnnotation:
    """A single sheva occurrence inside a Hebrew form."""

    base_letter_index: int
    grapheme_cluster_id: str
    status: ShevaStatus
    expected_phoneme: str
    source: ShevaSource
    review_status: str = "pending"
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "base_letter_index": self.base_letter_index,
            "grapheme_cluster_id": self.grapheme_cluster_id,
            "status": self.status.value,
            "expected_phoneme": self.expected_phoneme,
            "source": self.source.value,
            "review_status": self.review_status,
            "reason": self.reason,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ShevaAnnotation":
        return cls(
            base_letter_index=data["base_letter_index"],
            grapheme_cluster_id=data["grapheme_cluster_id"],
            status=ShevaStatus(data["status"]),
            expected_phoneme=data["expected_phoneme"],
            source=ShevaSource(data["source"]),
            review_status=data.get("review_status", "pending"),
            reason=data.get("reason", ""),
        )


def parse_grapheme_clusters(text: str) -> list[dict[str, Any]]:
    """Return Hebrew grapheme clusters: base letter + trailing diacritics."""
    normalized = normalize_unicode(text)
    clusters: list[dict[str, Any]] = []
    i = 0
    while i < len(normalized):
        ch = normalized[i]
        if ch in HEBREW_LETTERS:
            base = ch
            marks: list[str] = []
            j = i + 1
            while j < len(normalized) and normalized[j] in DIACRITICS:
                marks.append(normalized[j])
                j += 1
            clusters.append(
                {
                    "index": len(clusters),
                    "base": base,
                    "marks": "".join(marks),
                    "text": base + "".join(marks),
                }
            )
            i = j
        else:
            i += 1
    return clusters


def _has_full_vowel(marks: str) -> bool:
    """Return True if the cluster carries a non-sheva Hebrew vowel point."""
    for m in marks:
        if m == SHEVA:
            continue
        if "\u05b1" <= m <= "\u05bb" or m in {"\u05c1", "\u05c2"}:
            return True
    return False


def _phonikud_word_status(text: str) -> tuple[ShevaStatus | None, str]:
    """Return a low-confidence per-word sheva status from Phonikud, if available."""
    import importlib

    try:
        adapter = importlib.import_module("hebrew.adapters.phonikud_adapter")
        phonemize = adapter.phonemize
    except Exception:
        return None, "phonikud not installed"
    try:
        phonemes = phonemize(text)
    except Exception as exc:
        return None, f"phonikud failed: {exc}"
    # Phonikud does not explicitly mark vocal sheva.  A conservative signal:
    # if the returned IPA contains a short /e/ or /ɛ/ vowel, treat the word as
    # potentially containing a vocalic sheva; otherwise silent/ambiguous.
    lowered = phonemes.lower()
    if "e" in lowered or "ɛ" in lowered:
        return ShevaStatus.VOCALIC, phonemes
    return ShevaStatus.SILENT, phonemes


def _classify_one(
    clusters: list[dict[str, Any]],
    cluster_index: int,
    word_status: ShevaStatus | None,
) -> tuple[ShevaStatus, str, ShevaSource, str]:
    """Conservative morphology-rule classifier for one sheva occurrence."""
    prev = clusters[cluster_index - 1] if cluster_index > 0 else None
    nxt = clusters[cluster_index + 1] if cluster_index + 1 < len(clusters) else None

    # If Phonikud gives a clear per-word signal and this is the only sheva,
    # use it as a low-confidence hint only when morphology agrees.
    sheva_count = sum(1 for c in clusters if SHEVA in c["marks"])
    if word_status is not None and sheva_count == 1:
        # Accept Phonikud's single-sheva verdict when the morphology also points
        # in the same direction, otherwise remain uncertain.
        if word_status == ShevaStatus.VOCALIC and cluster_index == 0:
            return (
                ShevaStatus.VOCALIC,
                "e",
                ShevaSource.G2P,
                "phonikud and word-initial morphology agree on vocalic sheva",
            )
        if word_status == ShevaStatus.SILENT and prev and _has_full_vowel(prev["marks"]) and nxt:
            return (
                ShevaStatus.SILENT,
                "",
                ShevaSource.G2P,
                "phonikud and morphology agree on silent sheva",
            )

    # Word-initial sheva may be vocalic (e.g., initial "be-") or silent
    # (e.g., "ktavtem").  Keep it explicit and reviewable.
    if cluster_index == 0:
        return (
            ShevaStatus.UNCERTAIN,
            "",
            ShevaSource.MORPHOLOGY_RULE,
            "word-initial sheva may be vocalic or silent",
        )

    # If the next consonant carries a dagesh but no full vowel, the sheva may
    # be the short vowel that motivates the dagesh chazaq (gemination), or it
    # may be silent.  This is dialect-dependent and requires review.
    if nxt and DAGESH in nxt["marks"] and not _has_full_vowel(nxt["marks"]):
        return (
            ShevaStatus.UNCERTAIN,
            "",
            ShevaSource.MORPHOLOGY_RULE,
            "following dagesh without full vowel makes sheva dialect-dependent",
        )

    # Adjacent shevas are difficult to classify reliably from the surface form.
    adjacent_sheva = (prev is not None and SHEVA in prev["marks"]) or (
        nxt is not None and SHEVA in nxt["marks"]
    )
    if adjacent_sheva:
        return (
            ShevaStatus.UNCERTAIN,
            "",
            ShevaSource.MORPHOLOGY_RULE,
            "adjacent shevas require explicit review",
        )

    # The common case: a sheva follows a voweled consonant and precedes
    # another consonant.  It is normally silent (sheva nach), closing the
    # preceding syllable.
    if prev is not None and _has_full_vowel(prev["marks"]) and nxt is not None:
        return (
            ShevaStatus.SILENT,
            "",
            ShevaSource.MORPHOLOGY_RULE,
            "sheva follows a voweled consonant and precedes another consonant",
        )

    # A final sheva (or one with no following consonant) is silent.
    if nxt is None:
        return (
            ShevaStatus.SILENT,
            "",
            ShevaSource.MORPHOLOGY_RULE,
            "final sheva is silent",
        )

    return (
        ShevaStatus.UNCERTAIN,
        "",
        ShevaSource.MORPHOLOGY_RULE,
        "no clear morphology rule applies",
    )


def classify_shevas(
    text: str,
    lexicon: dict[str, list[ShevaAnnotation]] | None = None,
    use_phonikud: bool = False,
) -> list[ShevaAnnotation]:
    """Return a per-occurrence sheva annotation list for ``text``.

    ``lexicon`` maps a canonical NFC string to a list of pre-reviewed
    annotations.  If a matching entry exists, it wins.  Otherwise the
    function uses morphology rules, optionally supplemented by Phonikud when
    ``use_phonikud`` is True.
    """
    normalized = normalize_unicode(text)
    clusters = parse_grapheme_clusters(normalized)
    sheva_indices = [i for i, c in enumerate(clusters) if SHEVA in c["marks"]]
    if not sheva_indices:
        return []

    if lexicon and normalized in lexicon:
        return [
            ShevaAnnotation(
                base_letter_index=a.base_letter_index,
                grapheme_cluster_id=a.grapheme_cluster_id,
                status=a.status,
                expected_phoneme=a.expected_phoneme,
                source=ShevaSource.MANUAL_OVERRIDE,
                review_status=a.review_status,
                reason="manual lexicon override",
            )
            for a in lexicon[normalized]
        ]

    word_status: ShevaStatus | None = None
    if use_phonikud:
        word_status, _ = _phonikud_word_status(normalized)

    annotations: list[ShevaAnnotation] = []
    for cluster_index in sheva_indices:
        cluster = clusters[cluster_index]
        status, expected, source, reason = _classify_one(clusters, cluster_index, word_status)
        annotations.append(
            ShevaAnnotation(
                base_letter_index=cluster_index,
                grapheme_cluster_id=f"{cluster['base']}_{cluster_index}",
                status=status,
                expected_phoneme=expected,
                source=source,
                reason=reason,
            )
        )
    return annotations


def tts_variant(text: str, annotations: list[ShevaAnnotation], variant: str = "canonical") -> str:
    """Return a provider-specific TTS text for ``text``.

    Variants:
      - ``canonical``: the original fully-pointed text (variant A).
      - ``omit_silent``: remove sheva marks annotated as silent (variant B).
      - ``unpointed``: strip all Hebrew diacritics (variant C).
    """
    if variant == "canonical":
        return text

    normalized = normalize_unicode(text)
    if variant == "unpointed":
        return "".join(c for c in normalized if c not in DIACRITICS)

    if variant == "omit_silent":
        clusters = parse_grapheme_clusters(normalized)
        silent_indices = {
            a.base_letter_index for a in annotations if a.status == ShevaStatus.SILENT
        }
        result: list[str] = []
        for i, cluster in enumerate(clusters):
            if i in silent_indices:
                base = cluster["base"]
                marks = "".join(m for m in cluster["marks"] if m != SHEVA)
                result.append(base + marks)
            else:
                result.append(cluster["text"])
        return "".join(result)

    raise ValueError(f"unknown sheva TTS variant: {variant!r}")


def expected_phoneme(status: ShevaStatus) -> str:
    """Return the default expected phoneme for a sheva status."""
    if status == ShevaStatus.VOCALIC:
        return "e"
    if status == ShevaStatus.UNCERTAIN:
        return "?"
    return ""


def load_sheva_lexicon(path: Path | str) -> dict[str, list[ShevaAnnotation]]:
    """Load a JSON sheva lexicon mapping canonical text to annotations."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return {
        normalize_unicode(k): [ShevaAnnotation.from_dict(a) for a in v] for k, v in data.items()
    }


def save_sheva_lexicon(path: Path | str, lexicon: dict[str, list[ShevaAnnotation]]) -> None:
    """Save a sheva lexicon to JSON."""
    payload = {k: [a.to_dict() for a in v] for k, v in lexicon.items()}
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
