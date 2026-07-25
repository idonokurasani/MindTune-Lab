#!/usr/bin/env python3
"""Build the compact לְהִתְקַשֵּׁר mantra and shared Domino assets.

Uses the existing lehitkasher package cache plus a global shared cache.
Only synthesizes missing assets (merged plural forms, tense markers, and the
Italian infinitive translation).
"""
from __future__ import annotations

import json
import os
from functools import partial
from pathlib import Path
from typing import Any

from mantra.domain.audio_profile import AudioProfile
from mantra.phase1.assets import (
    ASSET_REGISTRY_PATH,
    AudioAssetRegistry,
    build_compact_mantra,
    domino_feedback_asset_id,
    ensure_tense_markers,
)

OUTPUT_DIR = Path("output/mantra_phase1_lehitkasher_hannah_full_niqqud")
COMPACT_WAV = OUTPUT_DIR / "compact_mantra.wav"
COMPACT_MANIFEST = OUTPUT_DIR / "compact_manifest.json"
COMPACT_INDEX = OUTPUT_DIR / "compact_index.html"
DOMINO_EXERCISES = OUTPUT_DIR / "domino_exercises.json"

ITALIAN_INFINITIVE = "telefonare"


def _metadata(tense: str, mood: str, **kwargs: Any) -> dict[str, Any]:
    return {"binyan": "Hitpa'el", "root": "ק-ש-ר", "tense": tense, "mood": mood, **kwargs}


