"""
Display Utilities
Handles OLED display (SSD1306) on I2C for Raspberry Pi.
"""

import time
from typing import Optional

try:
    import board
    import adafruit_ssd1306
    from PIL import Image, ImageDraw, ImageFont
    DISPLAY_AVAILABLE = True
except ImportError:
    DISPLAY_AVAILABLE = False
    board = None
    adafruit_ssd1306 = None
    Image = None
    ImageDraw = None
    ImageFont = None


class DisplayManager:
    """Manages OLED display operations."""
    
    def __init__(self, sda_pin=2, scl_pin=3, width=128, height=64):
        """
        Initialize display manager.
        
        Args:
            sda_pin: SDA GPIO pin (default: GPIO 2)
            scl_pin: SCL GPIO pin (default: GPIO 3)
            width: Display width in pixels (default: 128)
            height: Display height in pixels (default: 64)
        """
        self.sda_pin = sda_pin
        self.scl_pin = scl_pin
        self.width = width
        self.height = height
        self.display: Optional[adafruit_ssd1306.SSD1306_I2C] = None
        self.image: Optional[Image.Image] = None
        self.draw: Optional[ImageDraw.ImageDraw] = None
        self.font: Optional[ImageFont.FreeTypeFont] = None
        self.font_small: Optional[ImageFont.FreeTypeFont] = None
        
        if DISPLAY_AVAILABLE:
            self._initialize_display()
        else:
            print("⚠️  Display libraries not available. Display functionality disabled.")
    
    def _initialize_display(self):
        """Initialize the OLED display."""
        try:
            # Create I2C interface
            i2c = board.I2C()
            
            # Create SSD1306 display instance
            self.display = adafruit_ssd1306.SSD1306_I2C(
                self.width, 
                self.height, 
                i2c, 
                addr=0x3C
            )
            
            # Create image and drawing objects
            self.image = Image.new('1', (self.width, self.height))
            self.draw = ImageDraw.Draw(self.image)
            
            # Try to load fonts
            try:
                self.font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
                self.font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
            except:
                # Fallback to default font
                self.font = ImageFont.load_default()
                self.font_small = ImageFont.load_default()
            
            # Clear and show initial message
            self.clear()
            self.show_text("Initializing...")
            print("✅ OLED display initialized successfully!")
            
        except Exception as e:
            print(f"❌ Error initializing display: {e}")
            self.display = None
    
    def clear(self):
        """Clear the display."""
        if not self.display:
            return
        
        try:
            self.draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)
            self.display.image(self.image)
            self.display.show()
        except Exception as e:
            print(f"⚠️  Error clearing display: {e}")
    
    def show_text(self, text: str, line: int = 0, clear_first: bool = True):
        """
        Show text on the display.
        
        Args:
            text: Text to display
            line: Line number (0-3 for 4 lines)
            clear_first: Whether to clear display first
        """
        if not self.display:
            print(f"[Display] {text}")
            return
        
        try:
            if clear_first:
                self.clear()
            
            # Split text into lines if too long
            max_chars = 16  # Approximate characters per line
            lines = []
            words = text.split()
            current_line = ""
            
            for word in words:
                if len(current_line + word) <= max_chars:
                    current_line += word + " "
                else:
                    if current_line:
                        lines.append(current_line.strip())
                    current_line = word + " "
            if current_line:
                lines.append(current_line.strip())
            
            # Display lines
            y_offset = line * 16
            for i, line_text in enumerate(lines[:4]):  # Max 4 lines
                y_pos = y_offset + (i * 16)
                if y_pos < self.height:
                    self.draw.text((0, y_pos), line_text, font=self.font, fill=255)
            
            self.display.image(self.image)
            self.display.show()
            
        except Exception as e:
            print(f"⚠️  Error showing text: {e}")
    
    def show_multiline(self, lines: list, clear_first: bool = True):
        """
        Show multiple lines of text.
        
        Args:
            lines: List of text lines (max 4)
            clear_first: Whether to clear display first
        """
        if not self.display:
            for line in lines:
                print(f"[Display] {line}")
            return
        
        try:
            if clear_first:
                self.clear()
            
            for i, line_text in enumerate(lines[:4]):  # Max 4 lines
                y_pos = i * 16
                if y_pos < self.height:
                    # Truncate if too long
                    if len(line_text) > 16:
                        line_text = line_text[:13] + "..."
                    self.draw.text((0, y_pos), line_text, font=self.font, fill=255)
            
            self.display.image(self.image)
            self.display.show()
            
        except Exception as e:
            print(f"⚠️  Error showing multiline: {e}")
    
    def show_listening(self):
        """Show listening status."""
        self.show_text("Listening...", clear_first=True)
    
    def show_processing(self):
        """Show processing status."""
        self.show_text("Processing...", clear_first=True)
    
    def show_chat_mode(self):
        """Show chat mode activated."""
        self.show_multiline(["Chat Mode", "Press K1 to", "start chat"], clear_first=True)
    
    def show_object_mode(self):
        """Show object detection mode activated."""
        self.show_multiline(["Object Mode", "Press K3 to", "capture"], clear_first=True)
    
    def show_capture_image(self):
        """Show capture image prompt."""
        self.show_text("Capture Image", clear_first=True)
    
    def show_detecting(self):
        """Show detecting status."""
        self.show_text("Detecting...", clear_first=True)
    
    def is_available(self) -> bool:
        """Check if display is available."""
        return self.display is not None and DISPLAY_AVAILABLE
    
    def cleanup(self):
        """Clean up display resources."""
        if self.display:
            try:
                self.clear()
                self.display = None
            except:
                pass

