"""
Configuration file for Multi-Modal AI Assistant
Contains GPIO pin mappings, model paths, and system constants
"""

# GPIO Pin Mappings
GPIO_OLED_SDA = 2      # Physical Pin 3
GPIO_OLED_SCL = 3      # Physical Pin 5
GPIO_BUTTON_K1 = 17    # Physical Pin 11 (Select/Listen)
GPIO_BUTTON_K2 = 27    # Physical Pin 13 (Mode: Chat)
GPIO_BUTTON_K3 = 22    # Physical Pin 15 (Mode: Vision)

# OLED Display Settings
OLED_WIDTH = 128
OLED_HEIGHT = 64
OLED_I2C_ADDRESS = 0x3C

# Model Paths
LLM_MODEL_PATH = "/path/to/gemma-3-4b-it-IQ4_XS.gguf"  # Update this path
YOLO_MODEL = "yolov8n.pt"  # Nano model for efficiency on Pi

# ChromaDB Settings
CHROMA_DB_PATH = "./chroma_db"
COLLECTION_NAME = "conversation_history"

# Audio Settings
AUDIO_SAMPLE_RATE = 16000
AUDIO_CHUNK_SIZE = 1024
AUDIO_RECORD_DURATION = 5  # seconds

# LLM Settings
LLM_N_CTX = 2048  # Context window size
LLM_N_THREADS = 4  # Number of threads for inference
LLM_TEMPERATURE = 0.7
LLM_MAX_TOKENS = 256

# YOLO Settings
YOLO_CONFIDENCE_THRESHOLD = 0.25
YOLO_IOU_THRESHOLD = 0.45

# System Settings
CAMERA_RESOLUTION = (640, 480)
CAMERA_FRAMERATE = 30

# Mode Constants
MODE_CHAT = "chat"
MODE_VISION = "vision"

# Display Messages
MSG_MODE_CHAT = "Mode: Chat"
MSG_MODE_VISION = "Mode: Vision"
MSG_LISTENING = "Listening..."
MSG_PROCESSING = "Processing..."
MSG_READY = "Ready"

