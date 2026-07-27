"""Utility helpers for text normalization and phoneme processing."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path


def strip_niqqud(text: str) -> str:
    """Remove Hebrew niqqud / cantillation marks but keep Hebrew letters."""
    return "".join(
        c
        for c in text
        if not (
            "\u0591" <= c <= "\u05bd"
            or c in "\u05bf\u05c0\u05c1\u05c2\u05c3\u05c4\u05c5\u05c6\u05c7"
        )
    )


def _hebrew_base(c: str) -> bool:
    return "\u0590" <= c <= "\u05ff" and not _is_niqqud(c)


def _is_niqqud(c: str) -> bool:
    return (
        "\u0591" <= c <= "\u05bd" or c in "\u05bf\u05c0\u05c1\u05c2\u05c3\u05c4\u05c5\u05c6\u05c7"
    )


def standard_unvocalized(vocalized: str, chaser: str = "", hebrew_without_niqqud: str = "") -> str:
    """Return standard unvocalized spelling with matres lectionis (ו, י).

    Strategy:
    1. If Pealim's ``chaser`` hint exists and matches the consonantal skeleton,
       use it (it already contains the standard spelling).
    2. Otherwise derive from the vocalized string: insert a ו for HOLAM / QUBUTS
       points that appear on a consonant not already accompanied by a ו/י.
    """
    # Prefer chaser hint when it is the same form (same consonants ignoring maters)
    if chaser and "~" in chaser:
        candidate = chaser.split("~", 1)[-1].strip()
        candidate_clean = strip_niqqud(candidate).replace(" ", "").replace("ו", "").replace("י", "")
        base_clean = (
            strip_niqqud(hebrew_without_niqqud or vocalized)
            .replace(" ", "")
            .replace("ו", "")
            .replace("י", "")
        )
        if candidate_clean == base_clean and candidate_clean:
            return strip_niqqud(candidate)

    # Manual derivation from vocalized string
    result: list[str] = []
    i = 0
    chars = list(vocalized)
    n = len(chars)
    while i < n:
        c = chars[i]
        if not _hebrew_base(c):
            # pass through spaces, punctuation, etc.
            result.append(c)
            i += 1
            continue

        # gather combining marks following this base
        marks: list[str] = []
        j = i + 1
        while j < n and _is_niqqud(chars[j]):
            marks.append(chars[j])
            j += 1

        base = c
        has_holam = "\u05b9" in marks  # HOLAM point
        has_qubuts = "\u05bb" in marks  # QUBUTS point

        # If the base is a consonant (not vav/yod) and carries an o/u vowel point,
        # insert the mater vav before it. This covers forms like לִכְתֹּב -> לכתוב,
        # אֶכְתֹּב -> אכתוב, etc.
        if base not in "וי" and (has_holam or has_qubuts):
            result.append("ו")

        result.append(base)
        i = j

    # Strip any remaining points and normalize spaces
    text = "".join(result)
    text = strip_niqqud(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def transliteration_from_html(html_text: str) -> str:
    """Convert Pealim transcription HTML (with <b> stress marker) to plain text."""
    return re.sub(r"</?b>", "", html_text).strip()


def stress_from_phonemes(phonemes: str) -> int:
    """Return the 1-based stressed syllable index from a phonikud phoneme string.

    Phonikud marks primary stress with U+02C8 (ˈ). Count vowels before it.
    """
    if "ˈ" not in phonemes:
        return 0
    before, _ = phonemes.split("ˈ", 1)
    return len(re.findall(r"[aeiouAEIOU]", before)) + 1


def vocal_shva_in_phonemes(phonemes: str) -> bool:
    """Heuristic: a vocal shva is represented by a vowel in an unexpected position.

    This is intentionally conservative. The authoritative vocal-shva value comes
    from the manual override layer, not from this heuristic.
    """
    # A vocal shva in modern Hebrew often surfaces as /e/ or /a/ in phonikud output.
    # We keep this helper for cases where no override is present.
    return bool(re.search(r"[aeiou]", phonemes))


def load_json(path: Path) -> dict | list:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def wav_to_mp3(wav_path: Path, mp3_path: Path, q: int = 4) -> None:
    """Convert a WAV file to MP3 using ffmpeg."""
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(wav_path), "-q:a", str(q), str(mp3_path)],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
