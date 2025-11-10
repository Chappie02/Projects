"""
Wake Word Detection
Handles wake word detection ("Hey Pi") using a lightweight detection method.
"""

import numpy as np
import audioop
from typing import Optional, Callable
try:
    import pvporcupine
    PORCUPINE_AVAILABLE = True
except ImportError:
    PORCUPINE_AVAILABLE = False
    print("⚠️  Porcupine not available. Using simple keyword matching.")


class WakeWordDetector:
    """Detects wake word 'Hey Pi' from audio input."""
    
    def __init__(self, wake_word="hey pi", sensitivity=0.5, 
                 detection_callback: Optional[Callable] = None):
        """
        Initialize wake word detector.
        
        Args:
            wake_word: Wake word to detect (default: "hey pi")
            sensitivity: Detection sensitivity (0.0-1.0)
            detection_callback: Callback function called when wake word is detected
        """
        self.wake_word = wake_word.lower()
        self.sensitivity = sensitivity
        self.detection_callback = detection_callback
        self.is_listening = False
        
        # Initialize Porcupine if available
        self.porcupine = None
        if PORCUPINE_AVAILABLE:
            try:
                # Try to use Porcupine for better wake word detection
                # Note: Requires Porcupine access key and keyword model
                # For now, we'll use a simple keyword matching approach
                pass
            except Exception as e:
                print(f"⚠️  Porcupine initialization failed: {e}")
                print("   Using simple keyword matching instead")
        
        # Simple keyword matching (fallback)
        self.keywords = ["hey pi", "hey pie", "hi pi", "hi pie", "wake up"]
        
        print(f"✅ Wake word detector initialized (wake word: '{wake_word}')")
    
    def detect_in_audio(self, audio_data: bytes, sample_rate=16000) -> bool:
        """
        Detect wake word in audio data.
        
        Args:
            audio_data: Audio data as bytes
            sample_rate: Sample rate of audio
            
        Returns:
            True if wake word detected, False otherwise
        """
        # This is a placeholder - in production, use proper wake word detection
        # For now, we'll rely on ASR to detect the wake word in transcribed text
        return False
    
    def detect_in_text(self, text: str) -> bool:
        """
        Detect wake word in transcribed text.
        
        Args:
            text: Transcribed text
            
        Returns:
            True if wake word detected, False otherwise
        """
        text_lower = text.lower().strip()
        
        # Check if any keyword is in the text
        for keyword in self.keywords:
            if keyword in text_lower:
                return True
        
        return False
    
    def process_audio_stream(self, audio_chunk: bytes) -> bool:
        """
        Process audio chunk for wake word detection.
        
        Args:
            audio_chunk: Audio chunk as bytes
            
        Returns:
            True if wake word detected
        """
        # Placeholder for real-time audio processing
        # In production, use Porcupine or similar for continuous detection
        return False
    
    def set_callback(self, callback: Callable):
        """Set detection callback function."""
        self.detection_callback = callback
    
    def cleanup(self):
        """Clean up wake word detector resources."""
        try:
            if self.porcupine:
                self.porcupine.delete()
        except Exception as e:
            print(f"Error cleaning up wake word detector: {e}")


class SimpleWakeWordDetector:
    """Simple wake word detector using keyword matching in transcribed text."""
    
    def __init__(self, wake_words=None):
        """
        Initialize simple wake word detector.
        
        Args:
            wake_words: List of wake words to detect (default: ["hey pi"])
        """
        if wake_words is None:
            wake_words = ["hey pi", "hey pie", "hi pi", "wake up", "assistant"]
        
        self.wake_words = [w.lower() for w in wake_words]
        print(f"✅ Simple wake word detector initialized: {self.wake_words}")
    
    def is_wake_word(self, text: str) -> bool:
        """
        Check if text contains wake word.
        
        Args:
            text: Text to check
            
        Returns:
            True if wake word detected
        """
        text_lower = text.lower().strip()
        
        for wake_word in self.wake_words:
            if wake_word in text_lower:
                return True
        
        return False
    
    def extract_command(self, text: str) -> str:
        """
        Extract command after wake word.
        
        Args:
            text: Full text with wake word
            
        Returns:
            Command text without wake word
        """
        text_lower = text.lower().strip()
        
        for wake_word in self.wake_words:
            if wake_word in text_lower:
                # Remove wake word and return rest
                command = text_lower.replace(wake_word, "", 1).strip()
                return command
        
        return text_lower

