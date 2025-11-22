"""
Main application loop for Multi-Modal AI Assistant
Manages mode switching and coordinates all subsystems
"""

import time
import signal
import sys
from hardware import HardwareController
from vision import VisionSystem
from memory import MemorySystem
from assistant import Assistant
import config


class AIAssistant:
    """Main application class managing all subsystems"""
    
    def __init__(self):
        """Initialize all subsystems"""
        self.hardware = None
        self.vision = None
        self.memory = None
        self.assistant = None
        self.current_mode = config.MODE_CHAT
        self.running = True
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self._init_systems()
        self._setup_button_callbacks()
    
    def _init_systems(self):
        """Initialize all hardware and software systems"""
        print("Initializing Multi-Modal AI Assistant...")
        
        try:
            # Initialize hardware (OLED + buttons)
            print("1. Initializing hardware...")
            self.hardware = HardwareController()
            
            # Initialize memory system (ChromaDB)
            print("2. Initializing memory system...")
            self.memory = MemorySystem()
            
            # Initialize assistant (LLM, STT, TTS)
            print("3. Initializing assistant...")
            self.assistant = Assistant()
            
            # Initialize vision system (YOLO - camera on-demand)
            print("4. Initializing vision system...")
            self.vision = VisionSystem()
            
            print("All systems initialized successfully!")
            
            # Display initial mode
            self._update_display()
            
        except Exception as e:
            print(f"Error during initialization: {e}")
            self.cleanup()
            sys.exit(1)
    
    def _setup_button_callbacks(self):
        """Setup button callback functions"""
        # K1: Select/Listen button
        self.hardware.register_button_callback(
            config.GPIO_BUTTON_K1,
            self._on_k1_press
        )
        
        # K2: Switch to Chat mode
        self.hardware.register_button_callback(
            config.GPIO_BUTTON_K2,
            self._on_k2_press
        )
        
        # K3: Switch to Vision mode
        self.hardware.register_button_callback(
            config.GPIO_BUTTON_K3,
            self._on_k3_press
        )
    
    def _on_k1_press(self, pin):
        """Handle K1 button press (Select/Listen)"""
        print(f"K1 pressed - Current mode: {self.current_mode}")
        
        if self.current_mode == config.MODE_CHAT:
            self._handle_chat_mode()
        elif self.current_mode == config.MODE_VISION:
            self._handle_vision_mode()
    
    def _on_k2_press(self, pin):
        """Handle K2 button press (Switch to Chat mode)"""
        print("K2 pressed - Switching to Chat mode")
        self.current_mode = config.MODE_CHAT
        self._update_display()
    
    def _on_k3_press(self, pin):
        """Handle K3 button press (Switch to Vision mode)"""
        print("K3 pressed - Switching to Vision mode")
        self.current_mode = config.MODE_VISION
        self._update_display()
    
    def _update_display(self):
        """Update OLED display with current mode"""
        if self.current_mode == config.MODE_CHAT:
            self.hardware.display_text(config.MSG_MODE_CHAT)
        elif self.current_mode == config.MODE_VISION:
            self.hardware.display_text(config.MSG_MODE_VISION)
    
    def _handle_chat_mode(self):
        """Process chat mode interaction"""
        try:
            # Update display
            self.hardware.display_text(config.MSG_LISTENING)
            
            # Listen for user input
            user_query = self.assistant.listen(
                timeout=config.AUDIO_RECORD_DURATION,
                phrase_time_limit=10
            )
            
            if not user_query:
                self.hardware.display_text("No input detected")
                self.assistant.speak("I didn't catch that. Please try again.")
                time.sleep(2)
                self._update_display()
                return
            
            # Update display
            self.hardware.display_text(config.MSG_PROCESSING)
            
            # Process query with RAG
            response = self.assistant.process_chat_query(
                user_query,
                memory_system=self.memory
            )
            
            # Display response (truncated for display)
            display_text = response[:20] + "..." if len(response) > 20 else response
            self.hardware.display_multiline([
                config.MSG_MODE_CHAT,
                display_text
            ])
            
            # Speak response
            self.assistant.speak(response)
            
            # Return to mode display
            time.sleep(1)
            self._update_display()
            
        except Exception as e:
            print(f"Error in chat mode: {e}")
            self.hardware.display_text("Error occurred")
            self.assistant.speak("Sorry, I encountered an error.")
            time.sleep(2)
            self._update_display()
    
    def _handle_vision_mode(self):
        """Process vision mode interaction"""
        try:
            # Update display
            self.hardware.display_text(config.MSG_LISTENING)
            
            # Listen for voice command
            command = self.assistant.listen(
                timeout=config.AUDIO_RECORD_DURATION,
                phrase_time_limit=5
            )
            
            if not command:
                self.hardware.display_text("No command detected")
                self.assistant.speak("I didn't hear a command.")
                time.sleep(2)
                self._update_display()
                return
            
            # Check if command is vision-related
            command_lower = command.lower()
            if "what" in command_lower and ("this" in command_lower or "see" in command_lower):
                # Process vision query
                self.hardware.display_text("Capturing image...")
                
                # Capture and detect
                detections = self.vision.process_vision_query()
                
                if not detections:
                    response = "I couldn't detect any objects in the image."
                else:
                    # Format detections
                    detection_text = self.vision.format_detections_for_llm(detections)
                    
                    # Generate description using LLM
                    self.hardware.display_text(config.MSG_PROCESSING)
                    response = self.assistant.process_vision_query(detection_text)
                
                # Display and speak response
                display_text = response[:20] + "..." if len(response) > 20 else response
                self.hardware.display_multiline([
                    config.MSG_MODE_VISION,
                    display_text
                ])
                
                self.assistant.speak(response)
                
            else:
                # Not a vision command, treat as chat
                self.hardware.display_text(config.MSG_PROCESSING)
                response = self.assistant.process_chat_query(
                    command,
                    memory_system=self.memory
                )
                self.assistant.speak(response)
            
            # Return to mode display
            time.sleep(1)
            self._update_display()
            
        except Exception as e:
            print(f"Error in vision mode: {e}")
            self.hardware.display_text("Error occurred")
            self.assistant.speak("Sorry, I encountered an error processing the image.")
            time.sleep(2)
            self._update_display()
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print("\nShutdown signal received. Cleaning up...")
        self.running = False
        self.cleanup()
        sys.exit(0)
    
    def run(self):
        """Main application loop"""
        print("Multi-Modal AI Assistant is running!")
        print("Press K2 for Chat mode, K3 for Vision mode, K1 to interact")
        print("Press Ctrl+C to exit")
        
        try:
            while self.running:
                # Main loop is event-driven via button interrupts
                # Just sleep and let button callbacks handle interactions
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nKeyboard interrupt received")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Cleanup all resources"""
        print("Cleaning up resources...")
        
        try:
            if self.hardware:
                self.hardware.cleanup()
            if self.vision:
                self.vision.cleanup()
            if self.memory:
                self.memory.cleanup()
            if self.assistant:
                self.assistant.cleanup()
            
            print("Cleanup complete")
        except Exception as e:
            print(f"Error during cleanup: {e}")


def main():
    """Entry point"""
    app = AIAssistant()
    app.run()


if __name__ == "__main__":
    main()

