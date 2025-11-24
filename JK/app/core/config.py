import os
from pathlib import Path

# Base Directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# --- Hardware Pins ---
PIN_K1_TRIGGER = 17
PIN_K2_CHAT = 27
PIN_K3_VISION = 22

# --- Display Settings ---
I2C_PORT = 1
I2C_ADDRESS = 0x3C
DISPLAY_WIDTH = 128
DISPLAY_HEIGHT = 64

# --- Paths ---
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
LOGS_DIR = BASE_DIR / "logs"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
MODELS_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Model Paths
LLM_MODEL_PATH = MODELS_DIR / "gemma-3-4b-it-IQ4_XS.gguf"
YOLO_MODEL_PATH = MODELS_DIR / "yolov8n.pt"
CHROMA_DB_PATH = DATA_DIR / "chroma_db"

# --- Audio Settings ---
SAMPLE_RATE = 16000
CHUNK_SIZE = 1024

# --- Camera Settings ---
CAMERA_RESOLUTION = (640, 480)
