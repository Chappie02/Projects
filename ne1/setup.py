#!/usr/bin/env python3
"""
Setup script for Raspberry Pi 5 LLM System
This script installs dependencies and configures the system
"""

import subprocess
import sys
import os
import platform
import logging

def run_command(command, description):
    """Run a shell command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, 
                              capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def check_system():
    """Check if running on Raspberry Pi"""
    print("🔍 Checking system requirements...")
    
    # Check if running on Raspberry Pi
    if not os.path.exists('/proc/cpuinfo'):
        print("⚠️  Warning: Not running on Raspberry Pi")
        return False
    
    with open('/proc/cpuinfo', 'r') as f:
        cpuinfo = f.read()
        if 'Raspberry Pi' not in cpuinfo:
            print("⚠️  Warning: Not running on Raspberry Pi")
            return False
    
    print("✅ Running on Raspberry Pi")
    return True

def update_system():
    """Update system packages"""
    print("\n📦 Updating system packages...")
    
    commands = [
        ("sudo apt update", "Updating package list"),
        ("sudo apt upgrade -y", "Upgrading system packages"),
        ("sudo apt install -y python3-pip python3-venv", "Installing Python tools"),
        ("sudo apt install -y git curl wget", "Installing utilities"),
        ("sudo apt install -y libatlas-base-dev", "Installing math libraries"),
        ("sudo apt install -y libhdf5-dev libhdf5-serial-dev", "Installing HDF5"),
        ("sudo apt install -y libqtgui4 libqtwebkit4 libqt4-test", "Installing Qt libraries"),
        ("sudo apt install -y libjasper-dev libqtcore4", "Installing additional libraries"),
        ("sudo apt install -y libavcodec-dev libavformat-dev libswscale-dev", "Installing video libraries"),
        ("sudo apt install -y libv4l-dev libxvidcore-dev libx264-dev", "Installing video codecs"),
        ("sudo apt install -y libgtk-3-dev", "Installing GTK libraries"),
        ("sudo apt install -y libboost-all-dev", "Installing Boost libraries"),
        ("sudo apt install -y libopencv-dev python3-opencv", "Installing OpenCV"),
        ("sudo apt install -y portaudio19-dev", "Installing audio libraries"),
        ("sudo apt install -y espeak", "Installing text-to-speech"),
        ("sudo apt install -y bluetooth bluez", "Installing Bluetooth"),
        ("sudo apt install -y pulseaudio pulseaudio-module-bluetooth", "Installing PulseAudio"),
        ("sudo apt install -y mosquitto mosquitto-clients", "Installing MQTT broker"),
    ]
    
    for command, description in commands:
        if not run_command(command, description):
            print(f"⚠️  Warning: {description} failed, continuing...")

def setup_python_environment():
    """Setup Python virtual environment and install dependencies"""
    print("\n🐍 Setting up Python environment...")
    
    # Create virtual environment
    if not os.path.exists('venv'):
        if not run_command("python3 -m venv venv", "Creating virtual environment"):
            return False
    
    # Activate virtual environment and install dependencies
    venv_python = "venv/bin/python"
    venv_pip = "venv/bin/pip"
    
    # First, upgrade pip and install basic tools
    basic_commands = [
        (f"{venv_pip} install --upgrade pip", "Upgrading pip"),
        (f"{venv_pip} install wheel setuptools", "Installing build tools"),
    ]
    
    for command, description in basic_commands:
        if not run_command(command, description):
            return False
    
    # Install dependencies in groups to handle issues better
    print("\n📦 Installing Python dependencies...")
    
    # Core dependencies first
    core_deps = [
        "numpy>=1.24.0",
        "scipy>=1.11.0",
        "pandas>=2.0.0",
        "matplotlib>=3.7.0",
        "python-dotenv>=1.0.0",
        "psutil>=5.9.0",
        "requests>=2.31.0",
        "paho-mqtt>=1.6.1"
    ]
    
    for dep in core_deps:
        if not run_command(f"{venv_pip} install {dep}", f"Installing {dep}"):
            print(f"⚠️  Warning: Failed to install {dep}")
    
    # Audio dependencies
    audio_deps = [
        "pyaudio>=0.2.11",
        "speechrecognition>=3.10.0",
        "pyttsx3>=2.90",
        "sounddevice>=0.4.6",
        "librosa>=0.10.0"
    ]
    
    for dep in audio_deps:
        if not run_command(f"{venv_pip} install {dep}", f"Installing {dep}"):
            print(f"⚠️  Warning: Failed to install {dep}")
    
    # Web interface dependencies
    web_deps = [
        "flask>=2.3.0",
        "flask-socketio>=5.3.0"
    ]
    
    for dep in web_deps:
        if not run_command(f"{venv_pip} install {dep}", f"Installing {dep}"):
            print(f"⚠️  Warning: Failed to install {dep}")
    
    # Computer vision dependencies
    vision_deps = [
        "opencv-python>=4.8.0",
        "Pillow>=10.0.0",
        "ultralytics>=8.0.0"
    ]
    
    for dep in vision_deps:
        if not run_command(f"{venv_pip} install {dep}", f"Installing {dep}"):
            print(f"⚠️  Warning: Failed to install {dep}")
    
    # LLM dependencies (these might take longer)
    print("\n🤖 Installing LLM dependencies (this may take a while)...")
    llm_deps = [
        "torch>=2.0.0",
        "transformers>=4.30.0",
        "accelerate>=0.20.0",
        "bitsandbytes>=0.41.0",
        "sentencepiece>=0.1.99"
    ]
    
    for dep in llm_deps:
        if not run_command(f"{venv_pip} install {dep}", f"Installing {dep}"):
            print(f"⚠️  Warning: Failed to install {dep}")
    
    # Install RPi.GPIO separately (this is specific to Raspberry Pi)
    print("\n🔌 Installing Raspberry Pi GPIO...")
    if not run_command(f"{venv_pip} install RPi.GPIO>=0.7.1", "Installing RPi.GPIO"):
        print("⚠️  Warning: RPi.GPIO installation failed - this is normal on non-Pi systems")
    
    return True

def setup_bluetooth():
    """Setup Bluetooth audio"""
    print("\n🔵 Setting up Bluetooth...")
    
    commands = [
        ("sudo systemctl enable bluetooth", "Enabling Bluetooth service"),
        ("sudo systemctl start bluetooth", "Starting Bluetooth service"),
        ("sudo usermod -a -G bluetooth $USER", "Adding user to Bluetooth group"),
    ]
    
    for command, description in commands:
        if not run_command(command, description):
            print(f"⚠️  Warning: {description} failed")

def setup_mqtt():
    """Setup MQTT broker"""
    print("\n📡 Setting up MQTT broker...")
    
    commands = [
        ("sudo systemctl enable mosquitto", "Enabling MQTT service"),
        ("sudo systemctl start mosquitto", "Starting MQTT service"),
    ]
    
    for command, description in commands:
        if not run_command(command, description):
            print(f"⚠️  Warning: {description} failed")

def setup_gpio():
    """Setup GPIO permissions"""
    print("\n🔌 Setting up GPIO...")
    
    commands = [
        ("sudo usermod -a -G gpio $USER", "Adding user to GPIO group"),
        ("sudo usermod -a -G dialout $USER", "Adding user to dialout group"),
    ]
    
    for command, description in commands:
        if not run_command(command, description):
            print(f"⚠️  Warning: {description} failed")

def create_startup_script():
    """Create startup script"""
    print("\n🚀 Creating startup script...")
    
    startup_script = """#!/bin/bash
