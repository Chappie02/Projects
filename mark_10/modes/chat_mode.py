"""
Chat Mode Implementation
Handles text-based conversation using local LLM via llama.cpp with RAG support.
"""

import os
import time
from typing import Optional, List, Dict
from llama_cpp import Llama
from utils.rag_utils import RAGManager
from utils.display_utils import DisplayManager
from utils.audio_utils import AudioManager


class ChatMode:
    """Handles chat mode functionality using local LLM."""
    
    def __init__(self, display_manager: Optional[DisplayManager] = None,
                 audio_manager: Optional[AudioManager] = None):
        """Initialize chat mode with LLM and RAG."""
        self.llm: Optional[Llama] = None
        self.rag_manager: Optional[RAGManager] = None
        self.display_manager = display_manager
        self.audio_manager = audio_manager
        self.conversation_history: List[Dict[str, str]] = []
        self.system_prompt = """You are a helpful AI assistant running locally on a Raspberry Pi 5. 
You are designed to be helpful, harmless, and honest. You can assist with various tasks 
including answering questions, providing explanations, and helping with general inquiries. 
Keep your responses concise but informative."""
        
        self._initialize_rag()
        self._initialize_llm()
    
    def _initialize_rag(self):
        """Initialize RAG manager for conversation memory."""
        try:
            self.rag_manager = RAGManager(collection_name="ai_assistant_chat_history")
            print("✅ RAG system initialized for chat history")
        except Exception as e:
            print(f"⚠️  RAG initialization failed: {e}")
            self.rag_manager = None
    
    def _initialize_llm(self):
        """Initialize the local LLM using llama.cpp."""
        try:
            # Look for model file in common locations
            model_paths = [
                "./models/gemma-3-4b-it-IQ4_XS.gguf",
                "./models/gemma-2b-it.Q6_K.gguf",
                 #"gemma-2b-it.Q6_K.gguf",
                "./models/llama-2-7b-chat.Q4_0.gguf",
                "./models/llama-7b-q4_0.gguf",
                "./models/llama-7b.gguf", 
                "/home/pi/models/llama-7b-q4_0.gguf",
                "/home/pi/models/llama-7b.gguf",
                "llama-7b-q4_0.gguf"
            ]
            
            model_path = None
            for path in model_paths:
                if os.path.exists(path):
                    model_path = path
                    break
            
            if not model_path:
                raise FileNotFoundError(
                    "LLM model file not found. Please download a GGUF model file and place it in the models directory."
                )
            
            print(f"Loading LLM model from: {model_path}")
            
            # Initialize LLM with optimized settings for Raspberry Pi 5
            self.llm = Llama(
                model_path=model_path,
                n_ctx=2048,  # Context window
                n_threads=4,  # Number of threads
                n_gpu_layers=0,  # CPU only for Pi 5
                verbose=False
            )
            
            print("✅ LLM initialized successfully!")
            
        except Exception as e:
            print(f"❌ Error initializing LLM: {e}")
            raise
    
    def generate_response(self, user_message: str) -> str:
        """Generate a response to the user's message with RAG context."""
        if not self.llm:
            return "❌ LLM not initialized. Please restart the application."
        
        try:
            # Get relevant context from RAG
            rag_context = ""
            if self.rag_manager and self.rag_manager.is_available():
                rag_context = self.rag_manager.get_context_for_query(user_message, max_context_length=500)
            
            # Build conversation history context
            history_context = ""
            if self.conversation_history:
                # Include last few exchanges for context
                recent_history = self.conversation_history[-4:]  # Last 4 exchanges
                history_parts = []
                for exchange in recent_history:
                    history_parts.append(f"Human: {exchange.get('user', '')}")
                    history_parts.append(f"Assistant: {exchange.get('assistant', '')}")
                history_context = "\n".join(history_parts) + "\n\n"
            
            # Create the conversation prompt with RAG context
            prompt_parts = [f"System: {self.system_prompt}"]
            if rag_context:
                prompt_parts.append(rag_context)
            if history_context:
                prompt_parts.append("Previous conversation:")
                prompt_parts.append(history_context)
            prompt_parts.append(f"Human: {user_message}")
            prompt_parts.append("Assistant:")
            
            prompt = "\n\n".join(prompt_parts)
            
            # Generate response
            response = self.llm(
                prompt,
                max_tokens=256,
                temperature=0.7,
                top_p=0.9,
                stop=["Human:", "System:"],
                echo=False
            )
            
            # Extract the generated text
            if response and 'choices' in response and len(response['choices']) > 0:
                generated_text = response['choices'][0]['text'].strip()
                
                # Store conversation in history
                self.conversation_history.append({
                    'user': user_message,
                    'assistant': generated_text
                })
                
                # Store in RAG for future retrieval
                if self.rag_manager and self.rag_manager.is_available():
                    # Store user message and assistant response together
                    conversation_text = f"User: {user_message}\nAssistant: {generated_text}"
                    self.rag_manager.add_document(
                        conversation_text,
                        metadata={"type": "conversation", "user_message": user_message[:50]}
                    )
                
                # Limit conversation history size
                if len(self.conversation_history) > 20:
                    self.conversation_history = self.conversation_history[-20:]
                
                return generated_text
            else:
                return "❌ Failed to generate response. Please try again."
                
        except Exception as e:
            return f"❌ Error generating response: {e}"
    
    def run(self):
        """Run one chat cycle with audio input/output."""
        if not self.llm:
            error_msg = "LLM not init"
            print("❌ Chat mode not available. LLM not initialized.")
            if self.display_manager:
                self.display_manager.show_text(error_msg, clear_first=True)
            return
        
        # Show chat mode on display
        if self.display_manager:
            self.display_manager.show_chat_mode()
        
        try:
            # Show listening on display
            if self.display_manager:
                self.display_manager.show_listening()
            
            # Record audio from microphone
            if self.audio_manager and self.audio_manager.is_available():
                print("Listening... (speak now, will record for 5 seconds)")
                audio_data = self.audio_manager.record_audio(duration=5.0)
                
                if audio_data:
                    # For now, we'll use a simple approach
                    # In a full implementation, you'd use speech recognition here
                    # For now, we'll simulate by showing processing
                    if self.display_manager:
                        self.display_manager.show_processing()
                    
                    # TODO: Add speech-to-text conversion here
                    # For now, we'll use a placeholder
                    user_input = "What can you help me with?"  # Placeholder
                    print(f"You said: {user_input}")
                else:
                    print("No audio captured. Please try again.")
                    if self.display_manager:
                        self.display_manager.show_text("No audio", clear_first=True)
                    return
            else:
                # Fallback to text input if audio not available
                user_input = input("\nYou: ").strip()
                if not user_input:
                    return
            
            if user_input.lower() == "exit":
                print("Exiting chat mode...")
                return
            
            # Show processing on display
            if self.display_manager:
                self.display_manager.show_processing()
            
            print(f"\nAssistant: ", end="", flush=True)
            
            # Generate response
            response = self.generate_response(user_input)
            print(response)
            
            # Display response on OLED (truncated if needed)
            if self.display_manager:
                # Show first line of response
                response_lines = response.split('\n')
                first_line = response_lines[0][:16] if response_lines else response[:16]
                self.display_manager.show_text(f"AI: {first_line}", clear_first=True)
            
            # Speak the response
            if self.audio_manager:
                self.audio_manager.speak(response)
            
        except Exception as e:
            print(f"\n❌ Error in chat mode: {e}")
            error_msg = f"Error: {str(e)[:20]}"
            if self.display_manager:
                self.display_manager.show_text(error_msg, clear_first=True)
            if self.audio_manager:
                self.audio_manager.speak("Error occurred. Please try again.")
