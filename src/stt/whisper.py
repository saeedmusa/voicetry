"""Whisper-based speech-to-text transcription."""

import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
import soundfile as sf
import whisper


@dataclass
class TranscriptionResult:
    """Result of audio transcription."""
    text: str
    language: Optional[str] = None
    confidence: Optional[float] = None


class WhisperTranscriber:
    """Transcribes audio using OpenAI Whisper."""

    # Available model sizes: tiny, base, small, medium, large
    MODEL_SIZES = ["tiny", "base", "small", "medium", "large"]

    def __init__(self, model_size: str = "base"):
        """Initialize Whisper with specified model size.

        Args:
            model_size: Model size (tiny, base, small, medium, large)
                       - tiny: ~39M params, fastest, least accurate
                       - base: ~74M params, good balance (recommended)
                       - small: ~244M params, more accurate
                       - medium: ~769M params, very accurate
                       - large: ~1550M params, most accurate
        """
        self.model_size = model_size
        self._model = None  # Lazy load

    @property
    def model(self):
        """Lazy load the Whisper model."""
        if self._model is None:
            self._model = whisper.load_model(self.model_size)
        return self._model

    def transcribe(
        self,
        audio: np.ndarray,
        sample_rate: int = 16000,
        language: Optional[str] = None,
    ) -> TranscriptionResult:
        """Transcribe audio to text.

        Args:
            audio: Audio samples as numpy array (float32)
            sample_rate: Sample rate of the audio
            language: Optional language hint (e.g., "en")

        Returns:
            TranscriptionResult with transcribed text
        """
        # Whisper expects 16kHz audio, resample if needed
        if sample_rate != 16000:
            # For simplicity, we'll use whisper's built-in resampling
            pass

        # Save to temp file for whisper (it handles file input better)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            sf.write(f.name, audio, sample_rate)
            temp_path = f.name

        try:
            # Transcribe
            options = {}
            if language:
                options["language"] = language

            result = self.model.transcribe(temp_path, **options)

            return TranscriptionResult(
                text=result["text"].strip(),
                language=result.get("language"),
            )
        finally:
            # Clean up temp file
            Path(temp_path).unlink(missing_ok=True)

    def transcribe_file(self, filepath: str, language: Optional[str] = None) -> TranscriptionResult:
        """Transcribe audio from a file."""
        audio, sr = sf.read(filepath)
        if audio.ndim > 1:
            audio = audio.mean(axis=1)  # Convert to mono
        return self.transcribe(audio.astype(np.float32), sr, language)
