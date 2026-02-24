---
source: Official Docs
library: sounddevice
package: sounddevice
topic: best-practices
fetched: 2026-02-23T00:00:00Z
official_docs: https://python-sounddevice.readthedocs.io/
---

# Best Practices and Recent API Changes

## Version Information

**Current version**: 0.4.6 (released 2023-02-19)

## Recent API Changes

### Version 0.4.6 (2023-02-19)
- Redirect stderr with `os.dup2()` instead of CFFI calls (internal change)

### Version 0.4.5 (2022-08-21)
- Added `index` field to device dictionary
- Requires Python >= 3.7 (dropped Python 2.x support in 0.4.0)
- Added `PaWasapi_IsLoopback()` to low-level interface

### Version 0.4.4 (2021-12-31)
- Exact device string matches can now include the host API name

### Version 0.4.3 (2021-10-20)
- Fixed dimension check in `Stream.write()`
- Universal (x86_64 and arm64) `.dylib` for macOS

### Version 0.4.1 (2020-09-26)
- `CallbackFlags` attributes are now writable (can manually set/clear flags)

### Version 0.4.0 (2020-07-18)
- **Major change**: Dropped support for Python 2.x
- Fixed memory issues in `play()`, `rec()`, and `playrec()`

## Best Practices

### 1. Choosing the Right API

| Use Case | Recommended API |
|----------|-----------------|
| Simple scripts, interactive use | `sd.play()`, `sd.rec()`, `sd.wait()` |
| Gapless playback, multiple overlapping playbacks | `OutputStream` / `InputStream` with callback |
| Processing audio in real-time | Stream with callback |
| Precise timing control | Stream with `Stream.time` property |
| Block-wise processing (not real-time) | Blocking read/write streams |

### 2. Use Callback Streams for Real-time Applications

```python
import sounddevice as sd

def callback(indata, outdata, frames, time, status):
    if status:
        print(f"Status: {status}")
    # Process audio in real-time
    outdata[:] = process(indata)

with sd.Stream(callback=callback):
    sd.sleep(duration * 1000)
```

**Key rules for callbacks:**
- ⚠️ Never block: No file I/O, network, extensive computation
- ⚠️ Always fill the entire output buffer (even when raising exceptions)
- ⚠️ Keep it fast: Use at most 70% of available callback time
- ✅ Use `blocksize=0` for high CPU load situations (more robust)

### 3. Set Appropriate Latency and Blocksize

```python
import sounddevice as sd

# For robust playback (higher latency, fewer glitches)
stream = sd.OutputStream(
    samplerate=44100,
    latency='high',  # or 0.1 (seconds) like Audacity
    blocksize=2048
)

# For low-latency interactive apps
stream = sd.OutputStream(
    samplerate=44100,
    latency='low',
    blocksize=0  # Let PortAudio choose optimal size
)
```

**Troubleshooting:**
- Output underflow: Increase latency or blocksize
- Input overflow: Reduce callback CPU usage or increase blocksize

### 4. Handle Callback Status Properly

```python
import sounddevice as sd

def callback(outdata, frames, time, status):
    if status:
        if status.output_underflow:
            print("Warning: output underflow - increase latency?")
        if status.input_overflow:
            print("Warning: input overflow - reduce CPU usage?")

    # ... process audio ...
```

### 5. Use finished_callback for Cleanup

```python
import sounddevice as sd
import threading

event = threading.Event()

def finished_callback():
    print("Stream finished!")
    # Cleanup code here
    event.set()

stream = sd.OutputStream(
    callback=callback,
    finished_callback=finished_callback
)

with stream:
    event.wait()  # Clean shutdown
```

### 6. Always Specify Correct Samplerate

```python
import sounddevice as sd

# Wrong: Audio plays at wrong speed
sd.play(audio, fs=48000)  # But audio is 44100!

# Right: Match audio's actual samplerate
sd.play(audio, fs=44100)

# Better: Set defaults
sd.default.samplerate = 44100
sd.play(audio)  # No need to specify fs every time
```

### 7. Use Context Managers for Automatic Cleanup

