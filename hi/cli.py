from assistant import Assistant

def main():
    # Paths to models (adjust as needed)
    llm_model_path = "models/llama-3.1-8b.gguf"
    yolo_model_path = "models/yolov8n.pt"

    # Initialize assistant
    assistant = Assistant(llm_model_path, yolo_model_path)

    print("Pi Assistant CLI. Type 'exit' to quit.")
    print("Commands: 'hello' for chat, 'detect object' for object detection.")

    while True:
        user_input = input("> ")
        if user_input.lower() == "exit":
            break
        response = assistant.process_input(user_input)
        print(response)

if __name__ == "__main__":
    main()