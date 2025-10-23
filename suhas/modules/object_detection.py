"""
Object Detection Mode for the Raspberry Pi AI Assistant.
Uses YOLOv8 for real-time object detection through Pi camera.
"""

import os
import sys
import logging
import time
import threading
import queue
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path
import cv2
import numpy as np
from datetime import datetime

try:
    from ultralytics import YOLO
except ImportError:
    print("Warning: ultralytics not installed. Object detection mode will not work.")
    YOLO = None

try:
    from picamera2 import Picamera2
    from libcamera import controls
except ImportError:
    print("Warning: picamera2 not installed. Using OpenCV camera fallback.")
    Picamera2 = None
    controls = None

from .utils import ConfigManager, SystemMonitor, ProcessManager


class ObjectDetectionMode:
    """
    Object detection mode implementation using YOLOv8 and Pi camera.
    Provides real-time object detection and classification.
    """
    
    def __init__(self, config_manager: ConfigManager):
        """
        Initialize object detection mode.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        self.system_monitor = SystemMonitor()
        self.process_manager = ProcessManager()
        
        # Initialize components
        self.yolo_model = None
        self.camera = None
        self.is_running = False
        self.detection_thread = None
        self.frame_queue = queue.Queue(maxsize=5)
        self.detection_results = []
        
        # Load configuration
        self.model_path = self.config_manager.get("yolo.model_path", "yolo/yolov8n.pt")
        self.confidence_threshold = self.config_manager.get("yolo.confidence_threshold", 0.5)
        self.iou_threshold = self.config_manager.get("yolo.iou_threshold", 0.45)
        
        # Camera configuration
        self.resolution = self.config_manager.get("camera.resolution", [640, 480])
        self.fps = self.config_manager.get("camera.fps", 30)
        self.rotation = self.config_manager.get("camera.rotation", 0)
        
        self.logger.info("Object detection mode initialized")
    
    def initialize(self) -> bool:
        """
        Initialize the object detection components.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if ultralytics is available
            if YOLO is None:
                self.logger.error("ultralytics not available")
                return False
            
            # Initialize YOLO model
            self.logger.info(f"Loading YOLO model: {self.model_path}")
            
            # Check if model file exists, if not download it
            if not Path(self.model_path).exists():
                self.logger.info("Model file not found, downloading YOLOv8n...")
                Path(self.model_path).parent.mkdir(parents=True, exist_ok=True)
            
            self.yolo_model = YOLO(self.model_path)
            self.logger.info("YOLO model loaded successfully")
            
            # Initialize camera
            if not self._initialize_camera():
                return False
            
            self.logger.info("Object detection components initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize object detection mode: {e}")
            return False
    
    def _initialize_camera(self) -> bool:
        """
        Initialize camera (Pi camera or USB camera fallback).
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Try Pi camera first
            if Picamera2 is not None:
                self.logger.info("Initializing Pi camera...")
                self.camera = Picamera2()
                
                # Configure camera
                config = self.camera.create_preview_configuration(
                    main={"size": tuple(self.resolution), "format": "RGB888"}
                )
                self.camera.configure(config)
                
                # Set camera controls
                if controls is not None:
                    self.camera.set_controls({
                        "ExposureTime": 10000,  # 10ms
                        "AnalogueGain": 1.0,
                        "ColourGains": (1.0, 1.0)
                    })
                
                self.camera.start()
                time.sleep(2)  # Allow camera to warm up
                
                self.logger.info("Pi camera initialized successfully")
                return True
            
            else:
                # Fallback to OpenCV camera
                self.logger.info("Pi camera not available, using OpenCV camera...")
                self.camera = cv2.VideoCapture(0)
                
                if not self.camera.isOpened():
                    self.logger.error("Could not open camera")
                    return False
                
                # Set camera properties
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
                self.camera.set(cv2.CAP_PROP_FPS, self.fps)
                
                self.logger.info("OpenCV camera initialized successfully")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to initialize camera: {e}")
            return False
    
    def start(self) -> bool:
        """
        Start the object detection mode.
        
        Returns:
            True if successful, False otherwise
        """
        if self.is_running:
            self.logger.warning("Object detection mode is already running")
            return True
        
        if not self.initialize():
            return False
        
        self.is_running = True
        self.detection_results = []
        
        # Start detection thread
        self.detection_thread = threading.Thread(target=self._detection_loop, daemon=True)
        self.detection_thread.start()
        
        self.logger.info("Object detection mode started")
        self._print_welcome_message()
        
        return True
    
    def stop(self) -> None:
        """Stop the object detection mode and cleanup resources."""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # Wait for detection thread to finish
        if self.detection_thread and self.detection_thread.is_alive():
            self.detection_thread.join(timeout=2.0)
        
        # Cleanup camera
        if self.camera:
            if Picamera2 is not None and isinstance(self.camera, Picamera2):
                self.camera.stop()
                self.camera.close()
            elif hasattr(self.camera, 'release'):
                self.camera.release()
            self.camera = None
        
        # Clear detection results
        self.detection_results = []
        
        self.logger.info("Object detection mode stopped")
    
    def _print_welcome_message(self) -> None:
        """Print welcome message and instructions."""
        print("\n" + "="*60)
        print("🔍 AI Assistant - Object Detection Mode")
        print("="*60)
        print("Real-time object detection using YOLOv8.")
        print("Objects will be detected and displayed with confidence scores.")
        print("\nCommands:")
        print("  /help     - Show this help message")
        print("  /stats    - Show detection statistics")
        print("  /save     - Save current frame with detections")
        print("  /clear    - Clear detection history")
        print("  /exit     - Exit object detection mode")
        print("  /quit     - Exit object detection mode")
        print("-"*60)
        print("Starting detection... Press Ctrl+C to stop")
    
    def _capture_frame(self) -> Optional[np.ndarray]:
        """
        Capture a frame from the camera.
        
        Returns:
            Captured frame as numpy array, or None if failed
        """
        try:
            if Picamera2 is not None and isinstance(self.camera, Picamera2):
                # Pi camera
                frame = self.camera.capture_array()
                if self.rotation != 0:
                    frame = cv2.rotate(frame, self.rotation)
                return frame
            else:
                # OpenCV camera
                ret, frame = self.camera.read()
                if ret:
                    return frame
                return None
                
        except Exception as e:
            self.logger.error(f"Error capturing frame: {e}")
            return None
    
    def _detect_objects(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detect objects in a frame using YOLO.
        
        Args:
            frame: Input frame
            
        Returns:
            List of detection results
        """
        try:
            # Run YOLO inference
            results = self.yolo_model(
                frame,
                conf=self.confidence_threshold,
                iou=self.iou_threshold,
                verbose=False
            )
            
            detections = []
            if results and len(results) > 0:
                result = results[0]
                
                if result.boxes is not None:
                    boxes = result.boxes.xyxy.cpu().numpy()
                    confidences = result.boxes.conf.cpu().numpy()
                    class_ids = result.boxes.cls.cpu().numpy().astype(int)
                    
                    for i, (box, conf, class_id) in enumerate(zip(boxes, confidences, class_ids)):
                        detection = {
                            'class_id': int(class_id),
                            'class_name': self.yolo_model.names[class_id],
                            'confidence': float(conf),
                            'bbox': box.tolist(),
                            'timestamp': time.time()
                        }
                        detections.append(detection)
            
            return detections
            
        except Exception as e:
            self.logger.error(f"Error detecting objects: {e}")
            return []
    
    def _draw_detections(self, frame: np.ndarray, detections: List[Dict[str, Any]]) -> np.ndarray:
        """
        Draw detection boxes and labels on frame.
        
        Args:
            frame: Input frame
            detections: List of detection results
            
        Returns:
            Frame with drawn detections
        """
        try:
            annotated_frame = frame.copy()
            
            for detection in detections:
                bbox = detection['bbox']
                class_name = detection['class_name']
                confidence = detection['confidence']
                
                # Draw bounding box
                x1, y1, x2, y2 = map(int, bbox)
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                
                # Draw label
                label = f"{class_name}: {confidence:.2f}"
                label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
                cv2.rectangle(annotated_frame, (x1, y1 - label_size[1] - 10), 
                            (x1 + label_size[0], y1), (0, 255, 0), -1)
                cv2.putText(annotated_frame, label, (x1, y1 - 5), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
            
            return annotated_frame
            
        except Exception as e:
            self.logger.error(f"Error drawing detections: {e}")
            return frame
    
    def _detection_loop(self) -> None:
        """Main detection loop running in separate thread."""
        while self.is_running:
            try:
                # Capture frame
                frame = self._capture_frame()
                if frame is None:
                    time.sleep(0.1)
                    continue
                
                # Detect objects
                detections = self._detect_objects(frame)
                
                # Update detection results
                if detections:
                    self.detection_results.extend(detections)
                    # Keep only recent detections (last 100)
                    if len(self.detection_results) > 100:
                        self.detection_results = self.detection_results[-100:]
                
                # Draw detections on frame
                annotated_frame = self._draw_detections(frame, detections)
                
                # Put frame in queue for display
                try:
                    self.frame_queue.put_nowait(annotated_frame)
                except queue.Full:
                    # Remove oldest frame if queue is full
                    try:
                        self.frame_queue.get_nowait()
                        self.frame_queue.put_nowait(annotated_frame)
                    except queue.Empty:
                        pass
                
                # Print detections to console
                if detections:
                    self._print_detections(detections)
                
                time.sleep(0.1)  # Small delay to prevent overwhelming
                
            except Exception as e:
                self.logger.error(f"Error in detection loop: {e}")
                time.sleep(1.0)
    
    def _print_detections(self, detections: List[Dict[str, Any]]) -> None:
        """Print detection results to console."""
        if not detections:
            return
        
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Detected {len(detections)} object(s):")
        for detection in detections:
            print(f"  - {detection['class_name']}: {detection['confidence']:.2f}")
    
    def _check_system_health(self) -> bool:
        """Check system health before processing."""
        health = self.system_monitor.check_system_health()
        
        # Check memory usage
        if health['memory']['percent'] > self.config_manager.get("system.max_memory_usage", 80):
            self.logger.warning(f"High memory usage: {health['memory']['percent']:.1f}%")
            return False
        
        # Check temperature
        if health['temperature'] and health['temperature'] > self.config_manager.get("system.max_temperature", 70):
            self.logger.warning(f"High temperature: {health['temperature']:.1f}°C")
            return False
        
        return True
    
    def process_command(self, command: str) -> str:
        """
        Process user command.
        
        Args:
            command: Command string
            
        Returns:
            Command response
        """
        command = command.lower().strip()
        
        if command == '/help':
            return """Available commands:
/help     - Show this help message
/stats    - Show detection statistics
/save     - Save current frame with detections
/clear    - Clear detection history
/exit     - Exit object detection mode
/quit     - Exit object detection mode"""
        
        elif command == '/stats':
            return self._get_stats()
        
        elif command == '/save':
            return self._save_current_frame()
        
        elif command == '/clear':
            self.detection_results = []
            return "Detection history cleared."
        
        elif command in ['/exit', '/quit']:
            return "EXIT_DETECTION_MODE"
        
        else:
            return f"Unknown command: {command}. Type /help for available commands."
    
    def _get_stats(self) -> str:
        """Get detection statistics."""
        try:
            # System stats
            health = self.system_monitor.check_system_health()
            system_stats = f"""System Statistics:
CPU Usage: {health['cpu_usage']:.1f}%
Memory Usage: {health['memory']['percent']:.1f}% ({health['memory']['used']:.1f}GB / {health['memory']['total']:.1f}GB)
Temperature: {health['temperature']:.1f}°C if available

"""
            
            # Detection stats
            if self.detection_results:
                # Count objects by class
                class_counts = {}
                for detection in self.detection_results:
                    class_name = detection['class_name']
                    class_counts[class_name] = class_counts.get(class_name, 0) + 1
                
                detection_stats = f"""Detection Statistics:
Total Detections: {len(self.detection_results)}
Object Classes: {len(class_counts)}
"""
                
                # Top detected objects
                sorted_classes = sorted(class_counts.items(), key=lambda x: x[1], reverse=True)
                detection_stats += "\nTop Detected Objects:\n"
                for class_name, count in sorted_classes[:5]:
                    detection_stats += f"  - {class_name}: {count}\n"
            else:
                detection_stats = "Detection Statistics:\nNo detections yet.\n"
            
            return system_stats + detection_stats
            
        except Exception as e:
            self.logger.error(f"Error getting stats: {e}")
            return "Error retrieving statistics."
    
    def _save_current_frame(self) -> str:
        """Save current frame with detections."""
        try:
            if self.frame_queue.empty():
                return "No frame available to save."
            
            # Get latest frame
            frame = self.frame_queue.get()
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"captured_images/detection_{timestamp}.jpg"
            
            # Ensure directory exists
            Path("captured_images").mkdir(parents=True, exist_ok=True)
            
            # Save frame
            cv2.imwrite(filename, frame)
            
            return f"Frame saved as {filename}"
            
        except Exception as e:
            self.logger.error(f"Error saving frame: {e}")
            return "Error saving frame."
    
    def run_interactive(self) -> None:
        """Run interactive object detection loop."""
        if not self.start():
            print("Failed to start object detection mode")
            return
        
        try:
            while self.is_running:
                try:
                    # Get user input (non-blocking)
                    import select
                    import sys
                    
                    if select.select([sys.stdin], [], [], 0.1)[0]:
                        user_input = input().strip()
                        
                        if user_input:
                            response = self.process_command(user_input)
                            
                            if response == "EXIT_DETECTION_MODE":
                                break
                            else:
                                print(response)
                    
                except KeyboardInterrupt:
                    print("\n\nObject detection interrupted by user")
                    break
                except Exception as e:
                    self.logger.error(f"Error in detection loop: {e}")
                    time.sleep(1.0)
        
        finally:
            self.stop()
            print("\nObject detection mode ended.")
    
    def get_latest_detections(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get latest detection results."""
        return self.detection_results[-limit:] if self.detection_results else []
    
    def get_detection_summary(self) -> Dict[str, Any]:
        """Get summary of detection results."""
        if not self.detection_results:
            return {"total_detections": 0, "classes": {}}
        
        class_counts = {}
        for detection in self.detection_results:
            class_name = detection['class_name']
            class_counts[class_name] = class_counts.get(class_name, 0) + 1
        
        return {
            "total_detections": len(self.detection_results),
            "classes": class_counts,
            "latest_detection": self.detection_results[-1] if self.detection_results else None
        }
