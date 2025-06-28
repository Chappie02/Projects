# 🤖 AI Assistant for Raspberry Pi 5

A comprehensive multi-mode AI assistant that runs locally on Raspberry Pi 5, featuring voice interaction, object detection, and home automation capabilities.

## 🌟 Features

### 🗣️ **Main LLM Chat Mode**
- Local language model for natural conversations
- Context-aware responses
- Fallback responses when LLM is not available

### 👁️ **Object Detection Mode**
- Real-time camera-based object detection using YOLO
- Motion detection fallback
- Natural language descriptions of detected objects

### 🏠 **Home Automation Mode**
- Control smart devices via Home Assistant API
- MQTT support for IoT devices
- Natural language command parsing

### 🎤 **Voice Interface**
- Speech-to-text using Vosk (offline)
- Text-to-speech using pyttsx3
- Bluetooth audio support
- Voice command mode switching

## 📋 Requirements

### Hardware
- Raspberry Pi 5 (4GB RAM recommended)
- Camera module or USB camera
- Bluetooth speaker/microphone or USB audio
- MicroSD card (32GB+ recommended)

### Software
- Raspberry Pi OS (Bullseye or newer)
- Python 3.8+
- Internet connection for initial setup

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd ai-assistant-raspberry-pi
```

### 2. Run the Installation Script
```bash
chmod +x install.sh
./install.sh
```

### 3. Configure the Assistant
Edit the `.env` file to configure your settings:
```bash
nano .env
```

### 4. Download LLM Model
Download a GGUF format LLM model (e.g., Llama-2-7B-Chat) to the `models/` directory:
```bash
cd models
wget https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.gguf
cd ..
```

### 5. Start the Assistant
```bash
python3 ai_assistant.py
```

Or use the startup script:
```bash
./start_assistant.sh
```

## ⚙️ Configuration

### Environment Variables (.env file)

```env
# LLM Settings
LLM_MODEL_PATH=./models/llama-2-7b-chat.gguf
LLM_CONTEXT_LENGTH=2048
LLM_TEMPERATURE=0.7

# Voice Settings
VOICE_LANGUAGE=en-us
VOICE_RATE=150
VOICE_VOLUME=0.9

# Camera Settings
CAMERA_INDEX=0
CAMERA_WIDTH=640
CAMERA_HEIGHT=480

# Object Detection
YOLO_MODEL_PATH=./models/yolov8n.pt
DETECTION_CONFIDENCE=0.5

# Home Automation
HOME_ASSISTANT_URL=http://localhost:8123
HOME_ASSISTANT_TOKEN=your_token_here
MQTT_BROKER=localhost
MQTT_PORT=1883

# Bluetooth Settings
BLUETOOTH_DEVICE_NAME=RaspberryPi5
```

## 🎯 Usage

### Mode Switching
The assistant automatically switches modes based on your commands:

- **Chat Mode**: "Let's chat", "Switch to chat mode"
- **Object Detection**: "What do you see?", "Switch to object detection"
- **Home Automation**: "Turn on the light", "Switch to home automation"

### Voice Commands
Enable voice input by typing `voice` in the terminal:
- Speak naturally to interact
- Type `text` to return to text input

### Object Detection Commands
- "What do you see?" - Describe objects in camera view
- "Take a photo" - Capture current image
- "Detect objects" - Start object detection

### Home Automation Commands
- "Turn on the light" - Control smart lights
- "Switch off the fan" - Control smart fans
- "What's the status?" - Check device states

### General Commands
- `help` - Show available commands
- `status` - Show system status
- `exit` - Quit the assistant

## 🔧 Manual Installation

If you prefer manual installation:

### 1. Install System Dependencies
```bash
sudo apt update
sudo apt install -y python3-pip python3-venv libportaudio2 portaudio19-dev \
    python3-pyaudio espeak libespeak-dev libatlas-base-dev libblas-dev \
    liblapack-dev libhdf5-dev libqtgui4 libqtwebkit4 python3-pyqt5 \
    libjasper-dev libgstreamer1.0-dev libgtk-3-dev libavcodec-dev \
    libavformat-dev libswscale-dev libv4l-dev libxvidcore-dev \
    libx264-dev libjpeg-dev libpng-dev libtiff-dev gfortran \
    libbluetooth-dev bluez bluez-tools wget unzip
```

### 2. Install Python Dependencies
```bash
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

### 3. Download Models
```bash
mkdir -p models
cd models

# Download Vosk model
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip
rm vosk-model-small-en-us-0.15.zip

# Download YOLO model
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt

cd ..
```

## 🏠 Home Automation Setup

### Home Assistant Integration
1. Install Home Assistant on your network
2. Create a Long-Lived Access Token
3. Add the token to your `.env` file
4. Configure your smart devices in Home Assistant

### MQTT Setup
1. Install an MQTT broker (e.g., Mosquitto)
2. Configure device topics
3. Update MQTT settings in `.env`

## 🔧 Troubleshooting

### Common Issues

**Camera not working:**
```bash
# Check camera permissions
sudo usermod -a -G video $USER
# Reboot required
sudo reboot
```

**Audio not working:**
```bash
# Check audio devices
aplay -l
# Set default audio device
sudo raspi-config
```

**Bluetooth issues:**
```bash
# Check Bluetooth status
hciconfig
# Restart Bluetooth service
sudo systemctl restart bluetooth
```

**LLM model not loading:**
- Ensure the model file exists in `models/` directory
- Check file permissions
- Verify the model is in GGUF format

### Performance Optimization

**For better performance:**
1. Use a smaller LLM model (e.g., 3B parameters)
2. Reduce camera resolution
3. Close unnecessary background processes
4. Use a high-speed microSD card

## 📁 Project Structure

```
ai-assistant-raspberry-pi/
├── ai_assistant.py          # Main assistant application
├── config.py               # Configuration management
├── llm_module.py           # Language model interface
├── voice_module.py         # Speech recognition and synthesis
├── object_detection_module.py  # Computer vision
├── home_automation_module.py   # Smart home control
├── requirements.txt        # Python dependencies
├── install.sh             # Installation script
├── start_assistant.sh     # Startup script
├── .env                   # Environment configuration
├── models/                # AI models directory
├── logs/                  # Log files
└── README.md             # This file
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [llama.cpp](https://github.com/ggerganov/llama.cpp) for LLM inference
- [Vosk](https://alphacephei.com/vosk/) for speech recognition
- [Ultralytics YOLO](https://github.com/ultralytics/ultralytics) for object detection
- [Home Assistant](https://www.home-assistant.io/) for home automation
- [Raspberry Pi Foundation](https://www.raspberrypi.org/) for the amazing hardware

## 📞 Support

If you encounter any issues:
1. Check the troubleshooting section
2. Review the logs in the `logs/` directory
3. Open an issue on GitHub
4. Join our community discussions

---

**Happy coding! 🚀** 