"""
Camera Handler for Raspberry Pi 5 AI Assistant
Manages camera operations and frame capture
"""

import cv2
import numpy as np
import time
import threading
from typing import Optional, Tuple, Callable
import logging
from utils import handle_error, print_status

# Optional Picamera2 support (recommended on Raspberry Pi OS Bookworm with libcamera)
try:
    from picamera2 import Picamera2  # type: ignore
    PICAMERA2_AVAILABLE = True
except Exception:
    PICAMERA2_AVAILABLE = False

logger = logging.getLogger(__name__)

class CameraHandler:
    """Handles camera operations for Raspberry Pi"""
    
    def __init__(self, camera_index: int = 0, width: int = 640, height: int = 480, fps: int = 30):
        self.camera_index = camera_index
        self.width = width
        self.height = height
        self.fps = fps
        self.camera = None
        self.is_running = False
        self.current_frame = None
        self.frame_lock = threading.Lock()
        self.capture_thread = None
        
    def initialize_camera(self) -> bool:
        """Initialize the camera"""
        try:
            # Try different camera backends for Raspberry Pi
            backends = [cv2.CAP_V4L2, cv2.CAP_ANY]
            
            for backend in backends:
                self.camera = cv2.VideoCapture(self.camera_index, backend)
                if self.camera.isOpened():
                    break
            
            if not self.camera.isOpened():
                raise Exception("Failed to open camera with any backend")
            
            # Set camera properties
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.camera.set(cv2.CAP_PROP_FPS, self.fps)
            self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize latency
            
            # Verify camera settings
            actual_width = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = int(self.camera.get(cv2.CAP_PROP_FPS))
            
            print_status(f"Camera initialized: {actual_width}x{actual_height} @ {actual_fps}fps", "success")
            
            return True
            
        except Exception as e:
            handle_error(e, "initialize_camera")
            return False
    
    def start_capture(self) -> bool:
        """Start continuous frame capture in a separate thread"""
        if self.camera is None:
            if not self.initialize_camera():
                return False
        
        self.is_running = True
        self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.capture_thread.start()
        
        print_status("Camera capture started", "success")
        return True
    
    def stop_capture(self) -> None:
        """Stop frame capture"""
        self.is_running = False
        if self.capture_thread:
            self.capture_thread.join(timeout=2)
        
        if self.camera:
            self.camera.release()
            self.camera = None
        
        print_status("Camera capture stopped", "info")
    
    def _capture_loop(self) -> None:
        """Continuous frame capture loop"""
        while self.is_running:
            try:
                ret, frame = self.camera.read()
                if ret:
                    with self.frame_lock:
                        self.current_frame = frame.copy()
                else:
                    logger.warning("Failed to capture frame")
                    time.sleep(0.1)
                    
            except Exception as e:
                logger.error(f"Error in capture loop: {e}")
                time.sleep(0.1)
    
    def get_frame(self) -> Optional[np.ndarray]:
        """Get the current frame"""
        with self.frame_lock:
            if self.current_frame is not None:
                return self.current_frame.copy()
        return None
    
    def capture_single_frame(self) -> Optional[np.ndarray]:
        """Capture a single frame (for testing)"""
        if self.camera is None:
            if not self.initialize_camera():
                return None
        
        try:
            ret, frame = self.camera.read()
            if ret:
                return frame
            else:
                logger.error("Failed to capture single frame")
                return None
        except Exception as e:
            handle_error(e, "capture_single_frame")
            return None
    
    def test_camera(self) -> bool:
        """Test camera functionality"""
        try:
            if not self.initialize_camera():
                return False
            
            # Capture a test frame
            frame = self.capture_single_frame()
            if frame is None:
                return False
            
            # Check frame properties
            height, width = frame.shape[:2]
            if width == 0 or height == 0:
                logger.error("Invalid frame dimensions")
                return False
            
            print_status(f"Camera test successful: {width}x{height} frame captured", "success")
            return True
            
        except Exception as e:
            handle_error(e, "test_camera")
            return False
        finally:
            if self.camera:
                self.camera.release()
                self.camera = None
    
    def get_camera_info(self) -> dict:
        """Get camera information"""
        if self.camera is None:
            return {"status": "not_initialized"}
        
        try:
            info = {
                "status": "active" if self.camera.isOpened() else "inactive",
                "width": int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH)),
                "height": int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                "fps": int(self.camera.get(cv2.CAP_PROP_FPS)),
                "backend": self.camera.getBackendName()
            }
            return info
        except Exception as e:
            handle_error(e, "get_camera_info")
            return {"status": "error", "error": str(e)}
    
    def set_resolution(self, width: int, height: int) -> bool:
        """Set camera resolution"""
        if self.camera is None:
            return False
        
        try:
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            
            # Verify the change
            actual_width = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            if abs(actual_width - width) > 10 or abs(actual_height - height) > 10:
                logger.warning(f"Resolution change may not have taken effect. "
                             f"Requested: {width}x{height}, Actual: {actual_width}x{actual_height}")
            
            self.width = actual_width
            self.height = actual_height
            
            print_status(f"Resolution set to {actual_width}x{actual_height}", "success")
            return True
            
        except Exception as e:
            handle_error(e, "set_resolution")
            return False
    
    def __enter__(self):
        """Context manager entry"""
        if not self.initialize_camera():
            raise RuntimeError("Failed to initialize camera")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop_capture()

