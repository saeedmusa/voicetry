"""TTS configuration settings."""

from dataclasses import dataclass
from typing import Literal


@dataclass
class TTSConfig:
    """Configuration for text-to-speech synthesis.

    Attributes:
        voice_name: Voice to use (see TTSConfig.AVAILABLE_VOICES)
        language: Language code (e.g., "en-us", "en-gb")
        speed: Speech speed multiplier (0.5 to 2.0)
        sample_rate: Output audio sample rate in Hz
        engine: TTS engine to use ("kokoro" or "piper")
    """

    # Voice settings
    voice_name: str = "af_heart"
    language: str = "en-us"

    # Synthesis settings
    speed: float = 1.0
    sample_rate: int = 24000
    
    # Engine settings
    engine: Literal["kokoro", "piper"] = "kokoro"

    # Available Kokoro voices
    KOKORO_VOICES = [
        "af_bella",    # Female, American
        "af_heart",   # Female, warm
        "af_sarah",   # Female, clear
        "af_sky",     # Female
        "am_adam",    # Male, American
        "am_michael", # Male, American
        "bf_emma",    # Female, British
        "bm_george",  # Male, British
    ]
    
    # Available Piper voices (mapped from Kokoro)
    PIPER_VOICES = [
        "af_bella",    # Female, American -> en_US_lessac_medium
        "af_heart",   # Female, warm -> en_US_lessac_medium
        "af_sarah",   # Female, clear -> en_US_lessac_medium
        "af_sky",     # Female -> en_US_lessac_medium
        "am_adam",    # Male, American -> en_US_lessac_low
        "am_michael", # Male, American -> en_US_lessac_low
        "bf_emma",    # Female, British -> en_US_lessac_medium
        "bm_george",  # Male, British -> en_US_lessac_low
    ]

    # Keep for backward compatibility
    # Default to Kokoro voices at class level
    AVAILABLE_VOICES = [
        "af_bella",    # Female, American
        "af_heart",   # Female, warm
        "af_sarah",   # Female, clear
        "af_sky",     # Female
        "am_adam",    # Male, American
        "am_michael", # Male, American
        "bf_emma",    # Female, British
        "bm_george",  # Male, British
    ]
    
    @property
    def available_voices(self):
        """Get available voices based on engine."""
        if self.engine == "piper":
            return self.PIPER_VOICES
        return self.KOKORO_VOICES
