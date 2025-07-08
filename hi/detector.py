from ultralytics import YOLO
from picamera2 import Picamera2
import cv2
import numpy as np

class ObjectDetector:
    def __init__(self, model_path):
        """Initialize the YOLOv8 model and Pi Camera."""
        self.model = YOLO(model_path)
        self.camera = Picamera2()
        self.camera.configure(self.camera.create_still_configuration())
        self.camera.start()

    def detect_objects(self):
        """Capture an image and perform object detection."""
        try:
            # Capture image
            image = self.camera.capture_array()
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

            # Run YOLOv8 inference
            results = self.model(image)

            # Process results
            detected_objects = []
            for result in results:
                for box in result.boxes:
                    class_id = int(box.cls)
                    label = self.model.names[class_id]
                    confidence = box.conf.item()
                    detected_objects.append(f"{label} ({confidence:.2f})")

            return detected_objects if detected_objects else ["No objects detected"]
        except Exception as e:
            return [f"Detection Error: {str(e)}"]
        finally:
            # Optionally, stop the camera to save resources
            self.camera.stop()

    def __del__(self):
        """Clean up camera resources."""
        self.camera.close()