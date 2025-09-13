"""
Real-time audio streaming and buffering for speaker isolation system.
"""

import asyncio
import pyaudio
import numpy as np
import time
from typing import AsyncGenerator, Optional, Callable, Any
from dataclasses import dataclass
from queue import Queue, Empty
import threading
import logging

from .config import config


logger = logging.getLogger(__name__)


@dataclass
class AudioChunk:
    """Represents a chunk of audio data."""
    data: np.ndarray
    timestamp: float
    sample_rate: int
    channels: int
    
    @property
    def duration(self) -> float:
        """Get duration of audio chunk in seconds."""
        return len(self.data) / self.sample_rate


class AudioStreamer:
    """Real-time audio streamer with buffering and chunking capabilities."""
    
    def __init__(self, 
                 sample_rate: int = None,
                 chunk_duration: float = None,
                 device_index: Optional[int] = None,
                 channels: int = 1,
                 format=pyaudio.paFloat32):
        """Initialize audio streamer.
        
        Args:
            sample_rate: Audio sample rate (Hz)
            chunk_duration: Duration of each audio chunk (seconds)
            device_index: Microphone device index (None for default)
            channels: Number of audio channels
            format: PyAudio format
        """
        self.sample_rate = sample_rate or config.get("audio.sample_rate", 16000)
        self.chunk_duration = chunk_duration or config.get("audio.chunk_duration", 1.0)
        self.device_index = device_index or config.get("audio.device_index")
        self.channels = channels
        self.format = format
        
        # Calculate chunk size in frames
        self.chunk_size = int(self.sample_rate * self.chunk_duration)
        
        # PyAudio instance
        self.audio = pyaudio.PyAudio()
        
        # Streaming state
        self.is_streaming = False
        self.stream = None
        
        # Audio buffer for chunking
        self.audio_buffer = Queue()
        self.buffer_lock = threading.Lock()
        
        # Callbacks
        self.chunk_callbacks = []
        
        # Background thread for audio processing
        self.audio_thread = None
        self.stop_event = threading.Event()
    
    def add_chunk_callback(self, callback: Callable[[AudioChunk], None]):
        """Add callback function to be called for each audio chunk."""
        self.chunk_callbacks.append(callback)
    
    def remove_chunk_callback(self, callback: Callable[[AudioChunk], None]):
        """Remove callback function."""
        if callback in self.chunk_callbacks:
            self.chunk_callbacks.remove(callback)
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """PyAudio callback function for real-time audio capture."""
        if status:
            logger.warning(f"Audio callback status: {status}")
        
        # Convert bytes to numpy array
        audio_data = np.frombuffer(in_data, dtype=np.float32)
        
        # Add to buffer
        with self.buffer_lock:
            self.audio_buffer.put(audio_data)
        
        return (None, pyaudio.paContinue)
    
    def _process_audio_buffer(self):
        """Process audio buffer in background thread."""
        buffer = np.array([], dtype=np.float32)
        
        while not self.stop_event.is_set():
            try:
                # Get new audio data from buffer
                with self.buffer_lock:
                    audio_data = self.audio_buffer.get(timeout=0.1)
                
                # Append to buffer
                buffer = np.concatenate([buffer, audio_data])
                
                # Check if we have enough data for a chunk
                while len(buffer) >= self.chunk_size:
                    # Extract chunk
                    chunk_data = buffer[:self.chunk_size]
                    buffer = buffer[self.chunk_size:]
                    
                    # Create AudioChunk
                    chunk = AudioChunk(
                        data=chunk_data,
                        timestamp=time.time(),
                        sample_rate=self.sample_rate,
                        channels=self.channels
                    )
                    
                    # Call all registered callbacks
                    for callback in self.chunk_callbacks:
                        try:
                            callback(chunk)
                        except Exception as e:
                            logger.error(f"Error in audio chunk callback: {e}")
                
            except Empty:
                continue
            except Exception as e:
                logger.error(f"Error processing audio buffer: {e}")
                break
    
    def start_streaming(self) -> bool:
        """Start audio streaming.
        
        Returns:
            True if streaming started successfully, False otherwise
        """
        if self.is_streaming:
            logger.warning("Audio streaming already started")
            return False
        
        try:
            # Open audio stream
            self.stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=1024,  # Small buffer for low latency
                stream_callback=self._audio_callback
            )
            
            # Start streaming
            self.stream.start_stream()
            self.is_streaming = True
            
            # Start background processing thread
            self.stop_event.clear()
            self.audio_thread = threading.Thread(target=self._process_audio_buffer)
            self.audio_thread.daemon = True
            self.audio_thread.start()
            
            logger.info(f"Audio streaming started: {self.sample_rate}Hz, {self.chunk_duration}s chunks")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start audio streaming: {e}")
            self.is_streaming = False
            return False
    
    def stop_streaming(self):
        """Stop audio streaming."""
        if not self.is_streaming:
            return
        
        # Signal stop to background thread
        self.stop_event.set()
        
        # Stop PyAudio stream
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        
        # Wait for background thread to finish
        if self.audio_thread and self.audio_thread.is_alive():
            self.audio_thread.join(timeout=2.0)
        
        self.is_streaming = False
        logger.info("Audio streaming stopped")
    
    def get_available_devices(self) -> list:
        """Get list of available audio input devices."""
        devices = []
        for i in range(self.audio.get_device_count()):
            info = self.audio.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                devices.append({
                    'index': i,
                    'name': info['name'],
                    'channels': info['maxInputChannels'],
                    'sample_rate': info['defaultSampleRate']
                })
        return devices
    
    def __enter__(self):
        """Context manager entry."""
        self.start_streaming()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop_streaming()
    
    def __del__(self):
        """Cleanup on deletion."""
        self.stop_streaming()
        if hasattr(self, 'audio'):
            self.audio.terminate()


