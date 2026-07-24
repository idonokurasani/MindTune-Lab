#!/usr/bin/env python3
"""Generate MP3 audio from SSML files using Azure Speech TTS.

Usage:
    export MINDTUNE_AZURE_SPEECH_KEY="..."
    export MINDTUNE_AZURE_SPEECH_REGION="switzerlandnorth"  # optional
    python3 scripts/generate_mantra_audio.py [limit]
"""

from __future__ import annotations

import os
import sys
import time
import urllib.request
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
SSML_DIR = APP / "data" / "mantra" / "ssml"
AUDIO_DIR = APP / "data" / "mantra" / "audio"


def main() -> int:
    key = (os.environ.get("MINDTUNE_AZURE_SPEECH_KEY") or "").strip()
    region = (os.environ.get("MINDTUNE_AZURE_SPEECH_REGION") or "switzerlandnorth").strip()
    if not key:
        print("Error: MINDTUNE_AZURE_SPEECH_KEY is not set.")
        print("Set it to your Azure Speech subscription key and rerun.")
        return 1

    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    files = sorted(SSML_DIR.glob("*.xml"))
    if limit:
        files = files[:limit]

    AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    for ssml_path in files:
        out_path = AUDIO_DIR / ssml_path.with_suffix(".mp3").name
        ssml = ssml_path.read_text(encoding="utf-8")
        req = urllib.request.Request(
            f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1",
            data=ssml.encode("utf-8"),
            method="POST",
            headers={
                "Ocp-Apim-Subscription-Key": key,
                "Content-Type": "application/ssml+xml",
                "X-Microsoft-OutputFormat": "audio-16khz-128kbitrate-mono-mp3",
                "User-Agent": "MindTune-Lab-Mantra",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                out_path.write_bytes(resp.read())
            print(f"ok  -> {out_path}")
        except urllib.error.HTTPError as exc:
            print(f"err -> {ssml_path.name}: HTTP {exc.code} - {exc.read().decode('utf-8', errors='ignore')[:200]}")
        except Exception as exc:
            print(f"err -> {ssml_path.name}: {exc}")
        time.sleep(0.5)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
