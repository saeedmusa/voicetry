---
source: Official Docs
library: sounddevice
package: sounddevice
topic: stream-status
fetched: 2026-02-23T00:00:00Z
official_docs: https://python-sounddevice.readthedocs.io/
---

# Stream Status with sd.get_stream().active

## sd.get_stream()

Get a reference to the current stream created by `play()`, `rec()`, or `playrec()`:

```python
import sounddevice as sd

sd.play(audio, fs)
stream = sd.get_stream()

# Returns: OutputStream, InputStream, or Stream object
print(type(stream))  # <class 'sounddevice.OutputStream'>
```

## Stream.active property

Check if a stream is currently playing/recording:

```python
import sounddevice as sd

sd.play(audio, fs)
stream = sd.get_stream()

print(stream.active)  # True - stream is active

sd.wait()
print(stream.active)  # False - stream is stopped
```

## When is a stream active?

A stream is **active** after a successful call to `start()`, until it becomes inactive due to:
- A call to `stop()` or `abort()`
- An exception raised in the stream callback
- In the latter case (exception), stream is considered inactive after the last buffer has finished playing

## Stream states

| Property | Description |
|----------|-------------|
| `active` | `True` when stream is running (after start(), until stop/abort/callback exception) |
| `stopped` | `True` when stream is stopped (before start(), after stop()/abort()) |
| `closed` | `True` after `close()` is called |

```python
import sounddevice as sd

# Create a stream
stream = sd.OutputStream(samplerate=44100, channels=1)

print(stream.active)   # False - not started yet
print(stream.stopped)  # True  - stream is stopped
print(stream.closed)   # False - not closed

stream.start()
print(stream.active)   # True  - now playing
print(stream.stopped)  # False - no longer stopped

stream.stop()
print(stream.active)   # False - stopped
print(stream.stopped)  # True  - back to stopped

stream.close()
print(stream.closed)   # True  - now closed
```

## Checking stream status for convenience functions

When using `play()`, `rec()`, or `playrec()`:

```python
import sounddevice as sd
import time

# Start non-blocking playback
sd.play(audio, fs)

# Check if still playing
while sd.get_stream().active:
    print("Still playing...")
    time.sleep(0.1)

print("Done!")
```

## Using get_status() for error checking

`get_status()` returns `CallbackFlags` with information about overflows/underflows:

```python
import sounddevice as sd

sd.play(audio, fs)
status = sd.wait()  # Returns CallbackFlags or None

if status:
    if status.output_underflow:
        print("Warning: Output underflow occurred")
```

## Stream attributes for monitoring

| Attribute | Description |
|-----------|-------------|
| `active` | Stream is active (running) |
| `stopped` | Stream is stopped |
| `closed` | Stream is closed |
| `cpu_load` | CPU usage fraction (0.0 to 1.0+, only for callback streams) |
| `time` | Current stream time in seconds |
| `latency` | Actual input/output latency in seconds |

```python
import sounddevice as sd

sd.play(audio, fs)
stream = sd.get_stream()

print(f"CPU load: {stream.cpu_load:.2%}")
print(f"Stream time: {stream.time:.3f}s")
print(f"Latency: {stream.latency*1000:.1f}ms")
```

## Best Practices

1. **Always check if stream exists**: `sd.get_stream()` only works for streams created by `play()/rec()/playrec()`, not for manually created streams
2. **Use `active` not `stopped`**: For checking if playback is ongoing, `active` is more intuitive
3. **Monitor CPU load**: High CPU load (>70%) may cause underflows
4. **Handle underflows**: Check `get_status()` after `wait()` to detect issues
