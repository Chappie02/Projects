from llama_cpp import Llama

class LLMHandler:
    def __init__(self, model_path):
        """Initialize the LLM with the specified model path."""
        self.llm = Llama(model_path=model_path, n_ctx=2048, verbose=False)

    def generate_response(self, prompt):
        """Generate a response from the LLM for the given prompt."""
        try:
            output = self.llm(prompt, max_tokens=512, stop=["\n"], echo=False)
            return output['choices'][0]['text'].strip()
        except Exception as e:
            return f"LLM Error: {str(e)}"