---
source: GitHub (openai/whisper)
library: OpenAI Whisper
package: openai-whisper
topic: model-loading
fetched: 2026-02-23T21:46:00Z
official_docs: https://github.com/openai/whisper
---

# Whisper Model Loading

## `whisper.load_model()`

Load a Whisper ASR model.

```python
import whisper

model = whisper.load_model("turbo")
```

### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `str` | One of the official model names listed by `whisper.available_models()`, or path to a model checkpoint containing the model dimensions and the model state_dict. |
| `device` | `Union[str, torch.device]` | The PyTorch device to put the model into. Defaults to `cuda` if available, otherwise `cpu`. |
| `download_root` | `str` | Path to download the model files; by default, it uses `"~/.cache/whisper"`. |
| `in_memory` | `bool` | Whether to preload the model weights into host memory. |

### Returns

- `model: Whisper` - The Whisper ASR model instance

### Device Selection

```python
# Automatic (cuda if available, else cpu)
model = whisper.load_model("base")

# Explicit device selection
model = whisper.load_model("base", device="cpu")
model = whisper.load_model("base", device="cuda")
model = whisper.load_model("base", device=torch.device("cuda:0"))
```

### Custom Download Location

```python
model = whisper.load_model("base", download_root="/path/to/models")
```

### Loading from Local Checkpoint

You can also load a model from a local checkpoint file:

```python
model = whisper.load_model("/path/to/model.pt")
```

### Available Models Function

```python
import whisper
print(whisper.available_models())
# Output: ['tiny.en', 'tiny', 'base.en', 'base', 'small.en', 'small', 'medium.en', 'medium', 'large-v1', 'large-v2', 'large-v3', 'large', 'large-v3-turbo', 'turbo']
```
