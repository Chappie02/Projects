# Raspberry Pi 5 Offline AI Assistant

A complete CLI-based Python application for a Raspberry Pi 5 that combines local large language models (LLM) with YOLOv8 object detection for an offline AI assistant experience.

## 🚀 Features

### Core Features
- **Chat Mode**: Text/voice-based conversation using local LLM (llama.cpp)
- **Object Detection Mode**: Camera-based object detection with scene summarization
- **Fully Offline**: No internet connection required after setup
- **Raspberry Pi 5 Optimized**: Optimized for 4GB RAM Pi 5 with CPU-only inference
- **Modular Design**: Clean, extensible codebase with separate modules

### Voice & Hardware Features (New!)
- **Voice Input/Output**: Bluetooth microphone and speaker support
- **Wake Word Detection**: "Hey Pi" wake word to activate voice commands
- **Voice Commands**: Switch modes and control the assistant with voice
- **OLED Display**: 0.96-inch SSD1306 display for status and mode information
- **GPIO Rotary Switch**: 3-position switch for mode selection (Chat/Object/Exit)
- **Text-to-Speech**: Voice feedback for mode changes and responses
- **Speech Recognition**: Vosk-based ASR for voice command recognition

## 📋 Requirements

### Hardware
- Raspberry Pi 5 (4GB RAM recommended)
- Raspberry Pi Camera Module (or USB camera)
- MicroSD card (32GB+ recommended)
- Power supply (5V, 3A recommended)

### Optional Hardware (for Voice & Hardware Features)
- **OLED Display**: 0.96-inch SSD1306 (128x64) via I2C
- **Rotary Switch**: 3-position rotary switch for mode selection
- **Bluetooth Audio**: Bluetooth headset/microphone and speaker
- **Jumper Wires**: For GPIO connections

### Software
- Raspberry Pi OS (64-bit recommended)
- Python 3.8+
- OpenCV-compatible camera

## 🛠️ Installation

### 1. Clone or Download the Project
```bash
cd /home/pi
git clone <repository-url> ai_assistant
# OR download and extract the project files
```

### 2. Install System Dependencies
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required system packages
sudo apt install -y python3-pip python3-venv python3-opencv
sudo apt install -y libhdf5-dev libhdf5-serial-dev
sudo apt install -y libatlas-base-dev libjasper-dev libqtgui4 libqt4-test
sudo apt install -y libqtwebkit4 libgtk-3-dev libavcodec-dev libavformat-dev
sudo apt install -y libswscale-dev libv4l-dev libxvidcore-dev libx264-dev
```

### 3. Create Virtual Environment
```bash
cd ai_assistant
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Python Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Download AI Models

#### YOLOv8 Model
The YOLOv8 model will be downloaded automatically on first run.

#### LLaMA Model
Download a GGUF quantized LLaMA model (recommended: 7B q4_0):

```bash
# Create models directory
mkdir -p models

# Download LLaMA 7B q4_0 model (example URL - use actual download link)
cd models
wget https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q4_0.gguf
# OR download from another source
```
## important step
##install this before run
###pip install torch==2.3.1+cpu torchvision==0.18.1+cpu torchaudio==2.3.1 --index-url https://download.pytorch.org/whl/cpu

##pip install --upgrade llama-cpp-python

###pip install --upgrade huggingface_hub sentence-transformers


### 6. Enable Camera
```bash
# Enable camera interface
sudo raspi-config
# Navigate to Interface Options > Camera > Enable
sudo reboot
```

### 7. Setup Voice & Hardware (Optional)
For voice and hardware features, see the detailed setup guide:
```bash
# See SETUP_VOICE_HARDWARE.md for complete instructions
cat SETUP_VOICE_HARDWARE.md
```

Quick setup:
```bash
# Install audio dependencies
sudo apt-get install -y python3-pyaudio portaudio19-dev
sudo apt-get install -y espeak espeak-data libespeak1 libespeak-dev

# Install I2C tools
sudo apt-get install -y i2c-tools python3-smbus

# Enable I2C interface
sudo raspi-config
# Navigate to: Interface Options → I2C → Enable

# Download Vosk model for voice recognition
cd models
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip
rm vosk-model-small-en-us-0.15.zip
cd ..
```

## 🎯 Usage

### Starting the Application
```bash
cd ai_assistant
source venv/bin/activate
python main.py
```

### Available Commands

#### Control Methods

**1. GPIO Rotary Switch** (if hardware installed)
- Position 1: Switch to Chat Mode
- Position 2: Switch to Object Detection Mode
- Position 3: Exit the application

**2. Voice Commands** (if voice features enabled)
- Say "Hey Pi" to wake up the assistant
- Then say:
  - "Switch to chat mode" or "Chat mode"
  - "Switch to object mode" or "Object mode"
  - "Exit" or "Exit assistant"
  - "What is this" (in Object Mode to analyze scene)

