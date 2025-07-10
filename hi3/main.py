from chat_mode import ChatMode
from object_detection_mode import ObjectDetectionMode


def main():
    chat_mode = ChatMode()
    object_detection_mode = ObjectDetectionMode()
    mode = 'chat'
    print("Welcome! Type your message. Type 'switch to object detection' or 'switch to chat mode' to change modes.")
    while True:
        if mode == 'chat':
            user_input = input("[ChatMode] You: ")
            intent = chat_mode.detect_intent(user_input)
            if intent == 'object_detection':
                print("Switching to Object Detection Mode...")
                mode = 'object_detection'
                continue
            elif user_input.lower() in ['exit', 'quit']:
                print("Exiting application.")
                break
            response = chat_mode.generate_response(user_input)
            print(f"[ChatMode] Bot: {response}")
        elif mode == 'object_detection':
            print("[ObjectDetectionMode] Type a command (or 'switch to chat mode' to return to chat):")
            print("[ObjectDetectionMode] Starting camera. Press 'q' in the camera window to stop detection.")
            object_detection_mode.detect_objects()
            # After camera window closes, ask for user input
            user_input = input("[ObjectDetectionMode] Command: ")
            intent = object_detection_mode.detect_intent(user_input)
            if intent == 'chat':
                print("Switching to Chat Mode...")
                mode = 'chat'
                continue
            elif user_input.lower() in ['exit', 'quit']:
                print("Exiting application.")
                break
            print("[ObjectDetectionMode] Unrecognized command. Returning to object detection.")

if __name__ == "__main__":
    main() 