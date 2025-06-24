# 🔧 Troubleshooting Guide

This guide helps you resolve common issues when setting up the Raspberry Pi 5 LLM System.

## 🚨 Common Installation Issues

### PyBluez Installation Error

**Error:** `error in PyBluez setup command: use_2to3 is invalid`

**Solution:** 
1. PyBluez has been removed from the requirements. The system now uses system commands for Bluetooth management.
2. If you still need PyBluez, try:
   ```bash
   sudo apt install libbluetooth-dev
   pip install git+https://github.com/pybluez/pybluez.git
   ```

### PyAudio Installation Error

**Error:** `fatal error: 'portaudio.h' file not found`

**Solution:**
```bash
sudo apt install portaudio19-dev python3-dev
pip install pyaudio
```

### OpenCV Installation Error

**Error:** `fatal error: 'opencv2/opencv.hpp' file not found`

**Solution:**
```bash
sudo apt install libopencv-dev python3-opencv
pip install opencv-python
```

### Torch Installation Issues

**Error:** Torch installation takes too long or fails

**Solution:**
```bash
# For CPU-only installation (faster)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# For CUDA (if you have a GPU)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### RPi.GPIO Installation Error

**Error:** `Could not find a version that satisfies the requirement RPi.GPIO`

**Solution:**
```bash
# This is normal on non-Raspberry Pi systems
# On Raspberry Pi, try:
sudo apt install python3-rpi.gpio
pip install RPi.GPIO
```

## 🎤 Audio Issues

### No Audio Output

**Symptoms:** System runs but no sound

**Solutions:**
```bash
# Check audio devices
aplay -l

# Test audio
speaker-test -t wav -c 2

# Check volume
alsamixer

# Restart audio services
sudo systemctl restart pulseaudio
```

### Bluetooth Audio Not Working

**Symptoms:** Bluetooth device paired but no audio

**Solutions:**
```bash
# Check Bluetooth status
bluetoothctl show

# List paired devices
bluetoothctl devices

# Connect to device
bluetoothctl connect <device_mac>

# Set as default audio sink
pactl list short sinks
pactl set-default-sink <sink_id>
```

### Microphone Not Working

**Symptoms:** Voice commands not recognized

**Solutions:**
```bash
# Check microphone
arecord -l

# Test microphone
arecord -d 5 test.wav
aplay test.wav

# Check microphone permissions
sudo usermod -a -G audio $USER
```

## 📹 Camera Issues

### Camera Not Detected

**Symptoms:** Object detection fails

**Solutions:**
```bash
# Check camera status
vcgencmd get_camera

# List video devices
ls /dev/video*

# Enable camera interface
sudo raspi-config
# Navigate to: Interface Options > Camera > Enable

# Test camera
raspistill -o test.jpg
```

### USB Camera Issues

**Symptoms:** USB webcam not working

**Solutions:**
```bash
# Install USB camera support
sudo apt install v4l-utils

# Check USB camera
v4l2-ctl --list-devices

# Test USB camera
ffmpeg -f v4l2 -i /dev/video0 -frames:v 1 test.jpg
```

## 🔌 GPIO Issues

### Permission Denied

**Symptoms:** `RuntimeError: No access to /dev/mem`

**Solutions:**
```bash
# Add user to GPIO group
sudo usermod -a -G gpio $USER

# Add user to dialout group
sudo usermod -a -G dialout $USER

# Reboot or log out and back in
sudo reboot
```

### GPIO Pins Not Working

**Symptoms:** Home automation devices not responding

**Solutions:**
```bash
# Check GPIO permissions
groups $USER

# Test GPIO manually
python3 -c "import RPi.GPIO as GPIO; GPIO.setmode(GPIO.BCM); GPIO.setup(17, GPIO.OUT); GPIO.output(17, GPIO.HIGH)"
```

## 🌐 Web Interface Issues

### Cannot Access Web Interface

**Symptoms:** Browser shows connection refused

**Solutions:**
```bash
# Check if Flask is running
ps aux | grep python

# Check port usage
sudo netstat -tlnp | grep 5000

# Check firewall
sudo ufw status

