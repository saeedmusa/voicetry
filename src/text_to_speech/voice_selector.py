"""Voice selector for TTS."""

import sys
from typing import Optional

import readchar
from rich.console import Console

from .config import TTSConfig


class VoiceSelector:
    """Handles voice selection menu and configuration."""

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self._current_voice: str = TTSConfig.voice_name

    @property
    def current_voice(self) -> str:
        return self._current_voice

    @property
    def available_voices(self) -> list[str]:
        return TTSConfig.AVAILABLE_VOICES

    def get_voice_description(self, voice: str) -> str:
        """Get description for a voice."""
        descriptions = {
            "af_bella": "Female, American",
            "af_heart": "Female, warm",
            "af_sarah": "Female, clear",
            "af_sky": "Female",
            "am_adam": "Male, American",
            "am_michael": "Male, American",
            "bf_emma": "Female, British",
            "bm_george": "Male, British",
        }
        return descriptions.get(voice, "")

    def _render_menu(self, selected_index: int) -> None:
        """Render the voice selection menu."""
        self.console.print()
        self.console.print("[bold cyan]╔════════════════════════════════════════╗[/]")
        self.console.print("[bold cyan]║[/]        [bold white]SELECT VOICE[/]                   [bold cyan]║[/]")
        self.console.print("[bold cyan]╚════════════════════════════════════════╝[/]")
        self.console.print()

        for i, voice in enumerate(self.available_voices):
            desc = self.get_voice_description(voice)
            is_selected = i == selected_index
            marker = "▶" if is_selected else " "
            voice_style = "bold green" if is_selected else "white"
            self.console.print(f"  {marker} [bold]{i + 1}.[/] [{voice_style}]{voice:<12}[/] {desc}")

        self.console.print()
        self.console.print("[dim]↑/↓ navigate • ENTER select • ESC cancel[/]")

    def select_voice(self) -> str:
        """Display interactive voice selection menu with arrow keys."""
        import tty
        import termios

        selected_index = self.available_voices.index(self._current_voice)
        num_voices = len(self.available_voices)

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

            finally:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

        except Exception:
            self.console.print("[red]Error in interactive mode, falling back...[/]")
            return self._select_voice_fallback()

        return self._current_voice

    def _select_voice_fallback(self) -> str:
        """Fallback to number-based selection."""
        from rich.prompt import Prompt

        for i, voice in enumerate(self.available_voices, 1):
            desc = self.get_voice_description(voice)
            marker = "▶" if voice == self._current_voice else " "
            voice_style = "bold green" if voice == self._current_voice else "white"
            self.console.print(f"  {marker} [bold]{i}.[/] [{voice_style}]{voice:<12}[/] {desc}")

        choice = Prompt.ask(
            "[bold cyan]Select voice[/]",
            default="",
            console=self.console,
        )

        if not choice:
            return self._current_voice

        try:
            index = int(choice) - 1
            if 0 <= index < len(self.available_voices):
                self._current_voice = self.available_voices[index]
                self.console.print(f"[bold green]✓[/] Voice changed to: {self._current_voice}")
            else:
                self.console.print("[red]Invalid selection[/]")
        except ValueError:
            self.console.print("[red]Invalid input[/]")

        return self._current_voice

    def get_config(self) -> TTSConfig:
        """Get TTSConfig with current voice."""
        return TTSConfig(voice_name=self._current_voice)
