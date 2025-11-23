"""
Audio Input Utility
Handles Bluetooth earphone microphone input and audio recording.
"""

import wave
import threading
import time
from typing import Optional, Callable
import subprocess
import os

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    pyaudio = None
    print("Warning: pyaudio not available. Install with: pip install pyaudio")


class BluetoothAudioInput:
    """Manages Bluetooth audio input for microphone."""
    
    def __init__(self,
                 sample_rate=16000,
                 chunk_size=1024,
                 channels=1,
                 format=pyaudio.paInt16):
        """Initialize Bluetooth audio input."""
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.channels = channels
        self.format = format
        
        self.audio = None
        self.stream = None
        self.is_recording = False
        self.recording_thread: Optional[threading.Thread] = None
        self.audio_callback: Optional[Callable] = None
        
        self._check_bluetooth_audio()
    
    def _check_bluetooth_audio(self):
        """Check if Bluetooth audio is available."""
        try:
            # Check if pulseaudio is running
            result = subprocess.run(['pulseaudio', '--check'], 
                                  capture_output=True, stderr=subprocess.DEVNULL)
            if result.returncode != 0:
                print("⚠️  PulseAudio not running. Starting PulseAudio...")
                subprocess.Popen(['pulseaudio', '--start'], 
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(1)
            
            # List audio devices
            self._list_audio_devices()
            
        except Exception as e:
            print(f"⚠️  Error checking Bluetooth audio: {e}")
            print("Make sure Bluetooth earphones are paired and connected.")
    
    def _list_audio_devices(self):
        """List available audio input devices."""
        if not PYAUDIO_AVAILABLE or pyaudio is None:
            print("⚠️  PyAudio not available. Audio input will not function.")
            return None
        
        try:
            self.audio = pyaudio.PyAudio()
            print("\nAvailable audio input devices:")
            print("-" * 50)
            
            input_device_index = None
            
            for i in range(self.audio.get_device_count()):
                info = self.audio.get_device_info_by_index(i)
                if info['maxInputChannels'] > 0:
                    device_name = info['name']
                    is_bluetooth = 'bluez' in device_name.lower() or 'bluetooth' in device_name.lower()
                    
                    marker = " [BLUETOOTH]" if is_bluetooth else ""
                    print(f"  [{i}] {device_name}{marker}")
                    
                    # Prefer Bluetooth device
                    if is_bluetooth and input_device_index is None:
                        input_device_index = i
            
            if input_device_index is not None:
                print(f"\n✅ Using Bluetooth audio device: {input_device_index}")
            else:
                print("\n⚠️  No Bluetooth device found. Using default input device.")
                # Try to find default input device
                input_device_index = self.audio.get_default_input_device_info()['index']
            
            return input_device_index
            
        except Exception as e:
            print(f"❌ Error listing audio devices: {e}")
            return None
    
    def get_bluetooth_input_device(self):
        """Get the Bluetooth audio input device index."""
        if not PYAUDIO_AVAILABLE or pyaudio is None:
            return None
        
        if not self.audio:
            self.audio = pyaudio.PyAudio()
        
        try:
            for i in range(self.audio.get_device_count()):
                info = self.audio.get_device_info_by_index(i)
                if info['maxInputChannels'] > 0:
                    device_name = info['name']
                    if 'bluez' in device_name.lower() or 'bluetooth' in device_name.lower():
                        return i
            
            # Fallback to default input device
            return self.audio.get_default_input_device_info()['index']
            
        except Exception as e:
            print(f"Error getting Bluetooth input device: {e}")
            return None
    
    def start_recording(self, duration: Optional[float] = None, 
                       output_file: Optional[str] = None,
                       callback: Optional[Callable] = None):
        """Start recording audio from Bluetooth microphone."""
        if not PYAUDIO_AVAILABLE or pyaudio is None:
            print("❌ PyAudio not available. Cannot record audio.")
            return
        
        if self.is_recording:
            print("⚠️  Already recording. Stop current recording first.")
            return
        
        if not self.audio:
            self.audio = pyaudio.PyAudio()
        
        device_index = self.get_bluetooth_input_device()
        if device_index is None:
            print("❌ No audio input device available.")
            return
        
        try:
            self.audio_callback = callback
            
            self.stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=self.chunk_size
            )
            
            self.is_recording = True
            
            if output_file:
                # Record to file
                self._record_to_file(output_file, duration)
            else:
                # Record to callback
                self._record_with_callback(duration)
                
        except Exception as e:
            print(f"❌ Error starting recording: {e}")
            self.is_recording = False
    
    def _record_to_file(self, output_file: str, duration: Optional[float] = None):
        """Record audio to WAV file."""
        frames = []
        chunk_count = 0
        max_chunks = None if duration is None else int((self.sample_rate / self.chunk_size) * duration)
        
        try:
            while self.is_recording:
                if max_chunks and chunk_count >= max_chunks:
                    break
                
                data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                frames.append(data)
                chunk_count += 1
                
                if self.audio_callback:
                    self.audio_callback(data)
            
            # Save to WAV file
            wf = wave.open(output_file, 'wb')
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.audio.get_sample_size(self.format))
            wf.setframerate(self.sample_rate)
            wf.writeframes(b''.join(frames))
            wf.close()
            
            print(f"✅ Audio recorded to {output_file}")
            
        except Exception as e:
            print(f"❌ Error recording to file: {e}")
        finally:
            self.stop_recording()
    
    def _record_with_callback(self, duration: Optional[float] = None):
        """Record audio and call callback with chunks."""
        start_time = time.time()
        
        try:
            while self.is_recording:
                if duration and (time.time() - start_time) >= duration:
                    break
                
                data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                
                if self.audio_callback:
                    self.audio_callback(data)
                    
        except Exception as e:
            print(f"❌ Error in recording callback: {e}")
        finally:
            self.stop_recording()
    
    def stop_recording(self):
        """Stop recording audio."""
        self.is_recording = False
        
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None
            except Exception as e:
                print(f"Error stopping stream: {e}")
    
    def record_audio(self, duration: float, output_file: str) -> bool:
        """Record audio for specified duration to file."""
        self.start_recording(duration=duration, output_file=output_file)
        return os.path.exists(output_file)
    
    def cleanup(self):
        """Clean up audio resources."""
        self.stop_recording()
        
        if self.audio:
            try:
                self.audio.terminate()
                self.audio = None
            except Exception as e:
                print(f"Error cleaning up audio: {e}")


def setup_bluetooth_audio():
    """Helper function to setup Bluetooth audio."""
    try:
        # Check if bluetoothctl is available
        result = subprocess.run(['which', 'bluetoothctl'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Bluetooth tools available")
            return True
        else:
            print("⚠️  Bluetooth tools not found. Install with: sudo apt install bluez")
            return False
            
    except Exception as e:
        print(f"Error checking Bluetooth setup: {e}")
        return False


if __name__ == "__main__":
    # Test audio input
    import time
    
    audio_input = BluetoothAudioInput()
    
    print("\nTesting audio recording (3 seconds)...")
    test_file = "/tmp/test_audio.wav"
    audio_input.record_audio(duration=3.0, output_file=test_file)
    
    if os.path.exists(test_file):
        print(f"✅ Test recording saved to {test_file}")
        os.remove(test_file)
    else:
        print("❌ Test recording failed")

