# Multi-Modal AI Assistant for Raspberry Pi 5

A complete embedded AI assistant system running on Raspberry Pi 5 with local LLM, RAG, object detection, and voice interaction capabilities.

## Features

- **Dual Mode Operation:**
  - **Chat Mode:** RAG-enhanced conversations with local LLM using ChromaDB for memory
  - **Vision Mode:** Real-time object detection using YOLO with natural language descriptions

- **Hardware Integration:**
  - 0.96" OLED display (SSD1306) for status and feedback
  - 3-button interface for mode switching and interaction
  - Raspberry Pi Zero 2W Camera for vision mode
  - USB/Bluetooth audio for voice interaction

- **AI Capabilities:**
  - Local LLM inference using llama.cpp (Gemma 3 4B IT)
  - ChromaDB-based RAG for conversation context
  - YOLO object detection (YOLOv8n)
  - Speech-to-Text and Text-to-Speech

## Hardware Requirements

- **Raspberry Pi 5** (4GB RAM minimum)
- **NVMe SSD** for storage
- **Raspberry Pi Zero 2W Camera Module**
- **0.96" OLED Display (SSD1306)** with I2C interface
- **Expansion Board** with 3 buttons (K1, K2, K3)
- **USB Microphone/Speaker** or **Bluetooth Headset**
- **GPIO Connections:**
  - OLED: SDA=GPIO 2, SCL=GPIO 3 (I2C)
  - Button K1: GPIO 17 (Select/Listen)
  - Button K2: GPIO 27 (Chat Mode)
  - Button K3: GPIO 22 (Vision Mode)

## Software Requirements

- **Raspberry Pi OS** (64-bit recommended)
- **Python 3.9+**
- **picamera2** (system package)
- **I2C enabled** in raspi-config

## Installation

### 1. System Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Enable I2C
sudo raspi-config
# Navigate to Interface Options > I2C > Enable

# Install system dependencies
sudo apt install -y python3-pip python3-venv i2c-tools libcamera-dev

# Install picamera2 (system package)
sudo apt install -y python3-picamera2

# Verify I2C and OLED connection
sudo i2cdetect -y 1
# Should show 0x3C for SSD1306
```

### 2. Python Environment Setup

```bash
# Navigate to project directory
cd /path/to/JK

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Model Setup

#### LLM Model

1. Download the Gemma 3 4B IT model in GGUF format:
   ```bash
   # Example: Download from Hugging Face or your preferred source
   # Model: gemma-3-4b-it-IQ4_XS.gguf
   ```

2. Update the model path in `config.py`:
   ```python
   LLM_MODEL_PATH = "/path/to/gemma-3-4b-it-IQ4_XS.gguf"
   ```

#### YOLO Model

The YOLOv8n model will be automatically downloaded on first run by Ultralytics.

### 4. Audio Setup

#### USB Microphone/Speaker

```bash
# List audio devices
arecord -l
aplay -l

# Test microphone
arecord -d 5 -f cd test.wav
aplay test.wav
```

#### Bluetooth Audio (Optional)

```bash
# Install Bluetooth tools
sudo apt install -y pulseaudio-module-bluetooth

# Pair and connect your Bluetooth headset
bluetoothctl
# Follow pairing instructions
```

### 5. Camera Setup

```bash
# Test camera
libcamera-hello --timeout 5000

# Verify picamera2
python3 -c "import picamera2; print('picamera2 OK')"
```

## Configuration

Edit `config.py` to customize:

- **GPIO Pins:** If your hardware uses different pins
- **Model Paths:** Update LLM model location
- **Audio Settings:** Adjust sample rate, chunk size, etc.
- **LLM Parameters:** Context window, threads, temperature
- **YOLO Settings:** Confidence thresholds

## Usage

### Starting the Application

```bash
# Activate virtual environment (if using)
source venv/bin/activate

# Run the application
python3 main.py
```

### Operating Modes

#### Chat Mode (Default)

1. **Press K2** to switch to Chat mode (display shows "Mode: Chat")
2. **Press K1** to start listening
3. Speak your question/query
4. System processes with RAG and responds via speech
5. Conversation is stored in ChromaDB for context

