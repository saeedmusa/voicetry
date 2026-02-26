# AGENTS.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

VoiceTry is a voice AI terminal application: record speech → transcribe with Whisper → send to DeepSeek LLM → speak response with TTS. It uses a cyberpunk-themed Rich terminal UI with real-time audio visualization.

## Commands

### Run the application
```bash
source .venv/bin/activate
python -m src.main
```

### Install dependencies
```bash
pip install -r requirements.txt
```

### System dependencies (macOS)
```bash
brew install espeak-ng portaudio ffmpeg
```

### Verify module imports
```bash
python test_imports.py
```

## Environment Variables

Requires a `.env` file in the project root:
- `DEEPSEEK_API_KEY` — required
- `DEEPSEEK_MODEL` — defaults to `deepseek-chat`
- `DEEPSEEK_BASE_URL` — defaults to `https://api.deepseek.com`
- `LLM_TEMPERATURE`, `LLM_MAX_TOKENS`, `LLM_SYSTEM_PROMPT` — optional overrides
- `KOKORO_CACHE_DIR` — optional, defaults to `~/.cache/kokoro`
- `PIPER_BINARY` — optional, path to piper binary

## Architecture

### Module layout (`src/`)

Four independent modules plus an orchestrator:

- **`main.py`** — `VoiceTryApp` orchestrates the full voice loop. Uses lazy-loaded properties for all heavy components (Whisper, TTS, LLM). The response pipeline is async: LLM streams text → sentences are split and queued → multiple synthesis workers process in parallel → a playback worker plays audio sequentially.
- **`speech_to_text/`** — Recording (`Recorder` via `sounddevice` InputStream callback) and transcription (`Transcriber` using `faster-whisper`). Audio is recorded at 16kHz float32 mono.
- **`llm_processor/`** — `DeepSeekLLM` wraps the OpenAI-compatible API. Supports both `generate()` and `generate_stream()` (yields `StreamChunk`). `BaseLLM` in `interface.py` defines the abstract contract; `ConversationHistory` manages context window.
- **`text_to_speech/`** — Engine abstraction via `TTSEngine` (ABC in `base.py`). Two implementations in `engines/`: `KokoroEngine` (ONNX-based, 24kHz, async streaming) and `PiperEngine` (subprocess-based CLI, 16kHz). Factory in `engines/__init__.py` creates engines by name. `TTSPlayer` handles playback with level callbacks. `VoiceSelector` provides interactive terminal menus for engine/voice switching.
- **`ui/`** — Rich-based terminal UI. `VoiceTerminalUI` renders panels (header, visualizer, status, messages). `AudioVisualizer` animates level bars. `UIAnimator` runs a background thread updating the Rich `Live` display at 10fps. `AppState` enum drives UI state transitions: IDLE → RECORDING → TRANSCRIBING → THINKING → SPEAKING → IDLE.

### Key patterns

- **Lazy loading**: All heavy models (Whisper, Kokoro, LLM client) are loaded on first use via `@property` in `VoiceTryApp`.
- **Module imports**: `main.py` adds `src/` to `sys.path` so modules import as `from speech_to_text import ...` (not `from src.speech_to_text`).
- **Level callbacks**: Both `Recorder` and `TTSPlayer` accept level callbacks (`Callable[[float], None]`) to feed the audio visualizer.
- **Kokoro singleton**: `_KOKORO_INSTANCE` is a module-level global in `engines/kokoro.py`, reused across calls. Model files are auto-downloaded from HuggingFace to cache dir.
- **Piper subprocess**: `PiperEngine.synthesize()` pipes text to the `piper` CLI and reads WAV from stdout.

### Dependencies

STT uses `faster-whisper` (not `openai-whisper` despite pyproject.toml listing it — requirements.txt is the source of truth). TTS uses `kokoro-onnx` + `onnxruntime` (not PyTorch-based kokoro). The LLM client uses the `openai` SDK pointed at DeepSeek's API.
