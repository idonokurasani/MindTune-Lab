"""TTS adapter boundary, deterministic cache, and SpeechGen he-IL provider."""
from __future__ import annotations

import io
import json
import os
import struct
import urllib.error
import urllib.parse
import urllib.request
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from .timeline import TimelineSegment
from .utils import canonical_json, normalize_unicode, sha256_hex


class TTSRuntimeError(Exception):
    """Raised when TTS synthesis fails or returns an invalid artifact."""


@dataclass(frozen=True)
class TTSResult:
    """A synthesized speech segment result."""

    audio_bytes: bytes
    sample_rate: int
    duration: float
    provider: str
    voice: str
    text: str
    format: str
    checksum: str
    rate: float = 1.0
    pitch: float = 0.0

    def __post_init__(self) -> None:
        if not self.audio_bytes:
            raise TTSRuntimeError("TTSResult audio_bytes must not be empty")
        if self.duration <= 0.0:
            raise TTSRuntimeError("TTSResult duration must be positive")
        if self.sample_rate <= 0:
            raise TTSRuntimeError("TTSResult sample_rate must be positive")


@runtime_checkable
class TTSProvider(Protocol):
    """Protocol for a replaceable TTS provider."""

    name: str

    def synthesize(self, segment: TimelineSegment) -> TTSResult:
        """Synthesize the source text of a segment and return audio metadata."""
        ...


def _cache_key(
    text: str,
    provider: str,
    voice: str,
    rate: float,
    pitch: float,
    fmt: str,
    override: str | None,
) -> str:
    payload = {
        "text": normalize_unicode(text),
        "provider": provider,
        "voice": voice,
        "rate": rate,
        "pitch": pitch,
        "format": fmt,
        "override": override or "",
    }
    return sha256_hex(canonical_json(payload))


class TTSCache:
    """Deterministic on-disk cache for reusable speech segments."""

    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _paths(self, key: str) -> tuple[Path, Path]:
        return self.cache_dir / f"{key}.wav", self.cache_dir / f"{key}.meta.json"

    def get(self, key: str) -> TTSResult | None:
        wav_path, meta_path = self._paths(key)
        if not wav_path.exists() or not meta_path.exists():
            return None
        audio = wav_path.read_bytes()
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        return TTSResult(
            audio_bytes=audio,
            sample_rate=meta["sample_rate"],
            duration=meta["duration"],
            provider=meta["provider"],
            voice=meta["voice"],
            text=meta["text"],
            format=meta["format"],
            checksum=sha256_hex(audio),
            rate=meta.get("rate", 1.0),
            pitch=meta.get("pitch", 0.0),
        )

    def put(self, key: str, result: TTSResult) -> Path:
        wav_path, meta_path = self._paths(key)
        tmp_wav = wav_path.with_suffix(".wav.tmp")
        tmp_meta = meta_path.with_suffix(".json.tmp")
        tmp_wav.write_bytes(result.audio_bytes)
        meta = {
            "sample_rate": result.sample_rate,
            "duration": result.duration,
            "provider": result.provider,
            "voice": result.voice,
            "text": result.text,
            "format": result.format,
            "rate": result.rate,
            "pitch": result.pitch,
            "checksum": result.checksum,
        }
        tmp_meta.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp_wav.replace(wav_path)
        tmp_meta.replace(meta_path)
        return wav_path

    def cached_path(self, key: str) -> Path | None:
        wav_path, _ = self._paths(key)
        return wav_path if wav_path.exists() else None


