"""Voice selector for TTS."""

import sys
from typing import Optional, Literal

import readchar
from rich.console import Console

from .config import TTSConfig


class VoiceSelector:
    """Handles voice and engine selection menu and configuration."""

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self._current_voice: str = TTSConfig.voice_name
        self._current_engine: Literal["kokoro", "piper"] = "piper"

    @property
    def current_voice(self) -> str:
        return self._current_voice

    @property
    def current_engine(self) -> str:
        return self._current_engine

    @property
    def available_voices(self) -> list[str]:
        if self._current_engine == "piper":
            return self._get_piper_voices()
        return TTSConfig.KOKORO_VOICES

    def _get_piper_voices(self) -> list[str]:
        """Get list of available Piper voices."""
        return [
            "en_US_lessac_medium",
            "en_US_lessac_low", 
            "en_US_amy_medium",
            "en_US_ryan_medium",
            "en_US_ljspeech_medium",
            "en_US_libritts_medium",
        ]

    def get_voice_description(self, voice: str) -> str:
        """Get description for a voice."""
        # Kokoro descriptions
        kokoro_descriptions = {
            "af_bella": "Female, American",
            "af_heart": "Female, warm",
            "af_sarah": "Female, clear",
            "af_sky": "Female",
            "am_adam": "Male, American",
            "am_michael": "Male, American",
            "bf_emma": "Female, British",
            "bm_george": "Male, British",
        }
        
        # Piper descriptions
        piper_descriptions = {
            "en_US_lessac_medium": "Lessac (Medium)",
            "en_US_lessac_low": "Lessac (Low - Fastest)",
            "en_US_amy_medium": "Amy (Female)",
            "en_US_ryan_medium": "Ryan (Male)",
            "en_US_ljspeech_medium": "LJ Speech (Female)",
            "en_US_libritts_medium": "LibriTTS (Female)",
        }
        
        if self._current_engine == "piper":
            return piper_descriptions.get(voice, "")
        return kokoro_descriptions.get(voice, "")

    def select_engine(self) -> str:
        """Display engine selection menu."""
        self.console.print()
        self.console.print("[bold cyan]╔════════════════════════════════════════╗[/]")
        self.console.print("[bold cyan]║[/]      [bold white]SELECT TTS ENGINE[/]                [bold cyan]║[/]")
        self.console.print("[bold cyan]╚════════════════════════════════════════╝[/]")
        self.console.print()
        
        engines = [
            ("piper", "Piper", "Fast, lightweight, CPU-optimized"),
            ("kokoro", "Kokoro", "Higher quality, more voices"),
        ]
        
        for i, (engine_id, name, desc) in enumerate(engines, 1):
            marker = "▶" if engine_id == self._current_engine else " "
            engine_style = "bold green" if engine_id == self._current_engine else "white"
            self.console.print(f"  {marker} [bold]{i}.[/] [{engine_style}]{name:<10}[/] {desc}")

        self.console.print()
        self.console.print("[dim]↑/↓ navigate • ENTER select • ESC cancel[/]")

        selected_index = 0 if self._current_engine == "piper" else 1
        num_engines = len(engines)

        import tty
        import termios

        try:
            old_settings = termios.tcgetattr(sys.stdin)
            tty.setcbreak(sys.stdin.fileno())

            try:
                while True:
                    key = readchar.readkey()

                    if key == readchar.key.UP:
                        selected_index = (selected_index - 1) % num_engines
                        self._render_engine_menu(selected_index)

                    elif key == readchar.key.DOWN:
                        selected_index = (selected_index + 1) % num_engines
                        self._render_engine_menu(selected_index)

                    elif key == '\r' or key == '\n':
                        self._current_engine = engines[selected_index][0]
                        # Reset voice to first available for new engine
                        if self._current_engine == "piper":
                            self._current_voice = "en_US_lessac_medium"
                        else:
                            self._current_voice = "af_heart"
                        self.console.print()
                        self.console.print(f"[bold green]✓[/] Engine changed to: [bold]{self._current_engine.upper()}[/]")
                        return self._current_engine

                    elif key == '\x1b':
                        self.console.print()
                        self.console.print("[dim]Cancelled[/]")
                        return self._current_engine

            finally:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

        except Exception as e:
            self.console.print(f"[red]Error: {e}[/]")
        
        return self._current_engine

    def _render_engine_menu(self, selected_index: int) -> None:
        """Render the engine selection menu."""
        self.console.print()
        self.console.print("[bold cyan]╔════════════════════════════════════════╗[/]")
        self.console.print("[bold cyan]║[/]      [bold white]SELECT TTS ENGINE[/]                [bold cyan]║[/]")
        self.console.print("[bold cyan]╚════════════════════════════════════════╝[/]")
        self.console.print()
        
        engines = [
            ("piper", "Piper", "Fast, lightweight, CPU-optimized"),
            ("kokoro", "Kokoro", "Higher quality, more voices"),
        ]
        
        for i, (engine_id, name, desc) in enumerate(engines, 1):
            marker = "▶" if i - 1 == selected_index else " "
            engine_style = "bold green" if i - 1 == selected_index else "white"
            self.console.print(f"  {marker} [bold]{i}.[/] [{engine_style}]{name:<10}[/] {desc}")

        self.console.print()
        self.console.print("[dim]↑/↓ navigate • ENTER select • ESC cancel[/]")

    def _render_menu(self, selected_index: int) -> None:
        """Render the voice selection menu."""
        self.console.print()
        self.console.print("[bold cyan]╔════════════════════════════════════════╗[/]")
        engine_name = self._current_engine.upper()
        self.console.print(f"[bold cyan]║[/]   [bold white]SELECT VOICE ({engine_name})[/]              [bold cyan]║[/]")
        self.console.print("[bold cyan]╚════════════════════════════════════════╝[/]")
        self.console.print()

        for i, voice in enumerate(self.available_voices):
            desc = self.get_voice_description(voice)
            is_selected = i == selected_index
            marker = "▶" if is_selected else " "
            voice_style = "bold green" if is_selected else "white"
            self.console.print(f"  {marker} [bold]{i + 1}.[/] [{voice_style}]{voice:<22}[/] {desc}")

        self.console.print()
        self.console.print(f"[dim]↑/↓ navigate • ENTER select • ESC cancel • E switch engine[/]")

    def select_voice(self) -> str:
        """Display interactive voice selection menu with arrow keys."""
        import tty
        import termios

        voices = self.available_voices
        if self._current_voice not in voices:
            selected_index = 0
        else:
            selected_index = voices.index(self._current_voice)
        
        num_voices = len(voices)

        self._render_menu(selected_index)

        try:
            old_settings = termios.tcgetattr(sys.stdin)
            tty.setcbreak(sys.stdin.fileno())

            try:
                while True:
                    key = readchar.readkey()

                    if key == readchar.key.UP:
                        selected_index = (selected_index - 1) % num_voices
                        self._render_menu(selected_index)

                    elif key == readchar.key.DOWN:
                        selected_index = (selected_index + 1) % num_voices
                        self._render_menu(selected_index)

                    elif key == '\r' or key == '\n':
                        self._current_voice = self.available_voices[selected_index]
                        self.console.print()
                        self.console.print(f"[bold green]✓[/] Voice changed to: [bold]{self._current_voice}[/]")
                        return self._current_voice

                    elif key == '\x1b':
                        self.console.print()
                        self.console.print("[dim]Cancelled[/]")
                        return self._current_voice

                    elif key.lower() == 'e':
                        # Switch engine
                        self.select_engine()
                        # Re-render voice menu with new engine's voices
                        voices = self.available_voices
                        selected_index = 0 if not voices else min(selected_index, len(voices) - 1)
                        self._render_menu(selected_index)

            finally:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

        except Exception as e:
            self.console.print(f"[red]Error: {e}[/]")

        return self._current_voice

    def get_config(self) -> TTSConfig:
        """Get TTSConfig with current voice and engine."""
        config = TTSConfig()
        config.voice_name = self._current_voice
        config.engine = self._current_engine
        config.sample_rate = 16000 if self._current_engine == "piper" else 24000
        return config
