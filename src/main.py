#!/usr/bin/env python3
"""
VoiceTry - Modular Voice AI Terminal

A voice-powered AI assistant with real-time visualization.
Orchestrates 4 independent modules: speech_to_text, llm_processor, text_to_speech, ui
"""

import asyncio
import asyncio
import os
import sys
import time
import time

import time
from pathlib import Path
from typing import Optional

# Fix OpenMP conflict on macOS - must be set before importing any OpenMP-dependent libs
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
# Suppress PyTorch version warnings
os.environ["TORCH_CPP_MIN_LOG_LEVEL"] = "2"

# Ensure src directory is in path for module resolution
# When running as `python3 -m src.main`, we need src/ accessible
script_dir = Path(__file__).parent.absolute()
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))

# Also ensure parent directory is in path for 'src.speech_to_text' style imports if needed
project_root = script_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from rich.console import Console
from rich.live import Live

# Import from local modules (all modules are in src/)
from speech_to_text import Recorder, Transcriber, SpeechToTextConfig
from llm_processor import DeepSeekLLM
from text_to_speech import Synthesizer, TTSPlayer, TTSConfig, VoiceSelector
from ui import VoiceTerminalUI, UIAnimator, AppState


def clear_screen() -> None:
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_banner(console: Console) -> None:
    """Print startup banner."""
    console.clear()

    banner = """
[bold cyan]╔══════════════════════════════════════════════════════════════╗[/]
[bold cyan]║[/]                                                              [bold cyan]║[/]
[bold cyan]║[/]  [bold white]██╗   ██╗ ██████╗ ██╗ ██████╗████████╗██████╗  █████╗[/]  [bold cyan]║[/]
[bold cyan]║[/]  [bold white]██║   ██║██╔═══██╗██║██╔════╝╚══██╔══╝╚════██╗██╔══██╗[/]  [bold cyan]║[/]
[bold cyan]║[/]  [bold white]██║   ██║██║   ██║██║██║        ██║    █████╔╝███████║[/]  [bold cyan]║[/]
[bold cyan]║[/]  [bold white]╚██╗ ██╔╝██║   ██║██║██║        ██║   ██╔═══╝ ██╔══██║[/]  [bold cyan]║[/]
[bold cyan]║[/]   [bold white]╚████╔╝ ╚██████╔╝██║╚██████╗   ██║   ███████╗██║  ██║[/]  [bold cyan]║[/]
[bold cyan]║[/]    [bold white]╚═══╝   ╚═════╝ ╚═╝ ╚═════╝   ╚═╝   ╚══════╝╚═╝  ╚═╝[/]  [bold cyan]║[/]
[bold cyan]║[/]                                                              [bold cyan]║[/]
[bold cyan]║[/]  [dim]━━━━━━━━━━━━━━━━ Voice AI Terminal v2.0 ━━━━━━━━━━━━━━━━[/]  [bold cyan]║[/]
[bold cyan]║[/]                                                              [bold cyan]║[/]
[bold cyan]╚══════════════════════════════════════════════════════════════╝[/]
    """
    console.print(banner)

    # Print instructions
    console.print()
    console.print("[bold cyan]📋 Instructions:[/]")
    console.print("  [bold green]1.[/] Press [bold yellow]ENTER[/] to start the voice terminal")
    console.print("  [bold green]2.[/] Press [bold yellow]SPACE[/] to start/stop recording")
    console.print("  [bold green]3.[/] Press [bold yellow]V[/] to change voice")
    console.print("  [bold green]4.[/] Press [bold yellow]Q[/] to quit")
    console.print()


def get_keypress() -> str:
    """Get a single keypress without waiting for enter and without terminal echo."""
    try:
        import readchar
        import tty
        import termios
        import sys
        
        # Save terminal settings
        old_settings = termios.tcgetattr(sys.stdin)
        try:
            # Set terminal to raw mode, no echo
            tty.setcbreak(sys.stdin.fileno())
            # Read a single character
            key = readchar.readkey()
            return key
        finally:
            # Restore terminal settings
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
    except Exception:
        # Fallback - just read without echo control
        try:
            import readchar
            return readchar.readkey()
        except ImportError:
            return input().strip().lower()