```python
import sounddevice as sd

# Good: Automatic close on exit
with sd.OutputStream(callback=callback) as stream:
    sd.sleep(5000)
# Stream is automatically closed here

# Also good: Automatic start/stop/close
with sd.Stream(callback=callback) as stream:
    # stream.start() is called automatically
    sd.sleep(5000)
# stream.stop() and stream.close() are called automatically
```

### 8. Avoid Convenience Functions for Complex Use Cases

`sd.play()`, `sd.rec()`, `sd.playrec()` are designed for:
- Small scripts
- Interactive use (Jupyter notebooks)
- Simple one-shot operations

**Limitations:**
- Cannot handle multiple overlapping playbacks
- Cannot do gapless playback
- Limited control over stream behavior

**For production code, use stream classes directly:**

```python
import sounddevice as sd

# Instead of sd.play(audio, fs)
stream = sd.OutputStream(
    samplerate=fs,
    channels=audio.shape[1],
    callback=my_callback
)

with stream:
    # More control, can implement gapless playback, etc.
```

### 9. Proper Error Handling

```python
import sounddevice as sd

try:
    stream = sd.OutputStream(samplerate=44100)
    with stream:
        # ... use stream ...
except sd.PortAudioError as e:
    print(f"PortAudio error: {e.args[0]}")
    print(f"Error code: {e.args[1]}")
    if len(e.args) > 2:
        print(f"Host error: {e.args[2]}")
```

### 10. Device Selection Best Practices

```python
import sounddevice as sd

# Query available devices first
print(sd.query_devices())

# Select by device ID (reliable)
sd.default.device = 5  # Output device ID

# Or by substring (convenient but be specific)
sd.default.device = 'builtin output'  # Case-insensitive

# Include host API for disambiguation
sd.default.device = 'CoreAudio builtin'
```

## Common Mistakes to Avoid

### Mistake 1: Reassigning callback buffer variable

```python
# ❌ WRONG: Just rebinds the variable
def callback(outdata, frames, time, status):
    outdata = my_audio_data  # Doesn't work!

# ✅ CORRECT: Use slice assignment
def callback(outdata, frames, time, status):
    outdata[:] = my_audio_data  # Actually fills the buffer
```

### Mistake 2: Using sd.sleep() for timing

```python
# ❌ WRONG: Not accurate
sd.play(audio, fs)
sd.sleep(5000)

# ✅ CORRECT: Use sd.wait()
sd.play(audio, fs)
sd.wait()
```

### Mistake 3: Blocking in callbacks

```python
# ❌ WRONG: Blocks audio thread
def callback(outdata, frames, time, status):
    data = load_from_file()  # File I/O blocks!
    outdata[:] = data

# ✅ CORRECT: Pre-load or use queues
data = load_from_file()  # Load beforehand
def callback(outdata, frames, time, status):
    outdata[:] = data  # Just copy
```

### Mistake 4: Not filling entire output buffer on error

```python
# ❌ WRONG: Leaves buffer uninitialized
def callback(outdata, frames, time, status):
    if error:
        raise sd.CallbackStop()
    outdata[:] = process()

# ✅ CORRECT: Always fill buffer
def callback(outdata, frames, time, status):
    if error:
        outdata[:] = 0  # Fill with silence
        raise sd.CallbackStop()
    outdata[:] = process()
```

## Performance Tips

1. **Use `float32` dtype**: It's natively supported by PortAudio
2. **Avoid `float64` in streams**: Must be converted to `float32` first
3. **Pre-allocate buffers**: Don't allocate in callbacks
4. **Use C-contiguous arrays**: Required for `Stream.write()`
5. **Monitor `cpu_load`**: Keep under 70% for stability
6. **Use `blocksize=0` for variable buffer sizes**: More robust under load

## Platform-Specific Notes

### macOS
- CoreAudio provides high-quality timing
- Use `CoreAudioSettings` for advanced configuration

### Windows
- WASAPI is recommended (default)
- Use `WasapiSettings` for exclusive mode
- ASIO available with `AsioSettings`

### Linux
- ALSA and JACK available
- Check device capabilities with `check_output_settings()`
