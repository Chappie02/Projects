from llama_cpp import Llama
from app.core import config
from app.core.logger import setup_logger

logger = setup_logger(__name__)

class LLMEngine:
    def __init__(self):
        self.llm = None

    def _init_model(self):
        if self.llm is None:
            logger.info(f"Loading LLM from {config.LLM_MODEL_PATH}...")
            # Optimize for Pi 5 4GB
            try:
                self.llm = Llama(
                    model_path=str(config.LLM_MODEL_PATH),
                    n_ctx=2048,
                    n_threads=4, # Pi 5 has 4 cores
                    verbose=False
                )
                logger.info("LLM Loaded.")
            except Exception as e:
                logger.error(f"Failed to load LLM: {e}")

    def generate(self, prompt, context=""):
        self._init_model()
        if not self.llm:
            return "I am unable to think right now."

        full_prompt = f"System: You are a helpful assistant.\nContext: {context}\nUser: {prompt}\nAssistant:"
        
        try:
            output = self.llm(
                full_prompt,
                max_tokens=128, # Keep it short for speed
                stop=["User:", "\n"],
                echo=False
            )
            return output['choices'][0]['text'].strip()
        except Exception as e:
            logger.error(f"Generation Error: {e}")
            return "Error generating response."
