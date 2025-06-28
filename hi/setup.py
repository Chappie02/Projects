#!/usr/bin/env python3
"""
Setup script for AI Assistant on Raspberry Pi 5
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def run_command(command, description):
    """Run a shell command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def check_system():
    """Check if we're running on Raspberry Pi"""
    print("🔍 Checking system requirements...")
    
    # Check if we're on Linux (Raspberry Pi)
    if platform.system() != "Linux":
        print("⚠️  This setup is designed for Raspberry Pi (Linux). Some features may not work on other systems.")
    
    # Check Python version
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        print("❌ Python 3.8 or higher is required")
        return False
    
    print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro} detected")
    return True

def install_system_dependencies():
    """Install system-level dependencies"""
    print("\n📦 Installing system dependencies...")
    
    # Update package list
    if not run_command("sudo apt update", "Updating package list"):
        return False
    
    # Install system packages
    packages = [
        "python3-pip",
        "python3-venv",
        "libportaudio2",
        "libportaudiocpp0",
        "portaudio19-dev",
        "python3-pyaudio",
        "espeak",
        "espeak-data",
        "libespeak-dev",
        "libatlas-base-dev",
        "libblas-dev",
        "liblapack-dev",
        "libhdf5-dev",
        "libhdf5-serial-dev",
        "libhdf5-103",
        "libqtgui4",
        "libqtwebkit4",
        "libqt4-test",
        "python3-pyqt5",
        "libjasper-dev",
        "libqtcore4",
        "libqt4-test",
        "libgstreamer1.0-dev",
        "libgstreamer-plugins-base1.0-dev",
        "libgtk-3-dev",
        "libavcodec-dev",
        "libavformat-dev",
        "libswscale-dev",
        "libv4l-dev",
        "libxvidcore-dev",
        "libx264-dev",
        "libjpeg-dev",
        "libpng-dev",
        "libtiff-dev",
        "libatlas-base-dev",
        "gfortran",
        "libbluetooth-dev",
        "libbluetooth3",
        "bluez",
        "bluez-tools"
    ]
    
    for package in packages:
        if not run_command(f"sudo apt install -y {package}", f"Installing {package}"):
            print(f"⚠️  Failed to install {package}, continuing...")
    
    return True

def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating directories...")
    
    directories = [
        "models",
        "logs",
        "config",
        "data"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")
    
    return True

def install_python_dependencies():
    """Install Python dependencies"""
    print("\n🐍 Installing Python dependencies...")
    
    # Upgrade pip
    if not run_command("python3 -m pip install --upgrade pip", "Upgrading pip"):
        return False
    
    # Install dependencies from requirements.txt
    if not run_command("python3 -m pip install -r requirements.txt", "Installing Python packages"):
        return False
    
    return True

def download_models():
    """Download required models"""
    print("\n📥 Downloading models...")
    
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)
    
    # Download Vosk model for speech recognition
    vosk_model_path = models_dir / "vosk-model-small-en-us-0.15"
    if not vosk_model_path.exists():
        print("📥 Downloading Vosk speech recognition model...")
        if run_command(
            "cd models && wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip",
            "Downloading Vosk model"
        ):
            if run_command(
                "cd models && unzip vosk-model-small-en-us-0.15.zip && rm vosk-model-small-en-us-0.15.zip",
                "Extracting Vosk model"
            ):
                print("✅ Vosk model downloaded successfully")
            else:
                print("❌ Failed to extract Vosk model")
        else:
            print("❌ Failed to download Vosk model")
    else:
        print("✅ Vosk model already exists")
    
    # Download YOLO model for object detection
    yolo_model_path = models_dir / "yolov8n.pt"
    if not yolo_model_path.exists():
        print("📥 Downloading YOLO model...")
        if run_command(
            "cd models && wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt",
            "Downloading YOLO model"
        ):
            print("✅ YOLO model downloaded successfully")
        else:
            print("❌ Failed to download YOLO model")
    else:
        print("✅ YOLO model already exists")
    
    return True

def create_env_file():
    """Create .env file with default configuration"""
    print("\n⚙️  Creating configuration file...")
    
    env_content = """# AI Assistant Configuration

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
"""
    
    with open(".env", "w") as f:
        f.write(env_content)
    
    print("✅ Configuration file created (.env)")
    print("📝 Please edit .env file to configure your settings")
    
    return True

def setup_bluetooth():
    """Setup Bluetooth configuration"""
    print("\n🔵 Setting up Bluetooth...")
    
    # Check if Bluetooth is available
    if run_command("hciconfig", "Checking Bluetooth status"):
        print("✅ Bluetooth is available")
        
        # Enable Bluetooth
        run_command("sudo systemctl enable bluetooth", "Enabling Bluetooth service")
        run_command("sudo systemctl start bluetooth", "Starting Bluetooth service")
        
        print("✅ Bluetooth setup completed")
    else:
        print("⚠️  Bluetooth not detected or not available")
    
    return True

def create_startup_script():
    """Create a startup script"""
    print("\n🚀 Creating startup script...")
    
    startup_script = """#!/bin/bash
# AI Assistant Startup Script

cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Start the AI Assistant
python3 ai_assistant.py
"""
    
    with open("start_assistant.sh", "w") as f:
        f.write(startup_script)
    
    # Make it executable
    run_command("chmod +x start_assistant.sh", "Making startup script executable")
    
    print("✅ Startup script created (start_assistant.sh)")
    
    return True

def main():
    """Main setup function"""
    print("🤖 AI Assistant Setup for Raspberry Pi 5")
    print("=" * 50)
    
    # Check system requirements
    if not check_system():
        print("❌ System requirements not met")
        return False
    
    # Install system dependencies
    if not install_system_dependencies():
        print("❌ Failed to install system dependencies")
        return False
    
    # Create directories
    if not create_directories():
        print("❌ Failed to create directories")
        return False
    
    # Install Python dependencies
    if not install_python_dependencies():
        print("❌ Failed to install Python dependencies")
        return False
    
    # Download models
    if not download_models():
        print("❌ Failed to download models")
        return False
    
    # Create configuration
    if not create_env_file():
        print("❌ Failed to create configuration")
        return False
    
    # Setup Bluetooth
    if not setup_bluetooth():
        print("❌ Failed to setup Bluetooth")
        return False
    
    # Create startup script
    if not create_startup_script():
        print("❌ Failed to create startup script")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Edit .env file to configure your settings")
    print("2. Download a LLM model (e.g., llama-2-7b-chat.gguf) to models/ directory")
    print("3. Connect your camera and Bluetooth devices")
    print("4. Configure Home Assistant if you want home automation")
    print("5. Run: python3 ai_assistant.py")
    print("6. Or use: ./start_assistant.sh")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 