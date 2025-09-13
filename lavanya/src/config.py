"""
Configuration management for the speaker isolation system.
"""

import yaml
import os
from typing import Dict, Any, Optional
from pathlib import Path


class Config:
    """Configuration manager for the speaker isolation system."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize configuration from YAML file."""
        self.config_path = config_path
        self._config = self._load_config()
        self._ensure_directories()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            print(f"Config file {self.config_path} not found. Using default configuration.")
            return self._get_default_config()
        except yaml.YAMLError as e:
            print(f"Error parsing config file: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {
            "audio": {
                "sample_rate": 16000,
                "chunk_duration": 1.0,
                "buffer_size": 4096,
                "device_index": None
            },
            "models": {
                "separation": {
                    "model_name": "sepformer-wham",
                    "device": "cuda",
                    "batch_size": 1
                },
                "speaker_recognition": {
                    "model_name": "speechbrain/spkrec-ecapa-voxceleb",
                    "device": "cuda",
                    "embedding_dim": 192,
                    "similarity_threshold": 0.7
                },
                "transcription": {
                    "model_name": "whisper",
                    "model_size": "tiny",
                    "device": "cuda",
                    "language": "en"
                }
            },
            "processing": {
                "max_speakers": 4,
                "min_speaker_duration": 0.5,
                "overlap_threshold": 0.3,
                "confidence_threshold": 0.5
            },
            "storage": {
                "speaker_embeddings_dir": "./data/speaker_embeddings",
                "audio_cache_dir": "./data/audio_cache",
                "transcripts_dir": "./data/transcripts"
            },
            "server": {
                "host": "localhost",
                "port": 8000,
                "websocket_port": 8001
            },
            "ui": {
                "update_interval": 0.5,
                "max_transcript_length": 1000,
                "waveform_points": 200
            }
        }
    
    def _ensure_directories(self):
        """Ensure required directories exist."""
        directories = [
            self.get("storage.speaker_embeddings_dir"),
            self.get("storage.audio_cache_dir"),
            self.get("storage.transcripts_dir")
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value using dot notation (e.g., 'audio.sample_rate')."""
        keys = key_path.split('.')
        value = self._config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any):
        """Set configuration value using dot notation."""
        keys = key_path.split('.')
        config = self._config
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        config[keys[-1]] = value
    
    def save(self):
        """Save current configuration to file."""
        with open(self.config_path, 'w') as file:
            yaml.dump(self._config, file, default_flow_style=False, indent=2)
    
    def get_device(self, model_type: str) -> str:
        """Get device for specific model type, with fallback to CPU."""
        device = self.get(f"models.{model_type}.device", "cpu")
        
        # Check if CUDA is available
        if device == "cuda":
            try:
                import torch
                if not torch.cuda.is_available():
                    print(f"CUDA not available, falling back to CPU for {model_type}")
                    return "cpu"
            except ImportError:
                print(f"PyTorch not available, using CPU for {model_type}")
                return "cpu"
        
        return device
    
    def get_model_config(self, model_type: str) -> Dict[str, Any]:
        """Get configuration for specific model type."""
        return self.get(f"models.{model_type}", {})
    
    def get_audio_config(self) -> Dict[str, Any]:
        """Get audio configuration."""
        return self.get("audio", {})
    
    def get_processing_config(self) -> Dict[str, Any]:
        """Get processing configuration."""
        return self.get("processing", {})
    
    def get_server_config(self) -> Dict[str, Any]:
        """Get server configuration."""
        return self.get("server", {})
    
    def get_ui_config(self) -> Dict[str, Any]:
        """Get UI configuration."""
        return self.get("ui", {})


# Global configuration instance
config = Config()
