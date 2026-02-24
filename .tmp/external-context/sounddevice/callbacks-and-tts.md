---
source: Official Docs
library: sounddevice
package: sounddevice
topic: callbacks-and-tts
fetched: 2026-02-23T00:00:00Z
official_docs: https://python-sounddevice.readthedocs.io/
---

# Callbacks and TTS Playback with Level Monitoring

## Stream Callback Signatures

### OutputStream callback (playback only)

```python
def callback(outdata, frames, time, status):
    # outdata: numpy.ndarray, shape=(frames, channels)
    # frames: int - number of frames to fill
    # time: CData - timestamps
    # status: CallbackFlags - error/info flags
    pass
```

### InputStream callback (recording only)

```python
def callback(indata, frames, time, status):
    # indata: numpy.ndarray, shape=(frames, channels)
    pass
```

### Stream callback (full-duplex)

```python
def callback(indata, outdata, frames, time, status):
    # Both indata and outdata provided
    pass
```

## TTS Playback with Level Monitoring

### Complete Example: Synchronous TTS Player

```python
import sounddevice as sd
import numpy as np
import threading

class TTSPlayer:
    """Synchronous TTS audio player with level monitoring."""

    def __init__(self, samplerate=44100):
        self.samplerate = samplerate
        self.current_level = 0.0
        self.peak_level = 0.0
        self.event = threading.Event()
        self.stream = None

    def play(self, audio_data):
        """
        Play audio data and monitor levels.
        Blocks until playback completes.

        Args:
            audio_data: numpy.ndarray with shape (frames,) or (frames, channels)

        Returns:
            dict: Playback statistics
        """
        # Reset stats
        self.current_level = 0.0
        self.peak_level = 0.0
        self.event.clear()

        # Ensure 2D array for consistency
        if len(audio_data.shape) == 1:
            audio_data = audio_data.reshape(-1, 1)

        channels = audio_data.shape[1]
        current_frame = 0

        def callback(outdata, frames, time, status):
            nonlocal current_frame

            if status:
                print(f"Callback status: {status}")

            # Calculate how many frames we can play
            chunksize = min(len(audio_data) - current_frame, frames)

            # Copy audio to output buffer
            if chunksize > 0:
                outdata[:chunksize] = audio_data[current_frame:current_frame + chunksize]

                # Monitor level (RMS)
                chunk_rms = np.sqrt(np.mean(outdata[:chunksize] ** 2))
                self.current_level = chunk_rms
                self.peak_level = max(self.peak_level, chunk_rms)

            # Fill remaining with silence if at end
            if chunksize < frames:
                outdata[chunksize:] = 0
                raise sd.CallbackStop()

            current_frame += chunksize

        def finished_callback():
            self.event.set()

        # Create and start stream
        self.stream = sd.OutputStream(
            samplerate=self.samplerate,
            channels=channels,
            callback=callback,
            finished_callback=finished_callback
        )

        with self.stream:
            self.event.wait()  # Block until playback finishes

        return {
            'peak_level': self.peak_level,
            'duration': len(audio_data) / self.samplerate,
            'frames_played': current_frame
        }

    def stop(self):
        """Stop playback immediately."""
        if self.stream and self.stream.active:
            self.stream.abort()
            self.event.set()

    def get_current_level(self):
        """Get the current RMS level during playback."""
        return self.current_level
```

### Usage Example

```python
import numpy as np
import sounddevice as sd

# Create some TTS audio (simplified - replace with actual TTS)
def generate_tts_audio(text, duration=2.0, samplerate=44100):
    """Generate dummy TTS audio (replace with actual TTS)."""
    t = np.linspace(0, duration, int(samplerate * duration))
    # Create speech-like pattern (simplified)
    audio = np.zeros_like(t)
    for i in range(10):
        freq = 200 + i * 50
        start = int(i * duration / 10 * samplerate)
        end = int((i + 1) * duration / 10 * samplerate)
        audio[start:end] = 0.3 * np.sin(2 * np.pi * freq * t[start:end])
    return audio.reshape(-1, 1)

# Create player
player = TTSPlayer(samplerate=44100)

# Generate TTS audio
audio_data = generate_tts_audio("Hello, world!", duration=2.0)

# Play and monitor
print("Playing TTS audio...")
stats = player.play(audio_data)

print(f"\nPlayback complete!")
print(f"Peak level: {stats['peak_level']:.4f}")
print(f"Duration: {stats['duration']:.2f}s")
```

## Callback Status Handling

### Checking for Errors

```python
def callback(outdata, frames, time, status):
    if status:
        if status.output_underflow:
            print("⚠️ Output underflow - audio glitch!")
        if status.input_overflow:
            print("⚠️ Input overflow - samples lost!")
        if status.priming_output:
            print("ℹ️ Priming output buffers")

    # Process audio
    outdata[:] = generate_audio(frames)
```

