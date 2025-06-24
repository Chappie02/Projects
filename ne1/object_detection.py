import cv2
import numpy as np
from ultralytics import YOLO
import logging
from config import Config
import threading
import time

class ObjectDetection:
    def __init__(self):
        self.config = Config()
        self.logger = logging.getLogger(__name__)
        self.camera = None
        self.model = None
        self.is_running = False
        self.current_objects = []
        self.lock = threading.Lock()
        
        # Initialize YOLO model
        self.logger.info("Loading YOLO model...")
        try:
            self.model = YOLO(self.config.OBJECT_DETECTION_MODEL)
            self.logger.info("YOLO model loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load YOLO model: {e}")
            self.model = None
    
    def initialize_camera(self):
        """Initialize the camera"""
        try:
            self.camera = cv2.VideoCapture(self.config.CAMERA_INDEX)
            if not self.camera.isOpened():
                self.logger.error("Failed to open camera")
                return False
            
            # Set camera properties
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.camera.set(cv2.CAP_PROP_FPS, 30)
            
            self.logger.info("Camera initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize camera: {e}")
            return False
    
    def start_detection(self):
        """Start continuous object detection"""
        if not self.camera or not self.model:
            self.logger.error("Camera or model not initialized")
            return False
        
        self.is_running = True
        detection_thread = threading.Thread(target=self._detection_loop)
        detection_thread.daemon = True
        detection_thread.start()
        self.logger.info("Object detection started")
        return True
    
    def stop_detection(self):
        """Stop object detection"""
        self.is_running = False
        if self.camera:
            self.camera.release()
        self.logger.info("Object detection stopped")
    
    def _detection_loop(self):
        """Main detection loop"""
        while self.is_running:
            try:
                ret, frame = self.camera.read()
                if not ret:
                    self.logger.warning("Failed to read frame from camera")
                    time.sleep(0.1)
                    continue
                
                # Run detection
                results = self.model(frame, conf=self.config.CONFIDENCE_THRESHOLD)
                
                # Process results
                detected_objects = []
                for result in results:
                    boxes = result.boxes
                    if boxes is not None:
                        for box in boxes:
                            # Get box coordinates
                            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                            
                            # Get confidence and class
                            confidence = box.conf[0].cpu().numpy()
                            class_id = int(box.cls[0].cpu().numpy())
                            class_name = self.model.names[class_id]
                            
                            detected_objects.append({
                                'name': class_name,
                                'confidence': float(confidence),
                                'bbox': [int(x1), int(y1), int(x2), int(y2)]
                            })
                
                # Update current objects with thread safety
                with self.lock:
                    self.current_objects = detected_objects
                
                # Add small delay to prevent excessive CPU usage
                time.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"Error in detection loop: {e}")
                time.sleep(0.1)
    
    def get_current_objects(self):
        """Get currently detected objects"""
        with self.lock:
            return self.current_objects.copy()
    
    def detect_single_frame(self):
        """Detect objects in a single frame"""
        if not self.camera or not self.model:
            return []
        
        try:
            ret, frame = self.camera.read()
            if not ret:
                return []
            
            results = self.model(frame, conf=self.config.CONFIDENCE_THRESHOLD)
            
            detected_objects = []
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        confidence = box.conf[0].cpu().numpy()
                        class_id = int(box.cls[0].cpu().numpy())
                        class_name = self.model.names[class_id]
                        
                        detected_objects.append({
                            'name': class_name,
                            'confidence': float(confidence)
                        })
            
            return detected_objects
            
        except Exception as e:
            self.logger.error(f"Error in single frame detection: {e}")
            return []
    
    def get_camera_frame(self):
        """Get current camera frame for display"""
        if not self.camera:
            return None
        
        try:
            ret, frame = self.camera.read()
            if ret:
                # Draw bounding boxes on frame
                objects = self.get_current_objects()
                for obj in objects:
                    x1, y1, x2, y2 = obj['bbox']
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, f"{obj['name']} {obj['confidence']:.2f}", 
                              (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                
                return frame
            return None
        except Exception as e:
            self.logger.error(f"Error getting camera frame: {e}")
            return None
    
    def is_initialized(self):
        """Check if object detection is properly initialized"""
        return self.camera is not None and self.model is not None 