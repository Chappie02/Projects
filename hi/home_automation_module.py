import requests
import json
import logging
import threading
import time
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass

try:
    import paho.mqtt.client as mqtt
except ImportError:
    print("paho-mqtt not installed. MQTT functionality will be limited.")
    mqtt = None

from config import Config

@dataclass
class Device:
    id: str
    name: str
    type: str
    state: str
    controllable: bool

class HomeAutomationModule:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.devices = {}
        self.mqtt_client = None
        self.is_connected = False
        self.home_assistant_available = False
        
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize Home Assistant and MQTT connections"""
        try:
            # Test Home Assistant connection
            if Config.HOME_ASSISTANT_TOKEN:
                self._test_home_assistant_connection()
            
            # Initialize MQTT client
            if mqtt:
                self._initialize_mqtt()
            
            self.logger.info("Home automation module initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize home automation: {e}")
    
    def _test_home_assistant_connection(self):
        """Test connection to Home Assistant"""
        try:
            headers = {
                "Authorization": f"Bearer {Config.HOME_ASSISTANT_TOKEN}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(
                f"{Config.HOME_ASSISTANT_URL}/api/",
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200:
                self.home_assistant_available = True
                self.logger.info("Home Assistant connection successful")
                self._load_devices()
            else:
                self.logger.warning("Home Assistant connection failed")
                
        except Exception as e:
            self.logger.warning(f"Home Assistant not available: {e}")
    
    def _initialize_mqtt(self):
        """Initialize MQTT client"""
        try:
            self.mqtt_client = mqtt.Client()
            self.mqtt_client.on_connect = self._on_mqtt_connect
            self.mqtt_client.on_message = self._on_mqtt_message
            
            # Connect to MQTT broker
            self.mqtt_client.connect(Config.MQTT_BROKER, Config.MQTT_PORT, 60)
            self.mqtt_client.loop_start()
            
            self.logger.info("MQTT client initialized")
            
        except Exception as e:
            self.logger.warning(f"MQTT connection failed: {e}")
    
    def _on_mqtt_connect(self, client, userdata, flags, rc):
        """MQTT connection callback"""
        if rc == 0:
            self.is_connected = True
            self.logger.info("Connected to MQTT broker")
            # Subscribe to relevant topics
            client.subscribe("home/+/status")
        else:
            self.logger.error(f"Failed to connect to MQTT broker, return code: {rc}")
    
    def _on_mqtt_message(self, client, userdata, msg):
        """MQTT message callback"""
        try:
            payload = json.loads(msg.payload.decode())
            topic = msg.topic
            
            # Update device state based on MQTT message
            if "status" in topic:
                device_id = topic.split("/")[1]
                if device_id in self.devices:
                    self.devices[device_id].state = payload.get("state", "unknown")
                    
        except Exception as e:
            self.logger.error(f"Error processing MQTT message: {e}")
    
    def _load_devices(self):
        """Load devices from Home Assistant"""
        if not self.home_assistant_available:
            return
        
        try:
            headers = {
                "Authorization": f"Bearer {Config.HOME_ASSISTANT_TOKEN}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(
                f"{Config.HOME_ASSISTANT_URL}/api/states",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                states = response.json()
                
                for state in states:
                    entity_id = state["entity_id"]
                    
                    # Filter for relevant device types
                    if any(device_type in entity_id for device_type in ["light", "switch", "fan"]):
                        device = Device(
                            id=entity_id,
                            name=state["attributes"].get("friendly_name", entity_id),
                            type=entity_id.split(".")[0],
                            state=state["state"],
                            controllable=True
                        )
                        self.devices[entity_id] = device
                
                self.logger.info(f"Loaded {len(self.devices)} devices from Home Assistant")
                
        except Exception as e:
            self.logger.error(f"Error loading devices: {e}")
    
    def get_devices(self) -> List[Device]:
        """Get list of available devices"""
        return list(self.devices.values())
    
    def get_device(self, device_id: str) -> Optional[Device]:
        """Get a specific device by ID"""
        return self.devices.get(device_id)
    
    def control_device(self, device_id: str, action: str) -> bool:
        """Control a device via Home Assistant or MQTT"""
        device = self.get_device(device_id)
        if not device:
            self.logger.warning(f"Device {device_id} not found")
            return False
        
        try:
            if self.home_assistant_available:
                return self._control_via_home_assistant(device_id, action)
            elif self.is_connected:
                return self._control_via_mqtt(device_id, action)
            else:
                self.logger.warning("No control method available")
                return False
                
        except Exception as e:
            self.logger.error(f"Error controlling device {device_id}: {e}")
            return False
    
    def _control_via_home_assistant(self, device_id: str, action: str) -> bool:
        """Control device via Home Assistant API"""
        try:
            headers = {
                "Authorization": f"Bearer {Config.HOME_ASSISTANT_TOKEN}",
                "Content-Type": "application/json"
            }
            
            service = f"{device_id.split('.')[0]}.turn_{action}"
            
            data = {
                "entity_id": device_id
            }
            
            response = requests.post(
                f"{Config.HOME_ASSISTANT_URL}/api/services/{service.split('.')[0]}/{service.split('.')[1]}",
                headers=headers,
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                self.logger.info(f"Successfully controlled {device_id} via Home Assistant")
                return True
            else:
                self.logger.error(f"Failed to control {device_id} via Home Assistant")
                return False
                
        except Exception as e:
            self.logger.error(f"Error controlling device via Home Assistant: {e}")
            return False
    
    def _control_via_mqtt(self, device_id: str, action: str) -> bool:
        """Control device via MQTT"""
        try:
            topic = f"home/{device_id}/control"
            payload = {
                "action": action,
                "timestamp": time.time()
            }
            
            self.mqtt_client.publish(topic, json.dumps(payload))
            self.logger.info(f"Sent MQTT command to {device_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error controlling device via MQTT: {e}")
            return False
    
    def parse_command(self, command: str) -> Optional[Dict]:
        """Parse natural language command for home automation"""
        command = command.lower()
        
        # Check for device types
        device_type = None
        if "light" in command:
            device_type = "light"
        elif "fan" in command:
            device_type = "fan"
        elif "switch" in command:
            device_type = "switch"
        
        if not device_type:
            return None
        
        # Check for actions
        action = None
        if any(word in command for word in ["on", "turn on", "switch on", "activate"]):
            action = "on"
        elif any(word in command for word in ["off", "turn off", "switch off", "deactivate"]):
            action = "off"
        elif "toggle" in command:
            action = "toggle"
        
        if not action:
            return None
        
        # Find matching device
        for device in self.devices.values():
            if device.type == device_type:
                return {
                    "device_id": device.id,
                    "action": action,
                    "device_name": device.name
                }
        
        return None
    
    def execute_command(self, command: str) -> str:
        """Execute a natural language home automation command"""
        parsed = self.parse_command(command)
        
        if not parsed:
            return "I couldn't understand that home automation command. Try saying something like 'turn on the light' or 'switch off the fan'."
        
        device_id = parsed["device_id"]
        action = parsed["action"]
        device_name = parsed["device_name"]
        
        success = self.control_device(device_id, action)
        
        if success:
            return f"Successfully turned {action} the {device_name}."
        else:
            return f"Sorry, I couldn't control the {device_name}. Please check if it's connected and try again."
    
    def get_status_summary(self) -> str:
        """Get a summary of all device states"""
        if not self.devices:
            return "No smart devices are currently connected."
        
        summary_parts = []
        for device in self.devices.values():
            status = "on" if device.state == "on" else "off"
            summary_parts.append(f"{device.name} is {status}")
        
        return f"Here's the status of your devices: {', '.join(summary_parts)}."
    
    def is_available(self) -> bool:
        """Check if home automation is available"""
        return self.home_assistant_available or self.is_connected 