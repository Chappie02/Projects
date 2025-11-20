# Raspberry Pi 5 Offline AI Assistant

A complete CLI-based Python application for a Raspberry Pi 5 that combines local large language models (LLM) with YOLOv8 object detection for an offline AI assistant experience.

## 🚀 Features

- **Chat Mode**: Text-based conversation using local LLM (llama.cpp)
- **Object Detection Mode**: Camera-based object detection with scene summarization
- **Fully Offline**: No internet connection required after setup
- **Raspberry Pi 5 Optimized**: Optimized for 4GB RAM Pi 5 with CPU-only inference
- **Modular Design**: Clean, extensible codebase with separate modules

## 📋 Requirements

### Hardware
- Raspberry Pi 5 (4GB RAM recommended)
- Raspberry Pi Camera Module (or USB camera)
- 0.96" SSD1306 OLED (128x64, I2C, rotated 180°)
- Three momentary buttons (K1/K2/K3)
- MicroSD card (32GB+ recommended)
- Power supply (5V, 3A recommended)

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
sudo apt install libcap-dev
pip install python-prctl
sudo apt install python3-libgpiod
sudo apt install libgpiod-dev

# I2C, GPIO, and audio helpers
sudo apt install -y python3-rpi.gpio python3-smbus i2c-tools
sudo apt install -y portaudio19-dev libopenblas-dev
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
https://huggingface.co/unsloth/gemma-3-4b-it-GGUF/resolve/main/gemma-3-4b-it-IQ4_XS.gguf
# OR download from another source
```
###important step
###install this before run
###for pc

##pip install torch==2.3.1+cpu torchvision==0.18.1+cpu torchaudio==2.3.1 --index-url https://download.pytorch.org/whl/cpu
###for raspberrypi

##pip install torch==2.2.2 torchvision==0.17.2 torchaudio==2.2.2 --extra-index-url https://download.pytorch.org/whl/cpu

##pip install --upgrade llama-cpp-python

##pip install --upgrade huggingface_hub sentence-transformers


### 6. Enable Camera
```bash
# Enable camera interface
sudo raspi-config
# Navigate to Interface Options > Camera > Enable
sudo reboot
```

### 7. Enable I2C
```bash
sudo raspi-config
# Interface Options > I2C > Enable
sudo reboot
```

## 🪛 OLED & Button Wiring

| OLED Pin | Raspberry Pi 5 Pin | Notes |
|----------|--------------------|-------|
| GND      | Pin 6 (GND)        | Common ground |
| VCC      | Pin 1 (3V3)        | 3.3V supply |
| SCL      | Pin 5 (GPIO3 / I2C1 SCL) | Enable I2C in raspi-config |
| SDA      | Pin 3 (GPIO2 / I2C1 SDA) | Use 2.2k pull-ups if cable is long |

| Button | Pi GPIO (header pin) | Run.py Pin Reference | Purpose |
|--------|----------------------|----------------------|---------|
| K1     | GPIO17 (Pin 11)      | `k1_pin=17`          | Cycle Chat → Detection → Hybrid |
| K2     | GPIO27 (Pin 13)      | `k2_pin=27`          | Cycle Low → Medium → High speed |
| K3     | GPIO22 (Pin 15)      | `k3_pin=22`          | General command / refresh |

Wire each button between the GPIO pin and ground. Enable the internal pull-ups already configured in `ButtonManager`, so no external resistors are required.

> **Bluetooth Mic**: Pair your Bluetooth headset (`bluetoothctl`) and set it as the default input device in `pavucontrol` or `alsamixer`. Pass the matching device index to `AudioManager` if it is not the default.

## 🎯 Usage

### Starting the Application
```bash
cd ai_assistant
source venv/bin/activate
python main.py
```

### Hardware-Integrated Runtime
```bash
cd ai_assistant
source venv/bin/activate
python run.py
```

### Available Commands

#### Main Menu
- `chat mode` - Enter text-based chat mode
- `object mode` - Enter camera-based object detection mode
- `exit` - Exit the application

#### Chat Mode Commands
- Type any message to chat with the local LLM
- `exit` - Return to main menu

#### Object Detection Mode Commands
- `what is this` - Capture image and analyze scene
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
│   └── system_utils.py    # System monitoring
├── models/                # AI model files
│   └── llama-7b-q4_0.gguf # LLaMA model (download separately)
└── chroma_db/             # RAG database (created automatically)
```

## ⚙️ Configuration

### Model Configuration
Edit the model paths in the respective mode files if your models are in different locations:

```python
# In chat_mode.py and object_mode.py
model_paths = [
    "./models/llama-7b-q4_0.gguf",  # Add your model path here
    "/home/pi/models/llama-7b.gguf",
    # ... other paths
]
```

### Camera Configuration
Adjust camera settings in `utils/camera_utils.py`:

```python
# Camera resolution and settings
resolution = (640, 480)  # Adjust as needed
camera_index = 0         # Camera device index
```

### Performance Tuning
Adjust LLM parameters in the mode files based on your system:

```python
# For systems with less RAM
n_ctx = 1024        # Context window
n_threads = 2       # CPU threads
max_tokens = 128    # Response length
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


