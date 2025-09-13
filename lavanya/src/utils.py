"""
Utility functions for the speaker isolation system.
"""

import numpy as np
import torch
import torchaudio
from typing import Tuple, List, Optional, Dict, Any
import logging
import time
from pathlib import Path
import json
import pickle
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class AudioMetrics:
    """Audio quality and processing metrics."""
    rms_energy: float
    zero_crossing_rate: float
    spectral_centroid: float
    spectral_rolloff: float
    mfcc_features: List[float]
    duration: float
    sample_rate: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


class AudioProcessor:
    """Utility class for audio processing operations."""
    
    @staticmethod
    def normalize_audio(audio: np.ndarray, target_level: float = 0.95) -> np.ndarray:
        """Normalize audio to target level.
        
        Args:
            audio: Input audio array
            target_level: Target peak level (0.0 to 1.0)
            
        Returns:
            Normalized audio array
        """
        if len(audio) == 0:
            return audio
        
        max_val = np.max(np.abs(audio))
        if max_val > 0:
            return audio * (target_level / max_val)
        return audio
    
    @staticmethod
    def apply_preemphasis(audio: np.ndarray, coeff: float = 0.97) -> np.ndarray:
        """Apply preemphasis filter to audio.
        
        Args:
            audio: Input audio array
            coeff: Preemphasis coefficient
            
        Returns:
            Preemphasized audio array
        """
        if len(audio) <= 1:
            return audio
        
        emphasized = np.zeros_like(audio)
        emphasized[0] = audio[0]
        emphasized[1:] = audio[1:] - coeff * audio[:-1]
        
        return emphasized
    
    @staticmethod
    def compute_audio_metrics(audio: np.ndarray, sample_rate: int) -> AudioMetrics:
        """Compute various audio quality metrics.
        
        Args:
            audio: Input audio array
            sample_rate: Audio sample rate
            
        Returns:
            AudioMetrics object with computed metrics
        """
        try:
            # Basic metrics
            rms_energy = float(np.sqrt(np.mean(audio ** 2)))
            zero_crossing_rate = float(np.mean(np.abs(np.diff(np.sign(audio))))) / 2
            
            # Spectral features
            fft = np.fft.fft(audio)
            magnitude_spectrum = np.abs(fft[:len(fft) // 2])
            freqs = np.fft.fftfreq(len(audio), 1/sample_rate)[:len(audio) // 2]
            
            # Spectral centroid
            spectral_centroid = float(np.sum(freqs * magnitude_spectrum) / np.sum(magnitude_spectrum))
            
            # Spectral rolloff (95% of energy)
            cumulative_energy = np.cumsum(magnitude_spectrum)
            rolloff_threshold = 0.95 * cumulative_energy[-1]
            rolloff_idx = np.where(cumulative_energy >= rolloff_threshold)[0]
            spectral_rolloff = float(freqs[rolloff_idx[0]]) if len(rolloff_idx) > 0 else 0.0
            
            # MFCC features (simplified)
            mfcc_features = AudioProcessor._compute_mfcc(audio, sample_rate)
            
            return AudioMetrics(
                rms_energy=rms_energy,
                zero_crossing_rate=zero_crossing_rate,
                spectral_centroid=spectral_centroid,
                spectral_rolloff=spectral_rolloff,
                mfcc_features=mfcc_features,
                duration=len(audio) / sample_rate,
                sample_rate=sample_rate
            )
            
        except Exception as e:
            logger.error(f"Error computing audio metrics: {e}")
            return AudioMetrics(
                rms_energy=0.0,
                zero_crossing_rate=0.0,
                spectral_centroid=0.0,
                spectral_rolloff=0.0,
                mfcc_features=[],
                duration=0.0,
                sample_rate=sample_rate
            )
    
    @staticmethod
    def _compute_mfcc(audio: np.ndarray, sample_rate: int, n_mfcc: int = 13) -> List[float]:
        """Compute simplified MFCC features.
        
        Args:
            audio: Input audio array
            sample_rate: Audio sample rate
            n_mfcc: Number of MFCC coefficients
            
        Returns:
            List of MFCC coefficients
        """
        try:
            # Simple windowed FFT approach for MFCC
            window_size = int(0.025 * sample_rate)  # 25ms window
            hop_size = int(0.010 * sample_rate)     # 10ms hop
            
            mfcc_features = []
            
            for i in range(0, len(audio) - window_size, hop_size):
                window = audio[i:i + window_size]
                window = window * np.hanning(len(window))  # Apply window
                
                # FFT
                fft = np.fft.fft(window)
                magnitude = np.abs(fft[:len(fft) // 2])
                
                # Mel-scale filter bank (simplified)
                mel_filters = AudioProcessor._create_mel_filters(
                    len(magnitude), sample_rate, n_mfcc
                )
                
                # Apply mel filters
                mel_energies = np.dot(mel_filters, magnitude)
                mel_energies = np.log(mel_energies + 1e-10)  # Log
                
                # DCT to get MFCC
                mfcc = np.fft.fft(mel_energies).real[:n_mfcc]
                mfcc_features.extend(mfcc.tolist())
            
            # Return average MFCC features
            if len(mfcc_features) > 0:
                mfcc_array = np.array(mfcc_features).reshape(-1, n_mfcc)
                return np.mean(mfcc_array, axis=0).tolist()
            else:
                return [0.0] * n_mfcc
                
        except Exception as e:
            logger.error(f"Error computing MFCC: {e}")
            return [0.0] * n_mfcc
    
    @staticmethod
    def _create_mel_filters(n_fft: int, sample_rate: int, n_mel: int) -> np.ndarray:
        """Create mel-scale filter bank.
        
        Args:
            n_fft: FFT size
            sample_rate: Audio sample rate
            n_mel: Number of mel filters
            
        Returns:
            Filter bank matrix
        """
        # Mel scale conversion
        mel_low = 0
        mel_high = 2595 * np.log10(1 + sample_rate / 2 / 700)
        mel_points = np.linspace(mel_low, mel_high, n_mel + 2)
        
        # Convert back to Hz
        hz_points = 700 * (10 ** (mel_points / 2595) - 1)
        
        # Convert to bin indices
        bin_indices = np.floor((n_fft + 1) * hz_points / sample_rate).astype(int)
        
        # Create filters
        filters = np.zeros((n_mel, n_fft // 2))
        
        for i in range(n_mel):
            left = bin_indices[i]
            center = bin_indices[i + 1]
            right = bin_indices[i + 2]
            
            # Rising edge
            filters[i, left:center] = np.linspace(0, 1, center - left)
            # Falling edge
            filters[i, center:right] = np.linspace(1, 0, right - center)
        
        return filters


class ModelManager:
    """Utility class for managing model downloads and caching."""
    
    def __init__(self, cache_dir: str = "./models"):
        """Initialize model manager.
        
        Args:
            cache_dir: Directory to cache downloaded models
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.model_registry = {
            "sepformer-wham": {
                "source": "speechbrain/sepformer-wham",
                "type": "separation",
                "size": "~100MB"
            },
            "sepformer-libri2mix": {
                "source": "speechbrain/sepformer-libri2mix",
                "type": "separation",
                "size": "~100MB"
            },
            "ecapa-voxceleb": {
                "source": "speechbrain/spkrec-ecapa-voxceleb",
                "type": "speaker_recognition",
                "size": "~50MB"
            },
            "whisper-tiny": {
                "source": "whisper",
                "type": "transcription",
                "size": "~39MB"
            },
            "whisper-base": {
                "source": "whisper",
                "type": "transcription",
                "size": "~74MB"
            },
            "whisper-small": {
                "source": "whisper",
                "type": "transcription",
                "size": "~244MB"
            },
            "whisper-medium": {
                "source": "whisper",
                "type": "transcription",
                "size": "~769MB"
            },
            "whisper-large": {
                "source": "whisper",
                "type": "transcription",
                "size": "~1550MB"
            }
        }
    
    def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Model information dictionary or None if not found
        """
        return self.model_registry.get(model_name)
    
    def list_available_models(self, model_type: str = None) -> Dict[str, Dict[str, Any]]:
        """List available models, optionally filtered by type.
        
        Args:
            model_type: Filter by model type ('separation', 'speaker_recognition', 'transcription')
            
        Returns:
            Dictionary of available models
        """
        if model_type:
            return {
                name: info for name, info in self.model_registry.items()
                if info["type"] == model_type
            }
        return self.model_registry.copy()
    
    def get_model_cache_path(self, model_name: str) -> Path:
        """Get cache path for a model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Path object for model cache directory
        """
        return self.cache_dir / model_name
    
    def is_model_cached(self, model_name: str) -> bool:
        """Check if model is cached locally.
        
        Args:
            model_name: Name of the model
            
        Returns:
            True if model is cached, False otherwise
        """
        cache_path = self.get_model_cache_path(model_name)
        return cache_path.exists() and any(cache_path.iterdir())
    
    def get_model_stats(self) -> Dict[str, Any]:
        """Get statistics about cached models.
        
        Returns:
            Dictionary with model cache statistics
        """
        stats = {
            "total_models": len(self.model_registry),
            "cached_models": 0,
            "cache_size_bytes": 0,
            "models_by_type": {}
        }
        
        # Count by type
        for model_name, info in self.model_registry.items():
            model_type = info["type"]
            if model_type not in stats["models_by_type"]:
                stats["models_by_type"][model_type] = {"total": 0, "cached": 0}
            
            stats["models_by_type"][model_type]["total"] += 1
            
            if self.is_model_cached(model_name):
                stats["models_by_type"][model_type]["cached"] += 1
                stats["cached_models"] += 1
                
                # Calculate cache size
                cache_path = self.get_model_cache_path(model_name)
                for file_path in cache_path.rglob("*"):
                    if file_path.is_file():
                        stats["cache_size_bytes"] += file_path.stat().st_size
        
        return stats


class PerformanceMonitor:
    """Utility class for monitoring system performance."""
    
    def __init__(self):
        """Initialize performance monitor."""
        self.metrics = {
            "audio_processing_time": [],
            "separation_time": [],
            "speaker_id_time": [],
            "transcription_time": [],
            "total_pipeline_time": [],
            "memory_usage": [],
            "cpu_usage": []
        }
        
        self.start_times = {}
    
    def start_timer(self, operation: str):
        """Start timing an operation.
        
        Args:
            operation: Name of the operation being timed
        """
        self.start_times[operation] = time.time()
    
    def end_timer(self, operation: str):
        """End timing an operation and record the duration.
        
        Args:
            operation: Name of the operation
        """
        if operation in self.start_times:
            duration = time.time() - self.start_times[operation]
            
            if operation in self.metrics:
                self.metrics[operation].append(duration)
                
                # Keep only last 100 measurements
                if len(self.metrics[operation]) > 100:
                    self.metrics[operation] = self.metrics[operation][-100:]
            
            del self.start_times[operation]
            return duration
        
        return 0.0
    
    def get_average_time(self, operation: str) -> float:
        """Get average time for an operation.
        
        Args:
            operation: Name of the operation
            
        Returns:
            Average time in seconds
        """
        if operation in self.metrics and self.metrics[operation]:
            return sum(self.metrics[operation]) / len(self.metrics[operation])
        return 0.0
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary.
        
        Returns:
            Dictionary with performance metrics
        """
        summary = {}
        
        for operation, times in self.metrics.items():
            if times:
                summary[operation] = {
                    "average": sum(times) / len(times),
                    "min": min(times),
                    "max": max(times),
                    "count": len(times),
                    "latest": times[-1] if times else 0.0
                }
            else:
                summary[operation] = {
                    "average": 0.0,
                    "min": 0.0,
                    "max": 0.0,
                    "count": 0,
                    "latest": 0.0
                }
        
        return summary
    
    def reset_metrics(self):
        """Reset all performance metrics."""
        for operation in self.metrics:
            self.metrics[operation] = []
        self.start_times.clear()


class DataExporter:
    """Utility class for exporting system data."""
    
    @staticmethod
    def export_speaker_data(speakers: List[Any], output_path: str):
        """Export speaker data to JSON file.
        
        Args:
            speakers: List of speaker objects
            output_path: Output file path
        """
        try:
            data = []
            for speaker in speakers:
                if hasattr(speaker, 'to_dict'):
                    data.append(speaker.to_dict())
                elif hasattr(speaker, '__dict__'):
                    data.append(speaker.__dict__)
                else:
                    data.append(str(speaker))
            
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            logger.info(f"Speaker data exported to {output_path}")
            
        except Exception as e:
            logger.error(f"Error exporting speaker data: {e}")
    
    @staticmethod
    def export_transcripts(transcripts: Dict[str, List[Any]], output_path: str):
        """Export transcripts to JSON file.
        
        Args:
            transcripts: Dictionary of speaker transcripts
            output_path: Output file path
        """
        try:
            with open(output_path, 'w') as f:
                json.dump(transcripts, f, indent=2, default=str)
            
            logger.info(f"Transcripts exported to {output_path}")
            
        except Exception as e:
            logger.error(f"Error exporting transcripts: {e}")
    
    @staticmethod
    def export_performance_data(performance_data: Dict[str, Any], output_path: str):
        """Export performance data to JSON file.
        
        Args:
            performance_data: Performance metrics dictionary
            output_path: Output file path
        """
        try:
            with open(output_path, 'w') as f:
                json.dump(performance_data, f, indent=2, default=str)
            
            logger.info(f"Performance data exported to {output_path}")
            
        except Exception as e:
            logger.error(f"Error exporting performance data: {e}")


# Global instances
model_manager = ModelManager()
performance_monitor = PerformanceMonitor()
data_exporter = DataExporter()
