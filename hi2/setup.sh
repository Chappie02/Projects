#!/bin/bash

# RPi5 Multi-Modal AI Assistant Setup Script
# This script automates the installation process on Raspberry Pi

set -e  # Exit on any error

echo "=========================================="
echo "RPi5 Multi-Modal AI Assistant Setup"
echo "=========================================="

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo; then
    echo "Warning: This script is designed for Raspberry Pi. Continue anyway? (y/n)"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "Setup cancelled."
        exit 1
    fi
fi

# Update system
echo "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install system dependencies
echo "Installing system dependencies..."
sudo apt install -y python3-pip python3-venv
sudo apt install -y portaudio19-dev python3-pyaudio
sudo apt install -y libespeak1 espeak
sudo apt install -y libatlas-base-dev
sudo apt install -y libhdf5-dev libhdf5-serial-dev
sudo apt install -y libqtgui4 libqtwebkit4 libqt4-test python3-pyqt5
sudo apt install -y libjasper-dev libqtcore4 libqt4-test
sudo apt install -y curl wget git

# Install Ollama
echo "Installing Ollama..."
if ! command -v ollama &> /dev/null; then
    curl -fsSL https://ollama.ai/install.sh | sh
    echo "Ollama installed successfully"
else
    echo "Ollama is already installed"
fi

# Start Ollama service
echo "Starting Ollama service..."
sudo systemctl enable ollama
sudo systemctl start ollama

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv ai_assistant_env

# Activate virtual environment and install Python packages
echo "Installing Python dependencies..."
source ai_assistant_env/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Create log file
touch ai_assistant.log

# Set up configuration
echo "Setting up configuration..."
if [ ! -f config.ini ]; then
    echo "Configuration file not found. Creating default config.ini..."
    # The config.ini should already exist from the main.py creation
fi

# Test audio devices
echo "Testing audio devices..."
echo "Available audio input devices:"
arecord -l || echo "No audio input devices found"

echo "Available audio output devices:"
aplay -l || echo "No audio output devices found"

# Test camera
echo "Testing camera..."
if ls /dev/video* &> /dev/null; then
    echo "Camera devices found:"
    ls /dev/video*
else
    echo "No camera devices found"
fi

# Pull default Ollama model
echo "Pulling default Ollama model (llama2)..."
echo "This may take a while depending on your internet connection..."
ollama pull llama2

echo "=========================================="
echo "Setup completed successfully!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit config.ini with your specific settings"
echo "2. If using Home Assistant, add your bearer token to config.ini"
echo "3. Activate the virtual environment: source ai_assistant_env/bin/activate"
echo "4. Run the assistant: python main.py"
echo ""
echo "For troubleshooting, see README.md"
echo "==========================================" 