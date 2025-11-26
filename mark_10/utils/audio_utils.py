"""
Audio Utilities
Handles USB microphone input and speaker output for Raspberry Pi.
"""

import time
import threading
from typing import Optional, Callable
import queue

try:
    import pyaudio
    import wave
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    pyaudio = None
    wave = None

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    pyttsx3 = None


class AudioManager:
    """Manages audio input and output operations."""
    
    def __init__(self, sample_rate=16000, chunk_size=1024):
        """
        Initialize audio manager.
        
        Args:
            sample_rate: Audio sample rate (default: 16000 Hz)
            chunk_size: Audio chunk size (default: 1024)
        """
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.audio: Optional[pyaudio.PyAudio] = None
        self.is_recording = False
        self.recording_thread: Optional[threading.Thread] = None
        self.audio_queue = queue.Queue()
        self.tts_engine: Optional[pyttsx3.Engine] = None
        
        if AUDIO_AVAILABLE:
            self._initialize_audio()
        else:
            print("⚠️  Audio libraries not available. Audio functionality disabled.")
        
        if TTS_AVAILABLE:
            self._initialize_tts()
        else:
            print("⚠️  TTS libraries not available. Text-to-speech disabled.")
    
    def _initialize_audio(self):
        """Initialize PyAudio."""
        try:
            self.audio = pyaudio.PyAudio()
            print("✅ Audio system initialized successfully!")
        except Exception as e:
            print(f"❌ Error initializing audio: {e}")
            self.audio = None
    
    def _initialize_tts(self):
        """Initialize text-to-speech engine."""
        try:
            self.tts_engine = pyttsx3.init()
            # Set speech rate and volume
            self.tts_engine.setProperty('rate', 150)
            self.tts_engine.setProperty('volume', 0.8)
            print("✅ Text-to-speech initialized successfully!")
        except Exception as e:
            print(f"⚠️  Error initializing TTS: {e}")
            self.tts_engine = None
    
    def list_audio_devices(self):
        """List available audio input and output devices."""
        if not self.audio:
            return
        
        print("\n📢 Available Audio Devices:")
        print("-" * 50)
        
        for i in range(self.audio.get_device_count()):
            info = self.audio.get_device_info_by_index(i)
            device_type = []
            if info['maxInputChannels'] > 0:
                device_type.append("Input")
            if info['maxOutputChannels'] > 0:
                device_type.append("Output")
            
            print(f"Device {i}: {info['name']} ({', '.join(device_type)})")
    
    def find_usb_microphone(self) -> Optional[int]:
        """
        Find USB microphone device index.
        
        Returns:
            Device index if found, None otherwise
        """
        if not self.audio:
            return None
        
        for i in range(self.audio.get_device_count()):
            info = self.audio.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                name = info['name'].lower()
                # Look for USB microphone
                if 'usb' in name or 'microphone' in name or 'mic' in name:
                    return i
        
        # Fallback to default input device
        try:
            return self.audio.get_default_input_device_info()['index']
        except:
            return None
    
    def find_usb_speaker(self) -> Optional[int]:
        """
        Find USB speaker device index.
        
        Returns:
            Device index if found, None otherwise
        """
        if not self.audio:
            return None
        
        for i in range(self.audio.get_device_count()):
            info = self.audio.get_device_info_by_index(i)
            if info['maxOutputChannels'] > 0:
                name = info['name'].lower()
                # Look for USB speaker
                if 'usb' in name or 'speaker' in name or 'audio' in name:
                    return i
        
        # Fallback to default output device
        try:
            return self.audio.get_default_output_device_info()['index']
        except:
            return None
    
    def start_recording(self, duration: Optional[float] = None, callback: Optional[Callable] = None):
        """
        Start recording audio from microphone.
        
        Args:
            duration: Recording duration in seconds (None for continuous)
            callback: Optional callback function(data) called with audio data
        """
        if not self.audio or self.is_recording:
            return
        
        input_device = self.find_usb_microphone()
        if input_device is None:
            print("❌ No microphone found")
            return
        
        self.is_recording = True
        
        def record_audio():
            try:
                stream = self.audio.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=self.sample_rate,
                    input=True,
                    input_device_index=input_device,
                    frames_per_buffer=self.chunk_size
                )
                
                frames = []
                start_time = time.time()
                
                while self.is_recording:
                    if duration and (time.time() - start_time) >= duration:
                        break
                    
                    data = stream.read(self.chunk_size, exception_on_overflow=False)
                    frames.append(data)
                    
                    if callback:
                        callback(data)
                
                stream.stop_stream()
                stream.close()
                
                # Return recorded audio data
                audio_data = b''.join(frames)
                self.audio_queue.put(audio_data)
                
            except Exception as e:
                print(f"❌ Error recording audio: {e}")
                self.audio_queue.put(None)
        
        self.recording_thread = threading.Thread(target=record_audio, daemon=True)
        self.recording_thread.start()
    
    def stop_recording(self) -> Optional[bytes]:
        """
        Stop recording and return audio data.
        
        Returns:
            Recorded audio data as bytes, or None if error
        """
        if not self.is_recording:
            return None
        
        self.is_recording = False
        
        if self.recording_thread:
            self.recording_thread.join(timeout=2.0)
        
        try:
            return self.audio_queue.get(timeout=1.0)
        except queue.Empty:
            return None
    
    def record_audio(self, duration: float) -> Optional[bytes]:
        """
        Record audio for a specified duration.
        
        Args:
            duration: Recording duration in seconds
        
        Returns:
            Recorded audio data as bytes, or None if error
        """
        self.start_recording(duration=duration)
        time.sleep(duration + 0.1)  # Add small buffer
        return self.stop_recording()
    
    def save_audio(self, audio_data: bytes, filename: str):
        """
        Save audio data to WAV file.
        
        Args:
            audio_data: Audio data as bytes
            filename: Output filename
        """
        if not wave or not audio_data:
            return
        
        try:
            with wave.open(filename, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(self.sample_rate)
                wf.writeframes(audio_data)
            print(f"✅ Audio saved to {filename}")
        except Exception as e:
            print(f"❌ Error saving audio: {e}")
    
    def speak(self, text: str):
        """
        Convert text to speech and play through speaker.
        
        Args:
            text: Text to speak
        """
        if not self.tts_engine:
            print(f"[TTS] {text}")
            return
        
        try:
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        except Exception as e:
            print(f"⚠️  Error in TTS: {e}")
            print(f"[TTS] {text}")
    
    def play_audio_file(self, filename: str):
        """
        Play audio file through speaker.
        
        Args:
            filename: Path to audio file
        """
        if not wave or not self.audio:
            return
        
        try:
            with wave.open(filename, 'rb') as wf:
                output_device = self.find_usb_speaker()
                
                stream = self.audio.open(
                    format=self.audio.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True,
                    output_device_index=output_device
                )
                
                data = wf.readframes(self.chunk_size)
                while data:
                    stream.write(data)
                    data = wf.readframes(self.chunk_size)
                
                stream.stop_stream()
                stream.close()
                
        except Exception as e:
            print(f"❌ Error playing audio: {e}")
    
    def is_available(self) -> bool:
        """Check if audio is available."""
        return AUDIO_AVAILABLE and self.audio is not None
    
    def cleanup(self):
        """Clean up audio resources."""
        if self.is_recording:
            self.stop_recording()
        
        if self.audio:
            try:
                self.audio.terminate()
            except:
                pass

