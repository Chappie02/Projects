# RPi5 Multi-Modal AI Assistant

A comprehensive multi-modal AI assistant for Raspberry Pi 5 that integrates conversational LLM, object detection, and home automation capabilities.

## Features

- **Wake Word Detection**: Continuously listens for "Jarvis" (configurable)
- **Conversational LLM**: Powered by Ollama with local model inference
- **Object Detection**: Real-time object detection using YOLOv8
- **Home Automation**: Control smart devices via Home Assistant API
- **Speech Recognition**: Convert speech to text using Google Speech Recognition
- **Text-to-Speech**: Natural voice output using pyttsx3
- **Multi-Modal Switching**: Seamlessly switch between different modes

## Hardware Requirements

- Raspberry Pi 5 (4GB or 8GB RAM recommended)
- USB microphone or compatible audio input device
- Bluetooth speaker or audio output device
- USB camera or CSI camera module
- Internet connection for speech recognition and model downloads

## Software Requirements

- Raspberry Pi OS (Bullseye or newer)
- Python 3.8 or higher
- Ollama (for local LLM inference)
- Home Assistant (optional, for home automation)

## Installation

### 1. System Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install system dependencies
sudo apt install -y python3-pip python3-venv
sudo apt install -y portaudio19-dev python3-pyaudio
sudo apt install -y libespeak1 espeak
sudo apt install -y libatlas-base-dev  # For numpy optimization
sudo apt install -y libhdf5-dev libhdf5-serial-dev
sudo apt install -y libqtgui4 libqtwebkit4 libqt4-test python3-pyqt5
sudo apt install -y libjasper-dev libqtcore4 libqt4-test
```

### 2. Install Ollama

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
sudo systemctl enable ollama
sudo systemctl start ollama

# Pull a model (e.g., llama2)
ollama pull llama2
```

### 3. Python Environment Setup

```bash
# Create virtual environment
python3 -m venv ai_assistant_env
source ai_assistant_env/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Home Assistant Setup (Optional)

If you want to use home automation features:

1. Install Home Assistant on your Raspberry Pi or another device
2. Configure your smart devices in Home Assistant
3. Create a Long-Lived Access Token in Home Assistant
4. Update the `config.ini` file with your Home Assistant URL and token

## Configuration

### 1. Edit Configuration File

Edit `config.ini` with your specific settings:

```ini
[Assistant]
wake_word = jarvis  # Change to your preferred wake word
language = en-US
voice_rate = 150
voice_volume = 0.9

[Ollama]
base_url = http://localhost:11434
model = llama2  # Change to your preferred model
timeout = 30

[HomeAssistant]
base_url = http://192.168.1.100:8123  # Your Home Assistant URL
bearer_token = YOUR_BEARER_TOKEN_HERE  # Your Home Assistant token
timeout = 10

[Camera]
device_id = 0  # Camera device ID (0 for default)
resolution_width = 640
resolution_height = 480

[Audio]
sample_rate = 16000
chunk_size = 1024
channels = 1
```

### 2. Home Assistant Token Setup

1. In Home Assistant, go to **Settings** → **Users**
2. Click on your user profile
3. Scroll down to **Long-Lived Access Tokens**
4. Create a new token and copy it
5. Replace `YOUR_BEARER_TOKEN_HERE` in `config.ini`

### 3. Device Mappings

The assistant includes predefined device mappings for common smart home devices. You can modify these in the `control_home_device()` method in `main.py`:

```python
device_mappings = {
    'living room light': 'light.living_room',
    'bedroom light': 'light.bedroom',
    'kitchen light': 'light.kitchen',
    'living room fan': 'fan.living_room',
    'bedroom fan': 'fan.bedroom',
    'thermostat': 'climate.home',
    'tv': 'media_player.living_room_tv'
}
```

## Usage

### 1. Start the Assistant

```bash
# Activate virtual environment
source ai_assistant_env/bin/activate

# Run the assistant
python main.py
```

### 2. Basic Commands

- **Wake Word**: Say "Jarvis" (or your configured wake word)
- **General Questions**: Ask any question after the wake word
- **Object Detection**: Say "What do you see?" or "Switch to object detection mode"
- **Home Automation**: Say "Control my smart home" or "Switch to home automation mode"

### 3. Example Interactions

```
You: "Jarvis"
Assistant: "Yes, I'm listening."

You: "What's the weather like?"
Assistant: [LLM response about weather]

You: "What do you see?"
Assistant: "Switching to object detection mode."
Assistant: "I can see a person, a chair, and a laptop."
Assistant: "Back to main mode."

You: "Control my smart home"
Assistant: "Switching to home automation mode. What would you like me to control?"

You: "Turn on the living room light"
Assistant: "Okay, turning on the living room light."
```

## Troubleshooting

### Audio Issues

1. **Microphone not detected**:
   ```bash
   # Check audio devices
   arecord -l
   
   # Test microphone
   arecord -D hw:1,0 -f S16_LE -r 16000 -c 1 test.wav
   ```

2. **Speaker not working**:
   ```bash
   # Check audio output
   aplay -l
   
   # Test speaker
   speaker-test -t wav -c 2
   ```

### Camera Issues

1. **Camera not detected**:
   ```bash
   # Check camera devices
   ls /dev/video*
   
   # Test camera
   v4l2-ctl --list-devices
   ```

### Ollama Issues

1. **Model not found**:
   ```bash
   # List available models
   ollama list
   
   # Pull a specific model
   ollama pull llama2
   ```

2. **Connection refused**:
   ```bash
   # Check Ollama service
   sudo systemctl status ollama
   
   # Restart Ollama
   sudo systemctl restart ollama
   ```

### Home Assistant Issues

1. **Authentication failed**:
   - Verify your bearer token is correct
   - Check that the token has the necessary permissions

2. **Connection timeout**:
   - Verify your Home Assistant URL is correct
   - Check network connectivity

## Performance Optimization

### For Raspberry Pi 5

1. **Enable GPU acceleration**:
   ```bash
   # Enable OpenGL driver
   sudo raspi-config
   # Navigate to Advanced Options → GL Driver → GL (Fake KMS)
   ```

2. **Increase swap space** (if using 4GB model):
   ```bash
   # Edit swap configuration
   sudo nano /etc/dphys-swapfile
   # Set CONF_SWAPSIZE=2048
   sudo systemctl restart dphys-swapfile
   ```

3. **Use lighter models**:
   - Use `llama2:7b` instead of larger models
   - Consider using `yolov8n.pt` (nano) for faster object detection

## Security Considerations

1. **Network Security**: Ensure your Home Assistant instance is properly secured
2. **API Tokens**: Keep your Home Assistant bearer token secure
3. **Microphone Access**: Be aware that the assistant is always listening for the wake word
4. **Camera Privacy**: The camera is only activated during object detection mode

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is open source and available under the MIT License.

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review the logs in `ai_assistant.log`
3. Ensure all dependencies are properly installed
4. Verify your configuration settings 