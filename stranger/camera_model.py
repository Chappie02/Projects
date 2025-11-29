"""
Camera and Object Detection Module
Handles Picamera2 capture and YOLO model inference
"""

import sys
import os
import logging
from pathlib import Path
from typing import List, Optional, Tuple

# Critical: Picamera2 doesn't work in venv, add system path
sys.path.append("/usr/lib/python3/dist-packages")

try:
    from picamera2 import Picamera2
    from picamera2.encoders import JpegEncoder
    from picamera2.outputs import FileOutput
except ImportError as e:
    logging.warning(f"Picamera2 import failed: {e}")

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


class CameraModel:
    """Manages camera capture and YOLO object detection"""
    
    def __init__(self, model_path: str = "object_models/yolo_model.onnx", 
                 captures_dir: str = "/home/pi/Object_Captures"):
        """
        Initialize camera and YOLO model
        
        Args:
            model_path: Path to YOLO model file
            captures_dir: Directory to save captured images
        """
        self.camera: Optional[Picamera2] = None
        self.model_path = model_path
        self.captures_dir = Path(captures_dir)
        self.yolo_model = None
        
        # Create captures directory if it doesn't exist
        self.captures_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Captures directory: {self.captures_dir}")
        
        try:
            self._setup_camera()
            self._load_yolo_model()
            logger.info("CameraModel initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing CameraModel: {e}")
            raise
    
    def _setup_camera(self):
        """Initialize Picamera2"""
        try:
            self.camera = Picamera2()
            
            # Configure camera for still capture
            config = self.camera.create_still_configuration(
                main={"size": (1920, 1080)},  # Full HD
                lores={"size": (640, 480)}    # Lower resolution for preview
            )
            self.camera.configure(config)
            self.camera.start()
            
            # Give camera time to initialize
            import time
            time.sleep(2)
            
            logger.info("Camera initialized and started")
        except Exception as e:
            logger.error(f"Camera setup error: {e}")
            raise
    
    def _load_yolo_model(self):
        """Load YOLO model for object detection"""
        try:
            # Try to import onnxruntime for YOLO inference
            try:
                import onnxruntime as ort
                
                if os.path.exists(self.model_path):
                    self.yolo_model = ort.InferenceSession(
                        self.model_path,
                        providers=['CPUExecutionProvider']
                    )
                    logger.info(f"YOLO model loaded from {self.model_path}")
                else:
                    logger.warning(f"YOLO model not found at {self.model_path}")
                    logger.warning("Object detection will use placeholder detection")
            except ImportError:
                logger.warning("onnxruntime not available, using placeholder detection")
                
        except Exception as e:
            logger.error(f"Error loading YOLO model: {e}")
            # Continue without model - will use placeholder
    
    def capture_image(self) -> Optional[str]:
        """
        Capture a single image and save it
        
        Returns:
            Path to saved image file, or None if capture failed
        """
        if not self.camera:
            logger.error("Camera not initialized")
            return None
        
        try:
            # Capture image
            image_array = self.camera.capture_array()
            
            # Convert to PIL Image
            image = Image.fromarray(image_array)
            
            # Generate filename with timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"capture_{timestamp}.jpg"
            filepath = self.captures_dir / filename
            
            # Save image
            image.save(filepath, "JPEG", quality=95)
            logger.info(f"Image saved to {filepath}")
            
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error capturing image: {e}")
            return None
    
    def detect_objects(self, image_path: str) -> List[str]:
        """
        Run YOLO inference on captured image
        
        Args:
            image_path: Path to image file
            
        Returns:
            List of detected class names
        """
        detected_classes = []
        
        try:
            if self.yolo_model:
                # Real YOLO inference
                detected_classes = self._run_yolo_inference(image_path)
            else:
                # Placeholder detection for testing
                detected_classes = self._placeholder_detection(image_path)
            
            logger.info(f"Detected objects: {detected_classes}")
            return detected_classes
            
        except Exception as e:
            logger.error(f"Error in object detection: {e}")
            return []
    
    def _run_yolo_inference(self, image_path: str) -> List[str]:
        """Run actual YOLO model inference"""
        try:
            import onnxruntime as ort
            import cv2
            
            # Load and preprocess image
            image = cv2.imread(image_path)
            if image is None:
                logger.error(f"Could not load image: {image_path}")
                return []
            
            # Resize to model input size (typically 640x640 for YOLO)
            input_size = (640, 640)
            resized = cv2.resize(image, input_size)
            
            # Normalize and convert to RGB
            input_image = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
            input_image = input_image.astype(np.float32) / 255.0
            
            # Transpose to NCHW format
            input_image = np.transpose(input_image, (2, 0, 1))
            input_batch = np.expand_dims(input_image, axis=0)
            
            # Run inference
            input_name = self.yolo_model.get_inputs()[0].name
            outputs = self.yolo_model.run(None, {input_name: input_batch})
            
            # Parse YOLO outputs (simplified - adjust based on your model)
            # This is a placeholder - actual parsing depends on YOLO version
            # For now, return placeholder classes
            detected_classes = self._parse_yolo_outputs(outputs)
            
            return detected_classes
            
        except Exception as e:
            logger.error(f"YOLO inference error: {e}")
            return []
    
    def _parse_yolo_outputs(self, outputs) -> List[str]:
        """
        Parse YOLO model outputs to extract class names
        
        NOTE: This is a placeholder. You need to implement based on your specific YOLO model.
        Common YOLO classes include: person, bicycle, car, motorcycle, etc.
        """
        # Placeholder implementation
        # In real implementation, you would:
        # 1. Apply NMS (Non-Maximum Suppression)
        # 2. Filter by confidence threshold
        # 3. Map class indices to names using COCO or custom class list
        
        # Example COCO class names (80 classes)
        coco_classes = [
            'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck',
            'boat', 'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench',
            'bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra',
            'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee',
            'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove',
            'skateboard', 'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup',
            'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange',
            'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch',
            'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse',
            'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink',
            'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier',
            'toothbrush'
        ]
        
        # For now, return a placeholder
        # Replace this with actual parsing logic
        return ['person', 'laptop']  # Placeholder
    
    def _placeholder_detection(self, image_path: str) -> List[str]:
        """Placeholder detection when YOLO model is not available"""
        logger.info("Using placeholder detection")
        # Return some example detections for testing
        return ['person', 'laptop', 'bottle']
    
    def cleanup(self):
        """Clean up camera resources"""
        try:
            if self.camera:
                self.camera.stop()
                self.camera.close()
            logger.info("Camera cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up camera: {e}")

