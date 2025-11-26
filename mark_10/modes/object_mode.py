"""
Object Detection Mode Implementation
Handles camera-based object detection using YOLOv8 and scene summarization using LLM.
"""
import os
import cv2
import numpy as np
from datetime import datetime
from typing import List, Optional, Tuple
from ultralytics import YOLO
from llama_cpp import Llama
from pathlib import Path

from utils.camera_utils import CameraManager
from utils.display_utils import DisplayManager
from utils.audio_utils import AudioManager
from config import CAMERA_CONFIG


class ObjectMode:
    """Handles object detection mode functionality."""
    
    def __init__(self, display_manager: Optional[DisplayManager] = None, 
                 audio_manager: Optional[AudioManager] = None):
        """Initialize object detection mode with YOLOv8 and LLM."""
        self.yolo_model: Optional[YOLO] = None
        self.llm: Optional[Llama] = None
        self.camera_manager: Optional[CameraManager] = None
        self.display_manager = display_manager
        self.audio_manager = audio_manager
        
        # Create images directory
        self.images_dir = Path("./captured_images")
        self.images_dir.mkdir(exist_ok=True)
        
        self._initialize_models()
        self._initialize_camera()
    
    def _initialize_models(self):
        """Initialize YOLOv8 and LLM models."""
        try:
            # Initialize YOLOv8 model
            print("Loading YOLOv8 model...")
            self.yolo_model = YOLO('yolov8n.pt')  # nano version for Pi 5
            print("✅ YOLOv8 model loaded successfully!")
            
            # Initialize LLM for scene summarization
            print("Loading LLM for scene summarization...")
            model_paths = [
                "./models/gemma-3-4b-it-IQ4_XS.gguf",
                "./models/gemma-2b-it.Q6_K.gguf",
                 #"gemma-2b-it.Q6_K.gguf",
                "./models/llama-2-7b-chat.Q4_0.gguf",
                "./models/llama-7b-q4_0.gguf",
                "./models/llama-7b.gguf",
                "/home/pi/models/llama-7b-q4_0.gguf",
                "/home/pi/models/llama-7b.gguf",
                "llama-7b-q4_0.gguf"
            ]
            
            model_path = None
            for path in model_paths:
                if os.path.exists(path):
                    model_path = path
                    break
            
            if not model_path:
                raise FileNotFoundError(
                    "LLM model file not found for scene summarization."
                )
            
            self.llm = Llama(
                model_path=model_path,
                n_ctx=1024,  # Smaller context for summarization
                n_threads=4,
                n_gpu_layers=0,
                verbose=False
            )
            
            print("✅ LLM for scene summarization loaded successfully!")
            
        except Exception as e:
            print(f"❌ Error initializing models: {e}")
            raise
    
    def _initialize_camera(self):
        """Initialize camera manager with proper configuration."""
        try:
            self.camera_manager = CameraManager(
                camera_index=CAMERA_CONFIG['index'],
                resolution=CAMERA_CONFIG['resolution'],
                use_picamera=CAMERA_CONFIG['use_picamera']
            )
            # Set capture interval from config
            self.camera_manager.set_capture_interval(CAMERA_CONFIG['capture_interval'])
            print("✅ Camera initialized successfully!")
        except Exception as e:
            print(f"❌ Error initializing camera: {e}")
            raise
    
    def capture_and_detect(self, save_image: bool = True) -> Tuple[np.ndarray, List[str], str]:
        """
        Capture an image and detect objects.
        
        Args:
            save_image: Whether to save the captured image
        
        Returns:
            Tuple of (image, detected_objects, image_path)
        """
        if not self.camera_manager or not self.yolo_model:
            raise RuntimeError("Camera or YOLO model not initialized")
        
        # Show capture image on display
        if self.display_manager:
            self.display_manager.show_capture_image()
        
        # Capture image
        print("Capturing image...")
        image = self.camera_manager.capture_image()
        
        if image is None:
            raise RuntimeError("Failed to capture image")
        
        # Save image
        image_path = ""
        if save_image:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            image_path = str(self.images_dir / f"capture_{timestamp}.jpg")
            
            # Convert RGB to BGR for OpenCV save
            image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            cv2.imwrite(image_path, image_bgr)
            print(f"✅ Image saved to {image_path}")
        
        # Show detecting on display
        if self.display_manager:
            self.display_manager.show_detecting()
        
        # Run object detection
        print("Running object detection...")
        results = self.yolo_model(image)
        
        # Extract detected objects
        detected_objects = []
        if results and len(results) > 0:
            result = results[0]
            if result.boxes is not None:
                for box in result.boxes:
                    class_id = int(box.cls[0])
                    class_name = self.yolo_model.names[class_id]
                    confidence = float(box.conf[0])
                    
                    # Only include objects with confidence > 0.5
                    if confidence > 0.5:
                        detected_objects.append(class_name)
        
        return image, detected_objects, image_path
    
    def generate_scene_summary(self, detected_objects: List[str]) -> str:
        """Generate a natural language summary of the detected scene."""
        if not self.llm:
            return "❌ LLM not available for scene summarization."
        
        if not detected_objects:
            return "No objects detected in the scene."
        
        # Create prompt for scene summarization
        objects_text = ", ".join(detected_objects)
        prompt = f"""Based on the detected objects: {objects_text}

Provide a brief, natural description of what this scene likely represents. Keep it concise and conversational, as if describing what you see to someone.

Scene description:"""
        
        try:
            response = self.llm(
                prompt,
                max_tokens=128,
                temperature=0.7,
                top_p=0.9,
                stop=["\n\n", "Human:", "System:"],
                echo=False
            )
            
            if response and 'choices' in response and len(response['choices']) > 0:
                summary = response['choices'][0]['text'].strip()
                return summary
            else:
                return f"I can see {objects_text} in this scene."
                
        except Exception as e:
            return f"I can see {objects_text} in this scene."
    
    def analyze_scene(self):
        """Analyze the current scene and provide a summary."""
        try:
            # Capture image and detect objects
            image, detected_objects, image_path = self.capture_and_detect(save_image=True)
            
            # Print detected objects
            if detected_objects:
                objects_text = ', '.join(detected_objects)
                print(f"Detected objects: {objects_text}")
            else:
                print("No objects detected in the scene.")
            
            # Generate scene summary
            summary = self.generate_scene_summary(detected_objects)
            print(f"Summary: {summary}")
            
            # Display results on OLED
            if self.display_manager:
                if detected_objects:
                    # Show first few objects
                    display_lines = ["Detected:"]
                    for i, obj in enumerate(detected_objects[:3]):
                        display_lines.append(f"  {obj}")
                    if len(detected_objects) > 3:
                        display_lines.append(f"  +{len(detected_objects)-3} more")
                    self.display_manager.show_multiline(display_lines, clear_first=True)
                else:
                    self.display_manager.show_text("No objects found", clear_first=True)
            
            # Speak the summary
            if self.audio_manager:
                if detected_objects:
                    objects_text = ', '.join(detected_objects[:5])  # Limit to 5 objects
                    speech_text = f"I can see {objects_text}. {summary}"
                else:
                    speech_text = "No objects detected in the scene."
                self.audio_manager.speak(speech_text)
            
        except Exception as e:
            error_msg = f"Error: {str(e)[:30]}"
            print(f"❌ Error analyzing scene: {e}")
            if self.display_manager:
                self.display_manager.show_text(error_msg, clear_first=True)
            if self.audio_manager:
                self.audio_manager.speak("Error analyzing scene")
    
    def run(self):
        """
        Run the object detection mode.
        Note: This method just sets up the mode. 
        Actual capture is triggered by K3 button press via analyze_scene().
        """
        if not self.yolo_model or not self.camera_manager:
            error_msg = "Models not init"
            print("❌ Object detection mode not available. Models not initialized.")
            if self.display_manager:
                self.display_manager.show_text(error_msg, clear_first=True)
            return
        
        # Show object mode on display
        if self.display_manager:
            self.display_manager.show_object_mode()
        
        print("Object detection mode is ready!")
        print("Press K3 to capture and analyze image")
