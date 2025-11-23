"""
Voice Command Recognition Utility
Handles wake-up word detection and voice command recognition for mode switching.
"""

import os
import wave
import threading
from typing import Optional, Callable, List
import subprocess

try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False
    print("Warning: speech_recognition not available. Install with: pip install SpeechRecognition")

from utils.audio_utils import BluetoothAudioInput


class VoiceCommandRecognizer:
    """Recognizes voice commands from Bluetooth microphone input."""
    
    def __init__(self,
                 wake_words: List[str] = None,
                 language='en-US',
                 energy_threshold=300):
        """Initialize voice command recognizer."""
        self.wake_words = wake_words or ["hey assistant", "wake up", "assistant"]
        self.language = language
        self.energy_threshold = energy_threshold
        
        self.recognizer = None
        self.audio_input = None
        self.is_listening = False
        self.listening_thread: Optional[threading.Thread] = None
        
        self.wake_callback: Optional[Callable] = None
        self.command_callback: Optional[Callable] = None
        
        self.commands = {
            "chat mode": "chat_mode",
            "object mode": "object_mode",
            "switch mode": "switch_mode",
            "change mode": "switch_mode",
            "exit": "exit",
            "wake up": "wake_up"
        }
        
        if SPEECH_RECOGNITION_AVAILABLE:
            self._initialize_recognizer()
            self._initialize_audio()
    
    def _initialize_recognizer(self):
        """Initialize speech recognizer."""
        try:
            self.recognizer = sr.Recognizer()
            self.recognizer.energy_threshold = self.energy_threshold
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.pause_threshold = 0.8
            
            print("✅ Voice recognizer initialized")
            
        except Exception as e:
            print(f"❌ Error initializing recognizer: {e}")
            self.recognizer = None
    
    def _initialize_audio(self):
        """Initialize Bluetooth audio input."""
        try:
            self.audio_input = BluetoothAudioInput(
                sample_rate=16000,
                chunk_size=1024
            )
            print("✅ Audio input initialized")
            
        except Exception as e:
            print(f"❌ Error initializing audio input: {e}")
            self.audio_input = None
    
    def set_wake_callback(self, callback: Callable):
        """Set callback for wake word detection."""
        self.wake_callback = callback
    
    def set_command_callback(self, callback: Callable):
        """Set callback for command recognition."""
        self.command_callback = callback
    
    def start_listening(self):
        """Start continuous listening for wake words and commands."""
        if self.is_listening:
            print("⚠️  Already listening")
            return
        
        if not self.recognizer or not self.audio_input:
            print("❌ Recognizer or audio input not initialized")
            return
        
        self.is_listening = True
        self.listening_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.listening_thread.start()
        print("🎤 Started listening for voice commands...")
    
    def stop_listening(self):
        """Stop listening for voice commands."""
        self.is_listening = False
        if self.listening_thread:
            self.listening_thread.join(timeout=1.0)
        print("🛑 Stopped listening for voice commands")
    
    def _listen_loop(self):
        """Main listening loop for wake words and commands."""
        import time
        
        if not self.recognizer:
            return
        
        try:
            # Use microphone from Bluetooth audio
            with sr.Microphone() as source:
                # Adjust for ambient noise
                print("Adjusting for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                print("✅ Ready to listen")
                
                while self.is_listening:
                    try:
                        # Listen for audio with timeout
                        print("Listening...")
                        audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=5)
                        
                        # Recognize speech
                        try:
                            text = self.recognizer.recognize_google(audio, language=self.language)
                            text = text.lower()
                            
                            print(f"Recognized: {text}")
                            
                            # Check for wake words
                            if any(wake_word in text for wake_word in self.wake_words):
                                print(f"🔥 Wake word detected: {text}")
                                if self.wake_callback:
                                    self.wake_callback()
                                continue
                            
                            # Check for commands
                            command = self._parse_command(text)
                            if command:
                                print(f"📢 Command detected: {command}")
                                if self.command_callback:
                                    self.command_callback(command, text)
                            
                        except sr.UnknownValueError:
                            # Could not understand audio
                            pass
                        except sr.RequestError as e:
                            print(f"❌ Speech recognition error: {e}")
                        
                    except sr.WaitTimeoutError:
                        # Timeout - continue listening
                        pass
                    except KeyboardInterrupt:
                        break
                        
        except Exception as e:
            print(f"❌ Error in listening loop: {e}")
        finally:
            self.is_listening = False
    
    def _parse_command(self, text: str) -> Optional[str]:
        """Parse recognized text to find commands."""
        text_lower = text.lower()
        
        for command_phrase, command_id in self.commands.items():
            if command_phrase in text_lower:
                return command_id
        
        return None
    
    def recognize_from_file(self, audio_file: str) -> Optional[str]:
        """Recognize speech from audio file."""
        if not self.recognizer:
            return None
        
        try:
            with sr.AudioFile(audio_file) as source:
                audio = self.recognizer.record(source)
            
            text = self.recognizer.recognize_google(audio, language=self.language)
            return text.lower()
            
        except sr.UnknownValueError:
            return None
        except sr.RequestError as e:
            print(f"❌ Speech recognition error: {e}")
            return None
        except Exception as e:
            print(f"❌ Error recognizing from file: {e}")
            return None
    
    def add_command(self, phrase: str, command_id: str):
        """Add a custom command phrase."""
        self.commands[phrase.lower()] = command_id
    
    def cleanup(self):
        """Clean up resources."""
        self.stop_listening()
        if self.audio_input:
            self.audio_input.cleanup()


class WakeWordDetector:
    """Simple wake word detector using keyword matching."""
    
    def __init__(self, wake_words: List[str] = None):
        """Initialize wake word detector."""
        self.wake_words = wake_words or ["hey assistant", "wake up", "assistant", "hello assistant"]
        self.wake_callback: Optional[Callable] = None
        self.is_awake = False
    
    def set_wake_callback(self, callback: Callable):
        """Set callback for wake word detection."""
        self.wake_callback = callback
    
    def check_wake_word(self, text: str) -> bool:
        """Check if text contains wake word."""
        text_lower = text.lower()
        
        for wake_word in self.wake_words:
            if wake_word in text_lower:
                self.is_awake = True
                if self.wake_callback:
                    self.wake_callback()
                return True
        
        return False
    
    def wake_up(self):
        """Manually wake up the assistant."""
        self.is_awake = True
        if self.wake_callback:
            self.wake_callback()
    
    def sleep(self):
        """Put assistant to sleep."""
        self.is_awake = False


if __name__ == "__main__":
    # Test voice recognition
    if not SPEECH_RECOGNITION_AVAILABLE:
        print("❌ Speech recognition not available. Install dependencies first.")
        exit(1)
    
    print("Testing voice command recognition...")
    print("Say a wake word or command...")
    
    recognizer = VoiceCommandRecognizer()
    
    def on_wake():
        print("🔥 WAKE WORD DETECTED!")
    
    def on_command(command, text):
        print(f"📢 Command received: {command} (from: {text})")
    
    recognizer.set_wake_callback(on_wake)
    recognizer.set_command_callback(on_command)
    
    recognizer.start_listening()
    
    try:
        import time
        time.sleep(30)  # Listen for 30 seconds
    except KeyboardInterrupt:
        pass
    finally:
        recognizer.stop_listening()
        recognizer.cleanup()

