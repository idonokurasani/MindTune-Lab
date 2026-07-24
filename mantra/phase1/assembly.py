"""Audio assembly: concatenate speech and silence segments into a WAV artifact."""
from __future__ import annotations

import io
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import numpy as np
from numpy.typing import NDArray

from .events import EventEmitter, MantraEventType
from .spec import MantraSpecification
from .timeline import SegmentType, TimelineSegment
from .tts import TTSCache, TTSProvider, TTSRuntimeError, _cache_key
from .utils import normalize_unicode


@dataclass
class AssemblyResult:
    """Result of assembling a mantra audio artifact."""

    output_path: Path
    manifest_path: Path
    events_path: Path
    segments_dir: Path
    total_duration: float
    sample_rate: int
    warnings: list[str]


def _resample_mono_int16(
    samples: NDArray[np.int16], source_rate: int, target_rate: int
) -> NDArray[np.int16]:
    """Resample a 1-D int16 mono array to a new sample rate."""
    if source_rate == target_rate:
        return samples
    old_len = len(samples)
    new_len = int(round(old_len * target_rate / source_rate))
    old_positions = np.linspace(0, old_len - 1, new_len)
    resampled = np.interp(old_positions, np.arange(old_len), samples)
    return cast(NDArray[np.int16], np.asarray(resampled, dtype=np.int16))


