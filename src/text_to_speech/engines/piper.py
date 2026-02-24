"""Piper TTS engine implementation."""

import io
import os
import subprocess
import wave
from typing import AsyncGenerator, Optional

import numpy as np

from ..config import TTSConfig
from ..base import TTSEngine

_PIPER_BINARY = "/Library/Frameworks/Python.framework/Versions/3.12/bin/piper"

_VOICES = [
    "en_US_lessac_medium",
    "en_US_lessac_low",
    "en_US_amy_medium",
    "en_US_ryan_medium",
    "en_US_ljspeech_medium",
    "en_US_libritts_medium",
]

_VOICE_DESCRIPTIONS = {
    "en_US_lessac_medium": "Lessac (Medium)",
    "en_US_lessac_low": "Lessac (Low - Fastest)",
    "en_US_amy_medium": "Amy (Female)",
    "en_US_ryan_medium": "Ryan (Male)",
    "en_US_ljspeech_medium": "LJ Speech (Female)",
    "en_US_libritts_medium": "LibriTTS (Female)",
}

_VOICE_PATHS = {
    "en_US_lessac_medium": "~/.cache/piper/en_US-lessac-medium.onnx",
    "en_US_lessac_low": "~/.cache/piper/en_US-lessac-low.onnx",
    "en_US_amy_medium": "~/.cache/piper/en_US-amy-medium.onnx",
    "en_US_ryan_medium": "~/.cache/piper/en_US-ryan-medium.onnx",
    "en_US_ljspeech_medium": "~/.cache/piper/en_US-ljspeech-medium.onnx",
    "en_US_libritts_medium": "~/.cache/piper/en_US-libritts-medium.onnx",
}


def _get_voice_path(voice_name: str) -> str:
    """Get the path to a voice model."""
    path = _VOICE_PATHS.get(voice_name)
    if path:
        return os.path.expanduser(path)
    return os.path.expanduser(_VOICE_PATHS["en_US_lessac_medium"])


class PiperEngine(TTSEngine):
    """TTS engine using Piper.

    Uses the piper command-line tool for fast CPU-based synthesis.
    """

    voices = _VOICES

    def __init__(self, config: Optional[TTSConfig] = None) -> None:
        self.config = config or TTSConfig()
        self._voice = self.config.voice_name
        # Validate voice exists
        if self._voice not in _VOICES:
            self._voice = "en_US_lessac_medium"

    @property
    def name(self) -> str:
        return "piper"

    @property
    def voice_descriptions(self) -> dict:
        return _VOICE_DESCRIPTIONS

    @property
    def sample_rate(self) -> int:
        return 16000

    def synthesize(self, text: str) -> np.ndarray:
        if not text or not text.strip():
            raise ValueError("Input text cannot be empty")

        voice_path = _get_voice_path(self._voice)
        
        if not os.path.exists(voice_path):
            raise FileNotFoundError(
                f"Piper voice model not found at {voice_path}. "
                "Please download from https://github.com/rhasspy/piper/releases"
            )

        try:
            process = subprocess.Popen(
                [_PIPER_BINARY, "--model", voice_path, "--output-file", "-"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=False,
            )
            
            stdout, stderr = process.communicate(input=text.encode('utf-8'))
            
            if process.returncode != 0:
                raise RuntimeError(f"Piper failed: {stderr.decode('utf-8', errors='replace')}")
            
            wav_io = io.BytesIO(stdout)
            with wave.open(wav_io, 'rb') as wav:
                frames = wav.readframes(wav.getnframes())
                audio = np.frombuffer(frames, dtype=np.int16)
                audio = audio.astype(np.float32) / 32768.0
            
            return audio

        except FileNotFoundError:
            raise RuntimeError(
                "Piper not found. Install with: pip install piper-tts"
            )

    async def synthesize_stream(self, text: str) -> AsyncGenerator[tuple[np.ndarray, int], None]:
        if not text or not text.strip():
            raise ValueError("Input text cannot be empty")

        audio = self.synthesize(text)
        yield audio, 16000
