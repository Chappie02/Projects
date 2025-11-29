"""
Entry point and controller loop for the Multi-Modal AI Assistant.
"""

from __future__ import annotations

import logging
import queue
import signal
import threading
from enum import Enum, auto

from .audio_manager import AudioManager
from .button_manager import ButtonConfig, ButtonManager
from .config import AssistantConfig
from .display_manager import DisplayManager
from .llm_manager import LLMManager
from .vision_manager import VisionManager


class Mode(Enum):
    BOOT = auto()
    CHAT = auto()
    OBJECT = auto()


class AssistantController:
    """Top-level orchestrator for mode switching and task execution."""

    def __init__(self, config: AssistantConfig):
        self._config = config
        self._logger = logging.getLogger("assistant")
        self._display = DisplayManager(config.hardware.oled_reset_pin, self._logger.getChild("display"))
        self._audio = AudioManager(config.audio, self._logger.getChild("audio"))
        self._llm = LLMManager(config.llm, self._logger.getChild("llm"))
        self._vision = VisionManager(config.vision, self._logger.getChild("vision"))
        button_cfg = ButtonConfig(
            chat_pin=config.hardware.chat_button_pin,
            object_pin=config.hardware.object_button_pin,
            action_pin=config.hardware.action_button_pin,
        )
        self._buttons = ButtonManager(button_cfg, self._logger.getChild("buttons"))
        self._event_queue: "queue.Queue[tuple[str, object]]" = queue.Queue()
        self._history: list[tuple[str, str]] = []
        self._mode = Mode.BOOT
        self._running = threading.Event()

        self._buttons.register_mode_callbacks(self._on_chat_mode, self._on_object_mode)
        self._buttons.register_action_callbacks(self._on_action_press, self._on_action_release)

    def start(self) -> None:
        """Display boot instructions and enter the event loop."""
        self._logger.info("Assistant controller starting.")
        self._display.show_boot()
        self._running.set()
        self._event_loop()

    def stop(self) -> None:
        """Stop execution and clean up hardware resources."""
        self._logger.info("Assistant controller stopping.")
        self._running.clear()
        self._buttons.cleanup()
        self._audio.cleanup()
        self._display.power_off()

    def _event_loop(self) -> None:
        while self._running.is_set():
            try:
                event, payload = self._event_queue.get(timeout=0.1)
                self._logger.debug("Handling event: %s", event)
                handler = getattr(self, f"_handle_{event}", None)
                if handler:
                    handler(payload)
            except queue.Empty:
                continue
            except Exception as exc:  # noqa: BLE001
                self._logger.exception("Unexpected error while handling events: %s", exc)

    # Button callbacks -> queue events -----------------------------------------------------------
    def _on_chat_mode(self) -> None:
        self._event_queue.put(("mode_chat", None))

    def _on_object_mode(self) -> None:
        self._event_queue.put(("mode_object", None))

    def _on_action_press(self) -> None:
        if self._mode == Mode.CHAT:
            self._event_queue.put(("chat_press", None))
        elif self._mode == Mode.OBJECT:
            self._event_queue.put(("object_trigger", None))

    def _on_action_release(self) -> None:
        if self._mode == Mode.CHAT:
            self._event_queue.put(("chat_release", None))

    # Event handlers -----------------------------------------------------------------------------
    def _handle_mode_chat(self, _payload) -> None:
        self._mode = Mode.CHAT
        self._display.show_chat_idle()
        self._logger.info("Switched to chat mode.")

    def _handle_mode_object(self, _payload) -> None:
        self._mode = Mode.OBJECT
        self._display.show_object_idle()
        self._logger.info("Switched to object detection mode.")

    def _handle_chat_press(self, _payload) -> None:
        try:
            self._audio.start_recording()
            self._display.show_chat_listening()
        except Exception as exc:  # noqa: BLE001
            self._logger.exception("Failed to start recording: %s", exc)
            self._display.show_message("Mic error.")

    def _handle_chat_release(self, _payload) -> None:
        threading.Thread(target=self._process_chat_interaction, daemon=True).start()

    def _process_chat_interaction(self) -> None:
        self._display.show_processing()
        try:
            transcript = self._audio.stop_and_transcribe()
            if not transcript:
                self._display.show_chat_idle()
                return

            self._logger.info("User said: %s", transcript)
            response = self._llm.generate_response(transcript, history=self._history)
            self._history.append((transcript, response))
            self._llm.add_memory(transcript, response)
            self._audio.speak_text(response)
            self._display.show_chat_idle()
        except Exception as exc:  # noqa: BLE001
            self._logger.exception("Chat pipeline failed: %s", exc)
            self._display.show_message("Chat error.")

    def _handle_object_trigger(self, _payload) -> None:
        threading.Thread(target=self._process_object_capture, daemon=True).start()

    def _process_object_capture(self) -> None:
        self._display.show_processing()
        try:
            image_path = self._vision.capture_image()
            detections = self._vision.detect_objects(image_path)
            summary = self._vision.summarize_detections(detections, self._llm)
            self._audio.speak_text(summary)
            self._display.show_object_idle()
        except Exception as exc:  # noqa: BLE001
            self._logger.exception("Object mode failed: %s", exc)
            self._display.show_message("Object error.")


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


def main() -> None:
    configure_logging()
    config = AssistantConfig.load()
    controller = AssistantController(config)

    def handle_exit(signum, _frame):
        logging.getLogger("assistant").info("Received signal %s, shutting down.", signum)
        controller.stop()

    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)

    try:
        controller.start()
    finally:
        controller.stop()


if __name__ == "__main__":
    main()

