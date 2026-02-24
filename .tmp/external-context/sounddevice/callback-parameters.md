---
source: Official docs (python-sounddevice.readthedocs.io)
library: sounddevice
package: python-sounddevice
topic: callback parameters
fetched: 2026-02-23T12:00:00Z
official_docs: https://python-sounddevice.readthedocs.io/en/0.4.6/api/streams.html
---

# Callback Parameters

## Stream Callback (Full Duplex)

```python
callback(indata: numpy.ndarray, outdata: numpy.ndarray,
         frames: int, time: CData, status: CallbackFlags) -> None
```

Used by `Stream` class for simultaneous input and output.

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `indata` | numpy.ndarray | Input buffer with shape `(frames, channels)` |
| `outdata` | numpy.ndarray | Output buffer with shape `(frames, channels)` - must fill this |
| `frames` | int | Number of frames to process |
| `time` | CData | Timestamp structure |
| `status` | CallbackFlags | Status flags for overflow/underflow |

### time Structure Attributes

```python
time.inputBufferAdcTime   # ADC capture time of first input sample (seconds)
time.outputBufferDacTime   # DAC output time of first output sample (seconds)
time.currentTime           # Time callback was invoked (seconds)
```

These timestamps are synchronized with `stream.time` for the associated stream.

### status (CallbackFlags)

The `status` object indicates error conditions:

- Check with `if status:` to see if any flags are set
- `status.input_overflow` - Input data was discarded
- `status.output_underflow` - Output buffer underflow
- `status.priming_output` - Initial priming of output buffer

## InputStream Callback

```python
callback(indata: numpy.ndarray, frames: int,
         time: CData, status: CallbackFlags) -> None
```

Used by `InputStream` class for input-only streams.

**Note:** Does NOT include `outdata` parameter.

### Example with Level Calculation

```python
def audio_callback(indata, frames, time, status):
    if status:
        print(f"Status: {status}")

    # Calculate RMS level for level meter visualization
    level = np.sqrt(np.mean(indata**2))
    print(f"RMS Level: {level:.4f}")

    # Or calculate peak level
    peak = np.max(np.abs(indata))
    print(f"Peak Level: {peak:.4f}")
```

## OutputStream Callback

```python
callback(outdata: numpy.ndarray, frames: int,
         time: CData, status: CallbackFlags) -> None
```

Used by `OutputStream` class for output-only streams.

**Note:** Does NOT include `indata` parameter. Must fill `outdata` buffer.

### Example with Silence

```python
def output_callback(outdata, frames, time, status):
    if status:
        print(status)
    # Fill with zeros (silence)
    outdata.fill(0)
```

## Modifying Callback Buffers

### Common Pattern 1: Fill entire output buffer

```python
def callback(outdata, frames, time, status):
    outdata[:] = my_audio_data  # Fill entire buffer
```

### Common Pattern 2: Fill specific channel

```python
def callback(indata, outdata, frames, time, status):
    outdata[:, 0] = indata[:, 0]  # Copy channel 1
    outdata[:, 1] = indata[:, 1]  # Copy channel 2
```

### Common Pattern 3: Partial fill (end of stream)

```python
def callback(outdata, frames, time, status):
    global current_frame, audio_data
    chunk_size = min(len(audio_data) - current_frame, frames)
    outdata[:chunk_size] = audio_data[current_frame:current_frame+chunk_size]
    if chunk_size < frames:
        outdata[chunk_size:] = 0  # Fill rest with zeros
        raise sd.CallbackStop()
    current_frame += chunk_size
```

### ❌ Wrong Way - Won't work

```python
def callback(outdata, frames, time, status):
    outdata = my_data  # This only rebinds the name, doesn't modify buffer!
```

## Handling Callback Exceptions

The callback can control stream behavior by raising exceptions:

### CallbackStop

Stop the stream gracefully after processing all generated buffers:

```python
def callback(indata, frames, time, status):
    # ... process data ...
    if should_stop:
        raise sd.CallbackStop()
```

### CallbackAbort

Stop the stream immediately, discarding pending buffers:

```python
def callback(indata, frames, time, status):
    if critical_error:
        raise sd.CallbackAbort()
```

### Other Exceptions

Any other exception will:
1. Stop the callback from being called again
2. Print traceback to stderr
3. Continue running main program (exception not propagated)

**Important:** Even if an exception is raised, the callback must fill the entire `outdata` buffer (for output streams).

## finished_callback

Called when stream becomes inactive (stopped, aborted, or exception raised):

```python
def finished():
    print("Stream finished!")

stream = sd.InputStream(callback=audio_callback,
                        finished_callback=finished)
```

### For output streams with CallbackStop

The finished callback is called after all generated audio has been played:

```python
def finished():
    print("Playback complete!")

stream = sd.OutputStream(callback=output_callback,
                        finished_callback=finished)
```

## Performance Considerations

### Do NOT do in callback:
- Allocate memory
- Access file system
- Make network calls
- Call functions that may block
- Call PortAudio API functions (except `cpu_load`)

### Safe operations:
- NumPy array operations
- Simple math calculations
- Queuing data for processing in main thread
- Updating shared variables

### Example: Safe pattern for visualization

```python
import queue

q = queue.Queue(maxsize=10)

def audio_callback(indata, frames, time, status):
    if status:
        print(status, file=sys.stderr)
    # Calculate level and queue for main thread
    level = abs(indata).mean()
    try:
        q.put_nowait(level)
    except queue.Full:
        pass  # Drop if queue is full

# In main thread:
while True:
    level = q.get()  # Blocking get from queue
    # Update visualization
    update_level_meter(level)
```

## Real-time Level Monitoring Example

```python
import sounddevice as sd
import numpy as np
import queue

q = queue.Queue()

def audio_callback(indata, frames, time, status):
    if status:
        print(f"Status: {status}")

    # Calculate RMS level
    rms = np.sqrt(np.mean(indata**2))
    peak = np.max(np.abs(indata))

    # Queue for main thread visualization
    try:
        q.put_nowait({'rms': rms, 'peak': peak})
    except queue.Full:
        pass

stream = sd.InputStream(samplerate=44100, channels=1,
                        dtype='float32', callback=audio_callback)

with stream:
    while True:
        level_info = q.get()
        print(f"RMS: {level_info['rms']:.6f}, Peak: {level_info['peak']:.6f}")
```

## Callback Timing

The callback runs at very high or real-time priority. It must consistently meet time deadlines.

- Reasonable CPU utilization: Up to 70% or more of available CPU time
- For high CPU utilization: Use `blocksize=0` for most robust behavior
- Callback execution time should be less than: `frames / samplerate` seconds

Example for 1024 frames at 44100 Hz:
```
Maximum callback time = 1024 / 44100 ≈ 23.2 ms
```

## CPU Load Monitoring

You can check CPU load in the callback or from the main thread:

```python
def callback(indata, frames, time, status):
    cpu_load = stream.cpu_load  # 0.0 to 1.0 (can exceed 1.0)
    if cpu_load > 0.8:
        print(f"Warning: High CPU load: {cpu_load:.2%}")
    # ... process data ...
```

For blocking read/write streams, `cpu_load` always returns 0.0.
