import RPi.GPIO as GPIO
import paho.mqtt.client as mqtt
import logging
import json
import threading
import time
from config import Config

class HomeAutomation:
    def __init__(self):
        self.config = Config()
        self.logger = logging.getLogger(__name__)
        self.mqtt_client = None
        self.device_states = {}
        self.is_connected = False
        
        # Initialize GPIO
        self._setup_gpio()
        
        # Initialize MQTT
        self._setup_mqtt()
        
        # Device states
        self.device_states = {
            "light_1": False,
            "light_2": False,
            "fan": False,
            "door_lock": False,
            "motion_detected": False
        }
    
    def _setup_gpio(self):
        """Setup GPIO pins for home automation"""
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            
            # Setup output pins
            for device, pin in self.config.GPIO_PINS.items():
                if device != "motion_sensor":
                    GPIO.setup(pin, GPIO.OUT)
                    GPIO.output(pin, GPIO.LOW)  # Start with devices off
            
            # Setup input pin for motion sensor
            GPIO.setup(self.config.GPIO_PINS["motion_sensor"], GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            
            # Add event detection for motion sensor
            GPIO.add_event_detect(
                self.config.GPIO_PINS["motion_sensor"], 
                GPIO.BOTH, 
                callback=self._motion_callback,
                bouncetime=300
            )
            
            self.logger.info("GPIO setup completed")
        except Exception as e:
            self.logger.error(f"Failed to setup GPIO: {e}")
    
    def _setup_mqtt(self):
        """Setup MQTT client for smart home integration"""
        try:
            self.mqtt_client = mqtt.Client()
            self.mqtt_client.on_connect = self._on_mqtt_connect
            self.mqtt_client.on_message = self._on_mqtt_message
            self.mqtt_client.on_disconnect = self._on_mqtt_disconnect
            
            # Set credentials if provided
            if self.config.MQTT_USERNAME and self.config.MQTT_PASSWORD:
                self.mqtt_client.username_pw_set(self.config.MQTT_USERNAME, self.config.MQTT_PASSWORD)
            
            # Connect to MQTT broker
            self.mqtt_client.connect(self.config.MQTT_BROKER, self.config.MQTT_PORT, 60)
            self.mqtt_client.loop_start()
            
            self.logger.info("MQTT client setup completed")
        except Exception as e:
            self.logger.error(f"Failed to setup MQTT: {e}")
    
    def _on_mqtt_connect(self, client, userdata, flags, rc):
        """MQTT connection callback"""
        if rc == 0:
            self.is_connected = True
            self.logger.info("Connected to MQTT broker")
            
            # Subscribe to relevant topics
            topics = [
                "home/light/+/control",
                "home/fan/control",
                "home/door/control",
                "home/status/request"
            ]
            
            for topic in topics:
                client.subscribe(topic)
                self.logger.info(f"Subscribed to {topic}")
        else:
            self.logger.error(f"Failed to connect to MQTT broker, return code: {rc}")
    
    def _on_mqtt_message(self, client, userdata, msg):
        """MQTT message callback"""
        try:
            payload = json.loads(msg.payload.decode())
            topic = msg.topic
            
            self.logger.info(f"Received MQTT message on {topic}: {payload}")
            
            # Handle different topics
            if "light" in topic:
                light_id = topic.split('/')[2]
                self._control_light(light_id, payload.get('state', False))
            elif "fan" in topic:
                self._control_fan(payload.get('state', False))
            elif "door" in topic:
                self._control_door_lock(payload.get('state', False))
            elif "status" in topic:
                self._publish_status()
                
        except Exception as e:
            self.logger.error(f"Error processing MQTT message: {e}")
    
    def _on_mqtt_disconnect(self, client, userdata, rc):
        """MQTT disconnection callback"""
        self.is_connected = False
        self.logger.warning("Disconnected from MQTT broker")
    
    def _motion_callback(self, channel):
        """Motion sensor callback"""
        motion_detected = GPIO.input(channel) == GPIO.HIGH
        self.device_states["motion_detected"] = motion_detected
        
        if motion_detected:
            self.logger.info("Motion detected!")
            # Publish motion event to MQTT
            self._publish_mqtt("home/motion/event", {"detected": True})
        else:
            self.logger.info("Motion stopped")
            self._publish_mqtt("home/motion/event", {"detected": False})
    
    def _control_light(self, light_id, state):
        """Control light devices"""
        if light_id == "1":
            pin = self.config.GPIO_PINS["light_1"]
            device_key = "light_1"
        elif light_id == "2":
            pin = self.config.GPIO_PINS["light_2"]
            device_key = "light_2"
        else:
            self.logger.error(f"Unknown light ID: {light_id}")
            return
        
        try:
            GPIO.output(pin, GPIO.HIGH if state else GPIO.LOW)
            self.device_states[device_key] = state
            
            status = "on" if state else "off"
            self.logger.info(f"Light {light_id} turned {status}")
            
            # Publish status update
            self._publish_mqtt(f"home/light/{light_id}/status", {"state": state})
            
        except Exception as e:
            self.logger.error(f"Error controlling light {light_id}: {e}")
    
    def _control_fan(self, state):
        """Control fan device"""
        try:
            pin = self.config.GPIO_PINS["fan"]
            GPIO.output(pin, GPIO.HIGH if state else GPIO.LOW)
            self.device_states["fan"] = state
            
            status = "on" if state else "off"
            self.logger.info(f"Fan turned {status}")
            
            # Publish status update
            self._publish_mqtt("home/fan/status", {"state": state})
            
        except Exception as e:
            self.logger.error(f"Error controlling fan: {e}")
    
    def _control_door_lock(self, state):
        """Control door lock device"""
        try:
            pin = self.config.GPIO_PINS["door_lock"]
            GPIO.output(pin, GPIO.HIGH if state else GPIO.LOW)
            self.device_states["door_lock"] = state
            
            status = "locked" if state else "unlocked"
            self.logger.info(f"Door {status}")
            
            # Publish status update
            self._publish_mqtt("home/door/status", {"state": state})
            
        except Exception as e:
            self.logger.error(f"Error controlling door lock: {e}")
    
    def _publish_mqtt(self, topic, payload):
        """Publish message to MQTT"""
        if self.is_connected and self.mqtt_client:
            try:
                message = json.dumps(payload)
                self.mqtt_client.publish(topic, message)
                self.logger.debug(f"Published to {topic}: {message}")
            except Exception as e:
                self.logger.error(f"Error publishing MQTT message: {e}")
    
    def _publish_status(self):
        """Publish current status of all devices"""
        status = {
            "timestamp": time.time(),
            "devices": self.device_states.copy()
        }
        self._publish_mqtt("home/status", status)
    
    def control_device(self, device_name, action):
        """Control devices based on voice commands"""
        device_name = device_name.lower()
        action = action.lower()
        
        if "light" in device_name:
            if "1" in device_name or "first" in device_name:
                state = "on" in action or "turn on" in action
                self._control_light("1", state)
                return f"Light 1 turned {'on' if state else 'off'}"
            elif "2" in device_name or "second" in device_name:
                state = "on" in action or "turn on" in action
                self._control_light("2", state)
                return f"Light 2 turned {'on' if state else 'off'}"
            else:
                # Control both lights
                state = "on" in action or "turn on" in action
                self._control_light("1", state)
                self._control_light("2", state)
                return f"All lights turned {'on' if state else 'off'}"
        
        elif "fan" in device_name:
            state = "on" in action or "turn on" in action
            self._control_fan(state)
            return f"Fan turned {'on' if state else 'off'}"
        
        elif "door" in device_name:
            state = "lock" in action or "close" in action
            self._control_door_lock(state)
            return f"Door {'locked' if state else 'unlocked'}"
        
        else:
            return "I don't understand that device command"
    
    def get_device_status(self):
        """Get current status of all devices"""
        return self.device_states.copy()
    
    def get_motion_status(self):
        """Get current motion detection status"""
        return self.device_states.get("motion_detected", False)
    
    def cleanup(self):
        """Cleanup GPIO and MQTT connections"""
        try:
            if self.mqtt_client:
                self.mqtt_client.loop_stop()
                self.mqtt_client.disconnect()
            
            GPIO.cleanup()
            self.logger.info("Home automation cleanup completed")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}") 