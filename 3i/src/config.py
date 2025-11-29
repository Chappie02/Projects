"""
Configuration utilities for the Multi-Modal AI Assistant.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class HardwareConfig:
    """Pin assignments and hardware-specific paths."""

    chat_button_pin: int = 17  # K1
    object_button_pin: int = 27  # K2
    action_button_pin: int = 22  # K3
    oled_reset_pin: int | None = None


@dataclass
class AudioConfig:
    """Audio capture and playback configuration."""

    sample_rate: int = 16000
    channels: int = 1
    whisper_model: str = "small"
    vosk_model_path: Path | None = None
    tts_voice_path: Path | None = Path("/home/pi/piper/voices/en_US-amy-low.onnx")
    tts_binary: str = "piper"
    mic_device: int | None = None
    speaker_device: int | None = None


@dataclass
class VisionConfig:
    """Camera and detection configuration."""

    yolo_model_path: Path = Path("/home/pi/models/yolov8.pt")
    capture_resolution: tuple[int, int] = (1280, 720)
    capture_format: str = "rgb888"
    object_save_dir: Path = Path("/home/pi/Object_Captures")


@dataclass
class LLMConfig:
    """Configuration for llama.cpp and RAG."""

    model_path: Path = Path("/home/pi/models/llama.cpp/gguf-model.bin")
    temperature: float = 0.3
    top_p: float = 0.9
    max_tokens: int = 512
    chroma_path: Path = Path("/home/suhas/Desktop/3i/src/memory")
    collection_name: str = "assistant_memory"


@dataclass
class AssistantConfig:
    """Bundled configuration for the assistant."""

    hardware: HardwareConfig = field(default_factory=HardwareConfig)
    audio: AudioConfig = field(default_factory=AudioConfig)
    vision: VisionConfig = field(default_factory=VisionConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)

    @classmethod
    def load(cls) -> "AssistantConfig":
        """
        Load configuration from environment or defaults.

        The method can be extended to parse TOML/JSON or env vars.
        """
        # For now we return defaults; placeholder for future expansion.
        return cls()

