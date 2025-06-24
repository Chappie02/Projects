import pyaudio
import speech_recognition as sr
import pyttsx3
import sounddevice as sd
import numpy as np
import logging
import threading
import time
import queue
from config import Config
import subprocess
import os

class AudioManager:
    def __init__(self):
        self.config = Config()
        self.logger = logging.getLogger(__name__)
        
        # Audio settings
        self.sample_rate = self.config.AUDIO_SAMPLE_RATE
        self.chunk_size = self.config.AUDIO_CHUNK_SIZE
        self.channels = self.config.AUDIO_CHANNELS
        
        # Initialize components
        self.recognizer = sr.Recognizer()
        self.engine = None
        self.audio_queue = queue.Queue()
        self.is_listening = False
        self.is_speaking = False
        
        # Initialize text-to-speech
        self._setup_tts()
        
        # Initialize Bluetooth audio
        self._setup_bluetooth()
    
    def _setup_tts(self):
        """Setup text-to-speech engine"""
        try:
            self.engine = pyttsx3.init()
            
            # Configure TTS settings
            voices = self.engine.getProperty('voices')
            if voices:
                # Try to find a good voice
                for voice in voices:
                    if "en" in voice.languages[0].lower():
                        self.engine.setProperty('voice', voice.id)
                        break
            
            # Set speech rate and volume
            self.engine.setProperty('rate', 150)  # Speed of speech
            self.engine.setProperty('volume', 0.9)  # Volume level
            
            self.logger.info("Text-to-speech engine initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize TTS: {e}")
    
    def _setup_bluetooth(self):
        """Setup Bluetooth audio output using system commands"""
        try:
            # Check if Bluetooth is available
            result = subprocess.run(['bluetoothctl', 'show'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logger.info("Bluetooth is available")
                # Set Bluetooth as default audio output
                self._set_bluetooth_audio()
            else:
                self.logger.warning("Bluetooth not available, using default audio")
                
        except Exception as e:
            self.logger.error(f"Error setting up Bluetooth: {e}")
    
    def _set_bluetooth_audio(self):
        """Set Bluetooth device as default audio output"""
        try:
            # Get list of Bluetooth devices
            result = subprocess.run(['bluetoothctl', 'devices'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if 'DEVICE' in line:
                        device_info = line.split()
                        if len(device_info) >= 2:
                            device_mac = device_info[1]
                            # Try to connect to the device
                            self._connect_bluetooth_device(device_mac)
                            break
        except Exception as e:
            self.logger.error(f"Error setting Bluetooth audio: {e}")
    
    def _connect_bluetooth_device(self, device_mac):
        """Connect to a Bluetooth device"""
        try:
            # Connect to device
            subprocess.run(['bluetoothctl', 'connect', device_mac], 
                         capture_output=True, text=True)
            
            # Set as default audio sink using pactl
            try:
                # Get list of audio sinks
                result = subprocess.run(['pactl', 'list', 'short', 'sinks'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        if 'bluez' in line.lower():
                            sink_id = line.split()[0]
                            subprocess.run(['pactl', 'set-default-sink', sink_id], 
                                         capture_output=True, text=True)
                            self.logger.info(f"Set Bluetooth sink as default: {sink_id}")
                            break
            except Exception as e:
                self.logger.warning(f"Could not set Bluetooth as default sink: {e}")
            
            self.logger.info(f"Connected to Bluetooth device: {device_mac}")
        except Exception as e:
            self.logger.error(f"Error connecting to Bluetooth device: {e}")
    
    def listen_for_speech(self, timeout=5):
        """Listen for speech input and return transcribed text"""
        try:
            with sr.Microphone(sample_rate=self.sample_rate) as source:
                self.logger.info("Listening for speech...")
                
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                # Listen for audio
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=10)
                
                # Transcribe audio
                text = self.recognizer.recognize_google(audio)
                self.logger.info(f"Transcribed: {text}")
                return text.lower()
                
        except sr.WaitTimeoutError:
            self.logger.info("No speech detected within timeout")
            return None
        except sr.UnknownValueError:
            self.logger.info("Could not understand audio")
            return None
        except sr.RequestError as e:
            self.logger.error(f"Speech recognition service error: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error in speech recognition: {e}")
            return None
    
    def speak_text(self, text):
        """Convert text to speech and play through audio output"""
        if not self.engine:
            self.logger.error("TTS engine not initialized")
            return False
        
        try:
            self.is_speaking = True
            self.logger.info(f"Speaking: {text}")
            
            # Use threading to avoid blocking
            def speak_thread():
                try:
                    self.engine.say(text)
                    self.engine.runAndWait()
                except Exception as e:
                    self.logger.error(f"Error in speech synthesis: {e}")
                finally:
                    self.is_speaking = False
            
            speech_thread = threading.Thread(target=speak_thread)
            speech_thread.daemon = True
            speech_thread.start()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error speaking text: {e}")
            self.is_speaking = False
            return False
    
    def start_continuous_listening(self, callback):
        """Start continuous listening for voice commands"""
        self.is_listening = True
        
        def listen_loop():
            while self.is_listening:
                try:
                    text = self.listen_for_speech(timeout=1)
                    if text:
                        # Process the speech in a separate thread
                        process_thread = threading.Thread(target=callback, args=(text,))
                        process_thread.daemon = True
                        process_thread.start()
                except Exception as e:
                    self.logger.error(f"Error in continuous listening: {e}")
                    time.sleep(0.1)
        
        listen_thread = threading.Thread(target=listen_loop)
        listen_thread.daemon = True
        listen_thread.start()
        
        self.logger.info("Started continuous listening")
    
    def stop_continuous_listening(self):
        """Stop continuous listening"""
        self.is_listening = False
        self.logger.info("Stopped continuous listening")
    
    def play_audio_file(self, file_path):
        """Play an audio file through the audio output"""
        try:
            # Use aplay for ALSA or paplay for PulseAudio
            if os.path.exists('/usr/bin/paplay'):
                subprocess.run(['paplay', file_path])
            elif os.path.exists('/usr/bin/aplay'):
                subprocess.run(['aplay', file_path])
            else:
                self.logger.error("No audio player found")
                return False
            
            self.logger.info(f"Played audio file: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error playing audio file: {e}")
            return False
    
    def get_audio_levels(self):
        """Get current audio input levels for visualization"""
        try:
            with sd.InputStream(samplerate=self.sample_rate, channels=1, 
                              blocksize=self.chunk_size) as stream:
                audio_data, _ = stream.read(self.chunk_size)
                rms = np.sqrt(np.mean(audio_data**2))
                return float(rms)
        except Exception as e:
            self.logger.error(f"Error getting audio levels: {e}")
            return 0.0
    
    def is_speaking_now(self):
        """Check if currently speaking"""
        return self.is_speaking
    
    def is_listening_now(self):
        """Check if currently listening"""
        return self.is_listening
    
    def cleanup(self):
        """Cleanup audio resources"""
        try:
            self.stop_continuous_listening()
            if self.engine:
                self.engine.stop()
            self.logger.info("Audio manager cleanup completed")
        except Exception as e:
            self.logger.error(f"Error during audio cleanup: {e}") 