def _decode_wav_to_int16(wav_bytes: bytes) -> tuple[NDArray[np.int16], int]:
    """Decode WAV bytes into a mono int16 numpy array and its sample rate."""
    with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
        sample_rate = wf.getframerate()
        n_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        n_frames = wf.getnframes()
        raw = wf.readframes(n_frames)
    samples: NDArray[np.int16]
    if sampwidth == 1:
        # 8-bit PCM is unsigned; convert to int16 signed.
        samples = np.frombuffer(raw, dtype=np.uint8).astype(np.int16) - 128
        samples *= 256
    elif sampwidth == 2:
        samples = np.frombuffer(raw, dtype=np.int16).copy()
    elif sampwidth == 3:
        # 24-bit: pack into int32
        arr: NDArray[np.uint8] = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 3)
        packed = (arr[:, 2].astype(np.int32) << 16) | (arr[:, 1].astype(np.int32) << 8) | arr[:, 0]
        converted = (packed ^ 0x800000).astype(np.int32) - 0x800000
        samples = (converted // 256).astype(np.int16)
    elif sampwidth == 4:
        samples = (np.frombuffer(raw, dtype=np.int32) // 65536).astype(np.int16)
    else:
        raise TTSRuntimeError(f"Unsupported WAV sample width: {sampwidth}")
    if n_channels > 1:
        samples = samples.reshape(-1, n_channels).mean(axis=1).astype(np.int16)
    return samples, sample_rate


def _encode_int16_to_wav(samples: NDArray[np.int16], sample_rate: int) -> bytes:
    """Encode a 1-D int16 numpy array into WAV bytes."""
    if samples.dtype != np.int16:
        samples = samples.astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(samples.tobytes())
    return buf.getvalue()


def _silence_int16(duration: float, sample_rate: int) -> NDArray[np.int16]:
    """Return a silent int16 mono array."""
    length = int(round(duration * sample_rate))
    return np.zeros(length, dtype=np.int16)


def assemble_audio(
    spec: MantraSpecification,
    timeline: list[TimelineSegment],
    provider: TTSProvider,
    output_dir: Path,
    cache_dir: Path | None = None,
    events: EventEmitter | None = None,
    target_sample_rate: int = 22050,
) -> AssemblyResult:
    """Synthesize or cache all speech segments and assemble a single WAV file."""
    emitter = events or EventEmitter()
    output_dir.mkdir(parents=True, exist_ok=True)
    cache = TTSCache(cache_dir or output_dir / "cache")
    segments_dir = output_dir / "segments"
    segments_dir.mkdir(exist_ok=True)

    warnings: list[str] = []
    parts: list[NDArray[np.int16]] = []
    current_time = 0.0

    emitter.emit(
        MantraEventType.AUDIO_ASSEMBLED,
        {"status": "started", "output_dir": str(output_dir)},
    )

    for idx, segment in enumerate(timeline):
        if segment.segment_type in {
            SegmentType.OPENING_SILENCE,
            SegmentType.CLOSING_SILENCE,
            SegmentType.INTRA_FORM_SILENCE,
            SegmentType.INTER_FORM_SILENCE,
            SegmentType.GROUP_PAUSE,
            SegmentType.CYCLE_PAUSE,
            SegmentType.ITALIAN_CUE_PAUSE,
        }:
            duration = segment.planned_duration
            segment.actual_duration = duration
            segment.checksum = None
            segment.generation_status = "complete"
            segment.artifact_reference = None
            samples = _silence_int16(duration, target_sample_rate)
        else:
            text = normalize_unicode(segment.source_text) if segment.source_text else ""
            if not text:
                warnings.append(f"Segment {segment.segment_id} has empty source text; using silence")
                duration = 0.0
                segment.actual_duration = duration
                segment.generation_status = "skipped"
                samples = _silence_int16(duration, target_sample_rate)
                continue

            key = _cache_key(
                text,
                segment.provider,
                segment.voice,
                spec.speech.rate,
                spec.speech.pitch,
                spec.speech.format,
                segment.grammatical_metadata.get("pronunciation_override"),
            )

            emitter.emit(
                MantraEventType.SEGMENT_REQUESTED,
                {
                    "segment_id": segment.segment_id,
                    "segment_type": segment.segment_type.value,
                    "cache_key": key,
                },
            )

            cached = cache.get(key)
            if cached is not None:
                emitter.emit(
                    MantraEventType.SEGMENT_CACHE_HIT,
                    {
                        "segment_id": segment.segment_id,
                        "cache_key": key,
                        "duration": cached.duration,
                    },
                )
                result = cached
            else:
                try:
                    result = provider.synthesize(segment)
                except Exception as exc:
                    emitter.emit(
                        MantraEventType.SEGMENT_GENERATION_FAILED,
                        {
                            "segment_id": segment.segment_id,
                            "error": str(exc),
                        },
                    )
                    raise TTSRuntimeError(
                        f"Failed to synthesize segment {segment.segment_id}: {exc}"
                    ) from exc
                cache.put(key, result)
                emitter.emit(
                    MantraEventType.SEGMENT_GENERATED,
                    {
                        "segment_id": segment.segment_id,
                        "cache_key": key,
                        "duration": result.duration,
                        "sample_rate": result.sample_rate,
                    },
                )

            # Decode to int16 mono at target sample rate.
            samples, sr = _decode_wav_to_int16(result.audio_bytes)
            if sr != target_sample_rate:
                samples = _resample_mono_int16(samples, sr, target_sample_rate)

            segment.actual_duration = result.duration
            segment.checksum = result.checksum
            segment.generation_status = "complete"

            # Write per-segment WAV file for playback.
            seg_wav_path = segments_dir / f"{idx:04d}_{segment.segment_id}.wav"
            seg_wav_path.write_bytes(_encode_int16_to_wav(samples, target_sample_rate))
            segment.artifact_reference = str(seg_wav_path.relative_to(output_dir))

        parts.append(samples)
        segment.planned_start_time = current_time
        current_time += len(samples) / target_sample_rate

    combined = np.concatenate(parts) if parts else _silence_int16(0.0, target_sample_rate)
    output_wav = output_dir / "mantra.wav"
    tmp_wav = output_wav.with_suffix(".wav.tmp")
    tmp_wav.write_bytes(_encode_int16_to_wav(combined, target_sample_rate))
    tmp_wav.replace(output_wav)

    # Validate the resulting WAV
    with wave.open(str(output_wav), "rb") as wf:
        actual_channels = wf.getnchannels()
        actual_rate = wf.getframerate()
        actual_frames = wf.getnframes()
        actual_duration = actual_frames / actual_rate
        if actual_channels != 1:
            warnings.append(f"Output WAV has {actual_channels} channels; expected 1")
        if actual_rate != target_sample_rate:
            warnings.append(f"Output WAV sample rate {actual_rate}; expected {target_sample_rate}")

    emitter.emit(
        MantraEventType.AUDIO_ASSEMBLED,
        {
            "status": "complete",
            "output_path": str(output_wav),
            "duration": actual_duration,
            "sample_rate": actual_rate,
        },
    )

    return AssemblyResult(
        output_path=output_wav,
        manifest_path=output_dir / "manifest.json",
        events_path=output_dir / "events.jsonl",
        segments_dir=segments_dir,
        total_duration=actual_duration,
        sample_rate=actual_rate,
        warnings=warnings,
    )
