#!/usr/bin/env python3
"""
VoiceTry - Futuristic Voice AI Terminal

A voice-powered AI assistant with real-time visualization.
"""

import os
import sys
import time
from typing import Optional

from dotenv import load_dotenv
from rich.console import Console
from rich.live import Live

# Import our modules
from audio import AudioPlayer, AudioRecorder
from llm import DeepSeekClient
from stt import WhisperTranscriber
from tts import KokoroTTS
from ui import AppState, UIAnimator, VoiceTerminalUI


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
[bold cyan]║[/]  [dim]━━━━━━━━━━━━━━━━ Voice AI Terminal v1.0 ━━━━━━━━━━━━━━━━[/]  [bold cyan]║[/]
[bold cyan]║[/]                                                              [bold cyan]║[/]
[bold cyan]╚══════════════════════════════════════════════════════════════╝[/]
    """
    console.print(banner)


def get_keypress() -> str:
    """Get a single keypress without waiting for enter."""
    try:
        import readchar
        return readchar.readkey()
    except ImportError:
        # Fallback to input
        return input().strip().lower()


class VoiceTryApp:
    """Main application class."""

    def __init__(self):
        # Load environment
        load_dotenv()

        # Configuration
        self.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        self.deepseek_model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

        # Validate API key
        if not self.deepseek_api_key:
            raise ValueError("DEEPSEEK_API_KEY not found in environment")

        # Initialize components (lazy load heavy ones)
        self.console = Console()
        self.ui = VoiceTerminalUI()

        # These will be initialized on first use
        self._recorder: Optional[AudioRecorder] = None
        self._player: Optional[AudioPlayer] = None
        self._transcriber: Optional[WhisperTranscriber] = None
        self._llm: Optional[DeepSeekClient] = None
        self._tts: Optional[KokoroTTS] = None

    @property
    def recorder(self) -> AudioRecorder:
        if self._recorder is None:
            self._recorder = AudioRecorder()
            self._recorder.set_level_callback(self._on_audio_level)
        return self._recorder

    @property
    def player(self) -> AudioPlayer:
        if self._player is None:
            self._player = AudioPlayer()
            self._player.set_level_callback(self._on_audio_level)
        return self._player

    @property
    def transcriber(self) -> WhisperTranscriber:
        if self._transcriber is None:
            self.console.print("[dim]Loading Whisper model...[/]")
            self._transcriber = WhisperTranscriber(model_size="base")
        return self._transcriber

    @property
    def llm(self) -> DeepSeekClient:
        if self._llm is None:
            self._llm = DeepSeekClient(
                api_key=self.deepseek_api_key,
                model=self.deepseek_model,
                system_prompt=self._get_system_prompt(),
                temperature=0.7,
                max_tokens=2048,
            )
        return self._llm

    @property
    def tts(self) -> KokoroTTS:
        if self._tts is None:
            self.console.print("[dim]Loading Kokoro TTS...[/]")
            self._tts = KokoroTTS(voice="af_heart", language="en-us", speed=1.0)
        return self._tts

    def _get_system_prompt(self) -> str:
        """Get the system prompt for the AI."""
        return """You are a helpful, friendly AI assistant. You respond concisely 
and naturally, as if having a voice conversation. Keep responses relatively brief 
(2-4 sentences typically) since they will be spoken aloud. Be engaging and helpful."""

    def _on_audio_level(self, level: float) -> None:
        """Callback for audio level updates."""
        self.ui.update_audio_level(level)

    def run(self) -> None:
        """Run the main application loop."""
        clear_screen()
        print_banner(self.console)

        self.console.print()
        self.console.print("[bold green]✓[/] Initializing components...")
        self.console.print("[dim]  • DeepSeek API: Connected[/]")
        self.console.print("[dim]  • Whisper: Ready (will load on first use)[/]")
        self.console.print("[dim]  • Kokoro TTS: Ready (will load on first use)[/]")
        self.console.print()
        self.console.print("[bold cyan]Press ENTER to start the voice terminal...[/]")
        input()

        # Start the live UI
        with Live(self.ui.render(), console=self.console, refresh_per_second=20) as live:
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
            # Wait for keypress
            key = get_keypress()

            if key.lower() == 'q':
                # Quit
                break

            if key == ' ':  # Space bar
                self._handle_recording()

    def _handle_recording(self) -> None:
        """Handle recording, transcribing, and responding."""
        # Start recording
        self.ui.set_state(AppState.RECORDING)
        self.recorder.start_recording()

        # Wait for space to stop
        while True:
            key = get_keypress()
            if key == ' ':
                break
            time.sleep(0.05)

        # Stop recording
        audio = self.recorder.stop_recording()
        self.ui.set_state(AppState.TRANSCRIBING)

        # Transcribe
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

        # Get AI response (streaming)
        self.ui.set_state(AppState.THINKING)
        self.ui.clear_messages()
        self.ui.set_user_message(user_text)

        full_response = ""
        try:
            for chunk in self.llm.generate_stream(user_text):
                if chunk.content:
                    full_response += chunk.content
                    self.ui.append_ai_response(chunk.content)

                if chunk.is_done:
                    break

        except Exception as e:
            self.console.print(f"[red]LLM error: {e}[/]")
            self.ui.set_state(AppState.IDLE)
            return

        # Speak the response
        if full_response.strip():
            self.ui.set_state(AppState.SPEAKING)
            try:
                audio = self.tts.synthesize(full_response)
                self.player.play(audio, blocking=True)
            except Exception as e:
                self.console.print(f"[red]TTS error: {e}[/]")

        # Reset to idle
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
