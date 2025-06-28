import cv2
import numpy as np
import time
import threading
import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

try:
    from ultralytics import YOLO
except ImportError:
    print("Ultralytics not installed. Object detection will be limited.")
    YOLO = None

from config import Config

@dataclass
class Detection:
    label: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # x, y, width, height

class ObjectDetectionModule:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.camera = None
        self.model = None
        self.is_initialized = False
        self.is_detecting = False
        self.current_frame = None
        self.detection_thread = None
        
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize camera and YOLO model"""
        try:
            # Initialize camera
            self.camera = cv2.VideoCapture(Config.CAMERA_INDEX)
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, Config.CAMERA_WIDTH)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, Config.CAMERA_HEIGHT)
            
            if not self.camera.isOpened():
                self.logger.error("Failed to open camera")
                return
            
            self.logger.info("Camera initialized successfully")
            
            # Initialize YOLO model
            if YOLO and os.path.exists(Config.YOLO_MODEL_PATH):
                self.model = YOLO(Config.YOLO_MODEL_PATH)
                self.logger.info("YOLO model loaded successfully")
            else:
                self.logger.warning("YOLO model not found, using fallback detection")
                self.model = None
            
            self.is_initialized = True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize object detection: {e}")
            self.is_initialized = False
    
    def start_detection(self):
        """Start continuous object detection"""
        if not self.is_initialized:
            self.logger.error("Object detection not initialized")
            return False
        
        self.is_detecting = True
        self.detection_thread = threading.Thread(
            target=self._detection_loop,
            daemon=True
        )
        self.detection_thread.start()
        
        self.logger.info("Started object detection")
        return True
    
    def stop_detection(self):
        """Stop continuous object detection"""
        self.is_detecting = False
        if self.detection_thread:
            self.detection_thread.join(timeout=1)
        
        if self.camera:
            self.camera.release()
        
        self.logger.info("Stopped object detection")
    
    def _detection_loop(self):
        """Main detection loop"""
        while self.is_detecting:
            try:
                ret, frame = self.camera.read()
                if not ret:
                    self.logger.warning("Failed to read frame from camera")
                    time.sleep(0.1)
                    continue
                
                self.current_frame = frame
                time.sleep(0.1)  # Reduce CPU usage
                
            except Exception as e:
                self.logger.error(f"Error in detection loop: {e}")
                break
    
    def detect_objects(self, frame: Optional[np.ndarray] = None) -> List[Detection]:
        """Detect objects in a frame"""
        if not self.is_initialized:
            return []
        
        try:
            # Use provided frame or current frame
            if frame is None:
                if self.current_frame is None:
                    return []
                frame = self.current_frame.copy()
            
            if self.model:
                # Use YOLO for detection
                results = self.model(frame, conf=Config.DETECTION_CONFIDENCE)
                detections = []
                
                for result in results:
                    boxes = result.boxes
                    if boxes is not None:
                        for box in boxes:
                            # Get box coordinates
                            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                            
                            # Get confidence and class
                            confidence = float(box.conf[0])
                            class_id = int(box.cls[0])
                            label = result.names[class_id]
                            
                            detections.append(Detection(
                                label=label,
                                confidence=confidence,
                                bbox=(x1, y1, x2 - x1, y2 - y1)
                            ))
                
                return detections
            else:
                # Fallback detection using OpenCV
                return self._fallback_detection(frame)
                
        except Exception as e:
            self.logger.error(f"Error in object detection: {e}")
            return []
    
    def _fallback_detection(self, frame: np.ndarray) -> List[Detection]:
        """Fallback object detection using OpenCV"""
        detections = []
        
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Simple motion detection
            if hasattr(self, '_prev_frame'):
                frame_diff = cv2.absdiff(self._prev_frame, gray)
                _, thresh = cv2.threshold(frame_diff, 25, 255, cv2.THRESH_BINARY)
                
                # Find contours
                contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                for contour in contours:
                    if cv2.contourArea(contour) > 500:  # Filter small contours
                        x, y, w, h = cv2.boundingRect(contour)
                        detections.append(Detection(
                            label="motion",
                            confidence=0.7,
                            bbox=(x, y, w, h)
                        ))
            
            self._prev_frame = gray
            
        except Exception as e:
            self.logger.error(f"Error in fallback detection: {e}")
        
        return detections
    
    def get_detection_summary(self) -> str:
        """Get a text summary of detected objects"""
        if not self.is_initialized or self.current_frame is None:
            return "Camera not available or no frame captured."
        
        detections = self.detect_objects()
        
        if not detections:
            return "I don't see any objects in the camera view."
        
        # Group detections by label
        object_counts = {}
        for detection in detections:
            label = detection.label
            if label in object_counts:
                object_counts[label] += 1
            else:
                object_counts[label] = 1
        
        # Create summary
        summary_parts = []
        for label, count in object_counts.items():
            if count == 1:
                summary_parts.append(f"a {label}")
            else:
                summary_parts.append(f"{count} {label}s")
        
        if len(summary_parts) == 1:
            return f"I can see {summary_parts[0]} in the camera view."
        else:
            return f"I can see {', '.join(summary_parts[:-1])} and {summary_parts[-1]} in the camera view."
    
    def capture_image(self) -> Optional[np.ndarray]:
        """Capture a single image from the camera"""
        if not self.is_initialized or not self.camera:
            return None
        
        try:
            ret, frame = self.camera.read()
            if ret:
                return frame
            else:
                self.logger.warning("Failed to capture image")
                return None
        except Exception as e:
            self.logger.error(f"Error capturing image: {e}")
            return None
    
    def is_available(self) -> bool:
        """Check if object detection is available"""
        return self.is_initialized and self.camera is not None

# Import os at the top level
import os 