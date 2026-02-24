"""Configuration for speech-to-text module."""

from dataclasses import dataclass


class WhisperConfig:
    """Whisper model configuration constants."""

    # Available model sizes
    MODEL_SIZES = ["tiny", "base", "small", "medium", "large"]

    # Default model (balance of speed and accuracy)
    DEFAULT_MODEL = "base"


class RecordingConfig:
    """Audio recording configuration constants."""

    # Whisper expects 16kHz audio
    DEFAULT_SAMPLE_RATE = 16000
    DEFAULT_CHANNELS = 1
    DEFAULT_DTYPE = "float32"
    DEFAULT_BLOCK_SIZE = 1024


@dataclass
class SpeechToTextConfig:
    """Configuration for speech-to-text processing.

    Combines recording and Whisper model settings in a simple,
    self-contained configuration class.
    """

    # Whisper settings
    model_name: str = WhisperConfig.DEFAULT_MODEL
    language: str | None = None  # None for auto-detection
    device: str = "cpu"  # "cpu" or "cuda"

    # Recording settings
    sample_rate: int = RecordingConfig.DEFAULT_SAMPLE_RATE
    channels: int = RecordingConfig.DEFAULT_CHANNELS
    chunk_size: int = RecordingConfig.DEFAULT_BLOCK_SIZE

    def validate(self) -> None:
        """Validate configuration values.

        Raises:
            ValueError: If any configuration value is invalid.
        """
        if self.model_name not in WhisperConfig.MODEL_SIZES:
            raise ValueError(
                f"Invalid model_name: {self.model_name}. "
                f"Must be one of {WhisperConfig.MODEL_SIZES}"
            )

        if self.sample_rate <= 0:
            raise ValueError("sample_rate must be positive")

        if self.channels not in (1, 2):
            raise ValueError("channels must be 1 (mono) or 2 (stereo)")

        if self.chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
