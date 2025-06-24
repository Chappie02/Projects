import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # LLM Configuration
    LLM_MODEL_NAME = "microsoft/DialoGPT-medium"  # Lightweight model for Pi
    MAX_LENGTH = 1000
    TEMPERATURE = 0.7
    
    # Object Detection
    OBJECT_DETECTION_MODEL = "yolov8n.pt"  # Nano model for speed
    CONFIDENCE_THRESHOLD = 0.5
    CAMERA_INDEX = 0
    
    # Audio Configuration
    AUDIO_SAMPLE_RATE = 16000
    AUDIO_CHUNK_SIZE = 1024
    AUDIO_CHANNELS = 1
    BLUETOOTH_DEVICE_NAME = "RaspberryPi5_LLM"
    
    # Home Automation
    MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
    MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
    MQTT_USERNAME = os.getenv("MQTT_USERNAME", "")
    MQTT_PASSWORD = os.getenv("MQTT_PASSWORD", "")
    
    # GPIO Pins for home automation
    GPIO_PINS = {
        "light_1": 17,
        "light_2": 18,
        "fan": 27,
        "door_lock": 22,
        "motion_sensor": 23
    }
    
    # System Settings
    LOG_LEVEL = "INFO"
    LOG_FILE = "llm_system.log"
    
    # Web Interface
    WEB_PORT = 5000
    WEB_HOST = "0.0.0.0"
    
    # Mode switching keywords
    MODE_KEYWORDS = {
        "object_detection": ["detect", "object", "see", "vision", "camera", "what do you see"],
        "home_automation": ["home", "automation", "light", "fan", "door", "control", "smart home"],
        "main_chat": ["chat", "talk", "conversation", "help", "assistant"]
    } 