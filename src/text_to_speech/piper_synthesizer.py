"""Text-to-speech synthesizer using Piper TTS."""

import io
import os
import subprocess
import wave
from pathlib import Path
from typing import AsyncGenerator, Optional

import numpy as np

from .config import TTSConfig

_PIPER_BINARY = "/Library/Frameworks/Python.framework/Versions/3.12/bin/piper"

_PIPER_VOICES = {
    "en_US_lessac_medium": {
        "path": "~/.cache/piper/en_US-lessac-medium.onnx",
        "description": "English US, Lessac, Medium quality",
    },
    "en_US_lessac_low": {
        "path": "~/.cache/piper/en_US-lessac-low.onnx",
        "description": "English US, Lessac, Low quality (faster)",
    },
}

_DEFAULT_VOICE = "en_US_lessac_medium"


def _get_voice_path(voice_name: str) -> str:
    """Get the path to a voice model."""
    voice_info = _PIPER_VOICES.get(voice_name)
    if voice_info:
        return os.path.expanduser(voice_info["path"])
    
    # Default to the first available voice
    default = _PIPER_VOICES[_DEFAULT_VOICE]
    return os.path.expanduser(default["path"])


class Synthesizer:
    """TTS synthesizer using Piper.

    Uses the piper command-line tool for fast CPU-based synthesis.
    """

    def __init__(self, config: Optional[TTSConfig] = None) -> None:
        """Initialize synthesizer with TTS configuration.

        Args:
            config: TTS configuration. Uses defaults if None.
        """
        self.config = config or TTSConfig()
        
        # Map config voice_name to piper voice
        self._voice_name = getattr(self.config, 'voice_name', 'af_heart')
        self._piper_voice = self._map_kokoro_to_piper(self._voice_name)

    def _map_kokoro_to_piper(self, kokoro_voice: str) -> str:
        """Map Kokoro voice names to Piper voice names."""
        mapping = {
            # Female voices
            "af_bella": "en_US_lessac_medium",
            "af_heart": "en_US_lessac_medium", 
            "af_sarah": "en_US_lessac_medium",
            "af_sky": "en_US_lessac_medium",
            # Male voices - use lower quality for speed
            "am_adam": "en_US_lessac_low",
            "am_michael": "en_US_lessac_low",
            # British voices
            "bf_emma": "en_US_lessac_medium",
            "bm_george": "en_US_lessac_low",
        }
        return mapping.get(kokoro_voice, _DEFAULT_VOICE)

    def synthesize(self, text: str) -> np.ndarray:
        """Synthesize text to audio (sync, returns full audio).

        Args:
            text: Input text to synthesize.

        Returns:
            Audio samples as numpy array (float32, 16kHz).

        Raises:
            ValueError: If text is empty or synthesis fails.
        """
        if not text or not text.strip():
            raise ValueError("Input text cannot be empty")

        voice_path = _get_voice_path(self._piper_voice)
        
        if not os.path.exists(voice_path):
            raise FileNotFoundError(
                f"Piper voice model not found at {voice_path}. "
                "Please download from https://github.com/rhasspy/piper/releases"
            )

        try:
            # Run piper in stdin/stdout mode for raw wav
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
            
            # Parse WAV data
            wav_io = io.BytesIO(stdout)
            with wave.open(wav_io, 'rb') as wav:
                sample_rate = wav.getframerate()
                frames = wav.readframes(wav.getnframes())
                audio = np.frombuffer(frames, dtype=np.int16)
                audio = audio.astype(np.float32) / 32768.0
            
            return audio

        except FileNotFoundError:
            raise RuntimeError(
                "Piper not found. Install with: pip install piper-tts"
            )

    async def synthesize_stream(self, text: str) -> AsyncGenerator[tuple[np.ndarray, int], None]:
        """Synthesize text to audio stream (async, yields chunks).
        
        Note: Piper doesn't support true streaming, so we yield the full
        audio as a single chunk. For better streaming, consider using
        a chunked approach with sentence boundaries.

        Args:
            text: Input text to synthesize.

        Yields:
            Tuple of (audio_chunk, sample_rate).

        Raises:
            ValueError: If text is empty.
        """
        if not text or not text.strip():
            raise ValueError("Input text cannot be empty")

        # For now, synthesize full text and yield as single chunk
        # True streaming would require a different backend
        audio = self.synthesize(text)
        
        # Get sample rate from voice config
        sample_rate = 16000  # Piper uses 16kHz
        
        yield audio, sample_rate

    @property
    def sample_rate(self) -> int:
        """Return output sample rate (Piper uses 16kHz)."""
        return 16000
