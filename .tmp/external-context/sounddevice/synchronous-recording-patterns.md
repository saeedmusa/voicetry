---
source: Official docs (python-sounddevice.readthedocs.io)
library: sounddevice
package: python-sounddevice
topic: synchronous recording patterns
fetched: 2026-02-23T12:00:00Z
official_docs: https://python-sounddevice.readthedocs.io/en/0.4.6/examples.html
---

# Synchronous Recording Patterns

## Overview

Sounddevice supports two recording modes:
1. **Callback mode** - Asynchronous, callback processes audio blocks
2. **Blocking mode** - Synchronous, your code calls `read()` to get audio

For a simple synchronous recorder with level callbacks, you have two main patterns:
- **Pattern A:** Blocking `read()` with periodic level checks
- **Pattern B:** Callback for level monitoring + separate `read()` for recording

## Pattern A: Pure Blocking Recording

### Basic Pattern

```python
import sounddevice as sd
import numpy as np

samplerate = 44100
duration = 5  # seconds
channels = 1
frames = int(samplerate * duration)

# Create recording buffer
recording = np.empty((frames, channels), dtype='float32')

# Open stream in blocking mode (no callback)
stream = sd.InputStream(samplerate=samplerate,
                       channels=channels,
                       dtype='float32')

with stream:
    print("Recording...")
    for i in range(0, frames, 1024):
        chunk_size = min(1024, frames - i)
        data, overflowed = stream.read(chunk_size)
        recording[i:i+chunk_size] = data

        if overflowed:
            print(f"Warning: Input overflow at frame {i}")

        # Optional: Calculate level for display
        level = np.sqrt(np.mean(data**2))
        print(f"\rLevel: {level:.6f}", end="", flush=True)

print(f"\nDone! Recorded {len(recording)} frames")
```

### Using read_available for non-blocking checks

```python
import sounddevice as sd
import numpy as np

samplerate = 44100
channels = 1

stream = sd.InputStream(samplerate=samplerate,
                       channels=channels,
                       dtype='float32')

recording = []

with stream:
    print("Recording (press Ctrl+C to stop)...")
    try:
        while True:
            # Check available frames
            available = stream.read_available
            if available > 0:
                # Read all available data
                chunk_size = min(1024, available)
                data, overflowed = stream.read(chunk_size)
                recording.append(data)

                # Calculate level
                level = np.sqrt(np.mean(data**2))
                print(f"\rLevel: {level:.6f} | Frames: {len(recording)*1024}",
                      end="", flush=True)
    except KeyboardInterrupt:
        print("\nRecording stopped by user")

# Combine all chunks
full_recording = np.concatenate(recording)
print(f"Total frames: {len(full_recording)}")
```

## Pattern B: Callback for Level + Blocking for Recording

### Stream callback handles level monitoring

```python
import sounddevice as sd
import numpy as np
import queue

samplerate = 44100
duration = 5  # seconds
frames = int(samplerate * duration)
channels = 1

# Queue for level data from callback
level_queue = queue.Queue(maxsize=100)

def level_callback(indata, frames, time, status):
    """Callback only for level monitoring"""
    if status:
        print(f"Callback status: {status}")

    # Calculate and queue level info
    rms = np.sqrt(np.mean(indata**2))
    peak = np.max(np.abs(indata))

    try:
        level_queue.put_nowait({'rms': rms, 'peak': peak})
    except queue.Full:
        pass  # Drop if queue is full

# Open stream with callback
stream = sd.InputStream(samplerate=samplerate,
                       channels=channels,
                       dtype='float32',
                       callback=level_callback)

recording = np.empty((frames, channels), dtype='float32')

with stream:
    print("Recording with level monitoring...")

    # Synchronously read while callback provides level updates
    for i in range(0, frames, 1024):
        chunk_size = min(1024, frames - i)
        data, overflowed = stream.read(chunk_size)
        recording[i:i+chunk_size] = data

        if overflowed:
            print(f"Warning: Input overflow at frame {i}")

        # Get latest level info from callback
        while not level_queue.empty():
            level_info = level_queue.get_nowait()
            print(f"\rRMS: {level_info['rms']:.6f} | "
                  f"Peak: {level_info['peak']:.6f}",
                  end="", flush=True)

print(f"\nDone! Recorded {len(recording)} frames")
```

## Pattern C: Separate Threads

### Main thread handles recording, callback handles levels

```python
import sounddevice as sd
import numpy as np
import queue
import threading
import time

samplerate = 44100
duration = 10  # seconds
frames = int(samplerate * duration)
channels = 1

# Thread-safe queue for level data
level_queue = queue.Queue()

# Event to stop recording
stop_event = threading.Event()

def level_callback(indata, frames, time_info, status):
    """Callback runs in separate thread, provides level info"""
    if status:
        print(f"Status: {status}", file=sys.stderr)

    rms = np.sqrt(np.mean(indata**2))
    peak = np.max(np.abs(indata))

    try:
        level_queue.put_nowait({
            'rms': rms,
            'peak': peak,
            'time': time_info.currentTime
        })
    except queue.Full:
        pass

# Open stream with callback
stream = sd.InputStream(samplerate=samplerate,
                       channels=channels,
                       dtype='float32',
                       callback=level_callback)

recording = []

def record_audio():
    """Recording loop in main thread"""
    with stream:
        print("Recording...")
        while not stop_event.is_set():
            # Check available frames
            available = stream.read_available
            if available >= 1024:
                data, overflowed = stream.read(1024)
                recording.append(data)

                if overflowed:
                    print("Warning: Input overflow")

def display_levels():
    """Level display in separate thread"""
    while not stop_event.is_set():
        try:
            level_info = level_queue.get(timeout=0.1)
            print(f"\rRMS: {level_info['rms']:.6f} | "
                  f"Peak: {level_info['peak']:.6f}",
                  end="", flush=True)
        except queue.Empty:
            pass

# Start level display thread
level_thread = threading.Thread(target=display_levels)
level_thread.daemon = True
level_thread.start()

# Record for specified duration
start_time = time.time()
try:
    while time.time() - start_time < duration:
        record_audio()
except KeyboardInterrupt:
    print("\nRecording stopped by user")
finally:
    stop_event.set()
    level_thread.join(timeout=1)

# Combine recording
full_recording = np.concatenate(recording)
print(f"\nTotal frames: {len(full_recording)}")
```

