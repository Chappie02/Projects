# Offline Multi-Modal AI Assistant for Raspberry Pi 5

A complete offline AI assistant system that combines voice chat with object detection capabilities, running entirely on Raspberry Pi 5 without internet connectivity.

## 🎯 Features

- **Chat Mode**: Voice input → Speech-to-Text → RAG Memory → LLM → Text-to-Speech
- **Object Detection Mode**: Camera capture → YOLO detection → LLM summary → Voice output
- **OLED Display**: Real-time status and mode indicators
- **Physical Controls**: Three GPIO buttons for mode selection and interaction
- **Offline Operation**: All processing runs locally on the Raspberry Pi

## 🧩 Hardware Requirements

- Raspberry Pi 5
- Raspberry Pi Camera Module (compatible with Picamera2)
- USB Microphone
- USB Speaker
- OLED Display (Adafruit SSD1306, I2C)
- 3 Physical Switches:
  - K1: GPIO17 (Pin 11) - Select Chat Mode
  - K2: GPIO27 (Pin 13) - Select Object Detection Mode
  - K3: GPIO22 (Pin 15) - Hold to Speak / Press to Capture

## 📦 Software Setup

### 1. System Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install system packages
sudo apt install -y \
    python3-pip \
    python3-venv \
    python3-dev \
    libcamera-dev \
    libcamera-apps \
    libatlas-base-dev \
    portaudio19-dev \
    libasound2-dev \
    i2c-tools \
    git \
    build-essential \
    cmake \
    ffmpeg \
    libsm6 \
    libxext6
```

### 2. Enable Hardware Interfaces

#### Enable Camera:
```bash
sudo raspi-config
```
Navigate to: **Interface Options → Camera → Enable**

#### Enable I2C (for OLED):
```bash
sudo raspi-config
```
Navigate to: **Interface Options → I2C → Enable**

Verify I2C:
```bash
sudo i2cdetect -y 1
# Should show 0x3C for SSD1306
```

#### Enable Audio:
```bash
# Check audio devices
arecord -l  # List recording devices
aplay -l    # List playback devices

# Set default audio device if needed
sudo nano /etc/asound.conf
```

### 3. Python Environment Setup

**IMPORTANT**: Picamera2 does NOT work inside virtual environments. We'll install system-wide with special handling.

```bash
# Navigate to project directory
cd /home/pi/stranger  # or your project path

# Upgrade pip first (reduces build issues)
pip3 install --upgrade pip setuptools wheel

# Install requirements (system-wide for Picamera2 compatibility)
pip3 install -r requirements.txt
```

**Alternative**: If you prefer a virtual environment for other packages:

```bash
# Create venv
python3 -m venv venv
source venv/bin/activate

# Install most packages in venv
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# Note: Picamera2 will still use system Python path (handled in code)
```

### 4. Download AI Models

#### LLM Model (llama.cpp compatible):
```bash
# Create models directory
mkdir -p models

# Download a model (example: Gemma 2B or Llama 3 8B)
# Gemma 2B (recommended for Pi 5):
wget -O models/gemma-2b.gguf https://huggingface.co/bartowski/gemma-2b-it-GGUF/resolve/main/gemma-2b-it-q4_k_m.gguf

# Or Llama 3 8B:
# wget -O models/llama-3-8b.gguf [URL_TO_GGUF_FILE]
```

Update `chat_ai.py` model path if using different model:
```python
model_path: str = "models/gemma-2b.gguf"
```

#### YOLO Model (Optional - for object detection):
```bash
# Create object_models directory
mkdir -p object_models

# Download a YOLO ONNX model (example: YOLOv8n)
# You can convert from PyTorch or download pre-converted
# Place in: object_models/yolo_model.onnx
```

**Note**: The system will work with placeholder detection if YOLO model is not available.

#### TTS Model (Piper):
Piper models are automatically downloaded on first use. Default: `en_US-lessac-medium`

#### STT Model (Whisper):
Whisper models are automatically downloaded on first use. Default: `base`

### 5. Directory Structure

Ensure these directories exist:
```bash
mkdir -p memory          # ChromaDB storage
mkdir -p object_models   # YOLO models
mkdir -p models          # LLM models
mkdir -p /home/pi/Object_Captures  # Camera captures (auto-created)
```

## 🚀 Running the Application

### Basic Run:
```bash
cd /home/pi/stranger
python3 main.py
```

### Run with Logging:
```bash
python3 main.py 2>&1 | tee assistant.log
```

### Run as Service (Optional):

Create service file `/etc/systemd/system/ai-assistant.service`:
```ini
[Unit]
Description=AI Assistant
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/stranger
ExecStart=/usr/bin/python3 /home/pi/stranger/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable ai-assistant.service
sudo systemctl start ai-assistant.service
```

## 🎮 Usage

### Boot Screen
On startup, the OLED displays:
```
Select Mode:
 K1 Chat Mode
 K2 Object Mode
