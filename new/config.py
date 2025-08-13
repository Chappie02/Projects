"""
Configuration file for Raspberry Pi 5 AI Assistant
Modify these settings to customize the assistant behavior
"""

# LLM Configuration
LLM_CONFIG = {
    "default_model": "gemma2:2b",  # Default model to use
    "ollama_url": "http://localhost:11434",  # Ollama API URL
    "temperature": 0.7,  # Response creativity (0.0-1.0)
    "max_tokens": 500,  # Maximum response length
    "timeout": 60,  # Request timeout in seconds
}

# Camera Configuration
CAMERA_CONFIG = {
    "width": 640,  # Camera resolution width
    "height": 480,  # Camera resolution height
    "fps": 30,  # Frames per second
    "camera_index": 0,  # Camera device index
    "use_mock": False,  # Use mock camera for testing
}

# Object Detection Configuration
DETECTION_CONFIG = {
    "model_size": "n",  # YOLOv8 model size: n, s, m, l, x
    "confidence_threshold": 0.5,  # Minimum confidence for detection
    "nms_threshold": 0.4,  # Non-maximum suppression threshold
    "max_detections": 10,  # Maximum objects to detect per frame
    "analysis_cooldown": 3.0,  # Seconds between object analyses
    "detection_cooldown": 2.0,  # Seconds between detection updates
}

# Performance Configuration
PERFORMANCE_CONFIG = {
    "history_size": 10,  # Number of conversation/detection entries to keep
    "frame_buffer_size": 1,  # Camera frame buffer size
    "enable_logging": True,  # Enable detailed logging
    "log_level": "INFO",  # Logging level: DEBUG, INFO, WARNING, ERROR
}

# UI Configuration
UI_CONFIG = {
    "enable_colors": True,  # Enable colored output
    "show_timestamps": True,  # Show timestamps in status messages
    "clear_screen_on_menu": True,  # Clear screen when showing menu
    "show_detection_boxes": True,  # Show bounding boxes in detection mode
}

# Model Recommendations for Raspberry Pi 5
MODEL_RECOMMENDATIONS = {
    "4gb_ram": [
        "gemma2:2b",  # Fastest, good for basic tasks
        "llama2:7b-q4_0",  # Good balance of performance/quality
    ],
    "8gb_ram": [
        "mistral:7b",  # Better quality responses
        "llama2:7b",  # Full model, best quality
        "codellama:7b",  # Good for programming tasks
    ]
}

# Available models for easy switching
AVAILABLE_MODELS = [
    "gemma2:2b",
    "gemma2:7b", 
    "mistral:7b",
    "llama2:7b",
    "llama2:7b-q4_0",
    "codellama:7b",
]

# Camera backends to try (in order of preference)
CAMERA_BACKENDS = [
    "v4l2",  # Video4Linux2 (Linux)
    "any",   # Any available backend
]

# Object detection classes of interest (for filtering)
INTERESTING_CLASSES = [
    "person", "car", "truck", "bicycle", "motorcycle",
    "bus", "train", "airplane", "boat",
    "cat", "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe",
    "backpack", "umbrella", "handbag", "tie", "suitcase",
    "frisbee", "skis", "snowboard", "sports ball", "kite", "baseball bat", "baseball glove",
    "skateboard", "surfboard", "tennis racket", "bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl",
    "banana", "apple", "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza", "donut", "cake",
    "chair", "couch", "potted plant", "bed", "dining table", "toilet", "tv", "laptop", "mouse", "remote", "keyboard", "cell phone", "microwave", "oven", "toaster", "sink", "refrigerator", "book", "clock", "vase", "scissors", "teddy bear", "hair drier", "toothbrush"
]

# Error handling configuration
ERROR_CONFIG = {
    "max_retries": 3,  # Maximum retry attempts for failed operations
    "retry_delay": 1.0,  # Delay between retries in seconds
    "graceful_degradation": True,  # Continue with reduced functionality on errors
}

# Logging configuration
LOGGING_CONFIG = {
    "log_file": "ai_assistant.log",  # Log file name
    "max_log_size": 10 * 1024 * 1024,  # 10MB max log file size
    "backup_count": 3,  # Number of backup log files
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
}

# Development/Testing configuration
DEV_CONFIG = {
    "debug_mode": False,  # Enable debug mode
    "mock_ollama": False,  # Use mock Ollama responses
    "save_frames": False,  # Save captured frames for debugging
    "frame_save_path": "debug_frames/",  # Path to save debug frames
}

def get_config():
    """Get complete configuration dictionary"""
    return {
        "llm": LLM_CONFIG,
        "camera": CAMERA_CONFIG,
        "detection": DETECTION_CONFIG,
        "performance": PERFORMANCE_CONFIG,
        "ui": UI_CONFIG,
        "error": ERROR_CONFIG,
        "logging": LOGGING_CONFIG,
        "dev": DEV_CONFIG,
    }

def validate_config():
    """Validate configuration settings"""
    errors = []
    
    # Validate LLM config
    if LLM_CONFIG["temperature"] < 0 or LLM_CONFIG["temperature"] > 1:
        errors.append("LLM temperature must be between 0.0 and 1.0")
    
    if LLM_CONFIG["max_tokens"] <= 0:
        errors.append("LLM max_tokens must be positive")
    
    # Validate camera config
    if CAMERA_CONFIG["width"] <= 0 or CAMERA_CONFIG["height"] <= 0:
        errors.append("Camera dimensions must be positive")
    
    if CAMERA_CONFIG["fps"] <= 0:
        errors.append("Camera FPS must be positive")
    
    # Validate detection config
    if DETECTION_CONFIG["confidence_threshold"] < 0 or DETECTION_CONFIG["confidence_threshold"] > 1:
        errors.append("Detection confidence threshold must be between 0.0 and 1.0")
    
    if DETECTION_CONFIG["model_size"] not in ["n", "s", "m", "l", "x"]:
        errors.append("Detection model size must be one of: n, s, m, l, x")
    
    return errors

def print_config_summary():
    """Print a summary of current configuration"""
    print("=== AI Assistant Configuration ===")
    print(f"LLM Model: {LLM_CONFIG['default_model']}")
    print(f"Camera: {CAMERA_CONFIG['width']}x{CAMERA_CONFIG['height']} @ {CAMERA_CONFIG['fps']}fps")
    print(f"Detection Model: YOLOv8{DETECTION_CONFIG['model_size'].upper()}")
    print(f"Mock Camera: {CAMERA_CONFIG['use_mock']}")
    print(f"Debug Mode: {DEV_CONFIG['debug_mode']}")
    print("==================================")
