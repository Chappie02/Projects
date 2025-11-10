#!/usr/bin/env python3
"""
Raspberry Pi 5 Offline AI Assistant
Main entry point for the voice and hardware-enabled AI assistant.

Features:
1. Chat Mode: Voice/text-based conversation using local LLM
2. Object Detection Mode: Camera-based object detection with scene summarization
3. Voice Control: Wake word detection, voice commands, and TTS feedback
4. Hardware Control: OLED display and GPIO rotary switch for mode selection
"""

import sys
import os
import time
import threading
from typing import Optional

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modes.chat_mode import ChatMode
from modes.object_mode import ObjectMode
from utils.system_utils import print_banner, check_system_requirements
from utils.oled_display import OLEDDisplay
from utils.gpio_utils import RotarySwitch
from utils.voice_mode_manager import VoiceModeManager
import config


class AIAssistant:
    """Main controller for the AI Assistant application with voice and hardware support."""
    
    def __init__(self):
        self.chat_mode: Optional[ChatMode] = None
        self.object_mode: Optional[ObjectMode] = None
        self.current_mode = None
        self.running = True
        
        # Hardware components
        self.oled_display: Optional[OLEDDisplay] = None
        self.rotary_switch: Optional[RotarySwitch] = None
        self.voice_manager: Optional[VoiceModeManager] = None
        
        # Initialize hardware and voice components
        self._initialize_hardware()
        self._initialize_voice()
    
    def _initialize_hardware(self):
        """Initialize hardware components (OLED, GPIO)."""
        try:
            # Initialize OLED display
            if config.OLED_CONFIG.get('enabled', True):
                try:
                    self.oled_display = OLEDDisplay(
                        width=config.OLED_CONFIG['width'],
                        height=config.OLED_CONFIG['height'],
                        i2c_address=config.OLED_CONFIG['i2c_address']
                    )
                    self.oled_display.show_status("Initializing", "Starting...")
                except Exception as e:
                    print(f"⚠️  OLED display initialization failed: {e}")
                    self.oled_display = None
            
            # Initialize GPIO rotary switch
            if config.GPIO_CONFIG.get('enabled', True):
                try:
                    self.rotary_switch = RotarySwitch(
                        pin_a=config.GPIO_CONFIG['pin_chat'],
                        pin_b=config.GPIO_CONFIG['pin_object'],
                        pin_c=config.GPIO_CONFIG['pin_exit'],
                        mode_callback=self._on_mode_changed
                    )
                    print("✅ GPIO rotary switch initialized")
                except Exception as e:
                    print(f"⚠️  GPIO rotary switch initialization failed: {e}")
                    self.rotary_switch = None
            
        except Exception as e:
            print(f"⚠️  Hardware initialization error: {e}")
    
    def _initialize_voice(self):
        """Initialize voice components."""
        try:
            if config.VOICE_RECOGNITION_CONFIG.get('enabled', True) or \
               config.TTS_CONFIG.get('enabled', True):
                self.voice_manager = VoiceModeManager(oled_display=self.oled_display)
                print("✅ Voice mode manager initialized")
        except Exception as e:
            print(f"⚠️  Voice initialization error: {e}")
            self.voice_manager = None
    
    def _on_mode_changed(self, mode: int):
        """Callback for GPIO rotary switch mode changes."""
        try:
            if mode == RotarySwitch.MODE_CHAT:
                self._switch_to_chat_mode()
            elif mode == RotarySwitch.MODE_OBJECT:
                self._switch_to_object_mode()
            elif mode == RotarySwitch.MODE_EXIT:
                self._switch_to_exit_mode()
        except Exception as e:
            print(f"Error handling mode change: {e}")
    
    def _update_display(self, mode: str, status: str = ""):
        """Update OLED display."""
        if self.oled_display:
            self.oled_display.show_status(mode, status)
    
    def _speak_feedback(self, text: str):
        """Provide voice feedback."""
        if self.voice_manager:
            self.voice_manager.speak(text, blocking=False)
    
    def initialize_modes(self):
        """Initialize chat and object detection modes."""
        try:
            if self.oled_display:
                self.oled_display.show_status("Loading", "Initializing AI...")
            
            print("Initializing AI models...")
            self.chat_mode = ChatMode(oled_display=self.oled_display, 
                                     voice_manager=self.voice_manager)
            self.object_mode = ObjectMode(oled_display=self.oled_display,
                                         voice_manager=self.voice_manager)
            
            print("✅ AI models initialized successfully!")
            
            if self.oled_display:
                self.oled_display.show_status("Ready", "AI Assistant")
            
            return True
            
        except Exception as e:
            print(f"❌ Error initializing AI models: {e}")
            print("Please check your model files and dependencies.")
            if self.oled_display:
                self.oled_display.show_status("Error", "Init failed")
            return False
    
    def _switch_to_chat_mode(self):
        """Switch to chat mode."""
        if self.current_mode == "chat":
            return
        
        self.current_mode = "chat"
        self._update_display("Chat Mode", "Ready")
        self._speak_feedback("Switched to Chat Mode")
        print("💬 Switched to Chat Mode")
    
    def _switch_to_object_mode(self):
        """Switch to object detection mode."""
        if self.current_mode == "object":
            return
        
        self.current_mode = "object"
        self._update_display("Object Mode", "Ready")
        self._speak_feedback("Switched to Object Detection Mode")
        print("📷 Switched to Object Detection Mode")
    
    def _switch_to_exit_mode(self):
        """Switch to exit mode."""
        self.current_mode = "exit"
        self._update_display("Exiting...", "Goodbye!")
        self._speak_feedback("Exiting Assistant")
        print("👋 Exiting...")
        self.running = False
    
    def run_chat_mode(self):
        """Run chat mode with voice support."""
        if not self.chat_mode:
            print("❌ Chat mode not initialized. Please restart the application.")
            return
        
        self._switch_to_chat_mode()
        
        if self.voice_manager:
            # Voice-enabled chat mode
            self._run_voice_chat_mode()
        else:
            # Text-only chat mode
            self.chat_mode.run()
    
    def _run_voice_chat_mode(self):
        """Run voice-enabled chat mode."""
        print("\n💬 Chat Mode Activated (Voice Enabled)")
        print("Say 'Hey Pi' to activate, then ask your question.")
        print("Type 'exit' to return to main menu.")
        print("-" * 50)
        
        while self.running and self.current_mode == "chat":
            try:
                # Check GPIO switch
                if self.rotary_switch:
                    switch_mode = self.rotary_switch.get_mode()
                    if switch_mode != RotarySwitch.MODE_CHAT:
                        break
                
                # Listen for wake word if required
                if config.WAKE_WORD_CONFIG.get('require_wake_word', True):
                    if not self.voice_manager.listen_for_wake_word(timeout=1.0):
                        time.sleep(0.1)
                        continue
                
                # Listen for command
                command = self.voice_manager.listen_for_command(
                    duration=config.AUDIO_CONFIG.get('recording_duration', 3.0)
                )
                
                if not command:
                    continue
                
                # Process command
                action = self.voice_manager.process_voice_command(command)
                
                if action == "exit":
                    break
                elif action == "switch_to_object":
                    self._switch_to_object_mode()
                    self.run_object_mode()
                    break
                else:
                    # Treat as chat query
                    if self.oled_display:
                        self.oled_display.show_processing()
                    
                    response = self.chat_mode.generate_response(command)
                    print(f"Assistant: {response}")
                    
                    if self.oled_display:
                        self.oled_display.show_chat_mode()
                    
                    # Speak response if enabled
                    if config.TTS_CONFIG.get('speak_responses', False):
                        self.voice_manager.speak_response(response)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Error in chat mode: {e}")
                time.sleep(1)
    
    def run_object_mode(self):
        """Run object detection mode with voice support."""
        if not self.object_mode:
            print("❌ Object mode not initialized. Please restart the application.")
            return
        
        self._switch_to_object_mode()
        
        if self.voice_manager:
            # Voice-enabled object mode
            self._run_voice_object_mode()
        else:
            # Text-only object mode
            self.object_mode.run()
    
    def _run_voice_object_mode(self):
        """Run voice-enabled object detection mode."""
        print("\n📷 Object Detection Mode Activated (Voice Enabled)")
        print("Say 'Hey Pi' then 'what is this' to analyze the scene.")
        print("Type 'exit' to return to main menu.")
        print("-" * 50)
        
        while self.running and self.current_mode == "object":
            try:
                # Check GPIO switch
                if self.rotary_switch:
                    switch_mode = self.rotary_switch.get_mode()
                    if switch_mode != RotarySwitch.MODE_OBJECT:
                        break
                
                # Listen for wake word if required
                if config.WAKE_WORD_CONFIG.get('require_wake_word', True):
                    if not self.voice_manager.listen_for_wake_word(timeout=1.0):
                        time.sleep(0.1)
                        continue
                
                # Listen for command
                command = self.voice_manager.listen_for_command(
                    duration=config.AUDIO_CONFIG.get('recording_duration', 3.0)
                )
                
                if not command:
                    continue
                
                # Process command
                action = self.voice_manager.process_voice_command(command)
                
                if action == "exit":
                    break
                elif action == "switch_to_chat":
                    self._switch_to_chat_mode()
                    self.run_chat_mode()
                    break
                elif action == "what_is_this":
                    # Analyze scene
                    if self.oled_display:
                        self.oled_display.show_processing()
                    
                    self.object_mode.analyze_scene()
                    
                    if self.oled_display:
                        self.oled_display.show_object_mode()
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Error in object mode: {e}")
                time.sleep(1)
    
    def run(self):
        """Main application loop."""
        print_banner()
        
        # Check system requirements
        if not check_system_requirements():
            print("❌ System requirements not met. Please check your setup.")
            if self.oled_display:
                self.oled_display.show_status("Error", "System check failed")
            return
        
        # Initialize AI modes
        if not self.initialize_modes():
            return
        
        # Main application loop
        print("\n🤖 AI Assistant Ready!")
        print("Available controls:")
        print("  - GPIO Rotary Switch: Switch between modes")
        print("  - Voice Commands: Say 'Hey Pi' followed by your command")
        print("  - Keyboard: Type commands (if not using voice)")
        print("\nStarting main loop...")
        
        if self.oled_display:
            self.oled_display.show_status("Ready", "AI Assistant")
        
        # Monitor GPIO switch or use voice/text input
        try:
            while self.running:
                # Check GPIO rotary switch
                if self.rotary_switch:
                    mode = self.rotary_switch.get_mode()
                    
                    if mode == RotarySwitch.MODE_CHAT and self.current_mode != "chat":
                        self.run_chat_mode()
                    elif mode == RotarySwitch.MODE_OBJECT and self.current_mode != "object":
                        self.run_object_mode()
                    elif mode == RotarySwitch.MODE_EXIT:
                        self._switch_to_exit_mode()
                        break
                    
                    time.sleep(0.5)  # Check every 500ms
                
                else:
                    # Fallback to text/voice input if no GPIO switch
                    if self.voice_manager:
                        # Voice input mode
                        if config.WAKE_WORD_CONFIG.get('require_wake_word', True):
                            if self.voice_manager.listen_for_wake_word(timeout=1.0):
                                command = self.voice_manager.listen_for_command()
                                action = self.voice_manager.process_voice_command(command)
                                
                                if action == "switch_to_chat":
                                    self.run_chat_mode()
                                elif action == "switch_to_object":
                                    self.run_object_mode()
                                elif action == "exit":
                                    self._switch_to_exit_mode()
                                    break
                    else:
                        # Text input mode (original behavior)
                        user_input = input("\nEnter your choice (chat mode/object mode/exit): ").strip().lower()
                        
                        if user_input == "exit":
                            self._switch_to_exit_mode()
                            break
                        elif user_input == "chat mode":
                            self.run_chat_mode()
                        elif user_input == "object mode":
                            self.run_object_mode()
                        else:
                            print("❌ Invalid choice. Please enter 'chat mode', 'object mode', or 'exit'.")
        
        except KeyboardInterrupt:
            print("\n\n👋 Application interrupted. Goodbye!")
            self._switch_to_exit_mode()
        
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources."""
        try:
            if self.oled_display:
                self.oled_display.show_exiting()
                time.sleep(1)
                self.oled_display.cleanup()
            
            if self.voice_manager:
                self.voice_manager.cleanup()
            
            if self.rotary_switch:
                self.rotary_switch.cleanup()
            
            if self.object_mode and hasattr(self.object_mode, 'cleanup'):
                self.object_mode.cleanup()
            
            print("✅ Cleanup completed")
        
        except Exception as e:
            print(f"⚠️  Error during cleanup: {e}")


def main():
    """Main entry point."""
    try:
        assistant = AIAssistant()
        assistant.run()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
