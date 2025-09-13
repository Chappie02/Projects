"""
Main pipeline for real-time speaker isolation and identification.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Callable, Any
import time
from dataclasses import dataclass
import threading

from .config import config
from .audio_stream import AudioStreamer, AudioChunk
from .separation import RealTimeSpeechSeparator, SeparatedAudio
from .speaker_id import SpeakerIdentifier, SpeakerMatch
from .transcription import RealTimeTranscriber, TranscriptionResult
from .utils import PerformanceMonitor

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Result from the complete processing pipeline."""
    separated_audio: SeparatedAudio
    speaker_matches: List[SpeakerMatch]
    transcription_results: List[TranscriptionResult]
    processing_time: float
    timestamp: float


class SpeakerIsolationPipeline:
    """Main pipeline for real-time speaker isolation and identification."""
    
    def __init__(self, 
                 audio_streamer: AudioStreamer = None,
                 speech_separator: RealTimeSpeechSeparator = None,
                 speaker_identifier: SpeakerIdentifier = None,
                 transcriber: RealTimeTranscriber = None):
        """Initialize the processing pipeline.
        
        Args:
            audio_streamer: Audio streaming component
            speech_separator: Speech separation component
            speaker_identifier: Speaker identification component
            transcriber: Speech transcription component
        """
        self.audio_streamer = audio_streamer
        self.speech_separator = speech_separator
        self.speaker_identifier = speaker_identifier
        self.transcriber = transcriber
        
        # Pipeline state
        self.is_running = False
        self.processing_thread = None
        self.stop_event = threading.Event()
        
        # Performance monitoring
        self.performance_monitor = PerformanceMonitor()
        
        # Callbacks
        self.pipeline_callbacks = []
        self.result_callbacks = []
        
        # Statistics
        self.stats = {
            "total_chunks_processed": 0,
            "total_speakers_identified": 0,
            "total_transcriptions": 0,
            "session_start_time": None,
            "last_processing_time": 0.0
        }
        
        logger.info("Speaker isolation pipeline initialized")
    
    def add_pipeline_callback(self, callback: Callable[[PipelineResult], None]):
        """Add callback for complete pipeline results.
        
        Args:
            callback: Function to call with pipeline results
        """
        self.pipeline_callbacks.append(callback)
    
    def add_result_callback(self, callback: Callable[[str, Any], None]):
        """Add callback for individual component results.
        
        Args:
            callback: Function to call with (component_name, result) tuples
        """
        self.result_callbacks.append(callback)
    
    def _notify_callbacks(self, result: PipelineResult):
        """Notify all registered callbacks."""
        # Pipeline callbacks
        for callback in self.pipeline_callbacks:
            try:
                callback(result)
            except Exception as e:
                logger.error(f"Error in pipeline callback: {e}")
        
        # Individual result callbacks
        for callback in self.result_callbacks:
            try:
                callback("separated_audio", result.separated_audio)
                callback("speaker_matches", result.speaker_matches)
                callback("transcription_results", result.transcription_results)
            except Exception as e:
                logger.error(f"Error in result callback: {e}")
    
    def _process_audio_chunk(self, audio_chunk: AudioChunk):
        """Process a single audio chunk through the complete pipeline.
        
        Args:
            audio_chunk: Input audio chunk
        """
        pipeline_start_time = time.time()
        
        try:
            # Start performance monitoring
            self.performance_monitor.start_timer("total_pipeline")
            
            # Step 1: Speech Separation
            self.performance_monitor.start_timer("separation")
            separated_audio = self.speech_separator.separator.separate_audio(audio_chunk)
            self.performance_monitor.end_timer("separation")
            
            if separated_audio.num_speakers == 0:
                logger.warning("No speakers detected in audio chunk")
                return
            
            # Step 2: Speaker Identification
            self.performance_monitor.start_timer("speaker_id")
            speaker_matches = self.speaker_identifier.identify_speakers(separated_audio)
            self.performance_monitor.end_timer("speaker_id")
            
            # Step 3: Speech Transcription
            transcription_results = []
            self.performance_monitor.start_timer("transcription")
            
            # Process each separated stream
            for i, (stream, match) in enumerate(zip(separated_audio.streams, speaker_matches)):
                if match.is_unknown and match.speaker_id == "skip":
                    continue  # Skip short audio
                
                # Transcribe the stream
                result = self.transcriber.transcriber.transcribe_audio(stream, separated_audio.sample_rate)
                result.speaker_id = match.speaker_id
                result.speaker_name = match.name
                
                if result.text.strip():  # Only include non-empty transcriptions
                    transcription_results.append(result)
            
            self.performance_monitor.end_timer("transcription")
            
            # Complete pipeline timing
            total_time = self.performance_monitor.end_timer("total_pipeline")
            
            # Create pipeline result
            pipeline_result = PipelineResult(
                separated_audio=separated_audio,
                speaker_matches=speaker_matches,
                transcription_results=transcription_results,
                processing_time=total_time,
                timestamp=time.time()
            )
            
            # Update statistics
            self.stats["total_chunks_processed"] += 1
            self.stats["total_speakers_identified"] += len([m for m in speaker_matches if not m.is_unknown])
            self.stats["total_transcriptions"] += len(transcription_results)
            self.stats["last_processing_time"] = total_time
            
            # Notify callbacks
            self._notify_callbacks(pipeline_result)
            
            # Log processing info
            logger.debug(f"Processed audio chunk: {separated_audio.num_speakers} speakers, "
                        f"{len(transcription_results)} transcriptions, "
                        f"{total_time:.3f}s processing time")
            
        except Exception as e:
            logger.error(f"Error processing audio chunk: {e}")
            self.performance_monitor.end_timer("total_pipeline")
    
    def _processing_loop(self):
        """Main processing loop for the pipeline."""
        logger.info("Pipeline processing loop started")
        
        while not self.stop_event.is_set():
            try:
                # The actual processing is handled by the audio streamer callbacks
                # This loop just keeps the thread alive and handles any background tasks
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error in processing loop: {e}")
                break
        
        logger.info("Pipeline processing loop stopped")
    
    def start(self) -> bool:
        """Start the processing pipeline.
        
        Returns:
            True if started successfully, False otherwise
        """
        if self.is_running:
            logger.warning("Pipeline already running")
            return False
        
        try:
            # Validate components
            if not all([self.audio_streamer, self.speech_separator, 
                       self.speaker_identifier, self.transcriber]):
                raise ValueError("All pipeline components must be initialized")
            
            # Setup audio streamer callback
            self.audio_streamer.add_chunk_callback(self._process_audio_chunk)
            
            # Start audio streaming
            if not self.audio_streamer.start_streaming():
                raise RuntimeError("Failed to start audio streaming")
            
            # Start processing thread
            self.stop_event.clear()
            self.processing_thread = threading.Thread(target=self._processing_loop)
            self.processing_thread.daemon = True
            self.processing_thread.start()
            
            # Update state
            self.is_running = True
            self.stats["session_start_time"] = time.time()
            
            logger.info("Speaker isolation pipeline started")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start pipeline: {e}")
            self.is_running = False
            return False
    
    def stop(self):
        """Stop the processing pipeline."""
        if not self.is_running:
            return
        
        try:
            # Stop audio streaming
            if self.audio_streamer:
                self.audio_streamer.stop_streaming()
            
            # Stop processing thread
            self.stop_event.set()
            if self.processing_thread and self.processing_thread.is_alive():
                self.processing_thread.join(timeout=2.0)
            
            # Stop transcription
            if self.transcriber:
                self.transcriber.stop()
            
            # Update state
            self.is_running = False
            
            logger.info("Speaker isolation pipeline stopped")
            
        except Exception as e:
            logger.error(f"Error stopping pipeline: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current pipeline status.
        
        Returns:
            Dictionary with pipeline status information
        """
        uptime = 0.0
        if self.stats["session_start_time"]:
            uptime = time.time() - self.stats["session_start_time"]
        
        performance_summary = self.performance_monitor.get_performance_summary()
        
        return {
            "is_running": self.is_running,
            "uptime_seconds": uptime,
            "statistics": self.stats.copy(),
            "performance": performance_summary,
            "components": {
                "audio_streamer": self.audio_streamer is not None,
                "speech_separator": self.speech_separator is not None,
                "speaker_identifier": self.speaker_identifier is not None,
                "transcriber": self.transcriber is not None
            }
        }
    
    def get_active_speakers(self) -> List[str]:
        """Get list of currently active speakers."""
        if self.speaker_identifier:
            return self.speaker_identifier.get_active_speakers()
        return []
    
    def get_transcripts(self) -> Dict[str, str]:
        """Get current transcripts for all speakers."""
        if self.transcriber:
            return self.transcriber.get_all_transcripts()
        return {}
    
    def reset_statistics(self):
        """Reset pipeline statistics."""
        self.stats = {
            "total_chunks_processed": 0,
            "total_speakers_identified": 0,
            "total_transcriptions": 0,
            "session_start_time": None,
            "last_processing_time": 0.0
        }
        self.performance_monitor.reset_metrics()
        logger.info("Pipeline statistics reset")


class PipelineBuilder:
    """Builder class for creating configured pipeline instances."""
    
    def __init__(self):
        """Initialize pipeline builder."""
        self.components = {}
        self.callbacks = []
    
    def with_audio_streamer(self, audio_streamer: AudioStreamer):
        """Add audio streamer component."""
        self.components["audio_streamer"] = audio_streamer
        return self
    
    def with_speech_separator(self, speech_separator: RealTimeSpeechSeparator):
        """Add speech separator component."""
        self.components["speech_separator"] = speech_separator
        return self
    
    def with_speaker_identifier(self, speaker_identifier: SpeakerIdentifier):
        """Add speaker identifier component."""
        self.components["speaker_identifier"] = speaker_identifier
        return self
    
    def with_transcriber(self, transcriber: RealTimeTranscriber):
        """Add transcriber component."""
        self.components["transcriber"] = transcriber
        return self
    
    def with_callback(self, callback: Callable[[PipelineResult], None]):
        """Add pipeline callback."""
        self.callbacks.append(callback)
        return self
    
    def build(self) -> SpeakerIsolationPipeline:
        """Build the configured pipeline.
        
        Returns:
            Configured SpeakerIsolationPipeline instance
        """
        # Create pipeline with components
        pipeline = SpeakerIsolationPipeline(
            audio_streamer=self.components.get("audio_streamer"),
            speech_separator=self.components.get("speech_separator"),
            speaker_identifier=self.components.get("speaker_identifier"),
            transcriber=self.components.get("transcriber")
        )
        
        # Add callbacks
        for callback in self.callbacks:
            pipeline.add_pipeline_callback(callback)
        
        return pipeline


def create_default_pipeline() -> SpeakerIsolationPipeline:
    """Create a default pipeline with all components configured.
    
    Returns:
        Configured SpeakerIsolationPipeline instance
    """
    from .separation import create_realtime_separator
    from .speaker_id import create_speaker_identifier
    from .transcription import create_realtime_transcriber
    
    # Create components
    audio_streamer = AudioStreamer()
    speech_separator = create_realtime_separator()
    speaker_identifier = create_speaker_identifier()
    transcriber = create_realtime_transcriber()
    
    # Build pipeline
    return PipelineBuilder() \
        .with_audio_streamer(audio_streamer) \
        .with_speech_separator(speech_separator) \
        .with_speaker_identifier(speaker_identifier) \
        .with_transcriber(transcriber) \
        .build()


async def run_pipeline_demo():
    """Run a demonstration of the speaker isolation pipeline."""
    logger.info("Starting pipeline demonstration")
    
    # Create pipeline
    pipeline = create_default_pipeline()
    
    # Add demo callback
    def demo_callback(result: PipelineResult):
        logger.info(f"Pipeline result: {result.separated_audio.num_speakers} speakers, "
                   f"{len(result.transcription_results)} transcriptions")
    
    pipeline.add_pipeline_callback(demo_callback)
    
    try:
        # Start pipeline
        if pipeline.start():
            logger.info("Pipeline started successfully. Press Ctrl+C to stop.")
            
            # Keep running until interrupted
            while pipeline.is_running:
                await asyncio.sleep(1.0)
                
                # Print status every 10 seconds
                status = pipeline.get_status()
                if status["statistics"]["total_chunks_processed"] % 10 == 0:
                    logger.info(f"Processed {status['statistics']['total_chunks_processed']} chunks")
        
        else:
            logger.error("Failed to start pipeline")
    
    except KeyboardInterrupt:
        logger.info("Demo interrupted by user")
    
    finally:
        pipeline.stop()
        logger.info("Pipeline demonstration completed")
