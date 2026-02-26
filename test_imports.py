#!/usr/bin/env python3
"""Test script to verify all module imports work."""
import sys
from pathlib import Path

# Setup paths - add src directory to path
project_root = Path(__file__).parent.absolute()
src_dir = project_root / "src"

if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

print("Testing module imports...")

try:
    from speech_to_text import Recorder, Transcriber, SpeechToTextConfig
    print("✓ speech_to_text imports OK")
except Exception as e:
    print(f"✗ speech_to_text failed: {e}")
    sys.exit(1)

try:
    from llm_processor import DeepSeekLLM
    print("✓ llm_processor imports OK")
except Exception as e:
    print(f"✗ llm_processor failed: {e}")
    sys.exit(1)

try:
    from text_to_speech import get_synthesizer, TTSPlayer, TTSConfig, VoiceSelector
    print("✓ text_to_speech imports OK")
except Exception as e:
    print(f"✗ text_to_speech failed: {e}")
    sys.exit(1)

try:
    from ui import VoiceTerminalUI, UIAnimator, AppState
    print("✓ ui imports OK")
except Exception as e:
    print(f"✗ ui failed: {e}")
    sys.exit(1)

print("\n✅ All module imports successful!")
print("If you get dependency errors (whisper, kokoro), run:")
print("  pip install -r requirements.txt")
