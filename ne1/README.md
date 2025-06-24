# 🤖 Raspberry Pi 5 LLM System

A comprehensive AI assistant system for Raspberry Pi 5 that combines conversational AI, computer vision, and home automation capabilities. The system runs entirely locally and can be controlled via voice commands or a web interface.

## ✨ Features

### 🗣️ **Main Chat Mode**
- Natural language conversation using a local LLM
- Context-aware responses
- Conversation history tracking
- Voice input/output with Bluetooth audio support

### 👁️ **Object Detection Mode**
- Real-time object detection using YOLOv8
- Camera feed processing
- Object identification and description
- Confidence scoring for detected objects

### 🏠 **Home Automation Mode**
- GPIO-based device control (lights, fans, door locks)
- MQTT integration for smart home devices
- Motion detection
- Voice-controlled automation commands

### 🌐 **Web Interface**
- Real-time system monitoring
- Remote control via web browser
- Live camera feed streaming
- Device status dashboard
- Voice command interface

## 🛠️ Hardware Requirements

### Essential Components
- **Raspberry Pi 5** (4GB or 8GB RAM recommended)
- **MicroSD Card** (32GB+ Class 10)
- **Power Supply** (5V/3A minimum)
- **Camera Module** (Pi Camera or USB webcam)
- **Bluetooth Speaker/Headphones**
- **Microphone** (USB or built-in)

### Optional Components
- **Relay modules** for home automation
- **Motion sensors**
- **LED strips** for lighting control
- **Fan modules** for cooling
- **Door lock actuators**

## 📋 Software Requirements

- **Raspberry Pi OS** (Bullseye or newer)
- **Python 3.8+**
- **Git**

## 🚀 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/raspberry-pi-llm-system.git
cd raspberry-pi-llm-system
```

### 2. Run Setup Script
```bash
chmod +x setup.py
python3 setup.py
```

The setup script will:
- Update system packages
- Install required dependencies
- Configure Bluetooth audio
- Setup MQTT broker
- Configure GPIO permissions
- Create startup scripts

### 3. Configure Environment
```bash
cp .env.example .env
nano .env
```

Edit the `.env` file with your specific settings:
```env
# MQTT Configuration
MQTT_BROKER=localhost
MQTT_PORT=1883
MQTT_USERNAME=your_username
MQTT_PASSWORD=your_password

# Bluetooth Configuration
BLUETOOTH_DEVICE_NAME=RaspberryPi5_LLM

# System Configuration
LOG_LEVEL=INFO
```

### 4. Hardware Setup

#### Camera Connection
```bash
# Enable camera in raspi-config
sudo raspi-config
# Navigate to: Interface Options > Camera > Enable
```

#### GPIO Wiring (for home automation)
```
Light 1: GPIO 17
Light 2: GPIO 18
Fan: GPIO 27
Door Lock: GPIO 22
Motion Sensor: GPIO 23
```

#### Bluetooth Audio Setup
```bash
# Pair your Bluetooth device
bluetoothctl
scan on
pair <device_mac>
connect <device_mac>
trust <device_mac>
```

## 🎯 Usage

### Starting the System
```bash
# Manual start
./start_system.sh

# Or activate virtual environment and run directly
source venv/bin/activate
python main_system.py
```

### Voice Commands

#### Mode Switching
- **"Switch to chat mode"** - Enter conversation mode
- **"Enable object detection"** - Enter vision mode
- **"Home automation mode"** - Enter automation mode

#### General Commands
- **"Hello"** - Start a conversation
- **"What's the weather?"** - Ask questions
- **"Help"** - Get usage instructions
- **"Status"** - Check system status
- **"Goodbye"** - Shutdown system

#### Object Detection Commands
- **"What do you see?"** - Analyze current view
- **"Detect objects"** - Scan for objects
- **"Describe the scene"** - Get detailed description

#### Home Automation Commands
- **"Turn on the lights"** - Activate lighting
- **"Turn off the fan"** - Control fan
- **"Lock the door"** - Secure door
- **"Check device status"** - Get device states

### Web Interface

Access the web interface at: `http://your-pi-ip:5000`