class Picamera2Handler:
    """Picamera2-based camera handler (preferred on Raspberry Pi 5 with libcamera)"""
    
    def __init__(self, width: int = 640, height: int = 480, fps: int = 30):
        if not PICAMERA2_AVAILABLE:
            raise RuntimeError("Picamera2 not available")
        self.width = width
        self.height = height
        self.fps = fps
        self.picam = None
        self.is_running = False
        self.current_frame = None
        self.frame_lock = threading.Lock()
        self.capture_thread = None
    
    def initialize_camera(self) -> bool:
        try:
            self.picam = Picamera2()
            config = self.picam.create_video_configuration(
                main={"size": (self.width, self.height), "format": "RGB888"},
                controls={"FrameDurationLimits": (int(1e6 / self.fps), int(1e6 / self.fps))}
            )
            self.picam.configure(config)
            self.picam.start()
            time.sleep(0.2)
            print_status(f"Picamera2 initialized: {self.width}x{self.height} @ {self.fps}fps", "success")
            return True
        except Exception as e:
            handle_error(e, "picamera2.initialize_camera")
            return False
    
    def _capture_loop(self) -> None:
        while self.is_running:
            try:
                frame = self.picam.capture_array("main")
                if frame is not None:
                    with self.frame_lock:
                        self.current_frame = frame.copy()
                else:
                    time.sleep(0.01)
            except Exception as e:
                logger.error(f"Error in Picamera2 capture loop: {e}")
                time.sleep(0.05)
    
    def start_capture(self) -> bool:
        if self.picam is None:
            if not self.initialize_camera():
                return False
        self.is_running = True
        self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.capture_thread.start()
        print_status("Picamera2 capture started", "success")
        return True
    
    def stop_capture(self) -> None:
        self.is_running = False
        if self.capture_thread:
            self.capture_thread.join(timeout=2)
        try:
            if self.picam:
                self.picam.stop()
        except Exception:
            pass
        print_status("Picamera2 capture stopped", "info")
    
    def get_frame(self) -> Optional[np.ndarray]:
        with self.frame_lock:
            if self.current_frame is not None:
                return self.current_frame.copy()
        return None
    
    def capture_single_frame(self) -> Optional[np.ndarray]:
        try:
            if self.picam is None:
                if not self.initialize_camera():
                    return None
            frame = self.picam.capture_array("main")
            return frame
        except Exception as e:
            handle_error(e, "picamera2.capture_single_frame")
            return None
    
    def test_camera(self) -> bool:
        try:
            if not self.initialize_camera():
                return False
            frame = self.capture_single_frame()
            if frame is None:
                return False
            h, w = frame.shape[:2]
            if w == 0 or h == 0:
                return False
            print_status(f"Picamera2 test successful: {w}x{h} frame captured", "success")
            return True
        except Exception as e:
            handle_error(e, "picamera2.test_camera")
            return False
        finally:
            try:
                if self.picam:
                    self.picam.stop()
            except Exception:
                pass

class MockCameraHandler:
    """Mock camera handler for testing without hardware"""
    
    def __init__(self, width: int = 640, height: int = 480):
        self.width = width
        self.height = height
        self.is_running = False
        self.current_frame = None
        self.frame_lock = threading.Lock()
        self.capture_thread = None
    
    def initialize_camera(self) -> bool:
        """Initialize mock camera"""
        print_status("Mock camera initialized (no hardware required)", "warning")
        return True
    
    def start_capture(self) -> bool:
        """Start mock capture"""
        self.is_running = True
        self.capture_thread = threading.Thread(target=self._mock_capture_loop, daemon=True)
        self.capture_thread.start()
        print_status("Mock camera capture started", "warning")
        return True
    
    def stop_capture(self) -> None:
        """Stop mock capture"""
        self.is_running = False
        if self.capture_thread:
            self.capture_thread.join(timeout=2)
        print_status("Mock camera capture stopped", "info")
    
    def _mock_capture_loop(self) -> None:
        """Mock capture loop that generates test patterns"""
        frame_count = 0
        while self.is_running:
            try:
                # Create a test pattern
                frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
                
                # Add some visual elements
                cv2.rectangle(frame, (50, 50), (200, 150), (0, 255, 0), 2)
                cv2.circle(frame, (400, 300), 50, (255, 0, 0), -1)
                cv2.putText(frame, f"Mock Frame {frame_count}", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                
                with self.frame_lock:
                    self.current_frame = frame
                
                frame_count += 1
                time.sleep(1.0 / 30)  # 30 FPS
                
            except Exception as e:
                logger.error(f"Error in mock capture loop: {e}")
                time.sleep(0.1)
    
    def get_frame(self) -> Optional[np.ndarray]:
        """Get the current mock frame"""
        with self.frame_lock:
            if self.current_frame is not None:
                return self.current_frame.copy()
        return None
    
    def test_camera(self) -> bool:
        """Test mock camera"""
        print_status("Mock camera test successful", "warning")
        return True
    
    def get_camera_info(self) -> dict:
        """Get mock camera information"""
        return {
            "status": "mock",
            "width": self.width,
            "height": self.height,
            "fps": 30,
            "backend": "mock"
        }

def create_camera_handler(use_mock: bool = False, prefer_picamera2: bool = True, **kwargs) -> CameraHandler:
    """Factory function to create appropriate camera handler
    - If use_mock is True, returns MockCameraHandler
    - If Picamera2 is available and preferred, returns Picamera2Handler
    - Otherwise returns OpenCV-based CameraHandler
    """
    if use_mock:
        return MockCameraHandler(**kwargs)
    if prefer_picamera2 and PICAMERA2_AVAILABLE:
        return Picamera2Handler(**kwargs)
    return CameraHandler(**kwargs)
