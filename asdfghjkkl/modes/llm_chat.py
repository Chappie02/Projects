import os
import subprocess
import json

def handle_chat(user_input, config):
    backend = config['llm']['backend']
    model_path = config['llm']['model_path']
    if backend == 'ollama':
        return ollama_chat(user_input, config)
    elif backend == 'llama-cpp-python':
        return llama_cpp_chat(user_input, model_path)
    else:
        return "[LLM backend not configured properly]"

def ollama_chat(prompt, config):
    import requests
    url = config['llm']['ollama_url']
    model = config['llm']['model']
    data = {"model": model, "prompt": prompt}
    try:
        r = requests.post(f"{url}/api/generate", json=data, timeout=60)
        r.raise_for_status()
        return r.json().get('response', '[No response]')
    except Exception as e:
        return f"[Ollama error: {e}]"

def llama_cpp_chat(prompt, model_path):
    try:
        from llama_cpp import Llama
        llm = Llama(model_path=model_path, n_ctx=2048, n_threads=4)
        output = llm(prompt, max_tokens=256)
        return output['choices'][0]['text'].strip()
    except Exception as e:
        return f"[llama-cpp-python error: {e}]"

def summarize_scene(labels, config):
    prompt = f"Summarize the scene based on these objects: {', '.join(labels)}"
    return handle_chat(prompt, config)

# Placeholder for future voice input expansion
# def handle_voice_input(...):
#     pass 