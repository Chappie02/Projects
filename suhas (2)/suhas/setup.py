#!/usr/bin/env python3
"""
Setup script for Raspberry Pi AI Assistant
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


def run_command(command, check=True):
    """Run a shell command and return the result."""
    print(f"Running: {command}")
    try:
        result = subprocess.run(command, shell=True, check=check, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        if e.stderr:
            print(f"Stderr: {e.stderr}")
        return False


def check_python_version():
    """Check if Python version is 3.11+."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print(f"Error: Python 3.11+ required, found {version.major}.{version.minor}")
        return False
    print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
    return True


def install_system_dependencies():
    """Install system dependencies."""
    print("\n📦 Installing system dependencies...")
    
    # Update package list
    if not run_command("sudo apt update"):
        return False
    
    # Install system packages
    packages = [
        "python3-pip",
        "python3-venv", 
        "python3-dev",
        "libcamera-dev",
        "libcamera-apps",
        "libjpeg-dev",
        "zlib1g-dev",
        "libfreetype6-dev",
        "liblcms2-dev",
        "git"
    ]
    
    for package in packages:
        if not run_command(f"sudo apt install -y {package}"):
            print(f"Warning: Failed to install {package}")
    
    return True


def create_virtual_environment():
    """Create and activate virtual environment."""
    print("\n🐍 Setting up virtual environment...")
    
    venv_path = Path("venv")
    if venv_path.exists():
        print("Virtual environment already exists")
        return True
    
    if not run_command(f"{sys.executable} -m venv venv"):
        return False
    
    print("✓ Virtual environment created")
    return True


def install_python_dependencies():
    """Install Python dependencies."""
    print("\n📚 Installing Python dependencies...")
    
    # Use Linux pip path
    pip_path = "venv/bin/pip"
    
    # Upgrade pip first
    if not run_command(f"{pip_path} install --upgrade pip"):
        return False
    
    # Install requirements
    if not run_command(f"{pip_path} install -r requirements.txt"):
        return False
    
    print("✓ Python dependencies installed")
    return True


def create_directories():
    """Create necessary directories."""
    print("\n📁 Creating directories...")
    
    directories = [
        "data",
        "models", 
        "yolo",
        "knowledge_base",
        "captured_images"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✓ Created {directory}/")
    
    return True


def setup_configuration():
    """Setup configuration file."""
    print("\n⚙️ Setting up configuration...")
    
    config_path = Path("data/config.json")
    if config_path.exists():
        print("Configuration file already exists")
        return True
    
    # Create default config
    default_config = """{
  "llama_cpp": {
    "model_path": "models/llama-2-7b-chat.gguf",
    "n_ctx": 2048,
    "n_threads": 4,
    "temperature": 0.7,
    "max_tokens": 512
  },
  "yolo": {
    "model_path": "yolo/yolov8n.pt",
    "confidence_threshold": 0.5,
    "iou_threshold": 0.45
  },
  "rag": {
    "embedding_model": "all-MiniLM-L6-v2",
    "chunk_size": 512,
    "chunk_overlap": 50,
    "top_k": 3
  },
  "camera": {
    "resolution": [640, 480],
    "fps": 30,
    "rotation": 0
  },
  "system": {
    "log_level": "INFO",
    "max_memory_usage": 80.0,
    "max_temperature": 70.0
  }
}"""
    
    with open(config_path, 'w') as f:
        f.write(default_config)
    
    print("✓ Configuration file created")
    return True


def download_sample_models():
    """Download sample models if not present."""
    print("\n🤖 Checking for AI models...")
    
    # Check LLaMA model
    llama_path = Path("models/llama-2-7b-chat.gguf")
    if not llama_path.exists():
        print("⚠️  LLaMA model not found")
        print("   Please download a GGUF model manually:")
        print("   wget -O models/llama-2-7b-chat.gguf https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.q4_0.gguf")
    else:
        print("✓ LLaMA model found")
    
    # YOLO model will be downloaded automatically
    print("✓ YOLO model will be downloaded on first use")
    
    return True


def print_next_steps():
    """Print next steps for the user."""
    print("\n" + "="*60)
    print("🎉 Setup Complete!")
    print("="*60)
    print("\nNext steps:")
    print("1. Download a LLaMA model (if not already done):")
    print("   wget -O models/llama-2-7b-chat.gguf https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.q4_0.gguf")
    print("\n2. Activate virtual environment:")
    print("   source venv/bin/activate")
    print("\n3. Run the AI Assistant:")
    print("   python main.py")
    print("\n4. Add documents to knowledge_base/ for RAG functionality")
    print("\n5. Enable camera interface (if using Pi camera):")
    print("   sudo raspi-config")
    print("="*60)


def main():
    """Main setup function."""
    print("🤖 Raspberry Pi AI Assistant Setup")
    print("="*50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install system dependencies
    if not install_system_dependencies():
        print("Warning: Some system dependencies may not have installed correctly")
    
    # Create virtual environment
    if not create_virtual_environment():
        print("Error: Failed to create virtual environment")
        sys.exit(1)
    
    # Install Python dependencies
    if not install_python_dependencies():
        print("Error: Failed to install Python dependencies")
        sys.exit(1)
    
    # Create directories
    if not create_directories():
        print("Error: Failed to create directories")
        sys.exit(1)
    
    # Setup configuration
    if not setup_configuration():
        print("Error: Failed to setup configuration")
        sys.exit(1)
    
    # Check models
    download_sample_models()
    
    # Print next steps
    print_next_steps()


if __name__ == "__main__":
    main()