```

### Chat Mode
1. Press **K1** to enter Chat Mode
2. OLED shows: "Chat Mode - Hold K3 to Speak"
3. **Hold K3** to start recording
4. OLED shows: "Listening..."
5. **Release K3** to stop recording
6. OLED shows: "Processing..."
7. System processes: STT → RAG → LLM → TTS
8. Audio response plays through USB speaker

### Object Detection Mode
1. Press **K2** to enter Object Mode
2. OLED shows: "Object Mode - Press K3 to Capture"
3. **Press K3** to capture image
4. OLED shows: "Capturing Image..."
5. Then: "Detecting Object..."
6. System processes: Capture → YOLO → LLM Summary → TTS
7. Audio response plays through USB speaker

### Mode Switching
- Press **K1** at any time → Switch to Chat Mode
- Press **K2** at any time → Switch to Object Mode

## 🔧 Configuration

### Adjust Model Paths

Edit `chat_ai.py`:
```python
model_path: str = "models/your-model.gguf"
tts_model: str = "en_US-lessac-medium"
```

Edit `camera_model.py`:
```python
model_path: str = "object_models/your-yolo-model.onnx"
captures_dir: str = "/home/pi/Object_Captures"
```

### Adjust GPIO Pins

Edit `buttons.py`:
```python
class Button(Enum):
    K1 = 17  # Change pin numbers here
    K2 = 27
    K3 = 22
```

### Adjust OLED I2C Address

Edit `display.py`:
```python
self.display = SSD1306_I2C(
    self.width,
    self.height,
    i2c,
    addr=0x3C  # Change if your OLED uses different address
)
```

## 🐛 Troubleshooting

### Camera Issues
- Ensure camera is enabled: `sudo raspi-config`
- Check camera: `libcamera-hello --list-cameras`
- Test: `libcamera-jpeg -o test.jpg`

### Audio Issues
- List devices: `arecord -l` and `aplay -l`
- Test microphone: `arecord -d 5 test.wav && aplay test.wav`
- Check permissions: User must be in `audio` group

### OLED Not Displaying
- Check I2C: `sudo i2cdetect -y 1`
- Verify wiring (SDA, SCL, VCC, GND)
- Check I2C address (may be 0x3D instead of 0x3C)

### GPIO Buttons Not Working
- Verify wiring and pull-up resistors
- Check permissions: User must be in `gpio` group
- Test with: `gpio readall`

### Model Loading Errors
- Ensure models are in correct directories
- Check file permissions
- Verify model format (GGUF for LLM, ONNX for YOLO)

### Performance Issues
- Use smaller models (Gemma 2B instead of Llama 3 8B)
- Reduce LLM context window in `chat_ai.py`
- Use quantized models (q4_k_m, q5_k_m)

## 📝 Logging

Logs are written to:
- Console output
- `assistant.log` file

View logs:
```bash
tail -f assistant.log
```

## 🔒 Permissions

Ensure user has necessary permissions:
```bash
sudo usermod -a -G gpio,audio,i2c $USER
# Log out and back in for changes to take effect
```

## 📚 Project Structure

```
stranger/
├── main.py              # State machine and main loop
├── buttons.py            # GPIO button handling
├── display.py            # OLED display control
├── camera_model.py       # Picamera2 + YOLO detection
├── chat_ai.py            # STT + RAG + LLM + TTS
├── requirements.txt      # Python dependencies
├── README.md            # This file
├── memory/              # ChromaDB storage (auto-created)
├── models/              # LLM models
└── object_models/       # YOLO models
```

## 🎓 Technical Details

### State Machine
- **MENU**: Initial boot screen
- **CHAT_MODE**: Voice interaction mode
- **OBJECT_MODE**: Object detection mode

### RAG Memory
- Uses ChromaDB for persistent vector storage
- Stores user queries and assistant responses
- Retrieves top-k relevant past conversations before generating responses

### Threading
- Audio recording runs in separate thread
- Image processing runs in separate thread
- UI remains responsive during processing

## 📄 License

This project is provided as-is for educational and personal use.

## 🤝 Contributing

Feel free to submit issues or improvements!

## ⚠️ Notes

- First run may be slow as models download/initialize
- Ensure sufficient storage space for models and captures
- Recommended: 8GB+ RAM for smooth operation
- Use quality USB microphone and speaker for best results