class VoiceTryApp:
    """Main application class orchestrating all modules."""

    def __init__(self):
        load_dotenv()

        self.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        self.deepseek_model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

        if not self.deepseek_api_key:
            raise ValueError("DEEPSEEK_API_KEY not found in environment")

        self.console = Console(force_terminal=True, no_color=False)
        self.ui = VoiceTerminalUI()
        self.voice_selector = VoiceSelector(self.console)

        self._recorder: Optional[Recorder] = None
        self._transcriber: Optional[Transcriber] = None
        self._llm: Optional[DeepSeekLLM] = None
        self._synthesizer: Optional[Synthesizer] = None
        self._player: Optional[TTSPlayer] = None

    @property
    def recorder(self) -> Recorder:
        if self._recorder is None:
            config = SpeechToTextConfig()
            self._recorder = Recorder(config)
            self._recorder.set_level_callback(self._on_audio_level)
        return self._recorder

    @property
    def transcriber(self) -> Transcriber:
        if self._transcriber is None:
            self.console.print("[dim]Loading Whisper model...[/]")
            config = SpeechToTextConfig()
            self._transcriber = Transcriber(config)
        return self._transcriber

    @property
    def llm(self) -> DeepSeekLLM:
        if self._llm is None:
            self._llm = DeepSeekLLM(
                api_key=self.deepseek_api_key,
                model=self.deepseek_model,
                system_prompt=self._get_system_prompt(),
                temperature=0.7,
                max_tokens=2048,
            )
        return self._llm

    @property
    def synthesizer(self) -> Synthesizer:
        if self._synthesizer is None:
            self.console.print("[dim]Loading Kokoro TTS...[/]")
            config = self.voice_selector.get_config()
            self._synthesizer = Synthesizer(config)
        return self._synthesizer

    @property
    def player(self) -> TTSPlayer:
        if self._player is None:
            config = self.voice_selector.get_config()
            self._player = TTSPlayer(config)
            self._player.set_level_callback(self._on_audio_level)
        return self._player

    def _get_system_prompt(self) -> str:
        return """You are a helpful, friendly AI assistant. You respond concisely 
and naturally, as if having a voice conversation. Keep responses relatively brief 
(2-4 sentences typically) since they will be spoken aloud. Be engaging and helpful."""

    def _on_audio_level(self, level: float) -> None:
        self.ui.update_audio_level(level)

    def run(self) -> None:
        """Run the main application loop."""
        clear_screen()
        print_banner(self.console)

        self.console.print()
        self.console.print("[bold green]✓[/] Initializing modules...")
        self.console.print("[dim]  • DeepSeek API: Connected[/]")
        self.console.print("[dim]  • Whisper: Ready (will load on first use)[/]")
        self.console.print("[dim]  • Kokoro TTS: Ready (will load on first use)[/]")
        self.console.print()
        self.console.print("[bold cyan]Press ENTER to start the voice terminal...[/]")
        input()

        with Live(self.ui.render(), console=self.console, refresh_per_second=8) as live:
            animator = UIAnimator(self.ui, live)
            animator.start()

            try:
                self._main_loop()
            except KeyboardInterrupt:
                pass
            finally:
                animator.stop()

    def _main_loop(self) -> None:
        """Main interaction loop."""
        while True:
            key = get_keypress()

            if key.lower() == 'q':
                break

            if key.lower() == 'v':
                self._handle_voice_selection()

            if key == ' ':
                self._handle_recording()

    def _handle_voice_selection(self) -> None:
        """Handle voice selection menu."""
        selected = self.voice_selector.select_voice()
        self._synthesizer = None
        self._player = None

    def _handle_recording(self) -> None:
        """Handle recording, transcribing, and responding."""
        self.ui.set_state(AppState.RECORDING)
        self.recorder.start_recording()

        while True:
            key = get_keypress()
            if key == ' ':
                break
            time.sleep(0.05)

        audio = self.recorder.stop_recording()
        self.ui.set_state(AppState.TRANSCRIBING)

        try:
            result = self.transcriber.transcribe(audio)
            user_text = result.text

            if not user_text.strip():
                self.ui.set_state(AppState.IDLE)
                return

            self.ui.set_user_message(user_text)

        except Exception as e:
            self.console.print(f"[red]Transcription error: {e}[/]")
            self.ui.set_state(AppState.IDLE)
            return

        self.ui.set_state(AppState.THINKING)
        self.ui.clear_messages()
        self.ui.set_user_message(user_text)

        # Run LLM and TTS concurrently
        async def process_response():
            full_response = ""
            sentence_buffer = ""
            tts_started = False
            tts_queue: asyncio.Queue[str] = asyncio.Queue()
            
            async def tts_worker():
                nonlocal tts_started
                buffer = ""
                
                while True:
                    try:
                        text = await asyncio.wait_for(tts_queue.get(), timeout=0.5)
                        
                        if text == "END":
                            if buffer.strip():
                                try:
                                    audio_gen = self.synthesizer.synthesize_stream(buffer)
                                    await self.player.play_stream(audio_gen)
                                except Exception:
                                    pass
                            break
                        
                        buffer += text
                        
                        while buffer:
                            for punct in ['. ', '! ', '? ', '.', '!', '?']:
                                if punct in buffer:
                                    idx = buffer.index(punct) + len(punct)
                                    sentence = buffer[:idx]
                                    buffer = buffer[idx:]
                                    
                                    if sentence.strip():
                                        try:
                                            audio_gen = self.synthesizer.synthesize_stream(sentence)
                                            await self.player.play_stream(audio_gen)
                                        except Exception:
                                            pass
                                    break
                            else:
                                if len(buffer) < 100:
                                    break
                                sentence = buffer
                                buffer = ""
                                if sentence.strip():
                                    try:
                                        audio_gen = self.synthesizer.synthesize_stream(sentence)
                                        await self.player.play_stream(audio_gen)
                                    except Exception:
                                        pass
                            break
                    except asyncio.TimeoutError:
                        if buffer.strip():
                            try:
                                audio_gen = self.synthesizer.synthesize_stream(buffer)
                                await self.player.play_stream(audio_gen)
                            except Exception:
                                pass
                        buffer = ""
                        if tts_started and tts_queue.empty():
                            break
                    except Exception:
                        break
            
            tts_task = None
            
            for chunk in self.llm.generate_stream(user_text):
                if chunk.content:
                    full_response += chunk.content
                    sentence_buffer += chunk.content
                    self.ui.append_ai_response(chunk.content)
                    
                    if not tts_started and (len(sentence_buffer) >= 50 or any(p in sentence_buffer for p in '.!?')):
                        tts_started = True
                        self.ui.set_state(AppState.SPEAKING)
                        tts_task = asyncio.create_task(tts_worker())
                        await tts_queue.put(sentence_buffer)
                        sentence_buffer = ""

                if chunk.is_done:
                    break

            if not tts_started and full_response.strip():
                self.ui.set_state(AppState.SPEAKING)
                try:
                    audio_gen = self.synthesizer.synthesize_stream(full_response)
                    await self.player.play_stream(audio_gen)
                except Exception as e:
                    self.console.print(f"[red]TTS error: {e}[/]")
            elif tts_started:
                await tts_queue.put("END")
                if tts_task:
                    await tts_task

        try:
            asyncio.run(process_response())
        except Exception as e:
            self.console.print(f"[red]LLM error: {e}[/]")
            self.ui.set_state(AppState.IDLE)
            return

        self.ui.set_state(AppState.IDLE)


def main() -> None:
    """Entry point."""
    try:
        app = VoiceTryApp()
        app.run()
    except ValueError as e:
        console = Console()
        console.print(f"[red]Error: {e}[/]")
        console.print("[dim]Make sure DEEPSEEK_API_KEY is set in .env file[/]")
        sys.exit(1)
    except Exception as e:
        console = Console()
        console.print(f"[red]Fatal error: {e}[/]")
        sys.exit(1)


if __name__ == "__main__":
    main()
