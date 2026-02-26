"""Audio playback with visualization support."""

import tempfile
import threading
from typing import Callable, Optional

import numpy as np
import sounddevice as sd
import soundfile as sf


class AudioPlayer:
    """Plays audio with optional level visualization callback."""

    def __init__(self, sample_rate: int = 24000):
        self.sample_rate = sample_rate
        self._is_playing = False
        self._stop_flag = False
        self._level_callback: Optional[Callable[[float], None]] = None
        self._play_thread: Optional[threading.Thread] = None

    @property
    def is_playing(self) -> bool:
        return self._is_playing

    def set_level_callback(self, callback: Callable[[float], None]) -> None:
        """Set callback for real-time playback level updates."""
        self._level_callback = callback

    def _play_with_visualization(self, audio: np.ndarray) -> None:
        """Play audio while sending level updates."""
        block_size = 1024
        samples_played = 0

        # Start playback
        sd.play(audio, self.sample_rate)

        stream = sd.get_stream()
        while stream and stream.active and not self._stop_flag:
            if self._level_callback:
                # Calculate current position and level
                end_pos = min(samples_played + block_size, len(audio))
                if samples_played < len(audio):
                    block = audio[samples_played:end_pos]
                    rms = np.sqrt(np.mean(block**2)) if len(block) > 0 else 0
                    level = min(1.0, rms * 8)  # Adjust sensitivity
                    self._level_callback(level)
                samples_played = end_pos
            sd.sleep(50)  # Small sleep to not overwhelm

        # Ensure we're stopped
        sd.stop()
        self._is_playing = False

        # Final callback to reset level
        if self._level_callback:
            self._level_callback(0.0)

    def play(self, audio: np.ndarray, blocking: bool = True) -> None:
        """Play audio data.

        Args:
            audio: Audio samples as numpy array
            blocking: If True, wait for playback to complete
        """
        self._stop_flag = False
        self._is_playing = True

        if blocking:
            self._play_with_visualization(audio)
        else:
            self._play_thread = threading.Thread(
                target=self._play_with_visualization,
                args=(audio,)
            )
            self._play_thread.start()

    def play_file(self, filepath: str, blocking: bool = True) -> None:
        """Play audio from a file."""
        audio, sr = sf.read(filepath)
        if audio.ndim > 1:
            audio = audio.mean(axis=1)  # Convert to mono
        self.sample_rate = sr
        self.play(audio.astype(np.float32), blocking=blocking)

    def stop(self) -> None:
        """Stop playback."""
        self._stop_flag = True
        sd.stop()
        self._is_playing = False

    def save_to_file(self, audio: np.ndarray, filepath: str) -> None:
        """Save audio to a WAV file."""
        sf.write(filepath, audio, self.sample_rate)

    def save_temp(self, audio: np.ndarray) -> str:
        """Save audio to a temporary file and return the path."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            sf.write(f.name, audio, self.sample_rate)
            return f.name
