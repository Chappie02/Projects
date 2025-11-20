"""
Button manager for momentary switches K1/K2/K3 with debounce.
"""

from __future__ import annotations

import time
from typing import Callable, Optional

try:
    import RPi.GPIO as GPIO
except ImportError as exc:  # pragma: no cover - hardware only
    raise ImportError(
        "RPi.GPIO is required for button handling. Install with 'sudo apt install python3-rpi.gpio'."
    ) from exc


class ButtonManager:
    """Registers callbacks for three hardware buttons with software debounce.

    Default wiring (matching `run.py`):
        - K1 -> GPIO17 (Pin 11)
        - K2 -> GPIO27 (Pin 13)
        - K3 -> GPIO22 (Pin 15)
    """

    def __init__(
        self,
        k1_pin: int,
        k2_pin: int,
        k3_pin: int,
        bounce_time_ms: int = 200,
    ):
        self.k1_pin = k1_pin
        self.k2_pin = k2_pin
        self.k3_pin = k3_pin
        self.bounce_time_ms = bounce_time_ms

        self._callbacks = {"k1": None, "k2": None, "k3": None}
        self._last_press = {"k1": 0.0, "k2": 0.0, "k3": 0.0}

        GPIO.setmode(GPIO.BCM)
        for pin in (self.k1_pin, self.k2_pin, self.k3_pin):
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        GPIO.add_event_detect(self.k1_pin, GPIO.FALLING, callback=self._handle_k1, bouncetime=self.bounce_time_ms)
        GPIO.add_event_detect(self.k2_pin, GPIO.FALLING, callback=self._handle_k2, bouncetime=self.bounce_time_ms)
        GPIO.add_event_detect(self.k3_pin, GPIO.FALLING, callback=self._handle_k3, bouncetime=self.bounce_time_ms)

    def register_callbacks(
        self,
        *,
        on_mode_change: Optional[Callable[[], None]] = None,
        on_speed_change: Optional[Callable[[], None]] = None,
        on_general_command: Optional[Callable[[], None]] = None,
    ) -> None:
        """Attach callables to the button events."""
        self._callbacks["k1"] = on_mode_change
        self._callbacks["k2"] = on_speed_change
        self._callbacks["k3"] = on_general_command

    def _debounced_call(self, key: str, func: Optional[Callable[[], None]]) -> None:
        now = time.monotonic()
        if (now - self._last_press[key]) * 1000 < self.bounce_time_ms:
            return
        self._last_press[key] = now

        if func:
            func()

    def _handle_k1(self, channel: int) -> None:  # pragma: no cover - hardware callback
        self._debounced_call("k1", self._callbacks["k1"])

    def _handle_k2(self, channel: int) -> None:  # pragma: no cover - hardware callback
        self._debounced_call("k2", self._callbacks["k2"])

    def _handle_k3(self, channel: int) -> None:  # pragma: no cover - hardware callback
        self._debounced_call("k3", self._callbacks["k3"])

    def cleanup(self) -> None:
        """Release GPIO resources."""
        GPIO.cleanup()

