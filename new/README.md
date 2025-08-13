# Raspberry Pi 5 Multi-Modal AI Assistant

A local multi-modal AI assistant for Raspberry Pi 5 that combines LLM chat capabilities with real-time object detection and analysis.

## Features

### Mode 1: LLM Chat Mode
- Interactive text-based conversation using locally hosted LLM models
- Supports various models via Ollama API (Gemma-2B, Mistral-7B, LLaMA 3 8B)
- Low-latency responses optimized for Raspberry Pi 5

### Mode 2: Object Detection + LLM Summary Mode
- Real-time object detection using YOLOv8
- Automatic LLM analysis of detected objects
- Provides descriptions, use cases, fun facts, and safety information
- Camera integration for live video processing

## System Requirements

- Raspberry Pi 5 (4GB or 8GB RAM recommended)
- Raspberry Pi Camera Module (v2 or v3)
- MicroSD card with at least 16GB storage
- Internet connection for initial setup

## Installation

### 1. Install Ollama

```bash
# Download and install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
sudo systemctl enable ollama
sudo systemctl start ollama

# Download a lightweight model (choose one)
ollama pull gemma2:2b
# or
ollama pull mistral:7b
# or
ollama pull llama2:7b
```

### 2. Install Python Dependencies

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install required system packages
sudo apt install -y python3-pip python3-venv libatlas-base-dev libhdf5-dev libhdf5-serial-dev libatlas-base-dev libjasper-dev libqtcore4 libqtgui4 libqt4-test

# Create virtual environment
python3 -m venv ai_assistant_env
source ai_assistant_env/bin/activate

# Install Python packages
pip install -r requirements.txt
```

### 3. Enable and Install Camera Support (Picamera2 + libcamera)

```bash
# Install libcamera and Picamera2 (Bookworm)
sudo apt update
sudo apt install -y libcamera-apps python3-libcamera python3-picamera2

# Enable camera interface
sudo raspi-config

# Navigate to: Interface Options > Camera > Enable
# Reboot the system
sudo reboot
```

### 4. Test Camera (libcamera/Picamera2)

```bash
# Quick live preview
libcamera-hello -t 5000

# Capture a still image
libcamera-still -o test.jpg

# Optional: Python Picamera2 test (interactive)
python3 - << 'PY'
from picamera2 import Picamera2
picam = Picamera2()
picam.configure(picam.create_still_configuration())
picam.start()
array = picam.capture_array()
print('Captured frame:', array.shape)
picam.stop()
PY
```

## Usage

### Starting the Assistant

```bash
# Activate virtual environment
source ai_assistant_env/bin/activate

# Run the assistant
python main.py
```

### Mode Selection

1. **Chat Mode**: Select "1" for interactive text conversation
2. **Object Detection Mode**: Select "2" for real-time object detection and analysis
3. **Switch Modes**: Press "q" to quit current mode and return to menu
4. **Exit**: Press "x" to exit the program

### Example Usage

#### Chat Mode Example:
```
=== Raspberry Pi 5 AI Assistant ===
1. Chat Mode
2. Object Detection Mode
x. Exit

Select mode: 1

[Chat Mode Active]
You: What can you help me with?
Assistant: I'm your local AI assistant running on your Raspberry Pi 5! I can help you with:
- General questions and conversations
- Programming and technical topics
- Creative writing and brainstorming
- Problem-solving and analysis
- And much more!

What would you like to discuss?
```

#### Object Detection Mode Example:
```
=== Raspberry Pi 5 AI Assistant ===
1. Chat Mode
2. Object Detection Mode
x. Exit

Select mode: 2

[Object Detection Mode Active]
Starting camera...
Detected: coffee mug

🤖 AI Analysis:
A coffee mug is a cylindrical container typically made of ceramic, glass, or metal, designed to hold hot beverages like coffee, tea, or hot chocolate. 

Use cases:
- Drinking hot beverages
- Microwave heating (if microwave-safe)
- Office and home use
- Gift items

Fun fact: The first coffee mugs appeared in the 15th century in the Middle East, where coffee was first cultivated.

Safety: Hot liquids can cause burns. Always check temperature before drinking.

Press 'q' to return to menu, 'x' to exit
```

## Project Structure

```
ai_assistant/
├── main.py                 # Main program entry point
├── llm_interface.py        # Ollama API interface
├── object_detection.py     # YOLOv8 object detection
├── camera_handler.py       # Camera interface
├── utils.py               # Utility functions
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Configuration

### Model Selection

Edit `llm_interface.py` to change the default model:

```python
DEFAULT_MODEL = "gemma2:2b"  # Change to your preferred model
```

### Camera Settings

Adjust camera parameters in `camera_handler.py`:

```python
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_FPS = 30
```

## Troubleshooting

### Common Issues

1. **Ollama not responding**
   ```bash
   # Check if Ollama is running
   sudo systemctl status ollama
   
   # Restart Ollama
   sudo systemctl restart ollama
   ```

2. **Camera not detected**
   ```bash
   # Check camera status
   vcgencmd get_camera
   
   # Enable camera interface
   sudo raspi-config
   ```

3. **Low performance**
   - Use smaller models (2B parameters or less)
   - Reduce camera resolution
   - Close unnecessary background processes

4. **Memory issues**
   - Increase swap space
   - Use quantized models
   - Monitor memory usage with `htop`

### Performance Optimization

- Use quantized models for better performance
- Adjust camera resolution based on needs
- Consider using SSD for faster model loading
- Monitor CPU and memory usage

## Model Recommendations

### For Raspberry Pi 5 (4GB RAM):
- `gemma2:2b` - Fast, good performance
- `llama2:7b-q4_0` - Good balance of performance/quality

### For Raspberry Pi 5 (8GB RAM):
- `mistral:7b` - Better quality responses
- `llama2:7b` - Full model, best quality

## License

This project is open source and available under the MIT License.

## Contributing

Feel free to submit issues and enhancement requests!
