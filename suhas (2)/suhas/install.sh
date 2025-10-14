#!/bin/bash

# Quick installation script for Raspberry Pi AI Assistant

set -e  # Exit on any error

echo "🤖 Raspberry Pi AI Assistant - Quick Install"
echo "============================================="

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo "⚠️  Warning: This script is optimized for Raspberry Pi"
    echo "   It may work on other Linux systems but is not tested"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check Python version
python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
echo "✓ Python version: $python_version"

# Update system
echo "📦 Updating system packages..."
sudo apt update

# Install system dependencies
echo "📦 Installing system dependencies..."
sudo apt install -y \
    python3-pip \
    python3-venv \
    python3-dev \
    libcamera-dev \
    libcamera-apps \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    liblcms2-dev \
    git \
    wget

# Create virtual environment
echo "🐍 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo "📚 Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "📚 Installing Python dependencies..."
pip install -r requirements.txt

# Create directories
echo "📁 Creating directories..."
mkdir -p data models yolo knowledge_base captured_images

# Make run script executable
chmod +x run.sh

echo ""
echo "🎉 Installation complete!"
echo ""
echo "Next steps:"
echo "1. Download a LLaMA model:"
echo "   wget -O models/llama-2-7b-chat.gguf https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.q4_0.gguf"
echo ""
echo "2. Enable camera (if using Pi camera):"
echo "   sudo raspi-config"
echo "   # Interface Options → Camera → Enable"
echo ""
echo "3. Run the assistant:"
echo "   ./run.sh"
echo ""
echo "Happy AI assisting! 🤖✨"

