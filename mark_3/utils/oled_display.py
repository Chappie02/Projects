"""
OLED Display Utilities
Handles 0.96-inch SSD1306 OLED display via I2C for status display.
"""

import time
import threading
from typing import Optional
try:
    from board import SCL, SDA
    import busio
    from adafruit_ssd1306 import SSD1306_I2C
    from PIL import Image, ImageDraw, ImageFont
    OLED_AVAILABLE = True
except ImportError:
    OLED_AVAILABLE = False
    print("⚠️  OLED display libraries not available. Install with: pip install adafruit-circuitpython-ssd1306")


class OLEDDisplay:
    """Manages SSD1306 OLED display via I2C."""
    
    def __init__(self, width=128, height=64, i2c_address=0x3C):
        """
        Initialize OLED display.
        
        Args:
            width: Display width in pixels
            height: Display height in pixels
            i2c_address: I2C address of the display
        """
        self.width = width
        self.height = height
        self.i2c_address = i2c_address
        self.display: Optional[SSD1306_I2C] = None
        self.image: Optional[Image.Image] = None
        self.draw: Optional[ImageDraw.ImageDraw] = None
        self.font_small = None
        self.font_large = None
        self.current_text = []
        self.lock = threading.Lock()
        
        if not OLED_AVAILABLE:
            print("⚠️  OLED display not available - running in simulation mode")
            return
        
        self._initialize_display()
    
    def _initialize_display(self):
        """Initialize the OLED display hardware."""
        try:
            # Initialize I2C bus
            i2c = busio.I2C(SCL, SDA)
            
            # Initialize OLED display
            self.display = SSD1306_I2C(self.width, self.height, i2c, addr=self.i2c_address)
            
            # Clear display
            self.display.fill(0)
            self.display.show()
            
            # Create image and draw object
            self.image = Image.new('1', (self.width, self.height))
            self.draw = ImageDraw.Draw(self.image)
            
            # Load fonts (use default if custom fonts not available)
            try:
                self.font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
                self.font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
            except:
                # Use default font if custom fonts not available
                self.font_small = ImageFont.load_default()
                self.font_large = ImageFont.load_default()
            
            print("✅ OLED display initialized successfully!")
            
        except Exception as e:
            print(f"⚠️  Error initializing OLED display: {e}")
            print("   Running in simulation mode")
            self.display = None
    
    def clear(self):
        """Clear the display."""
        with self.lock:
            if self.display and self.draw:
                self.draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)
                self.display.image(self.image)
                self.display.show()
            self.current_text = []
    
    def show_text(self, lines: list, clear_first=True):
        """
        Display text on the OLED.
        
        Args:
            lines: List of text lines to display (max 4-5 lines for 64px height)
            clear_first: Whether to clear display first
        """
        with self.lock:
            if not self.display or not self.draw:
                # Simulation mode - just print to console
                print("\n" + "=" * 20)
                for line in lines:
                    print(line)
                print("=" * 20)
                return
            
            if clear_first:
                self.clear()
            
            # Draw text lines
            y_offset = 2
            line_height = 12
            
            for i, line in enumerate(lines[:5]):  # Max 5 lines
                if line:
                    try:
                        self.draw.text((2, y_offset + i * line_height), 
                                     line[:20],  # Limit to 20 chars per line
                                     font=self.font_small, fill=255)
                    except Exception as e:
                        print(f"Error drawing text: {e}")
            
            # Update display
            try:
                self.display.image(self.image)
                self.display.show()
                self.current_text = lines
            except Exception as e:
                print(f"Error updating display: {e}")
    
    def show_status(self, mode: str, status: str = ""):
        """
        Display current mode and status.
        
        Args:
            mode: Current mode (e.g., "Chat Mode", "Object Mode")
            status: Status message (e.g., "Listening...", "Processing...")
        """
        lines = [
            "🤖 AI Assistant",
            "",
            mode[:18],
            status[:18] if status else ""
        ]
        self.show_text(lines)
    
    def show_listening(self):
        """Show listening status."""
        self.show_status("Voice Mode", "Listening...")
    
    def show_processing(self):
        """Show processing status."""
        self.show_status(self.current_text[2] if len(self.current_text) > 2 else "Processing", 
                        "Processing...")
    
    def show_chat_mode(self):
        """Show chat mode."""
        self.show_status("Chat Mode", "Ready")
    
    def show_object_mode(self):
        """Show object detection mode."""
        self.show_status("Object Mode", "Ready")
    
    def show_exiting(self):
        """Show exiting status."""
        self.show_status("Exiting...", "Goodbye!")
    
    def show_wake_word_detected(self):
        """Show wake word detected."""
        self.show_status("Wake Word", "Detected!")
        time.sleep(1)
    
    def animate_loading(self, duration=2.0):
        """
        Show loading animation.
        
        Args:
            duration: Animation duration in seconds
        """
        frames = ["|", "/", "-", "\\"]
        start_time = time.time()
        frame_index = 0
        
        while time.time() - start_time < duration:
            status = f"Loading{frames[frame_index % len(frames)]}"
            if len(self.current_text) > 2:
                self.show_status(self.current_text[2], status)
            else:
                self.show_status("Loading", status)
            
            frame_index += 1
            time.sleep(0.2)
    
    def cleanup(self):
        """Clean up display resources."""
        try:
            if self.display:
                self.clear()
                self.display.fill(0)
                self.display.show()
        except Exception as e:
            print(f"Error cleaning up display: {e}")


if __name__ == "__main__":
    # Test OLED display
    display = OLEDDisplay()
    
    if display.display:
        display.show_status("Test Mode", "Starting...")
        time.sleep(2)
        
        display.show_chat_mode()
        time.sleep(2)
        
        display.show_listening()
        time.sleep(2)
        
        display.show_object_mode()
        time.sleep(2)
        
        display.show_exiting()
        time.sleep(2)
        
        display.cleanup()
    else:
        print("OLED display not available for testing")

