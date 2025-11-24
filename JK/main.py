import time
import sys
import argparse
from typing import Optional

from app.core import config
from app.core.logger import setup_logger
from app.hardware.drivers import DisplayManager, ButtonHandler
from app.services.audio import AudioManager
from app.services.vision import VisionEngine
from app.services.memory import RAGEngine
from app.services.llm import LLMEngine

logger = setup_logger("main")

# --- States ---
STATE_MENU = "MENU"
STATE_CHAT_LISTENING = "CHAT_LISTENING"
STATE_CHAT_PROCESSING = "CHAT_PROCESSING"
STATE_VISION_STANDBY = "VISION_STANDBY"
STATE_VISION_ANALYZING = "VISION_ANALYZING"

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Raspberry Pi 5 AI Assistant")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--mock-hardware", action="store_true", help="Run with mock hardware (if supported)")
    return parser.parse_args()

def main() -> None:
    args = parse_args()
    
    if args.debug:
        import logging
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled.")

    logger.info("Starting AI Assistant...")
    
    # Initialize Hardware
    try:
        display = DisplayManager(mock=args.mock_hardware)
        buttons = ButtonHandler(mock=args.mock_hardware)
    except Exception as e:
        logger.critical(f"Hardware Initialization Failed: {e}")
        sys.exit(1)
    
    # Initialize AI Modules
    # Note: We initialize these lazily or upfront depending on design. 
    # Here we instantiate the managers, but they might lazy-load heavy models.
    audio = AudioManager()
    vision = VisionEngine()
    memory = RAGEngine()
    llm = LLMEngine()

    current_state = STATE_MENU
    
    logger.info("System Ready. Starting Main Loop.")
    display.show_text("AI Assistant", "Select Mode:\nK2: Chat\nK3: Vision")

    try:
        while True:
            # --- Event Handling ---
            
            # K2 Pressed -> Switch to Chat Mode
            if buttons.is_pressed(config.PIN_K2_CHAT):
                logger.info("Switching to Chat Mode")
                current_state = STATE_CHAT_LISTENING
                time.sleep(0.5) # Debounce
                
                # Chat Workflow
                display.show_text("Chat Mode", "Listening...")
                
                user_input: Optional[str] = audio.listen()
                
                if user_input:
                    display.show_text("Chat Mode", "Thinking...")
                    
                    # RAG
                    context = memory.retrieve(user_input)
                    
                    # LLM
                    response = llm.generate(user_input, context)
                    
                    # Speak
                    display.show_text("Chat Mode", "Speaking...")
                    audio.speak(response)
                    
                    # Save to memory
                    memory.add_memory(f"User: {user_input}\nAI: {response}")
                else:
                    display.show_text("Chat Mode", "Didn't hear you.")
                    time.sleep(2)

                # Standby Loop
                display.show_text("Chat Mode", "Press K1 to Speak\nK2/K3 to Switch")
                while True:
                    if buttons.is_pressed(config.PIN_K1_TRIGGER):
                        current_state = STATE_CHAT_LISTENING
                        break
                    if buttons.is_pressed(config.PIN_K2_CHAT):
                        current_state = STATE_CHAT_LISTENING
                        break
                    if buttons.is_pressed(config.PIN_K3_VISION):
                        current_state = STATE_VISION_STANDBY
                        break
                    time.sleep(0.1)
                
                if current_state == STATE_VISION_STANDBY:
                    pass # Fall through
                else:
                    continue 

            # K3 Pressed -> Switch to Vision Mode
            if buttons.is_pressed(config.PIN_K3_VISION) or current_state == STATE_VISION_STANDBY:
                logger.info("Switching to Vision Mode")
                current_state = STATE_VISION_STANDBY
                display.show_text("Vision Mode", "Press K1 to Capture")
                time.sleep(0.5) 

                # Wait for K1
                while True:
                    if buttons.is_pressed(config.PIN_K1_TRIGGER):
                        # Capture
                        display.show_text("Vision Mode", "Analyzing...")
                        description = vision.capture_and_analyze()
                        
                        display.show_text("Vision Mode", "Speaking...")
                        audio.speak(description)
                        
                        # Return to "Capture Image" state
                        display.show_text("Vision Mode", "Press K1 to Capture")
                        time.sleep(0.5) 
                    
                    if buttons.is_pressed(config.PIN_K2_CHAT):
                        current_state = STATE_CHAT_LISTENING 
                        break
                        
                    time.sleep(0.1)

            time.sleep(0.1)

    except KeyboardInterrupt:
        logger.info("Exiting...")
        display.clear()
        buttons.cleanup()
        vision.cleanup()
    except Exception as e:
        logger.critical(f"Unhandled Exception: {e}", exc_info=True)
        display.show_text("Error", "System Failure")
        buttons.cleanup()
        vision.cleanup()

if __name__ == "__main__":
    main()
