#!/bin/bash

echo "🤖 AI Assistant Setup for Raspberry Pi 5"
echo "=========================================="

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo "⚠️  This setup is designed for Raspberry Pi. Some features may not work on other systems."
fi

# Update system
echo "🔄 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install system dependencies
echo "📦 Installing system dependencies..."
sudo apt install -y \
    python3-pip \
    python3-venv \
    libportaudio2 \
    libportaudiocpp0 \
    portaudio19-dev \
    python3-pyaudio \
    espeak \
    espeak-data \
    libespeak-dev \
    libatlas-base-dev \
    libblas-dev \
    liblapack-dev \
    libhdf5-dev \
    libhdf5-serial-dev \
    libhdf5-103 \
    libqtgui4 \
    libqtwebkit4 \
    libqt4-test \
    python3-pyqt5 \
    libjasper-dev \
    libqtcore4 \
    libqt4-test \
    libgstreamer1.0-dev \
    libgstreamer-plugins-base1.0-dev \
    libgtk-3-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libxvidcore-dev \
    libx264-dev \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    gfortran \
    libbluetooth-dev \
    libbluetooth3 \
    bluez \
    bluez-tools \
    wget \
    unzip

# Create directories
echo "📁 Creating directories..."
mkdir -p models logs config data

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

# Download models
echo "📥 Downloading models..."

# Download Vosk model
if [ ! -d "models/vosk-model-small-en-us-0.15" ]; then
    echo "📥 Downloading Vosk speech recognition model..."
    cd models
    wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
    unzip vosk-model-small-en-us-0.15.zip
    rm vosk-model-small-en-us-0.15.zip
    cd ..
    echo "✅ Vosk model downloaded successfully"
else
    echo "✅ Vosk model already exists"
fi

# Download YOLO model
if [ ! -f "models/yolov8n.pt" ]; then
    echo "📥 Downloading YOLO model..."
    cd models
    wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt
    cd ..
    echo "✅ YOLO model downloaded successfully"
else
    echo "✅ YOLO model already exists"
fi

# Create .env file
echo "⚙️  Creating configuration file..."
cat > .env << EOF
# AI Assistant Configuration

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
HOME_ASSISTANT_TOKEN=
MQTT_BROKER=localhost
MQTT_PORT=1883

# Bluetooth Settings
BLUETOOTH_DEVICE_NAME=RaspberryPi5
EOF

echo "✅ Configuration file created (.env)"

# Setup Bluetooth
echo "🔵 Setting up Bluetooth..."
sudo systemctl enable bluetooth
sudo systemctl start bluetooth

# Create startup script
echo "🚀 Creating startup script..."
cat > start_assistant.sh << 'EOF'
#!/bin/bash
# AI Assistant Startup Script

cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Start the AI Assistant
python3 ai_assistant.py
EOF

chmod +x start_assistant.sh
echo "✅ Startup script created (start_assistant.sh)"

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Edit .env file to configure your settings"
echo "2. Download a LLM model (e.g., llama-2-7b-chat.gguf) to models/ directory"
echo "3. Connect your camera and Bluetooth devices"
echo "4. Configure Home Assistant if you want home automation"
echo "5. Run: python3 ai_assistant.py"
echo "6. Or use: ./start_assistant.sh"
echo ""
echo "🔗 Useful links:"
echo "- LLM models: https://huggingface.co/TheBloke"
echo "- Vosk models: https://alphacephei.com/vosk/models"
echo "- Home Assistant: https://www.home-assistant.io/" 