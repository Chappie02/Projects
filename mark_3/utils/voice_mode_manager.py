"""
Voice Mode Manager
Integrates voice input, wake word detection, ASR, and TTS for voice interactions.
"""

import os
import tempfile
import time
import threading
from typing import Optional, Callable, Dict
from utils.audio_utils import AudioManager
from utils.wake_word_detector import SimpleWakeWordDetector
from utils.voice_recognition import VoiceRecognizer
from utils.text_to_speech import TextToSpeech
from utils.oled_display import OLEDDisplay
import config


class VoiceModeManager:
    """Manages voice interactions including wake word, ASR, and TTS."""
    
    def __init__(self, oled_display: Optional[OLEDDisplay] = None):
        """
        Initialize voice mode manager.
        
        Args:
            oled_display: Optional OLED display for status updates
        """
        self.oled_display = oled_display
        
        # Initialize components
        self.audio_manager = AudioManager(
            sample_rate=config.AUDIO_CONFIG['sample_rate'],
            chunk_size=config.AUDIO_CONFIG['chunk_size'],
            channels=config.AUDIO_CONFIG['channels']
        )
        
        self.wake_word_detector = SimpleWakeWordDetector(
            wake_words=config.WAKE_WORD_CONFIG['wake_words']
        )
        
        self.voice_recognizer = VoiceRecognizer(
            model_path=config.VOICE_RECOGNITION_CONFIG.get('model_path'),
            use_vosk=(config.VOICE_RECOGNITION_CONFIG['engine'] == 'vosk')
        )
        
        self.tts = TextToSpeech(
            engine=config.TTS_CONFIG['engine'],
            voice=config.TTS_CONFIG.get('voice'),
            rate=config.TTS_CONFIG['rate'],
            volume=config.TTS_CONFIG['volume']
        )
        
        self.is_listening = False
        self.require_wake_word = config.WAKE_WORD_CONFIG['require_wake_word']
        self.voice_commands = config.VOICE_COMMANDS
        
        print("✅ Voice mode manager initialized")
    
    def listen_for_wake_word(self, timeout: Optional[float] = None) -> bool:
        """
        Listen for wake word.
        
        Args:
            timeout: Maximum time to listen (None for infinite)
            
        Returns:
            True if wake word detected
        """
        if not self.require_wake_word:
            return True
        
        if self.oled_display:
            self.oled_display.show_status("Waiting", "Say 'Hey Pi'")
        
        print("🎤 Listening for wake word...")
        
        start_time = time.time()
        recording_duration = 3.0  # Record 3 seconds at a time
        
        while True:
            if timeout and (time.time() - start_time) > timeout:
                return False
            
            # Record audio
            audio_data = self.audio_manager.record_audio(recording_duration)
            
            # Save to temp file and recognize
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = temp_file.name
                self.audio_manager.save_audio(audio_data, temp_path)
                
                # Recognize speech
                text = self.voice_recognizer.recognize_audio_file(temp_path)
                os.unlink(temp_path)
                
                if text:
                    print(f"Recognized: {text}")
                    
                    # Check for wake word
                    if self.wake_word_detector.is_wake_word(text):
                        print("✅ Wake word detected!")
                        if self.oled_display:
                            self.oled_display.show_wake_word_detected()
                        return True
    
    def listen_for_command(self, duration: float = 3.0) -> str:
        """
        Listen for voice command.
        
        Args:
            duration: Recording duration in seconds
            
        Returns:
            Transcribed command text
        """
        if self.oled_display:
            self.oled_display.show_listening()
        
        print(f"🎤 Listening for command ({duration}s)...")
        
        # Record audio
        audio_data = self.audio_manager.record_audio(duration)
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_path = temp_file.name
            self.audio_manager.save_audio(audio_data, temp_path)
            
            # Recognize speech
            text = self.voice_recognizer.recognize_audio_file(temp_path)
            os.unlink(temp_path)
            
            if text:
                print(f"✅ Recognized: {text}")
                return text
            else:
                print("⚠️  No speech recognized")
                return ""
    
    def process_voice_command(self, text: str) -> Optional[str]:
        """
        Process voice command and return action.
        
        Args:
            text: Transcribed text
            
        Returns:
            Action name or None
        """
        text_lower = text.lower().strip()
        
        # Extract command after wake word if present
        if self.wake_word_detector.is_wake_word(text):
            command = self.wake_word_detector.extract_command(text)
        else:
            command = text_lower
        
        # Check voice commands
        for cmd_type, phrases in self.voice_commands.items():
            for phrase in phrases:
                if phrase.lower() in command:
                    return cmd_type
        
        # Return original text if no command matched
        return text if command else None
    
    def speak(self, text: str, blocking: bool = True):
        """Speak text using TTS."""
        if config.TTS_CONFIG['enabled']:
            self.tts.speak(text, blocking=blocking)
    
    def speak_mode_change(self, mode: str):
        """Speak mode change notification."""
        if config.TTS_CONFIG.get('speak_mode_changes', True):
            self.tts.say_mode_change(mode)
    
    def speak_response(self, text: str):
        """Speak LLM response (if enabled)."""
        if config.TTS_CONFIG.get('speak_responses', False):
            self.speak(text, blocking=False)
    
    def cleanup(self):
        """Clean up voice mode manager resources."""
        try:
            self.audio_manager.cleanup()
            self.voice_recognizer.cleanup()
            self.tts.cleanup()
        except Exception as e:
            print(f"Error cleaning up voice mode manager: {e}")


def test_voice_mode():
    """Test voice mode functionality."""
    print("Testing Voice Mode Manager...")
    
    oled = OLEDDisplay() if config.OLED_CONFIG['enabled'] else None
    voice_manager = VoiceModeManager(oled_display=oled)
    
    try:
        # Test wake word detection
        print("\n1. Testing wake word detection...")
        if voice_manager.require_wake_word:
            print("Say 'Hey Pi' when prompted...")
            detected = voice_manager.listen_for_wake_word(timeout=10.0)
            if detected:
                print("✅ Wake word detected!")
            else:
                print("⚠️  Wake word not detected")
        else:
            print("Wake word detection disabled")
        
        # Test command recognition
        print("\n2. Testing command recognition...")
        command = voice_manager.listen_for_command(duration=3.0)
        if command:
            action = voice_manager.process_voice_command(command)
            print(f"Command: {command}")
            print(f"Action: {action}")
        
        # Test TTS
        print("\n3. Testing TTS...")
        voice_manager.speak("Hello, this is a test")
        
    except KeyboardInterrupt:
        print("\nTest interrupted")
    finally:
        voice_manager.cleanup()
        if oled:
            oled.cleanup()


if __name__ == "__main__":
    test_voice_mode()

