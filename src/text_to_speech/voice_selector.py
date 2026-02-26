"""Voice and engine selector for TTS."""

import sys
from typing import Optional

import readchar
from rich.console import Console

from .config import TTSConfig
from .engines import get_engine


class VoiceSelector:
    """Handles voice and engine selection menu and configuration."""

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self._current_voice: str = "af_heart"
        self._current_engine: str = "kokoro"

    @property
    def current_voice(self) -> str:
        return self._current_voice

    @property
    def current_engine(self) -> str:
        return self._current_engine

    @property
    def available_voices(self):
        engine_class = get_engine(self._current_engine)
        return engine_class.voices

    def _ensure_valid_voice(self) -> None:
        """Ensure current voice is valid for current engine."""
        voices = self.available_voices
        if self._current_voice not in voices:
            self._current_voice = voices[0]

    def get_current_engine(self):
        """Get the current engine instance to access descriptions."""
        engine_class = get_engine(self._current_engine)
        return engine_class(TTSConfig())

    def get_voice_description(self, voice: str) -> str:
        """Get description for a voice from the current engine."""
        engine = self.get_current_engine()
        descriptions = getattr(engine, 'voice_descriptions', {})
        return descriptions.get(voice, "")

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
                        engine_class = get_engine(self._current_engine)
                        self._current_voice = engine_class.voices[0]
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
            self.console.print(f"  {marker} [bold]{i + 1}.[/] [{voice_style}]{voice:<25}[/] {desc}")

        self.console.print()
        self.console.print(f"[dim]↑/↓ navigate • ENTER select • ESC cancel • E switch engine[/]")

    def select_voice(self) -> str:
        """Display interactive voice selection menu with arrow keys."""
        self._ensure_valid_voice()
        
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
                        self.select_engine()
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
        return TTSConfig(
            voice_name=self._current_voice,
            engine=self._current_engine,
            sample_rate=16000 if self._current_engine == "piper" else 24000
        )
