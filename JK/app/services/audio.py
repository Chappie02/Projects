import speech_recognition as sr
from gtts import gTTS
import os
import tempfile
import time
from app.core import config
from app.core.logger import setup_logger

logger = setup_logger(__name__)

class AudioManager:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = None
        try:
            self.microphone = sr.Microphone()
            # Adjust for ambient noise once at startup
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            logger.info("Audio Manager initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize microphone (PyAudio might be missing): {e}")
            self.microphone = None

    def listen(self):
        """Listens for audio and converts to text."""
        if not self.microphone:
            logger.warning("Microphone not available.")
            return None

        logger.info("Listening...")
        try:
            with self.microphone as source:
                # Short timeout to keep UI responsive
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
            
            logger.info("Processing audio...")
            text = self.recognizer.recognize_google(audio)
            logger.info(f"Heard: {text}")
            return text
        except sr.WaitTimeoutError:
            logger.debug("Listen timeout.")
            return None
        except sr.UnknownValueError:
            logger.debug("Unknown value.")
            return None
        except Exception as e:
            logger.error(f"Audio Error: {e}")
            return None

    def speak(self, text):
        """Converts text to speech and plays it."""
        if not text:
            return
        
        logger.info(f"Speaking: {text}")
        try:
            # Using gTTS for simplicity
            tts = gTTS(text=text, lang='en')
            
            # Save to a temp file
            fd, path = tempfile.mkstemp(suffix=".mp3")
            os.close(fd)
            
            tts.save(path)
            
            # Play the audio (using mpg123 or similar)
            os.system(f"mpg123 -q {path}")
            
            # Cleanup
            os.remove(path)
        except Exception as e:
            logger.error(f"TTS Error: {e}")
