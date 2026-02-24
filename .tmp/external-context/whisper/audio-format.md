---
source: GitHub (openai/whisper)
library: OpenAI Whisper
package: openai-whisper
topic: audio-format
fetched: 2026-02-23T21:46:00Z
official_docs: https://github.com/openai/whisper
---

# Whisper Audio Format and Sample Rate

## Sample Rate

**Required sample rate: 16000 Hz (16 kHz)**

Whisper requires audio to be at 16 kHz sample rate. The library will automatically resample audio to this rate when using the `load_audio()` function.

```python
# Audio hyperparameters (from whisper/audio.py)
SAMPLE_RATE = 16000
N_FFT = 400
HOP_LENGTH = 160
CHUNK_LENGTH = 30
N_SAMPLES = CHUNK_LENGTH * SAMPLE_RATE  # 480000 samples in a 30-second chunk
N_FRAMES = N_SAMPLES // HOP_LENGTH  # 3000 frames in a mel spectrogram
```

## Supported Audio Formats

Whisper supports any audio format that can be processed by **FFmpeg**, including:

- MP3 (`.mp3`)
- WAV (`.wav`)
- FLAC (`.flac`)
- M4A (`.m4a`)
- OGG (`.ogg`)
- AAC (`.aac`)
- And any other format supported by FFmpeg

### Prerequisite

You must have `ffmpeg` installed on your system:

```bash
# Ubuntu or Debian
sudo apt update && sudo apt install ffmpeg

# macOS (Homebrew)
brew install ffmpeg

# Windows (Chocolatey)
choco install ffmpeg

# Windows (Scoop)
scoop install ffmpeg
```

## Loading Audio

### From File Path (Automatic Resampling)

```python
import whisper

# Load and automatically resample to 16 kHz
audio = whisper.load_audio("audio.mp3")
print(audio.shape)  # (num_samples,)
print(audio.dtype)  # float32
```

The `load_audio()` function:
1. Decodes audio using FFmpeg
2. Down-mixes to mono (single channel)
3. Resamples to 16 kHz if necessary
4. Returns a NumPy array of float32 values normalized to [-1, 1]

### From File Path with Explicit Sample Rate

```python
audio = whisper.load_audio("audio.wav", sr=16000)
```

### Direct Audio Input (Preprocessed)

You can also pass a pre-loaded NumPy array or PyTorch tensor directly:

```python
import numpy as np

# Audio must already be at 16 kHz
audio_array = np.random.randn(480000).astype(np.float32)  # 30 seconds at 16 kHz

result = model.transcribe(audio_array)
```

## Audio Processing

### Padding/Trimming

```python
from whisper import pad_or_trim

# Trim or pad audio to exactly 30 seconds (480000 samples at 16 kHz)
audio = whisper.load_audio("audio.mp3")
audio = pad_or_trim(audio)  # Shape: (480000,)
```

### Log-Mel Spectrogram

```python
from whisper import log_mel_spectrogram

# Convert audio to log-Mel spectrogram
mel = log_mel_spectrogram(audio)
print(mel.shape)  # (80, 3000) - 80 mel bands, 3000 frames for 30 seconds
```

### Loading Pre-loaded Audio (NumPy Array or Tensor)

```python
import whisper
import numpy as np

# If you have audio as a numpy array (must be at 16 kHz)
audio_data = np.load("preloaded_audio.npy")

# Pad/trim to 30 seconds if needed
audio_data = whisper.pad_or_trim(audio_data)

# Transcribe
result = model.transcribe(audio_data)
```

## Technical Details

### FFmpeg Command Used

The `load_audio()` function uses this FFmpeg command internally:

```bash
ffmpeg -nostdin -threads 0 -i audio.mp3 -f s16le -ac 1 -acodec pcm_s16le -ar 16000 -
```

- `-nostdin`: Don't read from stdin
- `-threads 0`: Use optimal thread count
- `-ac 1`: Convert to mono (single channel)
- `-acodec pcm_s16le`: Output as 16-bit PCM, little-endian
- `-ar 16000`: Resample to 16 kHz

### Normalization

Audio is normalized to float32 values in the range [-1, 1]:

```python
# From int16 range [-32768, 32767] to float32 [-1.0, 1.0]
audio = np.frombuffer(out, np.int16).flatten().astype(np.float32) / 32768.0
```

### Frame and Time Calculations

```python
# 30-second window
CHUNK_LENGTH = 30  # seconds
SAMPLE_RATE = 16000  # Hz
N_SAMPLES = CHUNK_LENGTH * SAMPLE_RATE  # 480000 samples

# STFT parameters
N_FFT = 400  # FFT window size
HOP_LENGTH = 160  # Hop between frames

# Derived values
N_FRAMES = N_SAMPLES // HOP_LENGTH  # 3000 frames
FRAMES_PER_SECOND = SAMPLE_RATE // HOP_LENGTH  # 100 frames/second (10ms per frame)
```
