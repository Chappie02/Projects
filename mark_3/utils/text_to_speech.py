"""
Text-to-Speech Utilities
Handles text-to-speech conversion for voice feedback.
"""

import subprocess
import tempfile
import os
from typing import Optional
try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False
    print("⚠️  pyttsx3 not available. Using espeak as fallback.")


class TextToSpeech:
    """Handles text-to-speech conversion."""
    
    def __init__(self, engine="espeak", voice=None, rate=150, volume=1.0):
        """
        Initialize text-to-speech engine.
        
        Args:
            engine: TTS engine to use ("espeak", "pyttsx3", or "gtts")
            voice: Voice to use (engine-specific)
            rate: Speech rate (words per minute)
            volume: Volume (0.0-1.0)
        """
        self.engine = engine
        self.voice = voice
        self.rate = rate
        self.volume = volume
        self.tts_engine = None
        
        if engine == "pyttsx3" and PYTTSX3_AVAILABLE:
            self._initialize_pyttsx3()
        elif engine == "espeak":
            self._initialize_espeak()
        else:
            print(f"⚠️  Using espeak as default TTS engine")
            self._initialize_espeak()
    
    def _initialize_pyttsx3(self):
        """Initialize pyttsx3 engine."""
        try:
            self.tts_engine = pyttsx3.init()
            
            # Set properties
            self.tts_engine.setProperty('rate', self.rate)
            self.tts_engine.setProperty('volume', self.volume)
            
            # Set voice if specified
            if self.voice:
                voices = self.tts_engine.getProperty('voices')
                for v in voices:
                    if self.voice.lower() in v.name.lower():
                        self.tts_engine.setProperty('voice', v.id)
                        break
            
            print("✅ pyttsx3 TTS engine initialized")
            
        except Exception as e:
            print(f"⚠️  Error initializing pyttsx3: {e}")
            print("   Falling back to espeak")
            self._initialize_espeak()
    
    def _initialize_espeak(self):
        """Initialize espeak engine."""
        try:
            # Check if espeak is installed
            result = subprocess.run(['which', 'espeak'], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                print("⚠️  espeak not found. Install with: sudo apt-get install espeak")
                print("   TTS will be disabled")
                return
            
            self.engine = "espeak"
            print("✅ espeak TTS engine initialized")
            
        except Exception as e:
            print(f"⚠️  Error initializing espeak: {e}")
    
    def speak(self, text: str, blocking=True):
        """
        Speak text.
        
        Args:
            text: Text to speak
            blocking: Whether to wait for speech to complete
        """
        if not text or not text.strip():
            return
        
        try:
            if self.engine == "pyttsx3" and self.tts_engine:
                self.tts_engine.say(text)
                if blocking:
                    self.tts_engine.runAndWait()
            elif self.engine == "espeak":
                self._speak_espeak(text, blocking)
            else:
                print(f"⚠️  TTS not available. Text: {text}")
        
        except Exception as e:
            print(f"❌ Error speaking text: {e}")
    
    def _speak_espeak(self, text: str, blocking=True):
        """Speak using espeak."""
        try:
            cmd = ['espeak', '-s', str(self.rate), '-v', 'en']
            
            if self.voice:
                cmd.extend(['-v', self.voice])
            
            cmd.append(text)
            
            if blocking:
                subprocess.run(cmd, check=False, 
                             stdout=subprocess.DEVNULL, 
                             stderr=subprocess.DEVNULL)
            else:
                subprocess.Popen(cmd, 
                               stdout=subprocess.DEVNULL, 
                               stderr=subprocess.DEVNULL)
        
        except Exception as e:
            print(f"❌ Error with espeak: {e}")
    
    def speak_async(self, text: str):
        """Speak text asynchronously (non-blocking)."""
        self.speak(text, blocking=False)
    
    def say_mode_change(self, mode: str):
        """Speak mode change notification."""
        messages = {
            "chat": "Switched to Chat Mode",
            "object": "Switched to Object Detection Mode",
            "exit": "Exiting Assistant",
        }
        
        message = messages.get(mode.lower(), f"Switched to {mode}")
        self.speak(message)
    
    def say_listening(self):
        """Speak listening notification."""
        self.speak("Listening")
    
    def say_processing(self):
        """Speak processing notification."""
        self.speak("Processing")
    
    def say_error(self, error_msg: str = "An error occurred"):
        """Speak error message."""
        self.speak(f"Error: {error_msg}")
    
    def cleanup(self):
        """Clean up TTS resources."""
        try:
            if self.tts_engine:
                self.tts_engine.stop()
        except Exception as e:
            print(f"Error cleaning up TTS: {e}")


def test_tts():
    """Test TTS functionality."""
    print("Testing Text-to-Speech...")
    
    tts = TextToSpeech()
    
    test_phrases = [
        "Hello, this is a test",
        "Switched to Chat Mode",
        "Switched to Object Detection Mode",
        "Listening",
        "Processing",
    ]
    
    for phrase in test_phrases:
        print(f"Speaking: {phrase}")
        tts.speak(phrase)
        import time
        time.sleep(1)
    
    tts.cleanup()
    print("TTS test completed")


if __name__ == "__main__":
    test_tts()

