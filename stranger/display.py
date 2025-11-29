"""
OLED Display Handler for Adafruit SSD1306
Manages user interface messages on the OLED screen
"""

import logging
import time
from typing import Optional
import board
import digitalio
from adafruit_ssd1306 import SSD1306_I2C
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)


class Display:
    """Manages OLED display output"""
    
    def __init__(self, width: int = 128, height: int = 64):
        """
        Initialize OLED display
        
        Args:
            width: Display width in pixels (default 128)
            height: Display height in pixels (default 64)
        """
        self.width = width
        self.height = height
        self.display: Optional[SSD1306_I2C] = None
        self.image: Optional[Image.Image] = None
        self.draw: Optional[ImageDraw.ImageDraw] = None
        self.font: Optional[ImageFont.ImageFont] = None
        
        try:
            self._setup_display()
            logger.info("Display initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing display: {e}")
            raise
    
    def _setup_display(self):
        """Configure I2C and OLED display"""
        try:
            # Initialize I2C
            i2c = board.I2C()
            
            # Initialize display (SSD1306)
            self.display = SSD1306_I2C(
                self.width,
                self.height,
                i2c,
                addr=0x3C  # Common I2C address for SSD1306
            )
            
            # Create image and drawing object
            self.image = Image.new("1", (self.width, self.height))
            self.draw = ImageDraw.Draw(self.image)
            
            # Try to load default font, fallback to built-in if not available
            try:
                self.font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
            except:
                self.font = ImageFont.load_default()
            
            # Clear display
            self.display.fill(0)
            self.display.show()
            
        except Exception as e:
            logger.error(f"Display setup error: {e}")
            raise
    
    def clear(self):
        """Clear the display"""
        if self.display and self.draw:
            try:
                self.draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)
                self.display.image(self.image)
                self.display.show()
            except Exception as e:
                logger.error(f"Error clearing display: {e}")
    
    def show_text(self, lines: list[str], clear_first: bool = True):
        """
        Display multiple lines of text
        
        Args:
            lines: List of strings to display (max ~4-5 lines for 64px height)
            clear_first: Whether to clear display before showing text
        """
        if not self.display or not self.draw:
            logger.warning("Display not initialized")
            return
        
        try:
            if clear_first:
                self.clear()
            
            # Calculate line height
            line_height = 12
            y_offset = 2
            
            # Draw each line
            for i, line in enumerate(lines[:5]):  # Max 5 lines
                y_pos = y_offset + (i * line_height)
                if y_pos + line_height <= self.height:
                    self.draw.text((2, y_pos), line, font=self.font, fill=255)
            
            # Update display
            self.display.image(self.image)
            self.display.show()
            
        except Exception as e:
            logger.error(f"Error showing text: {e}")
    
    def show_boot_screen(self):
        """Display boot screen with mode selection"""
        self.show_text([
            "Select Mode:",
            "",
            "K1 Chat Mode",
            "K2 Object Mode"
        ])
    
    def show_chat_mode(self):
        """Display chat mode screen"""
        self.show_text([
            "Chat Mode",
            "",
            "Hold K3 to Speak"
        ])
    
    def show_listening(self):
        """Display listening indicator"""
        self.show_text([
            "Chat Mode",
            "",
            "Listening..."
        ])
    
    def show_processing(self):
        """Display processing indicator"""
        self.show_text([
            "Chat Mode",
            "",
            "Processing..."
        ])
    
    def show_object_mode(self):
        """Display object detection mode screen"""
        self.show_text([
            "Object Mode",
            "",
            "Press K3 to Capture"
        ])
    
    def show_capturing(self):
        """Display capturing indicator"""
        self.show_text([
            "Object Mode",
            "",
            "Capturing Image..."
        ])
    
    def show_detecting(self):
        """Display detecting indicator"""
        self.show_text([
            "Object Mode",
            "",
            "Detecting Object..."
        ])
    
    def cleanup(self):
        """Clean up display resources"""
        try:
            if self.display:
                self.clear()
            logger.info("Display cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up display: {e}")

