---
source: Official docs (python-sounddevice.readthedocs.io)
library: sounddevice
package: python-sounddevice
topic: InputStream usage
fetched: 2026-02-23T12:00:00Z
official_docs: https://python-sounddevice.readthedocs.io/en/0.4.6/api/streams.html
---

# InputStream Usage

## Class Definition

```python
class sounddevice.InputStream(samplerate=None, blocksize=None, device=None,
                               channels=None, dtype=None, latency=None,
                               extra_settings=None, callback=None,
                               finished_callback=None, clip_off=None,
                               dither_off=None, never_drop_input=None,
                               prime_output_buffers_using_stream_callback=None)
```

PortAudio input stream (using NumPy).

This has the same methods and attributes as `Stream`, except `write()` and `write_available`. Furthermore, the stream callback is expected to have a different signature.

## Parameters

- **samplerate** (float, optional) - The desired sampling frequency
- **blocksize** (int, optional) - The number of frames per callback (0 = optimal/variable)
- **device** (int or str, optional) - Device index or query string
- **channels** (int, optional) - Number of input channels
- **dtype** (str, optional) - Sample format: 'float32', 'int32', 'int16', 'int8', 'uint8'
- **latency** (float or {'low', 'high'}, optional) - Desired latency in seconds
- **callback** (callable, optional) - User-supplied function to consume audio
- **finished_callback** (callable, optional) - Called when stream becomes inactive

## Callback Signature

For InputStream, the callback must have this signature:

```python
callback(indata: numpy.ndarray, frames: int,
         time: CData, status: CallbackFlags) -> None
```

**Parameters:**
- `indata` - Input buffer as 2D NumPy array with shape `(frames, channels)`
- `frames` - Number of frames to process (same as buffer length)
- `time` - CFFI structure with timestamps:
  - `time.inputBufferAdcTime` - ADC capture time of first sample
  - `time.currentTime` - When callback was invoked
- `status` - CallbackFlags instance indicating overflow/underflow conditions

**Important:** Unlike Stream callback, InputStream callback does NOT receive `outdata` parameter.

## Synchronous Recording (Blocking Mode)

When `callback` is NOT provided, the stream operates in blocking mode. Use `read()` method:

```python
# Open stream without callback
stream = sd.InputStream(samplerate=44100, channels=1, dtype='float32')

# Read a specific number of frames
data, overflowed = stream.read(frames=1024)

# data is a NumPy array with shape (frames, channels)
# overflowed is True if data was discarded by PortAudio
```

### read() Method

```python
read(frames) -> (numpy.ndarray, bool)
```

- **frames** (int) - Number of frames to read
- **Returns:** Tuple of (data, overflowed)
- **data** - 2D NumPy array with shape `(frames, channels)`
- **overflowed** - True if input overflow occurred

## Context Manager Usage

InputStream can be used as a context manager:

```python
with sd.InputStream(samplerate=44100, channels=1, dtype='float32') as stream:
    # Stream is automatically started
    data, overflowed = stream.read(1024)
    # Stream is automatically stopped and closed on exit
```

## Key Attributes

- `samplerate` - Current sampling frequency in Hz
- `channels` - Number of input channels
- `dtype` - Data type of audio samples
- `blocksize` - Number of frames per block (0 = variable)
- `read_available` - Number of frames readable without blocking
- `active` - True when stream is running
- `stopped` - True when stream is stopped
- `closed` - True after close() is called
- `cpu_load` - Fraction of CPU time consumed by callback stream (0.0 to 1.0+)
- `time` - Current stream time in seconds
- `latency` - Actual input latency in seconds
- `device` - Input device ID

## Methods

- `start()` - Commence audio processing
- `stop(ignore_errors=True)` - Stop audio processing (waits for buffers)
- `abort(ignore_errors=True)` - Stop immediately (discards pending buffers)
- `close(ignore_errors=True)` - Close the stream

## Example: Basic InputStream with Callback

```python
import sounddevice as sd

def audio_callback(indata, frames, time, status):
    if status:
        print(status)
    # Process indata here (e.g., calculate level for visualization)
    level = abs(indata).mean()
    print(f"Level: {level:.4f}")

stream = sd.InputStream(samplerate=44100, channels=1, callback=audio_callback)
with stream:
    input("Press Enter to stop...\n")
```

## Example: Synchronous Recording with read()

```python
import sounddevice as sd
import numpy as np

samplerate = 44100
duration = 5  # seconds
frames = int(samplerate * duration)

stream = sd.InputStream(samplerate=samplerate, channels=1, dtype='float32')
with stream:
    print("Recording...")
    recording = np.empty((frames, 1), dtype='float32')
    for i in range(0, frames, 1024):
        chunk_size = min(1024, frames - i)
        data, overflowed = stream.read(chunk_size)
        recording[i:i+chunk_size] = data
        if overflowed:
            print("Warning: Input overflow occurred!")

print(f"Recorded {len(recording)} frames")
```

## Common Issues

1. **Callback must not block:** Avoid file I/O, network calls, or long computations in callback
2. **Use `indata[:]` to modify:** Assigning directly won't work (`indata = newdata` doesn't modify buffer)
3. **Non-zero blocksize may add latency:** For minimal latency, use `blocksize=0` (default)
4. **Synchronous read() may block:** Check `read_available` first to avoid blocking
