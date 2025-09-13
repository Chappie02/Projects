"""
Tests for audio streaming functionality.
"""

import pytest
import numpy as np
import tempfile
import os
from unittest.mock import Mock, patch

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.audio_stream import AudioStreamer, AudioFileStreamer, AudioChunk


class TestAudioChunk:
    """Test AudioChunk class."""
    
    def test_audio_chunk_creation(self):
        """Test AudioChunk creation and properties."""
        data = np.random.randn(16000)  # 1 second at 16kHz
        timestamp = 1234567890.0
        sample_rate = 16000
        channels = 1
        
        chunk = AudioChunk(data, timestamp, sample_rate, channels)
        
        assert chunk.data is data
        assert chunk.timestamp == timestamp
        assert chunk.sample_rate == sample_rate
        assert chunk.channels == channels
        assert chunk.duration == 1.0
    
    def test_audio_chunk_duration_calculation(self):
        """Test duration calculation."""
        # Test with different durations
        for duration in [0.5, 1.0, 2.0, 3.5]:
            samples = int(duration * 16000)
            data = np.random.randn(samples)
            chunk = AudioChunk(data, 0.0, 16000, 1)
            assert abs(chunk.duration - duration) < 0.001


class TestAudioStreamer:
    """Test AudioStreamer class."""
    
    @patch('src.audio_stream.pyaudio.PyAudio')
    def test_audio_streamer_initialization(self, mock_pyaudio):
        """Test AudioStreamer initialization."""
        mock_audio = Mock()
        mock_pyaudio.return_value = mock_audio
        
        streamer = AudioStreamer()
        
        assert streamer.sample_rate == 16000  # Default
        assert streamer.chunk_duration == 1.0  # Default
        assert streamer.chunk_size == 16000  # 1 second at 16kHz
        assert not streamer.is_streaming
    
    @patch('src.audio_stream.pyaudio.PyAudio')
    def test_audio_streamer_custom_params(self, mock_pyaudio):
        """Test AudioStreamer with custom parameters."""
        mock_audio = Mock()
        mock_pyaudio.return_value = mock_audio
        
        streamer = AudioStreamer(
            sample_rate=8000,
            chunk_duration=0.5,
            device_index=1
        )
        
        assert streamer.sample_rate == 8000
        assert streamer.chunk_duration == 0.5
        assert streamer.chunk_size == 4000  # 0.5 seconds at 8kHz
        assert streamer.device_index == 1
    
    @patch('src.audio_stream.pyaudio.PyAudio')
    def test_add_chunk_callback(self, mock_pyaudio):
        """Test adding chunk callbacks."""
        mock_audio = Mock()
        mock_pyaudio.return_value = mock_audio
        
        streamer = AudioStreamer()
        callback = Mock()
        
        streamer.add_chunk_callback(callback)
        assert callback in streamer.chunk_callbacks
        
        streamer.remove_chunk_callback(callback)
        assert callback not in streamer.chunk_callbacks
    
    @patch('src.audio_stream.pyaudio.PyAudio')
    def test_get_available_devices(self, mock_pyaudio):
        """Test getting available audio devices."""
        mock_audio = Mock()
        mock_audio.get_device_count.return_value = 2
        mock_audio.get_device_info_by_index.side_effect = [
            {'maxInputChannels': 1, 'name': 'Microphone 1', 'defaultSampleRate': 44100},
            {'maxInputChannels': 0, 'name': 'Speaker 1', 'defaultSampleRate': 44100}
        ]
        mock_pyaudio.return_value = mock_audio
        
        streamer = AudioStreamer()
        devices = streamer.get_available_devices()
        
        assert len(devices) == 1  # Only input devices
        assert devices[0]['name'] == 'Microphone 1'
        assert devices[0]['channels'] == 1


class TestAudioFileStreamer:
    """Test AudioFileStreamer class."""
    
    def test_audio_file_streamer_creation(self):
        """Test AudioFileStreamer creation."""
        # Create a temporary audio file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            # Write a simple WAV file header (minimal)
            wav_data = self._create_simple_wav(16000, 1.0)  # 1 second at 16kHz
            tmp_file.write(wav_data)
            tmp_file.flush()
            
            try:
                with patch('librosa.load') as mock_load:
                    mock_load.return_value = (np.random.randn(16000), 16000)
                    
                    streamer = AudioFileStreamer(tmp_file.name)
                    
                    assert streamer.file_path == tmp_file.name
                    assert streamer.sample_rate == 16000
                    assert streamer.chunk_duration == 1.0
                    assert streamer.chunk_size == 16000
                    assert streamer.current_position == 0
                    
            finally:
                os.unlink(tmp_file.name)
    
    def test_add_chunk_callback(self):
        """Test adding chunk callbacks to file streamer."""
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            wav_data = self._create_simple_wav(16000, 1.0)
            tmp_file.write(wav_data)
            tmp_file.flush()
            
            try:
                with patch('librosa.load') as mock_load:
                    mock_load.return_value = (np.random.randn(16000), 16000)
                    
                    streamer = AudioFileStreamer(tmp_file.name)
                    callback = Mock()
                    
                    streamer.add_chunk_callback(callback)
                    assert callback in streamer.chunk_callbacks
                    
            finally:
                os.unlink(tmp_file.name)
    
    def test_reset(self):
        """Test resetting file streamer position."""
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            wav_data = self._create_simple_wav(16000, 1.0)
            tmp_file.write(wav_data)
            tmp_file.flush()
            
            try:
                with patch('librosa.load') as mock_load:
                    mock_load.return_value = (np.random.randn(16000), 16000)
                    
                    streamer = AudioFileStreamer(tmp_file.name)
                    streamer.current_position = 8000  # Move position
                    
                    streamer.reset()
                    assert streamer.current_position == 0
                    
            finally:
                os.unlink(tmp_file.name)
    
    def _create_simple_wav(self, sample_rate: int, duration: float) -> bytes:
        """Create a simple WAV file for testing."""
        # This is a minimal WAV file structure
        samples = int(sample_rate * duration)
        audio_data = np.random.randint(-32768, 32767, samples, dtype=np.int16)
        
        # WAV header
        header = bytearray()
        header.extend(b'RIFF')
        header.extend((len(audio_data) * 2 + 36).to_bytes(4, 'little'))
        header.extend(b'WAVE')
        header.extend(b'fmt ')
        header.extend((16).to_bytes(4, 'little'))  # fmt chunk size
        header.extend((1).to_bytes(2, 'little'))   # PCM format
        header.extend((1).to_bytes(2, 'little'))   # mono
        header.extend(sample_rate.to_bytes(4, 'little'))
        header.extend((sample_rate * 2).to_bytes(4, 'little'))  # byte rate
        header.extend((2).to_bytes(2, 'little'))   # block align
        header.extend((16).to_bytes(2, 'little'))  # bits per sample
        header.extend(b'data')
        header.extend((len(audio_data) * 2).to_bytes(4, 'little'))
        
        # Audio data
        audio_bytes = audio_data.tobytes()
        
        return bytes(header) + audio_bytes


@pytest.fixture
def sample_audio_chunk():
    """Create a sample AudioChunk for testing."""
    data = np.random.randn(16000)
    return AudioChunk(data, 1234567890.0, 16000, 1)


def test_audio_chunk_fixture(sample_audio_chunk):
    """Test the sample audio chunk fixture."""
    assert len(sample_audio_chunk.data) == 16000
    assert sample_audio_chunk.duration == 1.0
    assert sample_audio_chunk.sample_rate == 16000
