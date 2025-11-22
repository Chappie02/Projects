"""
Assistant module for LLM inference, Speech-to-Text, and Text-to-Speech
Handles llama.cpp model loading and audio processing
"""

from llama_cpp import Llama
import speech_recognition as sr
import pyttsx3
import threading
import config
import os


class Assistant:
    """Manages LLM, STT, and TTS functionality"""
    
    def __init__(self):
        """Initialize LLM, STT, and TTS systems"""
        self.llm = None
        self.recognizer = None
        self.tts_engine = None
        self._init_llm()
        self._init_stt()
        self._init_tts()
    
    def _init_llm(self):
        """Initialize llama.cpp LLM model"""
        try:
            if not os.path.exists(config.LLM_MODEL_PATH):
                raise FileNotFoundError(
                    f"LLM model not found at {config.LLM_MODEL_PATH}. "
                    "Please update config.py with the correct path."
                )
            
            print("Loading LLM model (this may take a moment)...")
            self.llm = Llama(
                model_path=config.LLM_MODEL_PATH,
                n_ctx=config.LLM_N_CTX,
                n_threads=config.LLM_N_THREADS,
                verbose=False
            )
            print("LLM model loaded successfully")
        except Exception as e:
            print(f"Error loading LLM model: {e}")
            raise
    
    def _init_stt(self):
        """Initialize Speech Recognition"""
        try:
            self.recognizer = sr.Recognizer()
            self.recognizer.energy_threshold = 4000
            self.recognizer.dynamic_energy_threshold = True
            print("Speech recognition initialized")
        except Exception as e:
            print(f"Error initializing speech recognition: {e}")
            raise
    
    def _init_tts(self):
        """Initialize Text-to-Speech engine"""
        try:
            self.tts_engine = pyttsx3.init()
            
            # Configure TTS settings
            voices = self.tts_engine.getProperty('voices')
            if voices:
                # Try to use a more natural voice if available
                for voice in voices:
                    if 'english' in voice.name.lower():
                        self.tts_engine.setProperty('voice', voice.id)
                        break
            
            # Set speech rate and volume
            self.tts_engine.setProperty('rate', 150)  # Words per minute
            self.tts_engine.setProperty('volume', 0.9)
            
            print("Text-to-speech initialized")
        except Exception as e:
            print(f"Error initializing TTS: {e}")
            raise
    
    def listen(self, timeout=5, phrase_time_limit=None):
        """
        Listen for and transcribe speech input
        
        Args:
            timeout: Maximum time to wait for speech (seconds)
            phrase_time_limit: Maximum length of phrase (seconds)
            
        Returns:
            str: Transcribed text, or None if no speech detected
        """
        if self.recognizer is None:
            raise RuntimeError("Speech recognition not initialized")
        
        try:
            with sr.Microphone() as source:
                # Adjust for ambient noise
                print("Adjusting for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                
                print("Listening...")
                audio = self.recognizer.listen(
                    source, 
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit
                )
            
            print("Processing speech...")
            # Use Google's speech recognition (works offline with pocketsphinx fallback)
            try:
                text = self.recognizer.recognize_google(audio)
                print(f"Recognized: {text}")
                return text
            except sr.UnknownValueError:
                print("Could not understand audio")
                return None
            except sr.RequestError as e:
                print(f"Speech recognition error: {e}")
                # Fallback to offline recognition
                try:
                    text = self.recognizer.recognize_sphinx(audio)
                    print(f"Recognized (offline): {text}")
                    return text
                except:
                    print("Offline recognition also failed")
                    return None
                    
        except sr.WaitTimeoutError:
            print("No speech detected within timeout")
            return None
        except Exception as e:
            print(f"Error during speech recognition: {e}")
            return None
    
    def generate_response(self, prompt, max_tokens=None):
        """
        Generate response using LLM
        
        Args:
            prompt: Input prompt text
            max_tokens: Maximum tokens to generate (defaults to config value)
            
        Returns:
            str: Generated response text
        """
        if self.llm is None:
            raise RuntimeError("LLM not initialized")
        
        try:
            max_tokens = max_tokens or config.LLM_MAX_TOKENS
            
            print("Generating response...")
            response = self.llm(
                prompt,
                max_tokens=max_tokens,
                temperature=config.LLM_TEMPERATURE,
                stop=["User:", "\n\n"],  # Stop sequences
                echo=False
            )
            
            # Extract text from response
            if 'choices' in response and len(response['choices']) > 0:
                text = response['choices'][0]['text'].strip()
                return text
            else:
                return "I'm sorry, I couldn't generate a response."
                
        except Exception as e:
            print(f"Error generating response: {e}")
            return f"I encountered an error: {str(e)}"
    
    def speak(self, text):
        """
        Convert text to speech and speak it
        
        Args:
            text: Text to speak
        """
        if self.tts_engine is None:
            print(f"TTS: {text}")
            return
        
        try:
            print(f"Speaking: {text[:50]}...")
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        except Exception as e:
            print(f"Error during TTS: {e}")
            print(f"Text was: {text}")
    
    def process_chat_query(self, user_query, memory_system=None):
        """
        Complete chat processing pipeline:
        1. Build RAG prompt (if memory system provided)
        2. Generate LLM response
        3. Store conversation (if memory system provided)
        4. Return response
        
        Args:
            user_query: User's text query
            memory_system: Optional MemorySystem instance for RAG
            
        Returns:
            str: Assistant's response
        """
        try:
            # Build prompt with RAG if memory system available
            if memory_system:
                prompt = memory_system.build_rag_prompt(user_query)
            else:
                prompt = f"User: {user_query}\nAssistant:"
            
            # Generate response
            response = self.generate_response(prompt)
            
            # Store conversation if memory system available
            if memory_system:
                memory_system.add_conversation(user_query, response)
            
            return response
        except Exception as e:
            print(f"Error processing chat query: {e}")
            return "I encountered an error processing your query."
    
    def process_vision_query(self, detection_text):
        """
        Process vision query by generating description from detections
        
        Args:
            detection_text: Text description of detected objects
            
        Returns:
            str: Generated description response
        """
        try:
            prompt = f"""You are a helpful AI assistant describing what you see in an image.

Object detection results: {detection_text}

Please provide a natural, conversational description of what is visible in the image. Be concise and friendly.

Description:"""
            
            response = self.generate_response(prompt, max_tokens=150)
            return response
        except Exception as e:
            print(f"Error processing vision query: {e}")
            return detection_text  # Fallback to raw detection text
    
    def cleanup(self):
        """Cleanup resources"""
        # LLM and TTS don't need explicit cleanup
        pass

