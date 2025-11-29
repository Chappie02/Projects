"""
Chat AI Module
Handles Speech-to-Text, RAG (ChromaDB), LLM (llama.cpp), and Text-to-Speech
"""

import logging
import os
import threading
import wave
import tempfile
from pathlib import Path
from typing import Optional, List, Tuple

logger = logging.getLogger(__name__)


class ChatAI:
    """Manages STT, RAG memory, LLM, and TTS for chat mode"""
    
    def __init__(self, 
                 memory_dir: str = "memory",
                 model_path: str = "models/llama-3-8b.gguf",
                 tts_model: str = "en_US-lessac-medium"):
        """
        Initialize ChatAI components
        
        Args:
            memory_dir: Directory for ChromaDB storage
            model_path: Path to LLM model file
            tts_model: TTS model name (for Piper)
        """
        self.memory_dir = Path(memory_dir)
        self.model_path = model_path
        self.tts_model = tts_model
        
        # Initialize components
        self.vector_db = None
        self.llm = None
        self.stt_engine = None
        self.tts_engine = None
        
        # Audio recording state
        self.is_recording = False
        self.audio_frames = []
        self.recording_thread: Optional[threading.Thread] = None
        
        try:
            self._setup_rag()
            self._setup_llm()
            self._setup_stt()
            self._setup_tts()
            logger.info("ChatAI initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing ChatAI: {e}")
            # Continue with partial initialization
    
    def _setup_rag(self):
        """Initialize ChromaDB for RAG memory"""
        try:
            import chromadb
            from chromadb.config import Settings
            
            # Create memory directory
            self.memory_dir.mkdir(parents=True, exist_ok=True)
            
            # Initialize ChromaDB client
            self.vector_db = chromadb.PersistentClient(
                path=str(self.memory_dir),
                settings=Settings(anonymized_telemetry=False)
            )
            
            # Get or create collection
            self.collection = self.vector_db.get_or_create_collection(
                name="chat_history",
                metadata={"hnsw:space": "cosine"}
            )
            
            logger.info("ChromaDB RAG initialized")
            
        except ImportError:
            logger.warning("ChromaDB not available, RAG disabled")
        except Exception as e:
            logger.error(f"Error setting up RAG: {e}")
    
    def _setup_llm(self):
        """Initialize llama.cpp LLM"""
        try:
            from llama_cpp import Llama
            
            if os.path.exists(self.model_path):
                self.llm = Llama(
                    model_path=self.model_path,
                    n_ctx=2048,  # Context window
                    n_threads=4,  # CPU threads
                    verbose=False
                )
                logger.info(f"LLM loaded from {self.model_path}")
            else:
                logger.warning(f"LLM model not found at {self.model_path}")
                logger.warning("Using placeholder LLM responses")
                
        except ImportError:
            logger.warning("llama-cpp-python not available, using placeholder")
        except Exception as e:
            logger.error(f"Error setting up LLM: {e}")
    
    def _setup_stt(self):
        """Initialize Speech-to-Text engine (Whisper or Vosk)"""
        try:
            # Try Whisper first
            try:
                import whisper
                self.stt_engine = whisper.load_model("base")
                self.stt_type = "whisper"
                logger.info("Whisper STT initialized")
                return
            except ImportError:
                pass
            
            # Try Vosk as fallback
            try:
                import vosk
                import json
                
                # Download model if needed (or use local path)
                model_path = "models/vosk-model-en-us-0.22"
                if os.path.exists(model_path):
                    self.vosk_model = vosk.Model(model_path)
                    self.vosk_rec = None  # Will be initialized per-recording
                    self.stt_type = "vosk"
                    logger.info("Vosk STT initialized")
                    return
            except ImportError:
                pass
            
            logger.warning("No STT engine available, using placeholder")
            self.stt_type = "placeholder"
            
        except Exception as e:
            logger.error(f"Error setting up STT: {e}")
            self.stt_type = "placeholder"
    
    def _setup_tts(self):
        """Initialize Text-to-Speech engine (Piper or Coqui)"""
        try:
            # Try Piper first
            try:
                import piper
                from piper import PiperVoice
                from piper.download import ensure_voice_exists, find_voice
                
                # Ensure voice model exists
                voice_path = ensure_voice_exists(self.tts_model, [])
                self.tts_engine = PiperVoice.load(voice_path)
                self.tts_type = "piper"
                logger.info(f"Piper TTS initialized with {self.tts_model}")
                return
            except ImportError:
                pass
            
            # Try Coqui TTS as fallback
            try:
                from TTS.api import TTS
                self.tts_engine = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC", gpu=False)
                self.tts_type = "coqui"
                logger.info("Coqui TTS initialized")
                return
            except ImportError:
                pass
            
            logger.warning("No TTS engine available, using placeholder")
            self.tts_type = "placeholder"
            
        except Exception as e:
            logger.error(f"Error setting up TTS: {e}")
            self.tts_type = "placeholder"
    
    def start_recording(self):
        """Start recording audio from USB microphone"""
        if self.is_recording:
            return
        
        try:
            import pyaudio
            
            self.is_recording = True
            self.audio_frames = []
            
            # Audio parameters
            CHUNK = 1024
            FORMAT = pyaudio.paInt16
            CHANNELS = 1
            RATE = 16000
            
            self.audio = pyaudio.PyAudio()
            self.stream = self.audio.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK
            )
            
            # Start recording thread
            self.recording_thread = threading.Thread(
                target=self._record_audio,
                args=(CHUNK,),
                daemon=True
            )
            self.recording_thread.start()
            
            logger.info("Recording started")
            
        except ImportError:
            logger.error("pyaudio not available for recording")
        except Exception as e:
            logger.error(f"Error starting recording: {e}")
            self.is_recording = False
    
    def _record_audio(self, chunk_size: int):
        """Internal method to continuously record audio"""
        try:
            while self.is_recording:
                data = self.stream.read(chunk_size, exception_on_overflow=False)
                self.audio_frames.append(data)
        except Exception as e:
            logger.error(f"Error in recording thread: {e}")
    
    def stop_recording(self) -> Optional[str]:
        """
        Stop recording and return path to audio file
        
        Returns:
            Path to saved audio file, or None if recording failed
        """
        if not self.is_recording:
            return None
        
        try:
            self.is_recording = False
            
            if hasattr(self, 'stream'):
                self.stream.stop_stream()
                self.stream.close()
            if hasattr(self, 'audio'):
                self.audio.terminate()
            
            if self.recording_thread:
                self.recording_thread.join(timeout=2)
            
            # Save audio to temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            temp_path = temp_file.name
            temp_file.close()
            
            # Write WAV file
            import wave
            wf = wave.open(temp_path, 'wb')
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(16000)
            wf.writeframes(b''.join(self.audio_frames))
            wf.close()
            
            logger.info(f"Recording saved to {temp_path}")
            return temp_path
            
        except Exception as e:
            logger.error(f"Error stopping recording: {e}")
            return None
    
    def speech_to_text(self, audio_path: str) -> str:
        """
        Convert speech audio to text
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Transcribed text
        """
        try:
            if self.stt_type == "whisper":
                result = self.stt_engine.transcribe(audio_path)
                text = result["text"].strip()
                logger.info(f"STT result: {text}")
                return text
            
            elif self.stt_type == "vosk":
                import json
                import wave
                import vosk
                
                wf = wave.open(audio_path, "rb")
                if wf.getnchannels() != 1 or wf.getcomptype() != "NONE":
                    logger.error("Audio file must be WAV format mono PCM")
                    return ""
                
                self.vosk_rec = vosk.KaldiRecognizer(self.vosk_model, wf.getframerate())
                self.vosk_rec.SetWords(True)
                
                text_parts = []
                while True:
                    data = wf.readframes(4000)
                    if len(data) == 0:
                        break
                    if self.vosk_rec.AcceptWaveform(data):
                        result = json.loads(self.vosk_rec.Result())
                        if 'text' in result:
                            text_parts.append(result['text'])
                
                # Get final result
                final_result = json.loads(self.vosk_rec.FinalResult())
                if 'text' in final_result:
                    text_parts.append(final_result['text'])
                
                text = ' '.join(text_parts).strip()
                logger.info(f"STT result: {text}")
                return text
            
            else:
                # Placeholder
                logger.warning("STT placeholder - returning sample text")
                return "What is the weather today?"
                
        except Exception as e:
            logger.error(f"Error in speech-to-text: {e}")
            return ""
    
    def _retrieve_context(self, query: str, top_k: int = 3) -> List[str]:
        """
        Retrieve relevant past conversations from RAG
        
        Args:
            query: User query
            top_k: Number of relevant messages to retrieve
            
        Returns:
            List of relevant past messages
        """
        if not self.collection:
            return []
        
        try:
            # Query ChromaDB for similar past conversations
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k
            )
            
            # Extract retrieved documents
            if results['documents'] and len(results['documents']) > 0:
                return results['documents'][0]
            return []
            
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return []
    
    def _store_conversation(self, query: str, response: str):
        """
        Store conversation in RAG memory
        
        Args:
            query: User query
            response: Assistant response
        """
        if not self.collection:
            return
        
        try:
            # Combine query and response for storage
            conversation_text = f"User: {query}\nAssistant: {response}"
            
            # Add to collection
            self.collection.add(
                documents=[conversation_text],
                ids=[f"conv_{len(self.collection.get()['ids'])}"]
            )
            
            logger.info("Conversation stored in RAG")
            
        except Exception as e:
            logger.error(f"Error storing conversation: {e}")
    
    def generate_response(self, user_query: str) -> str:
        """
        Generate LLM response with RAG context
        
        Args:
            user_query: User's text query
            
        Returns:
            Assistant's text response
        """
        try:
            # Retrieve relevant context
            context_messages = self._retrieve_context(user_query)
            
            # Build prompt with context
            if context_messages:
                context_text = "\n".join(context_messages[-2:])  # Last 2 relevant messages
                prompt = f"""Previous context:
{context_text}

User: {user_query}
Assistant:"""
            else:
                prompt = f"User: {user_query}\nAssistant:"
            
            # Generate response
            if self.llm:
                response = self.llm(
                    prompt,
                    max_tokens=256,
                    temperature=0.7,
                    stop=["User:", "\n\n"]
                )
                text_response = response['choices'][0]['text'].strip()
            else:
                # Placeholder response
                text_response = f"I understand you asked: {user_query}. This is a placeholder response. Please configure your LLM model."
            
            # Store conversation
            self._store_conversation(user_query, text_response)
            
            logger.info(f"Generated response: {text_response[:50]}...")
            return text_response
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "I'm sorry, I encountered an error processing your request."
    
    def text_to_speech(self, text: str) -> Optional[str]:
        """
        Convert text to speech audio file
        
        Args:
            text: Text to convert
            
        Returns:
            Path to generated audio file, or None if failed
        """
        try:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            temp_path = temp_file.name
            temp_file.close()
            
            if self.tts_type == "piper":
                # Generate audio with Piper
                with open(temp_path, 'wb') as f:
                    self.tts_engine.synthesize(text, f)
                logger.info(f"TTS audio saved to {temp_path}")
                return temp_path
            
            elif self.tts_type == "coqui":
                # Generate audio with Coqui
                self.tts_engine.tts_to_file(text=text, file_path=temp_path)
                logger.info(f"TTS audio saved to {temp_path}")
                return temp_path
            
            else:
                logger.warning("TTS placeholder - no audio generated")
                return None
                
        except Exception as e:
            logger.error(f"Error in text-to-speech: {e}")
            return None
    
    def play_audio(self, audio_path: str):
        """
        Play audio file through USB speaker
        
        Args:
            audio_path: Path to audio file
        """
        try:
            import pygame
            
            pygame.mixer.init()
            pygame.mixer.music.load(audio_path)
            pygame.mixer.music.play()
            
            # Wait for playback to finish
            while pygame.mixer.music.get_busy():
                import time
                time.sleep(0.1)
            
            pygame.mixer.quit()
            logger.info("Audio playback completed")
            
        except ImportError:
            logger.error("pygame not available for audio playback")
        except Exception as e:
            logger.error(f"Error playing audio: {e}")
    
    def cleanup(self):
        """Clean up resources"""
        try:
            if self.is_recording:
                self.stop_recording()
            logger.info("ChatAI cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up ChatAI: {e}")

