from __future__ import annotations

import io
import json
import os
import sys
import unittest
import wave
from pathlib import Path
from unittest.mock import patch

CONSOLE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CONSOLE_DIR))

import azure_speech


def wav_bytes(seconds: float = 0.1) -> bytes:
    output = io.BytesIO()
    with wave.open(output, "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(16000)
        handle.writeframes(b"\x00\x00" * int(16000 * seconds))
    return output.getvalue()


class FakeResponse:
    def __init__(self, payload: dict):
        self.payload = payload
        self.headers = {"X-RequestId": "request-1"}

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self) -> bytes:
        return json.dumps(self.payload).encode()


class AzureSpeechTests(unittest.TestCase):
    def test_status_never_exposes_the_key(self) -> None:
        with patch.dict(os.environ, {
            "MINDTUNE_AZURE_SPEECH_KEY": "secret-value",
            "MINDTUNE_AZURE_SPEECH_REGION": "switzerlandnorth",
        }, clear=False):
            result = azure_speech.status()
        self.assertTrue(result["configured"])
        self.assertNotIn("secret-value", json.dumps(result))
        self.assertFalse(result["pronunciation_assessment_supported"])

    def test_transcription_uses_hebrew_and_labels_confidence_correctly(self) -> None:
        captured = {}

        def opener(request, timeout):
            captured["request"] = request
            captured["timeout"] = timeout
            return FakeResponse({
                "RecognitionStatus": "Success",
                "NBest": [{"Display": "אני כותב", "Confidence": 0.91}],
            })

        with patch.dict(os.environ, {
            "MINDTUNE_AZURE_SPEECH_KEY": "secret-value",
            "MINDTUNE_AZURE_SPEECH_REGION": "switzerlandnorth",
        }, clear=False):
            result = azure_speech.transcribe_wav(wav_bytes(), opener=opener)

        self.assertTrue(result["ok"])
        self.assertEqual(result["display_text"], "אני כותב")
        self.assertEqual(result["recognition_confidence"], 0.91)
        self.assertIsNone(result["pronunciation_score"])
        self.assertFalse(result["audio_retained"])
        self.assertIn("language=he-IL", captured["request"].full_url)
        self.assertEqual(captured["request"].headers["Ocp-apim-subscription-key"], "secret-value")

    def test_rejects_incompatible_audio(self) -> None:
        output = io.BytesIO()
        with wave.open(output, "wb") as handle:
            handle.setnchannels(2)
            handle.setsampwidth(2)
            handle.setframerate(44100)
            handle.writeframes(b"\x00\x00" * 100)
        with self.assertRaisesRegex(ValueError, "WAV PCM"):
            azure_speech.transcribe_wav(output.getvalue())


if __name__ == "__main__":
    unittest.main()
