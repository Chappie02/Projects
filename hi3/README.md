# Raspberry Pi 5 Chat & Object Detection CLI

This project provides a command-line interface (CLI) app for Raspberry Pi 5 with two operational modes:

- **Chat Mode**: Interact with a lightweight local LLM (DistilGPT2) for conversational AI.
- **Object Detection Mode**: Use a connected camera and a pre-trained MobileNet SSD model to detect and identify objects in real time.

## Features
- Switch between modes using natural language prompts (e.g., "Switch to object detection").
- Real-time object detection with OpenCV and torchvision.
- Lightweight LLM chat using HuggingFace Transformers.

## Setup

1. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

2. **(Optional) For Pi Camera**
   - Ensure `opencv-python` is built with camera support, or use a USB webcam.

3. **Run the app**

   ```bash
   python main.py
   ```

## Usage
- Start in chat mode. Type your message and get a response.
- To switch to object detection, type: `switch to object detection` or similar.
- In object detection mode, the camera window opens. Press `q` to stop detection.
- To return to chat mode, type: `switch to chat mode` or similar.
- Type `exit` or `quit` to close the app.

## Notes
- The first run may take time to download models.
- For best performance, use a Raspberry Pi 5 with sufficient RAM.
- You can customize the LLM or detection model in `chat_mode.py` and `object_detection_mode.py`. 