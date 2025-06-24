import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import logging
from config import Config
import re

class LLMCore:
    def __init__(self):
        self.config = Config()
        self.logger = logging.getLogger(__name__)
        self.current_mode = "main_chat"
        self.conversation_history = []
        
        # Initialize the model
        self.logger.info("Loading LLM model...")
        self.tokenizer = AutoTokenizer.from_pretrained(self.config.LLM_MODEL_NAME)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.config.LLM_MODEL_NAME,
            torch_dtype=torch.float16,
            device_map="auto" if torch.cuda.is_available() else "cpu"
        )
        
        # Add padding token if not present
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
            
        self.logger.info("LLM model loaded successfully")
    
    def detect_mode(self, user_input):
        """Detect which mode the user wants to switch to based on keywords"""
        user_input_lower = user_input.lower()
        
        for mode, keywords in self.config.MODE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in user_input_lower:
                    return mode
        
        return self.current_mode
    
    def switch_mode(self, new_mode):
        """Switch to a new mode"""
        if new_mode != self.current_mode:
            self.logger.info(f"Switching from {self.current_mode} to {new_mode}")
            self.current_mode = new_mode
            return f"Switched to {new_mode.replace('_', ' ')} mode."
        return None
    
    def generate_response(self, user_input, context=None):
        """Generate response based on current mode and user input"""
        # Detect if user wants to switch modes
        detected_mode = self.detect_mode(user_input)
        mode_switch_message = self.switch_mode(detected_mode)
        
        # Prepare response based on mode
        if self.current_mode == "main_chat":
            response = self._generate_chat_response(user_input)
        elif self.current_mode == "object_detection":
            response = self._generate_object_detection_response(user_input, context)
        elif self.current_mode == "home_automation":
            response = self._generate_home_automation_response(user_input, context)
        else:
            response = "I'm not sure how to handle that request."
        
        # Add mode switch message if applicable
        if mode_switch_message:
            response = f"{mode_switch_message} {response}"
        
        # Update conversation history
        self.conversation_history.append({
            "user": user_input,
            "assistant": response,
            "mode": self.current_mode
        })
        
        return response
    
    def _generate_chat_response(self, user_input):
        """Generate a conversational response"""
        # Prepare input for the model
        inputs = self.tokenizer.encode(
            user_input + self.tokenizer.eos_token,
            return_tensors="pt",
            truncation=True,
            max_length=self.config.MAX_LENGTH
        )
        
        # Generate response
        with torch.no_grad():
            outputs = self.model.generate(
                inputs,
                max_length=inputs.shape[1] + 100,
                temperature=self.config.TEMPERATURE,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )
        
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        # Remove the input part from the response
        response = response[len(user_input):].strip()
        
        return response if response else "I understand. How can I help you further?"
    
    def _generate_object_detection_response(self, user_input, context=None):
        """Generate response for object detection mode"""
        if context and "objects" in context:
            objects = context["objects"]
            if objects:
                object_list = ", ".join([f"{obj['name']} ({obj['confidence']:.2f})" for obj in objects])
                return f"I can see: {object_list}. What would you like to know about these objects?"
            else:
                return "I don't see any objects in the current view. Would you like me to scan again?"
        else:
            return "I'm in object detection mode. I'll analyze what I can see through the camera."
    
    def _generate_home_automation_response(self, user_input, context=None):
        """Generate response for home automation mode"""
        automation_keywords = {
            "light": "I can control the lights. Say 'turn on lights' or 'turn off lights'.",
            "fan": "I can control the fan. Say 'turn on fan' or 'turn off fan'.",
            "door": "I can control the door lock. Say 'lock door' or 'unlock door'.",
            "temperature": "I can check the temperature sensors.",
            "status": "I can check the status of all connected devices."
        }
        
        user_input_lower = user_input.lower()
        for keyword, response in automation_keywords.items():
            if keyword in user_input_lower:
                return response
        
        return "I'm in home automation mode. I can control lights, fans, door locks, and check device status. What would you like me to do?"
    
    def get_current_mode(self):
        """Get the current active mode"""
        return self.current_mode
    
    def get_conversation_history(self):
        """Get the conversation history"""
        return self.conversation_history 