#!/usr/bin/env python3
"""
Raspberry Pi 5 Multi-Modal AI Assistant
Main program entry point
"""

import asyncio
import signal
import sys
import time
import threading
from typing import Optional
import logging

# Import our modules
from utils import (
    print_banner, print_menu, print_status, handle_error, 
    get_user_input, clear_screen, print_help, setup_logging
)
from llm_interface import LLMInterface, SyncLLMInterface
from camera_handler import create_camera_handler
from object_detection import create_object_detector, create_detection_processor

# Global variables for graceful shutdown
running = True
current_mode = None

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    global running
    print_status("Shutdown signal received, cleaning up...", "warning")
    running = False

def setup_signal_handlers():
    """Setup signal handlers for graceful shutdown"""
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

class AIAssistant:
    """Main AI Assistant class"""
    
    def __init__(self):
        self.llm_interface = None
        self.camera_handler = None
        self.object_detector = None
        self.detection_processor = None
        self.current_mode = None
        self.use_mock_camera = False
        
        # Check if we should use mock camera (for testing without hardware)
        if len(sys.argv) > 1 and sys.argv[1] == "--mock":
            self.use_mock_camera = True
            print_status("Using mock camera mode", "warning")
    
    def initialize_components(self) -> bool:
        """Initialize all components"""
        print_status("Initializing AI Assistant components...", "info")
        
        # Initialize LLM interface
        try:
            self.llm_interface = SyncLLMInterface()
            if not self.llm_interface.check_ollama_status():
                print_status("Ollama not running. Please start Ollama first.", "error")
                print_status("Run: sudo systemctl start ollama", "info")
                return False
            
            # Check model availability
            available_models = self.llm_interface.get_available_models()
            if not available_models:
                print_status("No models available. Please download a model first.", "error")
                print_status("Run: ollama pull gemma2:2b", "info")
                return False
            
            print_status(f"Available models: {', '.join(available_models)}", "success")
            
        except Exception as e:
            handle_error(e, "LLM initialization")
            return False
        
        # Initialize camera handler (optional; allow Chat mode even if it fails)
        try:
            self.camera_handler = create_camera_handler(
                use_mock=self.use_mock_camera,
                prefer_picamera2=True,
                width=640,
                height=480,
                fps=30
            )
            if not self.camera_handler.test_camera():
                print_status("Camera test failed. Chat mode will still work.", "warning")
                self.camera_handler = None
        except Exception as e:
            handle_error(e, "Camera initialization")
            print_status("Camera not available. Chat mode will still work.", "warning")
            self.camera_handler = None
        
        # Initialize object detector
        try:
            self.object_detector = create_object_detector(model_size="n")
            if not self.object_detector.initialize_model():
                print_status("Failed to initialize object detection model", "error")
                return False
            
            self.detection_processor = create_detection_processor(self.object_detector)
            
        except Exception as e:
            handle_error(e, "Object detection initialization")
            return False
        
        print_status("All components initialized successfully", "success")
        return True
    
    def cleanup(self):
        """Cleanup resources"""
        print_status("Cleaning up resources...", "info")
        
        if self.camera_handler:
            self.camera_handler.stop_capture()
        
        print_status("Cleanup complete", "success")
    
    def chat_mode(self):
        """Run chat mode"""
        global running
        self.current_mode = "chat"
        
        print_status("Chat Mode Active", "success")
        print("Type your message and press Enter. Type 'q' to return to menu, 'x' to exit.")
        print("Type 'help' for assistance.\n")
        
        while running and self.current_mode == "chat":
            try:
                user_input = get_user_input("You: ")
                
                if not user_input:
                    continue
                
                if user_input.lower() == 'q':
                    break
                elif user_input.lower() == 'x':
                    global running
                    running = False
                    break
                elif user_input.lower() == 'help':
                    print_help()
                    continue
                
                # Generate response
                print_status("Generating response...", "info")
                response = self.llm_interface.chat_response(user_input)
                
                print(f"\nAssistant: {response}\n")
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                handle_error(e, "chat_mode")
                print("An error occurred. Please try again.\n")
        
        self.current_mode = None
        print_status("Chat mode ended", "info")
    
    def object_detection_mode(self):
        """Run object detection mode"""
        global running
        self.current_mode = "detection"
        
        print_status("Object Detection Mode Active", "success")
        print("Camera is running. Objects will be detected and analyzed automatically.")
        print("Press 'q' to return to menu, 'x' to exit.\n")
        
        # Start camera capture
        if not self.camera_handler or not self.camera_handler.start_capture():
            print_status("Failed to start camera capture", "error")
            return
        
        last_analysis_time = 0
        analysis_cooldown = 3.0  # Seconds between analyses
        
        try:
            while running and self.current_mode == "detection":
                # Get current frame
                frame = self.camera_handler.get_frame()
                if frame is None:
                    time.sleep(0.1)
                    continue
                
                # Process frame for object detection
                detections, annotated_frame = self.detection_processor.process_frame(frame)
                
                # Add to history
                self.detection_processor.add_to_history(detections)
                
                # Check if we should analyze new detections
                current_time = time.time()
                if (detections and 
                    self.detection_processor.should_analyze_detections(detections) and
                    current_time - last_analysis_time > analysis_cooldown):
                    
                    # Get unique objects
                    unique_objects = self.object_detector.get_unique_objects(detections)
                    
                    if unique_objects:
                        print(f"\n📷 Detected: {', '.join(unique_objects)}")
                        
                        # Analyze each object with LLM
                        for obj_name in unique_objects:
                            print(f"\n🤖 AI Analysis for {obj_name}:")
                            print_status("Analyzing object...", "info")
                            
                            try:
                                analysis = self.llm_interface.analyze_object(obj_name)
                                print(analysis)
                            except Exception as e:
                                handle_error(e, "object_analysis")
                                print(f"Unable to analyze {obj_name}")
                        
                        print(f"\nPress 'q' to return to menu, 'x' to exit")
                        last_analysis_time = current_time
                
                # Check for user input (non-blocking)
                if sys.platform == "win32":
                    # Windows doesn't support select for stdin
                    time.sleep(0.1)
                else:
                    import select
                    if select.select([sys.stdin], [], [], 0.1)[0]:
                        user_input = get_user_input().strip().lower()
                        if user_input == 'q':
                            break
                        elif user_input == 'x':
                            global running
                            running = False
                            break
                
        except KeyboardInterrupt:
            pass
        except Exception as e:
            handle_error(e, "object_detection_mode")
        finally:
            self.camera_handler.stop_capture()
        
        self.current_mode = None
        print_status("Object detection mode ended", "info")
    
    def run(self):
        """Main run loop"""
        global running
        
        # Setup logging
        setup_logging()
        
        # Setup signal handlers
        setup_signal_handlers()
        
        # Print banner
        print_banner()
        
        # Initialize components
        if not self.initialize_components():
            print_status("Failed to initialize components. Exiting.", "error")
            return
        
        # Main menu loop
        while running:
            try:
                clear_screen()
                print_banner()
                print_menu()
                
                choice = get_user_input().strip().lower()
                
                if choice == '1':
                    self.chat_mode()
                elif choice == '2':
                    self.object_detection_mode()
                elif choice == 'x':
                    running = False
                elif choice == 'help':
                    print_help()
                    input("Press Enter to continue...")
                else:
                    print_status("Invalid choice. Please select 1, 2, or x.", "warning")
                    time.sleep(1)
                    
            except KeyboardInterrupt:
                running = False
            except Exception as e:
                handle_error(e, "main_loop")
                time.sleep(1)
        
        # Cleanup
        self.cleanup()
        print_status("AI Assistant shutdown complete", "success")

def main():
    """Main entry point"""
    try:
        assistant = AIAssistant()
        assistant.run()
    except Exception as e:
        handle_error(e, "main")
        sys.exit(1)

if __name__ == "__main__":
    main()
