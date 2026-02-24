---
source: Official docs (PyPI, GitHub, HuggingFace)
library: Kokoro TTS
package: kokoro
topic: kpipeline-usage-guide
fetched: 2026-02-23T00:00:00Z
official_docs: https://github.com/hexgrad/kokoro
---

# Kokoro TTS - KPipeline Usage Guide

## Installation

```bash
pip install -q kokoro>=0.9.4 soundfile
```

Install espeak-ng (required for English OOD fallback and some non-English languages):

**Linux:**
```bash
apt-get -qq -y install espeak-ng
```

**Windows:**
1. Go to [espeak-ng releases](https://github.com/espeak-ng/espeak-ng/releases)
2. Download the appropriate `*.msi` file (e.g., `espeak-ng-20191129-b702b03-x64.msi`)
3. Run the installer

---

## KPipeline Initialization

The `KPipeline` class is the main interface for Kokoro TTS inference.

### Basic Initialization

```python
from kokoro import KPipeline

# Initialize with language code
pipeline = KPipeline(lang_code='a')  # 'a' for American English
```

### Language Codes

Kokoro supports multiple languages via single-character language codes:

| Language | Code | Notes |
|----------|------|-------|
| 🇺🇸 American English | `a` | Default, `en-us` espeak-ng fallback |
| 🇬🇧 British English | `b` | `en-gb` espeak-ng fallback |
| 🇪🇸 Spanish | `e` | Requires `pip install misaki[en]`, espeak-ng `es` |
| 🇫🇷 French | `f` | espeak-ng `fr-fr` fallback |
| 🇮🇳 Hindi | `h` | espeak-ng `hi` fallback |
| 🇮🇹 Italian | `i` | espeak-ng `it` fallback |
| 🇯🇵 Japanese | `j` | Requires `pip install misaki[ja]` |
| 🇧🇷 Brazilian Portuguese | `p` | espeak-ng `pt-br` fallback |
| 🇨🇳 Mandarin Chinese | `z` | Requires `pip install misaki[zh]` |

**Important:** Make sure the `lang_code` matches your selected voice.

---

## Calling the Pipeline to Generate Audio

### Basic Usage

```python
from kokoro import KPipeline
import soundfile as sf

pipeline = KPipeline(lang_code='a')
text = "Hello world!"

# Generate audio - returns a generator
generator = pipeline(text, voice='af_heart')

# Iterate over the generator
for i, (gs, ps, audio) in enumerate(generator):
    # gs: graphemes (text)
    # ps: phonemes
    # audio: numpy array of audio samples
    sf.write(f'{i}.wav', audio, 24000)
```

### Pipeline Parameters

```python
generator = pipeline(
    text,           # Input text string
    voice='af_heart',  # Voice name or voice tensor
    speed=1,             # Speed multiplier (default: 1)
    split_pattern=r'\n+' # Regex pattern to split text into chunks
)
```

### Using Voice Tensors Directly

You can load a custom voice tensor:

```python
import torch

# Load a saved voice tensor
voice_tensor = torch.load('path/to/voice.pt', weights_only=True)

# Use the loaded tensor
generator = pipeline(
    text,
    voice=voice_tensor,
    speed=1,
    split_pattern=r'\n+'
)
```

---

## Voice Parameter Usage

### American English Voices (`lang_code='a'`)

| Voice | Gender | Traits | Quality Grade | Training Duration |
|-------|--------|--------|---------------|------------------|
| `af_heart` | F | ❤️ | A | HH hours |
| `af_alloy` | F | - | C | MM minutes |
| `af_aoede` | F | - | C+ | H hours |
| `af_bella` | F | 🔥 | A- | HH hours |
| `af_jessica` | F | - | D | MM minutes |
| `af_kore` | F | - | C+ | H hours |
| `af_nicole` | F | 🎧 | B- | HH hours |
| `af_nova` | F | - | C | MM minutes |
| `af_river` | F | - | D | MM minutes |
| `af_sarah` | F | - | C+ | H hours |
| `af_sky` | F | - | C- | * minutes (very short) |
| `am_adam` | M | - | F+ | H hours |
| `am_echo` | M | - | D | MM minutes |
| `am_eric` | M | - | D | MM minutes |
| `am_fenrir` | M | - | C+ | H hours |
| `am_liam` | M | - | D | MM minutes |
| `am_michael` | M | - | C+ | H hours |
| `am_onyx` | M | - | D | MM minutes |
| `am_puck` | M | - | C+ | H hours |
| `am_santa` | M | - | D- | * minutes (very short) |

### British English Voices (`lang_code='b'`)

| Voice | Gender | Quality Grade | Training Duration |
|-------|--------|---------------|------------------|
| `bf_alice` | F | D | MM minutes |
| `bf_emma` | F | B- | HH hours |
| `bf_isabella` | F | C | MM minutes |
| `bf_lily` | F | D | MM minutes |
| `bm_daniel` | M | D | MM minutes |
| `bm_fable` | M | C | MM minutes |
| `bm_george` | M | C | MM minutes |
| `bm_lewis` | M | D+ | H hours |

### Other Languages

**Japanese (`lang_code='j'`):** `jf_alpha`, `jf_gongitsune`, `jf_nezumi`, `jf_tebukuro`, `jm_kumo`

**Mandarin Chinese (`lang_code='z'`):** `zf_xiaobei`, `zf_xiaoni`, `zf_xiaoxiao`, `zf_xiaoyi`, `zm_yunjian`, `zm_yunxi`, `zm_yunxia`, `zm_yunyang`

**Spanish (`lang_code='e'`):** `ef_dora`, `em_alex`, `em_santa`

**French (`lang_code='f'`):** `ff_siwis`

**Hindi (`lang_code='h'`):** `hf_alpha`, `hf_beta`, `hm_omega`, `hm_psi`

**Italian (`lang_code='i'`):** `if_sara`, `im_nicola`

**Brazilian Portuguese (`lang_code='p'`):** `pf_dora`, `pm_alex`, `pm_santa`

### Voice Performance Notes

- **Goldilocks range:** Most voices perform best on 100-200 tokens (out of ~500 possible)
- **Weakness on short utterances:** Especially less than 10-20 tokens
- **Rushing on long utterances:** Especially over 400 tokens

### Voice Quality Grades

- **A/H**: Highest quality, longest training (HH = 10-100 hours)
- **B/H**: High quality, good training
- **C/H**: Moderate quality
- **D/H**: Lower quality, shorter training
- ***/M**: Very short training (M = 1-10 minutes, MM = 10-100 minutes)

---

## What the Generator Yields

The `pipeline()` method returns a generator that yields tuples of `(graphemes, phonemes, audio)`:

```python
for i, (gs, ps, audio) in enumerate(generator):
    print(i)         # Index (integer)
    print(gs)        # Graphemes - the text segment being processed (string)
    print(ps)        # Phonemes - phonetic representation (string)
    # audio           # Numpy array of audio samples (24kHz, int16 format)
```

### Example Output

```python
text = "The sky above the port was the color of television."

generator = pipeline(text, voice='af_heart')

for i, (gs, ps, audio) in enumerate(generator):
    print(f"Segment {i}:")
    print(f"  Graphemes: {gs}")
    print(f"  Phonemes:  {ps}")
    print(f"  Audio shape: {audio.shape}")
    print(f"  Audio dtype: {audio.dtype}")
```

Output:
```
Segment 0:
  Graphemes: The sky above the port was the color of television.
  Phonemes:  ðə skˈɪ əbˈʌv ðə pˈɔɹt wʌz ðə kˈʌləɹ ʌv tˈɛləvˌɪʒən.
  Audio shape: (58464,)
  Audio dtype: float32
```

### Audio Specifications

- **Sample rate:** 24000 Hz (24 kHz)
- **Data type:** float32 (numpy array)
- **Channels:** Mono
- **Format:** Raw PCM audio (use `soundfile` or similar to save)

### Saving Audio

```python
import soundfile as sf

for i, (gs, ps, audio) in enumerate(generator):
    sf.write(f'output_{i}.wav', audio, 24000)
```

---

## Advanced Usage Example

```python
from kokoro import KPipeline
from IPython.display import display, Audio
import soundfile as sf
import torch

# Initialize pipeline
pipeline = KPipeline(lang_code='a')

# Input text
text = '''
The sky above the port was the color of television, tuned to a dead channel.
"It's not like I'm using," Case heard someone say.
'''

# Generate with custom parameters
generator = pipeline(
    text,
    voice='af_heart',
    speed=1,
    split_pattern=r'\n+'
)

# Process each segment
for i, (gs, ps, audio) in enumerate(generator):
    print(f"Segment {i}: {len(gs)} characters")
    print(f"Phonemes: {ps[:50]}...")  # Print first 50 chars
    
    # Display audio (in Jupyter/Colab)
    display(Audio(data=audio, rate=24000, autoplay=(i==0)))
    
    # Save to file
    sf.write(f'segment_{i}.wav', audio, 24000)
```

---

## Performance Notes

- **Realtime speed:** 35x-100x (generation time to output audio length)
- **Chunking:** Text is automatically split at sentence boundaries
- **Speed parameter:** Use `speed` to adjust playback rate (default: 1.0)
- **Token limits:** ~500 tokens maximum per segment (model constraint)

---

## Platform-Specific Notes

### macOS Apple Silicon (M1/M2/M3/M4)
Enable GPU acceleration:
```bash
PYTORCH_ENABLE_MPS_FALLBACK=1 python your-script.py
```

### Windows
See the [official espeak-ng Windows guide](https://github.com/espeak-ng/espeak-ng/blob/master/docs/guide.md) for advanced configuration.

### GPU vs CPU
- **GPU:** ~300ms first token latency
- **CPU:** ~3500ms first token latency (older i7), <1s (M3 Pro)
