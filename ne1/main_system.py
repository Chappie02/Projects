import logging
import threading
import time
import signal
import sys
from config import Config
from llm_core import LLMCore
from object_detection import ObjectDetection
from home_automation import HomeAutomation
from audio_manager import AudioManager

class MainSystem:
    def __init__(self):
        self.config = Config()
        self.setup_logging()
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing Raspberry Pi 5 LLM System...")
        
        # Initialize all modules
        self.llm = LLMCore()
        self.object_detection = ObjectDetection()
        self.home_automation = HomeAutomation()
        self.audio_manager = AudioManager()
        
        # System state
        self.is_running = False
        self.current_mode = "main_chat"
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.logger.info("System initialization completed")
    
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=getattr(logging, self.config.LOG_LEVEL),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.config.LOG_FILE),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def _signal_handler(self, signum, frame):
        """Handle system shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.shutdown()
        sys.exit(0)
    
    def initialize_system(self):
        """Initialize all system components"""
        try:
            self.logger.info("Starting system initialization...")
            
            # Initialize object detection
            if self.object_detection.initialize_camera():
                self.object_detection.start_detection()
                self.logger.info("Object detection initialized and started")
            else:
                self.logger.warning("Object detection initialization failed")
            
            # Start continuous listening
            self.audio_manager.start_continuous_listening(self.process_voice_command)
            self.logger.info("Voice recognition started")
            
            # Initial greeting
            self.audio_manager.speak_text("Hello! I'm your Raspberry Pi 5 AI assistant. I can help you with conversation, object detection, and home automation. How can I help you today?")
            
            self.is_running = True
            self.logger.info("System initialization completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"System initialization failed: {e}")
            return False
    
    def process_voice_command(self, text):
        """Process voice commands and generate responses"""
        if not text or not self.is_running:
            return
        
        self.logger.info(f"Processing voice command: {text}")
        
        try:
            # Check for system commands first
            if self._is_system_command(text):
                self._handle_system_command(text)
                return
            
            # Get context based on current mode
            context = self._get_context()
            
            # Generate response using LLM
            response = self.llm.generate_response(text, context)
            
            # Handle mode-specific actions
            self._handle_mode_actions(text, response)
            
            # Speak the response
            self.audio_manager.speak_text(response)
            
        except Exception as e:
            self.logger.error(f"Error processing voice command: {e}")
            self.audio_manager.speak_text("I'm sorry, I encountered an error processing your request.")
    
    def _is_system_command(self, text):
        """Check if the command is a system-level command"""
        system_commands = [
            "shutdown", "stop", "exit", "quit", "goodbye",
            "restart", "reboot", "status", "help"
        ]
        return any(cmd in text.lower() for cmd in system_commands)
    
    def _handle_system_command(self, text):
        """Handle system-level commands"""
        text_lower = text.lower()
        
        if any(cmd in text_lower for cmd in ["shutdown", "stop", "exit", "quit", "goodbye"]):
            self.audio_manager.speak_text("Goodbye! Shutting down the system.")
            self.shutdown()
        elif "restart" in text_lower or "reboot" in text_lower:
            self.audio_manager.speak_text("Restarting the system.")
            self.shutdown()
            # Note: Actual restart would require system-level implementation
        elif "status" in text_lower:
            self._report_system_status()
        elif "help" in text_lower:
            self._provide_help()
    
    def _get_context(self):
        """Get context information based on current mode"""
        context = {}
        
        if self.llm.get_current_mode() == "object_detection":
            context["objects"] = self.object_detection.get_current_objects()
        elif self.llm.get_current_mode() == "home_automation":
            context["devices"] = self.home_automation.get_device_status()
            context["motion"] = self.home_automation.get_motion_status()
        
        return context
    
    def _handle_mode_actions(self, text, response):
        """Handle mode-specific actions after LLM response"""
        current_mode = self.llm.get_current_mode()
        
        if current_mode == "home_automation":
            # Parse home automation commands
            self._parse_home_automation_commands(text)
        elif current_mode == "object_detection":
            # Handle object detection specific actions
            self._handle_object_detection_actions(text)
    
    def _parse_home_automation_commands(self, text):
        """Parse and execute home automation commands"""
        text_lower = text.lower()
        
        # Light control
        if "light" in text_lower:
            if "on" in text_lower or "turn on" in text_lower:
                result = self.home_automation.control_device("light", "turn on")
                self.audio_manager.speak_text(result)
            elif "off" in text_lower or "turn off" in text_lower:
                result = self.home_automation.control_device("light", "turn off")
                self.audio_manager.speak_text(result)
        
        # Fan control
        elif "fan" in text_lower:
            if "on" in text_lower or "turn on" in text_lower:
                result = self.home_automation.control_device("fan", "turn on")
                self.audio_manager.speak_text(result)
            elif "off" in text_lower or "turn off" in text_lower:
                result = self.home_automation.control_device("fan", "turn off")
                self.audio_manager.speak_text(result)
        
        # Door control
        elif "door" in text_lower:
            if "lock" in text_lower:
                result = self.home_automation.control_device("door", "lock")
                self.audio_manager.speak_text(result)
            elif "unlock" in text_lower:
                result = self.home_automation.control_device("door", "unlock")
                self.audio_manager.speak_text(result)
    
    def _handle_object_detection_actions(self, text):
        """Handle object detection specific actions"""
        text_lower = text.lower()
        
        if "scan" in text_lower or "detect" in text_lower or "what do you see" in text_lower:
            objects = self.object_detection.detect_single_frame()
            if objects:
                object_list = ", ".join([f"{obj['name']} with {obj['confidence']:.2f} confidence" for obj in objects])
                self.audio_manager.speak_text(f"I can see: {object_list}")
            else:
                self.audio_manager.speak_text("I don't see any objects in the current view.")
    
    def _report_system_status(self):
        """Report current system status"""
        status_text = f"Current mode: {self.llm.get_current_mode().replace('_', ' ')}. "
        
        if self.llm.get_current_mode() == "object_detection":
            objects = self.object_detection.get_current_objects()
            if objects:
                status_text += f"Detected objects: {len(objects)}. "
            else:
                status_text += "No objects currently detected. "
        
        elif self.llm.get_current_mode() == "home_automation":
            devices = self.home_automation.get_device_status()
            active_devices = [device for device, state in devices.items() if state and device != "motion_detected"]
            if active_devices:
                status_text += f"Active devices: {', '.join(active_devices)}. "
            else:
                status_text += "No devices currently active. "
        
        status_text += "System is running normally."
        self.audio_manager.speak_text(status_text)
    
    def _provide_help(self):
        """Provide help information"""
        help_text = """
        I can help you with three main functions:
        1. General conversation - just talk to me normally
        2. Object detection - say 'detect objects' or 'what do you see' to analyze your surroundings
        3. Home automation - say 'home automation' to control lights, fans, and door locks
        
        You can switch between modes by mentioning keywords like 'detect', 'vision', 'home', 'automation', or 'chat'.
        Say 'status' to check system status or 'help' for this information.
        """
        self.audio_manager.speak_text(help_text)
    
    def run(self):
        """Main system run loop"""
        if not self.initialize_system():
            self.logger.error("Failed to initialize system")
            return
        
        self.logger.info("System is running. Press Ctrl+C to stop.")
        
        try:
            while self.is_running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Received keyboard interrupt")
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Graceful system shutdown"""
        self.logger.info("Starting system shutdown...")
        self.is_running = False
        
        # Stop all components
        self.audio_manager.stop_continuous_listening()
        self.object_detection.stop_detection()
        
        # Cleanup
        self.audio_manager.cleanup()
        self.home_automation.cleanup()
        
        self.logger.info("System shutdown completed")

def main():
    """Main entry point"""
    system = MainSystem()
    system.run()

if __name__ == "__main__":
    main() 