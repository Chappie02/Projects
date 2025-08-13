"""
LLM Interface for Raspberry Pi 5 AI Assistant
Handles communication with Ollama API
"""

import requests
import json
import time
import asyncio
import aiohttp
from typing import Optional, Dict, Any, List
import logging
from utils import handle_error, print_status, format_response_time

logger = logging.getLogger(__name__)

class LLMInterface:
    """Interface for communicating with Ollama API"""
    
    def __init__(self, model_name: str = "gemma2:2b", base_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url
        self.session = None
        self.conversation_history = []
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def check_ollama_status(self) -> bool:
        """Check if Ollama is running and accessible"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama not accessible: {e}")
            return False
    
    def get_available_models(self) -> List[str]:
        """Get list of available models from Ollama"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            if response.status_code == 200:
                models_data = response.json()
                return [model['name'] for model in models_data.get('models', [])]
            else:
                logger.error(f"Failed to get models: {response.status_code}")
                return []
        except Exception as e:
            handle_error(e, "get_available_models")
            return []
    
    def check_model_availability(self) -> bool:
        """Check if the specified model is available"""
        available_models = self.get_available_models()
        return self.model_name in available_models
    
    async def generate_response(self, prompt: str, stream: bool = False) -> str:
        """Generate response from LLM using Ollama API"""
        if not self.session:
            raise RuntimeError("Session not initialized. Use async context manager.")
        
        start_time = time.time()
        
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "num_predict": 500
            }
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"API request failed: {response.status} - {error_text}")
                
                if stream:
                    return await self._handle_stream_response(response)
                else:
                    result = await response.json()
                    response_time = time.time() - start_time
                    print_status(f"Response generated in {format_response_time(response_time)}", "success")
                    return result.get('response', '')
                    
        except asyncio.TimeoutError:
            raise Exception("Request timed out. Model may be too large for Pi 5.")
        except Exception as e:
            handle_error(e, "generate_response")
            raise
    
    async def _handle_stream_response(self, response) -> str:
        """Handle streaming response from Ollama"""
        full_response = ""
        async for line in response.content:
            if line:
                try:
                    data = json.loads(line.decode('utf-8'))
                    if 'response' in data:
                        chunk = data['response']
                        full_response += chunk
                        print(chunk, end='', flush=True)
                except json.JSONDecodeError:
                    continue
        
        print()  # New line after streaming
        return full_response
    
    def add_to_conversation(self, role: str, content: str) -> None:
        """Add message to conversation history"""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": time.time()
        })
        
        # Keep only last 10 messages to prevent memory issues
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]
    
    def get_conversation_context(self) -> str:
        """Get conversation context for LLM"""
        if not self.conversation_history:
            return ""
        
        context = "Previous conversation:\n"
        for msg in self.conversation_history[-5:]:  # Last 5 messages
            context += f"{msg['role'].title()}: {msg['content']}\n"
        return context
    
    async def chat_response(self, user_message: str) -> str:
        """Generate chat response with conversation context"""
        self.add_to_conversation("user", user_message)
        
        # Create prompt with conversation context
        context = self.get_conversation_context()
        if context:
            prompt = f"{context}\n\nUser: {user_message}\nAssistant:"
        else:
            prompt = f"User: {user_message}\nAssistant:"
        
        try:
            response = await self.generate_response(prompt)
            self.add_to_conversation("assistant", response)
            return response
        except Exception as e:
            error_msg = f"Failed to generate chat response: {str(e)}"
            logger.error(error_msg)
            return f"I apologize, but I encountered an error: {str(e)}"
    
    async def analyze_object(self, object_name: str) -> str:
        """Analyze detected object and provide summary"""
        from utils import create_llm_prompt
        
        prompt = create_llm_prompt(object_name)
        
        try:
            response = await self.generate_response(prompt)
            return response
        except Exception as e:
            error_msg = f"Failed to analyze object: {str(e)}"
            logger.error(error_msg)
            return f"Unable to analyze {object_name}: {str(e)}"
    
    def switch_model(self, new_model: str) -> bool:
        """Switch to a different model"""
        if self.check_model_availability():
            self.model_name = new_model
            self.conversation_history.clear()  # Clear history for new model
            print_status(f"Switched to model: {new_model}", "success")
            return True
        else:
            print_status(f"Model {new_model} not available", "error")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about current model"""
        try:
            response = requests.get(f"{self.base_url}/api/show", 
                                  json={"name": self.model_name}, 
                                  timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Failed to get model info: {response.status_code}"}
        except Exception as e:
            handle_error(e, "get_model_info")
            return {"error": str(e)}

# Synchronous wrapper for compatibility
class SyncLLMInterface:
    """Synchronous wrapper for LLM interface"""
    
    def __init__(self, model_name: str = "gemma2:2b", base_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url
        self.conversation_history = []
    
    def check_ollama_status(self) -> bool:
        """Check if Ollama is running and accessible"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama not accessible: {e}")
            return False
    
    def generate_response(self, prompt: str) -> str:
        """Generate response from LLM using Ollama API (synchronous)"""
        start_time = time.time()
        
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "num_predict": 500
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=60
            )
            
            if response.status_code != 200:
                raise Exception(f"API request failed: {response.status_code} - {response.text}")
            
            result = response.json()
            response_time = time.time() - start_time
            print_status(f"Response generated in {format_response_time(response_time)}", "success")
            return result.get('response', '')
            
        except requests.exceptions.Timeout:
            raise Exception("Request timed out. Model may be too large for Pi 5.")
        except Exception as e:
            handle_error(e, "generate_response")
            raise
    
    def chat_response(self, user_message: str) -> str:
        """Generate chat response with conversation context (synchronous)"""
        self.add_to_conversation("user", user_message)
        
        # Create prompt with conversation context
        context = self.get_conversation_context()
        if context:
            prompt = f"{context}\n\nUser: {user_message}\nAssistant:"
        else:
            prompt = f"User: {user_message}\nAssistant:"
        
        try:
            response = self.generate_response(prompt)
            self.add_to_conversation("assistant", response)
            return response
        except Exception as e:
            error_msg = f"Failed to generate chat response: {str(e)}"
            logger.error(error_msg)
            return f"I apologize, but I encountered an error: {str(e)}"
    
    def analyze_object(self, object_name: str) -> str:
        """Analyze detected object and provide summary (synchronous)"""
        from utils import create_llm_prompt
        
        prompt = create_llm_prompt(object_name)
        
        try:
            response = self.generate_response(prompt)
            return response
        except Exception as e:
            error_msg = f"Failed to analyze object: {str(e)}"
            logger.error(error_msg)
            return f"Unable to analyze {object_name}: {str(e)}"
    
    def add_to_conversation(self, role: str, content: str) -> None:
        """Add message to conversation history"""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": time.time()
        })
        
        # Keep only last 10 messages to prevent memory issues
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]
    
    def get_conversation_context(self) -> str:
        """Get conversation context for LLM"""
        if not self.conversation_history:
            return ""
        
        context = "Previous conversation:\n"
        for msg in self.conversation_history[-5:]:  # Last 5 messages
            context += f"{msg['role'].title()}: {msg['content']}\n"
        return context
