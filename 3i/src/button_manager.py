"""
GPIO button management for the assistant modes.
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from typing import Callable, Optional

try:
    import RPi.GPIO as GPIO
except ImportError:  # pragma: no cover - hardware-only dependency
    GPIO = None


ButtonCallback = Callable[[], None]


@dataclass
class ButtonConfig:
    chat_pin: int
    object_pin: int
    action_pin: int
    debounce_ms: int = 200


class ButtonManager:
    """Sets up GPIO inputs and routes events to the controller."""

    def __init__(self, config: ButtonConfig, logger: Optional[logging.Logger] = None):
        self._config = config
        self._logger = logger or logging.getLogger(__name__)
        self._chat_cb: Optional[ButtonCallback] = None
        self._object_cb: Optional[ButtonCallback] = None
        self._press_cb: Optional[ButtonCallback] = None
        self._release_cb: Optional[ButtonCallback] = None
        self._lock = threading.Lock()

        if GPIO is None:
            self._logger.warning("RPi.GPIO not available; button handling disabled.")
            return

        GPIO.setmode(GPIO.BCM)
        for pin in (config.chat_pin, config.object_pin, config.action_pin):
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        self._register_events()

    def register_mode_callbacks(self, chat_cb: ButtonCallback, object_cb: ButtonCallback) -> None:
        self._chat_cb = chat_cb
        self._object_cb = object_cb

    def register_action_callbacks(self, press_cb: ButtonCallback, release_cb: Optional[ButtonCallback] = None) -> None:
        self._press_cb = press_cb
        self._release_cb = release_cb

    def _register_events(self) -> None:
        if GPIO is None:
            return

        bounce = self._config.debounce_ms
        GPIO.add_event_detect(self._config.chat_pin, GPIO.FALLING, callback=self._wrap(self._on_chat), bouncetime=bounce)
        GPIO.add_event_detect(self._config.object_pin, GPIO.FALLING, callback=self._wrap(self._on_object), bouncetime=bounce)
        GPIO.add_event_detect(self._config.action_pin, GPIO.BOTH, callback=self._wrap(self._on_action), bouncetime=bounce)

    def _wrap(self, func: Callable[[int], None]) -> Callable[[int], None]:
        def inner(channel: int) -> None:  # pragma: no cover - hardware callback
            try:
                func(channel)
            except Exception as exc:  # noqa: BLE001
                self._logger.exception("Button callback error: %s", exc)

        return inner

    def _on_chat(self, _: int) -> None:
        if self._chat_cb:
            self._logger.debug("K1 pressed -> Chat mode.")
            self._chat_cb()

    def _on_object(self, _: int) -> None:
        if self._object_cb:
            self._logger.debug("K2 pressed -> Object mode.")
            self._object_cb()

    def _on_action(self, channel: int) -> None:
        if GPIO is None:
            return

        pressed = GPIO.input(channel) == GPIO.LOW
        callback = self._press_cb if pressed else self._release_cb
        if callback:
            state = "pressed" if pressed else "released"
            self._logger.debug("K3 %s -> dispatching callback.", state)
            # Serialize callbacks to avoid re-entry.
            with self._lock:
                callback()

    def cleanup(self) -> None:
        if GPIO:
            GPIO.cleanup()

