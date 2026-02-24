"""UI animation manager for VoiceTry application.

Coordinates UI rendering updates with threading for smooth animations.
Integrates with Rich Live display and terminal UI components.
"""

import threading
import time
from typing import Optional

from rich.live import Live


class UIAnimator:
    """Manages UI animation updates with threading.

    Coordinates visualizer and terminal components to render smooth
    animations through a background thread that continuously updates
    the Rich Live display.

    Thread-safe animation loop with graceful shutdown support.
    """

    def __init__(self, ui: 'VoiceTerminalUI', live: Live, fps: float = 8.0) -> None:
        """Initialize the animation manager.

        Args:
            ui: Terminal UI instance with render method
            live: Rich Live display instance
            fps: Animation frames per second (default: 8 - reduced to prevent flickering)
        """
        self.ui = ui
        self.live = live
        self._fps = fps
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Start the animation loop in a daemon thread.

        Creates and starts a background thread that continuously updates
        the UI display at the specified frame rate. The thread is marked
        as daemon to ensure cleanup on application exit.
        """
        self._running = True
        self._thread = threading.Thread(target=self._animate, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the animation loop.

        Sets the running flag to False and waits for the animation thread
        to terminate gracefully with a timeout.
        """
        self._running = False
        if self._thread:
            self._thread.join(timeout=0.5)

    def _animate(self) -> None:
        """Animation loop - runs in background thread.

        Continuously updates the UI display by calling render() on the
        UI component and passing the result to Live.update(). The loop
        runs until _running is set to False via stop().
        """
        sleep_time = 1.0 / self._fps
        while self._running:
            try:
                self.live.update(self.ui.render(), refresh=True)
                time.sleep(sleep_time)
            except Exception:
                # Silent fail - animation errors shouldn't crash the app
                pass
