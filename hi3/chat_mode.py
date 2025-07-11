import requests
from sentence_transformers import SentenceTransformer, util

class ChatMode:
    def __init__(self, model_name='llama3', api_url='http://localhost:11434'):
        self.model_name = model_name
        self.api_url = api_url
        # For intent recognition
        self.intent_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.switch_phrases = [
            'switch to object detection',
            'object detection mode',
            'detect objects',
            'start object detection',
            'go to object detection',
            'enable object detection',
        ]
        self.chat_phrases = [
            'switch to chat mode',
            'go back to chat',
            'chat mode',
            'return to chat',
            'enable chat mode',
        ]

    def generate_response(self, user_input):
        try:
            response = requests.post(
                f"{self.api_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": user_input,
                    "max_tokens": 100,  # Adjust as needed
                    "stream": False
                }
            )
            response.raise_for_status()
            generated_text = response.json().get('response', '')
            # Remove the input prompt from the response, if present
            return generated_text[len(user_input):].strip() if generated_text.startswith(user_input) else generated_text.strip()
        except requests.RequestException as e:
            return f"Error communicating with Ollama API: {e}"

    def detect_intent(self, user_input):
        # Returns 'object_detection', 'chat', or None
        all_phrases = self.switch_phrases + self.chat_phrases
        embeddings = self.intent_model.encode([user_input] + all_phrases)
        similarities = util.cos_sim(embeddings[0], embeddings[1:])[0]
        max_idx = similarities.argmax().item()
        if similarities[max_idx] > 0.7:
            if max_idx < len(self.switch_phrases):
                return 'object_detection'
            else:
                return 'chat'
        return None
