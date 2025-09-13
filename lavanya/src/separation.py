"""
Speech separation module for real-time speaker isolation.
"""

import torch
import torchaudio
import numpy as np
from typing import List, Tuple, Optional, Dict, Any
import logging
from dataclasses import dataclass
import time

from speechbrain.pretrained import SepformerSeparation as PretrainedSepformer
from .config import config
from .audio_stream import AudioChunk

logger = logging.getLogger(__name__)


@dataclass
class SeparatedAudio:
    """Represents separated audio streams."""
    streams: List[np.ndarray]
    timestamp: float
    sample_rate: int
    confidence_scores: List[float]
    
    @property
    def num_speakers(self) -> int:
        """Number of separated speakers."""
        return len(self.streams)


class SpeechSeparator:
    """Real-time speech separation using pretrained models."""
    
    def __init__(self, 
                 model_name: str = None,
                 device: str = None,
                 max_speakers: int = None):
        """Initialize speech separator.
        
        Args:
            model_name: Name of separation model to use
            device: Device to run model on ('cuda' or 'cpu')
            max_speakers: Maximum number of speakers to separate
        """
        self.model_name = model_name or config.get("models.separation.model_name", "sepformer-wham")
        self.device = device or config.get_device("separation")
        self.max_speakers = max_speakers or config.get("processing.max_speakers", 4)
        
        # Model and preprocessing
        self.model = None
        self.sample_rate = config.get("audio.sample_rate", 16000)
        
        # Audio buffer for real-time processing
        self.audio_buffer = []
        self.buffer_duration = 3.0  # seconds of audio to buffer
        self.buffer_size = int(self.sample_rate * self.buffer_duration)
        
        # Processing state
        self.is_initialized = False
        
        logger.info(f"Initializing speech separator: {self.model_name} on {self.device}")
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the separation model."""
        try:
            if self.model_name == "sepformer-wham":
                # Use SpeechBrain's Sepformer model
                self.model = PretrainedSepformer.from_hparams(
                    source="speechbrain/sepformer-wham",
                    savedir="pretrained_models/sepformer-wham",
                    run_opts={"device": self.device}
                )
                self.model.eval()
                
            elif self.model_name == "sepformer-libri2mix":
                # Alternative Sepformer model
                self.model = PretrainedSepformer.from_hparams(
                    source="speechbrain/sepformer-libri2mix",
                    savedir="pretrained_models/sepformer-libri2mix",
                    run_opts={"device": self.device}
                )
                self.model.eval()
                
            else:
                raise ValueError(f"Unknown separation model: {self.model_name}")
            
            self.is_initialized = True
            logger.info(f"Successfully initialized separation model: {self.model_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize separation model: {e}")
            self.is_initialized = False
            raise
    
    def _preprocess_audio(self, audio_chunk: AudioChunk) -> torch.Tensor:
        """Preprocess audio chunk for separation model.
        
        Args:
            audio_chunk: Input audio chunk
            
        Returns:
            Preprocessed audio tensor
        """
        # Convert to tensor
        audio_tensor = torch.from_numpy(audio_chunk.data).float()
        
        # Add channel dimension if needed
        if audio_tensor.dim() == 1:
            audio_tensor = audio_tensor.unsqueeze(0)
        
        # Resample if necessary
        if audio_chunk.sample_rate != self.sample_rate:
            resampler = torchaudio.transforms.Resample(
                audio_chunk.sample_rate, 
                self.sample_rate
            )
            audio_tensor = resampler(audio_tensor)
        
        # Move to device
        audio_tensor = audio_tensor.to(self.device)
        
        return audio_tensor
    
    def _postprocess_separation(self, separated_tensors: torch.Tensor, 
                              original_chunk: AudioChunk) -> SeparatedAudio:
        """Postprocess separated audio tensors.
        
        Args:
            separated_tensors: Separated audio tensors from model
            original_chunk: Original audio chunk for metadata
            
        Returns:
            SeparatedAudio object
        """
        # Convert to numpy arrays
        separated_streams = []
        confidence_scores = []
        
        for i in range(min(separated_tensors.shape[0], self.max_speakers)):
            # Extract speaker stream
            stream = separated_tensors[i].squeeze().cpu().numpy()
            separated_streams.append(stream)
            
            # Calculate confidence score (RMS energy)
            confidence = float(np.sqrt(np.mean(stream ** 2)))
            confidence_scores.append(confidence)
        
        return SeparatedAudio(
            streams=separated_streams,
            timestamp=original_chunk.timestamp,
            sample_rate=self.sample_rate,
            confidence_scores=confidence_scores
        )
    
    def separate_audio(self, audio_chunk: AudioChunk) -> SeparatedAudio:
        """Separate speakers in audio chunk.
        
        Args:
            audio_chunk: Input audio chunk
            
        Returns:
            SeparatedAudio with isolated speaker streams
        """
        if not self.is_initialized:
            raise RuntimeError("Separation model not initialized")
        
        try:
            # Preprocess audio
            audio_tensor = self._preprocess_audio(audio_chunk)
            
            # Add to buffer for context
            self.audio_buffer.append(audio_tensor)
            
            # Keep only recent audio for real-time processing
            if len(self.audio_buffer) * audio_tensor.shape[-1] > self.buffer_size:
                self.audio_buffer = self.audio_buffer[-1:]
            
            # Concatenate buffer for better separation
            if len(self.audio_buffer) > 1:
                buffered_audio = torch.cat(self.audio_buffer, dim=-1)
            else:
                buffered_audio = audio_tensor
            
            # Perform separation
            with torch.no_grad():
                separated_tensors = self.model.separate_batch(buffered_audio)
            
            # Extract only the last chunk's worth of separated audio
            chunk_samples = audio_tensor.shape[-1]
            separated_tensors = separated_tensors[:, :, -chunk_samples:]
            
            # Postprocess results
            separated_audio = self._postprocess_separation(separated_tensors, audio_chunk)
            
            return separated_audio
            
        except Exception as e:
            logger.error(f"Error in speech separation: {e}")
            # Return empty separation on error
            return SeparatedAudio(
                streams=[audio_chunk.data],
                timestamp=audio_chunk.timestamp,
                sample_rate=self.sample_rate,
                confidence_scores=[0.0]
            )
    
    def separate_batch(self, audio_chunks: List[AudioChunk]) -> List[SeparatedAudio]:
        """Separate speakers in batch of audio chunks.
        
        Args:
            audio_chunks: List of input audio chunks
            
        Returns:
            List of SeparatedAudio objects
        """
        results = []
        for chunk in audio_chunks:
            result = self.separate_audio(chunk)
            results.append(result)
        return results
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model."""
        return {
            "model_name": self.model_name,
            "device": self.device,
            "max_speakers": self.max_speakers,
            "sample_rate": self.sample_rate,
            "is_initialized": self.is_initialized,
            "buffer_duration": self.buffer_duration
        }
    
    def reset_buffer(self):
        """Reset audio buffer (useful for new conversations)."""
        self.audio_buffer = []
        logger.info("Audio buffer reset")


