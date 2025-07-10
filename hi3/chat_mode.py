from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from sentence_transformers import SentenceTransformer, util

class ChatMode:
    def __init__(self, model_name='distilgpt2'):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(model_name)
        self.generator = pipeline('text-generation', model=self.model, tokenizer=self.tokenizer, max_length=100)
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
        response = self.generator(user_input, max_length=100, num_return_sequences=1)[0]['generated_text']
        return response[len(user_input):].strip()

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