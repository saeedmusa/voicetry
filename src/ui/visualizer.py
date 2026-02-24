"""Audio visualizer with animated bars for terminal UI."""

import math
import random
import time
from dataclasses import dataclass

from rich.style import Style
from rich.text import Text

from .config import AppState, Colors


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

    def update_level(self, level: float) -> None:
        """Update visualizer with new audio level (0.0 to 1.0)."""
        for i, bar in enumerate(self.bars):
            wave_offset = math.sin(time.time() * 5 + i * 0.5) * 0.3
            random_factor = random.uniform(0.8, 1.2)

            bar.target_height = min(1.0, max(0.0,
                level * random_factor + wave_offset * level
            ))
            bar.glow_intensity = bar.target_height

    def _animate_bars(self) -> None:
        """Smooth bar height transitions."""
        for bar in self.bars:
            diff = bar.target_height - bar.height
            bar.height += diff * 0.3

    def render(self, state: AppState) -> Text:
        """Render the visualizer bars."""
        self._animate_bars()

        if state == AppState.RECORDING:
            color = Colors.RECORDING
        elif state == AppState.SPEAKING:
            color = Colors.SPEAKING
        elif state == AppState.THINKING:
            color = Colors.NEON_PURPLE
        else:
            color = Colors.IDLE

        bars_text = Text()

        for bar in self.bars:
            char_index = int(bar.height * (len(self.BAR_CHARS) - 1))
            char_index = max(0, min(len(self.BAR_CHARS) - 1, char_index))
            char = self.BAR_CHARS[char_index]

            style = Style(color=color, bold=bar.glow_intensity > 0.5)
            bars_text.append(char, style=style)
            bars_text.append(" ")

        return bars_text