Features:
- **Real-time status monitoring**
- **Device control buttons**
- **Live camera feed**
- **Voice command input**
- **Conversation history**
- **Mode switching**

## 🔧 Configuration

### LLM Model
The system uses Microsoft's DialoGPT-medium by default. You can change this in `config.py`:

```python
LLM_MODEL_NAME = "microsoft/DialoGPT-medium"  # Change to your preferred model
```

### Object Detection
Configure detection settings in `config.py`:

```python
OBJECT_DETECTION_MODEL = "yolov8n.pt"  # Use nano model for speed
CONFIDENCE_THRESHOLD = 0.5  # Detection confidence
```

### GPIO Pins
Modify GPIO pin assignments in `config.py`:

```python
GPIO_PINS = {
    "light_1": 17,
    "light_2": 18,
    "fan": 27,
    "door_lock": 22,
    "motion_sensor": 23
}
```

## 📊 System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Voice Input   │    │   Web Interface │    │   GPIO Control  │
│   (Microphone)  │    │   (Flask/Web)   │    │   (Home Auto)   │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────┴─────────────┐
                    │      Main System          │
                    │   (System Controller)     │
                    └─────────────┬─────────────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          │                       │                       │
┌─────────▼────────┐  ┌──────────▼──────────┐  ┌─────────▼────────┐
│   LLM Core       │  │  Object Detection   │  │  Audio Manager   │
│   (Conversation) │  │   (Computer Vision) │  │  (Voice I/O)     │
└──────────────────┘  └──────────────────────┘  └──────────────────┘
```

## 🔍 Troubleshooting

### Common Issues

#### Audio Problems
```bash
# Check audio devices
aplay -l
# Test audio
speaker-test -t wav -c 2

# Fix Bluetooth audio
sudo systemctl restart bluetooth
sudo systemctl restart pulseaudio
```

#### Camera Issues
```bash
# Test camera
vcgencmd get_camera
# Check camera module
ls /dev/video*

# Enable camera interface
sudo raspi-config
```

#### GPIO Problems
```bash
# Check GPIO permissions
groups $USER
# Add user to GPIO group
sudo usermod -a -G gpio $USER
```

#### Model Download Issues
```bash
# Clear model cache
rm -rf ~/.cache/huggingface/
# Download models manually
python -c "from transformers import AutoTokenizer, AutoModelForCausalLM; AutoTokenizer.from_pretrained('microsoft/DialoGPT-medium')"
```

### Performance Optimization

#### For Better Performance
1. **Use SSD instead of SD card**
2. **Increase swap space**
3. **Use lighter models**
4. **Optimize camera resolution**

#### Memory Management
```bash
# Monitor memory usage
htop
# Check available memory
free -h
```

## 🔒 Security Considerations

- Change default passwords
- Use HTTPS for web interface in production
- Restrict network access
- Regular system updates
- Secure MQTT broker configuration

## 📈 Performance Benchmarks

| Component | Response Time | Memory Usage | CPU Usage |
|-----------|---------------|--------------|-----------|
| LLM Chat | 2-5 seconds | 2-4 GB | 30-50% |
| Object Detection | 100-300ms | 1-2 GB | 40-60% |
| Voice Recognition | 1-3 seconds | 100-200 MB | 10-20% |
| Home Automation | <100ms | <50 MB | <5% |

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Hugging Face](https://huggingface.co/) for transformer models
- [Ultralytics](https://ultralytics.com/) for YOLOv8
- [OpenCV](https://opencv.org/) for computer vision
- [Raspberry Pi Foundation](https://www.raspberrypi.org/) for the amazing hardware

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/raspberry-pi-llm-system/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/raspberry-pi-llm-system/discussions)
- **Documentation**: [Wiki](https://github.com/yourusername/raspberry-pi-llm-system/wiki)

---

**Made with ❤️ for the Raspberry Pi community** 