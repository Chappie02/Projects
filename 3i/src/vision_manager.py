"""
Camera capture and YOLO inference utilities.
"""

from __future__ import annotations

import logging
import threading
import time
from pathlib import Path
from typing import List, Optional, Sequence

from .config import VisionConfig

try:  # pragma: no cover - hardware dependency
    from picamera2 import Picamera2
except ImportError:
    Picamera2 = None

try:  # pragma: no cover - heavy dependency
    from ultralytics import YOLO
except ImportError:
    YOLO = None


class VisionManager:
    """Controls PiCamera2 capture and YOLO detections."""

    def __init__(self, config: VisionConfig, logger: Optional[logging.Logger] = None):
        self._config = config
        self._logger = logger or logging.getLogger(__name__)
        self._camera = Picamera2() if Picamera2 else None
        self._yolo = YOLO(str(config.yolo_model_path)) if YOLO else None
        self._capture_lock = threading.Lock()
        Path(config.object_save_dir).mkdir(parents=True, exist_ok=True)

        if self._camera:
            self._camera.configure(
                self._camera.create_still_configuration(
                    main={"size": config.capture_resolution, "format": config.capture_format}
                )
            )

    def capture_image(self) -> Path:
        """Capture and persist a single frame from the camera."""
        if self._camera is None:
            raise RuntimeError("picamera2 is required but not installed.")

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        save_path = self._config.object_save_dir / f"capture_{timestamp}.jpg"

        with self._capture_lock:
            self._logger.debug("Starting camera preview for capture.")
            self._camera.start_and_capture_files(str(save_path), show_preview=False)

        self._logger.info("Image captured: %s", save_path)
        return save_path

    def detect_objects(self, image_path: Path) -> List[str]:
        """Run YOLO inference and return detected class names."""
        if self._yolo is None:
            raise RuntimeError("YOLO model not available; install ultralytics or provide a model.")

        results = self._yolo(str(image_path))
        detections: List[str] = []
        for result in results:
            for box in result.boxes:
                cls_id = int(box.cls[0])
                detections.append(result.names.get(cls_id, f"class_{cls_id}"))

        unique = sorted(set(detections))
        self._logger.info("Detections for %s: %s", image_path, unique)
        return unique

    def summarize_detections(self, detections: Sequence[str], llm_manager) -> str:
        """Use the LLM to verbalize detection results."""
        if not detections:
            return "I could not detect any objects in the scene."

        prompt = (
            "You are summarizing visual detections for a user. "
            "Describe the scene in one or two sentences, mentioning each object.\n"
            f"Detected labels: {', '.join(detections)}"
        )
        summary = llm_manager.generate_response(prompt, history=[])
        self._logger.debug("Detection summary: %s", summary)
        return summary

