import sys
import time
import os

# --- CRITICAL: Picamera2 Import Fix ---
sys.path.append("/usr/lib/python3/dist-packages")
try:
    import picamera2
except ImportError:
    # print("Warning: picamera2 not found. Ensure you are on a Pi with camera enabled.")
    picamera2 = None

from ultralytics import YOLO
from app.core import config
from app.core.logger import setup_logger

logger = setup_logger(__name__)

class VisionEngine:
    def __init__(self):
        self.camera = None
        self.model = None
        self._camera_config = None
        if not picamera2:
            logger.warning("Picamera2 not found. Vision features will be limited.")

    def _init_camera(self):
        if self.camera is None and picamera2:
            try:
                self.camera = picamera2.Picamera2()
                self._camera_config = self.camera.create_preview_configuration(main={"size": config.CAMERA_RESOLUTION, "format": "RGB888"})
                self.camera.configure(self._camera_config)
                self.camera.start()
                logger.info("Camera initialized.")
            except Exception as e:
                logger.error(f"Camera init failed: {e}")

    def _init_model(self):
        if self.model is None:
            logger.info("Loading YOLO model...")
            # Lazy load YOLO
            try:
                self.model = YOLO(str(config.YOLO_MODEL_PATH))
                logger.info("YOLO model loaded.")
            except Exception as e:
                logger.error(f"Failed to load YOLO model: {e}")

    def capture_and_analyze(self):
        """Captures an image and runs object detection."""
        self._init_camera()
        self._init_model()

        if not self.camera or not self.model:
            return "Vision system unavailable."

        try:
            # Capture array
            # Picamera2 capture_array returns a numpy array
            image = self.camera.capture_array()
            
            # Run Inference
            results = self.model(image)
            
            # Process results
            detections = []
            for result in results:
                for box in result.boxes:
                    class_id = int(box.cls[0])
                    class_name = self.model.names[class_id]
                    detections.append(class_name)
            
            if detections:
                # Count occurrences
                counts = {}
                for det in detections:
                    counts[det] = counts.get(det, 0) + 1
                
                desc_parts = [f"{count} {name}" + ("s" if count > 1 else "") for name, count in counts.items()]
                description = "I see " + ", ".join(desc_parts) + "."
            else:
                description = "I don't see any recognizable objects."
                
            return description

        except Exception as e:
            logger.error(f"Vision Error: {e}")
            return "Error analyzing image."

    def cleanup(self):
        if self.camera:
            try:
                self.camera.stop()
                self.camera.close()
                self.camera = None
                logger.info("Camera closed.")
            except Exception as e:
                logger.error(f"Error closing camera: {e}")
