# Raspberry Pi Multi-Modal AI Assistant

A local, privacy-first AI assistant for Raspberry Pi 5 (4GB+), supporting:
- **Chat Mode**: Local LLM chat (Ollama or llama-cpp-python)
- **Object Detection Mode**: Camera capture + YOLOv8n, scene summary via LLM
- **Home Automation Mode**: Control Wi-Fi smart devices via Home Assistant or MQTT

## Features
- CLI interface with automatic mode switching
- All models run locally (no cloud dependencies)
- Modular, extensible codebase
- Easy configuration via `config/config.json`

## Requirements
- Python 3.9+
- Raspberry Pi 5 (4GB RAM, 256GB NVMe recommended)
- [Ollama](https://ollama.com/) or [llama-cpp-python](https://github.com/abetlen/llama-cpp-python)
- [ultralytics](https://github.com/ultralytics/ultralytics) (`pip install ultralytics`)
- [opencv-python](https://pypi.org/project/opencv-python/)
- [requests](https://pypi.org/project/requests/)
- [paho-mqtt](https://pypi.org/project/paho-mqtt/) (if using MQTT)

## Installation
```bash
# Clone repo
$ git clone <repo-url>
$ cd <repo-folder>

# Install dependencies
$ pip install -r requirements.txt

# Download models (see config/config.json for paths)
# - YOLOv8n: https://github.com/ultralytics/ultralytics
# - LLM: e.g., phi-2, mistral-7b (quantized)
```

## Configuration
Edit `config/config.json` to set model paths, Home Assistant/MQTT endpoints, and API keys.

## Usage
```bash
$ python main.py
```
- Type your request at the prompt.
- The assistant will switch modes based on your input:
  - **Chat**: General questions, conversation
  - **Object Detection**: e.g., "What do you see?", "Detect objects"
  - **Home Automation**: e.g., "Turn on the light", "Switch off fan"
- Type `exit` to quit.

## Example
```
[llm_chat] > Hello!
Hi there! How can I help you today?
[llm_chat] > What do you see?
Switching to Object Detection mode.
Detected objects: laptop, bottle
Scene summary: You might be working at a desk with a laptop and water bottle.
[object_detection] > Turn on the light
Switching to Home Automation mode.
[home_automation] > [Light turn on command sent]
```

## Notes
- All processing is local. No cloud APIs are used.
- For best performance, use quantized models (Q4 or smaller).
- Voice input expansion is planned (see code comments).

## License
MIT 