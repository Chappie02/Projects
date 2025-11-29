"""
GPIO Button Handler for Raspberry Pi 5
Handles three physical switches: K1, K2, K3
"""

import RPi.GPIO as GPIO
import logging
from enum import Enum
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class Button(Enum):
    """Button GPIO pin assignments"""
    K1 = 17  # Pin 11 - Select Chat Mode
    K2 = 27  # Pin 13 - Select Object Detection Mode
    K3 = 22  # Pin 15 - Hold to Speak / Press to Capture


class ButtonHandler:
    """Manages GPIO button inputs with callback support"""
    
    def __init__(self):
        """Initialize GPIO and button states"""
        self.callbacks: dict[Button, Optional[Callable]] = {
            Button.K1: None,
            Button.K2: None,
            Button.K3: None
        }
        self.button_states = {
            Button.K1: False,
            Button.K2: False,
            Button.K3: False
        }
        self._setup_gpio()
        logger.info("ButtonHandler initialized")
    
    def _setup_gpio(self):
        """Configure GPIO pins for buttons"""
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            
            # Setup all buttons as inputs with pull-up resistors
            for button in Button:
                GPIO.setup(button.value, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                # Add event detection for both rising and falling edges
                GPIO.add_event_detect(
                    button.value,
                    GPIO.BOTH,
                    callback=lambda channel, btn=button: self._button_callback(btn, channel),
                    bouncetime=50
                )
            
            logger.info("GPIO buttons configured successfully")
        except Exception as e:
            logger.error(f"Error setting up GPIO: {e}")
            raise
    
    def _button_callback(self, button: Button, channel: int):
        """Internal callback for GPIO events"""
        try:
            # Read current state (LOW = pressed, HIGH = released due to pull-up)
            current_state = GPIO.input(channel) == GPIO.LOW
            
            # Only trigger if state changed
            if current_state != self.button_states[button]:
                self.button_states[button] = current_state
                
                if self.callbacks[button]:
                    try:
                        self.callbacks[button](button, current_state)
                    except Exception as e:
                        logger.error(f"Error in button callback for {button.name}: {e}")
        except Exception as e:
            logger.error(f"Error in button callback: {e}")
    
    def register_callback(self, button: Button, callback: Callable[[Button, bool], None]):
        """
        Register a callback for a button
        
        Args:
            button: Button enum (K1, K2, or K3)
            callback: Function that takes (button, is_pressed) as arguments
        """
        self.callbacks[button] = callback
        logger.info(f"Callback registered for {button.name}")
    
    def unregister_callback(self, button: Button):
        """Remove callback for a button"""
        self.callbacks[button] = None
        logger.info(f"Callback unregistered for {button.name}")
    
    def read_button(self, button: Button) -> bool:
        """
        Read current state of a button
        
        Args:
            button: Button enum
            
        Returns:
            True if pressed, False if released
        """
        try:
            return GPIO.input(button.value) == GPIO.LOW
        except Exception as e:
            logger.error(f"Error reading button {button.name}: {e}")
            return False
    
    def cleanup(self):
        """Clean up GPIO resources"""
        try:
            GPIO.cleanup()
            logger.info("GPIO cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up GPIO: {e}")

