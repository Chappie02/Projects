"""
Utility functions for Raspberry Pi 5 AI Assistant
"""

import logging
import sys
import time
from typing import Optional, Dict, Any
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('ai_assistant.log')
    ]
)

logger = logging.getLogger(__name__)

def setup_logging(level: str = "INFO") -> None:
    """Setup logging configuration"""
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {level}')
    
    logging.getLogger().setLevel(numeric_level)

def print_banner() -> None:
    """Print the application banner"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                Raspberry Pi 5 AI Assistant                   ║
║                                                              ║
║  🤖 Multi-Modal AI Assistant with Chat & Object Detection   ║
║  📷 Real-time camera processing with YOLOv8                 ║
║  💬 Local LLM conversation via Ollama                       ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def print_menu() -> None:
    """Print the main menu"""
    menu = """
=== Raspberry Pi 5 AI Assistant ===
1. Chat Mode
2. Object Detection Mode
x. Exit

Select mode: """
    print(menu, end="")

def clear_screen() -> None:
    """Clear the terminal screen"""
    print("\033[2J\033[H", end="")

def print_status(message: str, status_type: str = "info") -> None:
    """Print a status message with color coding"""
    colors = {
        "info": "\033[94m",      # Blue
        "success": "\033[92m",   # Green
        "warning": "\033[93m",   # Yellow
        "error": "\033[91m",     # Red
        "reset": "\033[0m"       # Reset
    }
    
    color = colors.get(status_type, colors["info"])
    reset = colors["reset"]
    
    timestamp = time.strftime("%H:%M:%S")
    print(f"{color}[{timestamp}] {message}{reset}")

def handle_error(error: Exception, context: str = "") -> None:
    """Handle and log errors gracefully"""
    error_msg = f"Error in {context}: {str(error)}" if context else str(error)
    logger.error(error_msg)
    print_status(f"Error: {error_msg}", "error")

def check_system_resources() -> Dict[str, Any]:
    """Check system resources and return status"""
    try:
        import psutil
        
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available_gb": memory.available / (1024**3),
            "disk_percent": disk.percent,
            "disk_free_gb": disk.free / (1024**3)
        }
    except ImportError:
        logger.warning("psutil not available, skipping resource check")
        return {}

def format_object_summary(objects: list) -> str:
    """Format detected objects for LLM prompt"""
    if not objects:
        return "No objects detected"
    
    if len(objects) == 1:
        return f"a {objects[0]}"
    else:
        return f"objects: {', '.join(objects)}"

def create_llm_prompt(object_name: str) -> str:
    """Create a prompt for the LLM to analyze an object"""
    prompt = f"""Please provide a helpful analysis of this object: {object_name}

Please include:
1. A brief description of what it is
2. Common use cases
3. An interesting fun fact about it
4. Any relevant safety information

Keep the response concise but informative, suitable for a Raspberry Pi assistant."""

    return prompt

def save_detection_log(objects: list, timestamp: float) -> None:
    """Save detection results to a log file"""
    try:
        log_entry = {
            "timestamp": timestamp,
            "objects": objects,
            "datetime": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        with open("detection_log.json", "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        logger.error(f"Failed to save detection log: {e}")

def get_user_input(prompt: str = "> ") -> str:
    """Get user input with proper handling"""
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        return ""

def is_valid_model_name(model_name: str) -> bool:
    """Check if the model name is valid"""
    valid_models = [
        "gemma2:2b", "gemma2:7b", "gemma2:9b",
        "mistral:7b", "mistral:13b",
        "llama2:7b", "llama2:13b", "llama2:70b",
        "llama2:7b-q4_0", "llama2:13b-q4_0",
        "codellama:7b", "codellama:13b"
    ]
    return model_name in valid_models

def format_response_time(response_time: float) -> str:
    """Format response time for display"""
    if response_time < 1.0:
        return f"{response_time*1000:.0f}ms"
    else:
        return f"{response_time:.1f}s"

def print_help() -> None:
    """Print help information"""
    help_text = """
=== AI Assistant Help ===

Chat Mode:
- Type your message and press Enter
- Press 'q' to return to main menu
- Press 'x' to exit

Object Detection Mode:
- Camera will automatically detect objects
- AI will provide analysis of detected objects
- Press 'q' to return to main menu
- Press 'x' to exit

General:
- Use Ctrl+C to force quit
- Check logs in ai_assistant.log for errors
- Monitor system resources with htop
    """
    print(help_text)
