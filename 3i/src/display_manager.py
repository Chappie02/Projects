"""
OLED display controller for the assistant UI.
"""

from __future__ import annotations

import logging
import textwrap
from dataclasses import dataclass
from typing import Optional

try:
    from Adafruit_SSD1306 import SSD1306_128_64
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # pragma: no cover - hardware-only dependency
    SSD1306_128_64 = None
    Image = ImageDraw = ImageFont = None


@dataclass
class DisplayStateTexts:
    boot: str = "Select Mode:\nK1 Chat Mode\nK2 Object Mode"
    chat_idle: str = "Chat Mode - Hold K3 to Speak"
    chat_listening: str = "Listening...\nRelease K3"
    object_idle: str = "Object Mode - Press K3 to Capture"
    processing: str = "Processing..."


class DisplayManager:
    """Handles rendering text to the OLED display."""

    def __init__(self, reset_pin: Optional[int] = None, logger: Optional[logging.Logger] = None):
        self._logger = logger or logging.getLogger(__name__)
        self._display = None
        self._state_texts = DisplayStateTexts()
        self._font = None

        if SSD1306_128_64 is None or Image is None:
            self._logger.warning("SSD1306 or Pillow not available; display output will be skipped.")
            return

        self._display = SSD1306_128_64(rst=reset_pin)
        self._display.begin()
        self._display.clear()
        self._display.display()
        self._font = ImageFont.load_default()

    def _render_text(self, text: str) -> None:
        if not self._display or not Image:
            self._logger.debug("Skipping OLED render: hardware not initialized.")
            return

        width = self._display.width
        height = self._display.height
        image = Image.new("1", (width, height))
        draw = ImageDraw.Draw(image)
        wrapped = textwrap.fill(text, width=18)
        draw.text((0, 0), wrapped, font=self._font, fill=255)
        self._display.image(image)
        self._display.display()
        self._logger.debug("OLED updated with text: %s", text)

    def show_boot(self) -> None:
        self._render_text(self._state_texts.boot)

    def show_chat_idle(self) -> None:
        self._render_text(self._state_texts.chat_idle)

    def show_chat_listening(self) -> None:
        self._render_text(self._state_texts.chat_listening)

    def show_object_idle(self) -> None:
        self._render_text(self._state_texts.object_idle)

    def show_processing(self) -> None:
        self._render_text(self._state_texts.processing)

    def show_message(self, message: str) -> None:
        self._render_text(message)

    def power_off(self) -> None:
        if self._display:
            self._display.clear()
            self._display.display()

