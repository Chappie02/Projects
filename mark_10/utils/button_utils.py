"""
Button Utilities
Handles GPIO button inputs for Raspberry Pi.
"""

import time
from typing import Optional, Callable
from enum import Enum

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    GPIO = None


class ButtonState(Enum):
    """Button state enumeration."""
    IDLE = "idle"
    PRESSED = "pressed"
    HELD = "held"


class ButtonManager:
    """Manages GPIO button operations."""
    
    def __init__(self, k1_pin=17, k2_pin=27, k3_pin=22):
        """
        Initialize button manager.
        
        Args:
            k1_pin: GPIO pin for K1 button (chat mode) - default: GPIO 17
            k2_pin: GPIO pin for K2 button (object detection mode) - default: GPIO 27
            k3_pin: GPIO pin for K3 button (capture image) - default: GPIO 22
        """
        self.k1_pin = k1_pin
        self.k2_pin = k2_pin
        self.k3_pin = k3_pin
        
        self.k1_callback: Optional[Callable] = None
        self.k2_callback: Optional[Callable] = None
        self.k3_callback: Optional[Callable] = None
        
        self.k1_state = ButtonState.IDLE
        self.k2_state = ButtonState.IDLE
        self.k3_state = ButtonState.IDLE
        
        self.k1_press_time = 0
        self.k2_press_time = 0
        self.k3_press_time = 0
        
        self.debounce_time = 0.05  # 50ms debounce
        
        if GPIO_AVAILABLE:
            self._initialize_gpio()
        else:
            print("⚠️  GPIO libraries not available. Button functionality disabled.")
    
    def _initialize_gpio(self):
        """Initialize GPIO pins for buttons."""
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            
            # Setup buttons as inputs with pull-up resistors
            GPIO.setup(self.k1_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.k2_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.k3_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
            # Add event detection for buttons
            GPIO.add_event_detect(self.k1_pin, GPIO.FALLING, callback=self._k1_pressed, bouncetime=200)
            GPIO.add_event_detect(self.k2_pin, GPIO.FALLING, callback=self._k2_pressed, bouncetime=200)
            GPIO.add_event_detect(self.k3_pin, GPIO.FALLING, callback=self._k3_pressed, bouncetime=200)
            
            print("✅ Buttons initialized successfully!")
            print(f"   K1 (Chat Mode): GPIO {self.k1_pin}")
            print(f"   K2 (Object Mode): GPIO {self.k2_pin}")
            print(f"   K3 (Capture): GPIO {self.k3_pin}")
            
        except Exception as e:
            print(f"❌ Error initializing buttons: {e}")
    
    def _k1_pressed(self, channel):
        """Handle K1 button press."""
        if self.k1_callback:
            try:
                self.k1_callback()
            except Exception as e:
                print(f"⚠️  Error in K1 callback: {e}")
    
    def _k2_pressed(self, channel):
        """Handle K2 button press."""
        if self.k2_callback:
            try:
                self.k2_callback()
            except Exception as e:
                print(f"⚠️  Error in K2 callback: {e}")
    
    def _k3_pressed(self, channel):
        """Handle K3 button press."""
        if self.k3_callback:
            try:
                self.k3_callback()
            except Exception as e:
                print(f"⚠️  Error in K3 callback: {e}")
    
    def set_k1_callback(self, callback: Callable):
        """Set callback for K1 button."""
        self.k1_callback = callback
    
    def set_k2_callback(self, callback: Callable):
        """Set callback for K2 button."""
        self.k2_callback = callback
    
    def set_k3_callback(self, callback: Callable):
        """Set callback for K3 button."""
        self.k3_callback = callback
    
    def is_k1_pressed(self) -> bool:
        """Check if K1 button is currently pressed."""
        if not GPIO_AVAILABLE or not GPIO:
            return False
        try:
            return GPIO.input(self.k1_pin) == GPIO.LOW
        except:
            return False
    
    def is_k2_pressed(self) -> bool:
        """Check if K2 button is currently pressed."""
        if not GPIO_AVAILABLE or not GPIO:
            return False
        try:
            return GPIO.input(self.k2_pin) == GPIO.LOW
        except:
            return False
    
    def is_k3_pressed(self) -> bool:
        """Check if K3 button is currently pressed."""
        if not GPIO_AVAILABLE or not GPIO:
            return False
        try:
            return GPIO.input(self.k3_pin) == GPIO.LOW
        except:
            return False
    
    def wait_for_k1(self, timeout: Optional[float] = None) -> bool:
        """
        Wait for K1 button press.
        
        Args:
            timeout: Maximum time to wait in seconds (None for infinite)
        
        Returns:
            True if button was pressed, False if timeout
        """
        start_time = time.time()
        while True:
            if self.is_k1_pressed():
                time.sleep(self.debounce_time)
                if self.is_k1_pressed():
                    return True
            
            if timeout and (time.time() - start_time) > timeout:
                return False
            
            time.sleep(0.01)
    
    def wait_for_k2(self, timeout: Optional[float] = None) -> bool:
        """
        Wait for K2 button press.
        
        Args:
            timeout: Maximum time to wait in seconds (None for infinite)
        
        Returns:
            True if button was pressed, False if timeout
        """
        start_time = time.time()
        while True:
            if self.is_k2_pressed():
                time.sleep(self.debounce_time)
                if self.is_k2_pressed():
                    return True
            
            if timeout and (time.time() - start_time) > timeout:
                return False
            
            time.sleep(0.01)
    
    def wait_for_k3(self, timeout: Optional[float] = None) -> bool:
        """
        Wait for K3 button press.
        
        Args:
            timeout: Maximum time to wait in seconds (None for infinite)
        
        Returns:
            True if button was pressed, False if timeout
        """
        start_time = time.time()
        while True:
            if self.is_k3_pressed():
                time.sleep(self.debounce_time)
                if self.is_k3_pressed():
                    return True
            
            if timeout and (time.time() - start_time) > timeout:
                return False
            
            time.sleep(0.01)
    
    def is_available(self) -> bool:
        """Check if GPIO is available."""
        return GPIO_AVAILABLE and GPIO is not None
    
    def cleanup(self):
        """Clean up GPIO resources."""
        if GPIO_AVAILABLE and GPIO:
            try:
                GPIO.cleanup()
            except:
                pass

