import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # LLM Settings
    LLM_MODEL_PATH = os.getenv("LLM_MODEL_PATH", "./models/llama-2-7b-chat.gguf")
    LLM_CONTEXT_LENGTH = int(os.getenv("LLM_CONTEXT_LENGTH", "2048"))
    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    
    # Voice Settings
    VOICE_LANGUAGE = os.getenv("VOICE_LANGUAGE", "en-us")
    VOICE_RATE = int(os.getenv("VOICE_RATE", "150"))
    VOICE_VOLUME = float(os.getenv("VOICE_VOLUME", "0.9"))
    
    # Camera Settings
    CAMERA_INDEX = int(os.getenv("CAMERA_INDEX", "0"))
    CAMERA_WIDTH = int(os.getenv("CAMERA_WIDTH", "640"))
    CAMERA_HEIGHT = int(os.getenv("CAMERA_HEIGHT", "480"))
    
    # Object Detection
    YOLO_MODEL_PATH = os.getenv("YOLO_MODEL_PATH", "./models/yolov8n.pt")
    DETECTION_CONFIDENCE = float(os.getenv("DETECTION_CONFIDENCE", "0.5"))
    
    # Home Automation
    HOME_ASSISTANT_URL = os.getenv("HOME_ASSISTANT_URL", "http://localhost:8123")
    HOME_ASSISTANT_TOKEN = os.getenv("HOME_ASSISTANT_TOKEN", "")
    MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
    MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
    
    # Bluetooth Settings
    BLUETOOTH_DEVICE_NAME = os.getenv("BLUETOOTH_DEVICE_NAME", "RaspberryPi5")
    
    # Mode switching keywords
    MODE_KEYWORDS = {
        "chat": ["chat", "talk", "conversation", "main", "normal"],
        "object_detection": ["object", "detect", "see", "camera", "vision", "what do you see"],
        "home_automation": ["home", "automation", "light", "fan", "turn on", "turn off", "switch"]
    }
    
    # Home automation commands mapping
    HOME_COMMANDS = {
        "light": {
            "on": ["turn on light", "light on", "switch on light"],
            "off": ["turn off light", "light off", "switch off light"]
        },
        "fan": {
            "on": ["turn on fan", "fan on", "switch on fan"],
            "off": ["turn off fan", "fan off", "switch off fan"]
        }
    } 