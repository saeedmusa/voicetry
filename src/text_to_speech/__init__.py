"""Text-to-speech module for audio synthesis and playback."""

from .config import TTSConfig
from .player import TTSPlayer
from .voice_selector import VoiceSelector
from .base import TTSEngine
from .engines import create_engine, get_engine

# Alias for backward compatibility
def get_synthesizer(config: TTSConfig = None):
    """Create a TTS engine from config (alias for create_engine)."""
    return create_engine(config)

__all__ = [
    "TTSConfig",
    "TTSEngine",
    "TTSPlayer",
    "VoiceSelector",
    "get_synthesizer",
    "create_engine",
    "get_engine",
]