#### Vision Mode

1. **Press K3** to switch to Vision mode (display shows "Mode: Vision")
2. **Press K1** to start listening
3. Say "What is this?" or similar vision command
4. System captures image, runs YOLO detection
5. LLM generates natural description and speaks it

### Button Functions

- **K1 (GPIO 17):** Select/Listen - Activates current mode
- **K2 (GPIO 27):** Switch to Chat Mode
- **K3 (GPIO 22):** Switch to Vision Mode

## Project Structure

```
JK/
├── main.py              # Main application loop
├── config.py            # Configuration and constants
├── hardware.py          # OLED display and GPIO buttons
├── vision.py            # Camera capture and YOLO
├── memory.py            # ChromaDB RAG and conversation history
├── assistant.py         # LLM, STT, TTS handling
├── requirements.txt     # Python dependencies
├── README.md           # This file
└── chroma_db/          # ChromaDB database (created automatically)
```

## Troubleshooting

### OLED Display Not Working

```bash
# Check I2C connection
sudo i2cdetect -y 1

# Verify I2C is enabled
sudo raspi-config

# Check permissions
sudo usermod -a -G i2c $USER
# Log out and back in
```

### Camera Not Detected

```bash
# Check camera connection
libcamera-hello --timeout 5000

# Verify picamera2 import path
python3 -c "import sys; sys.path.append('/usr/lib/python3/dist-packages'); import picamera2; print('OK')"
```

### Audio Issues

```bash
# Test microphone
python3 -c "import speech_recognition as sr; r = sr.Recognizer(); print('OK')"

# Check audio devices
python3 -c "import pyaudio; p = pyaudio.PyAudio(); [print(p.get_device_info_by_index(i)) for i in range(p.get_device_count())]"
```

### LLM Model Not Found

- Verify the model path in `config.py`
- Ensure the model file exists and is readable
- Check file permissions: `ls -l /path/to/model.gguf`

### Memory Issues (4GB RAM)

- Use quantized models (IQ4_XS, Q4_K_M)
- Reduce `LLM_N_CTX` in `config.py`
- Close other applications
- Consider using swap space:
  ```bash
  sudo dphys-swapfile swapoff
  sudo nano /etc/dphys-swapfile
  # Set CONF_SWAPSIZE=2048
  sudo dphys-swapfile setup
  sudo dphys-swapfile swapon
  ```

### ChromaDB Errors

- Ensure write permissions in project directory
- Delete `chroma_db/` folder to reset database
- Check disk space: `df -h`

## Performance Optimization

1. **LLM Performance:**
   - Use quantized models (IQ4_XS, Q4_K_M)
   - Adjust `LLM_N_THREADS` based on CPU cores
   - Reduce `LLM_N_CTX` for faster inference

2. **YOLO Performance:**
   - Use YOLOv8n (nano) model
   - Reduce camera resolution in `config.py`
   - Lower confidence threshold if needed

3. **Memory Management:**
   - Camera is initialized on-demand and released immediately
   - LLM model stays loaded (one-time cost)
   - ChromaDB uses persistent storage

## Development

### Adding Custom Knowledge

```python
from memory import MemorySystem

memory = MemorySystem()
memory.add_knowledge(
    "Your custom knowledge text here",
    metadata={"source": "custom", "topic": "example"}
)
```

### Extending Functionality

- Add new modes by extending `main.py`
- Customize prompts in `assistant.py`
- Add new hardware in `hardware.py`

## License

This project is provided as-is for educational and development purposes.

## Acknowledgments

- **llama.cpp** for efficient LLM inference
- **ChromaDB** for vector database
- **Ultralytics** for YOLO models
- **Raspberry Pi Foundation** for hardware and picamera2

## Support

For issues and questions:
1. Check the troubleshooting section
2. Verify all hardware connections
3. Review system logs for errors
4. Ensure all dependencies are installed correctly

---

**Note:** This system is designed for Raspberry Pi 5 with 4GB RAM. Performance may vary with different hardware configurations. Ensure adequate cooling for sustained operation.

