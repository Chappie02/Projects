"""
Speech transcription module using Whisper for real-time processing.
"""

import torch
import numpy as np
import whisper
from typing import List, Dict, Optional, Any, Callable
import logging
from dataclasses import dataclass
import time
import threading
from queue import Queue, Empty
import asyncio

from .config import config
from .separation import SeparatedAudio
from .speaker_id import SpeakerMatch

logger = logging.getLogger(__name__)


@dataclass
class TranscriptionResult:
    """Represents a transcription result."""
    text: str
    confidence: float
    timestamp: float
    speaker_id: str
    speaker_name: str
    language: str
    is_final: bool = False


class WhisperTranscriber:
    """Whisper-based speech transcriber."""
    
    def __init__(self, 
                 model_size: str = None,
                 device: str = None,
                 language: str = None):
        """Initialize Whisper transcriber.
        
        Args:
            model_size: Whisper model size ('tiny', 'base', 'small', 'medium', 'large')
            device: Device to run model on ('cuda' or 'cpu')
            language: Target language code (e.g., 'en', 'es', 'fr')
        """
        self.model_size = model_size or config.get("models.transcription.model_size", "tiny")
        self.device = device or config.get_device("transcription")
        self.language = language or config.get("models.transcription.language", "en")
        
        # Model
        self.model = None
        self.sample_rate = 16000  # Whisper's expected sample rate
        
        logger.info(f"Initializing Whisper transcriber: {self.model_size} on {self.device}")
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize Whisper model."""
        try:
            # Load model
            self.model = whisper.load_model(self.model_size, device=self.device)
            
            logger.info(f"Successfully loaded Whisper model: {self.model_size}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Whisper model: {e}")
            raise
    
    def transcribe_audio(self, audio_data: np.ndarray, 
                        sample_rate: int = None,
                        initial_prompt: str = None) -> TranscriptionResult:
        """Transcribe audio data.
        
        Args:
            audio_data: Audio data as numpy array
            sample_rate: Audio sample rate
            initial_prompt: Optional initial prompt for context
            
        Returns:
            TranscriptionResult object
        """
        if sample_rate is None:
            sample_rate = self.sample_rate
        
        try:
            # Resample if necessary
            if sample_rate != self.sample_rate:
                audio_data = self._resample_audio(audio_data, sample_rate, self.sample_rate)
            
            # Normalize audio
            audio_data = audio_data.astype(np.float32)
            if np.max(np.abs(audio_data)) > 0:
                audio_data = audio_data / np.max(np.abs(audio_data))
            
            # Transcribe
            result = self.model.transcribe(
                audio_data,
                language=self.language,
                initial_prompt=initial_prompt,
                word_timestamps=False,  # Disable for faster processing
                fp16=False  # Use fp32 for better compatibility
            )
            
            # Extract text and confidence
            text = result["text"].strip()
            confidence = self._calculate_confidence(result)
            
            return TranscriptionResult(
                text=text,
                confidence=confidence,
                timestamp=time.time(),
                speaker_id="",
                speaker_name="",
                language=self.language,
                is_final=True
            )
            
        except Exception as e:
            logger.error(f"Error in transcription: {e}")
            return TranscriptionResult(
                text="",
                confidence=0.0,
                timestamp=time.time(),
                speaker_id="",
                speaker_name="",
                language=self.language,
                is_final=True
            )
    
    def _resample_audio(self, audio_data: np.ndarray, 
                       original_sr: int, target_sr: int) -> np.ndarray:
        """Resample audio data."""
        try:
            import librosa
            return librosa.resample(audio_data, orig_sr=original_sr, target_sr=target_sr)
        except ImportError:
            # Fallback: simple linear interpolation
            ratio = target_sr / original_sr
            new_length = int(len(audio_data) * ratio)
            indices = np.linspace(0, len(audio_data) - 1, new_length)
            return np.interp(indices, np.arange(len(audio_data)), audio_data)
    
    def _calculate_confidence(self, whisper_result: Dict[str, Any]) -> float:
        """Calculate confidence score from Whisper result."""
        try:
            # Use average log probability if available
            if "segments" in whisper_result and whisper_result["segments"]:
                logprobs = []
                for segment in whisper_result["segments"]:
                    if "avg_logprob" in segment:
                        logprobs.append(segment["avg_logprob"])
                
                if logprobs:
                    # Convert log probability to confidence (0-1 scale)
                    avg_logprob = np.mean(logprobs)
                    confidence = min(1.0, max(0.0, np.exp(avg_logprob)))
                    return confidence
            
            # Fallback: estimate based on text length and noisiness
            text = whisper_result.get("text", "")
            if not text:
                return 0.0
            
            # Simple heuristic: longer text with reasonable length gets higher confidence
            length_score = min(1.0, len(text) / 100.0)  # Normalize by 100 chars
            return length_score * 0.8  # Scale down for conservative estimate
            
        except Exception as e:
            logger.warning(f"Error calculating confidence: {e}")
            return 0.5  # Default confidence


class RealTimeTranscriber:
    """Real-time transcriber with buffering and streaming capabilities."""
    
    def __init__(self, transcriber: WhisperTranscriber = None, **kwargs):
        """Initialize real-time transcriber.
        
        Args:
            transcriber: Existing WhisperTranscriber instance
            **kwargs: Arguments for WhisperTranscriber if not provided
        """
        self.transcriber = transcriber or WhisperTranscriber(**kwargs)
        
        # Audio buffers for each speaker
        self.speaker_buffers: Dict[str, List[np.ndarray]] = {}
        self.buffer_duration = 2.0  # seconds
        self.buffer_size = int(self.transcriber.sample_rate * self.buffer_duration)
        
        # Transcription state
        self.speaker_transcripts: Dict[str, str] = {}
        self.speaker_contexts: Dict[str, str] = {}
        
        # Processing
        self.transcription_queue = Queue()
        self.processing_thread = None
        self.stop_event = threading.Event()
        
        # Callbacks
        self.transcription_callbacks = []
        
        logger.info("Real-time transcriber initialized")
    
    def add_transcription_callback(self, callback: Callable[[TranscriptionResult], None]):
        """Add callback for transcription results."""
        self.transcription_callbacks.append(callback)
    
    def _start_processing_thread(self):
        """Start background transcription processing thread."""
        if self.processing_thread is None or not self.processing_thread.is_alive():
            self.stop_event.clear()
            self.processing_thread = threading.Thread(target=self._process_transcription_queue)
            self.processing_thread.daemon = True
            self.processing_thread.start()
    
    def _process_transcription_queue(self):
        """Process transcription queue in background thread."""
        while not self.stop_event.is_set():
            try:
                # Get next transcription task
                speaker_id, audio_data, sample_rate = self.transcription_queue.get(timeout=1.0)
                
                # Perform transcription
                result = self.transcriber.transcribe_audio(audio_data, sample_rate)
                result.speaker_id = speaker_id
                result.speaker_name = self._get_speaker_name(speaker_id)
                
                # Update speaker transcript
                if result.text:
                    self.speaker_transcripts[speaker_id] = result.text
                
                # Call callbacks
                for callback in self.transcription_callbacks:
                    try:
                        callback(result)
                    except Exception as e:
                        logger.error(f"Error in transcription callback: {e}")
                
                self.transcription_queue.task_done()
                
            except Empty:
                continue
            except Exception as e:
                logger.error(f"Error in transcription processing: {e}")
    
    def _get_speaker_name(self, speaker_id: str) -> str:
        """Get speaker name from ID."""
        # This would typically query the speaker database
        # For now, return a simple name based on ID
        if speaker_id.startswith("unknown"):
            return "Unknown Speaker"
        return f"Speaker {speaker_id}"
    
    def transcribe_separated_audio(self, separated_audio: SeparatedAudio, 
                                 speaker_matches: List[SpeakerMatch]):
        """Transcribe separated audio streams.
        
        Args:
            separated_audio: Separated audio streams
            speaker_matches: Speaker identification results
        """
        # Start processing thread if needed
        self._start_processing_thread()
        
        for i, (stream, match) in enumerate(zip(separated_audio.streams, speaker_matches)):
            if match.is_unknown and match.speaker_id == "skip":
                continue  # Skip short audio
            
            # Add to speaker buffer
            speaker_id = match.speaker_id
            if speaker_id not in self.speaker_buffers:
                self.speaker_buffers[speaker_id] = []
            
            self.speaker_buffers[speaker_id].append(stream)
            
            # Check if buffer is ready for transcription
            total_samples = sum(len(chunk) for chunk in self.speaker_buffers[speaker_id])
            if total_samples >= self.buffer_size:
                # Concatenate buffer
                audio_data = np.concatenate(self.speaker_buffers[speaker_id])
                
                # Queue for transcription
                self.transcription_queue.put((
                    speaker_id,
                    audio_data,
                    separated_audio.sample_rate
                ))
                
                # Clear buffer (keep some overlap)
                overlap_samples = int(self.buffer_size * 0.2)  # 20% overlap
                if len(self.speaker_buffers[speaker_id]) > 1:
                    # Keep last chunk for overlap
                    self.speaker_buffers[speaker_id] = self.speaker_buffers[speaker_id][-1:]
                else:
                    # Keep partial chunk for overlap
                    remaining_samples = max(0, len(audio_data) - overlap_samples)
                    if remaining_samples > 0:
                        self.speaker_buffers[speaker_id] = [audio_data[-overlap_samples:]]
                    else:
                        self.speaker_buffers[speaker_id] = []
    
    def get_speaker_transcript(self, speaker_id: str) -> str:
        """Get current transcript for speaker."""
        return self.speaker_transcripts.get(speaker_id, "")
    
    def get_all_transcripts(self) -> Dict[str, str]:
        """Get transcripts for all speakers."""
        return self.speaker_transcripts.copy()
    
    def clear_speaker_transcript(self, speaker_id: str):
        """Clear transcript for specific speaker."""
        if speaker_id in self.speaker_transcripts:
            del self.speaker_transcripts[speaker_id]
    
    def clear_all_transcripts(self):
        """Clear all transcripts."""
        self.speaker_transcripts.clear()
        self.speaker_buffers.clear()
    
    def stop(self):
        """Stop transcription processing."""
        self.stop_event.set()
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=2.0)


class StreamingTranscriber:
    """Streaming transcriber with incremental updates."""
    
    def __init__(self, transcriber: WhisperTranscriber = None, **kwargs):
        """Initialize streaming transcriber.
        
        Args:
            transcriber: Existing WhisperTranscriber instance
            **kwargs: Arguments for WhisperTranscriber if not provided
        """
        self.transcriber = transcriber or WhisperTranscriber(**kwargs)
        
        # Streaming state
        self.speaker_streams: Dict[str, List[np.ndarray]] = {}
        self.stream_duration = 1.0  # seconds
        self.stream_size = int(self.transcriber.sample_rate * self.stream_duration)
        
        # Callbacks
        self.streaming_callbacks = []
        
        logger.info("Streaming transcriber initialized")
    
    def add_streaming_callback(self, callback: Callable[[TranscriptionResult], None]):
        """Add callback for streaming transcription results."""
        self.streaming_callbacks.append(callback)
    
    def process_audio_chunk(self, speaker_id: str, audio_data: np.ndarray, 
                           sample_rate: int = None):
        """Process audio chunk for streaming transcription.
        
        Args:
            speaker_id: Speaker identifier
            audio_data: Audio data chunk
            sample_rate: Audio sample rate
        """
        if speaker_id not in self.speaker_streams:
            self.speaker_streams[speaker_id] = []
        
        # Add to stream
        self.speaker_streams[speaker_id].append(audio_data)
        
        # Check if we have enough data
        total_samples = sum(len(chunk) for chunk in self.speaker_streams[speaker_id])
        if total_samples >= self.stream_size:
            # Concatenate and transcribe
            audio_stream = np.concatenate(self.speaker_streams[speaker_id])
            
            # Perform transcription
            result = self.transcriber.transcribe_audio(audio_stream, sample_rate)
            result.speaker_id = speaker_id
            result.speaker_name = f"Speaker {speaker_id}"
            
            # Call callbacks
            for callback in self.streaming_callbacks:
                try:
                    callback(result)
                except Exception as e:
                    logger.error(f"Error in streaming callback: {e}")
            
            # Clear stream
            self.speaker_streams[speaker_id] = []


def create_transcriber(model_size: str = None, 
                      device: str = None,
                      language: str = None) -> WhisperTranscriber:
    """Create Whisper transcriber with configuration.
    
    Args:
        model_size: Whisper model size
        device: Device to use
        language: Target language
        
    Returns:
        WhisperTranscriber instance
    """
    return WhisperTranscriber(
        model_size=model_size,
        device=device,
        language=language
    )


def create_realtime_transcriber(**kwargs) -> RealTimeTranscriber:
    """Create real-time transcriber.
    
    Args:
        **kwargs: Arguments for WhisperTranscriber
        
    Returns:
        RealTimeTranscriber instance
    """
    return RealTimeTranscriber(**kwargs)
