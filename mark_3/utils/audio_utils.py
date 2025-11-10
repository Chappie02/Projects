"""
Audio Utilities
Handles Bluetooth microphone and speaker for voice input and output.
"""

import pyaudio
import wave
import threading
import queue
import time
from typing import Optional, Callable
import subprocess
import os


class AudioManager:
    """Manages audio input and output for voice interactions."""
    
    def __init__(self, sample_rate=16000, chunk_size=4096, channels=1, format=pyaudio.paInt16):
        """
        Initialize audio manager.
        
        Args:
            sample_rate: Audio sample rate (Hz)
            chunk_size: Number of frames per buffer
            channels: Number of audio channels (1 for mono)
            format: Audio format
        """
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.channels = channels
        self.format = format
        self.audio = pyaudio.PyAudio()
        
        self.is_recording = False
        self.is_playing = False
        self.audio_queue = queue.Queue()
        self.recording_thread: Optional[threading.Thread] = None
        
        # Try to find Bluetooth audio devices
        self.input_device_index = self._find_bluetooth_input_device()
        self.output_device_index = self._find_bluetooth_output_device()
        
    def _find_bluetooth_input_device(self) -> Optional[int]:
        """Find Bluetooth microphone device index."""
        try:
            # List all audio input devices
            device_count = self.audio.get_device_count()
            for i in range(device_count):
                device_info = self.audio.get_device_info_by_index(i)
                device_name = device_info.get('name', '').lower()
                # Check if device name contains bluetooth-related keywords
                if device_info.get('maxInputChannels', 0) > 0:
                    if any(keyword in device_name for keyword in ['bluetooth', 'bt', 'bluez']):
                        print(f"✅ Found Bluetooth input device: {device_info['name']} (index: {i})")
                        return i
            # If no Bluetooth device found, use default input
            default_input = self.audio.get_default_input_device_info()
            print(f"⚠️  No Bluetooth input found, using default: {default_input['name']}")
            return default_input.get('index')
        except Exception as e:
            print(f"⚠️  Error finding input device: {e}, using default")
            return None
    
    def _find_bluetooth_output_device(self) -> Optional[int]:
        """Find Bluetooth speaker device index."""
        try:
            # List all audio output devices
            device_count = self.audio.get_device_count()
            for i in range(device_count):
                device_info = self.audio.get_device_info_by_index(i)
                device_name = device_info.get('name', '').lower()
                # Check if device name contains bluetooth-related keywords
                if device_info.get('maxOutputChannels', 0) > 0:
                    if any(keyword in device_name for keyword in ['bluetooth', 'bt', 'bluez']):
                        print(f"✅ Found Bluetooth output device: {device_info['name']} (index: {i})")
                        return i
            # If no Bluetooth device found, use default output
            default_output = self.audio.get_default_output_device_info()
            print(f"⚠️  No Bluetooth output found, using default: {default_output['name']}")
            return default_output.get('index')
        except Exception as e:
            print(f"⚠️  Error finding output device: {e}, using default")
            return None
    
    def record_audio(self, duration: float, callback: Optional[Callable] = None) -> bytes:
        """
        Record audio for specified duration.
        
        Args:
            duration: Recording duration in seconds
            callback: Optional callback function called with audio chunks
            
        Returns:
            Recorded audio data as bytes
        """
        try:
            stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=self.input_device_index,
                frames_per_buffer=self.chunk_size
            )
            
            frames = []
            num_chunks = int(self.sample_rate / self.chunk_size * duration)
            
            for _ in range(num_chunks):
                data = stream.read(self.chunk_size, exception_on_overflow=False)
                frames.append(data)
                if callback:
                    callback(data)
            
            stream.stop_stream()
            stream.close()
            
            return b''.join(frames)
            
        except Exception as e:
            print(f"❌ Error recording audio: {e}")
            return b''
    
    def record_audio_stream(self, callback: Callable, duration: Optional[float] = None):
        """
        Record audio continuously and call callback with chunks.
        
        Args:
            callback: Callback function called with each audio chunk
            duration: Optional maximum recording duration
        """
        if self.is_recording:
            return
        
        self.is_recording = True
        
        def _record():
            try:
                stream = self.audio.open(
                    format=self.format,
                    channels=self.channels,
                    rate=self.sample_rate,
                    input=True,
                    input_device_index=self.input_device_index,
                    frames_per_buffer=self.chunk_size
                )
                
                start_time = time.time()
                
                while self.is_recording:
                    if duration and (time.time() - start_time) > duration:
                        break
                    
                    try:
                        data = stream.read(self.chunk_size, exception_on_overflow=False)
                        callback(data)
                    except Exception as e:
                        print(f"Error reading audio: {e}")
                        break
                
                stream.stop_stream()
                stream.close()
                
            except Exception as e:
                print(f"❌ Error in recording stream: {e}")
            finally:
                self.is_recording = False
        
        self.recording_thread = threading.Thread(target=_record, daemon=True)
        self.recording_thread.start()
    
    def stop_recording(self):
        """Stop recording audio."""
        self.is_recording = False
        if self.recording_thread:
            self.recording_thread.join(timeout=1.0)
    
    def play_audio(self, audio_data: bytes):
        """
        Play audio data through speaker.
        
        Args:
            audio_data: Audio data as bytes
        """
        try:
            stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                output=True,
                output_device_index=self.output_device_index,
                frames_per_buffer=self.chunk_size
            )
            
            # Split audio data into chunks and play
            chunk_size = self.chunk_size * 2  # 2 bytes per sample for Int16
            for i in range(0, len(audio_data), chunk_size):
                chunk = audio_data[i:i + chunk_size]
                stream.write(chunk)
            
            stream.stop_stream()
            stream.close()
            
        except Exception as e:
            print(f"❌ Error playing audio: {e}")
    
    def play_audio_file(self, file_path: str):
        """
        Play audio from file.
        
        Args:
            file_path: Path to audio file
        """
        try:
            # Use system audio player for better compatibility
            subprocess.run(['aplay', file_path], check=False, 
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            print(f"⚠️  Error playing audio file: {e}")
            # Fallback to pyaudio
            try:
                with wave.open(file_path, 'rb') as wf:
                    audio_data = wf.readframes(wf.getnframes())
                    self.play_audio(audio_data)
            except Exception as e2:
                print(f"❌ Error with fallback audio playback: {e2}")
    
    def save_audio(self, audio_data: bytes, file_path: str):
        """
        Save audio data to WAV file.
        
        Args:
            audio_data: Audio data as bytes
            file_path: Output file path
        """
        try:
            with wave.open(file_path, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(self.audio.get_sample_size(self.format))
                wf.setframerate(self.sample_rate)
                wf.writeframes(audio_data)
        except Exception as e:
            print(f"❌ Error saving audio: {e}")
    
    def cleanup(self):
        """Clean up audio resources."""
        self.stop_recording()
        if hasattr(self, 'audio'):
            self.audio.terminate()


def test_audio_devices():
    """Test available audio devices."""
    audio = pyaudio.PyAudio()
    print("\n📱 Available Audio Devices:")
    print("=" * 60)
    
    device_count = audio.get_device_count()
    for i in range(device_count):
        device_info = audio.get_device_info_by_index(i)
        device_type = []
        if device_info.get('maxInputChannels', 0) > 0:
            device_type.append("INPUT")
        if device_info.get('maxOutputChannels', 0) > 0:
            device_type.append("OUTPUT")
        
        print(f"Device {i}: {device_info['name']}")
        print(f"  Type: {', '.join(device_type)}")
        print(f"  Channels: {device_info.get('maxInputChannels', 0)} in, {device_info.get('maxOutputChannels', 0)} out")
        print(f"  Sample Rate: {device_info.get('defaultSampleRate', 'N/A')} Hz")
        print()
    
    audio.terminate()


if __name__ == "__main__":
    test_audio_devices()

