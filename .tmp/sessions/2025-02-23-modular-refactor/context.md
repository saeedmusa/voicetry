# Task Context: Modular Refactor of VoiceTry

Session ID: 2025-02-23-modular-refactor
Created: 2025-02-23
Status: in_progress

## Current Request

Refactor VoiceTry codebase into 4 completely independent, simple modules:
1. speech_to_text - Audio capture and Whisper transcription
2. llm_processor - DeepSeek LLM with streaming support
3. text_to_speech - Kokoro TTS synthesis and playback
4. ui - Terminal UI with visualization

## Context Files (Standards to Follow)

None - No project-specific context files found. Using Python best practices:
- Clean, modular architecture
- Simple synchronous code (no async)
- Minimal type hints
- Self-contained modules with independent configs
- Clear, readable code

## Reference Files (Source Material to Look At)

Current source files to refactor:
- src/main.py - Application orchestrator
- src/ui.py - Terminal UI with visualization (380 lines)
- src/audio/recorder.py - Audio recording (83 lines)
- src/audio/player.py - Audio playback (99 lines)
- src/stt/whisper.py - Whisper transcriber (95 lines)
- src/llm/deepseek.py - DeepSeek client (108 lines)
- src/llm/base.py - Base LLM interface (113 lines)
- src/tts/kokoro.py - Kokoro TTS (131 lines)
- requirements.txt - Dependencies

## Components

### Module 1: speech_to_text/
- recorder.py - Audio capture from microphone
- transcriber.py - Whisper-based transcription
- config.py - Recording settings, model options

### Module 2: llm_processor/
- interface.py - BaseLLM, Message, StreamChunk types
- deepseek.py - OpenAI-compatible DeepSeek client
- config.py - API settings, model parameters

### Module 3: text_to_speech/
- synthesizer.py - Kokoro TTS synthesis
- player.py - Audio playback with callbacks
- config.py - Voice, language, speed settings

### Module 4: ui/
- visualizer.py - Audio bar visualizer component
- terminal.py - Terminal UI panels
- animator.py - Animation manager
- config.py - Color palette, state definitions

### Orchestrator
- main.py - Simple app wiring the 4 modules together

## Constraints

- Complete module independence (each works standalone)
- Simple synchronous code (no async)
- Minimal type hints for readability
- Self-contained configs in each module
- Maintain all original functionality

## Exit Criteria

- [ ] All 4 modules created independently
- [ ] Each module has __init__.py exposing main classes
- [ ] Each module has its own config.py
- [ ] main.py orchestrates all modules
- [ ] Original functionality preserved
- [ ] Code is clean and readable
- [ ] No dependencies between modules (except main.py)
