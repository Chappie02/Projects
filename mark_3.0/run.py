#!/usr/bin/env python3
"""
Entry point for the hardware-integrated AI Assistant runtime.

This script wires together:
  - DisplayManager (OLED feedback)
  - ButtonManager (K1–K3 inputs)
  - AudioManager (wake word + commands)
  - ModeController (state machine)
  - ChatMode / ObjectMode / HybridMode (AI capabilities)
"""

from __future__ import annotations

import signal
import sys
import time
import threading

from hardware import AudioManager, ButtonManager, DisplayManager, ModeController
from modes.chat_mode import ChatMode
from modes.object_mode import ObjectMode
from modes.hybrid_mode import HybridMode


def main() -> None:
    display = DisplayManager()
    mode_controller = ModeController(display)

    chat_mode = ChatMode()
    object_mode = ObjectMode()
    hybrid_mode = HybridMode(chat_mode, object_mode)

    def refresh_current_mode() -> None:
        mode = mode_controller.current_mode
        if mode == "chat":
            mode_controller.set_status("Processing", "Chat ready")
        elif mode == "detection":
            mode_controller.set_status("Processing", "YOLO ready")
        else:
            mode_controller.set_status("Processing", "Hybrid ready")

    mode_controller.register_callback("mode", refresh_current_mode)

    general_event = threading.Event()

    def trigger_general_action() -> None:
        mode_controller.handle_general_command()
        general_event.set()

    # K1 -> GPIO17 (Pin 11), K2 -> GPIO27 (Pin 13), K3 -> GPIO22 (Pin 15)
    button_manager = ButtonManager(k1_pin=17, k2_pin=27, k3_pin=22, bounce_time_ms=200)
    button_manager.register_callbacks(
        on_mode_change=mode_controller.cycle_mode,
        on_speed_change=mode_controller.cycle_speed,
        on_general_command=trigger_general_action,
    )

    def on_wake() -> None:
        mode_controller.set_status("Listening", "Wake word")

    def on_command(text: str) -> None:
        if "switch" in text:
            mode_controller.handle_voice_command(text)
        elif "refresh" in text or "listen" in text or "wake" in text:
            trigger_general_action()
        else:
            mode_controller.set_status("Processing", text[:20])

    audio_manager = AudioManager(
        wake_word="hey vision",
        on_wake=on_wake,
        on_command=on_command,
    )
    audio_manager.start()

    running = True

    def _handle_sigterm(signum, frame):
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, _handle_sigterm)
    signal.signal(signal.SIGTERM, _handle_sigterm)

    try:
        while running:
            if general_event.is_set():
                general_event.clear()
                mode = mode_controller.current_mode

                if mode == "chat":
                    mode_controller.set_status("Processing", "Chat wake")
                elif mode == "detection":
                    object_mode.analyze_scene()
                    mode_controller.set_status("Idle", "Detection done")
                elif mode == "hybrid":
                    response = hybrid_mode.run_once()
                    mode_controller.set_status("Idle", response[:20])
            time.sleep(0.1)
    finally:
        audio_manager.stop()
        button_manager.cleanup()
        display.clear()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Fatal error: {exc}")
        sys.exit(1)

