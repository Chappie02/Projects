"""
GPIO Utilities
Handles 3-speed rotary switch connected via GPIO for mode switching.
"""

import time
import threading
from typing import Optional, Callable
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    print("⚠️  RPi.GPIO not available. Install with: pip install RPi.GPIO")


class RotarySwitch:
    """Manages 3-speed rotary switch for mode selection."""
    
    # Mode definitions
    MODE_CHAT = 0
    MODE_OBJECT = 1
    MODE_EXIT = 2
    
    MODE_NAMES = {
        MODE_CHAT: "Chat Mode",
        MODE_OBJECT: "Object Mode",
        MODE_EXIT: "Exit"
    }
    
    def __init__(self, pin_a: int = 17, pin_b: int = 27, pin_c: int = 22, 
                 mode_callback: Optional[Callable] = None):
        """
        Initialize rotary switch.
        
        Args:
            pin_a: GPIO pin for position 1 (Chat Mode)
            pin_b: GPIO pin for position 2 (Object Mode)
            pin_c: GPIO pin for position 3 (Exit)
            mode_callback: Callback function called when mode changes (mode: int)
        """
        self.pin_a = pin_a
        self.pin_b = pin_b
        self.pin_c = pin_c
        self.mode_callback = mode_callback
        self.current_mode = self.MODE_CHAT
        self.last_mode = self.MODE_CHAT
        
        if not GPIO_AVAILABLE:
            print("⚠️  GPIO not available - rotary switch disabled")
            return
        
        self._initialize_gpio()
        self._start_monitoring()
    
    def _initialize_gpio(self):
        """Initialize GPIO pins."""
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            
            # Configure pins as inputs with pull-up resistors
            GPIO.setup(self.pin_a, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.pin_b, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.pin_c, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
            # Add event detection for all pins
            GPIO.add_event_detect(self.pin_a, GPIO.BOTH, callback=self._pin_callback, bouncetime=50)
            GPIO.add_event_detect(self.pin_b, GPIO.BOTH, callback=self._pin_callback, bouncetime=50)
            GPIO.add_event_detect(self.pin_c, GPIO.BOTH, callback=self._pin_callback, bouncetime=50)
            
            print("✅ GPIO rotary switch initialized successfully!")
            
        except Exception as e:
            print(f"⚠️  Error initializing GPIO: {e}")
    
    def _pin_callback(self, channel):
        """Callback for GPIO pin changes."""
        # Debounce delay
        time.sleep(0.01)
        self._read_mode()
    
    def _read_mode(self):
        """Read current mode from GPIO pins."""
        try:
            # Read pin states (LOW = selected, HIGH = not selected due to pull-up)
            pin_a_state = GPIO.input(self.pin_a)
            pin_b_state = GPIO.input(self.pin_b)
            pin_c_state = GPIO.input(self.pin_c)
            
            # Determine mode based on which pin is LOW
            if not pin_a_state:  # Pin A is LOW (selected)
                new_mode = self.MODE_CHAT
            elif not pin_b_state:  # Pin B is LOW (selected)
                new_mode = self.MODE_OBJECT
            elif not pin_c_state:  # Pin C is LOW (selected)
                new_mode = self.MODE_EXIT
            else:
                # No pin selected, keep current mode
                return
            
            # Check if mode changed
            if new_mode != self.current_mode:
                self.last_mode = self.current_mode
                self.current_mode = new_mode
                
                print(f"🔄 Mode changed: {self.MODE_NAMES[self.last_mode]} -> {self.MODE_NAMES[self.current_mode]}")
                
                # Call callback if provided
                if self.mode_callback:
                    try:
                        self.mode_callback(self.current_mode)
                    except Exception as e:
                        print(f"Error in mode callback: {e}")
        
        except Exception as e:
            print(f"Error reading mode: {e}")
    
    def _start_monitoring(self):
        """Start monitoring GPIO pins in a separate thread."""
        if not GPIO_AVAILABLE:
            return
        
        def monitor():
            while True:
                self._read_mode()
                time.sleep(0.1)  # Check every 100ms
        
        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()
    
    def get_mode(self) -> int:
        """
        Get current mode.
        
        Returns:
            Current mode (MODE_CHAT, MODE_OBJECT, or MODE_EXIT)
        """
        if GPIO_AVAILABLE:
            self._read_mode()
        return self.current_mode
    
    def get_mode_name(self) -> str:
        """
        Get current mode name.
        
        Returns:
            Current mode name as string
        """
        return self.MODE_NAMES[self.get_mode()]
    
    def cleanup(self):
        """Clean up GPIO resources."""
        try:
            if GPIO_AVAILABLE:
                GPIO.cleanup()
        except Exception as e:
            print(f"Error cleaning up GPIO: {e}")


class GPIOButton:
    """Simple GPIO button handler (alternative to rotary switch)."""
    
    def __init__(self, pin: int, callback: Optional[Callable] = None, pull_up=True):
        """
        Initialize GPIO button.
        
        Args:
            pin: GPIO pin number
            callback: Callback function called on button press
            pull_up: Use pull-up resistor (button connects to GND when pressed)
        """
        self.pin = pin
        self.callback = callback
        self.pull_up = pull_up
        
        if not GPIO_AVAILABLE:
            return
        
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.pin, GPIO.IN, 
                      pull_up_down=GPIO.PUD_UP if pull_up else GPIO.PUD_DOWN)
            GPIO.add_event_detect(self.pin, GPIO.FALLING if pull_up else GPIO.RISING,
                                 callback=self._button_callback, bouncetime=300)
        except Exception as e:
            print(f"Error initializing button: {e}")
    
    def _button_callback(self, channel):
        """Button press callback."""
        if self.callback:
            try:
                self.callback()
            except Exception as e:
                print(f"Error in button callback: {e}")
    
    def cleanup(self):
        """Clean up GPIO resources."""
        try:
            if GPIO_AVAILABLE:
                GPIO.remove_event_detect(self.pin)
        except Exception as e:
            print(f"Error cleaning up button: {e}")


if __name__ == "__main__":
    # Test rotary switch
    if GPIO_AVAILABLE:
        def mode_changed(mode):
            print(f"Mode changed to: {RotarySwitch.MODE_NAMES[mode]}")
        
        switch = RotarySwitch(mode_callback=mode_changed)
        
        try:
            print("Monitoring rotary switch... (Press Ctrl+C to exit)")
            while True:
                current_mode = switch.get_mode()
                print(f"Current mode: {RotarySwitch.MODE_NAMES[current_mode]}")
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nExiting...")
        finally:
            switch.cleanup()
    else:
        print("GPIO not available for testing")