def main() -> None:
    api_key = os.environ.get("SPEECHGEN_API_KEY")
    email = os.environ.get("SPEECHGEN_EMAIL")
    if not api_key or not email:
        raise SystemExit("SPEECHGEN_API_KEY and SPEECHGEN_EMAIL are required")

    profile = AudioProfile.load("hannah")
    he_voice, he_locale = profile.voice_for("he")
    it_voice, it_locale = profile.voice_for("it")

    registry = AudioAssetRegistry()
    ensure = partial(
        registry.ensure,
        voice=he_voice,
        locale=he_locale,
        api_key=api_key,
        email=email,
    )
    ensure_it = partial(
        registry.ensure,
        voice=it_voice,
        locale=it_locale,
        api_key=api_key,
        email=email,
    )

    # Migrate the lehitkasher package cache into the global shared cache.
    migrated = registry.migrate_package_cache(OUTPUT_DIR / "cache")
    print(f"Migrated {migrated} cache entries from lehitkasher package cache")

    # Italian infinitive translation (Giuseppe).
    ensure_it(
        asset_id="it.lehitkasher.infinitive",
        text=ITALIAN_INFINITIVE,
        **_metadata("infinitive", "infinitive"),
    )

    # Hebrew infinitive.
    ensure(
        asset_id="he.lehitkasher.infinitive",
        text="לְהִתְקַשֵּׁר",
        **_metadata("infinitive", "infinitive"),
    )

    # Present.
    present_forms = [
        ("ms", "מִתְקַשֵּׁר"),
        ("fs", "מִתְקַשֶּׁרֶת"),
        ("mp", "מִתְקַשְּׁרִים"),
        ("fp", "מִתְקַשְּׁרוֹת"),
    ]
    for key, text in present_forms:
        ensure(
            asset_id=f"he.lehitkasher.present.{key}",
            text=text,
            **_metadata("present", "participial", person="", number=key[1], gender="masculine" if key[0] == "m" else "feminine"),
        )

    # Past (3pl masculine/feminine merged).
    past_entries = [
        ("1sg", "אֲנִי הִתְקַשַּׁרְתִּי", "1", "singular", ""),
        ("2msg", "אַתָּה הִתְקַשַּׁרְתָּ", "2", "singular", "masculine"),
        ("2fsg", "אַתְּ הִתְקַשַּׁרְתְּ", "2", "singular", "feminine"),
        ("3msg", "הוּא הִתְקַשֵּׁר", "3", "singular", "masculine"),
        ("3fsg", "הִיא הִתְקַשְּׁרָה", "3", "singular", "feminine"),
        ("1pl", "אֲנַחְנוּ הִתְקַשַּׁרְנוּ", "1", "plural", ""),
        ("2mpl", "אַתֶּם הִתְקַשַּׁרְתֶּם", "2", "plural", "masculine"),
        ("2fpl", "אַתֶּן הִתְקַשַּׁרְתֶּן", "2", "plural", "feminine"),
        ("3pl", "הֵם וְהֵן הִתְקַשְּׁרוּ", "3", "plural", ""),
    ]
    for key, text, person, number, gender in past_entries:
        ensure(
            asset_id=f"he.lehitkasher.past.{key}",
            text=text,
            **_metadata("past", "indicative", person=person, number=number, gender=gender),
        )

    # Future (2pl and 3pl masculine/feminine merged).
    future_entries = [
        ("1sg", "אֲנִי אֶתְקַשֵּׁר", "1", "singular", ""),
        ("2msg", "אַתָּה תִּתְקַשֵּׁר", "2", "singular", "masculine"),
        ("2fsg", "אַתְּ תִּתְקַשְּׁרִי", "2", "singular", "feminine"),
        ("3msg", "הוּא יִתְקַשֵּׁר", "3", "singular", "masculine"),
        ("3fsg", "הִיא תִּתְקַשֵּׁר", "3", "singular", "feminine"),
        ("1pl", "אֲנַחְנוּ נִתְקַשֵּׁר", "1", "plural", ""),
        ("2pl", "אַתֶּם וְאַתֶּן תִּתְקַשְּׁרוּ", "2", "plural", ""),
        ("3pl", "הֵם וְהֵן יִתְקַשְּׁרוּ", "3", "plural", ""),
    ]
    for key, text, person, number, gender in future_entries:
        ensure(
            asset_id=f"he.lehitkasher.future.{key}",
            text=text,
            **_metadata("future", "indicative", person=person, number=number, gender=gender),
        )

    # Imperative.
    imperative_entries = [
        ("ms", "הִתְקַשֵּׁר", "masculine", "singular"),
        ("fs", "הִתְקַשְּׁרִי", "feminine", "singular"),
        ("pl", "הִתְקַשְּׁרוּ", "", "plural"),
    ]
    for key, text, gender, number in imperative_entries:
        ensure(
            asset_id=f"he.lehitkasher.imperative.{key}",
            text=text,
            **_metadata("imperative", "imperative", person="2", number=number, gender=gender),
        )

    # Global tense markers.
    ensure_tense_markers(
        registry,
        api_key=api_key,
        email=email,
        audio_profile=profile,
    )

    # Compact mantra sequence: Italian intro, then Hebrew only.
    sequence = [
        ("it.lehitkasher.infinitive", 0.7),
        ("he.lehitkasher.infinitive", 0.5),
        # present
        ("he.lehitkasher.present.ms", 0.25),
        ("he.lehitkasher.present.fs", 0.25),
        ("he.lehitkasher.present.mp", 0.25),
        ("he.lehitkasher.present.fp", 0.6),
        # past
        ("he.lehitkasher.past.1sg", 0.25),
        ("he.lehitkasher.past.2msg", 0.25),
        ("he.lehitkasher.past.2fsg", 0.25),
        ("he.lehitkasher.past.3msg", 0.25),
        ("he.lehitkasher.past.3fsg", 0.25),
        ("he.lehitkasher.past.1pl", 0.25),
        ("he.lehitkasher.past.2mpl", 0.25),
        ("he.lehitkasher.past.2fpl", 0.25),
        ("he.lehitkasher.past.3pl", 0.6),
        # future
        ("he.lehitkasher.future.1sg", 0.25),
        ("he.lehitkasher.future.2msg", 0.25),
        ("he.lehitkasher.future.2fsg", 0.25),
        ("he.lehitkasher.future.3msg", 0.25),
        ("he.lehitkasher.future.3fsg", 0.25),
        ("he.lehitkasher.future.1pl", 0.25),
        ("he.lehitkasher.future.2pl", 0.25),
        ("he.lehitkasher.future.3pl", 0.6),
        # imperative
        ("he.lehitkasher.imperative.ms", 0.25),
        ("he.lehitkasher.imperative.fs", 0.25),
        ("he.lehitkasher.imperative.pl", 0.0),
    ]

    compact_manifest = build_compact_mantra(registry, sequence, COMPACT_WAV, default_pause=0.3)
    compact_manifest["voice"] = he_voice
    compact_manifest["intro_voice"] = it_voice
    compact_manifest["asset_registry"] = str(ASSET_REGISTRY_PATH)
    COMPACT_MANIFEST.write_text(json.dumps(compact_manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    # Domino exercises: tense marker + target form.
    domino_items: list[dict[str, Any]] = []
    domino_targets = [
        ("past", "he.lehitkasher.past.1sg", "אֲנִי הִתְקַשַּׁרְתִּי"),
        ("past", "he.lehitkasher.past.2msg", "אַתָּה הִתְקַשַּׁרְתָּ"),
        ("past", "he.lehitkasher.past.2fsg", "אַתְּ הִתְקַשַּׁרְתְּ"),
        ("past", "he.lehitkasher.past.3msg", "הוּא הִתְקַשֵּׁר"),
        ("past", "he.lehitkasher.past.3fsg", "הִיא הִתְקַשְּׁרָה"),
        ("past", "he.lehitkasher.past.1pl", "אֲנַחְנוּ הִתְקַשַּׁרְנוּ"),
        ("past", "he.lehitkasher.past.2mpl", "אַתֶּם הִתְקַשַּׁרְתֶּם"),
        ("past", "he.lehitkasher.past.2fpl", "אַתֶּן הִתְקַשַּׁרְתֶּן"),
        ("past", "he.lehitkasher.past.3pl", "הֵם וְהֵן הִתְקַשְּׁרוּ"),
        ("present", "he.lehitkasher.present.ms", "מִתְקַשֵּׁר"),
        ("present", "he.lehitkasher.present.fs", "מִתְקַשֶּׁרֶת"),
        ("present", "he.lehitkasher.present.mp", "מִתְקַשְּׁרִים"),
        ("present", "he.lehitkasher.present.fp", "מִתְקַשְּׁרוֹת"),
        ("future", "he.lehitkasher.future.1sg", "אֲנִי אֶתְקַשֵּׁר"),
        ("future", "he.lehitkasher.future.2msg", "אַתָּה תִּתְקַשֵּׁר"),
        ("future", "he.lehitkasher.future.2fsg", "אַתְּ תִּתְקַשְּׁרִי"),
        ("future", "he.lehitkasher.future.3msg", "הוּא יִתְקַשֵּׁר"),
        ("future", "he.lehitkasher.future.3fsg", "הִיא תִּתְקַשֵּׁר"),
        ("future", "he.lehitkasher.future.1pl", "אֲנַחְנוּ נִתְקַשֵּׁר"),
        ("future", "he.lehitkasher.future.2pl", "אַתֶּם וְאַתֶּן תִּתְקַשְּׁרוּ"),
        ("future", "he.lehitkasher.future.3pl", "הֵם וְהֵן יִתְקַשְּׁרוּ"),
    ]
    for tense, target_id, target_text in domino_targets:
        domino_items.append(
            {
                "tense": tense,
                "tense_marker_asset_id": f"he.tense.{tense}",
                "tense_marker_text": {"past": "בֶּעָבָר", "present": "בַּהוֹוֶה", "future": "בֶּעָתִיד"}[tense],
                "target_asset_id": target_id,
                "target_text": target_text,
                "feedback_asset_id": domino_feedback_asset_id(target_id),
                "human_review_status": "pending",
            }
        )

    DOMINO_EXERCISES.write_text(json.dumps(domino_items, ensure_ascii=False, indent=2), encoding="utf-8")

    # HTML review page for compact mantra.
    html = [
        "<!DOCTYPE html>",
        "<html lang='en'><head><meta charset='utf-8'>",
        "<title>Compact Mantra — לְהִתְקַשֵּׁר</title>",
        "<style>",
        "body{font-family:system-ui,sans-serif;max-width:900px;margin:2rem auto;}",
        ".rtl{direction:rtl;unicode-bidi:plaintext;font-size:1.4rem;}",
        "table{border-collapse:collapse;width:100%;font-size:.9rem;}",
        "td,th{border:1px solid #ddd;padding:.4rem .6rem;text-align:left;}",
        "</style></head><body>",
        "<h1>Compact Mantra — לְהִתְקַשֵּׁר</h1>",
        f"<p>Italian intro: <strong>{it_voice}</strong> — '{ITALIAN_INFINITIVE}'</p>",
        f"<p>Hebrew voice: <strong>{he_voice}</strong></p>",
        "<p><audio controls src='compact_mantra.wav'></audio> (compact mantra)</p>",
        "<h2>Sequence</h2>",
        "<table><tr><th>#</th><th>asset_id</th><th>text</th><th>voice</th></tr>",
    ]
    for idx, (asset_id, _) in enumerate(sequence, 1):
        asset = registry.get(asset_id)
        text = asset.text if asset else ""
        voice = asset.voice if asset else ""
        html.append(f"<tr><td>{idx}</td><td>{asset_id}</td><td class='rtl'>{text}</td><td>{voice}</td></tr>")
    html.append("</table>")
    html.append("<h2>Domino exercises</h2>")
    html.append("<p>See <a href='domino_exercises.json'>domino_exercises.json</a></p>")
    html.append("</body></html>")
    COMPACT_INDEX.write_text("\n".join(html), encoding="utf-8")

    print(f"Compact mantra: {COMPACT_WAV}")
    print(f"Duration: {compact_manifest.get('duration', 0):.2f}s")
    print(f"Domino exercises: {DOMINO_EXERCISES}")
    print(f"Asset registry: {ASSET_REGISTRY_PATH}")


if __name__ == "__main__":
    main()
