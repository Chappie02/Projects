import os
from c_transformers import AutoModelForCausalLM, AutoConfig
from pathlib import Path

def load_model(model_path):
    """Load the GGUF model using c_transformers."""
    try:
        config = AutoConfig()
        config.model_type = "gemma"  # Specify model type for gemma-2b
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            model_type="gemma",
            local_files_only=True,
            gpu_layers=0  # No GPU acceleration on Raspberry Pi
        )
        return model
    except Exception as e:
        print(f"Error loading model: {e}")
        return None

def generate_response(model, prompt, max_length=200):
    """Generate a response from the model given a prompt."""
    try:
        response = model(prompt, max_new_tokens=max_length, temperature=0.7, repetition_penalty=1.1)
        return response
    except Exception as e:
        return f"Error generating response: {e}"

def main():
    # Path to the downloaded GGUF model file
    model_path = "./gemma-2b.gguf"  # Adjust this path as needed

    # Check if model file exists
    if not Path(model_path).exists():
        print(f"Model file not found at {model_path}. Please download the 'gemma-2b-GGUF' model from Hugging Face.")
        print("URL: https://huggingface.co/MaziyarPanahi/gemma-2b-GGUF")
        return

    # Load the model
    print("Loading model... This may take a moment.")
    model = load_model(model_path)
    if not model:
        print("Failed to load the model. Exiting.")
        return

    # CLI loop
    print("\nGemma-2B CLI Interface (type 'exit' to quit)")
    while True:
        prompt = input("\nYou: ")
        if prompt.lower() == "exit":
            print("Exiting...")
            break
        if not prompt.strip():
            print("Please enter a valid prompt.")
            continue

        print("Gemma: ", end="")
        response = generate_response(model, prompt)
        print(response)

if __name__ == "__main__":
    main()