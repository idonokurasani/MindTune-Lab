"""Shared Piper / Phonikud-TTS adapter."""

from __future__ import annotations

from pathlib import Path
from typing import Tuple

import numpy as np
import soundfile as sf
from piper_onnx import Piper

from ..exceptions import PronunciationError


class PiperVoice:
    """Replaceable voice renderer. Only this class depends on Piper."""

    def __init__(self, model_path: Path, config_path: Path):
        self.model_path = model_path
        self.config_path = config_path
        self._piper: Piper | None = None

    def _get_piper(self) -> Piper:
        if self._piper is None:
            self._piper = Piper(str(self.model_path), str(self.config_path))
        return self._piper

    def synthesize(self, phonemes: str, is_phonemes: bool = True) -> Tuple[np.ndarray, int]:
        try:
            return self._get_piper().create(phonemes, is_phonemes=is_phonemes)
        except Exception as exc:
            raise PronunciationError(f"Piper synthesis failed: {exc}") from exc

    def synthesize_to_wav(self, phonemes: str, wav_path: Path, is_phonemes: bool = True) -> int:
        samples, sr = self.synthesize(phonemes, is_phonemes=is_phonemes)
        sf.write(wav_path, samples, sr)
        return sr


class PiperAdapter:
    """Higher-level Piper adapter with project paths and optional MP3 conversion."""

    def __init__(
        self,
        model_path: Path | None = None,
        config_path: Path | None = None,
    ):
        self.model_path = model_path or self._default_model_path()
        self.config_path = config_path or self._default_config_path()
        self.voice = PiperVoice(self.model_path, self.config_path)

    @staticmethod
    def _default_model_path() -> Path:
        return Path(__file__).resolve().parents[2] / "data" / "phonikud_models" / "shaul.onnx"

    @staticmethod
    def _default_config_path() -> Path:
        return (
            Path(__file__).resolve().parents[2] / "data" / "phonikud_models" / "shaul.config.json"
        )

    def render(
        self,
        phonemes: str,
        output_path: Path,
        to_mp3: bool = False,
    ) -> Path:
        import tempfile

        wav_path = output_path.with_suffix(".wav") if to_mp3 else output_path
        self.voice.synthesize_to_wav(phonemes, wav_path, is_phonemes=True)
        if to_mp3:
            import subprocess

            mp3_path = output_path.with_suffix(".mp3")
            subprocess.run(
                ["ffmpeg", "-y", "-i", str(wav_path), "-q:a", "4", str(mp3_path)],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            wav_path.unlink(missing_ok=True)
            return mp3_path
        return wav_path