**3. Keyboard Input** (fallback/default)
- Type commands at the prompt
- `chat mode` - Enter text-based chat mode
- `object mode` - Enter camera-based object detection mode
- `exit` - Exit the application

#### Chat Mode
- Voice: Say "Hey Pi" then ask your question
- Text: Type any message to chat with the local LLM
- `exit` - Return to main menu

#### Object Detection Mode
- Voice: Say "Hey Pi" then "what is this"
- Text: Type `what is this` to capture image and analyze scene
- `exit` - Return to main menu

## 📁 Project Structure

```
ai_assistant/
├── main.py                 # Main entry point
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── modes/                 # Application modes
│   ├── chat_mode.py       # Chat mode implementation
│   └── object_mode.py     # Object detection mode
├── utils/                 # Utility modules
│   ├── camera_utils.py    # Camera operations
│   ├── llm_utils.py       # LLM management
│   ├── rag_utils.py       # RAG functionality
│   ├── system_utils.py    # System monitoring
│   ├── audio_utils.py     # Audio input/output (Bluetooth)
│   ├── oled_display.py    # OLED display control
│   ├── gpio_utils.py      # GPIO rotary switch
│   ├── wake_word_detector.py  # Wake word detection
│   ├── voice_recognition.py   # Speech-to-text (ASR)
│   ├── text_to_speech.py      # Text-to-speech (TTS)
│   └── voice_mode_manager.py  # Voice mode integration
├── models/                # AI model files
│   ├── llama-7b-q4_0.gguf # LLaMA model (download separately)
│   └── vosk-model-small-en-us-0.15/  # Vosk ASR model (download separately)
└── chroma_db/             # RAG database (created automatically)
```

## ⚙️ Configuration

### Model Configuration
Edit the model paths in `config.py`:

```python
LLAMA_MODEL_PATHS = [
    "./models/llama-2-7b-chat.Q4_0.gguf",
    "./models/gemma-2b-it.Q6_K.gguf",
    # ... other paths
]
```

### Hardware Configuration
Edit hardware settings in `config.py`:

```python
# OLED Display
OLED_CONFIG = {
    'enabled': True,
    'i2c_address': 0x3C,  # Change if needed
}

# GPIO Rotary Switch
GPIO_CONFIG = {
    'enabled': True,
    'pin_chat': 17,      # GPIO pin for Chat Mode
    'pin_object': 27,    # GPIO pin for Object Mode
    'pin_exit': 22,      # GPIO pin for Exit
}

# Audio
AUDIO_CONFIG = {
    'sample_rate': 16000,
    'use_bluetooth': True,
}

# Voice Recognition
VOICE_RECOGNITION_CONFIG = {
    'enabled': True,
    'engine': 'vosk',
    'vosk_model': 'vosk-model-small-en-us-0.15',
}

# Text-to-Speech
TTS_CONFIG = {
    'enabled': True,
    'engine': 'espeak',
    'speak_mode_changes': True,
    'speak_responses': False,  # Set to True to speak LLM responses
}
```

### Camera Configuration
Adjust camera settings in `config.py`:

```python
CAMERA_CONFIG = {
    'index': 0,
    'resolution': (640, 480),
    'fps': 30,
}
```

### Performance Tuning
Adjust LLM parameters in `config.py`:

```python
LLM_CONFIG = {
    'n_ctx': 2048,      # Context window
    'n_threads': 4,     # CPU threads
    'max_tokens': 256,  # Response length
}
```

## 🔧 Troubleshooting

### Common Issues

#### 1. Camera Not Working
```bash
# Check if camera is detected
ls /dev/video*
# Test camera with OpenCV
python -c "import cv2; cap = cv2.VideoCapture(0); print(cap.isOpened())"
```

#### 2. Model Loading Errors
- Ensure model files are in the correct directory
- Check file permissions
- Verify model format (GGUF files only)

#### 3. Memory Issues
- Reduce context window size (`n_ctx`)
- Close other applications
- Consider using smaller models

#### 4. Slow Performance
- Reduce camera resolution
- Lower YOLO confidence threshold
- Use fewer CPU threads for LLM

### Debug Mode
Enable debug output by setting environment variable:
```bash
export DEBUG=1
python main.py
```

## 🎤 Voice & Hardware Features

The assistant now supports voice control and hardware interfaces:

### Voice Features
- **Wake Word**: Say "Hey Pi" to activate
- **Voice Commands**: Control modes and interact via voice
- **Speech Recognition**: Vosk-based ASR for accurate transcription
- **Text-to-Speech**: Voice feedback for mode changes and responses

### Hardware Features
- **OLED Display**: Shows current mode and status
- **GPIO Rotary Switch**: Physical mode selection
- **Bluetooth Audio**: Wireless microphone and speaker support

### Setup
See `SETUP_VOICE_HARDWARE.md` for detailed setup instructions.

**Note**: All features are optional. The assistant works without hardware - it will fall back to text/console mode if hardware is not available.


