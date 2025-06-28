import time
import sys
import logging
import threading
from enum import Enum
from typing import Optional
from colorama import init, Fore, Style

# Initialize colorama for colored output
init()

# Import our modules
from config import Config
from llm_module import LLMModule
from voice_module import VoiceModule
from object_detection_module import ObjectDetectionModule
from home_automation_module import HomeAutomationModule

class Mode(Enum):
    CHAT = "chat"
    OBJECT_DETECTION = "object_detection"
    HOME_AUTOMATION = "home_automation"

class AIAssistant:
    def __init__(self):
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Initialize mode
        self.current_mode = Mode.CHAT
        self.previous_mode = Mode.CHAT
        
        # Initialize modules
        self.logger.info("Initializing AI Assistant modules...")
        self.llm = LLMModule()
        self.voice = VoiceModule()
        self.object_detection = ObjectDetectionModule()
        self.home_automation = HomeAutomationModule()
        
        # Voice input handling
        self.voice_input_queue = []
        self.is_voice_active = False
        
        self.logger.info("AI Assistant initialized successfully!")
        self._print_welcome_message()
    
    def _print_welcome_message(self):
        """Print welcome message with available features"""
        print(f"\n{Fore.CYAN}🤖 AI Assistant for Raspberry Pi 5{Style.RESET_ALL}")
        print(f"{Fore.GREEN}✓ LLM: {'Available' if self.llm.is_available() else 'Not available'}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}✓ Voice: {'Available' if self.voice.is_voice_available() else 'Not available'}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}✓ Object Detection: {'Available' if self.object_detection.is_available() else 'Not available'}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}✓ Home Automation: {'Available' if self.home_automation.is_available() else 'Not available'}{Style.RESET_ALL}")
        print(f"\n{Fore.YELLOW}Current Mode: {self.current_mode.value.upper()}{Style.RESET_ALL}")
        print(f"{Fore.BLUE}Type 'help' for commands or 'exit' to quit{Style.RESET_ALL}\n")
    
    def switch_mode(self, new_mode: Mode):
        """Switch between different modes"""
        if new_mode == self.current_mode:
            return
        
        self.previous_mode = self.current_mode
        self.current_mode = new_mode
        
        # Handle mode-specific initialization
        if new_mode == Mode.OBJECT_DETECTION:
            if self.object_detection.is_available():
                self.object_detection.start_detection()
                self._speak_and_print(f"Switched to object detection mode. I can now see through the camera.")
            else:
                self._speak_and_print("Object detection is not available. Please check camera connection.")
                self.current_mode = self.previous_mode
        
        elif new_mode == Mode.HOME_AUTOMATION:
            if self.home_automation.is_available():
                self._speak_and_print("Switched to home automation mode. I can control your smart devices.")
            else:
                self._speak_and_print("Home automation is not available. Please check device connections.")
                self.current_mode = self.previous_mode
        
        elif new_mode == Mode.CHAT:
            # Stop object detection if it was running
            if self.previous_mode == Mode.OBJECT_DETECTION:
                self.object_detection.stop_detection()
            self._speak_and_print("Switched to chat mode. How can I help you?")
        
        print(f"{Fore.YELLOW}Mode: {self.current_mode.value.upper()}{Style.RESET_ALL}")
    
    def process_input(self, user_input: str):
        """Process user input and generate appropriate response"""
        if not user_input.strip():
            return
        
        # Convert input to lowercase for easier matching
        user_input_lower = user_input.lower()
        
        # Check for mode switch commands
        if self._should_switch_mode(user_input_lower):
            return
        
        # Check for special commands
        if user_input_lower in ['help', 'commands']:
            self._show_help()
            return
        
        if user_input_lower in ['status', 'info']:
            self._show_status()
            return
        
        # Process based on current mode
        response = self._handle_mode_specific_input(user_input)
        self._speak_and_print(response)
    
    def _should_switch_mode(self, user_input: str) -> bool:
        """Check if user input should trigger a mode switch"""
        # Check for chat mode keywords
        if any(keyword in user_input for keyword in Config.MODE_KEYWORDS["chat"]):
            self.switch_mode(Mode.CHAT)
            return True
        
        # Check for object detection keywords
        if any(keyword in user_input for keyword in Config.MODE_KEYWORDS["object_detection"]):
            self.switch_mode(Mode.OBJECT_DETECTION)
            return True
        
        # Check for home automation keywords
        if any(keyword in user_input for keyword in Config.MODE_KEYWORDS["home_automation"]):
            self.switch_mode(Mode.HOME_AUTOMATION)
            return True
        
        return False
    
    def _handle_mode_specific_input(self, user_input: str) -> str:
        """Handle input based on current mode"""
        if self.current_mode == Mode.CHAT:
            return self._chat_response(user_input)
        elif self.current_mode == Mode.OBJECT_DETECTION:
            return self._object_detection_response(user_input)
        elif self.current_mode == Mode.HOME_AUTOMATION:
            return self._home_automation_response(user_input)
        else:
            return "Unknown mode. Switching to chat mode."
    
    def _chat_response(self, user_input: str) -> str:
        """Generate response in chat mode"""
        # Add context about available capabilities
        context = "You can help with general conversation, object detection, and home automation. The user can switch modes by saying 'switch to object detection' or 'switch to home automation'."
        
        return self.llm.generate_response(user_input, context)
    
    def _object_detection_response(self, user_input: str) -> str:
        """Handle object detection mode"""
        user_input_lower = user_input.lower()
        
        if any(word in user_input_lower for word in ["what", "see", "detect", "objects"]):
            return self.object_detection.get_detection_summary()
        
        elif "capture" in user_input_lower or "photo" in user_input_lower:
            frame = self.object_detection.capture_image()
            if frame is not None:
                return "I've captured an image. I can see objects in the frame."
            else:
                return "Sorry, I couldn't capture an image right now."
        
        else:
            # Use LLM to generate response with object detection context
            detection_summary = self.object_detection.get_detection_summary()
            context = f"Current camera view: {detection_summary}"
            return self.llm.generate_response(user_input, context)
    
    def _home_automation_response(self, user_input: str) -> str:
        """Handle home automation mode"""
        user_input_lower = user_input.lower()
        
        if any(word in user_input_lower for word in ["status", "state", "what"]):
            return self.home_automation.get_status_summary()
        
        elif any(word in user_input_lower for word in ["turn", "switch", "control"]):
            return self.home_automation.execute_command(user_input)
        
        else:
            # Use LLM to generate response with home automation context
            devices = self.home_automation.get_devices()
            if devices:
                device_list = ", ".join([f"{d.name} ({d.type})" for d in devices])
                context = f"Available devices: {device_list}. You can control them by saying 'turn on the light' or 'switch off the fan'."
            else:
                context = "No smart devices are currently connected."
            
            return self.llm.generate_response(user_input, context)
    
    def _speak_and_print(self, text: str):
        """Speak the text and print it to console"""
        print(f"{Fore.GREEN}Assistant: {text}{Style.RESET_ALL}")
        
        # Speak the text if voice is available
        if self.voice.is_voice_available():
            self.voice.speak_async(text)
    
    def _show_help(self):
        """Show help information"""
        help_text = f"""
{Fore.CYAN}🤖 AI Assistant Commands{Style.RESET_ALL}

{Fore.YELLOW}Mode Switching:{Style.RESET_ALL}
• "Switch to chat mode" - General conversation
• "Switch to object detection" - Use camera to detect objects
• "Switch to home automation" - Control smart devices

{Fore.YELLOW}Object Detection Commands:{Style.RESET_ALL}
• "What do you see?" - Describe objects in camera view
• "Take a photo" - Capture current image

{Fore.YELLOW}Home Automation Commands:{Style.RESET_ALL}
• "Turn on the light" - Control smart lights
• "Switch off the fan" - Control smart fans
• "What's the status?" - Check device states

{Fore.YELLOW}General Commands:{Style.RESET_ALL}
• "help" - Show this help message
• "status" - Show system status
• "exit" - Quit the assistant

{Fore.BLUE}Current Mode: {self.current_mode.value.upper()}{Style.RESET_ALL}
"""
        print(help_text)
    
    def _show_status(self):
        """Show system status"""
        status_text = f"""
{Fore.CYAN}📊 System Status{Style.RESET_ALL}

{Fore.GREEN}Modules:{Style.RESET_ALL}
• LLM: {'✅ Available' if self.llm.is_available() else '❌ Not available'}
• Voice: {'✅ Available' if self.voice.is_voice_available() else '❌ Not available'}
• Object Detection: {'✅ Available' if self.object_detection.is_available() else '❌ Not available'}
• Home Automation: {'✅ Available' if self.home_automation.is_available() else '❌ Not available'}

{Fore.YELLOW}Current Mode: {self.current_mode.value.upper()}{Style.RESET_ALL}
"""
        print(status_text)
    
    def start_voice_input(self):
        """Start listening for voice input"""
        if not self.voice.is_voice_available():
            print(f"{Fore.RED}Voice input not available{Style.RESET_ALL}")
            return
        
        print(f"{Fore.BLUE}🎤 Voice input activated. Speak to interact!{Style.RESET_ALL}")
        self.is_voice_active = True
        
        def voice_callback(text):
            print(f"{Fore.MAGENTA}🎤 Heard: {text}{Style.RESET_ALL}")
            self.process_input(text)
        
        self.voice.start_listening(voice_callback)
    
    def stop_voice_input(self):
        """Stop listening for voice input"""
        if self.is_voice_active:
            self.voice.stop_listening()
            self.is_voice_active = False
            print(f"{Fore.BLUE}🎤 Voice input deactivated{Style.RESET_ALL}")
    
    def cleanup(self):
        """Clean up resources"""
        self.logger.info("Cleaning up AI Assistant...")
        
        # Stop voice input
        self.stop_voice_input()
        
        # Stop object detection
        if self.current_mode == Mode.OBJECT_DETECTION:
            self.object_detection.stop_detection()
        
        # Close MQTT connection
        if self.home_automation.mqtt_client:
            self.home_automation.mqtt_client.loop_stop()
            self.home_automation.mqtt_client.disconnect()
        
        self.logger.info("Cleanup completed")

def main():
    assistant = AIAssistant()
    
    try:
        print(f"{Fore.CYAN}Starting AI Assistant...{Style.RESET_ALL}")
        print(f"{Fore.BLUE}Type 'voice' to enable voice input, 'help' for commands, or 'exit' to quit{Style.RESET_ALL}\n")
        
        while True:
            try:
                user_input = input(f"{Fore.YELLOW}You ({assistant.current_mode.value}): {Style.RESET_ALL}").strip()
                
                if user_input.lower() == 'exit':
                    break
                elif user_input.lower() == 'voice':
                    if assistant.is_voice_active:
                        assistant.stop_voice_input()
                    else:
                        assistant.start_voice_input()
                    continue
                elif user_input.lower() == 'text':
                    assistant.stop_voice_input()
                    continue
                
                assistant.process_input(user_input)
                
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}Interrupted by user{Style.RESET_ALL}")
                break
            except Exception as e:
                print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
    
    finally:
        assistant.cleanup()
        print(f"\n{Fore.CYAN}Goodbye! 👋{Style.RESET_ALL}")

if __name__ == "__main__":
    main()