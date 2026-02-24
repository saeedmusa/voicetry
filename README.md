# VoiceTry 🎤

A futuristic voice AI terminal application with real-time audio visualization.

```
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║  ██╗   ██╗ ██████╗ ██╗ ██████╗████████╗██████╗  █████╗      ║
║  ██║   ██║██╔═══██╗██║██╔════╝╚══██╔══╝╚════██╗██╔══██╗     ║
║  ██║   ██║██║   ██║██║██║        ██║    █████╔╝███████║     ║
║  ╚██╗ ██╔╝██║   ██║██║██║        ██║   ██╔═══╝ ██╔══██║     ║
║   ╚████╔╝ ╚██████╔╝██║╚██████╗   ██║   ███████╗██║  ██║     ║
║    ╚═══╝   ╚═════╝ ╚═╝ ╚═════╝   ╚═╝   ╚══════╝╚═╝  ╚═╝     ║
║                                                              ║
║  ━━━━━━━━━━━━━━━━━ Voice AI Terminal v1.0 ━━━━━━━━━━━━━━━━   ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

## Features

- 🎤 **Voice Recording** - Press SPACE to start/stop recording
- 📝 **Speech-to-Text** - Local Whisper transcription (no API needed)
- 🧠 **AI Chat** - DeepSeek with streaming responses
- 🔊 **Text-to-Speech** - Kokoro v1.0 TTS (82M params, runs locally)
- 📊 **Audio Visualizer** - Real-time animated bars during recording/playback
- 💬 **Conversation History** - Context preserved between messages
- 🎨 **Futuristic UI** - Cyberpunk-themed terminal with glowing effects

## Prerequisites

### System Dependencies (macOS)

```bash
# Install Homebrew if you don't have it
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install required system packages
brew install espeak-ng portaudio ffmpeg
```

### Python

Python 3.9+ is required.

## Installation

```bash
# Clone or navigate to the project
cd voicetry

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your DeepSeek API key
```

## Configuration

Edit `.env` file:

```env
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_MODEL=deepseek-chat
```

Get your DeepSeek API key at: https://platform.deepseek.com/

## Usage

```bash
# Run the application
python -m src.main
```

### Controls

| Key | Action |
|-----|--------|
| `SPACE` | Start/Stop recording |
| `Q` | Quit application |

### Workflow

1. Press `SPACE` to start recording
2. Speak your message
3. Press `SPACE` to stop recording
4. Watch as your voice is transcribed → sent to AI → response streams → spoken back
5. Repeat!

## Architecture

```
voicetry/
├── src/
│   ├── __init__.py
│   ├── main.py              # Entry point
│   ├── ui.py                # Futuristic terminal UI
│   ├── audio/
│   │   ├── __init__.py
│   │   ├── recorder.py      # Microphone recording
│   │   └── player.py        # Audio playback
│   ├── stt/
│   │   ├── __init__.py
│   │   └── whisper.py       # Speech-to-text
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── base.py          # Abstract LLM interface
│   │   └── deepseek.py      # DeepSeek implementation
│   └── tts/
│       ├── __init__.py
│       └── kokoro.py        # Text-to-speech
├── requirements.txt
├── .env
├── .env.example
└── README.md
```

## Hardware Requirements

Tested on:
- 2020 MacBook Pro (1.4 GHz Quad-Core Intel Core i5)
- 8GB+ RAM recommended

**Kokoro TTS** is lightweight (82M params) and runs well on CPU.

## Troubleshooting

### Audio not recording
```bash
# Check microphone permissions in System Preferences > Security & Privacy > Microphone
# Ensure terminal has access
```

### espeak-ng not found
```bash
brew install espeak-ng
```

### PortAudio not found
```bash
brew install portaudio
pip install --upgrade sounddevice
```

### Kokoro fails to load
```bash
# Make sure espeak-ng is installed first
brew install espeak-ng

# Reinstall kokoro
pip install --upgrade kokoro misaki[en]
```

## License

MIT License

## Credits

- [Kokoro TTS](https://github.com/hexgrad/kokoro) - Text-to-speech
- [OpenAI Whisper](https://github.com/openai/whisper) - Speech recognition
- [DeepSeek](https://deepseek.com/) - LLM API
- [Rich](https://github.com/Textualize/rich) - Terminal UI
