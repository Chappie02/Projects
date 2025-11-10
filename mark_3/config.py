"""
Configuration file for Raspberry Pi 5 Offline AI Assistant
Modify these settings based on your system and preferences.
"""

import os
from pathlib import Path

# =============================================================================
# MODEL CONFIGURATION
# =============================================================================

# LLaMA model paths (in order of preference)
LLAMA_MODEL_PATHS = [
   
    "./models/gemma-2b-it.Q6_K.gguf",
   # "gemma-2b-it.Q6_K.gguf",
    "./models/llama-2-7b-chat.Q4_0.gguf",
    "./models/llama-7b-q4_0.gguf",
    "./models/llama-7b.gguf",
    "./models/llama-2-7b-chat.Q4_0.gguf",
    "/home/pi/models/llama-7b-q4_0.gguf",
    "/home/pi/models/llama-7b.gguf"
]

# YOLOv8 model (will be downloaded automatically if not present)
YOLO_MODEL_PATH = "yolov8n.pt"

# =============================================================================
# LLM CONFIGURATION
# =============================================================================

# LLM settings optimized for Raspberry Pi 5
LLM_CONFIG = {
    'n_ctx': 2048,           # Context window size
    'n_threads': 4,          # Number of CPU threads
    'n_gpu_layers': 0,       # GPU layers (0 for CPU only)
    'verbose': False,        # Verbose output
    'temperature': 0.7,      # Response creativity (0.0-1.0)
    'top_p': 0.9,           # Top-p sampling
    'max_tokens': 256,      # Maximum tokens to generate
    'repeat_penalty': 1.1,   # Repetition penalty
    'top_k': 40,            # Top-k sampling
}

# System prompt for the AI assistant
SYSTEM_PROMPT = """You are a helpful AI assistant running locally on a Raspberry Pi 5. 
You are designed to be helpful, harmless, and honest. You can assist with various tasks 
including answering questions, providing explanations, and helping with general inquiries. 
Keep your responses concise but informative."""

# =============================================================================
# CAMERA CONFIGURATION
# =============================================================================

# Camera settings
CAMERA_CONFIG = {
    'index': 0,              # Camera device index
    'resolution': (640, 480), # Camera resolution (width, height)
    'fps': 30,               # Frames per second
    'backend': None,         # OpenCV backend (None for auto-detect)
}

# =============================================================================
# OBJECT DETECTION CONFIGURATION
# =============================================================================

# YOLOv8 settings
YOLO_CONFIG = {
    'confidence_threshold': 0.5,  # Minimum confidence for detections
    'iou_threshold': 0.45,        # IoU threshold for NMS
    'max_detections': 100,        # Maximum number of detections
}

# =============================================================================
# RAG CONFIGURATION
# =============================================================================

# RAG settings
RAG_CONFIG = {
    'collection_name': 'ai_assistant_kb',
    'embedding_model': 'all-MiniLM-L6-v2',
    'chroma_db_path': './chroma_db',
    'max_context_length': 500,
    'n_results': 3,
}

# =============================================================================
# SYSTEM CONFIGURATION
# =============================================================================

# System monitoring settings
SYSTEM_CONFIG = {
    'memory_threshold': 85,       # Memory usage threshold (%)
    'cpu_threshold': 90,          # CPU usage threshold (%)
    'disk_threshold': 90,         # Disk usage threshold (%)
    'monitor_interval': 30,       # Monitoring interval (seconds)
}

# Logging configuration
LOGGING_CONFIG = {
    'level': 'INFO',              # Logging level
    'file': './ai_assistant.log', # Log file path
    'max_size': 10 * 1024 * 1024, # Max log file size (10MB)
    'backup_count': 5,            # Number of backup log files
}

# =============================================================================
# UI CONFIGURATION
# =============================================================================

# User interface settings
UI_CONFIG = {
    'show_banner': True,          # Show startup banner
    'show_system_info': True,     # Show system information
    'max_conversation_history': 10, # Maximum conversation history
    'auto_save_history': True,    # Auto-save conversation history
}

# =============================================================================
# HARDWARE CONFIGURATION
# =============================================================================

# OLED Display Configuration (SSD1306)
OLED_CONFIG = {
    'enabled': True,              # Enable OLED display
    'width': 128,                 # Display width in pixels
    'height': 64,                 # Display height in pixels
    'i2c_address': 0x3C,          # I2C address
    'i2c_bus': 1,                 # I2C bus number
}

# GPIO Rotary Switch Configuration
GPIO_CONFIG = {
    'enabled': True,              # Enable GPIO rotary switch
    'pin_chat': 17,               # GPIO pin for Chat Mode
    'pin_object': 27,             # GPIO pin for Object Mode
    'pin_exit': 22,               # GPIO pin for Exit Mode
    'pull_up': True,              # Use pull-up resistors
}

# Audio Configuration
AUDIO_CONFIG = {
    'sample_rate': 16000,         # Audio sample rate (Hz)
    'chunk_size': 4096,           # Audio chunk size
    'channels': 1,                # Number of audio channels (1=mono)
    'format': 'int16',            # Audio format
    'use_bluetooth': True,        # Prefer Bluetooth devices
    'recording_duration': 3.0,    # Default recording duration (seconds)
}

