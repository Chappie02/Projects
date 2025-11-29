#!/bin/bash
# Setup script for Offline Multi-Modal AI Assistant

set -e

echo "=========================================="
echo "AI Assistant Setup Script"
echo "=========================================="

# Check if running on Raspberry Pi
if [ ! -f /proc/device-tree/model ] || ! grep -q "Raspberry Pi" /proc/device-tree/model; then
    echo "Warning: This script is designed for Raspberry Pi"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Update system
echo "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install system dependencies
echo "Installing system dependencies..."
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

# Add user to required groups
echo "Adding user to required groups..."
sudo usermod -a -G gpio,audio,i2c $USER

# Create necessary directories
echo "Creating directories..."
mkdir -p models
mkdir -p object_models
mkdir -p memory
mkdir -p /home/pi/Object_Captures

# Upgrade pip
echo "Upgrading pip..."
pip3 install --upgrade pip setuptools wheel

# Install Python packages
echo "Installing Python packages..."
pip3 install -r requirements.txt

echo ""
echo "=========================================="
echo "Setup complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Enable camera: sudo raspi-config -> Interface Options -> Camera"
echo "2. Enable I2C: sudo raspi-config -> Interface Options -> I2C"
echo "3. Download LLM model to models/ directory"
echo "4. (Optional) Download YOLO model to object_models/ directory"
echo "5. Log out and back in for group changes to take effect"
echo "6. Run: python3 main.py"
echo ""

