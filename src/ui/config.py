"""UI configuration for VoiceTry application.

This module contains the color palette and application state definitions
used throughout the UI components.
"""

from enum import Enum


class Colors:
    """Cyberpunk color palette for the futuristic terminal UI."""

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
    """Application states for the voice AI terminal."""

    IDLE = "idle"
    RECORDING = "recording"
    TRANSCRIBING = "transcribing"
    THINKING = "thinking"
    SPEAKING = "speaking"
