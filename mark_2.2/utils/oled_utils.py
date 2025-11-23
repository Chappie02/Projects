"""
OLED Display Utility
Handles 0.96 inch OLED display (SSD1306) with K1, K2, K3 buttons and rotation support.
"""

import time
import threading
from typing import Optional, Callable

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    GPIO = None
    print("Warning: RPi.GPIO not available. Install with: pip install RPi.GPIO")

try:
    from luma.core.interface.serial import i2c
    from luma.core.render import canvas
    from luma.oled.device import ssd1306
    OLED_AVAILABLE = True
except ImportError:
    OLED_AVAILABLE = False
    print("Warning: luma.oled not available. Install with: pip install luma.oled")


class OLEDDisplay:
    """Manages 0.96 inch OLED display with button support."""
    
    def __init__(self, 
                 i2c_port=1,
                 i2c_address=0x3C,
                 k1_pin=18,  # GPIO pin for K1 button
                 k2_pin=23,  # GPIO pin for K2 button
                 k3_pin=24,  # GPIO pin for K3 button
                 rotation=180):  # 180 degrees for 360-degree rotated display
        """Initialize OLED display with buttons."""
        self.i2c_port = i2c_port
        self.i2c_address = i2c_address
        self.k1_pin = k1_pin
        self.k2_pin = k2_pin
        self.k3_pin = k3_pin
        self.rotation = rotation  # 0, 90, 180, or 270
        
        self.device: Optional[object] = None
        self.k1_callback: Optional[Callable] = None
        self.k2_callback: Optional[Callable] = None
        self.k3_callback: Optional[Callable] = None
        
        self.is_running = False
        self.button_thread: Optional[threading.Thread] = None
        
        self.current_mode = "Ready"
        self.status_text = ""
        
        if OLED_AVAILABLE:
            self._initialize_display()
            self._initialize_buttons()
        else:
            print("⚠️  OLED display libraries not available. Install with: pip install luma.oled")
            print("⚠️  Display will not function. Continuing without OLED...")
    
    def _initialize_display(self):
        """Initialize the OLED display via I2C."""
        try:
            # Create I2C interface
            serial = i2c(port=self.i2c_port, address=self.i2c_address)
            
            # Create SSD1306 device with rotation
            self.device = ssd1306(serial, width=128, height=64, rotate=self.rotation)
            
            print(f"✅ OLED display initialized (rotation: {self.rotation}°)")
            self._show_startup_message()
            
        except Exception as e:
            print(f"❌ Error initializing OLED display: {e}")
            print("Please check I2C connections (SDA, SCL) and power (VCC, GND)")
            self.device = None
    
    def _initialize_buttons(self):
        """Initialize GPIO pins for K1, K2, K3 buttons."""
        if not GPIO_AVAILABLE or GPIO is None:
            print("⚠️  GPIO not available. Buttons will not function.")
            return
        
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            
            # Setup button pins as input with pull-up resistors
            GPIO.setup(self.k1_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.k2_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.k3_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
            # Add event detection for buttons
            GPIO.add_event_detect(self.k1_pin, GPIO.FALLING, 
                                  callback=self._k1_pressed, bouncetime=300)
            GPIO.add_event_detect(self.k2_pin, GPIO.FALLING, 
                                  callback=self._k2_pressed, bouncetime=300)
            GPIO.add_event_detect(self.k3_pin, GPIO.FALLING, 
                                  callback=self._k3_pressed, bouncetime=300)
            
            print(f"✅ Buttons initialized: K1(GPIO{self.k1_pin}), K2(GPIO{self.k2_pin}), K3(GPIO{self.k3_pin})")
            
        except Exception as e:
            print(f"❌ Error initializing buttons: {e}")
    
    def _k1_pressed(self, channel):
        """Handle K1 button press."""
        if self.k1_callback:
            try:
                self.k1_callback()
            except Exception as e:
                print(f"Error in K1 callback: {e}")
    
    def _k2_pressed(self, channel):
        """Handle K2 button press."""
        if self.k2_callback:
            try:
                self.k2_callback()
            except Exception as e:
                print(f"Error in K2 callback: {e}")
    
    def _k3_pressed(self, channel):
        """Handle K3 button press."""
        if self.k3_callback:
            try:
                self.k3_callback()
            except Exception as e:
                print(f"Error in K3 callback: {e}")
    
    def set_k1_callback(self, callback: Callable):
        """Set callback function for K1 button."""
        self.k1_callback = callback
    
    def set_k2_callback(self, callback: Callable):
        """Set callback function for K2 button."""
        self.k2_callback = callback
    
    def set_k3_callback(self, callback: Callable):
        """Set callback function for K3 button."""
        self.k3_callback = callback
    
    def _show_startup_message(self):
        """Display startup message on OLED."""
        if not self.device:
            return
        
        try:
            with canvas(self.device) as draw:
                draw.text((0, 0), "AI Assistant", fill="white")
                draw.text((0, 15), "Initializing...", fill="white")
                draw.text((0, 30), "K1: Mode", fill="white")
                draw.text((0, 45), "K2: Speed", fill="white")
        except Exception as e:
            print(f"Error displaying startup message: {e}")
    
    def update_display(self, mode: str = None, status: str = None, info_lines: list = None):
        """Update the OLED display with current information."""
        if not self.device:
            return
        
        if mode:
            self.current_mode = mode
        if status:
            self.status_text = status
        
        try:
            with canvas(self.device) as draw:
                # Title/Mode (top line)
                mode_text = self.current_mode[:20]  # Limit to 20 chars
                draw.text((0, 0), mode_text, fill="white")
                
                # Status line
                if self.status_text:
                    status_text = self.status_text[:20]
                    draw.text((0, 15), status_text, fill="white")
                
                # Info lines (optional)
                y_offset = 30
                if info_lines:
                    for line in info_lines[:2]:  # Max 2 info lines
                        if y_offset >= 64:
                            break
                        draw.text((0, y_offset), line[:20], fill="white")
                        y_offset += 15
                
                # Button indicators at bottom
                draw.text((0, 50), f"K1 K2 K3", fill="white")
                
        except Exception as e:
            print(f"Error updating display: {e}")
    
    def clear(self):
        """Clear the OLED display."""
        if not self.device:
            return
        
        try:
            self.device.clear()
        except Exception as e:
            print(f"Error clearing display: {e}")
    
    def cleanup(self):
        """Clean up GPIO and display resources."""
        try:
            if self.device:
                self.clear()
            if GPIO_AVAILABLE and GPIO is not None:
                GPIO.cleanup([self.k1_pin, self.k2_pin, self.k3_pin])
        except Exception as e:
            print(f"Error during cleanup: {e}")


class ButtonHandler:
    """Handles button presses for mode switching and speed control."""
    
    def __init__(self, oled: OLEDDisplay):
        """Initialize button handler."""
        self.oled = oled
        self.mode_callback: Optional[Callable] = None
        self.speed_callback: Optional[Callable] = None
        
        # Setup button callbacks
        self.oled.set_k1_callback(self.on_k1_press)
        self.oled.set_k2_callback(self.on_k2_press)
        self.oled.set_k3_callback(self.on_k3_press)
    
    def set_mode_callback(self, callback: Callable):
        """Set callback for mode switching."""
        self.mode_callback = callback
    
    def set_speed_callback(self, callback: Callable):
        """Set callback for speed switching."""
        self.speed_callback = callback
    
    def on_k1_press(self):
        """Handle K1 button press (Mode Switch)."""
        print("K1 pressed: Switching mode...")
        if self.mode_callback:
            self.mode_callback()
    
    def on_k2_press(self):
        """Handle K2 button press (Speed Switch)."""
        print("K2 pressed: Switching speed...")
        if self.speed_callback:
            self.speed_callback()
    
    def on_k3_press(self):
        """Handle K3 button press (Additional function)."""
        print("K3 pressed")
        # Can be used for additional functions like wake-up, etc.

