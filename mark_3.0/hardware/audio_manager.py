"""
Audio manager that provides wake-word detection and voice command parsing.
"""

from __future__ import annotations

import threading
from typing import Callable, Optional

import speech_recognition as sr


class AudioManager:
    """Listens to the Bluetooth microphone, surfaces wake events and commands."""

    def __init__(
        self,
        wake_word: str,
        on_wake: Callable[[], None],
        on_command: Callable[[str], None],
        device_index: Optional[int] = None,
        energy_threshold: int = 250,
    ):
        self.wake_word = wake_word.lower()
        self.on_wake = on_wake
        self.on_command = on_command
        self.device_index = device_index
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = energy_threshold
        self._stop_event = threading.Event()
        self._listener = None

    def start(self) -> None:
        """Begin background listening loop."""
        microphone = sr.Microphone(device_index=self.device_index)
        self._listener = self.recognizer.listen_in_background(microphone, self._callback)

    def _callback(self, recognizer: sr.Recognizer, audio: sr.AudioData) -> None:  # pragma: no cover - hardware loop
        if self._stop_event.is_set():
            return

        try:
            transcript = recognizer.recognize_google(audio).lower()
        except sr.UnknownValueError:
            return
        except sr.RequestError:
            return

        if self.wake_word in transcript:
            self.on_wake()
            clean_text = transcript.replace(self.wake_word, "").strip()
            if clean_text:
                self.on_command(clean_text)
            return

        self.on_command(transcript)

    def stop(self) -> None:
        """Stop background listening."""
        self._stop_event.set()
        if self._listener:
            self._listener(wait_for_stop=False)

