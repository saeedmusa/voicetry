"""Speech-to-text module for audio recording and transcription."""

from .config import SpeechToTextConfig, WhisperConfig, RecordingConfig
from .recorder import Recorder
from .transcriber import Transcriber, TranscriptionResult

__all__ = [
    "SpeechToTextConfig",
    "WhisperConfig",
    "RecordingConfig",
    "Recorder",
    "Transcriber",
    "TranscriptionResult",
]
