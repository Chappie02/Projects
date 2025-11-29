"""
LLM + RAG manager built around llama.cpp and ChromaDB.
"""

from __future__ import annotations

import logging
import time
import uuid
from pathlib import Path
from typing import Iterable, List, Optional

from .config import LLMConfig

try:  # pragma: no cover - heavy dependency
    from llama_cpp import Llama
except ImportError:
    Llama = None

try:
    import chromadb
except ImportError:  # pragma: no cover - heavy dependency
    chromadb = None


class LLMManager:
    """Wraps llama.cpp inference and ChromaDB-backed memory."""

    def __init__(self, config: LLMConfig, logger: Optional[logging.Logger] = None):
        if Llama is None:
            raise RuntimeError("llama_cpp Python bindings are required but not installed.")
        if chromadb is None:
            raise RuntimeError("chromadb is required for RAG but not installed.")

        self._config = config
        self._logger = logger or logging.getLogger(__name__)
        Path(config.chroma_path).mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=str(config.chroma_path))
        self._collection = self._client.get_or_create_collection(config.collection_name)
        self._llm = Llama(
            model_path=str(config.model_path),
            n_ctx=4096,
            n_threads=4,
            logits_all=False,
        )

    def add_memory(self, question: str, answer: str) -> None:
        """Persist Q/A pair in the vector store."""
        doc_id = str(uuid.uuid4())
        metadata = {"timestamp": time.time(), "type": "chat_exchange"}
        self._collection.add(
            ids=[doc_id],
            documents=[f"Q: {question}\nA: {answer}"],
            metadatas=[metadata],
        )
        self._logger.debug("Stored interaction %s in memory.", doc_id)

    def _retrieve_context(self, query: str, k: int = 3) -> List[str]:
        if self._collection.count() == 0:
            return []

        results = self._collection.query(query_texts=[query], n_results=k)
        documents = results.get("documents", [[]])[0]
        return [doc for doc in documents if doc]

    def _build_prompt(self, history: Iterable[tuple[str, str]], context_docs: List[str], user_text: str) -> str:
        history_lines = []
        for user_msg, assistant_msg in history:
            history_lines.append(f"User: {user_msg}")
            history_lines.append(f"Assistant: {assistant_msg}")
        history_block = "\n".join(history_lines)
        context_block = "\n---\n".join(context_docs) if context_docs else "No prior context."

        prompt = (
            "You are an on-device multimodal assistant running entirely on a Raspberry Pi. "
            "Use the retrieved chat memory when helpful, stay concise, and mention detection results when provided.\n\n"
            f"Retrieved memory snippets:\n{context_block}\n\n"
            f"Conversation so far:\n{history_block}\n\n"
            f"User: {user_text}\nAssistant:"
        )
        return prompt

    def generate_response(self, user_text: str, history: Iterable[tuple[str, str]]) -> str:
        """Generate a response using llama.cpp with RAG context."""
        context_docs = self._retrieve_context(user_text)
        prompt = self._build_prompt(history, context_docs, user_text)
        self._logger.debug("LLM prompt prepared (%d chars).", len(prompt))
        result = self._llm(
            prompt,
            max_tokens=self._config.max_tokens,
            temperature=self._config.temperature,
            top_p=self._config.top_p,
            stop=["User:", "\nUser:"],
        )
        text = result["choices"][0]["text"].strip()
        self._logger.info("LLM response generated (%d chars).", len(text))
        return text