# Allow port 5000
sudo ufw allow 5000
```

### Web Interface Slow

**Symptoms:** Web interface is unresponsive

**Solutions:**
```bash
# Check system resources
htop

# Check memory usage
free -h

# Restart the system
sudo systemctl restart llm-system
```

## 🤖 LLM Issues

### Model Download Fails

**Symptoms:** System hangs during model download

**Solutions:**
```bash
# Clear model cache
rm -rf ~/.cache/huggingface/

# Download models manually
python -c "from transformers import AutoTokenizer; AutoTokenizer.from_pretrained('microsoft/DialoGPT-medium')"

# Use smaller model
# Edit config.py: LLM_MODEL_NAME = "microsoft/DialoGPT-small"
```

### Out of Memory

**Symptoms:** System crashes or becomes unresponsive

**Solutions:**
```bash
# Check memory usage
free -h

# Increase swap space
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# Change CONF_SWAPSIZE=100 to CONF_SWAPSIZE=2048
sudo dphys-swapfile setup
sudo dphys-swapfile swapon

# Use lighter models
# Edit config.py to use smaller models
```

## 📡 MQTT Issues

### MQTT Connection Failed

**Symptoms:** Home automation not working

**Solutions:**
```bash
# Check MQTT service
sudo systemctl status mosquitto

# Start MQTT service
sudo systemctl start mosquitto

# Check MQTT configuration
sudo nano /etc/mosquitto/mosquitto.conf
```

## 🔄 System Performance Issues

### System Running Slow

**Symptoms:** Delayed responses, high CPU usage

**Solutions:**
```bash
# Check system resources
htop

# Check temperature
vcgencmd measure_temp

# Optimize performance
# 1. Use SSD instead of SD card
# 2. Increase swap space
# 3. Use lighter models
# 4. Reduce camera resolution
```

### High Memory Usage

**Symptoms:** System becomes unresponsive

**Solutions:**
```bash
# Monitor memory
watch -n 1 free -h

# Kill memory-intensive processes
pkill -f python

# Restart system
sudo reboot
```

## 📋 Diagnostic Commands

### System Information
```bash
# Check Raspberry Pi model
cat /proc/cpuinfo | grep Model

# Check OS version
cat /etc/os-release

# Check Python version
python3 --version

# Check available memory
free -h

# Check disk space
df -h
```

### Service Status
```bash
# Check all services
sudo systemctl status bluetooth
sudo systemctl status mosquitto
sudo systemctl status pulseaudio

# Check logs
sudo journalctl -u bluetooth
sudo journalctl -u mosquitto
```

### Network Issues
```bash
# Check network connectivity
ping 8.8.8.8

# Check IP address
ip addr show

# Check DNS
nslookup google.com
```

## 🆘 Getting Help

### Log Files
Check these log files for detailed error information:
```bash
# System logs
tail -f llm_system.log

# Application logs
tail -f /var/log/syslog

# Service logs
sudo journalctl -f
```

### Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| `ModuleNotFoundError` | Missing dependency | Install with pip |
| `Permission denied` | User not in group | Add user to group |
| `No module named 'cv2'` | OpenCV not installed | `sudo apt install python3-opencv` |
| `Bluetooth not available` | Bluetooth service down | `sudo systemctl start bluetooth` |
| `Camera not found` | Camera interface disabled | Enable in raspi-config |

### Performance Optimization Tips

1. **Use SSD storage** instead of SD card
2. **Increase swap space** to 2GB
3. **Use lighter models** (DialoGPT-small instead of medium)
4. **Reduce camera resolution** to 320x240
5. **Close unnecessary services**
6. **Monitor temperature** and add cooling if needed

### Emergency Recovery

If the system becomes completely unresponsive:

```bash
# Force reboot
sudo reboot

# If that doesn't work, unplug power and reconnect

# Check filesystem
sudo fsck /dev/mmcblk0p2

# Reinstall if necessary
# Follow the installation guide again
```

## 📞 Support

If you're still having issues:

1. **Check the logs:** `tail -f llm_system.log`
2. **Search existing issues** in the GitHub repository
3. **Create a new issue** with:
   - Error message
   - System information
   - Steps to reproduce
   - Log files

Remember: Most issues can be resolved by following this guide step by step! 