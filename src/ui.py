"""Futuristic terminal UI with audio visualization."""

import math
import os
import random
import threading
import time
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional

from rich.align import Align
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.style import Style
from rich.text import Text


# ═══════════════════════════════════════════════════════════════════════════════
# COLOR PALETTE - Cyberpunk Futuristic Theme
# ═══════════════════════════════════════════════════════════════════════════════

class Colors:
    """Cyberpunk color palette."""
    # Primary colors
    NEON_CYAN = "#00fff7"
    NEON_GREEN = "#39ff14"
    NEON_PURPLE = "#bf00ff"
    NEON_PINK = "#ff00ff"
    NEON_ORANGE = "#ff6600"
    NEON_BLUE = "#0066ff"

    # Background/dark colors
    DARK_BG = "#0a0a1a"
    PANEL_BG = "#0d1117"
    BORDER_DIM = "#1a3a4a"
    BORDER_ACTIVE = "#00fff7"

    # Text colors
    TEXT_BRIGHT = "#ffffff"
    TEXT_DIM = "#6a7a8a"
    TEXT_CYAN = "#00d4aa"
    TEXT_GREEN = "#00ff88"
    TEXT_PURPLE = "#aa88ff"

    # Status colors
    RECORDING = "#ff3366"
    PROCESSING = "#ffaa00"
    SPEAKING = "#00ff88"
    IDLE = "#4466aa"


class AppState(Enum):
    """Application states."""
    IDLE = "idle"
    RECORDING = "recording"
    TRANSCRIBING = "transcribing"
    THINKING = "thinking"
    SPEAKING = "speaking"


# ═══════════════════════════════════════════════════════════════════════════════
# AUDIO VISUALIZER
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class BarData:
    """Data for a single visualizer bar."""
    height: float = 0.0
    target_height: float = 0.0
    glow_intensity: float = 0.0


class AudioVisualizer:
    """Animated audio visualizer with glowing bars."""

    BAR_CHARS = ["▁", "▂", "▃", "▄", "▅", "▆", "▇", "█"]
    NUM_BARS = 20

    def __init__(self):
        self.bars = [BarData() for _ in range(self.NUM_BARS)]
        self._animation_thread: Optional[threading.Thread] = None
        self._running = False

    def update_level(self, level: float) -> None:
        """Update visualizer with new audio level (0.0 to 1.0)."""
        for i, bar in enumerate(self.bars):
            # Create wave-like pattern with some randomness
            wave_offset = math.sin(time.time() * 5 + i * 0.5) * 0.3
            random_factor = random.uniform(0.8, 1.2)

            bar.target_height = min(1.0, max(0.0,
                level * random_factor + wave_offset * level
            ))
            bar.glow_intensity = bar.target_height

    def _animate_bars(self) -> None:
        """Smooth bar height transitions."""
        for bar in self.bars:
            # Smooth interpolation
            diff = bar.target_height - bar.height
            bar.height += diff * 0.3

    def render(self, state: AppState) -> Text:
        """Render the visualizer bars."""
        self._animate_bars()

        # Choose color based on state
        if state == AppState.RECORDING:
            color = Colors.RECORDING
        elif state == AppState.SPEAKING:
            color = Colors.SPEAKING
        elif state == AppState.THINKING:
            color = Colors.NEON_PURPLE
        else:
            color = Colors.IDLE

        # Build the bar string
        bars_text = Text()

        for bar in self.bars:
            # Map height to bar character
            char_index = int(bar.height * (len(self.BAR_CHARS) - 1))
            char_index = max(0, min(len(self.BAR_CHARS) - 1, char_index))
            char = self.BAR_CHARS[char_index]

            # Apply glow effect with bold
            style = Style(color=color, bold=bar.glow_intensity > 0.5)
            bars_text.append(char, style=style)
            bars_text.append(" ")  # Space between bars

        return bars_text


# ═══════════════════════════════════════════════════════════════════════════════
# FUTURISTIC TERMINAL UI
# ═══════════════════════════════════════════════════════════════════════════════

class VoiceTerminalUI:
    """Futuristic terminal interface for voice AI."""

    def __init__(self):
        self.console = Console()
        self.visualizer = AudioVisualizer()
        self.state = AppState.IDLE

        # Message buffers
        self.user_message = ""
        self.ai_response = ""
        self.status_text = ""

        # Animation state
        self._pulse_phase = 0.0
        self._spin_chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        self._spin_index = 0

    def _get_pulse_intensity(self) -> float:
        """Get current pulse animation intensity."""
        return (math.sin(self._pulse_phase) + 1) / 2

    def _get_spinner(self) -> str:
        """Get current spinner character."""
        return self._spin_chars[self._spin_index % len(self._spin_chars)]

    def _update_animation(self) -> None:
        """Update animation states."""
        self._pulse_phase += 0.15
        self._spin_index += 1

    def _get_state_color(self) -> str:
        """Get color for current state."""
        colors = {
            AppState.IDLE: Colors.IDLE,
            AppState.RECORDING: Colors.RECORDING,
            AppState.TRANSCRIBING: Colors.NEON_ORANGE,
            AppState.THINKING: Colors.NEON_PURPLE,
            AppState.SPEAKING: Colors.SPEAKING,
        }
        return colors.get(self.state, Colors.IDLE)

    def _get_state_icon(self) -> str:
        """Get icon for current state."""
        icons = {
            AppState.IDLE: "◉",
            AppState.RECORDING: "●",
            AppState.TRANSCRIBING: "◈",
            AppState.THINKING: "◆",
            AppState.SPEAKING: "♦",
        }
        return icons.get(self.state, "◉")

    def _render_header(self) -> Panel:
        """Render the header panel."""
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
        """Render the audio visualizer panel."""
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
        """Render status messages."""
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
        """Render user message and AI response."""
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
        """Render the complete UI."""
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
        """Update audio level for visualization."""
        self.visualizer.update_level(level)

    def set_user_message(self, message: str) -> None:
        """Set the user's transcribed message."""
        self.user_message = message

    def append_ai_response(self, chunk: str) -> None:
        """Append to the AI response (for streaming)."""
        self.ai_response += chunk

    def clear_messages(self) -> None:
        """Clear message buffers."""
        self.user_message = ""
        self.ai_response = ""

    def set_state(self, state: AppState) -> None:
        """Set the application state."""
        self.state = state


# ═══════════════════════════════════════════════════════════════════════════════
# ANIMATION HELPER
# ═══════════════════════════════════════════════════════════════════════════════

class UIAnimator:
    """Manages UI animation updates."""

    def __init__(self, ui: VoiceTerminalUI, live: Live):
        self.ui = ui
        self.live = live
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Start animation loop."""
        self._running = True
        self._thread = threading.Thread(target=self._animate, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop animation loop."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=0.5)

    def _animate(self) -> None:
        """Animation loop."""
        while self._running:
            try:
                self.live.update(self.ui.render(), refresh=True)
                time.sleep(0.125)  # 8 FPS - matches Live refresh rate
            except Exception:
                pass