# Wake Word Configuration
WAKE_WORD_CONFIG = {
    'enabled': True,              # Enable wake word detection
    'wake_words': ["hey pi", "hey pie", "hi pi", "wake up"],  # Wake words
    'sensitivity': 0.5,           # Detection sensitivity (0.0-1.0)
    'require_wake_word': True,    # Require wake word before listening
}

# Voice Recognition Configuration (ASR)
VOICE_RECOGNITION_CONFIG = {
    'enabled': True,              # Enable voice recognition
    'engine': 'vosk',             # ASR engine: 'vosk' or 'whisper'
    'model_path': None,           # Path to ASR model (auto-detect if None)
    'language': 'en',             # Language code
    'vosk_model': 'vosk-model-small-en-us-0.15',  # Vosk model name
}

# Text-to-Speech Configuration
TTS_CONFIG = {
    'enabled': True,              # Enable text-to-speech
    'engine': 'espeak',           # TTS engine: 'espeak', 'pyttsx3', or 'gtts'
    'voice': None,                # Voice name (engine-specific)
    'rate': 150,                  # Speech rate (words per minute)
    'volume': 1.0,                # Volume (0.0-1.0)
    'speak_mode_changes': True,   # Speak mode change notifications
    'speak_responses': False,     # Speak LLM responses (can be slow)
}

# Voice Commands Configuration
VOICE_COMMANDS = {
    'switch_to_chat': ["switch to chat mode", "chat mode", "chat"],
    'switch_to_object': ["switch to object mode", "object mode", "object detection"],
    'exit': ["exit", "exit assistant", "goodbye", "stop"],
    'what_is_this': ["what is this", "what do you see", "analyze scene"],
}

# =============================================================================
# DEVELOPMENT CONFIGURATION
# =============================================================================

# Development settings
DEBUG = os.getenv('DEBUG', '0') == '1'

# Test mode settings
TEST_MODE = os.getenv('TEST_MODE', '0') == '1'

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_model_path(model_name: str) -> str:
    """Get the full path to a model file."""
    if model_name == 'llama':
        for path in LLAMA_MODEL_PATHS:
            if Path(path).exists():
                return path
        return LLAMA_MODEL_PATHS[0]  # Return first path as fallback
    elif model_name == 'yolo':
        return YOLO_MODEL_PATH
    else:
        return ""

def get_config_for_system() -> dict:
    """Get configuration optimized for the current system."""
    import psutil
    
    # Get system info
    memory_gb = psutil.virtual_memory().total / (1024**3)
    cpu_count = psutil.cpu_count()
    
    # Adjust configuration based on system capabilities
    config = LLM_CONFIG.copy()
    
    if memory_gb < 4:
        config['n_ctx'] = 1024
        config['max_tokens'] = 128
    elif memory_gb >= 8:
        config['n_ctx'] = 4096
        config['max_tokens'] = 512
    
    if cpu_count < 4:
        config['n_threads'] = 2
    elif cpu_count >= 8:
        config['n_threads'] = 6
    
    return config

def validate_config() -> bool:
    """Validate the configuration."""
    errors = []
    
    # Check model paths
    llama_found = False
    for path in LLAMA_MODEL_PATHS:
        if Path(path).exists():
            llama_found = True
            break
    
    if not llama_found:
        errors.append("No LLaMA model found in specified paths")
    
    # Check camera
    try:
        import cv2
        cap = cv2.VideoCapture(CAMERA_CONFIG['index'])
        if not cap.isOpened():
            errors.append("Camera not accessible")
        cap.release()
    except ImportError:
        errors.append("OpenCV not installed")
    
    if errors:
        print("Configuration validation errors:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    return True

# =============================================================================
# MAIN CONFIGURATION EXPORT
# =============================================================================

# Export main configuration
CONFIG = {
    'llama_model_paths': LLAMA_MODEL_PATHS,
    'yolo_model_path': YOLO_MODEL_PATH,
    'llm_config': LLM_CONFIG,
    'system_prompt': SYSTEM_PROMPT,
    'camera_config': CAMERA_CONFIG,
    'yolo_config': YOLO_CONFIG,
    'rag_config': RAG_CONFIG,
    'system_config': SYSTEM_CONFIG,
    'logging_config': LOGGING_CONFIG,
    'ui_config': UI_CONFIG,
    'oled_config': OLED_CONFIG,
    'gpio_config': GPIO_CONFIG,
    'audio_config': AUDIO_CONFIG,
    'wake_word_config': WAKE_WORD_CONFIG,
    'voice_recognition_config': VOICE_RECOGNITION_CONFIG,
    'tts_config': TTS_CONFIG,
    'voice_commands': VOICE_COMMANDS,
    'debug': DEBUG,
    'test_mode': TEST_MODE,
}

if __name__ == "__main__":
    # Test configuration
    import sys
    print("🔧 Testing configuration...")
    if validate_config():
        print("✅ Configuration is valid")
    else:
        print("❌ Configuration has errors")
        sys.exit(1)
