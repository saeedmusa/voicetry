"""Futuristic terminal UI with audio visualization.

This module contains the VoiceTerminalUI class which provides a rich terminal
interface with multiple panels for header, visualizer, status, and messages.
"""

import math
from typing import Callable, Optional

from rich.align import Align
from rich.console import Console, Group
from rich.panel import Panel
from rich.style import Style
from rich.text import Text

from .config import AppState, Colors
from .visualizer import AudioVisualizer


# ═══════════════════════════════════════════════════════════════════════════════
# FUTURISTIC TERMINAL UI
# ═══════════════════════════════════════════════════════════════════════════════

class VoiceTerminalUI:
    """Futuristic terminal interface for voice AI.

    This class provides a modular terminal UI with separate panels for:
    - Header: Shows app title and current state
    - Visualizer: Animated audio level bars
    - Status: Current operation status with instructions
    - Messages: User input and AI response display
    """

    def __init__(self) -> None:
        """Initialize the terminal UI."""
        self.console = Console()
        self.visualizer = AudioVisualizer()
        self.state = AppState.IDLE

        # Message buffers
        self.user_message: str = ""
        self.ai_response: str = ""
        self.status_text: str = ""

        # Animation state
        self._pulse_phase: float = 0.0
        self._spin_chars: str = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        self._spin_index: int = 0

        # Speaking timing
        self.speaking_time: float = 0.0
        self._speaking_start_time: float = 0.0

    def _get_pulse_intensity(self) -> float:
        """Get current pulse animation intensity.

        Returns:
            Float value between 0.0 and 1.0 based on sine wave.
        """
        return (math.sin(self._pulse_phase) + 1) / 2

    def _get_spinner(self) -> str:
        """Get current spinner character.

        Returns:
            Current character from the spinner sequence.
        """
        return self._spin_chars[self._spin_index % len(self._spin_chars)]

    def _update_animation(self) -> None:
        """Update animation states for pulse and spinner."""
        self._pulse_phase += 0.15
        self._spin_index += 1

    def _get_state_color(self) -> str:
        """Get color for current application state.

        Returns:
            Hex color code for the current state.
        """
        colors = {
            AppState.IDLE: Colors.IDLE,
            AppState.RECORDING: Colors.RECORDING,
            AppState.TRANSCRIBING: Colors.NEON_ORANGE,
            AppState.THINKING: Colors.NEON_PURPLE,
            AppState.SPEAKING: Colors.SPEAKING,
        }
        return colors.get(self.state, Colors.IDLE)

    def _get_state_icon(self) -> str:
        """Get icon for current application state.

        Returns:
            Unicode icon character for the current state.
        """
        icons = {
            AppState.IDLE: "◉",
            AppState.RECORDING: "●",
            AppState.TRANSCRIBING: "◈",
            AppState.THINKING: "◆",
            AppState.SPEAKING: "♦",
        }
        return icons.get(self.state, "◉")

    def _render_header(self) -> Panel:
        """Render the header panel with title and state.

        Returns:
            Rich Panel containing the header content.
        """
        self._update_animation()

        pulse = self._get_pulse_intensity()
        state_color = self._get_state_color()
        icon = self._get_state_icon()

        # Glowing title
        title = Text()
        title.append("╔══ ", style=Style(color=Colors.NEON_CYAN))
        title.append("VOICETRY", style=Style(
            color=Colors.NEON_CYAN,
            bold=True,
        ))
        title.append(" ══╗", style=Style(color=Colors.NEON_CYAN))

        # Subtitle with state
        subtitle = Text()
        subtitle.append(f"  {icon} ", style=Style(color=state_color))
        subtitle.append(self.state.value.upper(), style=Style(
            color=state_color,
            bold=True,
        ))
        
        # Show timing for SPEAKING state
        if self.state == AppState.SPEAKING:
            self.update_speaking_time()
            subtitle.append(" │ ", style=Style(color=Colors.TEXT_DIM))
            subtitle.append(f"{self.speaking_time:.1f}s", style=Style(
                color=Colors.NEON_GREEN,
                bold=True,
            ))
        else:
            subtitle.append(" ─ ", style=Style(color=Colors.TEXT_DIM))
        
        subtitle.append("Voice AI Terminal v1.0", style=Style(color=Colors.TEXT_DIM))

        content = Group(
            Align.center(title),
            "",
            Align.center(subtitle),
        )

        return Panel(
            content,
            border_style=Style(color=Colors.BORDER_ACTIVE),
            padding=(0, 2),
        )

    def _render_visualizer(self) -> Panel:
        """Render the audio visualizer panel.

        Returns:
            Rich Panel containing the animated audio visualizer.
        """
        bars = self.visualizer.render(self.state)

        # Add some padding lines
        content = Group(
            "",
            Align.center(bars),
            "",
        )

        # Border color pulses with state
        border_color = self._get_state_color()
        pulse_intensity = self._get_pulse_intensity()

        return Panel(
            content,
            border_style=Style(color=border_color),
            padding=(0, 1),
        )

    def _render_status(self) -> Panel:
        """Render status messages panel.

        Returns:
            Rich Panel containing current status and instructions.
        """
        content = Text()

        if self.state == AppState.RECORDING:
            content.append("🎤 ", style=Style(color=Colors.RECORDING))
            content.append("Listening...", style=Style(color=Colors.RECORDING))
        elif self.state == AppState.TRANSCRIBING:
            content.append(f"{self._get_spinner()} ", style=Style(color=Colors.NEON_ORANGE))
            content.append("Transcribing audio...", style=Style(color=Colors.NEON_ORANGE))
        elif self.state == AppState.THINKING:
            content.append(f"{self._get_spinner()} ", style=Style(color=Colors.NEON_PURPLE))
            content.append("DeepSeek is thinking...", style=Style(color=Colors.NEON_PURPLE))
        elif self.state == AppState.SPEAKING:
            content.append("🔊 ", style=Style(color=Colors.SPEAKING))
            content.append("Speaking response...", style=Style(color=Colors.SPEAKING))
        else:
            content.append("Ready", style=Style(color=Colors.TEXT_DIM))
            content.append(" │ ", style=Style(color=Colors.TEXT_DIM))
            content.append("SPACE", style=Style(color=Colors.NEON_CYAN, bold=True))
            content.append(" record │ ", style=Style(color=Colors.TEXT_DIM))
            content.append("Q", style=Style(color=Colors.NEON_CYAN, bold=True))
            content.append(" quit", style=Style(color=Colors.TEXT_DIM))

        return Panel(
            Align.center(content),
            border_style=Style(color=Colors.BORDER_DIM),
            padding=(0, 1),
        )

    def _render_messages(self) -> Panel:
        """Render user message and AI response panel.

        Returns:
            Rich Panel containing the conversation history.
        """
        content = Text()

        # User message
        if self.user_message:
            content.append("┌─ YOU\n", style=Style(color=Colors.NEON_GREEN))
            content.append("│ ", style=Style(color=Colors.NEON_GREEN))
            content.append(self.user_message, style=Style(color=Colors.TEXT_BRIGHT))
            content.append("\n")

        # AI response
        if self.ai_response:
            content.append("\n┌─ AI\n", style=Style(color=Colors.NEON_PURPLE))
            content.append("│ ", style=Style(color=Colors.NEON_PURPLE))
            content.append(self.ai_response, style=Style(color=Colors.TEXT_BRIGHT))

        if not self.user_message and not self.ai_response:
            content.append(
                "Your conversation will appear here...",
                style=Style(color=Colors.TEXT_DIM)
            )

        return Panel(
            content,
            title="[bold cyan]CONVERSATION[/]",
            border_style=Style(color=Colors.BORDER_ACTIVE),
            padding=(1, 1),
        )

    def render(self) -> Group:
        """Render the complete UI with all panels.

        Returns:
            Rich Group containing all UI panels arranged vertically.
        """
        return Group(
            self._render_header(),
            "",
            self._render_visualizer(),
            "",
            self._render_status(),
            "",
            self._render_messages(),
        )

    def update_audio_level(self, level: float) -> None:
        """Update audio level for visualization.

        Args:
            level: Audio level between 0.0 (silent) and 1.0 (maximum).
        """
        self.visualizer.update_level(level)

    def set_user_message(self, message: str) -> None:
        """Set the user's transcribed message.

        Args:
            message: The user's message text to display.
        """
        self.user_message = message

    def append_ai_response(self, chunk: str) -> None:
        """Append to the AI response (for streaming).

        Args:
            chunk: A chunk of text from the AI response.
        """
        self.ai_response += chunk

    def clear_messages(self) -> None:
        """Clear message buffers."""
        self.user_message = ""
        self.ai_response = ""

    def set_state(self, state: AppState) -> None:
        """Set the application state.

        Args:
            state: The new application state from AppState enum.
        """
        self.state = state
        if state == AppState.SPEAKING:
            import time
            self._speaking_start_time = time.time()
            self.speaking_time = 0.0
        else:
            self._speaking_start_time = 0.0
            self.speaking_time = 0.0

    def update_speaking_time(self) -> None:
        """Update the speaking time counter."""
        if self.state == AppState.SPEAKING and self._speaking_start_time > 0:
            import time
            self.speaking_time = time.time() - self._speaking_start_time
