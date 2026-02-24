---
source: Official Docs
library: sounddevice
package: sounddevice
topic: sleep-function
fetched: 2026-02-23T00:00:00Z
official_docs: https://python-sounddevice.readthedocs.io/
---

# Using sd.sleep() Properly

## Function Signature

```python
sounddevice.sleep(msec)
```

**Put the caller to sleep for at least `msec` milliseconds.**

## Important Warnings

⚠️ **The function may sleep longer than requested so don't rely on this for accurate musical timing.**

`sd.sleep()` is not a high-precision timing function. It's a convenience wrapper for sleeping while audio streams are running.

## Basic Usage

```python
import sounddevice as sd

# Sleep for 5.5 seconds
sd.sleep(5500)  # milliseconds

# Common pattern: sleep while playing
with sd.Stream(channels=2, callback=my_callback):
    sd.sleep(5500)  # Play for 5.5 seconds
```

## When to use sd.sleep()

`sd.sleep()` is primarily useful in these scenarios:

### 1. Keeping callback streams alive

```python
import sounddevice as sd

def callback(indata, outdata, frames, time, status):
    # Process audio in callback
    outdata[:] = indata

# Stream will stop when we exit the with block
with sd.Stream(channels=2, callback=callback):
    sd.sleep(5000)  # Keep stream alive for 5 seconds
```

### 2. Waiting for playback in examples/scripts

```python
import sounddevice as sd
import numpy as np

# Generate some audio
fs = 44100
duration = 5
t = np.linspace(0, duration, int(fs * duration))
audio = 0.5 * np.sin(2 * np.pi * 440 * t)

# Play and wait
sd.play(audio, fs)
sd.sleep(int(duration * 1000))
```

## Comparison with other waiting methods

| Method | Use Case | Notes |
|--------|----------|-------|
| `sd.wait()` | Wait for `play()/rec()/playrec()` to finish | Only works with convenience functions |
| `sd.sleep(msec)` | Sleep for a duration | For callback streams or simple delays |
| `sd.get_stream().active` | Check if still playing | Polling approach |
| `threading.Event` | Custom synchronization | More control over when to stop |

## Better alternatives for different scenarios

### For play()/rec()/playrec() - use sd.wait()

```python
import sounddevice as sd

sd.play(audio, fs)
sd.wait()  # Proper way to wait for playback to finish
```

### For callback streams - use finished_callback

```python
import sounddevice as sd
import threading

event = threading.Event()

def finished_callback():
    print("Playback finished!")
    event.set()

stream = sd.OutputStream(
    samplerate=fs,
    callback=playback_callback,
    finished_callback=finished_callback
)

with stream:
    event.wait()  # Wait for finished_callback
```

### For polling - use active property

```python
import sounddevice as sd
import time

sd.play(audio, fs)

while sd.get_stream().active:
    # Do something while playing
    print("Still playing...")
    time.sleep(0.1)

print("Done!")
```

## Best Practices

1. **Use `sd.wait()` for convenience functions**: It's the intended way to block until `play()/rec()/playrec()` completes
2. **Don't use `sd.sleep()` for timing**: If you need accurate timing, look at the `time` property of streams
3. **Use `sd.sleep()` only for keeping callback streams alive**: In with blocks where you want the stream to run for a specific duration
4. **Use `finished_callback` for event-driven code**: More efficient than polling `active`

## Example: TTS playback with level monitoring

```python
import sounddevice as sd
import numpy as np
import threading

class AudioPlayer:
    def __init__(self):
        self.event = threading.Event()
        self.level = 0.0

    def play(self, audio_data, samplerate=44100):
        current_frame = 0

        def callback(outdata, frames, time, status):
            nonlocal current_frame
            if status:
                print(f"Status: {status}")

            chunksize = min(len(audio_data) - current_frame, frames)
            outdata[:chunksize] = audio_data[current_frame:current_frame + chunksize]

            # Calculate level (RMS)
            if chunksize > 0:
                self.level = np.sqrt(np.mean(outdata[:chunksize] ** 2))

            if chunksize < frames:
                outdata[chunksize:] = 0
                raise sd.CallbackStop()
            current_frame += chunksize

        def finished_callback():
            self.event.set()

        stream = sd.OutputStream(
            samplerate=samplerate,
            channels=audio_data.shape[1] if len(audio_data.shape) > 1 else 1,
            callback=callback,
            finished_callback=finished_callback
        )

        with stream:
            self.event.wait()  # Wait for playback to finish

        return self.level

# Usage
player = AudioPlayer()
final_level = player.play(audio_data, samplerate=44100)
print(f"Final level: {final_level}")
```

## Common Pitfalls

❌ **Using sd.sleep() to wait for play() completion:**
```python
sd.play(audio, fs)
sd.sleep(5000)  # Wrong! Might sleep too long or not long enough
```

✅ **Use sd.wait() instead:**
```python
sd.play(audio, fs)
sd.wait()  # Correct! Waits exactly until playback finishes
```

❌ **Relying on sd.sleep() for accurate timing:**
```python
sd.sleep(1000)  # Might be 1001ms, 1005ms, or more!
```

✅ **Use stream.time for timing:**
```python
start_time = stream.time
# ... do work ...
elapsed = stream.time - start_time  # Accurate timing
```
