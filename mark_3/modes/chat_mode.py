"""
Chat Mode Implementation
Handles text-based conversation using local LLM via llama.cpp.
"""

import os
from typing import Optional
from llama_cpp import Llama


class ChatMode:
    """Handles chat mode functionality using local LLM."""
    
    def __init__(self, oled_display=None, voice_manager=None):
        """
        Initialize chat mode with LLM.
        
        Args:
            oled_display: Optional OLED display for status updates
            voice_manager: Optional voice mode manager for voice interactions
        """
        self.llm: Optional[Llama] = None
        self.oled_display = oled_display
        self.voice_manager = voice_manager
        self.system_prompt = """You are a helpful AI assistant running locally on a Raspberry Pi 5. 
You are designed to be helpful, harmless, and honest. You can assist with various tasks 
including answering questions, providing explanations, and helping with general inquiries. 
Keep your responses concise but informative."""
        
        self._initialize_llm()
    
    def _initialize_llm(self):
        """Initialize the local LLM using llama.cpp."""
        try:
            # Get project root for absolute paths
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(script_dir)
            
            # Look for model file in common locations (using absolute paths)
            model_paths = [
                os.path.join(project_root, "models", "llama-2-7b-chat.Q4_0.gguf"),
                os.path.join(project_root, "models", "gemma-2b-it.Q6_K.gguf"),
                os.path.join(project_root, "models", "llama-7b-q4_0.gguf"),
                os.path.join(project_root, "models", "llama-7b.gguf"),
                "./models/llama-2-7b-chat.Q4_0.gguf",
                "./models/gemma-2b-it.Q6_K.gguf",
                "./models/llama-7b-q4_0.gguf",
                "./models/llama-7b.gguf",
                "/home/pi/models/llama-7b-q4_0.gguf",
                "/home/pi/models/llama-7b.gguf",
            ]
            
            model_path = None
            for path in model_paths:
                abs_path = os.path.abspath(path) if not os.path.isabs(path) else path
                if os.path.exists(abs_path):
                    model_path = abs_path
                    break
            
            if not model_path:
                raise FileNotFoundError(
                    "LLM model file not found. Please download a GGUF model file and place it in the models directory."
                )
            
            print(f"Loading LLM model from: {model_path}")
            
            if self.oled_display:
                self.oled_display.show_status("Loading", "LLM Model...")
            
            # Initialize LLM with optimized settings for Raspberry Pi 5
            try:
                self.llm = Llama(
                    model_path=model_path,
                    n_ctx=2048,  # Context window
                    n_threads=4,  # Number of threads
                    n_gpu_layers=0,  # CPU only for Pi 5
                    verbose=False,
                    use_mmap=True,
                    use_mlock=False,
                )
            except Exception as e:
                print(f"⚠️  First attempt failed: {e}, trying minimal settings...")
                self.llm = Llama(
                    model_path=model_path,
                    n_ctx=512,
                    n_threads=2,
                    n_gpu_layers=0,
                    verbose=False,
                    use_mmap=True,
                    use_mlock=False,
                )
            
            print("✅ LLM initialized successfully!")
            
            if self.oled_display:
                self.oled_display.show_chat_mode()
            
        except Exception as e:
            print(f"❌ Error initializing LLM: {e}")
            raise
    
    def generate_response(self, user_message: str) -> str:
        """Generate a response to the user's message."""
        if not self.llm:
            return "❌ LLM not initialized. Please restart the application."
        
        try:
            if self.oled_display:
                self.oled_display.show_processing()
            
            # Create the conversation prompt
            prompt = f"System: {self.system_prompt}\n\nHuman: {user_message}\n\nAssistant:"
            
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
                
                if self.oled_display:
                    self.oled_display.show_chat_mode()
                
                return generated_text
            else:
                return "❌ Failed to generate response. Please try again."
                
        except Exception as e:
            error_msg = f"❌ Error generating response: {e}"
            if self.oled_display:
                self.oled_display.show_chat_mode()
            return error_msg
    
    def run(self):
        """Run the chat mode loop."""
        if not self.llm:
            print("❌ Chat mode not available. LLM not initialized.")
            return
        
        conversation_count = 0
        
        while True:
            try:
                user_input = input("\nYou: ").strip()
                
                if user_input.lower() == "exit":
                    print("Exiting chat mode...")
                    break
                
                if not user_input:
                    continue
                
                conversation_count += 1
                print(f"\nAssistant: ", end="", flush=True)
                
                # Generate and display response
                response = self.generate_response(user_input)
                print(response)
                
                # Add a small delay to prevent overwhelming the system
                import time
                time.sleep(0.1)
                
            except KeyboardInterrupt:
                print("\n\nExiting chat mode...")
                break
            except Exception as e:
                print(f"\n❌ Error in chat mode: {e}")
                print("Please try again or type 'exit' to return to main menu.")
        
        print(f"Chat session ended. Total conversations: {conversation_count}")