class AudioFileStreamer:
    """Audio streamer for pre-recorded files (useful for testing)."""
    
    def __init__(self, file_path: str, 
                 sample_rate: int = None,
                 chunk_duration: float = None):
        """Initialize file-based audio streamer.
        
        Args:
            file_path: Path to audio file
            sample_rate: Target sample rate for resampling
            chunk_duration: Duration of each chunk (seconds)
        """
        self.file_path = file_path
        self.sample_rate = sample_rate or config.get("audio.sample_rate", 16000)
        self.chunk_duration = chunk_duration or config.get("audio.chunk_duration", 1.0)
        
        # Load audio file
        try:
            import librosa
            self.audio_data, self.original_sr = librosa.load(
                file_path, 
                sr=self.sample_rate,
                mono=True
            )
        except ImportError:
            logger.error("librosa not available. Please install it for file streaming.")
            raise
        except Exception as e:
            logger.error(f"Failed to load audio file {file_path}: {e}")
            raise
        
        # Calculate chunk size
        self.chunk_size = int(self.sample_rate * self.chunk_duration)
        self.current_position = 0
        
        # Callbacks
        self.chunk_callbacks = []
        
        # Streaming state
        self.is_streaming = False
        self.stop_event = asyncio.Event()
    
    def add_chunk_callback(self, callback: Callable[[AudioChunk], None]):
        """Add callback function to be called for each audio chunk."""
        self.chunk_callbacks.append(callback)
    
    async def start_streaming(self, playback_speed: float = 1.0):
        """Start streaming audio file.
        
        Args:
            playback_speed: Speed multiplier for playback (1.0 = real-time)
        """
        if self.is_streaming:
            return
        
        self.is_streaming = True
        self.stop_event.clear()
        
        chunk_interval = self.chunk_duration / playback_speed
        
        while self.current_position < len(self.audio_data) and not self.stop_event.is_set():
            # Extract chunk
            end_position = min(self.current_position + self.chunk_size, len(self.audio_data))
            chunk_data = self.audio_data[self.current_position:end_position]
            
            # Create AudioChunk
            chunk = AudioChunk(
                data=chunk_data,
                timestamp=time.time(),
                sample_rate=self.sample_rate,
                channels=1
            )
            
            # Call callbacks
            for callback in self.chunk_callbacks:
                try:
                    callback(chunk)
                except Exception as e:
                    logger.error(f"Error in audio chunk callback: {e}")
            
            self.current_position = end_position
            
            # Wait for next chunk
            await asyncio.sleep(chunk_interval)
        
        self.is_streaming = False
    
    def stop_streaming(self):
        """Stop audio streaming."""
        self.stop_event.set()
        self.is_streaming = False
    
    def reset(self):
        """Reset to beginning of file."""
        self.current_position = 0


async def create_audio_streamer(use_microphone: bool = True, 
                              file_path: Optional[str] = None,
                              **kwargs) -> AudioStreamer:
    """Create appropriate audio streamer based on input type.
    
    Args:
        use_microphone: If True, use microphone; if False, use file
        file_path: Path to audio file (required if use_microphone=False)
        **kwargs: Additional arguments for streamer initialization
    
    Returns:
        AudioStreamer instance
    """
    if use_microphone:
        return AudioStreamer(**kwargs)
    else:
        if not file_path:
            raise ValueError("file_path required when use_microphone=False")
        return AudioFileStreamer(file_path, **kwargs)