## Pattern D: Async Recording with asyncio

### Modern async/await pattern

```python
import sounddevice as sd
import numpy as np
import asyncio
import queue

samplerate = 44100
duration = 5  # seconds
frames = int(samplerate * duration)
channels = 1

level_queue = queue.Queue()

def level_callback(indata, frames, time_info, status):
    """Callback queues level info"""
    if status:
        print(f"Status: {status}")
    rms = np.sqrt(np.mean(indata**2))
    try:
        level_queue.put_nowait(rms)
    except queue.Full:
        pass

async def display_levels():
    """Async task to display levels"""
    while True:
        try:
            level = level_queue.get_nowait()
            print(f"\rRMS Level: {level:.6f}", end="", flush=True)
        except queue.Empty:
            await asyncio.sleep(0.01)

async def record_audio():
    """Async recording task"""
    recording = np.empty((frames, channels), dtype='float32')
    stream = sd.InputStream(samplerate=samplerate,
                           channels=channels,
                           dtype='float32',
                           callback=level_callback)

    with stream:
        print("Recording...")
        for i in range(0, frames, 1024):
            chunk_size = min(1024, frames - i)
            data, overflowed = stream.read(chunk_size)
            recording[i:i+chunk_size] = data
            await asyncio.sleep(0)  # Yield to event loop

    return recording

async def main():
    # Start level display task
    display_task = asyncio.create_task(display_levels())

    # Record
    recording = await record_audio()

    # Cancel display task
    display_task.cancel()
    try:
        await display_task
    except asyncio.CancelledError:
        pass

    print(f"\nDone! Recorded {len(recording)} frames")

# Run with: asyncio.run(main())
```

## Comparison of Patterns

| Pattern | Pros | Cons | Best For |
|---------|------|------|----------|
| **Pure Blocking** | Simple, no threading | Level checks in recording loop | Simple applications |
| **Callback + Blocking** | Clean separation | Callback overhead | Most use cases |
| **Separate Threads** | Parallel processing | More complex | Heavy visualization |
| **Async/await** | Modern, clean | Requires Python 3.7+ | Async applications |

## Common Mistakes

### 1. Blocking in callback

❌ Wrong:
```python
def callback(indata, frames, time, status):
    level = calculate_level(indata)
    print(level)  # Blocking I/O in callback!
```

✅ Correct:
```python
def callback(indata, frames, time, status):
    level = calculate_level(indata)
    try:
        q.put_nowait(level)  # Non-blocking queue
    except queue.Full:
        pass
```

### 2. Forgetting to check overflow

❌ Wrong:
```python
data, _ = stream.read(1024)  # Ignoring overflow!
```

✅ Correct:
```python
data, overflowed = stream.read(1024)
if overflowed:
    print("Warning: Input overflow - frames were dropped!")
```

### 3. Using wrong buffer assignment

❌ Wrong:
```python
def callback(outdata, frames, time, status):
    outdata = my_data  # Only rebinds name!
```

✅ Correct:
```python
def callback(outdata, frames, time, status):
    outdata[:] = my_data  # Actually modifies buffer
```

### 4. Not handling partial reads

❌ Wrong:
```python
recording = []
while True:
    data, _ = stream.read(1024)  # May block forever!
    recording.append(data)
```

✅ Correct:
```python
recording = []
while not done:
    available = stream.read_available
    if available >= 1024:
        data, _ = stream.read(1024)
        recording.append(data)
```

## Recommended Pattern for Simple Recorder

For a simple synchronous recorder with level visualization:

```python
import sounddevice as sd
import numpy as np
import queue

samplerate = 44100
duration = 5
frames = int(samplerate * duration)

# Queue for level updates from callback
level_queue = queue.Queue()

def level_callback(indata, frames, time, status):
    """Callback provides level monitoring"""
    if status:
        print(f"Status: {status}")
    rms = np.sqrt(np.mean(indata**2))
    try:
        level_queue.put_nowait(rms)
    except queue.Full:
        pass

# Stream with callback for levels
stream = sd.InputStream(samplerate=samplerate,
                       channels=1,
                       dtype='float32',
                       callback=level_callback)

recording = np.empty((frames, 1), dtype='float32')

with stream:
    print("Recording...")
    for i in range(0, frames, 1024):
        chunk_size = min(1024, frames - i)
        data, overflowed = stream.read(chunk_size)
        recording[i:i+chunk_size] = data

        # Display latest level
        while not level_queue.empty():
            level = level_queue.get_nowait()
            print(f"\rLevel: {level:.6f} | Progress: {i}/{frames}",
                  end="", flush=True)

print(f"\nDone! Recorded {len(recording)} frames")
```

This pattern gives you:
- ✅ Synchronous recording control
- ✅ Real-time level monitoring via callback
- ✅ Clean separation of concerns
- ✅ No blocking in callback
- ✅ Simple and maintainable code
