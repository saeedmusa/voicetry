"""Abstract TTS Engine interface."""

from abc import ABC, abstractmethod
from typing import AsyncGenerator

import numpy as np


class TTSEngine(ABC):
    """Abstract base class for TTS engines.
    
    All TTS implementations must inherit from this class and implement
    the required methods.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the engine name (e.g., 'piper', 'kokoro')."""
        pass

    @property
    @abstractmethod
    def sample_rate(self) -> int:
        """Return the sample rate in Hz."""
        pass

    @abstractmethod
    def synthesize(self, text: str) -> np.ndarray:
        """Synthesize text to audio.

        Args:
            text: Input text to synthesize.

        Returns:
            Audio samples as numpy array (float32).
        """
        pass

    @abstractmethod
    async def synthesize_stream(
        self, text: str
    ) -> AsyncGenerator[tuple[np.ndarray, int], None]:
        """Synthesize text to audio stream (async, yields chunks).

        Args:
            text: Input text to synthesize.

        Yields:
            Tuple of (audio_chunk, sample_rate).
        """
        pass
