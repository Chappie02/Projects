"""
Camera Utilities
Handles camera operations for the Raspberry Pi camera module.
Supports both picamera2 (Raspberry Pi native) and OpenCV fallback.
"""

import cv2
import numpy as np
from typing import Optional, Callable
import time

# Try to import picamera2 for Raspberry Pi
try:
    from picamera2 import Picamera2
    PICAMERA2_AVAILABLE = True
except ImportError:
    PICAMERA2_AVAILABLE = False
    Picamera2 = None


class CameraManager:
    """Manages camera operations for object detection."""
    
    def __init__(self, camera_index: int = 0, resolution: tuple = (1920, 1080), use_picamera: bool = True):
        """
        Initialize camera manager.
        
        Args:
            camera_index: Camera device index (usually 0 for default camera)
            resolution: Camera resolution (width, height) - default 1920x1080 for proper quality
            use_picamera: If True, try to use picamera2 for Raspberry Pi (recommended)
        """
        self.camera_index = camera_index
        self.resolution = resolution
        self.use_picamera = use_picamera and PICAMERA2_AVAILABLE
        self.cap: Optional[cv2.VideoCapture] = None
        self.picam2: Optional[Picamera2] = None
        self.camera_type = None
        self.last_capture_time = 0
        self.capture_interval = 1.0  # 1 second interval between captures
        
        self._initialize_camera()
    
    def _initialize_camera(self):
        """Initialize the camera capture."""
        try:
            # Try picamera2 first if available and requested
            if self.use_picamera:
                try:
                    self.picam2 = Picamera2()
                    
                    # Configure camera for capture with proper resolution
                    # Main stream for high quality captures
                    capture_config = self.picam2.create_still_configuration(
                        main={"size": self.resolution},
                        controls={"FrameRate": 1.0}  # 1 FPS for 1-second interval
                    )
                    self.picam2.configure(capture_config)
                    self.picam2.start()
                    
                    # Allow camera to warm up and stabilize
                    time.sleep(2)
                    
                    self.camera_type = "picamera2"
                    print(f"✅ Raspberry Pi Camera initialized with picamera2")
                    print(f"   Resolution: {self.resolution[0]}x{self.resolution[1]}")
                    print(f"   Capture interval: {self.capture_interval} second(s)")
                    return
                    
                except Exception as e:
                    print(f"⚠️  picamera2 initialization failed: {e}")
                    print("   Falling back to OpenCV...")
                    self.use_picamera = False
                    if self.picam2:
                        try:
                            self.picam2.stop()
                            self.picam2.close()
                        except:
                            pass
                        self.picam2 = None
            
            # Fallback to OpenCV
            backends = [cv2.CAP_V4L2, cv2.CAP_GSTREAMER, cv2.CAP_ANY]
            
            for backend in backends:
                try:
                    self.cap = cv2.VideoCapture(self.camera_index, backend)
                    if self.cap.isOpened():
                        print(f"✅ Camera initialized with OpenCV backend: {backend}")
                        break
                except:
                    continue
            
            if not self.cap or not self.cap.isOpened():
                # Fallback to default
                self.cap = cv2.VideoCapture(self.camera_index)
            
            if not self.cap.isOpened():
                raise RuntimeError("Could not open camera")
            
            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
            self.cap.set(cv2.CAP_PROP_FPS, 1)  # 1 FPS for 1-second interval
            
            # Allow camera to warm up
            time.sleep(1)
            
            self.camera_type = "opencv"
            print(f"Camera initialized with OpenCV: {self.resolution[0]}x{self.resolution[1]}")
            
        except Exception as e:
            print(f"❌ Error initializing camera: {e}")
            raise
    
    def capture_image(self, enforce_interval: bool = True) -> Optional[np.ndarray]:
        """
        Capture a single image from the camera.
        
        Args:
            enforce_interval: If True, enforces 1-second interval between captures
        
        Returns:
            Captured image as numpy array, or None if failed
        """
        # Enforce 1-second interval if requested
        if enforce_interval:
            current_time = time.time()
            time_since_last_capture = current_time - self.last_capture_time
            
            if time_since_last_capture < self.capture_interval:
                sleep_time = self.capture_interval - time_since_last_capture
                time.sleep(sleep_time)
            
            self.last_capture_time = time.time()
        
        if self.camera_type == "picamera2" and self.picam2:
            try:
                # Capture image using picamera2
                image = self.picam2.capture_array()
                
                # picamera2 returns RGB by default
                # Ensure it's the right shape (height, width, channels)
                if len(image.shape) == 3 and image.shape[2] == 3:
                    return image
                else:
                    print("❌ Unexpected image format from picamera2")
                    return None
                    
            except Exception as e:
                print(f"❌ Error capturing image with picamera2: {e}")
                return None
        
        elif self.cap and self.cap.isOpened():
            try:
                # Capture frame using OpenCV
                ret, frame = self.cap.read()
                
                if not ret:
                    print("❌ Failed to capture frame")
                    return None
                
                # Convert BGR to RGB (OpenCV uses BGR by default)
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                return frame_rgb
                
            except Exception as e:
                print(f"❌ Error capturing image with OpenCV: {e}")
                return None
        else:
            print("❌ Camera not initialized")
            return None
    
    def capture_images_interval(self, count: int = 1, callback: Optional[Callable[[np.ndarray, int], None]] = None) -> list:
        """
        Capture multiple images at 1-second intervals.
        
        Args:
            count: Number of images to capture
            callback: Optional callback function(image, index) called after each capture
        
        Returns:
            List of captured images
        """
        images = []
        
        for i in range(count):
            print(f"Capturing image {i+1}/{count}...")
            image = self.capture_image(enforce_interval=True)
            
            if image is not None:
                images.append(image)
                if callback:
                    callback(image, i)
            else:
                print(f"⚠️  Failed to capture image {i+1}")
            
            # Wait 1 second before next capture (if not last image)
            if i < count - 1:
                time.sleep(self.capture_interval)
        
        return images
    
    def test_camera(self) -> bool:
        """
        Test if camera is working properly.
        
        Returns:
            True if camera is working, False otherwise
        """
        try:
            image = self.capture_image()
            return image is not None
        except:
            return False
    
    def set_resolution(self, resolution: tuple):
        """
        Update camera resolution.
        
        Args:
            resolution: New resolution (width, height)
        """
        self.resolution = resolution
        
        if self.camera_type == "picamera2" and self.picam2:
            try:
                self.picam2.stop()
                capture_config = self.picam2.create_still_configuration(
                    main={"size": self.resolution},
                    controls={"FrameRate": 1.0}
                )
                self.picam2.configure(capture_config)
                self.picam2.start()
                time.sleep(1)  # Allow reconfiguration to settle
                print(f"✅ Resolution updated to {self.resolution[0]}x{self.resolution[1]}")
            except Exception as e:
                print(f"❌ Error updating resolution: {e}")
        elif self.cap and self.cap.isOpened():
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])
            print(f"✅ Resolution updated to {self.resolution[0]}x{self.resolution[1]}")
    
    def set_capture_interval(self, interval: float):
        """
        Set the capture interval in seconds.
        
        Args:
            interval: Interval in seconds between captures
        """
        self.capture_interval = max(0.1, interval)  # Minimum 0.1 seconds
        print(f"✅ Capture interval set to {self.capture_interval} second(s)")
    
    def cleanup(self):
        """Clean up camera resources."""
        if self.picam2:
            try:
                self.picam2.stop()
                self.picam2.close()
                self.picam2 = None
            except Exception as e:
                print(f"⚠️  Error closing picamera2: {e}")
        
        if self.cap:
            self.cap.release()
            self.cap = None
        
        self.camera_type = None
        print("Camera resources cleaned up.")


def test_camera_connection(camera_index: int = 0) -> bool:
    """
    Test camera connection without initializing full camera manager.
    
    Args:
        camera_index: Camera device index to test
        
    Returns:
        True if camera is accessible, False otherwise
    """
    try:
        cap = cv2.VideoCapture(camera_index)
        if cap.isOpened():
            ret, frame = cap.read()
            cap.release()
            return ret and frame is not None
        return False
    except:
        return False


def list_available_cameras() -> list:
    """
    List available camera devices.
    
    Returns:
        List of available camera indices
    """
    available_cameras = []
    
    for i in range(5):  # Check first 5 camera indices
        if test_camera_connection(i):
            available_cameras.append(i)
    
    return available_cameras
