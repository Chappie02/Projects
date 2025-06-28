import threading
import time
import queue
import logging
from typing import Optional, Callable

try:
    import pyaudio
    import sounddevice as sd
    import numpy as np
    from vosk import Model, KaldiRecognizer
    import pyttsx3
except ImportError as e:
    print(f"Voice processing libraries not available: {e}")
    pyaudio = None
    sounddevice = None
    vosk = None
    pyttsx3 = None

from config import Config

class VoiceModule:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.audio_queue = queue.Queue()
        self.is_listening = False
        self.is_speaking = False
        
        # Initialize components
        self.recognizer = None
        self.tts_engine = None
        self.audio_stream = None
        
        self._initialize_voice_components()
    
    def _initialize_voice_components(self):
        """Initialize speech recognition and text-to-speech"""
        try:
            # Initialize Vosk for speech recognition
            if vosk:
                # Try to load Vosk model (you'll need to download this)
                model_path = "./models/vosk-model-small-en-us-0.15"
                if os.path.exists(model_path):
                    model = Model(model_path)
                    self.recognizer = KaldiRecognizer(model, 16000)
                    self.logger.info("Speech recognition initialized")
                else:
                    self.logger.warning("Vosk model not found. Speech recognition disabled.")
            
            # Initialize text-to-speech
            if pyttsx3:
                self.tts_engine = pyttsx3.init()
                self.tts_engine.setProperty('rate', Config.VOICE_RATE)
                self.tts_engine.setProperty('volume', Config.VOICE_VOLUME)
                
                # Try to set voice
                voices = self.tts_engine.getProperty('voices')
                for voice in voices:
                    if Config.VOICE_LANGUAGE in voice.id.lower():
                        self.tts_engine.setProperty('voice', voice.id)
                        break
                
                self.logger.info("Text-to-speech initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize voice components: {e}")
    
    def start_listening(self, callback: Callable[[str], None]):
        """Start listening for voice input"""
        if not self.recognizer:
            self.logger.warning("Speech recognition not available")
            return False
        
        self.is_listening = True
        self.audio_queue = queue.Queue()
        
        # Start audio capture thread
        self.audio_thread = threading.Thread(
            target=self._audio_capture_loop,
            args=(callback,),
            daemon=True
        )
        self.audio_thread.start()
        
        self.logger.info("Started listening for voice input")
        return True
    
    def stop_listening(self):
        """Stop listening for voice input"""
        self.is_listening = False
        if hasattr(self, 'audio_thread'):
            self.audio_thread.join(timeout=1)
        self.logger.info("Stopped listening for voice input")
    
    def _audio_capture_loop(self, callback: Callable[[str], None]):
        """Audio capture loop for speech recognition"""
        try:
            # Initialize PyAudio
            p = pyaudio.PyAudio()
            
            # Open audio stream
            stream = p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=8000
            )
            
            self.logger.info("Audio stream opened")
            
            while self.is_listening:
                try:
                    data = stream.read(4000, exception_on_overflow=False)
                    
                    if self.recognizer.AcceptWaveform(data):
                        result = self.recognizer.Result()
                        if result and '"text"' in result:
                            import json
                            text = json.loads(result)['text']
                            if text.strip():
                                self.logger.info(f"Recognized: {text}")
                                callback(text)
                
                except Exception as e:
                    self.logger.error(f"Error in audio capture: {e}")
                    break
            
            # Cleanup
            stream.stop_stream()
            stream.close()
            p.terminate()
            
        except Exception as e:
            self.logger.error(f"Failed to start audio capture: {e}")
    
    def speak(self, text: str):
        """Convert text to speech"""
        if not self.tts_engine:
            self.logger.warning("Text-to-speech not available")
            return False
        
        try:
            self.is_speaking = True
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
            self.is_speaking = False
            return True
        except Exception as e:
            self.logger.error(f"Error in text-to-speech: {e}")
            self.is_speaking = False
            return False
    
    def speak_async(self, text: str):
        """Convert text to speech asynchronously"""
        if not self.tts_engine:
            return False
        
        def speak_thread():
            self.speak(text)
        
        threading.Thread(target=speak_thread, daemon=True).start()
        return True
    
    def is_voice_available(self) -> bool:
        """Check if voice processing is available"""
        return self.recognizer is not None and self.tts_engine is not None

# Import os at the top level
import os 