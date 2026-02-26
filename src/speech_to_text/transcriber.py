"""Whisper-based speech-to-text transcription using faster-whisper."""

import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
import soundfile as sf
from faster_whisper import WhisperModel

from .config import SpeechToTextConfig


@dataclass
class TranscriptionResult:
    """Result of audio transcription."""
    text: str
    language: Optional[str] = None


class Transcriber:
    """Transcribes audio using Faster Whisper."""

    def __init__(self, config: SpeechToTextConfig):
        """Initialize Whisper transcriber with configuration.

        Args:
            config: Configuration settings for the transcriber.
        """
        self.config = config
        self._model = None  # Lazy load

    @property
    def model(self) -> WhisperModel:
        """Lazy load the Faster Whisper model.

        Returns:
            The loaded WhisperModel instance.
        """
        if self._model is None:
            # faster-whisper uses different model sizes
            # tiny, base, small, medium, large-v1, large-v2, large-v3
            model_size = self.config.model_name.replace("turbo", "large-v3")
            self._model = WhisperModel(
                model_size,
                device=self.config.device,
                compute_type="float16" if self.config.device == "cuda" else "int8",
                cpu_threads=8
            )
        return self._model

    def transcribe(self, audio: np.ndarray, sample_rate: Optional[int] = None) -> TranscriptionResult:
        """Transcribe audio to text.

        Args:
            audio: Audio samples as numpy array (float32).
            sample_rate: Sample rate of the audio. Defaults to config sample_rate.

        Returns:
            TranscriptionResult with transcribed text and detected language.
        """
        sr = sample_rate or self.config.sample_rate
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            sf.write(f.name, audio, sr)
            temp_path = f.name

        try:
            # Transcribe using faster-whisper
            options = {}
            if self.config.language:
                options["language"] = self.config.language

            # Latency/accuracy balanced defaults for interactive voice UX
            options.setdefault("beam_size", 3)
            options.setdefault("vad_filter", True)
            options.setdefault("vad_parameters", {"min_silence_duration_ms": 300})
            options.setdefault("condition_on_previous_text", False)
            segments, info = self.model.transcribe(temp_path, **options)

            # Collect all segments into text
            text_parts = []
            for segment in segments:
                text_parts.append(segment.text)

            full_text = " ".join(text_parts)

            return TranscriptionResult(
                text=full_text.strip(),
                language=info.language if hasattr(info, 'language') else None,
            )
        finally:
            # Clean up temp file
            Path(temp_path).unlink(missing_ok=True)
