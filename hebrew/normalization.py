"""Unicode and Hebrew orthographic normalization utilities."""

from __future__ import annotations

import re
import unicodedata


def normalize_unicode(text: str) -> str:
    """Apply NFC normalization to the whole string."""
    return unicodedata.normalize("NFC", text)


def decompose(text: str) -> str:
    """Decompose to NFD so base letters and combining marks are separated."""
    return unicodedata.normalize("NFD", text)


def is_niqqud(char: str) -> bool:
    """True for Hebrew combining points/cantillation marks."""
    return (
        "\u0591" <= char <= "\u05bd"
        or char in "\u05bf\u05c0\u05c1\u05c2\u05c3\u05c4\u05c5\u05c6\u05c7"
    )


def is_hebrew_letter(char: str) -> bool:
    return "\u0590" <= char <= "\u05ff" and not is_niqqud(char)


def strip_niqqud(text: str) -> str:
    """Remove all niqqud / cantillation marks but keep Hebrew letters."""
    return "".join(c for c in text if not is_niqqud(c))


def strip_maqaf(text: str) -> str:
    """Replace maqaf (Hebrew hyphen) with regular hyphen or space."""
    return text.replace("\u05be", " ")


def remove_mater_hints(text: str) -> str:
    """Remove ASCII apostrophes sometimes used to encode shin/sin hints."""
    return text.replace("'", "").replace("'", "")


def final_to_nonfinal(letter: str) -> str:
    """Map final Hebrew forms to their non-final counterparts."""
    final_map = {
        "\u05da": "\u05db",  # final kaf -> kaf
        "\u05dd": "\u05de",  # final mem -> mem
        "\u05df": "\u05e0",  # final nun -> nun
        "\u05e3": "\u05e4",  # final pe -> pe
        "\u05e5": "\u05e6",  # final tsadi -> tsadi
    }
    return final_map.get(letter, letter)


def nonfinal_to_final(letter: str) -> str:
    """Map non-final Hebrew forms to final forms."""
    final_map = {
        "\u05db": "\u05da",
        "\u05de": "\u05dd",
        "\u05e0": "\u05df",
        "\u05e4": "\u05e3",
        "\u05e6": "\u05e5",
    }
    return final_map.get(letter, letter)


def standard_unvocalized(vocalized: str) -> str:
    """Return standard unvocalized spelling with matres lectionis (ו, י).

    Heuristic: if a consonant carries an explicit HOLAM / QUBUTS point and is
    followed by another consonant, insert a ו between them.  וֹ / וּ are left
    unchanged.  This is intentionally conservative; exceptions should be handled
    by the central override layer.
    """
    chars = list(decompose(vocalized))
    n = len(chars)
    clusters: list[tuple[str, list[str], bool]] = []  # (base, marks, is_last)
    i = 0
    while i < n:
        c = chars[i]
        if not is_hebrew_letter(c):
            clusters.append((c, [], True))  # non-letter separator
            i += 1
            continue
        marks: list[str] = []
        j = i + 1
        while j < n and is_niqqud(chars[j]):
            marks.append(chars[j])
            j += 1
        # Determine whether this is the last Hebrew-letter cluster
        is_last = True
        k = j
        while k < n:
            if is_hebrew_letter(chars[k]):
                is_last = False
                break
            k += 1
        clusters.append((c, marks, is_last))
        i = j

    result: list[str] = []
    for idx, (base, marks, is_last) in enumerate(clusters):
        has_holam = "\u05b9" in marks
        has_qubuts = "\u05bb" in marks
        result.append(base)
        if not is_last and base not in "\u05d5\u05d9" and (has_holam or has_qubuts):
            result.append("\u05d5")

    return strip_niqqud("".join(result))


def normalize_hebrew(text: str) -> str:
    """Full normalization: NFC, maqaf replaced, extra spaces collapsed."""
    text = normalize_unicode(text)
    text = strip_maqaf(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def consonantal_skeleton(text: str) -> str:
    """Return consonants only (no vowel letters ו/י, no niqqud) for matching."""
    text = strip_niqqud(text)
    text = text.replace("\u05d5", "").replace("\u05d9", "")
    return text


def has_niqqud(text: str) -> bool:
    return any(is_niqqud(c) for c in text)


def has_final_letters(text: str) -> bool:
    final_letters = "\u05da\u05dd\u05df\u05e3\u05e5"
    return any(c in final_letters for c in text)
