---
source: GitHub (openai/whisper)
library: OpenAI Whisper
package: openai-whisper
topic: model-sizes
fetched: 2026-02-23T21:46:00Z
official_docs: https://github.com/openai/whisper
---

# Whisper Model Sizes

There are six model sizes, four with English-only versions, offering speed and accuracy tradeoffs.

## Model Comparison Table

| Size | Parameters | English-only Model | Multilingual Model | Required VRAM | Relative Speed |
|------|------------|-------------------|-------------------|---------------|----------------|
| tiny | 39 M | `tiny.en` | `tiny` | ~1 GB | ~10x |
| base | 74 M | `base.en` | `base` | ~1 GB | ~7x |
| small | 244 M | `small.en` | `small` | ~2 GB | ~4x |
| medium | 769 M | `medium.en` | `medium` | ~5 GB | ~2x |
| large | 1550 M | N/A | `large` | ~10 GB | 1x |
| turbo | 809 M | N/A | `turbo` | ~6 GB | ~8x |

## Notes

- The `.en` models for English-only applications tend to perform better, especially for the `tiny.en` and `base.en` models.
- The difference becomes less significant for the `small.en` and `medium.en` models.
- The `turbo` model is an optimized version of `large-v3` that offers faster transcription speed with a minimal degradation in accuracy.
- The `turbo` model is **NOT** trained for translation tasks - it will return the original language even if `--task translate` is specified.
- Use `medium` or `large` for the best translation results.

## Model Aliases

- `large` → `large-v3` (current default)
- `turbo` → `large-v3-turbo` (optimized fast version)

## Performance Considerations

The relative speeds are measured by transcribing English speech on an A100 GPU. Real-world speed may vary significantly depending on many factors including:
- The language being transcribed
- Speaking speed
- Available hardware

## Choosing a Model

- **Use `tiny` or `base`** for fastest transcription when lower accuracy is acceptable
- **Use `small`** for a good balance of speed and accuracy
- **Use `medium`** for higher accuracy with reasonable speed
- **Use `large`** for the best accuracy when speed is less critical
- **Use `turbo`** for fast transcription of English-only audio (not for translation)
