"""
Voice Recognition Utilities
Handles speech-to-text using Vosk or Whisper.cpp for ASR.
"""

import json
import os
import wave
from typing import Optional, Callable
try:
    import vosk
    VOSK_AVAILABLE = True
except ImportError:
    VOSK_AVAILABLE = False
    print("⚠️  Vosk not available. Install with: pip install vosk")

try:
    from whisper_cpp_py import Whisper
    WHISPER_CPP_AVAILABLE = True
except ImportError:
    WHISPER_CPP_AVAILABLE = False
    print("⚠️  Whisper.cpp not available. Install separately if needed.")


class VoiceRecognizer:
    """Handles speech-to-text conversion using Vosk or Whisper.cpp."""
    
    def __init__(self, model_path: Optional[str] = None, use_vosk=True):
        """
        Initialize voice recognizer.
        
        Args:
            model_path: Path to ASR model (Vosk or Whisper)
            use_vosk: Use Vosk if True, Whisper.cpp if False
        """
        self.model_path = model_path
        self.use_vosk = use_vosk
        self.vosk_model = None
        self.vosk_recognizer = None
        self.whisper_model = None
        self.sample_rate = 16000
        
        if use_vosk and VOSK_AVAILABLE:
            self._initialize_vosk()
        elif not use_vosk and WHISPER_CPP_AVAILABLE:
            self._initialize_whisper()
        else:
            print("⚠️  No ASR engine available. Voice recognition disabled.")
    
    def _initialize_vosk(self):
        """Initialize Vosk model."""
        try:
            if not self.model_path:
                # Try to find Vosk model in common locations
                model_paths = [
                    "./models/vosk-model-small-en-us-0.15",
                    "./models/vosk-model-en-us-0.22",
                    "/usr/share/vosk/models/vosk-model-small-en-us-0.15",
                    "/usr/share/vosk/models/vosk-model-en-us-0.22",
                ]
                
                for path in model_paths:
                    if os.path.exists(path):
                        self.model_path = path
                        break
                
                if not self.model_path:
                    print("⚠️  Vosk model not found. Download from: https://alphacephei.com/vosk/models")
                    print("   Place model in ./models/ directory")
                    return
            
            if not os.path.exists(self.model_path):
                print(f"⚠️  Vosk model path does not exist: {self.model_path}")
                return
            
            self.vosk_model = vosk.Model(self.model_path)
            self.vosk_recognizer = vosk.KaldiRecognizer(self.vosk_model, self.sample_rate)
            self.vosk_recognizer.SetWords(True)
            
            print(f"✅ Vosk model loaded: {self.model_path}")
            
        except Exception as e:
            print(f"❌ Error initializing Vosk: {e}")
            self.vosk_model = None
            self.vosk_recognizer = None
    
    def _initialize_whisper(self):
        """Initialize Whisper.cpp model."""
        try:
            if not self.model_path:
                # Try to find Whisper model
                model_paths = [
                    "./models/ggml-base.bin",
                    "./models/ggml-small.bin",
                ]
                
                for path in model_paths:
                    if os.path.exists(path):
                        self.model_path = path
                        break
            
            if not self.model_path or not os.path.exists(self.model_path):
                print("⚠️  Whisper model not found")
                return
            
            self.whisper_model = Whisper(self.model_path)
            print(f"✅ Whisper model loaded: {self.model_path}")
            
        except Exception as e:
            print(f"❌ Error initializing Whisper: {e}")
            self.whisper_model = None
    
    def recognize_audio_file(self, audio_file: str) -> str:
        """
        Recognize speech from audio file.
        
        Args:
            audio_file: Path to audio file (WAV format)
            
        Returns:
            Transcribed text
        """
        if self.use_vosk and self.vosk_recognizer:
            return self._recognize_vosk_file(audio_file)
        elif not self.use_vosk and self.whisper_model:
            return self._recognize_whisper_file(audio_file)
        else:
            return ""
    
    def _recognize_vosk_file(self, audio_file: str) -> str:
        """Recognize using Vosk from file."""
        try:
            wf = wave.open(audio_file, "rb")
            
            if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
                print("⚠️  Audio file must be WAV format: mono, 16-bit, PCM")
                wf.close()
                return ""
            
            results = []
            
            while True:
                data = wf.readframes(4000)
                if len(data) == 0:
                    break
                
                if self.vosk_recognizer.AcceptWaveform(data):
                    result = json.loads(self.vosk_recognizer.Result())
                    if 'text' in result and result['text']:
                        results.append(result['text'])
            
            # Get final result
            final_result = json.loads(self.vosk_recognizer.FinalResult())
            if 'text' in final_result and final_result['text']:
                results.append(final_result['text'])
            
            wf.close()
            
            return " ".join(results).strip()
            
        except Exception as e:
            print(f"❌ Error recognizing with Vosk: {e}")
            return ""
    
    def _recognize_whisper_file(self, audio_file: str) -> str:
        """Recognize using Whisper.cpp from file."""
        try:
            result = self.whisper_model.transcribe(audio_file)
            return result.get('text', '').strip()
        except Exception as e:
            print(f"❌ Error recognizing with Whisper: {e}")
            return ""
    
    def recognize_audio_stream(self, audio_data: bytes) -> Optional[str]:
        """
        Recognize speech from audio stream data.
        
        Args:
            audio_data: Audio data as bytes
            
        Returns:
            Transcribed text or None if partial
        """
        if self.use_vosk and self.vosk_recognizer:
            return self._recognize_vosk_stream(audio_data)
        else:
            # For streaming, save to temp file and process
            return None
    
    def _recognize_vosk_stream(self, audio_data: bytes) -> Optional[str]:
        """Recognize using Vosk from stream."""
        try:
            if self.vosk_recognizer.AcceptWaveform(audio_data):
                result = json.loads(self.vosk_recognizer.Result())
                if 'text' in result and result['text']:
                    return result['text']
            
            # Check for partial results
            partial = json.loads(self.vosk_recognizer.PartialResult())
            if 'partial' in partial and partial['partial']:
                return None  # Still processing
            
            return None
            
        except Exception as e:
            print(f"❌ Error in Vosk stream recognition: {e}")
            return None
    
    def is_available(self) -> bool:
        """Check if voice recognition is available."""
        return (self.vosk_recognizer is not None) or (self.whisper_model is not None)
    
    def cleanup(self):
        """Clean up voice recognizer resources."""
        try:
            if self.vosk_recognizer:
                self.vosk_recognizer = None
            if self.vosk_model:
                self.vosk_model = None
            if self.whisper_model:
                self.whisper_model = None
        except Exception as e:
            print(f"Error cleaning up voice recognizer: {e}")


def download_vosk_model(model_name="vosk-model-small-en-us-0.15"):
    """Download Vosk model (helper function)."""
    import urllib.request
    import zipfile
    
    model_url = f"https://alphacephei.com/vosk/models/{model_name}.zip"
    model_dir = "./models"
    
    os.makedirs(model_dir, exist_ok=True)
    
    model_path = os.path.join(model_dir, model_name)
    zip_path = os.path.join(model_dir, f"{model_name}.zip")
    
    if os.path.exists(model_path):
        print(f"✅ Model already exists: {model_path}")
        return model_path
    
    print(f"Downloading Vosk model: {model_name}")
    print(f"URL: {model_url}")
    
    try:
        urllib.request.urlretrieve(model_url, zip_path)
        print("Extracting model...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(model_dir)
        os.remove(zip_path)
        print(f"✅ Model downloaded and extracted to: {model_path}")
        return model_path
    except Exception as e:
        print(f"❌ Error downloading model: {e}")
        return None

