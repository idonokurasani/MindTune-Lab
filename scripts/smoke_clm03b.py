#!/usr/bin/env python3
"""Manual, non-CI smoke test for CLM-03B SpeechGen Giuseppe/Aaron.

Requires:
    export SPEECHGEN_API_KEY="..."
    export SPEECHGEN_EMAIL="..."

Usage:
    python scripts/smoke_clm03b.py
"""

from __future__ import annotations

import os
from pathlib import Path

from mindtune_clm.voice.cache import VoiceCache
from mindtune_clm.voice.fixture_clm03b import (
    hebrew_form_request,
    hebrew_sentence_request,
    italian_label_request,
)
from mindtune_clm.voice.speechgen import SpeechGenClient


def main() -> int:
    if not os.environ.get("SPEECHGEN_API_KEY") or not os.environ.get("SPEECHGEN_EMAIL"):
        print("SKIP: SPEECHGEN_API_KEY and SPEECHGEN_EMAIL not both set.")
        return 0

    cache_dir = Path("output/clm03b_smoke_cache")
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache = VoiceCache(cache_dir)
    client = SpeechGenClient()

    requests = [
        ("Italian (Giuseppe)", italian_label_request(), "it-IT", "Giuseppe"),
        ("Hebrew sentence (Aaron)", hebrew_sentence_request(), "he-IL", "Aaron"),
        ("Hebrew form (Aaron)", hebrew_form_request(), "he-IL", "Aaron"),
    ]

    print("=== CLM-03B Smoke Test ===")
    for label, req, locale, voice in requests:
        print(f"\n{label}")
        asset = client.synthesize(req, cache)
        print(f"  provider: {asset.provider}")
        print(f"  voice:    {asset.provider_voice_id}")
        print(f"  locale:   {asset.locale}")
        print(f"  duration: {asset.duration:.4f}s")
        print(f"  frames:   {asset.frame_count}")
        print(f"  provider audio checksum: {asset.provider_audio_checksum[:32]}")
        print(f"  canonical audio checksum: {asset.canonical_audio_checksum[:32]}")
        print(f"  cache key: {asset.cache_key[:32]}...")
        print(f"  review status: {asset.human_review_status}")
        assert asset.locale == locale, f"expected {locale}, got {asset.locale}"
        assert asset.provider_voice_id == voice, f"expected {voice}, got {asset.provider_voice_id}"
        assert asset.human_review_status == "pending"

    print("\n--- Second run (cache hits) ---")
    for label, req, _locale, _voice in requests:
        asset = client.synthesize(req, cache)
        print(f"{label}: cache hit, duration={asset.duration:.4f}s")

    print("\n=== Smoke test passed ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
