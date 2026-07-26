"""Canonical CLM-03 audio conversion for SpeechGen output."""

from __future__ import annotations

import io
import math
import wave


def _resample_nearest(src: bytes, src_rate: int, dst_rate: int, channels: int, sample_width: int) -> bytes:
    """Resample raw PCM using nearest-neighbor, preserving mono/width."""
    if src_rate == dst_rate:
        return src

    if sample_width == 2:
        import array
        arr = array.array("h", src)
        ratio = src_rate / dst_rate
        n_frames = len(arr) // channels
        out_len = math.floor(n_frames * dst_rate / src_rate)
        out16 = array.array("h")
        for i in range(out_len):
            src_index = math.floor(i * ratio)
            for ch in range(channels):
                out16.append(arr[src_index * channels + ch])
        return out16.tobytes()

    # Generic byte-per-sample resample for 1/2/4 byte widths.
    ratio = src_rate / dst_rate
    n_frames = len(src) // (channels * sample_width)
    out_len = math.floor(n_frames * dst_rate / src_rate)
    out_bytes = bytearray(out_len * channels * sample_width)
    for i in range(out_len):
        src_index = math.floor(i * ratio)
        for ch in range(channels):
            for b in range(sample_width):
                out_bytes[(i * channels + ch) * sample_width + b] = src[
                    (src_index * channels + ch) * sample_width + b
                ]
    return bytes(out_bytes)


def _mono_from_stereo(src: bytes, sample_width: int) -> bytes:
    """Mix stereo interleaved PCM to mono."""
    if sample_width == 2:
        import array
        arr = array.array("h", src)
        out16 = array.array("h")
        for i in range(0, len(arr), 2):
            s = arr[i] + arr[i + 1]
            # clip
            if s > 32767:
                s = 32767
            if s < -32768:
                s = -32768
            out16.append(s)
        return out16.tobytes()

    # Generic byte-width mix not implemented for > 16 bit; assume mono or raise.
    raise CanonicalizeError("Only 16-bit stereo conversion is supported")


def parse_wav(wav_bytes: bytes) -> tuple[bytes, int, int, int]:
    """Parse WAV bytes into (pcm_bytes, sample_rate, sample_width, channels)."""
    try:
        with wave.open(io.BytesIO(wav_bytes), "rb") as handle:
            n_channels = handle.getnchannels()
            sample_width = handle.getsampwidth()
            sample_rate = handle.getframerate()
            n_frames = handle.getnframes()
            pcm = handle.readframes(n_frames)
            return pcm, sample_rate, sample_width, n_channels
    except wave.Error as exc:
        raise CanonicalizeError(f"WAV parse error: {exc}") from exc


def canonicalize_pcm(
    provider_bytes: bytes,
    target_rate: int = 16000,
    target_width: int = 2,
    target_channels: int = 1,
) -> tuple[bytes, int, int, int, int, float]:
    """Convert provider audio bytes to CLM-03 canonical PCM.

    Returns (pcm, sample_rate, sample_width, channels, frame_count, duration).
    """
    pcm, src_rate, sample_width, n_channels = parse_wav(provider_bytes)

    if sample_width != target_width and sample_width in (1, 2):
        # Convert to 16-bit PCM.
        if sample_width == 1:
            import array
            arr = array.array("B", pcm)
            out16 = array.array("h")
            for v in arr:
                out16.append(int((v - 128) / 127.0 * 32767))
            pcm = out16.tobytes()
            sample_width = target_width

    if sample_width != target_width:
        raise CanonicalizeError(f"Unsupported sample width {sample_width}; expected {target_width}")

    if n_channels == 2 and target_channels == 1:
        pcm = _mono_from_stereo(pcm, sample_width)
        n_channels = 1

    if src_rate != target_rate:
        pcm = _resample_nearest(pcm, src_rate, target_rate, n_channels, sample_width)

    frame_count = len(pcm) // (sample_width * n_channels)
    duration = frame_count / target_rate
    return pcm, target_rate, target_width, n_channels, frame_count, duration


def build_canonical_wav_bytes(
    pcm: bytes,
    sample_rate: int,
    sample_width: int,
    channels: int,
) -> bytes:
    """Build a deterministic WAV container from raw canonical PCM."""
    bio = io.BytesIO()
    with wave.open(bio, "wb") as handle:
        handle.setnchannels(channels)
        handle.setsampwidth(sample_width)
        handle.setframerate(sample_rate)
        handle.setnframes(len(pcm) // (sample_width * channels))
        handle.writeframes(pcm)
    return bio.getvalue()


class CanonicalizeError(Exception):
    """Raised when provider audio cannot be converted to the CLM-03 canonical format."""
