"""TTS configuration settings."""

from dataclasses import dataclass


@dataclass
class TTSConfig:
    """Configuration for text-to-speech synthesis.

    Attributes:
        voice_name: Voice to use (see TTSConfig.AVAILABLE_VOICES)
        language: Language code (e.g., "en-us", "en-gb")
        speed: Speech speed multiplier (0.5 to 2.0)
        sample_rate: Output audio sample rate in Hz
    """

    # Voice settings
    voice_name: str = "af_heart"
    language: str = "en-us"

    # Synthesis settings
    speed: float = 1.0
    sample_rate: int = 24000

    # Available voices
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
