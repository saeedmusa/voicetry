"""Text-to-speech module for audio synthesis and playback."""

from .config import TTSConfig
from .synthesizer import Synthesizer
from .player import TTSPlayer
from .voice_selector import VoiceSelector

__all__ = [
    "TTSConfig",
    "Synthesizer",
    "TTSPlayer",
    "VoiceSelector",
]
