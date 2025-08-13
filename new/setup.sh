#!/bin/bash

# Raspberry Pi 5 AI Assistant Setup Script
# This script automates the installation process

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[$(date +%H:%M:%S)]${NC} $1"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to check if running on Raspberry Pi
check_raspberry_pi() {
    if [ -f /proc/device-tree/model ]; then
        if grep -q "Raspberry Pi" /proc/device-tree/model; then
            print_success "Raspberry Pi detected"
            return 0
        fi
    fi
    print_warning "Not running on Raspberry Pi - some features may not work"
    return 1
}

# Function to check Python version
check_python() {
    print_status "Checking Python version..."
    if command -v python3 &> /dev/null; then
        python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
            print_success "Python $python_version is compatible"
            return 0
        else
            print_error "Python $python_version is too old. Requires Python 3.8+"
            return 1
        fi
    else
        print_error "Python 3 not found"
        return 1
    fi
}

# Function to install system dependencies
install_system_deps() {
    print_status "Installing system dependencies..."
    
    # Update package list
    sudo apt update
    
    # Install required packages
    sudo apt install -y \
        python3-pip \
        python3-venv \
        python3-libcamera \
        python3-picamera2 \
        libcamera-apps \
        libatlas-base-dev \
        libhdf5-dev \
        libhdf5-serial-dev \
        libjasper-dev \
        libqtcore4 \
        libqtgui4 \
        libqt4-test \
        libavcodec-dev \
        libavformat-dev \
        libswscale-dev \
        libv4l-dev \
        libxvidcore-dev \
        libx264-dev \
        libjpeg-dev \
        libpng-dev \
        libtiff-dev \
        libatlas-base-dev \
        gfortran \
        wget \
        curl \
        git
    
    print_success "System dependencies installed"
}

# Function to install Ollama
install_ollama() {
    print_status "Installing Ollama..."
    
    if command -v ollama &> /dev/null; then
        print_success "Ollama is already installed"
    else
        # Download and install Ollama
        curl -fsSL https://ollama.ai/install.sh | sh
        
        # Start Ollama service
        sudo systemctl enable ollama
        sudo systemctl start ollama
        
        print_success "Ollama installed and started"
    fi
    
    # Wait for Ollama to be ready
    print_status "Waiting for Ollama to be ready..."
    sleep 5
    
    # Test Ollama connection
    if curl -s http://localhost:11434/api/tags > /dev/null; then
        print_success "Ollama is running"
    else
        print_error "Ollama is not responding"
        return 1
    fi
}

# Function to download a model
download_model() {
    local model_name=${1:-"gemma2:2b"}
    
    print_status "Downloading model: $model_name"
    
    if ollama list | grep -q "$model_name"; then
        print_success "Model $model_name is already downloaded"
    else
        ollama pull "$model_name"
        print_success "Model $model_name downloaded"
    fi
}

# Function to create virtual environment
create_venv() {
    print_status "Creating virtual environment..."
    
    if [ -d "ai_assistant_env" ]; then
        print_warning "Virtual environment already exists"
        read -p "Do you want to recreate it? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf ai_assistant_env
        else
            return 0
        fi
    fi
    
    python3 -m venv ai_assistant_env
    print_success "Virtual environment created"
}

# Function to install Python dependencies
install_python_deps() {
    print_status "Installing Python dependencies..."
    
    source ai_assistant_env/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install dependencies
    pip install -r requirements.txt
    
    print_success "Python dependencies installed"
}

# Function to enable camera interface
enable_camera() {
    print_status "Enabling camera interface..."
    
    # Check if camera is already enabled
    if vcgencmd get_camera | grep -q "detected=1"; then
        print_success "Camera interface is already enabled"
        return 0
    fi
    
    print_warning "Camera interface needs to be enabled"
    print_warning "Please run: sudo raspi-config"
    print_warning "Navigate to: Interface Options > Camera > Enable"
    print_warning "Then reboot your Raspberry Pi"
    
    read -p "Have you enabled the camera interface? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_success "Camera interface enabled"
    else
        print_warning "Camera interface not enabled - object detection may not work"
    fi
}

# Function to test installation
test_installation() {
    print_status "Testing installation..."
    
    source ai_assistant_env/bin/activate
    
    # Run test script
    python test_installation.py
    
    print_success "Installation test completed"
}

# Function to create desktop shortcut
create_desktop_shortcut() {
    print_status "Creating desktop shortcut..."
    
    cat > ~/Desktop/ai-assistant.desktop << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=AI Assistant
Comment=Raspberry Pi 5 Multi-Modal AI Assistant
Exec=gnome-terminal --working-directory=$(pwd) -- bash -c "source ai_assistant_env/bin/activate && python main.py"
Icon=applications-science
Terminal=true
Categories=Utility;Science;
EOF
    
    chmod +x ~/Desktop/ai-assistant.desktop
    print_success "Desktop shortcut created"
}

# Main installation function
main() {
    echo "🚀 Raspberry Pi 5 AI Assistant Setup"
    echo "===================================="
    
    # Check if running on Raspberry Pi
    check_raspberry_pi
    
    # Check Python version
    if ! check_python; then
        print_error "Python requirements not met. Exiting."
        exit 1
    fi
    
    # Install system dependencies
    install_system_deps
    
    # Install Ollama
    if ! install_ollama; then
        print_error "Failed to install Ollama. Exiting."
        exit 1
    fi
    
    # Download default model
    download_model "gemma2:2b"
    
    # Create virtual environment
    create_venv
    
    # Install Python dependencies
    install_python_deps
    
    # Enable camera interface
    enable_camera
    
    # Test installation
    test_installation
    
    # Create desktop shortcut
    create_desktop_shortcut
    
    echo ""
    echo "🎉 Installation completed successfully!"
    echo ""
    echo "To start the AI Assistant:"
    echo "1. Activate virtual environment: source ai_assistant_env/bin/activate"
    echo "2. Run the assistant: python main.py"
    echo "3. Or use the desktop shortcut"
    echo ""
    echo "For testing without camera: python main.py --mock"
    echo ""
    echo "For help: python main.py --help"
}

# Check if script is run with sudo
if [ "$EUID" -eq 0 ]; then
    print_error "Please don't run this script as root"
    exit 1
fi

# Run main function
main "$@"
