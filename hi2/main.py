#!/usr/bin/env python3
"""
RPi5_MultiModal_AI_Assistant
A comprehensive multi-modal AI assistant for Raspberry Pi 5 with CLI input

This script integrates:
- Conversational LLM via Ollama
- Object detection using YOLOv8 with Raspberry Pi Camera Module 2
- Home automation via Home Assistant API
- Text input via CLI
- Text output to console

Author: AI Assistant
Date: 2024
"""

import os
import sys
import time
import json
import threading
import queue
import logging
from typing import Optional, Dict, List, Tuple
from enum import Enum

# Computer Vision Libraries
import cv2
from ultralytics import YOLO
from picamera2 import Picamera2

# Network and API Libraries
import requests
from requests.exceptions import RequestException

# Configuration and Utilities
import configparser
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_assistant.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class AssistantMode(Enum):
    """Enumeration for different assistant modes"""
    MAIN_LLM = "main_llm"
    OBJECT_DETECTION = "object_detection"
    HOME_AUTOMATION = "home_automation"

class AIAssistant:
    """
    Main AI Assistant class that handles multi-modal interactions with CLI input
    """
    
    def __init__(self, config_file: str = "config.ini"):
        """
        Initialize the AI Assistant with all components
        
        Args:
            config_file: Path to configuration file
        """
        self.config = self._load_config(config_file)
        self.current_mode = AssistantMode.MAIN_LLM
        self.wake_word = self.config.get('Assistant', 'wake_word', fallback='jarvis')
        
        # Initialize components
        self._init_vision_components()
        self._init_llm_components()
        self._init_home_assistant()
        
        logger.info("AI Assistant initialized successfully")
    
    def _load_config(self, config_file: str) -> configparser.ConfigParser:
        """Load configuration from file or create default"""
        config = configparser.ConfigParser()
        
        if os.path.exists(config_file):
            config.read(config_file)
        else:
            self._create_default_config(config, config_file)
        
        return config
    
    def _create_default_config(self, config: configparser.ConfigParser, config_file: str):
        """Create default configuration file"""
        config['Assistant'] = {
            'wake_word': 'jarvis',
            'language': 'en-US',
            'voice_rate': '150',
            'voice_volume': '0.9'
        }
        
        config['Ollama'] = {
            'base_url': 'http://localhost:11434',
            'model': 'tinyllama:1.1b',
            'timeout': '30'
        }
        
        config['HomeAssistant'] = {
            'base_url': 'http://192.168.1.100:8123',
            'bearer_token': 'YOUR_BEARER_TOKEN_HERE',
            'timeout': '10'
        }
        
        config['Camera'] = {
            'resolution_width': '640',
            'resolution_height': '480'
        }
        
        config['Audio'] = {
            'sample_rate': '16000',
            'chunk_size': '1024',
            'channels': '1',
            'mic_device_index': None
        }
        
        with open(config_file, 'w') as f:
            config.write(f)
        
        logger.info(f"Default configuration created at {config_file}")
        logger.warning("Please update the configuration file with your actual settings")
    
    def _init_vision_components(self):
        """Initialize computer vision components using Raspberry Pi Camera Module 2"""
        try:
            # Initialize PiCamera2
            self.camera = Picamera2()
            
            # Configure camera with desired resolution
            resolution_width = int(self.config.get('Camera', 'resolution_width', fallback='640'))
            resolution_height = int(self.config.get('Camera', 'resolution_height', fallback='480'))
            
            # Create a configuration for the camera
            camera_config = self.camera.create_still_configuration(
                main={"size": (resolution_width, resolution_height)}
            )
            self.camera.configure(camera_config)
            
            # Start the camera
            self.camera.start()
            
            # Initialize YOLO model
            self.yolo_model = YOLO('yolov8n.pt')
            
            logger.info("Vision components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize vision components: {e}")
            raise
    
    def _init_llm_components(self):
        """Initialize LLM components"""
        self.ollama_url = self.config.get('Ollama', 'base_url', fallback='http://localhost:11434')
        self.ollama_model = self.config.get('Ollama', 'model', fallback='llama2')
        self.ollama_timeout = int(self.config.get('Ollama', 'timeout', fallback='30'))
        
        # Test Ollama connection
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                logger.info("Ollama connection established successfully")
            else:
                logger.warning("Ollama connection test failed")
        except Exception as e:
            logger.warning(f"Could not test Ollama connection: {e}")
    
    def _init_home_assistant(self):
        """Initialize Home Assistant components"""
        self.ha_url = self.config.get('HomeAssistant', 'base_url', fallback='http://192.168.1.100:8123')
        self.ha_token = self.config.get('HomeAssistant', 'bearer_token', fallback='YOUR_BEARER_TOKEN_HERE')
        self.ha_timeout = int(self.config.get('HomeAssistant', 'timeout', fallback='10'))
        
        # Test Home Assistant connection
        if self.ha_token != 'YOUR_BEARER_TOKEN_HERE':
            try:
                headers = {'Authorization': f'Bearer {self.ha_token}'}
                response = requests.get(f"{self.ha_url}/api/", headers=headers, timeout=5)
                if response.status_code == 200:
                    logger.info("Home Assistant connection established successfully")
                else:
                    logger.warning("Home Assistant connection test failed")
            except Exception as e:
                logger.warning(f"Could not test Home Assistant connection: {e}")
        else:
            logger.warning("Home Assistant token not configured")
    
    def query_ollama(self, prompt: str) -> Optional[str]:
        """
        Send a prompt to the Ollama LLM and get response
        
        Args:
            prompt: The prompt to send to the LLM
            
        Returns:
            LLM response text or None if failed
        """
        try:
            payload = {
                "model": self.ollama_model,
                "prompt": prompt,
                "stream": False
            }
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=self.ollama_timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', '').strip()
            else:
                logger.error(f"Ollama API error: {response.status_code}")
                return None
                
        except RequestException as e:
            logger.error(f"Request error when querying Ollama: {e}")
            return None
        except Exception as e:
            logger.error(f"Error querying Ollama: {e}")
            return None
    
    def process_llm_response(self, response: str) -> AssistantMode:
        """
        Process LLM response to determine mode switching
        
        Args:
            response: The LLM response text
            
        Returns:
            The mode to switch to
        """
        response_lower = response.lower()
        
        # Check for object detection triggers
        object_triggers = [
            "switch to object detection mode",
            "what do you see",
            "detect objects",
            "look around",
            "what's in front of you"
        ]
        
        for trigger in object_triggers:
            if trigger in response_lower:
                logger.info("Switching to object detection mode")
                return AssistantMode.OBJECT_DETECTION
        
        # Check for home automation triggers
        home_triggers = [
            "switch to home automation mode",
            "control my smart home",
            "home automation",
            "smart home",
            "control devices"
        ]
        
        for trigger in home_triggers:
            if trigger in response_lower:
                logger.info("Switching to home automation mode")
                return AssistantMode.HOME_AUTOMATION
        
        # Default to main LLM mode
        return AssistantMode.MAIN_LLM
    
    def run_object_detection(self) -> str:
        """
        Capture image from Raspberry Pi Camera Module 2 and run object detection
        
        Returns:
            Descriptive text of detected objects
        """
        try:
            logger.info("Capturing image for object detection...")
            
            # Capture frame from PiCamera2
            frame = self.camera.capture_array()
            
            # Convert frame to BGR format for OpenCV/YOLO compatibility
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            
            # Run YOLO detection
            results = self.yolo_model(frame)
            
            # Extract detected objects
            detected_objects = []
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        # Get class name
                        class_id = int(box.cls[0])
                        class_name = result.names[class_id]
                        
                        # Get confidence
                        confidence = float(box.conf[0])
                        
                        # Only include high-confidence detections
                        if confidence > 0.5:
                            detected_objects.append(class_name)
            
            # Remove duplicates and create description
            unique_objects = list(set(detected_objects))
            
            if not unique_objects:
                description = "I don't see any objects clearly in the image."
            elif len(unique_objects) == 1:
                description = f"I can see a {unique_objects[0]}."
            elif len(unique_objects) == 2:
                description = f"I can see a {unique_objects[0]} and a {unique_objects[1]}."
            else:
                objects_text = ", ".join(unique_objects[:-1]) + f", and a {unique_objects[-1]}"
                description = f"I can see a {objects_text}."
            
            logger.info(f"Object detection result: {description}")
            return description
            
        except Exception as e:
            logger.error(f"Error in object detection: {e}")
            return "Sorry, I encountered an error while trying to detect objects."
    
    def control_home_device(self, command: str) -> str:
        """
        Parse command and control Home Assistant devices
        
        Args:
            command: Text command for home automation
            
        Returns:
            Confirmation message
        """
        try:
            # Parse the command to extract device and action
            command_lower = command.lower()
            
            # Define device mappings (device name -> entity_id)
            device_mappings = {
                'living room light': 'light.living_room',
                'bedroom light': 'light.bedroom',
                'kitchen light': 'light.kitchen',
                'living room fan': 'fan.living_room',
                'bedroom fan': 'fan.bedroom',
                'thermostat': 'climate.home',
                'tv': 'media_player.living_room_tv'
            }
            
            # Define action mappings
            action_mappings = {
                'turn on': 'turn_on',
                'turn off': 'turn_off',
                'switch on': 'turn_on',
                'switch off': 'turn_off',
                'set to high': 'set_speed',
                'set to low': 'set_speed',
                'setಸ
                'set to medium': 'set_speed'
            }
            
            # Find device and action
            target_device = None
            target_action = None
            
            for device_name, entity_id in device_mappings.items():
                if device_name in command_lower:
                    target_device = entity_id
                    break
            
            for action_phrase, action in action_mappings.items():
                if action_phrase in command_lower:
                    target_action = action
                    break
            
            if not target_device or not target_action:
                return "I couldn't understand which device or action you want me to control."
            
            # Determine service and domain
            if target_device.startswith('light.'):
                domain = 'light'
                service = target_action
            elif target_device.startswith('fan.'):
                domain = 'fan'
                service = target_action
            elif target_device.startswith('climate.'):
                domain = 'climate'
                service = 'set_temperature'
            elif target_device.startswith('media_player.'):
                domain = 'media_player'
                service = 'turn_on' if 'on' in target_action else 'turn_off'
            else:
                return f"I don't know how to control {target_device}."
            
            # Prepare service data
            service_data = {'entity_id': target_device}
            
            # Handle special cases
            if target_action == 'set_speed':
                if 'high' in command_lower:
                    service_data['speed'] = 'high'
                elif 'low' in command_lower:
                    service_data['speed'] = 'low'
                elif 'medium' in command_lower:
                    service_data['speed'] = 'medium'
            
            # Send request to Home Assistant
            headers = {'Authorization': f'Bearer {self.ha_token}'}
            url = f"{self.ha_url}/api/services/{domain}/{service}"
            
            response = requests.post(
                url,
                json=service_data,
                headers=headers,
                timeout=self.ha_timeout
            )
            
            if response.status_code == 200:
                # Create confirmation message
                device_display_name = target_device.split('.')[-1].replace('_', ' ')
                action_display = target_action.replace('_', ' ')
                
                if 'turn_on' in target_action:
                    confirmation = f"Okay, turning on the {device_display_name}."
                elif 'turn_off' in target_action:
                    confirmation = f"Okay, turning off the {device_display_name}."
                elif 'set_speed' in target_action:
                    speed = service_data.get('speed', 'medium')
                    confirmation = f"Okay, setting the {device_display_name} to {speed} speed."
                else:
                    confirmation = f"Okay, {action_display} the {device_display_name}."
                
                logger.info(f"Home automation command executed: {confirmation}")
                return confirmation
            else:
                logger.error(f"Home Assistant API error: {response.status_code}")
                return "Sorry, I encountered an error while trying to control the device."
                
        except RequestException as e:
            logger.error(f"Request error in home automation: {e}")
            return "Sorry, I couldn't connect to the home automation system."
        except Exception as e:
            logger.error(f"Error in home automation: {e}")
            return "Sorry, I encountered an error while trying to control the device."
    
    def start_listening(self):
        """Start the main loop to accept CLI input"""
        print("Hello! I'm your AI assistant. I'm ready to help you.")
        logger.info("Starting AI Assistant...")
        
        try:
            while True:
                command = input("Enter your command (or 'exit' to quit): ")
                
                if command.lower() == 'exit':
                    print("Goodbye!")
                    break
                
                if self.current_mode == AssistantMode.MAIN_LLM:
                    response = self.query_ollama(command)
                    if response:
                        new_mode = self.process_llm_response(response)
                        
                        if new_mode != AssistantMode.MAIN_LLM:
                            self.current_mode = new_mode
                            if new_mode == AssistantMode.OBJECT_DETECTION:
                                print("Switching to object detection mode.")
                                detection_result = self.run_object_detection()
                                print(detection_result)
                                self.current_mode = AssistantMode.MAIN_LLM
                                print("Back to main mode.")
                            elif new_mode == AssistantMode.HOME_AUTOMATION:
                                print("Switching to home automation mode. Enter your home automation command:")
                                ha_command = input("> ")
                                confirmation = self.control_home_device(ha_command)
                                print(confirmation)
                                self.current_mode = AssistantMode.MAIN_LLM
                                print("Back to main mode.")
                        else:
                            print(response)
                    else:
                        print("Sorry, I couldn't process your request. Please try again.")
                
        except KeyboardInterrupt:
            logger.info("Shutting down AI Assistant...")
            self.stop_listening()
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            self.stop_listening()
    
    def stop_listening(self):
        """Stop the assistant and cleanup"""
        if hasattr(self, 'camera'):
            self.camera.stop()
            self.camera.close()
        cv2.destroyAllWindows()
        print("Goodbye!")
        logger.info("AI Assistant stopped")

def main():
    """Main function to run the AI Assistant"""
    print("=" * 60)
    print("RPi5 Multi-Modal AI Assistant (CLI Version)")
    print("=" * 60)
    print("Initializing...")
    
    try:
        # Create and start the assistant
        assistant = AIAssistant()
        
        # Start the main loop
        assistant.start_listening()
        
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
