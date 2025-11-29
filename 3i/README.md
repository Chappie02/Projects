# Multi-Modal AI Assistant on Raspberry Pi 5

An on-device chatbot and object-detection assistant for Raspberry Pi 5 combining voice I/O, RAG-enhanced LLM responses, and YOLO-based visual perception.

## Hardware Summary

- Raspberry Pi 5 running 64-bit Raspberry Pi OS
- Raspberry Pi Camera Module (Picamera2 stack)
- USB microphone + USB speaker
- 128x64 OLED display (Adafruit SSD1306 over I2C)
- Buttons:
  - `K1` → GPIO17 (pin 11) – select Chat mode
  - `K2` → GPIO27 (pin 13) – select Object mode
  - `K3` → GPIO22 (pin 15) – hold-to-speak / capture trigger

## Project Layout

```
src/
 ├─ main.py              # Controller and state machine
 ├─ audio_manager.py     # STT, TTS, USB audio capture/playback
 ├─ button_manager.py    # GPIO setup and callbacks
 ├─ config.py            # Dataclasses with configurable paths/pins
 ├─ display_manager.py   # OLED text rendering helpers
 ├─ llm_manager.py       # llama.cpp integration + ChromaDB RAG
 ├─ vision_manager.py    # Picamera2 capture + YOLO detections
 └─ memory/              # Persistent ChromaDB store
requirements.txt
README.md
```

## Software Setup

1. **System prep**

   ```bash
   sudo apt update && sudo apt install -y python3-dev python3-venv libatlas-base-dev ffmpeg
   ```

2. **Create a Python environment**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Pre-upgrade packaging tools** (prevents build hiccups on the Pi per best practice):

   ```bash
   pip install --upgrade pip setuptools wheel
   ```

4. **Install project dependencies**

   ```bash
   pip install -r requirements.txt
   ```

5. **Model + voice assets**

   - Place your `llama.cpp` GGUF model under `/home/pi/models/llama.cpp/`.
   - Copy the custom YOLOv8/YOLOv5 weights to `/home/pi/models/yolov8.pt`.
   - Download a Piper voice and update the `AudioConfig.tts_voice_path` if needed.
   - (Optional) Download a Vosk STT model and set `AudioConfig.vosk_model_path`.

6. **Enable hardware interfaces**

   ```bash
   sudo raspi-config  # Enable I2C and camera
   ```

## Usage

```bash
source .venv/bin/activate
python -m src.main
```

### Modes

- **Boot** – OLED displays selection instructions.
- **Chat Mode** – `K1` switches here. OLED shows `Chat Mode - Hold K3 to Speak`. Hold `K3` to capture audio. On release the assistant:
  1. Runs Whisper/Vosk STT.
  2. Retrieves similar past chats from ChromaDB.
  3. Generates a response with llama.cpp (Gemma/Llama-3 GGUF).
  4. Stores the exchange back into memory and speaks via Piper.

- **Object Mode** – `K2` switches here. OLED shows `Object Mode - Press K3 to Capture`. Press `K3` to:
  1. Capture a frame with Picamera2.
  2. Save it under `/home/pi/Object_Captures/`.
  3. Run YOLO inference and collect the detected class names.
  4. Summarize detections with the LLM and speak the result.

Mode buttons work at any time; the K3 behavior adapts to the active mode.

## Customization

- Adjust pins, model paths, and audio preferences inside `src/config.py`.
- `memory/` holds the ChromaDB persistent store—retain it between sessions for richer context.
- Extend `DisplayManager` if you add new UI screens.

## Troubleshooting

- **Audio device busy**: Verify no other service (PulseAudio, PipeWire) locks the USB mic/speaker; update `AudioConfig.mic_device` / `speaker_device`.
- **No camera feed**: Ensure Picamera2 is enabled, and you have the latest firmware.
- **TTS/LLM slow**: Lower `LLMConfig.max_tokens` or switch to a smaller GGUF model; for Piper, select a lighter voice or reduce sample rate.
- **ChromaDB missing**: Delete `src/memory/` if the DB becomes corrupted; it will be recreated automatically.

## License

MIT-style use permitted; adapt as needed for your lab or deployment.

