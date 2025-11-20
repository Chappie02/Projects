"""
Hybrid mode combines YOLO detections with the LLM to describe scenes
and answer quick follow-up questions.
"""

from __future__ import annotations

from typing import Optional

from modes.chat_mode import ChatMode
from modes.object_mode import ObjectMode


class HybridMode:
    """Simple orchestrator that fuses object detections with the LLM."""

    def __init__(self, chat_mode: Optional[ChatMode] = None, object_mode: Optional[ObjectMode] = None):
        self.chat_mode = chat_mode or ChatMode()
        self.object_mode = object_mode or ObjectMode()

    def run_once(self, follow_up_question: str = "") -> str:
        """Capture a frame, detect objects, and synthesize a response."""
        image, detected_objects = self.object_mode.capture_and_detect()
        summary = self.object_mode.generate_scene_summary(detected_objects)

        if not follow_up_question:
            return summary

        prompt = f"{summary}\n\nQuestion: {follow_up_question}\nAnswer concisely."
        return self.chat_mode.generate_response(prompt)

