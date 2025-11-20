"""
Hardware management package for the Raspberry Pi AI Assistant.

Exposes helper classes that encapsulate display, button, audio, and
mode-control responsibilities so the main application loop can remain
clean and testable.
"""

from .display_manager import DisplayManager
from .button_manager import ButtonManager
from .audio_manager import AudioManager
from .mode_controller import ModeController

