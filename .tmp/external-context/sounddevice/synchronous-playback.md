---
source: Official Docs
library: sounddevice
package: sounddevice
topic: synchronous-playback
fetched: 2026-02-23T00:00:00Z
official_docs: https://python-sounddevice.readthedocs.io/
---

# Synchronous Playback with sd.play()

## Using sd.play() with blocking mode

The `sd.play()` function has a `blocking` parameter that controls whether playback is synchronous or asynchronous:

```python
import sounddevice as sd
import numpy as np

# Create some audio data (1 second of 440Hz sine wave)
fs = 44100
t = np.linspace(0, 1, fs)
audio = 0.5 * np.sin(2 * np.pi * 440 * t)

# Blocking mode - waits until playback finishes
sd.play(audio, fs, blocking=True)
print("Playback complete!")

# Or use default non-blocking with sd.wait()
sd.play(audio, fs)
sd.wait()  # Blocks until playback is done
print("Playback complete!")
```

## sd.play() Parameters

- `data`: NumPy array containing audio data (mono or multi-channel)
- `samplerate`: Sampling frequency in Hz (critical - wrong rate = wrong speed)
- `blocking`: If `True`, wait until playback is finished. If `False` (default), return immediately
- `loop`: If `True`, play data in a loop
- `mapping`: Channel mapping for output
- Other parameters from `OutputStream` (device, channels, dtype, latency, etc.)

## What sd.play() does internally

1. Calls `sd.stop()` to terminate any currently running play/rec/playrec
2. Creates an `OutputStream` with a callback function for playback
3. Starts the stream
4. If `blocking=True`, waits until playback is done

## Synchronous playback with finished_callback

For more control over when playback finishes, use `OutputStream` directly:

```python
import sounddevice as sd
import threading

event = threading.Event()

def finished_callback():
    print("Playback finished!")
    event.set()

stream = sd.OutputStream(
    samplerate=fs,
    channels=1,
    callback=your_playback_callback,
    finished_callback=finished_callback
)

with stream:
    event.wait()  # Wait for playback to finish
```

## Important Notes

- **Correct samplerate is critical**: If you don't specify the correct sampling frequency, audio will play too slow or too fast
- **Cannot be used for overlapping playbacks**: `sd.play()` is designed for simple scripts, not multiple concurrent playbacks
- **For gapless playback**: Use `OutputStream` directly with custom callback
- **Default dtype**: If data is float64, it's converted to float32 before playback (PortAudio doesn't natively support float64)

## Setting defaults for repeated use

```python
import sounddevice as sd

sd.default.samplerate = 44100
sd.default.channels = 2

# Now you can omit these arguments
sd.play(myarray)  # Uses default samplerate
```
