#!/usr/bin/env python3
"""Generate comparison audio for the three verb infinitives.

Engines:
- Azure from unvocalized Hebrew text
- Azure from Pealim-vocalized Hebrew text (SSML)
- phonikud-tts from manually corrected phonemes
- Mic Hebrew-TTS trial-direct API
"""
from __future__ import annotations

import base64
import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

import soundfile as sf
from piper_onnx import Piper

APP = Path(__file__).resolve().parents[1]
DATA = APP / "data" / "phonikud_eval"
AUDIO = DATA / "audio"
AUDIO.mkdir(parents=True, exist_ok=True)

AZURE_REGION = "switzerlandnorth"
AZURE_VOICE = "he-IL-HilaNeural"
AZURE_FORMAT = "audio-16khz-128kbitrate-mono-mp3"
MIC_BASE = "https://qcpghubyif.eu-west-1.awsapprunner.com"


def azure_key() -> str:
    key = os.environ.get("MINDTUNE_AZURE_SPEECH_KEY", "").strip()
    if not key:
        key = (
            subprocess.run(
                [
                    "security",
                    "find-generic-password",
                    "-s",
                    "local.biohacking.mindtunelab.azure-speech",
                    "-a",
                    "subscription-key",
                    "-w",
                ],
                capture_output=True,
                text=True,
                check=False,
            ).stdout.strip()
            or ""
        )
    return key


def azure_tts(ssml: str, out_path: Path) -> str:
    key = azure_key()
    if not key:
        return "skipped: no Azure key"
    req = urllib.request.Request(
        f"https://{AZURE_REGION}.tts.speech.microsoft.com/cognitiveservices/v1",
        data=ssml.encode("utf-8"),
        method="POST",
        headers={
            "Ocp-Apim-Subscription-Key": key,
            "Content-Type": "application/ssml+xml",
            "X-Microsoft-OutputFormat": AZURE_FORMAT,
            "User-Agent": "MindTune-Lab-Phonikud-Eval",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            out_path.write_bytes(resp.read())
        return f"generated: {out_path.name}"
    except urllib.error.HTTPError as exc:
        return f"error: HTTP {exc.code}"
    except Exception as exc:
        return f"error: {exc}"


def mic_tts(text: str, out_path: Path) -> str:
    body = json.dumps(
        {
            "text": text,
            "voice_name": "Orus",
            "style_instructions": "",
            "temperature": 1.2,
            "distinct_id": "",
            "session_id": "",
        },
        ensure_ascii=False,
    ).encode("utf-8")
    req = urllib.request.Request(
        f"{MIC_BASE}/api/tts/trial-direct",
        data=body,
        method="POST",
        headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        audio = base64.b64decode(payload["audio_base64"])
        wav_path = out_path.with_suffix(".wav")
        wav_path.write_bytes(audio)
        mp3_path = wav_to_mp3(wav_path)
        wav_path.unlink(missing_ok=True)
        return f"generated: {mp3_path.name}"
    except Exception as exc:
        return f"error: {exc}"


def wav_to_mp3(wav_path: Path) -> Path:
    mp3_path = wav_path.with_suffix(".mp3")
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(wav_path), "-q:a", "4", str(mp3_path)],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return mp3_path


def phonikud_tts(phonemes: str, out_path: Path) -> str:
    piper = Piper(
        str(APP / "data" / "phonikud_models" / "shaul.onnx"),
        str(APP / "data" / "phonikud_models" / "shaul.config.json"),
    )
    samples, sr = piper.create(phonemes, is_phonemes=True)
    wav_path = out_path.with_suffix(".wav")
    sf.write(wav_path, samples, sr)
    mp3_path = wav_to_mp3(wav_path)
    wav_path.unlink(missing_ok=True)
    return f"generated: {mp3_path.name}"


def main() -> int:
    rows = json.loads((DATA / "phonikud_evaluation.json").read_text(encoding="utf-8"))
    infinitives = [r for r in rows if r["form_key"] == "infinitive"]

    for row in infinitives:
        verb = row["verb"]
        vowelled = row["hebrew_with_niqqud"]
        unvowelled = row["hebrew_without_niqqud"]
        phonemes = row["manual_override"] or row["phonikud_phonemes"]

        # Azure unvocalized
        ssml_plain = f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="he-IL"><voice name="{AZURE_VOICE}">{unvowelled}</voice></speak>'
        status_plain = azure_tts(ssml_plain, AUDIO / f"azure_plain_{verb}.mp3")

        # Azure vocalized
        ssml_niqqud = f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="he-IL"><voice name="{AZURE_VOICE}">{vowelled}</voice></speak>'
        status_niqqud = azure_tts(ssml_niqqud, AUDIO / f"azure_vocalized_{verb}.mp3")

        # phonikud-tts
        status_phonikud = phonikud_tts(phonemes, AUDIO / f"phonikud_tts_{verb}.mp3")

        # Mic Hebrew-TTS (trial direct)
        status_mic = mic_tts(unvowelled, AUDIO / f"mic_hebrew_tts_{verb}.mp3")

        row["azure_status"] = f"plain={status_plain}; vocalized={status_niqqud}"
        row["phonikud_tts_status"] = status_phonikud
        row["mic_tts_status"] = status_mic
        print(verb, row["azure_status"], row["phonikud_tts_status"], row["mic_tts_status"])
        time.sleep(0.5)

    # Update JSON/CSV
    (DATA / "phonikud_evaluation.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    CSV = DATA / "phonikud_evaluation.csv"
    if CSV.exists():
        import csv

        # Re-read current CSV so we only update infinitive rows
        with CSV.open("r", encoding="utf-8", newline="") as fp:
            reader = csv.DictReader(fp)
            fieldnames = reader.fieldnames or []
            csv_rows = list(reader)
        for r in csv_rows:
            if r["form_key"] == "infinitive":
                for src in rows:
                    if src["verb"] == r["verb"] and src["form_key"] == "infinitive":
                        for col in ["azure_status", "phonikud_tts_status", "mic_tts_status"]:
                            if col in src:
                                r[col] = src[col]
                        break
        with CSV.open("w", encoding="utf-8", newline="") as fp:
            writer = csv.DictWriter(fp, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
