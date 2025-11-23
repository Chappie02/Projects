#!/usr/bin/env python3
"""
Raspberry Pi 5 Offline AI Assistant
Main entry point for the CLI-based AI assistant.

This application provides two modes:
1. Chat Mode: Text-based conversation using local LLM
2. Object Detection Mode: Camera-based object detection with scene summarization

Hardware features:
- 0.96 inch OLED display (SSD1306) with K1, K2, K3 buttons
- Bluetooth earphone for microphone input
- Voice commands for wake-up and mode switching
"""

import sys
import os
import time
import threading
from typing import Optional

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append("/usr/lib/python3/dist-packages")
from modes.chat_mode import ChatMode
from modes.object_mode import ObjectMode
from utils.system_utils import print_banner, check_system_requirements
from utils.oled_utils import OLEDDisplay, ButtonHandler
from utils.voice_utils import VoiceCommandRecognizer
from config import OLED_CONFIG, AUDIO_CONFIG, VOICE_CONFIG


class AIAssistant:
    """Main controller for the AI Assistant application."""
    
    def __init__(self):
        self.chat_mode: Optional[ChatMode] = None
        self.object_mode: Optional[ObjectMode] = None
        self.current_mode = None
        
        # Hardware components
        self.oled: Optional[OLEDDisplay] = None
        self.button_handler: Optional[ButtonHandler] = None
        self.voice_recognizer: Optional[VoiceCommandRecognizer] = None
        
        # Mode management
        self.modes_list = ["chat", "object"]
        self.current_mode_index = 0
        self.is_asleep = False
        self.speed_mode = 0  # 0: normal, 1: fast, 2: slow
    
    def initialize_hardware(self):
        """Initialize OLED display, buttons, and voice recognition."""
        try:
            # Initialize OLED display
            if OLED_CONFIG.get('enabled', True):
                print("Initializing OLED display...")
                self.oled = OLEDDisplay(
                    i2c_port=OLED_CONFIG['i2c_port'],
                    i2c_address=OLED_CONFIG['i2c_address'],
                    k1_pin=OLED_CONFIG['k1_pin'],
                    k2_pin=OLED_CONFIG['k2_pin'],
                    k3_pin=OLED_CONFIG['k3_pin'],
                    rotation=OLED_CONFIG['rotation']
                )
                
                # Initialize button handler
                if self.oled:
                    self.button_handler = ButtonHandler(self.oled)
                    self.button_handler.set_mode_callback(self.switch_mode)
                    self.button_handler.set_speed_callback(self.switch_speed)
                    print("✅ OLED display and buttons initialized!")
                
                # Update display with initial state
                self.update_oled_display()
            
            # Initialize voice recognition
            if VOICE_CONFIG.get('enabled', True):
                print("Initializing voice recognition...")
                try:
                    self.voice_recognizer = VoiceCommandRecognizer(
                        wake_words=VOICE_CONFIG.get('wake_words', []),
                        language=AUDIO_CONFIG.get('language', 'en-US'),
                        energy_threshold=AUDIO_CONFIG.get('energy_threshold', 300)
                    )
                    self.voice_recognizer.set_wake_callback(self.wake_up)
                    self.voice_recognizer.set_command_callback(self.handle_voice_command)
                    
                    # Start listening in background
                    self.voice_recognizer.start_listening()
                    print("✅ Voice recognition initialized!")
                except Exception as e:
                    print(f"⚠️  Voice recognition not available: {e}")
                    self.voice_recognizer = None
            
        except Exception as e:
            print(f"⚠️  Error initializing hardware: {e}")
            print("Application will continue without hardware features.")
    
    def wake_up(self):
        """Wake up the assistant from sleep mode."""
        if self.is_asleep:
            self.is_asleep = False
            print("🔥 Assistant awakened!")
            self.update_oled_display(status="Awake")
    
    def switch_mode(self):
        """Switch between available modes (Chat/Object)."""
        if self.is_asleep:
            self.wake_up()
            return
        
        # Cycle through modes
        self.current_mode_index = (self.current_mode_index + 1) % len(self.modes_list)
        mode_name = self.modes_list[self.current_mode_index]
        
        print(f"🔄 Switching to {mode_name} mode...")
        self.update_oled_display(mode=mode_name.capitalize() + " Mode")
    
    def switch_speed(self):
        """Switch between speed modes (Normal/Fast/Slow)."""
        if self.is_asleep:
            self.wake_up()
            return
        
        # Cycle through speed modes
        self.speed_mode = (self.speed_mode + 1) % 3
        speed_names = ["Normal", "Fast", "Slow"]
        speed_name = speed_names[self.speed_mode]
        
        print(f"⚡ Speed mode: {speed_name}")
        self.update_oled_display(info_lines=[f"Speed: {speed_name}"])
    
    def handle_voice_command(self, command: str, text: str):
        """Handle voice command recognition."""
        print(f"📢 Voice command: {command}")
        
        if command == "wake_up":
            self.wake_up()
        elif command == "chat_mode":
            self.current_mode_index = 0
            self.run_chat_mode()
        elif command == "object_mode":
            self.current_mode_index = 1
            self.run_object_mode()
        elif command == "switch_mode":
            self.switch_mode()
        elif command == "exit":
            print("Voice command: Exiting...")
            # Signal to exit main loop
            return True
        return False
    
    def update_oled_display(self, mode: str = None, status: str = None, info_lines: list = None):
        """Update OLED display with current information."""
        if not self.oled:
            return
        
        # Determine mode name
        if mode is None:
            if self.current_mode:
                mode = self.current_mode.capitalize() + " Mode"
            elif self.current_mode_index < len(self.modes_list):
                mode = self.modes_list[self.current_mode_index].capitalize() + " Mode"
            else:
                mode = "Ready"
        
        # Determine status
        if status is None:
            if self.is_asleep:
                status = "Sleeping..."
            else:
                status = "Ready"
        
        # Update display
        self.oled.update_display(
            mode=mode,
            status=status,
            info_lines=info_lines
        )
    
    def print_main_menu(self):
        """Print the main menu options."""
        print("\n" + "="*60)
        print("🤖 Raspberry Pi 5 Offline AI Assistant")
        print("="*60)
        print("Available modes:")
        print("1. 'chat mode' - Text-based conversation with local LLM")
        print("2. 'object mode' - Camera-based object detection and analysis")
        print("3. 'wake up' - Wake up the assistant (voice command)")
        print("4. 'exit' - Exit the application")
        print("="*60)
        print("Hardware controls:")
        print("- K1 button: Switch mode")
        print("- K2 button: Switch speed")
        print("- K3 button: Wake up")
        print("- Voice: Say 'hey assistant' or 'wake up'")
        print("="*60)
    
    def initialize_modes(self):
        """Initialize chat and object detection modes."""
        try:
            print("Initializing AI models...")
            self.chat_mode = ChatMode()
            self.object_mode = ObjectMode()
            print("✅ AI models initialized successfully!")
        except Exception as e:
            print(f"❌ Error initializing AI models: {e}")
            print("Please check your model files and dependencies.")
            return False
        return True
    
    def run_chat_mode(self):
        """Run chat mode."""
        if not self.chat_mode:
            print("❌ Chat mode not initialized. Please restart the application.")
            return
        
        print("\n💬 Chat Mode Activated")
        print("Type your messages and press Enter. Type 'exit' to return to main menu.")
        print("-" * 50)
        
        self.current_mode = "chat"
        self.current_mode_index = 0
        self.update_oled_display(mode="Chat Mode", status="Active")
        self.chat_mode.run()
        self.current_mode = None
        self.update_oled_display(mode="Ready", status="Idle")
    
    def run_object_mode(self):
        """Run object detection mode."""
        if not self.object_mode:
            print("❌ Object mode not initialized. Please restart the application.")
            return
        
        print("\n📷 Object Detection Mode Activated")
        print("Type 'what is this' to analyze the scene, or 'exit' to return to main menu.")
        print("-" * 50)
        
        self.current_mode = "object"
        self.current_mode_index = 1
        self.update_oled_display(mode="Object Mode", status="Active")
        self.object_mode.run()
        self.current_mode = None
        self.update_oled_display(mode="Ready", status="Idle")
    
    def run(self):
        """Main application loop."""
        print_banner()
        
        # Check system requirements
        if not check_system_requirements():
            print("❌ System requirements not met. Please check your setup.")
            return
        
        # Initialize hardware (OLED, buttons, voice)
        self.initialize_hardware()
        
        # Initialize AI modes
        if not self.initialize_modes():
            return
        
        # Update OLED with initialized state
        self.update_oled_display(mode="Ready", status="Initialized")
        
        # Main application loop
        should_exit = False
        while not should_exit:
            try:
                self.print_main_menu()
                user_input = input("\nEnter your choice: ").strip().lower()
                
                if user_input == "exit":
                    print("\n👋 Thank you for using the AI Assistant!")
                    should_exit = True
                elif user_input in ["chat mode", "chat"]:
                    self.run_chat_mode()
                elif user_input in ["object mode", "object"]:
                    self.run_object_mode()
                elif user_input in ["wake up", "wake"]:
                    self.wake_up()
                elif user_input == "k1":
                    # Simulate K1 button press
                    self.switch_mode()
                elif user_input == "k2":
                    # Simulate K2 button press
                    self.switch_speed()
                elif user_input == "k3":
                    # Simulate K3 button press
                    self.wake_up()
                else:
                    print("❌ Invalid choice. Please enter 'chat mode', 'object mode', 'wake up', or 'exit'.")
                    print("    Or use buttons: K1 (mode), K2 (speed), K3 (wake)")
            
            except KeyboardInterrupt:
                print("\n\n👋 Application interrupted. Goodbye!")
                should_exit = True
            except Exception as e:
                print(f"❌ Unexpected error: {e}")
                print("Please try again or restart the application.")
        
        # Cleanup
        self.cleanup()
    
    def cleanup(self):
        """Clean up hardware resources."""
        print("Cleaning up hardware resources...")
        
        if self.voice_recognizer:
            try:
                self.voice_recognizer.stop_listening()
                self.voice_recognizer.cleanup()
            except Exception as e:
                print(f"Error cleaning up voice recognizer: {e}")
        
        if self.oled:
            try:
                self.oled.clear()
                self.oled.cleanup()
            except Exception as e:
                print(f"Error cleaning up OLED: {e}")
        
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
