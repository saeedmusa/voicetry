"""TTS audio playback with level callbacks using sounddevice."""

import asyncio
import queue
import threading
from typing import AsyncGenerator, Callable, Optional

import numpy as np
import sounddevice as sd

from .config import TTSConfig


class TTSPlayer:
    """Plays synthesized speech with real-time level visualization.

    Supports both sync and async streaming playback.
    """

    def __init__(self, config: Optional[TTSConfig] = None):
        """Initialize TTS player.

        Args:
            config: TTS configuration with sample_rate settings.
                    If None, uses default TTSConfig.
        """
        self.config = config or TTSConfig()
        self.sample_rate = self.config.sample_rate
        self._is_playing = False
        self._stop_flag = False
        self._level_callback: Optional[Callable[[float], None]] = None

    @property
    def is_playing(self) -> bool:
        """Check if audio is currently playing."""
        return self._is_playing

    def set_level_callback(self, callback: Callable[[float], None]) -> None:
        """Set callback for real-time playback level updates (0.0 to 1.0).

        Args:
            callback: Function called with level value during playback.
        """
        self._level_callback = callback

    def play(self, audio: np.ndarray, blocking: bool = True) -> None:
        """Play audio data synchronously with level callbacks.

        Args:
            audio: Audio samples as numpy array (float32).
            blocking: If True, wait for playback to complete.
        """
        self._stop_flag = False
        self._is_playing = True

        try:
            sd.play(audio, self.sample_rate, blocksize=1024, latency='low')

            if blocking:
                block_size = 1024
                samples_played = 0

                while sd.get_stream().active and not self._stop_flag:
                    if self._level_callback:
                        end_pos = min(samples_played + block_size, len(audio))
                        if samples_played < len(audio):
                            block = audio[samples_played:end_pos]
                            rms = np.sqrt(np.mean(block**2)) if len(block) > 0 else 0
                            level = min(1.0, rms * 8)
                            self._level_callback(level)
                        samples_played = end_pos
                    sd.sleep(50)

        finally:
            if blocking:
                sd.stop()
                self._is_playing = False
                if self._level_callback:
                    self._level_callback(0.0)

    async def play_direct(self, audio: np.ndarray, sample_rate: int) -> None:
        """Play audio directly (for parallel pipeline).
        
        This is a sync wrapper around play() for use in async context.
        
        Args:
            audio: Audio samples as numpy array (float32).
            sample_rate: Sample rate of the audio.
        """
        # Store original sample rate
        original_rate = self.sample_rate
        self.sample_rate = sample_rate
        
        try:
            # Run sync play in executor to not block the event loop
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: self.play(audio, blocking=True))
        finally:
            self.sample_rate = original_rate

    async def play_stream(
        self, 
        audio_generator: AsyncGenerator[tuple[np.ndarray, int], None],
        on_chunk: Optional[Callable[[np.ndarray], None]] = None
    ) -> tuple[int, float]:
        """Play audio chunks as they arrive (async).

        Args:
            audio_generator: AsyncGenerator yielding (audio_chunk, sample_rate) tuples.
            on_chunk: Optional callback called for each chunk received.

        Returns:
            Tuple of (total_samples, elapsed_seconds).
        """
        import time
        
        self._stop_flag = False
        self._is_playing = True
        total_samples = 0
        start_time = time.time()
        
        audio_queue: queue.Queue[Optional[np.ndarray]] = queue.Queue()
        playback_thread: Optional[threading.Thread] = None
        stream: Optional[sd.OutputStream] = None
        
        def level_calculator(block: np.ndarray) -> float:
            """Calculate RMS level from audio block."""
            if len(block) == 0:
                return 0.0
            rms = np.sqrt(np.mean(block**2))
            return min(1.0, rms * 8)

        def playback_worker():
            """Background thread that plays audio from queue."""
            nonlocal stream, total_samples
            
            try:
                while not self._stop_flag:
                    try:
                        chunk = audio_queue.get(timeout=0.1)
                    except queue.Empty:
                        if self._stop_flag:
                            break
                        continue
                    
                    if chunk is None:
                        break
                    
                    if stream is None:
                        stream = sd.OutputStream(
                            samplerate=self.sample_rate,
                            channels=1,
                            dtype='float32',
                            blocksize=1024,
                            latency='low',
                            finished_callback=None
                        )
                        stream.start()
                    
                    samples_remaining = len(chunk)
                    offset = 0
                    
                    while samples_remaining > 0 and not self._stop_flag:
                        block_size = min(4096, samples_remaining)
                        block = chunk[offset:offset + block_size]
                        
                        try:
                            stream.write(block)
                        except:
                            pass
                        
                        if self._level_callback:
                            level = level_calculator(block)
                            self._level_callback(level)
                        
                        offset += block_size
                        samples_remaining -= block_size
                        total_samples += block_size
                    
                    audio_queue.task_done()
                    
            except Exception as e:
                pass
            finally:
                if stream:
                    stream.stop()
                    stream.close()
                    stream = None

        try:
            playback_thread = threading.Thread(target=playback_worker, daemon=True)
            playback_thread.start()

            async for audio_chunk, sr in audio_generator:
                if self._stop_flag:
                    break
                
                if on_chunk:
                    on_chunk(audio_chunk)
                
                audio_queue.put(audio_chunk)

            audio_queue.put(None)
            
            while playback_thread.is_alive():
                await asyncio.sleep(0.05)

        finally:
            self._stop_flag = True
            if stream:
                try:
                    stream.stop()
                    stream.close()
                except:
                    pass
            self._is_playing = False
            if self._level_callback:
                self._level_callback(0.0)
        
        elapsed = time.time() - start_time
        return total_samples, elapsed

    def stop(self) -> None:
        """Stop playback immediately."""
        self._stop_flag = True
        try:
            sd.stop()
        except:
            pass
        self._is_playing = False
