import time
from app.core import config
from app.core.logger import setup_logger

logger = setup_logger(__name__)

# --- Hardware Imports with Graceful Fallback ---
try:
    import RPi.GPIO as GPIO
    from luma.core.interface.serial import i2c
    from luma.core.render import canvas
    from luma.oled.device import ssd1306
    from PIL import ImageFont
    HARDWARE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Hardware libraries not found ({e}). Using Mock Drivers.")
    HARDWARE_AVAILABLE = False
    GPIO = None

class DisplayManager:
    def __init__(self, mock=False):
        self.mock = mock or not HARDWARE_AVAILABLE
        self.device = None
        
        if not self.mock:
            try:
                self.serial = i2c(port=config.I2C_PORT, address=config.I2C_ADDRESS)
                self.device = ssd1306(self.serial, width=config.DISPLAY_WIDTH, height=config.DISPLAY_HEIGHT)
                self.font = ImageFont.load_default()
                self.clear()
                logger.info("Display initialized (Real).")
            except Exception as e:
                logger.error(f"Error initializing real display: {e}. Switching to Mock.")
                self.mock = True

        if self.mock:
            logger.info("Display initialized (Mock).")

    def clear(self):
        if not self.mock and self.device:
            self.device.clear()
        else:
            logger.debug("[Display] Cleared")

    def show_text(self, title, body):
        if self.mock:
            logger.info(f"[Display Mock] Title: {title} | Body: {body}")
            return

        if self.device:
            with canvas(self.device) as draw:
                # Draw Title Bar
                draw.rectangle((0, 0, config.DISPLAY_WIDTH, 12), fill="white")
                draw.text((2, 0), title, fill="black", font=self.font)
                
                # Draw Body Text
                lines = self._wrap_text(body, 20)
                y = 14
                for line in lines[:4]:
                    draw.text((0, y), line, fill="white", font=self.font)
                    y += 10

    def _wrap_text(self, text, max_chars):
        words = text.split()
        lines = []
        current_line = []
        current_len = 0
        
        for word in words:
            if current_len + len(word) + 1 <= max_chars:
                current_line.append(word)
                current_len += len(word) + 1
            else:
                lines.append(" ".join(current_line))
                current_line = [word]
                current_len = len(word)
        
        if current_line:
            lines.append(" ".join(current_line))
        return lines

class ButtonHandler:
    def __init__(self, mock=False):
        self.mock = mock or not HARDWARE_AVAILABLE
        
        if not self.mock:
            try:
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(config.PIN_K1_TRIGGER, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                GPIO.setup(config.PIN_K2_CHAT, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                GPIO.setup(config.PIN_K3_VISION, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                logger.info("Buttons initialized (Real).")
            except Exception as e:
                logger.error(f"Error initializing real buttons: {e}. Switching to Mock.")
                self.mock = True
        
        if self.mock:
            logger.info("Buttons initialized (Mock). Use keyboard simulation if implemented.")

    def is_pressed(self, pin):
        if self.mock:
            # In a real mock scenario, we might read from a file or listen to keyboard
            # For now, we return False to prevent infinite loops of triggers
            return False
            
        return GPIO.input(pin) == GPIO.LOW

    def cleanup(self):
        if not self.mock and GPIO:
            GPIO.cleanup()
        else:
            logger.info("Buttons cleaned up (Mock).")
