#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting Raspberry Pi 5 AI Assistant Setup...${NC}"

# 1. System Dependencies
echo -e "${GREEN}[1/5] Installing System Dependencies...${NC}"
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv libopenblas-dev libcamera-dev portaudio19-dev libatlas-base-dev

# 2. Python Dependencies
echo -e "${GREEN}[2/5] Installing Python Dependencies...${NC}"
pip3 install -r requirements.txt

# 3. Create Directories
echo -e "${GREEN}[3/5] Creating Directory Structure...${NC}"
mkdir -p data models logs

# 4. Download Models
echo -e "${GREEN}[4/5] Downloading AI Models...${NC}"

# YOLOv8 Nano
if [ ! -f "models/yolov8n.pt" ]; then
    echo "Downloading YOLOv8n..."
    wget -O models/yolov8n.pt https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt
else
    echo "YOLOv8n already exists."
fi

# Gemma 3 4B GGUF
GEMMA_URL="https://huggingface.co/unsloth/gemma-3-4b-it-GGUF/resolve/main/gemma-3-4b-it-IQ4_XS.gguf"
GEMMA_FILE="models/gemma-3-4b-it-IQ4_XS.gguf"

if [ ! -f "$GEMMA_FILE" ]; then
    echo "Downloading Gemma 3 4B GGUF..."
    wget -O "$GEMMA_FILE" "$GEMMA_URL"
else
    echo "Gemma 3 4B GGUF already exists."
fi

# 5. Permissions
echo -e "${GREEN}[5/5] Setting Permissions...${NC}"
chmod +x main.py

echo -e "${BLUE}Setup Complete! You can now run the assistant with:${NC}"
echo "python3 main.py"
