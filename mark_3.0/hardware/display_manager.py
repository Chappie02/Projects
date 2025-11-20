"""
Display manager for the 0.96-inch SSD1306 OLED (128x64, I2C) rotated 180°.

Handles drawing the current mode, system status, and speed setting.
"""

from __future__ import annotations

import threading
from typing import Optional

try:
    import board
    import busio
    from adafruit_ssd1306 import SSD1306_I2C
except ImportError as exc:  # pragma: no cover - hardware only
    raise ImportError(
        "Missing required libraries for the SSD1306 display. "
        "Install with 'pip install adafruit-circuitpython-ssd1306 adafruit-blinka'."
    ) from exc

from PIL import Image, ImageDraw, ImageFont


class DisplayManager:
    """High-level wrapper that keeps the OLED in sync with system state."""

    def __init__(
        self,
        width: int = 128,
        height: int = 64,
        i2c_address: int = 0x3C,
        rotate_180: bool = True,
        i2c_bus: Optional[busio.I2C] = None,
    ):
        self.width = width
        self.height = height
        self.rotate_180 = rotate_180

        self.i2c = i2c_bus or busio.I2C(board.SCL, board.SDA)
        self.display = SSD1306_I2C(self.width, self.height, self.i2c, addr=i2c_address)
        self.display.poweron()
        self.display.fill(0)
        self.display.show()

        self.image = Image.new("1", (self.width, self.height))
        self.draw = ImageDraw.Draw(self.image)
        self.font_small = ImageFont.load_default()
        self.font_large = ImageFont.load_default()

        self._lock = threading.Lock()
        self._last_payload = {
            "mode": "Chat",
            "status": "Idle",
            "speed": "Low",
            "message": "",
        }

        self.update_display()

    def _prepare_frame(self) -> Image.Image:
        """Render text onto the back buffer and return a (possibly rotated) image."""
        self.draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)

        mode_text = f"Mode: {self._last_payload['mode']}"
        status_text = f"Status: {self._last_payload['status']}"
        speed_text = f"Speed: {self._last_payload['speed']}"
        message_text = self._last_payload["message"][:20]  # keep it short

        self.draw.text((0, 0), mode_text, font=self.font_large, fill=255)
        self.draw.text((0, 16), status_text, font=self.font_small, fill=255)
        self.draw.text((0, 32), speed_text, font=self.font_small, fill=255)
        self.draw.text((0, 48), message_text, font=self.font_small, fill=255)

        return self.image.rotate(180) if self.rotate_180 else self.image

    def update(self, *, mode: str, status: str, speed: str, message: str = "") -> None:
        """Update the cached payload and refresh the OLED."""
        with self._lock:
            self._last_payload = {
                "mode": mode.capitalize(),
                "status": status.capitalize(),
                "speed": speed.capitalize(),
                "message": message,
            }
            self.update_display()

    def show_temporary_message(self, message: str) -> None:
        """Overlay a transient message without mutating the base payload."""
        with self._lock:
            cached = dict(self._last_payload)
            cached["message"] = message
            self._last_payload = cached
            self.update_display()

    def update_display(self) -> None:
        """Push the current frame buffer to the OLED."""
        frame = self._prepare_frame()
        self.display.image(frame)
        self.display.show()

    def clear(self) -> None:
        """Blank the OLED."""
        with self._lock:
            self.display.fill(0)
            self.display.show()

