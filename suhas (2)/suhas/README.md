# Raspberry Pi 5 AI Assistant

A modular Python-based AI assistant designed for Raspberry Pi 5, featuring natural language chat with RAG (Retrieval-Augmented Generation) and real-time object detection capabilities.

## 🚀 Features

### 🤖 Chat Mode
- **Local LLM Integration**: Uses llama.cpp for running large language models locally
- **RAG System**: Retrieval-Augmented Generation with ChromaDB and sentence transformers
- **Context-Aware Responses**: Retrieves relevant information from knowledge base before generating responses
- **Conversation History**: Maintains context across conversation turns

### 🔍 Object Detection Mode
- **YOLOv8 Integration**: Real-time object detection using ultralytics
- **Pi Camera Support**: Native Raspberry Pi camera integration with OpenCV fallback
- **Live Detection**: Continuous object detection with confidence scores
- **Image Capture**: Save detected frames with bounding boxes

### ⚙️ System Management
- **Mode Switching**: Clean switching between different modes
- **Resource Monitoring**: CPU, memory, and temperature monitoring
- **Configuration Management**: JSON-based configuration system
- **Logging**: Comprehensive logging with file and console output

## 📋 Requirements

### Hardware
- Raspberry Pi 5 (recommended) or Pi 4
- Raspberry Pi Camera Module (optional, USB camera fallback available)
- MicroSD card (32GB+ recommended)
- Adequate cooling (recommended for sustained AI workloads)

### Software
- Python 3.11+
- Raspberry Pi OS (64-bit recommended) or Ubuntu/Debian Linux
- At least 4GB RAM (8GB recommended for better performance)

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd raspberry-pi-ai-assistant
```

### 2. Install Dependencies
```bash
# Option 1: Quick install (recommended for Raspberry Pi)
./install.sh

# Option 2: Python setup script
python3 setup.py

# Option 3: Manual installation
# Install system dependencies
sudo apt update
sudo apt install -y python3-pip python3-venv python3-dev
sudo apt install -y libcamera-dev libcamera-apps
sudo apt install -y libjpeg-dev zlib1g-dev libfreetype6-dev liblcms2-dev

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### 3. Download Models

#### LLaMA Model (Required for Chat Mode)
Download a compatible GGUF model (recommended: Llama-2-7B-Chat):
```bash
# Create models directory
mkdir -p models

# Download Llama-2-7B-Chat (example)
wget -O models/llama-2-7b-chat.gguf https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.q4_0.gguf
```

**Note**: YOLOv8 model will be downloaded automatically on first use.

### 4. Configure the System
```bash
# Copy and edit configuration
cp data/config.json.example data/config.json
nano data/config.json
```

Update the model paths in the configuration file:
```json
{
  "llama_cpp": {
    "model_path": "models/llama-2-7b-chat.gguf"
  },
  "yolo": {
    "model_path": "yolo/yolov8n.pt"
  }
}
```

## 🚀 Usage

### Starting the Assistant
```bash
# Option 1: Use the launcher script
./run.sh

# Option 2: Manual start
source venv/bin/activate
python main.py
```

### Main Menu Options
1. **Chat Mode**: Interactive conversation with RAG
2. **Object Detection Mode**: Real-time object detection
3. **System Status**: View system health and statistics
4. **Configuration**: Manage settings
5. **Exit**: Shutdown the assistant

### Chat Mode Commands
- `/help` - Show available commands
- `/stats` - Display system and knowledge base statistics
- `/clear` - Clear conversation history
- `/exit` or `/quit` - Exit chat mode

### Object Detection Mode Commands
- `/help` - Show available commands
- `/stats` - Display detection statistics
- `/save` - Save current frame with detections
- `/clear` - Clear detection history
- `/exit` or `/quit` - Exit detection mode

## 📚 Knowledge Base Setup

### Adding Documents
Place your text documents (`.txt` or `.md` files) in the `knowledge_base/` directory:

```bash
# Example knowledge base structure
knowledge_base/
├── user_manual.txt
├── troubleshooting.md
├── api_documentation.txt
└── faq.md
```

### Ingesting Documents
Documents are automatically ingested when you start chat mode. You can also manually ingest:

```python
# In the Python console or script
from modules.chat_mode import ChatMode
from modules.utils import ConfigManager

config = ConfigManager()
chat = ChatMode(config)
chat.initialize()
count = chat.ingest_knowledge_base("knowledge_base")
print(f"Ingested {count} documents")
```

## ⚙️ Configuration

The system uses a JSON configuration file at `data/config.json`. Key settings:

### LLaMA Settings
```json
{
  "llama_cpp": {
    "model_path": "models/llama-2-7b-chat.gguf",
    "n_ctx": 2048,
    "n_threads": 4,
    "temperature": 0.7,
    "max_tokens": 512
  }
}
```

### YOLO Settings
```json
{
  "yolo": {
    "model_path": "yolo/yolov8n.pt",
    "confidence_threshold": 0.5,
    "iou_threshold": 0.45
  }
}
```

### RAG Settings
```json
{
  "rag": {
    "embedding_model": "all-MiniLM-L6-v2",
    "chunk_size": 512,
    "chunk_overlap": 50,
    "top_k": 3
  }
}
```

### Camera Settings
```json
{
  "camera": {
    "resolution": [640, 480],
    "fps": 30,
    "rotation": 0
  }
}
```

## 🔧 Troubleshooting

### Common Issues

#### 1. Model Not Found
```
Error: Model file not found: models/llama-2-7b-chat.gguf
```
**Solution**: Download the required model and update the configuration path.

#### 2. Camera Not Working
```
Error: Could not open camera
```
**Solutions**:
- Enable camera: `sudo raspi-config` → Interface Options → Camera → Enable
- Check camera connection
- Try USB camera as fallback

#### 3. High Memory Usage
```
Warning: High memory usage: 85.2%
```
**Solutions**:
- Reduce model context size (`n_ctx`)
- Use smaller YOLO model (yolov8n instead of yolov8s)
- Close other applications

#### 4. High Temperature
```
Warning: High temperature: 72.5°C
```
**Solutions**:
- Improve cooling (heat sink, fan)
- Reduce CPU threads
- Lower camera resolution

### Performance Optimization

#### For Better Chat Performance
- Use quantized models (Q4_0, Q4_1)
- Reduce context size if memory is limited
- Increase swap space if needed

#### For Better Object Detection
- Use YOLOv8n (nano) instead of larger models
- Reduce camera resolution
- Lower FPS if needed

## 📁 Project Structure

```
raspberry-pi-ai-assistant/
├── main.py                 # Main system controller
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── modules/               # Core modules
│   ├── __init__.py
│   ├── chat_mode.py       # Chat mode implementation
│   ├── object_detection.py # Object detection implementation
│   ├── rag_engine.py      # RAG system
│   └── utils.py           # Utilities and helpers
├── data/                  # Data and configuration
│   ├── config.json        # Configuration file
│   ├── assistant.log      # Log file
│   └── chroma_db/         # ChromaDB storage
├── models/                # AI models
│   └── llama-2-7b-chat.gguf
├── yolo/                  # YOLO models
│   └── yolov8n.pt
├── knowledge_base/        # Knowledge base documents
│   ├── *.txt
│   └── *.md
└── captured_images/       # Saved detection images
    └── detection_*.jpg
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [llama.cpp](https://github.com/ggerganov/llama.cpp) for efficient LLM inference
- [ultralytics](https://github.com/ultralytics/ultralytics) for YOLOv8 implementation
- [ChromaDB](https://www.trychroma.com/) for vector database
- [sentence-transformers](https://www.sbert.net/) for embeddings
- [picamera2](https://github.com/raspberrypi/picamera2) for Pi camera support

## 📞 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs in `data/assistant.log`
3. Open an issue on GitHub
4. Check system resources and model availability

---

**Happy AI Assisting! 🤖✨**