class RealTimeSpeechSeparator:
    """Real-time speech separator with streaming capabilities."""
    
    def __init__(self, separator: SpeechSeparator = None, **kwargs):
        """Initialize real-time separator.
        
        Args:
            separator: Existing SpeechSeparator instance
            **kwargs: Arguments for SpeechSeparator if not provided
        """
        self.separator = separator or SpeechSeparator(**kwargs)
        self.callbacks = []
        
        # Processing queue
        self.processing_queue = []
        self.max_queue_size = 5  # Prevent memory buildup
        
    def add_separation_callback(self, callback):
        """Add callback for separated audio results."""
        self.callbacks.append(callback)
    
    def process_audio_chunk(self, audio_chunk: AudioChunk):
        """Process audio chunk and call callbacks with separated audio.
        
        Args:
            audio_chunk: Input audio chunk
        """
        try:
            # Perform separation
            separated_audio = self.separator.separate_audio(audio_chunk)
            
            # Call all registered callbacks
            for callback in self.callbacks:
                try:
                    callback(separated_audio)
                except Exception as e:
                    logger.error(f"Error in separation callback: {e}")
                    
        except Exception as e:
            logger.error(f"Error processing audio chunk: {e}")
    
    def process_audio_stream(self, audio_stream):
        """Process continuous audio stream.
        
        Args:
            audio_stream: AudioStreamer instance
        """
        # Add this processor as a callback to the audio stream
        audio_stream.add_chunk_callback(self.process_audio_chunk)
        logger.info("Real-time separation processing started")


def create_separator(model_name: str = None, 
                    device: str = None,
                    max_speakers: int = None) -> SpeechSeparator:
    """Create speech separator with configuration.
    
    Args:
        model_name: Separation model name
        device: Device to use ('cuda' or 'cpu')
        max_speakers: Maximum number of speakers
        
    Returns:
        SpeechSeparator instance
    """
    return SpeechSeparator(
        model_name=model_name,
        device=device,
        max_speakers=max_speakers
    )


def create_realtime_separator(**kwargs) -> RealTimeSpeechSeparator:
    """Create real-time speech separator.
    
    Args:
        **kwargs: Arguments for SpeechSeparator
        
    Returns:
        RealTimeSpeechSeparator instance
    """
    return RealTimeSpeechSeparator(**kwargs)