# Raspberry Pi 5 LLM System Startup Script

cd "$(dirname "$0")"
source venv/bin/activate

# Start the main system
python main_system.py
"""
    
    with open('start_system.sh', 'w') as f:
        f.write(startup_script)
    
    run_command("chmod +x start_system.sh", "Making startup script executable")
    
    # Create systemd service
    service_content = """[Unit]
Description=Raspberry Pi 5 LLM System
After=network.target bluetooth.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/llm-system
ExecStart=/home/pi/llm-system/start_system.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
    
    with open('llm-system.service', 'w') as f:
        f.write(service_content)
    
    print("✅ Startup script created")
    print("📝 To enable auto-start: sudo cp llm-system.service /etc/systemd/system/ && sudo systemctl enable llm-system")

def create_config_file():
    """Create configuration file"""
    print("\n⚙️  Creating configuration file...")
    
    config_content = """# Raspberry Pi 5 LLM System Configuration
# Copy this to .env file and modify as needed

# MQTT Configuration
MQTT_BROKER=localhost
MQTT_PORT=1883
MQTT_USERNAME=
MQTT_PASSWORD=

# Bluetooth Configuration
BLUETOOTH_DEVICE_NAME=RaspberryPi5_LLM

# System Configuration
LOG_LEVEL=INFO
"""
    
    with open('.env.example', 'w') as f:
        f.write(config_content)
    
    print("✅ Configuration template created (.env.example)")
    print("📝 Copy .env.example to .env and modify settings as needed")

def download_models():
    """Download required AI models"""
    print("\n🤖 Downloading AI models...")
    
    # This will be done automatically when the system starts
    print("ℹ️  Models will be downloaded automatically on first run")
    print("ℹ️  This may take some time depending on your internet connection")

def main():
    """Main setup function"""
    print("🚀 Raspberry Pi 5 LLM System Setup")
    print("=" * 50)
    
    # Check system
    if not check_system():
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            print("Setup cancelled")
            return
    
    # Update system
    update_system()
    
    # Setup Python environment
    if not setup_python_environment():
        print("❌ Python environment setup failed")
        print("\n🔧 Troubleshooting tips:")
        print("1. Try running: sudo apt install python3-dev")
        print("2. For PyAudio issues: sudo apt install portaudio19-dev")
        print("3. For OpenCV issues: sudo apt install libopencv-dev")
        print("4. For torch issues: pip install torch --index-url https://download.pytorch.org/whl/cpu")
        return
    
    # Setup services
    setup_bluetooth()
    setup_mqtt()
    setup_gpio()
    
    # Create files
    create_startup_script()
    create_config_file()
    
    # Download models
    download_models()
    
    print("\n" + "=" * 50)
    print("✅ Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Copy .env.example to .env and configure settings")
    print("2. Connect your Bluetooth audio device")
    print("3. Connect your camera module")
    print("4. Wire up GPIO devices for home automation")
    print("5. Run: ./start_system.sh")
    print("\n🌐 Web interface will be available at: http://your-pi-ip:5000")
    print("\n🎤 Say 'help' to the system for usage instructions")
    print("\n🔧 If you encounter issues:")
    print("   - Check the logs: tail -f llm_system.log")
    print("   - Test audio: speaker-test -t wav -c 2")
    print("   - Test camera: vcgencmd get_camera")

if __name__ == "__main__":
    main()