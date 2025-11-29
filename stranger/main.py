#!/usr/bin/env python3
"""
Offline Multi-Modal AI Assistant for Raspberry Pi 5
Main entry point with state machine
"""

import sys
import os
import logging
import signal
import time
import threading
from enum import Enum
from pathlib import Path

# Import project modules
from buttons import ButtonHandler, Button
from display import Display
from camera_model import CameraModel
from chat_ai import ChatAI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('assistant.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class State(Enum):
    """Application states"""
    MENU = "menu"
    CHAT_MODE = "chat_mode"
    OBJECT_MODE = "object_mode"


class Assistant:
    """Main application class with state machine"""
    
    def __init__(self):
        """Initialize all components"""
        self.state = State.MENU
        self.running = True
        
        # Initialize hardware components
        try:
            self.display = Display()
            self.buttons = ButtonHandler()
            self.camera = CameraModel()
            self.chat_ai = ChatAI()
            
            logger.info("All components initialized")
        except Exception as e:
            logger.error(f"Initialization error: {e}")
            raise
        
        # Register button callbacks
        self.buttons.register_callback(Button.K1, self._on_k1)
        self.buttons.register_callback(Button.K2, self._on_k2)
        self.buttons.register_callback(Button.K3, self._on_k3)
        
        # Chat mode state
        self.k3_held = False
        self.chat_processing = False
        
        # Object mode state
        self.object_processing = False
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
        self.cleanup()
        sys.exit(0)
    
    def _on_k1(self, button: Button, is_pressed: bool):
        """Handle K1 button (Chat Mode)"""
        if is_pressed and self.state != State.CHAT_MODE:
            logger.info("K1 pressed - Switching to Chat Mode")
            self._switch_to_chat_mode()
    
    def _on_k2(self, button: Button, is_pressed: bool):
        """Handle K2 button (Object Mode)"""
        if is_pressed and self.state != State.OBJECT_MODE:
            logger.info("K2 pressed - Switching to Object Mode")
            self._switch_to_object_mode()
    
    def _on_k3(self, button: Button, is_pressed: bool):
        """Handle K3 button (mode-dependent action)"""
        self.k3_held = is_pressed
        
        if self.state == State.CHAT_MODE:
            if is_pressed:
                # Start recording
                logger.info("K3 pressed - Starting recording")
                self.display.show_listening()
                self.chat_ai.start_recording()
            else:
                # Stop recording and process
                if not self.chat_processing:
                    logger.info("K3 released - Processing chat")
                    self._process_chat()
        
        elif self.state == State.OBJECT_MODE:
            if is_pressed and not self.object_processing:
                # Capture and detect
                logger.info("K3 pressed - Capturing image")
                self._process_object_detection()
    
    def _switch_to_chat_mode(self):
        """Switch to chat mode"""
        self.state = State.CHAT_MODE
        self.display.show_chat_mode()
        logger.info("Switched to Chat Mode")
    
    def _switch_to_object_mode(self):
        """Switch to object mode"""
        self.state = State.OBJECT_MODE
        self.display.show_object_mode()
        logger.info("Switched to Object Mode")
    
    def _process_chat(self):
        """Process chat mode: STT -> RAG -> LLM -> TTS -> Play"""
        if self.chat_processing:
            return
        
        self.chat_processing = True
        
        def process_thread():
            try:
                # Stop recording and get audio file
                self.display.show_processing()
                audio_path = self.chat_ai.stop_recording()
                
                if not audio_path:
                    logger.error("No audio file from recording")
                    self.chat_processing = False
                    self.display.show_chat_mode()
                    return
                
                # Speech to text
                user_query = self.chat_ai.speech_to_text(audio_path)
                
                if not user_query:
                    logger.warning("No text transcribed")
                    self.chat_processing = False
                    self.display.show_chat_mode()
                    return
                
                # Generate response with RAG
                response = self.chat_ai.generate_response(user_query)
                
                # Text to speech
                audio_path = self.chat_ai.text_to_speech(response)
                
                if audio_path:
                    # Play audio
                    self.chat_ai.play_audio(audio_path)
                    
                    # Cleanup temp files
                    try:
                        os.unlink(audio_path)
                    except:
                        pass
                
                # Return to chat mode display
                self.display.show_chat_mode()
                self.chat_processing = False
                
            except Exception as e:
                logger.error(f"Error in chat processing: {e}")
                self.chat_processing = False
                self.display.show_chat_mode()
        
        # Run in separate thread to avoid blocking
        thread = threading.Thread(target=process_thread, daemon=True)
        thread.start()
    
    def _process_object_detection(self):
        """Process object detection: Capture -> YOLO -> LLM -> TTS -> Play"""
        if self.object_processing:
            return
        
        self.object_processing = True
        
        def process_thread():
            try:
                # Show capturing
                self.display.show_capturing()
                
                # Capture image
                image_path = self.camera.capture_image()
                
                if not image_path:
                    logger.error("Failed to capture image")
                    self.object_processing = False
                    self.display.show_object_mode()
                    return
                
                # Show detecting
                self.display.show_detecting()
                
                # Run object detection
                detected_objects = self.camera.detect_objects(image_path)
                
                if not detected_objects:
                    logger.warning("No objects detected")
                    response = "I couldn't detect any objects in the image."
                else:
                    # Generate summary with LLM
                    objects_text = ", ".join(detected_objects)
                    prompt = f"Describe what you see in this image. Detected objects: {objects_text}. Give a brief, natural spoken summary."
                    response = self.chat_ai.generate_response(prompt)
                
                # Text to speech
                audio_path = self.chat_ai.text_to_speech(response)
                
                if audio_path:
                    # Play audio
                    self.chat_ai.play_audio(audio_path)
                    
                    # Cleanup temp files
                    try:
                        os.unlink(audio_path)
                    except:
                        pass
                
                # Return to object mode display
                self.display.show_object_mode()
                self.object_processing = False
                
            except Exception as e:
                logger.error(f"Error in object detection processing: {e}")
                self.object_processing = False
                self.display.show_object_mode()
        
        # Run in separate thread to avoid blocking
        thread = threading.Thread(target=process_thread, daemon=True)
        thread.start()
    
    def run(self):
        """Main application loop"""
        logger.info("Starting AI Assistant...")
        
        # Show boot screen
        self.display.show_boot_screen()
        
        # Main loop
        try:
            while self.running:
                time.sleep(0.1)  # Small delay to prevent CPU spinning
                
                # Check for state changes (handled by callbacks)
                # Main loop just keeps the program alive
                
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up all resources"""
        logger.info("Cleaning up resources...")
        
        try:
            if hasattr(self, 'display'):
                self.display.cleanup()
            if hasattr(self, 'buttons'):
                self.buttons.cleanup()
            if hasattr(self, 'camera'):
                self.camera.cleanup()
            if hasattr(self, 'chat_ai'):
                self.chat_ai.cleanup()
            
            logger.info("Cleanup complete")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


def main():
    """Main entry point"""
    try:
        assistant = Assistant()
        assistant.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

