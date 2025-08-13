"""
Object Detection for Raspberry Pi 5 AI Assistant
Uses YOLOv8 for real-time object detection
"""

import cv2
import numpy as np
import time
from typing import List, Tuple, Dict, Optional
import logging
from ultralytics import YOLO
from utils import handle_error, print_status, save_detection_log

logger = logging.getLogger(__name__)

class ObjectDetector:
    """YOLOv8-based object detector optimized for Raspberry Pi 5"""
    
    def __init__(self, model_size: str = "n", confidence_threshold: float = 0.5, 
                 nms_threshold: float = 0.4, max_detections: int = 10):
        self.model_size = model_size
        self.confidence_threshold = confidence_threshold
        self.nms_threshold = nms_threshold
        self.max_detections = max_detections
        self.model = None
        self.class_names = []
        self.is_initialized = False
        
    def initialize_model(self) -> bool:
        """Initialize YOLOv8 model"""
        try:
            print_status("Loading YOLOv8 model...", "info")
            
            # Load YOLOv8 model (will download if not present)
            model_name = f"yolov8{self.model_size}.pt"
            self.model = YOLO(model_name)
            
            # Get class names
            self.class_names = self.model.names
            
            print_status(f"YOLOv8{self.model_size.upper()} model loaded successfully", "success")
            print_status(f"Available classes: {len(self.class_names)}", "info")
            
            self.is_initialized = True
            return True
            
        except Exception as e:
            handle_error(e, "initialize_model")
            return False
    
    def detect_objects(self, frame: np.ndarray) -> List[Dict]:
        """Detect objects in a frame"""
        if not self.is_initialized:
            if not self.initialize_model():
                return []
        
        try:
            # Run inference
            results = self.model(frame, conf=self.confidence_threshold, 
                               iou=self.nms_threshold, max_det=self.max_detections)
            
            detections = []
            
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        # Get detection info
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        confidence = float(box.conf[0].cpu().numpy())
                        class_id = int(box.cls[0].cpu().numpy())
                        class_name = self.class_names[class_id]
                        
                        detection = {
                            "bbox": [int(x1), int(y1), int(x2), int(y2)],
                            "confidence": confidence,
                            "class_id": class_id,
                            "class_name": class_name,
                            "center": [int((x1 + x2) / 2), int((y1 + y2) / 2)]
                        }
                        
                        detections.append(detection)
            
            return detections
            
        except Exception as e:
            handle_error(e, "detect_objects")
            return []
    
    def draw_detections(self, frame: np.ndarray, detections: List[Dict]) -> np.ndarray:
        """Draw detection boxes and labels on frame"""
        annotated_frame = frame.copy()
        
        for detection in detections:
            x1, y1, x2, y2 = detection["bbox"]
            class_name = detection["class_name"]
            confidence = detection["confidence"]
            
            # Choose color based on confidence
            if confidence > 0.8:
                color = (0, 255, 0)  # Green for high confidence
            elif confidence > 0.6:
                color = (0, 255, 255)  # Yellow for medium confidence
            else:
                color = (0, 0, 255)  # Red for low confidence
            
            # Draw bounding box
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
            
            # Create label
            label = f"{class_name}: {confidence:.2f}"
            
            # Get label size
            (label_width, label_height), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            
            # Draw label background
            cv2.rectangle(annotated_frame, (x1, y1 - label_height - 10), 
                         (x1 + label_width, y1), color, -1)
            
            # Draw label text
            cv2.putText(annotated_frame, label, (x1, y1 - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return annotated_frame
    
    def get_unique_objects(self, detections: List[Dict]) -> List[str]:
        """Get unique object names from detections"""
        unique_objects = []
        seen_objects = set()
        
        for detection in detections:
            class_name = detection["class_name"]
            if class_name not in seen_objects:
                unique_objects.append(class_name)
                seen_objects.add(class_name)
        
        return unique_objects
    
    def filter_detections_by_confidence(self, detections: List[Dict], 
                                      min_confidence: float = 0.6) -> List[Dict]:
        """Filter detections by confidence threshold"""
        return [det for det in detections if det["confidence"] >= min_confidence]
    
    def get_detection_summary(self, detections: List[Dict]) -> Dict:
        """Get summary statistics of detections"""
        if not detections:
            return {"count": 0, "objects": [], "avg_confidence": 0.0}
        
        object_counts = {}
        total_confidence = 0.0
        
        for detection in detections:
            class_name = detection["class_name"]
            confidence = detection["confidence"]
            
            object_counts[class_name] = object_counts.get(class_name, 0) + 1
            total_confidence += confidence
        
        return {
            "count": len(detections),
            "objects": object_counts,
            "avg_confidence": total_confidence / len(detections),
            "unique_objects": list(object_counts.keys())
        }

class DetectionProcessor:
    """Process detection results and manage detection history"""
    
    def __init__(self, detector: ObjectDetector, history_size: int = 10):
        self.detector = detector
        self.history_size = history_size
        self.detection_history = []
        self.last_detection_time = 0
        self.detection_cooldown = 2.0  # Seconds between detections
        
    def process_frame(self, frame: np.ndarray) -> Tuple[List[Dict], np.ndarray]:
        """Process a frame and return detections and annotated frame"""
        # Run detection
        detections = self.detector.detect_objects(frame)
        
        # Filter by confidence
        filtered_detections = self.detector.filter_detections_by_confidence(detections)
        
        # Draw detections on frame
        annotated_frame = self.detector.draw_detections(frame, filtered_detections)
        
        return filtered_detections, annotated_frame
    
    def should_analyze_detections(self, detections: List[Dict]) -> bool:
        """Check if detections should be analyzed (avoid spam)"""
        current_time = time.time()
        
        if not detections:
            return False
        
        # Check cooldown
        if current_time - self.last_detection_time < self.detection_cooldown:
            return False
        
        # Check if we have new objects
        current_objects = set(self.detector.get_unique_objects(detections))
        
        if not self.detection_history:
            self.last_detection_time = current_time
            return True
        
        # Check if objects are different from last detection
        last_objects = set()
        for hist in self.detection_history[-3:]:  # Check last 3 detections
            last_objects.update(hist.get("objects", []))
        
        if current_objects != last_objects:
            self.last_detection_time = current_time
            return True
        
        return False
    
    def add_to_history(self, detections: List[Dict]) -> None:
        """Add detection result to history"""
        unique_objects = self.detector.get_unique_objects(detections)
        
        history_entry = {
            "timestamp": time.time(),
            "detections": detections,
            "objects": unique_objects,
            "count": len(detections)
        }
        
        self.detection_history.append(history_entry)
        
        # Keep history size manageable
        if len(self.detection_history) > self.history_size:
            self.detection_history = self.detection_history[-self.history_size:]
        
        # Save to log file
        save_detection_log(unique_objects, time.time())
    
    def get_recent_detections(self, minutes: int = 5) -> List[Dict]:
        """Get detections from the last N minutes"""
        cutoff_time = time.time() - (minutes * 60)
        return [entry for entry in self.detection_history 
                if entry["timestamp"] > cutoff_time]
    
    def get_detection_stats(self) -> Dict:
        """Get detection statistics"""
        if not self.detection_history:
            return {"total_detections": 0, "unique_objects": [], "avg_objects_per_frame": 0}
        
        total_detections = sum(entry["count"] for entry in self.detection_history)
        all_objects = set()
        for entry in self.detection_history:
            all_objects.update(entry["objects"])
        
        return {
            "total_detections": total_detections,
            "unique_objects": list(all_objects),
            "avg_objects_per_frame": total_detections / len(self.detection_history),
            "history_size": len(self.detection_history)
        }

def create_object_detector(model_size: str = "n", **kwargs) -> ObjectDetector:
    """Factory function to create object detector"""
    return ObjectDetector(model_size=model_size, **kwargs)

def create_detection_processor(detector: ObjectDetector, **kwargs) -> DetectionProcessor:
    """Factory function to create detection processor"""
    return DetectionProcessor(detector, **kwargs)
