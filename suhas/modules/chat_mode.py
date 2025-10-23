"""
Chat Mode for the Raspberry Pi AI Assistant.
Integrates llama.cpp with RAG system for context-aware conversations.
"""

import os
import sys
import logging
import time
from typing import Optional, Dict, Any, List
from pathlib import Path
import threading
import queue

try:
    from llama_cpp import Llama
except ImportError:
    print("Warning: llama-cpp-python not installed. Chat mode will not work.")
    Llama = None

from .rag_engine import RAGEngine
from .utils import ConfigManager, SystemMonitor, ProcessManager


class ChatMode:
    """
    Chat mode implementation with llama.cpp and RAG integration.
    Provides natural language conversation with context-aware responses.
    """
    
    def __init__(self, config_manager: ConfigManager):
        """
        Initialize chat mode.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        self.system_monitor = SystemMonitor()
        self.process_manager = ProcessManager()
        
        # Initialize components
        self.llama_model = None
        self.rag_engine = None
        self.is_running = False
        self.conversation_history = []
        
        # Load configuration
        self.model_path = self.config_manager.get("llama_cpp.model_path")
        self.n_ctx = self.config_manager.get("llama_cpp.n_ctx", 2048)
        self.n_threads = self.config_manager.get("llama_cpp.n_threads", 4)
        self.temperature = self.config_manager.get("llama_cpp.temperature", 0.7)
        self.max_tokens = self.config_manager.get("llama_cpp.max_tokens", 512)
        
        self.logger.info("Chat mode initialized")
    
    def initialize(self) -> bool:
        """
        Initialize the chat mode components.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if llama-cpp-python is available
            if Llama is None:
                self.logger.error("llama-cpp-python not available")
                return False
            
            # Initialize RAG engine
            self.logger.info("Initializing RAG engine...")
            self.rag_engine = RAGEngine(
                knowledge_base_path="knowledge_base",
                embedding_model=self.config_manager.get("rag.embedding_model", "all-MiniLM-L6-v2"),
                chunk_size=self.config_manager.get("rag.chunk_size", 512),
                chunk_overlap=self.config_manager.get("rag.chunk_overlap", 50),
                top_k=self.config_manager.get("rag.top_k", 3)
            )
            
            # Check if model file exists
            if not Path(self.model_path).exists():
                self.logger.error(f"Model file not found: {self.model_path}")
                self.logger.info("Please download a compatible GGUF model and update the config")
                return False
            
            # Initialize llama.cpp model
            self.logger.info(f"Loading llama.cpp model: {self.model_path}")
            self.llama_model = Llama(
                model_path=self.model_path,
                n_ctx=self.n_ctx,
                n_threads=self.n_threads,
                verbose=False
            )
            
            self.logger.info("Chat mode components initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize chat mode: {e}")
            return False
    
    def start(self) -> bool:
        """
        Start the chat mode.
        
        Returns:
            True if successful, False otherwise
        """
        if self.is_running:
            self.logger.warning("Chat mode is already running")
            return True
        
        if not self.initialize():
            return False
        
        self.is_running = True
        self.conversation_history = []
        
        self.logger.info("Chat mode started")
        self._print_welcome_message()
        
        return True
    
    def stop(self) -> None:
        """Stop the chat mode and cleanup resources."""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # Cleanup model resources
        if self.llama_model:
            del self.llama_model
            self.llama_model = None
        
        # Clear conversation history
        self.conversation_history = []
        
        self.logger.info("Chat mode stopped")
    
    def _print_welcome_message(self) -> None:
        """Print welcome message and instructions."""
        print("\n" + "="*60)
        print("🤖 AI Assistant - Chat Mode")
        print("="*60)
        print("Type your questions or messages. The assistant will use")
        print("RAG (Retrieval-Augmented Generation) to provide context-aware responses.")
        print("\nCommands:")
        print("  /help     - Show this help message")
        print("  /stats    - Show system and knowledge base statistics")
        print("  /clear    - Clear conversation history")
        print("  /exit     - Exit chat mode")
        print("  /quit     - Exit chat mode")
        print("-"*60)
    
    def _check_system_health(self) -> bool:
        """Check system health before processing."""
        health = self.system_monitor.check_system_health()
        
        # Check memory usage
        if health['memory']['percent'] > self.config_manager.get("system.max_memory_usage", 80):
            self.logger.warning(f"High memory usage: {health['memory']['percent']:.1f}%")
            return False
        
        # Check temperature
        if health['temperature'] and health['temperature'] > self.config_manager.get("system.max_temperature", 70):
            self.logger.warning(f"High temperature: {health['temperature']:.1f}°C")
            return False
        
        return True
    
    def _format_prompt(self, user_input: str, context: str = "") -> str:
        """
        Format the prompt for the LLM with context and conversation history.
        
        Args:
            user_input: User's input message
            context: Retrieved context from RAG
            
        Returns:
            Formatted prompt string
        """
        # System prompt
        system_prompt = """You are a helpful AI assistant running on a Raspberry Pi. 
You have access to a knowledge base through RAG (Retrieval-Augmented Generation).
Use the provided context to give accurate and helpful responses.
If the context doesn't contain relevant information, say so and provide general help.
Keep responses concise but informative."""

        # Build conversation history
        history_text = ""
        if self.conversation_history:
            history_text = "\n\nPrevious conversation:\n"
            for msg in self.conversation_history[-5:]:  # Last 5 messages
                history_text += f"User: {msg['user']}\nAssistant: {msg['assistant']}\n"
        
        # Build context section
        context_section = ""
        if context.strip():
            context_section = f"\n\nRelevant context from knowledge base:\n{context}\n"
        
        # Final prompt
        prompt = f"""{system_prompt}{context_section}{history_text}

Current question: {user_input}

Assistant:"""
        
        return prompt
    
    def _generate_response(self, prompt: str) -> str:
        """
        Generate response using llama.cpp model.
        
        Args:
            prompt: Formatted prompt for the model
            
        Returns:
            Generated response text
        """
        try:
            # Generate response
            response = self.llama_model(
                prompt,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                top_p=0.9,
                repeat_penalty=1.1,
                stop=["User:", "Assistant:", "\n\n"],
                echo=False
            )
            
            # Extract the generated text
            if 'choices' in response and len(response['choices']) > 0:
                generated_text = response['choices'][0]['text'].strip()
                return generated_text
            else:
                return "I'm sorry, I couldn't generate a response."
                
        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            return "I'm sorry, there was an error generating my response."
    
    def process_input(self, user_input: str) -> str:
        """
        Process user input and generate response.
        
        Args:
            user_input: User's input message
            
        Returns:
            Assistant's response
        """
        if not self.is_running:
            return "Chat mode is not running."
        
        # Handle commands
        if user_input.startswith('/'):
            return self._handle_command(user_input)
        
        # Check system health
        if not self._check_system_health():
            return "System resources are running low. Please try again later."
        
        try:
            # Retrieve relevant context
            self.logger.info("Retrieving context from knowledge base...")
            context = self.rag_engine.retrieve_context(user_input)
            
            # Format prompt
            prompt = self._format_prompt(user_input, context)
            
            # Generate response
            self.logger.info("Generating response...")
            response = self._generate_response(prompt)
            
            # Store in conversation history
            self.conversation_history.append({
                'user': user_input,
                'assistant': response,
                'timestamp': time.time()
            })
            
            # Keep history manageable
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-15:]
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error processing input: {e}")
            return "I'm sorry, there was an error processing your request."
    
    def _handle_command(self, command: str) -> str:
        """
        Handle special commands.
        
        Args:
            command: Command string
            
        Returns:
            Command response
        """
        command = command.lower().strip()
        
        if command == '/help':
            return """Available commands:
/help     - Show this help message
/stats    - Show system and knowledge base statistics
/clear    - Clear conversation history
/exit     - Exit chat mode
/quit     - Exit chat mode"""
        
        elif command == '/stats':
            return self._get_stats()
        
        elif command == '/clear':
            self.conversation_history = []
            return "Conversation history cleared."
        
        elif command in ['/exit', '/quit']:
            return "EXIT_CHAT_MODE"
        
        else:
            return f"Unknown command: {command}. Type /help for available commands."
    
    def _get_stats(self) -> str:
        """Get system and knowledge base statistics."""
        try:
            # System stats
            health = self.system_monitor.check_system_health()
            system_stats = f"""System Statistics:
CPU Usage: {health['cpu_usage']:.1f}%
Memory Usage: {health['memory']['percent']:.1f}% ({health['memory']['used']:.1f}GB / {health['memory']['total']:.1f}GB)
Temperature: {health['temperature']:.1f}°C if available

"""
            
            # Knowledge base stats
            if self.rag_engine:
                kb_stats = self.rag_engine.get_collection_stats()
                kb_info = f"""Knowledge Base Statistics:
Total Documents: {kb_stats['total_documents']}
Unique Sources: {kb_stats['unique_sources']}
"""
            else:
                kb_info = "Knowledge Base: Not initialized\n"
            
            # Conversation stats
            conv_stats = f"""Conversation Statistics:
Messages in History: {len(self.conversation_history)}
"""
            
            return system_stats + kb_info + conv_stats
            
        except Exception as e:
            self.logger.error(f"Error getting stats: {e}")
            return "Error retrieving statistics."
    
    def run_interactive(self) -> None:
        """Run interactive chat loop."""
        if not self.start():
            print("Failed to start chat mode")
            return
        
        try:
            while self.is_running:
                try:
                    # Get user input
                    user_input = input("\nYou: ").strip()
                    
                    if not user_input:
                        continue
                    
                    # Process input
                    response = self.process_input(user_input)
                    
                    # Check for exit command
                    if response == "EXIT_CHAT_MODE":
                        break
                    
                    # Print response
                    print(f"\nAssistant: {response}")
                    
                except KeyboardInterrupt:
                    print("\n\nChat interrupted by user")
                    break
                except EOFError:
                    print("\n\nEnd of input")
                    break
                except Exception as e:
                    self.logger.error(f"Error in chat loop: {e}")
                    print(f"Error: {e}")
        
        finally:
            self.stop()
            print("\nChat mode ended.")
    
    def ingest_knowledge_base(self, directory_path: str = "knowledge_base") -> int:
        """
        Ingest documents from knowledge base directory.
        
        Args:
            directory_path: Path to knowledge base directory
            
        Returns:
            Number of documents ingested
        """
        if not self.rag_engine:
            self.logger.error("RAG engine not initialized")
            return 0
        
        return self.rag_engine.ingest_directory(directory_path)
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get conversation history."""
        return self.conversation_history.copy()
    
    def clear_conversation_history(self) -> None:
        """Clear conversation history."""
        self.conversation_history = []
        self.logger.info("Conversation history cleared")
