import os
import sys
import json
import threading
from modes import llm_chat, object_detection, home_automation

CONFIG_PATH = os.path.join('config', 'config.json')

# Load configuration
def load_config():
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)

config = load_config()

# Simple intent detection for mode switching
def detect_intent(user_input):
    user_input = user_input.lower()
    if any(kw in user_input for kw in ['see', 'camera', 'detect', 'objects']):
        return 'object_detection'
    elif any(kw in user_input for kw in ['turn on', 'turn off', 'switch', 'light', 'fan', 'appliance', 'automation']):
        return 'home_automation'
    else:
        return 'llm_chat'

def main():
    print("\nWelcome to the Raspberry Pi Multi-Modal AI Assistant!\n")
    print("Type your request. Modes: [Chat, Object Detection, Home Automation]")
    print("Type 'exit' to quit.\n")
    mode = 'llm_chat'
    while True:
        user_input = input(f"[{mode}] > ")
        if user_input.strip().lower() == 'exit':
            print("Goodbye!")
            break
        new_mode = detect_intent(user_input)
        if new_mode != mode:
            print(f"Switching to {new_mode.replace('_', ' ').title()} mode.")
            mode = new_mode
        if mode == 'llm_chat':
            response = llm_chat.handle_chat(user_input, config)
            print(response)
        elif mode == 'object_detection':
            def detect_and_summarize():
                labels = object_detection.detect_objects(config)
                summary = llm_chat.summarize_scene(labels, config)
                print(f"Detected objects: {', '.join(labels)}")
                print(f"Scene summary: {summary}")
            t = threading.Thread(target=detect_and_summarize)
            t.start()
            t.join()
        elif mode == 'home_automation':
            response = home_automation.handle_automation(user_input, config)
            print(response)
        # Placeholder for future voice input
        # if config.get('voice_input_enabled', False):
        #     ...

if __name__ == '__main__':
    main() 