### Accumulating Status Flags

```python
import sounddevice as sd

# Track status across callbacks
errors = sd.CallbackFlags()

def callback(outdata, frames, time, status):
    global errors
    if status:
        errors |= status  # Accumulate errors

    # ... process audio ...

# Check after playback
if errors.output_underflow:
    print("Underflows occurred!")
```

## Advanced: TTS Stream with Queue

For streaming TTS output (for very long audio):

```python
import sounddevice as sd
import numpy as np
import queue
import threading

class StreamingTTSPlayer:
    """Stream TTS audio with queue-based buffering."""

    def __init__(self, samplerate=44100, blocksize=2048, buffersize=20):
        self.samplerate = samplerate
        self.blocksize = blocksize
        self.buffersize = buffersize
        self.queue = queue.Queue(maxsize=buffersize)
        self.event = threading.Event()

    def add_audio_chunk(self, audio_data):
        """Add audio chunk to playback queue."""
        # Ensure correct blocksize
        if len(audio_data) < self.blocksize:
            # Pad with silence
            padded = np.zeros((self.blocksize, audio_data.shape[1]))
            padded[:len(audio_data)] = audio_data
            self.queue.put_nowait(padded)
        elif len(audio_data) > self.blocksize:
            # Split into blocks
            for i in range(0, len(audio_data), self.blocksize):
                chunk = audio_data[i:i + self.blocksize]
                if len(chunk) < self.blocksize:
                    padded = np.zeros((self.blocksize, chunk.shape[1]))
                    padded[:len(chunk)] = chunk
                    self.queue.put_nowait(padded)
                else:
                    self.queue.put_nowait(chunk)
        else:
            self.queue.put_nowait(audio_data)

    def signal_end(self):
        """Signal end of audio stream."""
        self.queue.put(None)  # Sentinel value

    def play(self):
        """Start playback stream."""
        current_level = 0.0
        peak_level = 0.0

        def callback(outdata, frames, time, status):
            nonlocal current_level, peak_level

            if status:
                print(f"Status: {status}")

            try:
                data = self.queue.get_nowait()
            except queue.Empty:
                print("Buffer underflow!")
                outdata[:] = 0
                return

            if data is None:
                # End of stream
                outdata[:] = 0
                raise sd.CallbackStop()

            if len(data) < len(outdata):
                outdata[:len(data)] = data
                outdata[len(data):] = 0
                raise sd.CallbackStop()
            else:
                outdata[:] = data

            # Monitor level
            rms = np.sqrt(np.mean(outdata ** 2))
            current_level = rms
            peak_level = max(peak_level, rms)

        def finished_callback():
            self.event.set()

        stream = sd.OutputStream(
            samplerate=self.samplerate,
            blocksize=self.blocksize,
            callback=callback,
            finished_callback=finished_callback
        )

        with stream:
            self.event.wait()

        return {'peak_level': peak_level}
```

## Using CallbackStop vs CallbackAbort

### CallbackStop - Graceful finish

```python
def callback(outdata, frames, time, status):
    if should_stop:
        # Fill remaining buffer, then stop
        outdata[:] = 0
        raise sd.CallbackStop()  # All buffers play out
```

### CallbackAbort - Immediate stop

```python
def callback(outdata, frames, time, status):
    if should_stop:
        # Discard all pending buffers
        raise sd.CallbackAbort()  # Immediate stop
```

## Real-time Level Visualization

```python
import sounddevice as sd
import numpy as np

class LevelMonitor:
    """Monitor audio levels in real-time."""

    def __init__(self):
        self.level = 0.0
        self.peak = 0.0

    def callback(self, outdata, frames, time, status):
        # Calculate RMS level
        self.level = np.sqrt(np.mean(outdata ** 2))
        self.peak = max(self.peak, self.level)

        # Visual feedback (in a real app, use GUI/console)
        bar_length = int(self.level * 50)
        print(f"\r[{'=' * bar_length:{'>'}50}] {self.level:.3f}", end='', flush=True)

# Usage
monitor = LevelMonitor()
stream = sd.OutputStream(callback=monitor.callback)

with stream:
    sd.sleep(5000)
```

## Key Takeaways for TTS Playback

1. **Use `OutputStream` with callback** for control and level monitoring
2. **Always fill entire output buffer** even when stopping
3. **Use `finished_callback`** for clean shutdown
4. **Monitor `status` flags** for underflow/overflow detection
5. **Track levels in callback** but display outside callback
6. **Use `threading.Event`** for blocking main thread while playing
7. **For long audio**, consider queue-based streaming
8. **Handle edge cases** (end of file, empty buffers, errors)
