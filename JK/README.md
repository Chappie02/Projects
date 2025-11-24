# Raspberry Pi 5 AI Assistant

A powerful, offline, multi-modal AI Assistant designed specifically for the Raspberry Pi 5. This project integrates Large Language Models (LLM), Retrieval-Augmented Generation (RAG), and Computer Vision (YOLO) into a compact wearable-style device with an OLED display and button interface.

## 🌟 Features

*   **Chat Mode**: Voice-activated AI assistant powered by Llama-3 (via `llama.cpp`).
*   **Vision Mode**: Object detection and description using YOLOv8 and Pi Camera.
*   **Memory (RAG)**: Remembers previous conversations using ChromaDB vector storage.
*   **Offline Capable**: Runs entirely on-device (requires offline TTS/STT configuration for full air-gapped usage).
*   **OLED UI**: Real-time status updates on a 0.96" SSD1306 Display.
*   **Modular Design**: Clean architecture with separated services for easy extension.

## 🛠️ Hardware Requirements

*   **Raspberry Pi 5** (4GB or 8GB RAM recommended)
*   **MicroSD Card** (32GB+ recommended for models)
*   **Pi Camera Module 3** or **Pi Zero 2W Camera** (requires adapter cable)
*   **0.96" OLED Display** (I2C, SSD1306 driver)
*   **USB Microphone** or I2S Microphone HAT
*   **Speaker** (USB or 3.5mm jack)
*   **3x Push Buttons**

### 🔌 Pinout / Wiring

| Component | Pin / Connection | GPIO (BCM) | Description |
| :--- | :--- | :--- | :--- |
| **OLED SDA** | Pin 3 | GPIO 2 | I2C Data |
| **OLED SCL** | Pin 5 | GPIO 3 | I2C Clock |
| **Button K1** | Pin 11 | GPIO 17 | **Trigger** (Action) |
| **Button K2** | Pin 13 | GPIO 27 | **Chat Mode** Select |
| **Button K3** | Pin 15 | GPIO 22 | **Vision Mode** Select |
| **Ground** | Any GND Pin | - | Common Ground |

> **Note**: Buttons should be wired to **Ground** when pressed. The code enables internal Pull-Up resistors.

## 📂 Project Structure

```
/home/suhas/Desktop/JK/
├── app/
│   ├── core/           # Configuration & Logging
│   ├── services/       # AI Engines (Audio, Vision, Memory, LLM)
│   └── hardware/       # Hardware Drivers (OLED, Buttons)
├── data/               # ChromaDB storage (auto-generated)
├── models/             # Place your .gguf and .pt models here
├── logs/               # Application logs
└── main.py             # Application Entry Point
```

## 🚀 Installation

1.  **System Dependencies**:
    Ensure your Pi is up to date and I2C/Camera are enabled (`sudo raspi-config`).
    ```bash
    sudo apt update && sudo apt install -y python3-pip python3-venv libopenblas-dev libcamera-dev portaudio19-dev
    ```

2.  **Clone & Setup**:
    ```bash
    cd /home/suhas/Desktop/JK
    # (Optional) Create a virtual environment
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install Python Packages**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Download Models**:
    You need to place the following models in the `models/` directory:
    *   **LLM**: `llama-3-8b.Q4_K_M.gguf` (or similar GGUF model supported by `llama-cpp-python`)
    *   **YOLO**: `yolov8n.pt` (Ultralytics YOLOv8 Nano)

    *Example download (ensure you have legal rights to use these models):*
    ```bash
    mkdir -p models
    # Download YOLOv8n
    wget -O models/yolov8n.pt https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt
    # LLM must be downloaded manually from HuggingFace (e.g., TheBloke/Llama-2-7B-Chat-GGUF)
    ```

## ⚙️ Configuration

Edit `app/core/config.py` to adjust settings:

*   **Pins**: Change `PIN_K1_TRIGGER`, `PIN_K2_CHAT`, etc.
*   **Models**: Update `LLM_MODEL_PATH` if you use a different filename.
*   **Display**: Adjust `I2C_ADDRESS` if your OLED is `0x3D`.

## 🎮 Usage

Run the main application:
```bash
python3 main.py
```

### Workflow

1.  **Menu**: The screen shows "Select Mode".
2.  **Chat Mode** (Press **K2**):
    *   System listens for your voice.
    *   Speak your query.
    *   System thinks (RAG + LLM) and speaks the response.
    *   Press **K1** to speak again.
3.  **Vision Mode** (Press **K3**):
    *   Screen shows "Press K1 to Capture".
    *   Point camera at object and press **K1**.
    *   System analyzes image and describes what it sees.

## 🐛 Troubleshooting

*   **Camera Error**: Ensure `picamera2` is installed. On Pi 5, this is a system package. The code handles the path import automatically.
*   **I2C Error**: Run `i2cdetect -y 1` to verify your OLED address.
*   **Audio Issues**: Use `alsamixer` to check microphone gain and speaker volume.

## 📜 License

[MIT License](LICENSE)
