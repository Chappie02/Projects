import os
import sys
from typing import Optional
import logging

try:
    from llama_cpp import Llama
except ImportError:
    print("llama-cpp-python not installed. Using fallback LLM.")
    Llama = None

from config import Config

class LLMModule:
    def __init__(self):
        self.model = None
        self.is_initialized = False
        self.logger = logging.getLogger(__name__)
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the LLM model"""
        try:
            if Llama and os.path.exists(Config.LLM_MODEL_PATH):
                self.model = Llama(
                    model_path=Config.LLM_MODEL_PATH,
                    n_ctx=Config.LLM_CONTEXT_LENGTH,
                    temperature=Config.LLM_TEMPERATURE,
                    verbose=False
                )
                self.is_initialized = True
                self.logger.info("LLM model initialized successfully")
            else:
                self.logger.warning("LLM model not found, using fallback responses")
                self.is_initialized = False
        except Exception as e:
            self.logger.error(f"Failed to initialize LLM: {e}")
            self.is_initialized = False
    
    def generate_response(self, user_input: str, context: str = "") -> str:
        """Generate a response using the LLM"""
        if not self.is_initialized or not self.model:
            return self._fallback_response(user_input)
        
        try:
            # Create a prompt with context
            prompt = self._create_prompt(user_input, context)
            
            # Generate response
            response = self.model(
                prompt,
                max_tokens=512,
                stop=["User:", "\n\n"],
                echo=False
            )
            
            return response['choices'][0]['text'].strip()
        
        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            return self._fallback_response(user_input)
    
    def _create_prompt(self, user_input: str, context: str = "") -> str:
        """Create a formatted prompt for the LLM"""
        system_prompt = """You are a helpful AI assistant running on a Raspberry Pi 5. 
You can help with general conversation, object detection, and home automation.
Be concise and helpful in your responses."""
        
        if context:
            prompt = f"{system_prompt}\n\nContext: {context}\n\nUser: {user_input}\nAssistant:"
        else:
            prompt = f"{system_prompt}\n\nUser: {user_input}\nAssistant:"
        
        return prompt
    
    def _fallback_response(self, user_input: str) -> str:
        """Fallback responses when LLM is not available"""
        user_input = user_input.lower()
        
        # Mode switching responses
        if any(word in user_input for word in ["object", "detect", "see", "camera"]):
            return "I can help you with object detection. I'll switch to camera mode to see what's in front of me."
        
        if any(word in user_input for word in ["home", "automation", "light", "fan"]):
            return "I can help you control your smart home devices. What would you like me to do?"
        
        # General conversation responses
        if "hello" in user_input or "hi" in user_input:
            return "Hello! I'm your AI assistant. I can help you with conversation, object detection, and home automation."
        
        if "how are you" in user_input:
            return "I'm doing well, thank you! How can I help you today?"
        
        if "what can you do" in user_input:
            return "I can help you with three main things: 1) General conversation, 2) Object detection using my camera, and 3) Home automation to control smart devices."
        
        # Default response
        return "I understand what you're saying. I'm here to help with conversation, object detection, or home automation tasks."
    
    def is_available(self) -> bool:
        """Check if the LLM is available and working"""
        return self.is_initialized and self.model is not None 