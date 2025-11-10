# Voice and Hardware Setup Guide

This guide explains how to set up the voice and hardware features for the Raspberry Pi 5 Multimodal AI Assistant.

## Hardware Requirements

### 1. OLED Display (SSD1306)
- **Type**: 0.96-inch OLED display (128x64 pixels)
- **Interface**: I2C
- **Address**: 0x3C (default)
- **Connections**:
  - VCC → 3.3V
  - GND → GND
  - SDA → GPIO 2 (Pin 3)
  - SCL → GPIO 3 (Pin 5)

### 2. Rotary Switch (3-Position)
- **Type**: 3-position rotary switch
- **Connections**:
  - Position 1 (Chat Mode) → GPIO 17 (Pin 11)
  - Position 2 (Object Mode) → GPIO 27 (Pin 13)
  - Position 3 (Exit) → GPIO 22 (Pin 15)
  - Common → GND (with pull-up resistors enabled in software)

### 3. Bluetooth Audio
- **Microphone**: Bluetooth headset or microphone
- **Speaker**: Bluetooth speaker or headset
- **Setup**: Pair Bluetooth devices via Raspberry Pi's Bluetooth settings

## Software Installation

### 1. System Dependencies

```bash
# Update system
sudo apt-get update
sudo apt-get upgrade

# Install audio dependencies
sudo apt-get install -y python3-pyaudio portaudio19-dev
sudo apt-get install -y espeak espeak-data libespeak1 libespeak-dev

# Install I2C tools
sudo apt-get install -y i2c-tools python3-smbus

# Enable I2C interface
sudo raspi-config
# Navigate to: Interface Options → I2C → Enable
```

### 2. Python Dependencies

```bash
# Activate virtual environment
source venv/bin/activate

# Install new dependencies
pip install -r requirements.txt

# If pyaudio fails, install system packages first:
sudo apt-get install portaudio19-dev python3-pyaudio
```

### 3. Vosk Model Download

The voice recognition uses Vosk for speech-to-text. Download a Vosk model:

```bash
# Create models directory if it doesn't exist
mkdir -p models

# Download small English model (recommended for Raspberry Pi)
cd models
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip
rm vosk-model-small-en-us-0.15.zip
cd ..
```

Or use the helper function in the code:
```python
from utils.voice_recognition import download_vosk_model
download_vosk_model("vosk-model-small-en-us-0.15")
```

## Hardware Setup

### 1. Enable I2C Interface

```bash
sudo raspi-config
# Interface Options → I2C → Enable
sudo reboot
```

### 2. Test I2C Connection

```bash
# Scan for I2C devices
sudo i2cdetect -y 1

# You should see your OLED display at address 0x3C
```

### 3. Test OLED Display

```bash
python3 -c "from utils.oled_display import OLEDDisplay; d = OLEDDisplay(); d.show_status('Test', 'OLED Working'); import time; time.sleep(2)"
```

### 4. Test GPIO Rotary Switch

```bash
python3 -c "from utils.gpio_utils import RotarySwitch; s = RotarySwitch(); import time; [print(s.get_mode_name()) or time.sleep(1) for _ in range(10)]"
```

### 5. Test Audio Devices

```bash
# List audio devices
python3 -c "from utils.audio_utils import test_audio_devices; test_audio_devices()"

# Test microphone
python3 -c "from utils.audio_utils import AudioManager; a = AudioManager(); data = a.record_audio(2); print('Recording complete')"

# Test speaker
python3 -c "from utils.text_to_speech import TextToSpeech; tts = TextToSpeech(); tts.speak('Hello, this is a test')"
```

## Bluetooth Audio Setup

### 1. Pair Bluetooth Devices

```bash
# Install Bluetooth tools
sudo apt-get install -y bluetooth bluez

# Start Bluetooth service
sudo systemctl start bluetooth
sudo systemctl enable bluetooth

# Scan for devices
bluetoothctl
# In bluetoothctl:
#   scan on
#   (wait for your device to appear)
#   pair <device_address>
#   trust <device_address>
#   connect <device_address>
#   exit
```

### 2. Set Bluetooth as Default Audio

```bash
# Install pulseaudio
sudo apt-get install -y pulseaudio pulseaudio-module-bluetooth

# Restart pulseaudio
pulseaudio -k
pulseaudio --start

# Set Bluetooth device as default (use pavucontrol for GUI)
pavucontrol
# Or use pactl commands:
pactl set-default-sink <bluetooth_sink_name>
pactl set-default-source <bluetooth_source_name>
```

## Configuration

### 1. Update config.py

Edit `config.py` to adjust hardware settings:

```python
# OLED Display Configuration
OLED_CONFIG = {
    'enabled': True,
    'width': 128,
    'height': 64,
    'i2c_address': 0x3C,  # Change if your display uses different address
}

# GPIO Rotary Switch Configuration
GPIO_CONFIG = {
    'enabled': True,
    'pin_chat': 17,      # Change GPIO pins if needed
    'pin_object': 27,
    'pin_exit': 22,
}

# Audio Configuration
AUDIO_CONFIG = {
    'sample_rate': 16000,
    'chunk_size': 4096,
    'use_bluetooth': True,  # Set to False to use default audio devices
}

# Wake Word Configuration
WAKE_WORD_CONFIG = {
    'enabled': True,
    'wake_words': ["hey pi", "hey pie", "hi pi", "wake up"],
    'require_wake_word': True,  # Set to False to always listen
}

# Voice Recognition Configuration
VOICE_RECOGNITION_CONFIG = {
    'enabled': True,
    'engine': 'vosk',  # 'vosk' or 'whisper'
    'vosk_model': 'vosk-model-small-en-us-0.15',
}

# Text-to-Speech Configuration
TTS_CONFIG = {
    'enabled': True,
    'engine': 'espeak',  # 'espeak', 'pyttsx3', or 'gtts'
    'rate': 150,
    'speak_mode_changes': True,
    'speak_responses': False,  # Set to True to speak LLM responses
}
```

## Usage

### 1. Start the Application

```bash
# Activate virtual environment
source venv/bin/activate

# Run the application
python main.py
```

### 2. Control Methods

#### GPIO Rotary Switch
- **Position 1**: Switch to Chat Mode
- **Position 2**: Switch to Object Detection Mode
- **Position 3**: Exit the application

#### Voice Commands
1. Say "Hey Pi" to wake up the assistant
2. Then say one of:
   - "Switch to chat mode" or "Chat mode"
   - "Switch to object mode" or "Object mode"
   - "Exit" or "Exit assistant"
   - "What is this" (in Object Mode)

#### Keyboard Input
- Type commands if voice is not available
- Works as fallback when hardware is disabled

### 3. OLED Display

The OLED display shows:
- Current mode (Chat Mode, Object Mode, etc.)
- Status (Listening, Processing, Ready, etc.)
- Wake word detection
- Error messages

## Troubleshooting

### OLED Display Not Working

1. Check I2C connection:
   ```bash
   sudo i2cdetect -y 1
   ```

2. Verify I2C is enabled:
   ```bash
   sudo raspi-config
   # Interface Options → I2C → Enable
   ```

3. Check wiring (SDA/SCL, VCC/GND)

4. Try different I2C address in config.py

### GPIO Switch Not Working

1. Check GPIO pin connections
2. Verify pull-up resistors (software pull-ups are enabled by default)
3. Test GPIO pins:
   ```bash
   python3 -c "import RPi.GPIO as GPIO; GPIO.setmode(GPIO.BCM); GPIO.setup(17, GPIO.IN); print(GPIO.input(17))"
   ```

### Audio Not Working

1. Check Bluetooth connection:
   ```bash
   bluetoothctl
   # devices
   # info <device_address>
   ```

2. Verify audio devices:
   ```bash
   python3 -c "from utils.audio_utils import test_audio_devices; test_audio_devices()"
   ```

3. Test microphone:
   ```bash
   arecord -d 3 -f cd test.wav
   aplay test.wav
   ```

4. Test speaker:
   ```bash
   espeak "Hello, this is a test"
   ```

### Voice Recognition Not Working

1. Verify Vosk model is downloaded:
   ```bash
   ls -la models/vosk-model-small-en-us-0.15/
   ```

2. Test voice recognition:
   ```python
   from utils.voice_recognition import VoiceRecognizer
   from utils.audio_utils import AudioManager
   
   audio = AudioManager()
   recognizer = VoiceRecognizer()
   
   # Record audio
   audio_data = audio.record_audio(3.0)
   audio.save_audio(audio_data, "test.wav")
   
   # Recognize
   text = recognizer.recognize_audio_file("test.wav")
   print(f"Recognized: {text}")
   ```

### Wake Word Not Detected

1. Check wake word configuration in config.py
2. Verify voice recognition is working
3. Try speaking clearly and closer to microphone
4. Adjust sensitivity if using Porcupine (not implemented in current version)

## Advanced Configuration

### Using Different TTS Engine

1. **pyttsx3** (cross-platform, may require additional setup):
   ```bash
   pip install pyttsx3
   ```
   Update config.py: `'engine': 'pyttsx3'`

2. **Google TTS** (requires internet):
   ```bash
   pip install gtts playsound
   ```
   Update config.py: `'engine': 'gtts'`

### Using Whisper.cpp Instead of Vosk

1. Install whisper.cpp:
   ```bash
   git clone https://github.com/ggerganov/whisper.cpp.git
   cd whisper.cpp
   make
   ```

2. Download Whisper model:
   ```bash
   bash ./models/download-ggml-model.sh base.en
   ```

3. Update config.py:
   ```python
   VOICE_RECOGNITION_CONFIG = {
       'engine': 'whisper',
       'model_path': './whisper.cpp/models/ggml-base.en.bin',
   }
   ```

## Notes

- The system works without hardware (OLED, GPIO) - it will fall back to text/console mode
- Voice features can be disabled in config.py if not needed
- Bluetooth audio is preferred but system audio devices will work as fallback
- Wake word detection uses simple keyword matching - for production, consider using Porcupine or similar
- TTS responses can be slow - disable `speak_responses` in config for faster interaction

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review configuration in config.py
3. Test individual components using test scripts
4. Check system logs for errors

