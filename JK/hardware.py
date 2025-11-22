"""
Hardware interface module for OLED display and GPIO buttons
Handles display updates and button interrupt callbacks
"""

import RPi.GPIO as GPIO
import time
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306
from PIL import Image, ImageDraw, ImageFont
import config


class HardwareController:
    """Manages OLED display and GPIO button inputs"""
    
    def __init__(self):
        """Initialize OLED display and GPIO buttons"""
        self.device = None
        self.button_callbacks = {
            config.GPIO_BUTTON_K1: None,
            config.GPIO_BUTTON_K2: None,
            config.GPIO_BUTTON_K3: None
        }
        self._init_gpio()
        self._init_display()
        
    def _init_gpio(self):
        """Initialize GPIO pins for buttons"""
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            
            # Setup button pins as inputs with pull-up resistors
            for pin in [config.GPIO_BUTTON_K1, config.GPIO_BUTTON_K2, config.GPIO_BUTTON_K3]:
                GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                # Add event detection for falling edge (button press)
                GPIO.add_event_detect(pin, GPIO.FALLING, 
                                     callback=self._button_callback,
                                     bouncetime=300)
        except Exception as e:
            print(f"Error initializing GPIO: {e}")
            raise
    
    def _init_display(self):
        """Initialize OLED display via I2C"""
        try:
            serial = i2c(port=1, address=config.OLED_I2C_ADDRESS)
            self.device = ssd1306(serial, width=config.OLED_WIDTH, 
                                  height=config.OLED_HEIGHT)
            self.device.clear()
            print("OLED display initialized successfully")
        except Exception as e:
            print(f"Error initializing OLED display: {e}")
            print("Continuing without display...")
            self.device = None
    
    def _button_callback(self, channel):
        """Internal callback for button presses"""
        if channel in self.button_callbacks:
            callback = self.button_callbacks[channel]
            if callback:
                try:
                    callback(channel)
                except Exception as e:
                    print(f"Error in button callback: {e}")
    
    def register_button_callback(self, pin, callback):
        """
        Register a callback function for a button press
        
        Args:
            pin: GPIO pin number (config.GPIO_BUTTON_K1, K2, or K3)
            callback: Function to call when button is pressed
        """
        if pin in self.button_callbacks:
            self.button_callbacks[pin] = callback
        else:
            raise ValueError(f"Invalid button pin: {pin}")
    
    def display_text(self, text, line=0, clear=True):
        """
        Display text on OLED screen
        
        Args:
            text: Text to display
            line: Line number (0-3 for 4 lines)
            clear: Whether to clear display first
        """
        if not self.device:
            print(f"Display: {text}")
            return
        
        try:
            with canvas(self.device) as draw:
                if clear:
                    draw.rectangle((0, 0, config.OLED_WIDTH, config.OLED_HEIGHT), 
                                  outline=0, fill=0)
                
                # Simple font rendering (built-in)
                y_offset = line * 16
                draw.text((0, y_offset), text, fill=255)
        except Exception as e:
            print(f"Error updating display: {e}")
    
    def display_multiline(self, lines, clear=True):
        """
        Display multiple lines of text
        
        Args:
            lines: List of strings to display (max 4 lines)
            clear: Whether to clear display first
        """
        if not self.device:
            for line in lines:
                print(f"Display: {line}")
            return
        
        try:
            with canvas(self.device) as draw:
                if clear:
                    draw.rectangle((0, 0, config.OLED_WIDTH, config.OLED_HEIGHT), 
                                  outline=0, fill=0)
                
                for i, line in enumerate(lines[:4]):  # Max 4 lines
                    y_offset = i * 16
                    draw.text((0, y_offset), line[:20], fill=255)  # Max 20 chars per line
        except Exception as e:
            print(f"Error updating display: {e}")
    
    def clear_display(self):
        """Clear the OLED display"""
        if self.device:
            try:
                self.device.clear()
            except Exception as e:
                print(f"Error clearing display: {e}")
    
    def cleanup(self):
        """Cleanup GPIO and display resources"""
        try:
            GPIO.cleanup()
            if self.device:
                self.device.clear()
        except Exception as e:
            print(f"Error during cleanup: {e}")

