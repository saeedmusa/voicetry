"""Audio recording with real-time visualization."""

import queue
import threading
from dataclasses import dataclass
from typing import Callable, Optional

import numpy as np
import sounddevice as sd


@dataclass
class RecordingConfig:
    """Configuration for audio recording."""
    sample_rate: int = 16000  # Whisper expects 16kHz
    channels: int = 1
    dtype: str = "float32"
    block_size: int = 1024


class AudioRecorder:
    """Records audio from microphone with real-time level callbacks."""

    def __init__(self, config: Optional[RecordingConfig] = None):
        self.config = config or RecordingConfig()
        self._is_recording = False
        self._audio_data: list[np.ndarray] = []
        self._level_callback: Optional[Callable[[float], None]] = None
        self._level_queue: queue.Queue = queue.Queue()

    @property
    def is_recording(self) -> bool:
        return self._is_recording

    def set_level_callback(self, callback: Callable[[float], None]) -> None:
        """Set callback for real-time audio level updates (0.0 to 1.0)."""
        self._level_callback = callback

    def _audio_callback(self, indata: np.ndarray, frames: int, time, status) -> None:
        """Called by sounddevice for each audio block."""
        if status:
            print(f"Audio status: {status}")

        if self._is_recording:
            self._audio_data.append(indata.copy())

            # Calculate RMS level for visualization
            if self._level_callback:
                rms = np.sqrt(np.mean(indata**2))
                # Normalize to 0-1 range (adjust sensitivity as needed)
                level = min(1.0, rms * 10)
                self._level_callback(level)

    def start_recording(self) -> None:
        """Start recording audio."""
        self._audio_data = []
        self._is_recording = True

        self._stream = sd.InputStream(
            samplerate=self.config.sample_rate,
            channels=self.config.channels,
            dtype=self.config.dtype,
            blocksize=self.config.block_size,
            callback=self._audio_callback,
        )
        self._stream.start()

    def stop_recording(self) -> np.ndarray:
        """Stop recording and return the audio data."""
        self._is_recording = False
        
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        if not self._audio_data:
            return np.array([], dtype=np.float32)

        # Concatenate all audio chunks
        audio = np.concatenate(self._audio_data, axis=0)
        return audio.flatten()

    def get_audio_for_whisper(self, audio: np.ndarray) -> np.ndarray:
        """Prepare audio data for Whisper (ensure float32, 16kHz)."""
        return audio.astype(np.float32)
