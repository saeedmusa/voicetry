"""Text-to-speech module for audio synthesis and playback."""

from .config import TTSConfig
from .player import TTSPlayer
from .voice_selector import VoiceSelector

# Import the appropriate synthesizer based on config
# We'll do a lazy import to avoid issues when engine is not installed


def get_synthesizer(config: TTSConfig = None):
    """Get the appropriate synthesizer based on config.
    
    Args:
        config: TTSConfig with engine setting. Defaults to Kokoro.
        
    Returns:
        Synthesizer instance (KokoroSynthesizer or PiperSynthesizer)
    """
    config = config or TTSConfig()
    
    if config.engine == "piper":
        from .piper_synthesizer import Synthesizer as PiperSynthesizer
        return PiperSynthesizer(config)
    else:
        from .synthesizer import Synthesizer as KokoroSynthesizer
        return KokoroSynthesizer(config)


# Default: import Kokoro synthesizer
from .synthesizer import Synthesizer

__all__ = [
    "TTSConfig",
    "Synthesizer",
    "PiperSynthesizer", 
    "TTSPlayer",
    "VoiceSelector",
    "get_synthesizer",
]
