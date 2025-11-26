#!/usr/bin/env python3
"""
Raspberry Pi 5 Offline AI Assistant
Main entry point for the display and button-based AI assistant.

This application provides two modes:
1. Chat Mode: Voice-based conversation using local LLM (K1 button)
2. Object Detection Mode: Camera-based object detection (K2 button, K3 to capture)
"""

import sys
import os
import time
from typing import Optional

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append("/usr/lib/python3/dist-packages")

from modes.chat_mode import ChatMode
from modes.object_mode import ObjectMode
from utils.display_utils import DisplayManager
from utils.button_utils import ButtonManager
from utils.audio_utils import AudioManager
from utils.system_utils import check_system_requirements


class AIAssistant:
    """Main controller for the AI Assistant application."""
    
    def __init__(self):
        self.chat_mode: Optional[ChatMode] = None
        self.object_mode: Optional[ObjectMode] = None
        self.display_manager: Optional[DisplayManager] = None
        self.button_manager: Optional[ButtonManager] = None
        self.audio_manager: Optional[AudioManager] = None
        self.current_mode = None
        self.running = True
    
    def initialize_components(self):
        """Initialize all components (display, buttons, audio, modes)."""
        try:
            # Initialize display
            print("Initializing OLED display...")
            self.display_manager = DisplayManager(sda_pin=2, scl_pin=3)
            if self.display_manager.is_available():
                self.display_manager.show_text("Initializing...")
            print("✅ Display initialized")
            
            # Initialize buttons
            print("Initializing buttons...")
            self.button_manager = ButtonManager(k1_pin=17, k2_pin=27, k3_pin=22)
            if self.button_manager.is_available():
                # Set up button callbacks
                self.button_manager.set_k1_callback(self.on_k1_pressed)
                self.button_manager.set_k2_callback(self.on_k2_pressed)
                self.button_manager.set_k3_callback(self.on_k3_pressed)
            print("✅ Buttons initialized")
            
            # Initialize audio
            print("Initializing audio...")
            self.audio_manager = AudioManager()
            if self.audio_manager.is_available():
                self.audio_manager.list_audio_devices()
            print("✅ Audio initialized")
            
            # Initialize AI modes
            print("Initializing AI models...")
            self.chat_mode = ChatMode(
                display_manager=self.display_manager,
                audio_manager=self.audio_manager
            )
            self.object_mode = ObjectMode(
                display_manager=self.display_manager,
                audio_manager=self.audio_manager
            )
            print("✅ AI models initialized successfully!")
            
            # Show ready message
            if self.display_manager:
                self.display_manager.show_multiline([
                    "AI Assistant",
                    "Ready",
                    "K1: Chat Mode",
                    "K2: Object Mode"
                ], clear_first=True)
            
            return True
            
        except Exception as e:
            print(f"❌ Error initializing components: {e}")
            if self.display_manager:
                self.display_manager.show_text(f"Error: {str(e)[:20]}")
            return False
    
    def on_k1_pressed(self):
        """Handle K1 button press (Chat Mode)."""
        print("K1 pressed - Entering Chat Mode")
        self.current_mode = "chat"
        self.run_chat_mode()
        # Don't reset current_mode here - let it stay in chat mode
    
    def on_k2_pressed(self):
        """Handle K2 button press (Object Detection Mode)."""
        print("K2 pressed - Entering Object Detection Mode")
        self.current_mode = "object"
        self.run_object_mode()
        # Don't reset current_mode here - let it stay in object mode
    
    def on_k3_pressed(self):
        """Handle K3 button press (Capture Image in Object Mode)."""
        if self.current_mode == "object" and self.object_mode:
            print("K3 pressed - Capturing image")
            try:
                self.object_mode.analyze_scene()
            except Exception as e:
                print(f"❌ Error capturing image: {e}")
                if self.display_manager:
                    self.display_manager.show_text("Capture error", clear_first=True)
    
    def run_chat_mode(self):
        """Run one chat cycle."""
        if not self.chat_mode:
            error_msg = "Chat mode not init"
            print("❌ Chat mode not initialized.")
            if self.display_manager:
                self.display_manager.show_text(error_msg, clear_first=True)
            return
        
        # Run one chat cycle (triggered by K1 button)
        try:
            self.chat_mode.run()
        except Exception as e:
            print(f"❌ Error in chat mode: {e}")
            if self.display_manager:
                self.display_manager.show_text("Chat error", clear_first=True)
    
    def run_object_mode(self):
        """Activate object detection mode."""
        if not self.object_mode:
            error_msg = "Object mode not init"
            print("❌ Object mode not initialized.")
            if self.display_manager:
                self.display_manager.show_text(error_msg, clear_first=True)
            return
        
        # Show object mode on display
        if self.display_manager:
            self.display_manager.show_object_mode()
        
        print("Object detection mode active. Press K3 to capture image.")
        print("Press K1 to switch to chat mode.")
    
    def run(self):
        """Main application loop."""
        print("="*60)
        print("🤖 Raspberry Pi 5 Offline AI Assistant")
        print("="*60)
        
        # Check system requirements
        if not check_system_requirements():
            error_msg = "System check failed"
            print("❌ System requirements not met.")
            if self.display_manager:
                self.display_manager.show_text(error_msg, clear_first=True)
            return
        
        # Initialize components
        if not self.initialize_components():
            return
        
        # Main application loop - wait for button presses
        print("\n" + "="*60)
        print("Application ready!")
        print("Press K1 for Chat Mode")
        print("Press K2 for Object Detection Mode")
        print("Press K3 in Object Mode to capture image")
        print("="*60 + "\n")
        
        try:
            while self.running:
                # Main loop - buttons handle mode switching via callbacks
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\n\n👋 Application interrupted. Goodbye!")
            if self.display_manager:
                self.display_manager.show_text("Shutting down", clear_first=True)
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            if self.display_manager:
                self.display_manager.show_text("Fatal error", clear_first=True)
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources."""
        print("Cleaning up resources...")
        
        if self.display_manager:
            self.display_manager.cleanup()
        
        if self.button_manager:
            self.button_manager.cleanup()
        
        if self.audio_manager:
            self.audio_manager.cleanup()
        
        if self.object_mode and self.object_mode.camera_manager:
            self.object_mode.camera_manager.cleanup()
        
        print("✅ Cleanup complete")


def main():
    """Main entry point."""
    try:
        assistant = AIAssistant()
        assistant.run()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
