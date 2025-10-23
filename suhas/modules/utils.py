"""
Utility functions and classes for the Raspberry Pi AI Assistant.
Provides common functionality used across different modules.
"""

import os
import sys
import logging
import psutil
import time
from typing import Optional, Dict, Any, List
from pathlib import Path
import json


class SystemMonitor:
    """Monitor system resources for Raspberry Pi optimization."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def get_cpu_usage(self) -> float:
        """Get current CPU usage percentage."""
        return psutil.cpu_percent(interval=1)
    
    def get_memory_usage(self) -> Dict[str, float]:
        """Get current memory usage statistics."""
        memory = psutil.virtual_memory()
        return {
            'total': memory.total / (1024**3),  # GB
            'available': memory.available / (1024**3),  # GB
            'percent': memory.percent,
            'used': memory.used / (1024**3)  # GB
        }
    
    def get_temperature(self) -> Optional[float]:
        """Get CPU temperature in Celsius (Raspberry Pi specific)."""
        try:
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                temp = int(f.read().strip()) / 1000.0
                return temp
        except (FileNotFoundError, PermissionError):
            self.logger.warning("Could not read CPU temperature")
            return None
    
    def get_disk_usage(self) -> Dict[str, float]:
        """Get disk usage statistics."""
        disk = psutil.disk_usage('/')
        return {
            'total': disk.total / (1024**3),  # GB
            'used': disk.used / (1024**3),    # GB
            'free': disk.free / (1024**3),    # GB
            'percent': (disk.used / disk.total) * 100
        }
    
    def check_system_health(self) -> Dict[str, Any]:
        """Comprehensive system health check."""
        return {
            'cpu_usage': self.get_cpu_usage(),
            'memory': self.get_memory_usage(),
            'temperature': self.get_temperature(),
            'timestamp': time.time()
        }


class ConfigManager:
    """Manage configuration settings for the AI assistant."""
    
    def __init__(self, config_path: str = "data/config.json"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.logger = logging.getLogger(__name__)
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        default_config = {
            "llama_cpp": {
                "model_path": "models/llama-2-7b-chat.gguf",
                "n_ctx": 2048,
                "n_threads": 4,
                "temperature": 0.7,
                "max_tokens": 512
            },
            "yolo": {
                "model_path": "yolo/yolov8n.pt",
                "confidence_threshold": 0.5,
                "iou_threshold": 0.45
            },
            "rag": {
                "embedding_model": "all-MiniLM-L6-v2",
                "chunk_size": 512,
                "chunk_overlap": 50,
                "top_k": 3
            },
            "camera": {
                "resolution": [640, 480],
                "fps": 30,
                "rotation": 0
            },
            "system": {
                "log_level": "INFO",
                "max_memory_usage": 80.0,  # Percentage
                "max_temperature": 70.0    # Celsius
            }
        }
        
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    return self._merge_configs(default_config, config)
            except (json.JSONDecodeError, IOError) as e:
                self.logger.error(f"Error loading config: {e}")
                return default_config
        else:
            # Create default config file
            self._save_config(default_config)
            return default_config
    
    def _merge_configs(self, default: Dict, user: Dict) -> Dict:
        """Recursively merge user config with defaults."""
        result = default.copy()
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        return result
    
    def _save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to JSON file."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
        except IOError as e:
            self.logger.error(f"Error saving config: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-separated key."""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value by dot-separated key."""
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        self._save_config(self.config)
    
    def update(self, updates: Dict[str, Any]) -> None:
        """Update multiple configuration values."""
        self.config = self._merge_configs(self.config, updates)
        self._save_config(self.config)


class Logger:
    """Centralized logging configuration."""
    
    @staticmethod
    def setup_logging(log_level: str = "INFO", log_file: str = "data/assistant.log") -> None:
        """Setup logging configuration."""
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Setup file handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        
        # Setup console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_level.upper()))
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)


class ProcessManager:
    """Manage subprocesses and clean shutdown."""
    
    def __init__(self):
        self.processes: Dict[str, Any] = {}
        self.logger = logging.getLogger(__name__)
    
    def register_process(self, name: str, process: Any) -> None:
        """Register a process for management."""
        self.processes[name] = process
        self.logger.info(f"Registered process: {name}")
    
    def terminate_process(self, name: str) -> bool:
        """Terminate a registered process."""
        if name in self.processes:
            try:
                process = self.processes[name]
                if hasattr(process, 'terminate'):
                    process.terminate()
                elif hasattr(process, 'close'):
                    process.close()
                del self.processes[name]
                self.logger.info(f"Terminated process: {name}")
                return True
            except Exception as e:
                self.logger.error(f"Error terminating process {name}: {e}")
                return False
        return False
    
    def terminate_all(self) -> None:
        """Terminate all registered processes."""
        for name in list(self.processes.keys()):
            self.terminate_process(name)
        self.logger.info("All processes terminated")


def ensure_directory(path: str) -> Path:
    """Ensure directory exists, create if it doesn't."""
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def format_timestamp(timestamp: Optional[float] = None) -> str:
    """Format timestamp for display."""
    if timestamp is None:
        timestamp = time.time()
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))


def validate_model_path(path: str) -> bool:
    """Validate that a model file exists and is accessible."""
    model_path = Path(path)
    if not model_path.exists():
        return False
    if not model_path.is_file():
        return False
    return True


def get_available_models(directory: str) -> List[str]:
    """Get list of available model files in directory."""
    model_dir = Path(directory)
    if not model_dir.exists():
        return []
    
    model_extensions = {'.gguf', '.pt', '.onnx', '.bin'}
    models = []
    
    for file_path in model_dir.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in model_extensions:
            models.append(str(file_path))
    
    return sorted(models)


def cleanup_old_files(directory: str, max_age_hours: int = 24) -> int:
    """Clean up old files in directory, return count of deleted files."""
    dir_path = Path(directory)
    if not dir_path.exists():
        return 0
    
    current_time = time.time()
    max_age_seconds = max_age_hours * 3600
    deleted_count = 0
    
    for file_path in dir_path.iterdir():
        if file_path.is_file():
            file_age = current_time - file_path.stat().st_mtime
            if file_age > max_age_seconds:
                try:
                    file_path.unlink()
                    deleted_count += 1
                except OSError as e:
                    logging.getLogger(__name__).warning(f"Could not delete {file_path}: {e}")
    
    return deleted_count
