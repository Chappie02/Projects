"""
Vision module for camera capture and YOLO object detection
Handles picamera2 initialization and YOLO inference
"""

import sys
sys.path.append("/usr/lib/python3/dist-packages")

import picamera2
import numpy as np
from ultralytics import YOLO
import cv2
import config
import os


class VisionSystem:
    """Manages camera capture and YOLO object detection"""
    
    def __init__(self):
        """Initialize YOLO model (camera initialized on-demand)"""
        self.camera = None
        self.yolo_model = None
        self._init_yolo()
    
    def _init_yolo(self):
        """Initialize YOLO model"""
        try:
            print("Loading YOLO model...")
            self.yolo_model = YOLO(config.YOLO_MODEL)
            print("YOLO model loaded successfully")
        except Exception as e:
            print(f"Error loading YOLO model: {e}")
            raise
    
    def _init_camera(self):
        """Initialize picamera2 (called on-demand)"""
        if self.camera is None:
            try:
                print("Initializing camera...")
                self.camera = picamera2.Picamera2()
                
                # Configure camera
                camera_config = self.camera.create_still_configuration(
                    main={"size": config.CAMERA_RESOLUTION}
                )
                self.camera.configure(camera_config)
                self.camera.start()
                
                # Allow camera to stabilize
                import time
                time.sleep(2)
                print("Camera initialized successfully")
            except Exception as e:
                print(f"Error initializing camera: {e}")
                raise
    
    def _release_camera(self):
        """Release camera resources"""
        if self.camera:
            try:
                self.camera.stop()
                self.camera.close()
                self.camera = None
                print("Camera released")
            except Exception as e:
                print(f"Error releasing camera: {e}")
    
    def capture_image(self):
        """
        Capture a single image from the camera
        
        Returns:
            numpy.ndarray: Image array in RGB format
        """
        self._init_camera()
        
        try:
            # Capture image (picamera2 returns RGB format by default)
            image = self.camera.capture_array()
            
            # Ensure RGB format (picamera2 should already be RGB, but verify)
            if len(image.shape) == 3 and image.shape[2] == 3:
                # picamera2 returns RGB, but verify and ensure correct format
                # YOLO expects RGB format
                pass  # Already in correct format
            
            return image
        except Exception as e:
            print(f"Error capturing image: {e}")
            raise
        finally:
            self._release_camera()
    
    def detect_objects(self, image):
        """
        Run YOLO object detection on an image
        
        Args:
            image: numpy array image in RGB format
            
        Returns:
            list: List of detected objects with labels and confidence scores
        """
        if self.yolo_model is None:
            raise RuntimeError("YOLO model not initialized")
        
        try:
            # Run YOLO inference
            results = self.yolo_model(image, 
                                     conf=config.YOLO_CONFIDENCE_THRESHOLD,
                                     iou=config.YOLO_IOU_THRESHOLD,
                                     verbose=False)
            
            detections = []
            
            # Extract detections from results
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        # Get class ID and confidence
                        class_id = int(box.cls[0])
                        confidence = float(box.conf[0])
                        class_name = self.yolo_model.names[class_id]
                        
                        detections.append({
                            'label': class_name,
                            'confidence': confidence,
                            'class_id': class_id
                        })
            
            return detections
        except Exception as e:
            print(f"Error running object detection: {e}")
            raise
    
    def process_vision_query(self):
        """
        Complete vision processing pipeline:
        1. Capture image
        2. Run object detection
        3. Return detection results
        
        Returns:
            list: List of detected objects
        """
        try:
            print("Capturing image...")
            image = self.capture_image()
            
            print("Running object detection...")
            detections = self.detect_objects(image)
            
            return detections
        except Exception as e:
            print(f"Error in vision processing: {e}")
            return []
    
    def format_detections_for_llm(self, detections):
        """
        Format detection results as a string for LLM input
        
        Args:
            detections: List of detection dictionaries
            
        Returns:
            str: Formatted string describing detected objects
        """
        if not detections:
            return "No objects detected in the image."
        
        # Group by label and count
        object_counts = {}
        for det in detections:
            label = det['label']
            if label not in object_counts:
                object_counts[label] = 0
            object_counts[label] += 1
        
        # Format as natural language
        descriptions = []
        for label, count in object_counts.items():
            if count == 1:
                descriptions.append(f"a {label}")
            else:
                descriptions.append(f"{count} {label}s")
        
        if len(descriptions) == 1:
            return f"I can see {descriptions[0]} in the image."
        else:
            return f"I can see {', '.join(descriptions[:-1])}, and {descriptions[-1]} in the image."
    
    def cleanup(self):
        """Cleanup resources"""
        self._release_camera()

