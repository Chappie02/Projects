from llm_handler import LLMHandler
from detector import ObjectDetector

class Assistant:
    def __init__(self, llm_model_path, yolo_model_path):
        """Initialize the assistant with LLM and object detector."""
        self.llm_handler = LLMHandler(llm_model_path)
        self.detector = ObjectDetector(yolo_model_path)
        self.mode = "chat"  # Default mode

    def process_input(self, user_input):
        """Process user input and switch modes if necessary."""
        # Check for object detection command
        if user_input.lower().startswith("detect object"):
            self.mode = "detect"
            results = self.detector.detect_objects()
            response = "Detected objects: " + ", ".join(results)
            self.mode = "chat"  # Return to chat mode
            return response
        else:
            # Default to chat mode
            return self.llm_handler.generate_response(user_input)