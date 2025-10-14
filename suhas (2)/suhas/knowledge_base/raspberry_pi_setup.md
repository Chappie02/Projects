# Raspberry Pi Setup Guide

## Initial Setup

### 1. Operating System Installation
- Download Raspberry Pi OS from the official website
- Use Raspberry Pi Imager to flash the OS to your microSD card
- Enable SSH and configure WiFi during the imaging process

### 2. First Boot Configuration
```bash
sudo raspi-config
```
- Change default password
- Enable SSH
- Enable camera interface
- Expand filesystem
- Set locale and timezone

### 3. System Updates
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv git
```

## Camera Setup

### Enable Camera Interface
```bash
sudo raspi-config
# Navigate to: Interface Options → Camera → Enable
```

### Test Camera
```bash
# Test with libcamera
libcamera-hello --timeout 5000

# Test with picamera2
python3 -c "from picamera2 import Picamera2; print('Camera OK')"
```

## Performance Optimization

### Memory Split
For AI workloads, allocate more RAM to the GPU:
```bash
sudo raspi-config
# Advanced Options → Memory Split → 128
```

### Swap Configuration
Increase swap for better performance:
```bash
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# Change CONF_SWAPSIZE=2048
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

### Thermal Management
Monitor temperature:
```bash
vcgencmd measure_temp
```

Install cooling solutions if temperature exceeds 70°C during AI workloads.
