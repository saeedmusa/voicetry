"""Audio recording with real-time level callbacks for visualization."""

from typing import Callable, Optional

import numpy as np
import sounddevice as sd

from .config import SpeechToTextConfig


class Recorder:
    """Simple synchronous audio recorder with level callbacks.

    Records audio from microphone and provides real-time level updates
    via callback for visualization. Uses callback-based recording with
    start/stop control.
    """

    def __init__(
        self,
        config: Optional[SpeechToTextConfig] = None,
        level_callback: Optional[Callable[[float], None]] = None,
    ):
        """Initialize the recorder.

        Args:
            config: Configuration for recording settings.
                Defaults to SpeechToTextConfig().
            level_callback: Optional callback for real-time audio level
                updates (0.0 to 1.0). Called during recording.
        """
        self.config = config or SpeechToTextConfig()
        self._level_callback = level_callback
        self._stream: Optional[sd.InputStream] = None
        self._is_recording = False
        self._audio_data: list[np.ndarray] = []

    @property
    def is_recording(self) -> bool:
        """Whether recording is active."""
        return self._is_recording

    def set_level_callback(self, callback: Callable[[float], None]) -> None:
        """Set callback for real-time audio level updates (0.0 to 1.0).

        Args:
            callback: Function to call with level value during recording.
        """
        self._level_callback = callback

    def _audio_callback(
        self,
        indata: np.ndarray,
        frames: int,
        time,  # type: ignore
        status,  # type: ignore
    ) -> None:
        """Callback for audio recording and level monitoring.

        Args:
            indata: Incoming audio data.
            frames: Number of frames in this block.
            time: Time information from sounddevice.
            status: Status flags (overflow, etc.).
        """
        if status:
            # Non-blocking status check
            if status.input_overflow:
                pass  # Could log overflow warning

        if self._is_recording:
            # Store audio data
            self._audio_data.append(indata.copy())

            # Calculate RMS level for visualization
            if self._level_callback:
                rms = np.sqrt(np.mean(indata**2))
                # Normalize to 0-1 range (adjust sensitivity as needed)
                level = min(1.0, rms * 10)
                self._level_callback(level)

    def start_recording(self) -> None:
        """Start recording audio.

        Opens the audio stream and begins capturing. Recording continues
        until stop_recording() is called.
        """
        self._audio_data = []
        self._is_recording = True

        self._stream = sd.InputStream(
            samplerate=self.config.sample_rate,
            channels=self.config.channels,
            dtype="float32",
            blocksize=self.config.chunk_size,
            callback=self._audio_callback,
        )
        self._stream.start()

    def stop_recording(self) -> np.ndarray:
        """Stop recording and return captured audio.

        Returns:
            Audio data as flattened numpy array (float32). Empty array
            if no audio was recorded.
        """
        if self._stream is None:
            raise RuntimeError("No active recording. Call start_recording() first.")

        self._is_recording = False
        self._stream.stop()
        self._stream.close()
        self._stream = None

        if not self._audio_data:
            return np.array([], dtype=np.float32)

        # Concatenate all audio chunks
        audio = np.concatenate(self._audio_data, axis=0)
        return audio.flatten()
