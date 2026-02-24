"""Kokoro ONNX TTS synthesis with audio visualization support."""

import tempfile
from pathlib import Path
from typing import Callable, Generator, Optional, Tuple

import numpy as np

try:
    from kokoro_onnx import Kokoro
except ImportError:
    Kokoro = None

import soundfile as sf


_KOKORO_INSTANCE = None


def _get_kokoro() -> Kokoro:
    """Get or create global Kokoro instance."""
    global _KOKORO_INSTANCE
    if _KOKORO_INSTANCE is None:
        cache_dir = Path.home() / ".cache" / "kokoro"
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        model_path = cache_dir / "kokoro-v1.0.onnx"
        voices_path = cache_dir / "voices-v1.0.bin"
        
        if not model_path.exists():
            from huggingface_hub import hf_hub_download
            print("Downloading Kokoro ONNX model...")
            model_path = hf_hub_download("fastrtc/kokoro-onnx", "kokoro-v1.0.onnx", local_dir=str(cache_dir))
            voices_path = hf_hub_download("fastrtc/kokoro-onnx", "voices-v1.0.bin", local_dir=str(cache_dir))
        
        _KOKORO_INSTANCE = Kokoro(str(model_path), str(voices_path))
    
    return _KOKORO_INSTANCE


class KokoroTTS:
    """Text-to-speech using Kokoro ONNX."""

    VOICES = [
        "af_bella",
        "af_heart",
        "af_sarah",
        "af_sky",
        "am_adam",
        "am_michael",
        "bf_emma",
        "bm_george",
    ]

    def __init__(
        self,
        voice: str = "af_heart",
        language: str = "en-us",
        speed: float = 1.0,
    ):
        """Initialize Kokoro TTS.

        Args:
            voice: Voice to use (see VOICES list)
            language: Language code (currently not used, kept for API compatibility)
            speed: Speech speed multiplier (0.5 to 2.0)
        """
        self.voice = voice
        self.language = language
        self.speed = speed

    def synthesize(self, text: str) -> np.ndarray:
        """Synthesize text to audio.

        Args:
            text: Text to synthesize

        Returns:
            Audio samples as numpy array (float32, 24kHz)
        """
        kokoro = _get_kokoro()
        audio, _ = kokoro.create(text, voice=self.voice, speed=self.speed)
        return audio

    def synthesize_stream(
        self,
        text: str,
        chunk_callback: Optional[Callable[[np.ndarray], None]] = None,
    ) -> Generator[Tuple[str, str, np.ndarray], None, None]:
        """Stream synthesis - yields full audio in one chunk for now."""
        kokoro = _get_kokoro()
        audio, _ = kokoro.create(text, voice=self.voice, speed=self.speed)
        if chunk_callback:
            chunk_callback(audio)
        yield ("", "", audio)

    def save_audio(self, audio: np.ndarray, filepath: str) -> None:
        """Save audio to a WAV file."""
        sf.write(filepath, audio, 24000)

    def save_temp(self, audio: np.ndarray) -> str:
        """Save audio to a temporary file and return path."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            sf.write(f.name, audio, 24000)
            return f.name

    @property
    def sample_rate(self) -> int:
        """Kokoro outputs at 24kHz."""
        return 24000
