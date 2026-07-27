#!/usr/bin/env python3
"""Minimal Azure Speech adapter for Hebrew spoken responses.

The adapter performs short-audio speech recognition only. Azure currently
supports he-IL speech recognition, but not pronunciation assessment. The
returned confidence is recognition confidence and must never be presented as
a pronunciation score.
"""

from __future__ import annotations

import io
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
import wave
from typing import Any, Callable


LOCALE = "he-IL"
MAX_AUDIO_BYTES = 2_000_000
MAX_AUDIO_SECONDS = 30.0
REGION_RE = re.compile(r"^[a-z0-9]+$")


def configuration() -> dict[str, str]:
    return {
        "key": str(os.environ.get("MINDTUNE_AZURE_SPEECH_KEY") or "").strip(),
        "region": str(os.environ.get("MINDTUNE_AZURE_SPEECH_REGION") or "").strip().lower(),
        "resource_endpoint": str(os.environ.get("MINDTUNE_AZURE_SPEECH_ENDPOINT") or "").strip(),
    }


def status() -> dict[str, Any]:
    config = configuration()
    configured = bool(config["key"] and REGION_RE.fullmatch(config["region"]))
    return {
        "ok": True,
        "configured": configured,
        "provider": "azure_speech",
        "region": config["region"],
        "locale": LOCALE,
        "capability": "speech_recognition",
        "pronunciation_assessment_supported": False,
        "privacy": "audio_inviato ad Azure per la trascrizione e non conservato da MindTune Lab",
    }


def _validate_wav(audio: bytes) -> float:
    if not audio or len(audio) > MAX_AUDIO_BYTES:
        raise ValueError("audio assente o troppo grande")
    try:
        with wave.open(io.BytesIO(audio), "rb") as handle:
            channels = handle.getnchannels()
            width = handle.getsampwidth()
            rate = handle.getframerate()
            frames = handle.getnframes()
            compression = handle.getcomptype()
    except (EOFError, wave.Error) as exc:
        raise ValueError("WAV non valido") from exc
    if (channels, width, rate, compression) != (1, 2, 16000, "NONE"):
        raise ValueError("serve WAV PCM 16 bit, mono, 16 kHz")
    duration = frames / rate if rate else 0.0
    if duration <= 0 or duration > MAX_AUDIO_SECONDS:
        raise ValueError("durata audio non valida")
    return duration


def transcribe_wav(
    audio: bytes,
    *,
    opener: Callable[..., Any] = urllib.request.urlopen,
    timeout: float = 20.0,
) -> dict[str, Any]:
    duration = _validate_wav(audio)
    config = configuration()
    region = config["region"]
    if not config["key"] or not REGION_RE.fullmatch(region):
        raise ValueError("Azure Speech non configurato")
    query = urllib.parse.urlencode({"language": LOCALE, "format": "detailed"})
    url = (
        f"https://{region}.stt.speech.microsoft.com/"
        f"speech/recognition/conversation/cognitiveservices/v1?{query}"
    )
    request = urllib.request.Request(
        url,
        data=audio,
        method="POST",
        headers={
            "Ocp-Apim-Subscription-Key": config["key"],
            "Content-Type": "audio/wav; codecs=audio/pcm; samplerate=16000",
            "Accept": "application/json",
            "User-Agent": "MindTune-Lab/3.21.4",
        },
    )
    try:
        with opener(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
            request_id = str(
                response.headers.get("X-RequestId") or response.headers.get("X-Request-ID") or ""
            )
    except urllib.error.HTTPError as exc:
        message = (
            "autenticazione non valida"
            if exc.code in {401, 403}
            else f"servizio Azure non disponibile ({exc.code})"
        )
        raise RuntimeError(message) from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError("Azure Speech non raggiungibile") from exc
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("risposta Azure non valida") from exc

    status_value = str(payload.get("RecognitionStatus") or "")
    alternatives = payload.get("NBest") if isinstance(payload.get("NBest"), list) else []
    best = alternatives[0] if alternatives and isinstance(alternatives[0], dict) else {}
    text = str(
        best.get("Display") or best.get("Lexical") or payload.get("DisplayText") or ""
    ).strip()
    confidence = best.get("Confidence")
    try:
        confidence = round(float(confidence), 4) if confidence is not None else None
    except (TypeError, ValueError):
        confidence = None
    return {
        "ok": status_value == "Success" and bool(text),
        "provider": "azure_speech",
        "locale": LOCALE,
        "recognition_status": status_value or "Unknown",
        "display_text": text,
        "recognition_confidence": confidence,
        "duration_ms": round(duration * 1000),
        "request_id": request_id,
        "pronunciation_score": None,
        "audio_retained": False,
    }