class SpeechGenTTSProvider:
    """SpeechGen he-IL TTS provider.

    Reads credentials from environment:
      - SPEECHGEN_API_KEY (the API token)
      - SPEECHGEN_EMAIL (the account email)
      - SPEECHGEN_VOICE (optional; default "Avri")
      - SPEECHGEN_API_URL (optional; default "https://speechgen.io/index.php?r=api/text")
      - SPEECHGEN_SAMPLE_RATE (optional; default 22050)
      - SPEECHGEN_CHANNELS (optional; default 1)

    The /text endpoint returns a JSON job descriptor containing a `file`
    URL; this provider downloads the audio file from that URL, validates it
    as WAV, and returns a TTSResult.
    """

    name = "speechgen"

    def __init__(
        self,
        api_key: str | None = None,
        email: str | None = None,
        voice: str = "Avri",
        rate: float = 1.0,
        pitch: float = 0.0,
        fmt: str = "wav",
        sample_rate: int | None = None,
        channels: int | None = None,
        api_url: str | None = None,
    ):
        self.api_key = api_key or os.environ.get("SPEECHGEN_API_KEY") or os.environ.get("SPEECHGEN_TOKEN")
        self.email = email or os.environ.get("SPEECHGEN_EMAIL")
        self.voice = voice
        self.rate = rate
        self.pitch = pitch
        self.format = fmt
        self.sample_rate = sample_rate or int(os.environ.get("SPEECHGEN_SAMPLE_RATE", "22050"))
        self.channels = channels or int(os.environ.get("SPEECHGEN_CHANNELS", "1"))
        self.api_url = api_url or os.environ.get(
            "SPEECHGEN_API_URL",
            "https://speechgen.io/index.php?r=api/text",
        )

    def _require_credentials(self) -> None:
        missing: list[str] = []
        if not self.api_key:
            missing.append("SPEECHGEN_API_KEY")
        if not self.email:
            missing.append("SPEECHGEN_EMAIL")
        if missing:
            raise TTSRuntimeError(
                f"SpeechGen credentials missing: {', '.join(missing)}. "
                "Set them as environment variables."
            )

    def _request(
        self,
        url: str,
        data: bytes | None = None,
        headers: dict[str, str] | None = None,
        timeout: int = 120,
    ) -> tuple[int, str, bytes]:
        """Execute a single HTTP request and return (status, content_type, body)."""
        req = urllib.request.Request(url, data=data, headers=headers or {}, method="POST" if data else "GET")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return response.status, response.headers.get("Content-Type", ""), response.read()
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="ignore")[:2000]
            raise TTSRuntimeError(
                f"SpeechGen HTTP {exc.code} at {url}: {body}"
            ) from exc
        except urllib.error.URLError as exc:
            raise TTSRuntimeError(f"SpeechGen request to {url} failed: {exc.reason}") from exc

    def _safe_public_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Return a copy of the payload with credentials redacted."""
        return {k: v for k, v in payload.items() if k not in {"token", "email"}}

    def synthesize(self, segment: TimelineSegment) -> TTSResult:
        self._require_credentials()
        text = normalize_unicode(segment.source_text)
        voice = segment.voice or self.voice
        payload = {
            "token": self.api_key,
            "email": self.email,
            "voice": voice,
            "text": text,
            "format": self.format,
            "speed": self.rate,
            "pitch": self.pitch,
            "emotion": "good",
            "sample_rate": self.sample_rate,
            "channels": self.channels,
        }
        data = urllib.parse.urlencode(payload).encode("utf-8")
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        status, content_type, body = self._request(self.api_url, data, headers)

        if not body:
            raise TTSRuntimeError(
                f"SpeechGen returned an empty response at {self.api_url} "
                f"for segment {segment.segment_id}. "
                f"Parameters: {self._safe_public_payload(payload)}. "
                f"Retry may be safe for transient network errors."
            )

        if "application/json" not in content_type:
            raise TTSRuntimeError(
                f"SpeechGen returned unexpected content-type {content_type!r} "
                f"at {self.api_url} for segment {segment.segment_id}. "
                f"Retry is not safe unless the error is transient."
            )

        try:
            meta = json.loads(body)
        except json.JSONDecodeError as exc:
            raise TTSRuntimeError(
                f"SpeechGen returned non-JSON body at {self.api_url} for segment {segment.segment_id}: {exc}. "
                f"Body preview: {body[:500]!r}."
            ) from exc

        error_field = meta.get("error")
        if error_field:
            raise TTSRuntimeError(
                f"SpeechGen synthesis error for segment {segment.segment_id}: {error_field}. "
                f"Endpoint: {self.api_url}. "
                f"Parameters: {self._safe_public_payload(payload)}. "
                f"Retry is not safe for provider-reported errors."
            )

        file_url = meta.get("file") or meta.get("file_cors")
        if not file_url:
            raise TTSRuntimeError(
                f"SpeechGen response did not contain a download URL for segment {segment.segment_id}. "
                f"Response: {self._safe_public_payload(meta)}. "
                f"Endpoint: {self.api_url}."
            )

        audio_status, audio_content_type, audio_body = self._request(file_url, timeout=60)

        if not audio_body:
            raise TTSRuntimeError(
                f"SpeechGen audio download was empty for segment {segment.segment_id}. "
                f"Download URL: {file_url}. "
                f"Retry may be safe."
            )

        if "audio" not in audio_content_type and not audio_body.startswith(b"RIFF"):
            raise TTSRuntimeError(
                f"SpeechGen download for segment {segment.segment_id} is not audio "
                f"(content-type {audio_content_type!r}, body preview {audio_body[:200]!r}). "
                f"Retry may be safe for transient provider issues."
            )

        # Validate as WAV and compute duration/sample rate.
        try:
            sample_rate, duration = _wav_info_from_bytes(audio_body)
        except Exception as exc:
            raise TTSRuntimeError(
                f"SpeechGen response for segment {segment.segment_id} is not a valid WAV file: {exc}. "
                f"Download URL: {file_url}."
            ) from exc

        checksum = sha256_hex(audio_body)
        return TTSResult(
            audio_bytes=audio_body,
            sample_rate=sample_rate,
            duration=duration,
            provider=self.name,
            voice=voice,
            text=text,
            format=self.format,
            checksum=checksum,
            rate=self.rate,
            pitch=self.pitch,
        )


def _wav_info_from_bytes(data: bytes) -> tuple[int, float]:
    """Return (sample_rate, duration_seconds) from WAV bytes."""
    with wave.open(io.BytesIO(data), "rb") as wf:
        sample_rate = wf.getframerate()
        n_frames = wf.getnframes()
        if sample_rate == 0:
            raise TTSRuntimeError("WAV sample rate is zero")
        duration = n_frames / sample_rate
        return sample_rate, duration


class FakeTTSProvider:
    """Deterministic fake TTS provider for tests and offline demos.

    Generates a valid mono WAV with a short sine tone whose duration is
    derived deterministically from the input text length. This provider
    never touches the network and requires no credentials.
    """

    name = "fake"

    def __init__(self, sample_rate: int = 22050, base_duration: float = 0.05):
        self.sample_rate = sample_rate
        self.base_duration = base_duration

    def synthesize(self, segment: TimelineSegment) -> TTSResult:
        text = normalize_unicode(segment.source_text)
        duration = max(0.05, len(text) * self.base_duration)
        n_samples = int(round(self.sample_rate * duration))
        # Deterministic pseudo-sine at 440 Hz to keep audio content non-empty.
        import math

        audio = bytearray()
        for i in range(n_samples):
            sample = int(8000 * math.sin(2 * math.pi * 440 * i / self.sample_rate))
            audio.extend(struct.pack("<h", sample))
        audio_bytes = bytes(audio)
        # Wrap raw PCM in a WAV header.
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio_bytes)
        wav_bytes = buf.getvalue()
        checksum = sha256_hex(wav_bytes)
        return TTSResult(
            audio_bytes=wav_bytes,
            sample_rate=self.sample_rate,
            duration=duration,
            provider=self.name,
            voice=segment.voice or "fake",
            text=text,
            format="wav",
            checksum=checksum,
        )


def provider_for_segment(segment: TimelineSegment, spec_provider: str | None = None) -> str:
    """Return the provider name for a segment."""
    return segment.provider or spec_provider or "fake"
