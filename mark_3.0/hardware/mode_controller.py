"""
Shared state container for Chat, Detection, and Hybrid modes.
"""

from __future__ import annotations

import threading
from typing import Callable, Dict, Optional


class ModeController:
    """Keeps track of the current mode, speed, and system status."""

    MODES = ["chat", "detection", "hybrid"]
    SPEEDS = ["low", "medium", "high"]

    def __init__(self, display_manager):
        self.display = display_manager
        self._lock = threading.Lock()
        self.mode_index = 0
        self.speed_index = 0
        self.system_status = "Idle"
        self._status_callbacks: Dict[str, Callable[[], None]] = {}
        self._update_display()

    @property
    def current_mode(self) -> str:
        return self.MODES[self.mode_index]

    @property
    def current_speed(self) -> str:
        return self.SPEEDS[self.speed_index]

    def _update_display(self, message: str = "") -> None:
        self.display.update(
            mode=self.current_mode.title(),
            status=self.system_status,
            speed=self.current_speed.title(),
            message=message,
        )

    def cycle_mode(self) -> None:
        with self._lock:
            self.mode_index = (self.mode_index + 1) % len(self.MODES)
            self.system_status = "Idle"
            self._update_display("Mode changed")
        self._invoke_callback("mode")

    def cycle_speed(self) -> None:
        with self._lock:
            self.speed_index = (self.speed_index + 1) % len(self.SPEEDS)
            self._update_display("Speed changed")
        self._invoke_callback("speed")

    def set_status(self, status: str, message: str = "") -> None:
        with self._lock:
            self.system_status = status.title()
            self._update_display(message)

    def handle_general_command(self) -> None:
        with self._lock:
            self._update_display("Refreshing…")
        self._invoke_callback("general")

    def handle_voice_command(self, command: str) -> None:
        command = command.lower()
        if "switch to chat" in command or "chat mode" in command:
            self._set_mode("chat")
        elif "switch to object" in command or "object mode" in command or "detection" in command:
            self._set_mode("detection")
        elif "switch to hybrid" in command or "hybrid mode" in command:
            self._set_mode("hybrid")

    def _set_mode(self, mode: str) -> None:
        if mode not in self.MODES:
            return
        with self._lock:
            self.mode_index = self.MODES.index(mode)
            self.system_status = "Idle"
            self._update_display("Voice cmd")
        self._invoke_callback("mode")

    def register_callback(self, event: str, callback: Callable[[], None]) -> None:
        """event keys: 'mode', 'speed', 'general'."""
        self._status_callbacks[event] = callback

    def _invoke_callback(self, event: str) -> None:
        callback = self._status_callbacks.get(event)
        if callback:
            callback()

