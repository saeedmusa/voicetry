---
source: GitHub (openai/whisper)
library: OpenAI Whisper
package: openai-whisper
topic: transcribe-audio
fetched: 2026-02-23T21:46:00Z
official_docs: https://github.com/openai/whisper
---

# Whisper Transcription

## Basic Usage

```python
import whisper

model = whisper.load_model("turbo")
result = model.transcribe("audio.mp3")
print(result["text"])
```

### Internally

The `transcribe()` method reads the entire file and processes the audio with a sliding 30-second window, performing autoregressive sequence-to-sequence predictions on each window.

## Function Signature

```python
def transcribe(
    model: "Whisper",
    audio: Union[str, np.ndarray, torch.Tensor],
    *,
    verbose: Optional[bool] = None,
    temperature: Union[float, Tuple[float, ...]] = (0.0, 0.2, 0.4, 0.6, 0.8, 1.0),
    compression_ratio_threshold: Optional[float] = 2.4,
    logprob_threshold: Optional[float] = -1.0,
    no_speech_threshold: Optional[float] = 0.6,
    condition_on_previous_text: bool = True,
    initial_prompt: Optional[str] = None,
    carry_initial_prompt: bool = False,
    word_timestamps: bool = False,
    prepend_punctuations: str = "\"'\"¿([{-",
    append_punctuations: str = "\"'.。,，!！?？:：\")]}、",
    clip_timestamps: Union[str, List[float]] = "0",
    hallucination_silence_threshold: Optional[float] = None,
    **decode_options,
)
```

## Key Parameters

### Audio Input

| Parameter | Type | Description |
|-----------|------|-------------|
| `audio` | `Union[str, np.ndarray, torch.Tensor]` | The path to the audio file to open, or the audio waveform |

### Decoding Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `language` | `str` | `None` | Language spoken in the audio. If `None`, language will be auto-detected. |
| `task` | `str` | `"transcribe"` | Either `"transcribe"` (speech-to-text) or `"translate"` (to English) |
| `temperature` | `float` or `tuple` | `(0.0, 0.2, 0.4, 0.6, 0.8, 1.0)` | Temperature for sampling. Can be a tuple of temperatures to try on fallback. |
| `fp16` | `bool` | `True` | Whether to use FP16 precision (faster on GPU) |

### Speech Detection

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `no_speech_threshold` | `float` | `0.6` | If no_speech probability is above this and logprob is below threshold, treat as silence |
| `logprob_threshold` | `float` | `-1.0` | If average log probability is below this, treat as failed |
| `compression_ratio_threshold` | `float` | `2.4` | If gzip compression ratio is above this, treat as failed |

### Text Conditioning

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `condition_on_previous_text` | `bool` | `True` | Provide previous output as prompt for next window |
| `initial_prompt` | `str` | `None` | Optional text to provide as prompt for first window |
| `carry_initial_prompt` | `bool` | `False` | Prepend initial_prompt to every decode() call |

### Timestamps

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `word_timestamps` | `bool` | `False` | Extract word-level timestamps (experimental) |
| `clip_timestamps` | `str` or `list` | `"0"` | Comma-separated start,end timestamps for clips |

## Return Value

Returns a dictionary with:

```python
{
    "text": "Full transcribed text...",
    "language": "en",
    "segments": [
        {
            "id": 0,
            "seek": 0,
            "start": 0.0,
            "end": 2.5,
            "text": "First segment",
            "tokens": [...],
            "temperature": 0.0,
            "avg_logprob": -0.5,
            "compression_ratio": 1.2,
            "no_speech_prob": 0.1
        },
        ...
    ]
}
```

## Examples

### Simple Transcription

```python
import whisper
model = whisper.load_model("base")
result = model.transcribe("audio.mp3")
print(result["text"])
```

### Specify Language

```python
result = model.transcribe("audio.mp3", language="Japanese")
```

### Translate to English

```python
# Use multilingual model (not turbo!) for translation
model = whisper.load_model("medium")
result = model.transcribe("japanese.wav", task="translate")
print(result["text"])
```

### With Word Timestamps

```python
result = model.transcribe("audio.mp3", word_timestamps=True)
for segment in result["segments"]:
    print(f"{segment['start']:.2f}s - {segment['end']:.2f}s: {segment['text']}")
    if "words" in segment:
        for word in segment["words"]:
            print(f"  {word['start']:.2f}s - {word['end']:.2f}s: {word['word']}")
```

### Custom Initial Prompt

```python
# Provide context to help with proper nouns or technical terms
result = model.transcribe(
    "podcast.mp3",
    initial_prompt="This is a discussion about machine learning and transformers.",
    language="English"
)
```

### Process Specific Clip

```python
# Transcribe only from 10s to 60s
result = model.transcribe("audio.mp3", clip_timestamps="10,60")
```

### Multiple Clips

```python
# Transcribe clips: 0-30s, 60-90s, 120-180s
result = model.transcribe("audio.mp3", clip_timestamps="0,30,60,90,120,180")
```
