# VoiceTry Modular Structure - Installation Guide

## Fixed Issues

### ✅ Module Import Path Fixed
The "No module named 'speech_to_text'" error has been fixed by:
1. Adding src/ directory to sys.path in main.py
2. Creating src/__init__.py for proper package structure

## New Modular Structure

```
voicetry/
├── src/
│   ├── __init__.py              ← Added for package structure
│   ├── main.py                   ← Updated orchestrator
│   ├── speech_to_text/         ← Module 1
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── recorder.py
│   │   └── transcriber.py
│   ├── llm_processor/            ← Module 2
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── interface.py
│   │   └── deepseek.py
│   ├── text_to_speech/           ← Module 3
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── synthesizer.py
│   │   └── player.py
│   └── ui/                      ← Module 4
│       ├── __init__.py
│       ├── config.py
│       ├── visualizer.py
│       ├── terminal.py
│       └── animator.py
└── requirements.txt
```

## Installation Steps

### 1. Install Dependencies
```bash
cd /Users/saeed/development/voicetry
pip install -r requirements.txt
```

### 2. Run the Application

**Method 1: Run as module (Recommended)**
```bash
python3 -m src.main
```

**Method 2: Run as script**
```bash
cd src
python3 main.py
```

### 3. Test Imports (Optional)
```bash
python3 test_imports.py
```

## Dependencies Required

- **speech_to_text**: openai-whisper, sounddevice, numpy, soundfile
- **llm_processor**: openai, python-dotenv
- **text_to_speech**: kokoro, misaki[en], transformers, soundfile, numpy
- **ui**: rich, readchar
- **common**: python-dotenv

## Troubleshooting

### Error: "No module named 'speech_to_text'"
→ This is now fixed. The src/ directory is properly added to sys.path.

### Error: "No module named 'whisper'" or "No module named 'kokoro'"
→ Install dependencies: `pip install -r requirements.txt`

### Error: "ModuleNotFoundError" for other modules
→ Make sure you're running from the project root directory
→ Ensure all __init__.py files exist in module directories

## What Changed

### Old Structure
- `src/audio/` → replaced by `speech_to_text/` + `text_to_speech/`
- `src/stt/` → replaced by `speech_to_text/`
- `src/llm/` → replaced by `llm_processor/`
- `src/tts/` → replaced by `text_to_speech/`
- `src/ui.py` → expanded to `ui/` module

### New Structure Benefits
- ✅ Complete module independence
- ✅ Lazy loading of heavy models (Whisper, Kokoro)
- ✅ Simple synchronous code (no async complexity)
- ✅ Self-contained configs per module
- ✅ Each module can be used standalone

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up environment
cp .env.example .env
# Edit .env and add: DEEPSEEK_API_KEY=your_key_here

# 3. Run
python3 -m src.main
```

## API Keys Required

Set up a `.env` file in the project root:
```
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_MODEL=deepseek-chat
```
