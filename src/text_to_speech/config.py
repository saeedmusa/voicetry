"""TTS configuration settings."""

from dataclasses import dataclass
from typing import Literal


@dataclass
class TTSConfig:
    """Configuration for text-to-speech synthesis.

    Attributes:
        voice_name: Voice ID to use
        language: Language code (e.g., "en-us", "en-gb")
        speed: Speech speed multiplier (0.5 to 2.0)
        sample_rate: Output audio sample rate in Hz
        engine: TTS engine to use ("kokoro" or "piper")
    """

    voice_name: str = "en_US_lessac_medium"
    language: str = "en-us"
    speed: float = 1.0
    sample_rate: int = 16000
    engine: Literal["kokoro", "piper"] = "piper"
