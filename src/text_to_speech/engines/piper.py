"""Piper TTS engine implementation."""

import io
import os
import shutil
import subprocess
import wave
from pathlib import Path
from typing import AsyncGenerator, Optional

import numpy as np

from ..config import TTSConfig
from ..base import TTSEngine


def _get_piper_binary() -> str:
    """Find the piper binary path dynamically.
    
    Checks:
    1. Environment variable PIPER_BINARY
    2. In PATH via shutil.which
    3. Common macOS locations
    
    Returns:
        Path to piper binary
        
    Raises:
        FileNotFoundError: If piper is not found
    """
    # Check environment variable first
    env_path = os.environ.get("PIPER_BINARY")
    if env_path and os.path.isfile(env_path):
        return env_path
    
    # Try to find in PATH
    path_bin = shutil.which("piper")
    if path_bin:
        return path_bin
    
    # Check common macOS paths
    common_paths = [
        "/opt/homebrew/bin/piper",
        "/usr/local/bin/piper",
        "/Library/Frameworks/Python.framework/Versions/3.12/bin/piper",
    ]
    for p in common_paths:
        if os.path.isfile(p):
            return p
    
    raise FileNotFoundError(
        "Piper binary not found. Install with: brew install piper-tts or pip install piper-tts"
    )


_PIPER_BINARY = None

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
    "en_US_lessac_medium": "en/en_US/lessac/medium/en_US-lessac-medium.onnx",
    "en_US_lessac_low": "en/en_US/lessac/low/en_US-lessac-low.onnx",
    "en_US_amy_medium": "en/en_US/amy/medium/en_US-amy-medium.onnx",
    "en_US_ryan_medium": "en/en_US/ryan/medium/en_US-ryan-medium.onnx",
    "en_US_ljspeech_medium": "en/en_US/ljspeech/medium/en_US-ljspeech-medium.onnx",
    "en_US_libritts_medium": "en/en_US/libritts/medium/en_US-libritts-medium.onnx",
}


def _get_voice_path(voice_name: str) -> str:
    """Get the path to a voice model, downloading if needed."""
    path = _VOICE_PATHS.get(voice_name)
    if path:
        try:
            from huggingface_hub import hf_hub_download
            cached_path = hf_hub_download("rhasspy/piper-voices", path)
            # Also download the config file
            config_path = path.replace(".onnx", ".onnx.json")
            hf_hub_download("rhasspy/piper-voices", config_path)
            return cached_path
        except Exception as e:
            print(f"Error downloading {voice_name}: {e}")
    
    # Fallback to default
    try:
        from huggingface_hub import hf_hub_download
        default_path = "en/en_US/lessac/medium/en_US-lessac-medium.onnx"
        cached_path = hf_hub_download("rhasspy/piper-voices", default_path)
        hf_hub_download("rhasspy/piper-voices", default_path.replace(".onnx", ".onnx.json"))
        return cached_path
    except:
        pass
    
    raise FileNotFoundError(
        f"Piper voice model not found for {voice_name}. "
        "Please download from https://github.com/rhasspy/piper/releases"
    )


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
        piper_binary = _get_piper_binary()
        
        if not os.path.exists(voice_path):
            raise FileNotFoundError(
                f"Piper voice model not found at {voice_path}. "
                "Please download from https://github.com/rhasspy/piper/releases"
            )

        try:
            piper_cmd: list[str] = [piper_binary, "--model", voice_path, "--output-file", "-"]
            process = subprocess.Popen(
                piper_cmd,
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
