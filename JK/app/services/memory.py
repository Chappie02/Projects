import chromadb
from chromadb.utils import embedding_functions
from app.core import config
from app.core.logger import setup_logger

logger = setup_logger(__name__)

class RAGEngine:
    def __init__(self):
        self.client = None
        self.collection = None

    def _init_db(self):
        if self.client is None:
            logger.info("Initializing ChromaDB...")
            try:
                # Persistent client
                self.client = chromadb.PersistentClient(path=str(config.CHROMA_DB_PATH))
                
                # Use a default embedding function or specify one
                emb_fn = embedding_functions.DefaultEmbeddingFunction()
                
                self.collection = self.client.get_or_create_collection(
                    name="assistant_memory",
                    embedding_function=emb_fn
                )
                logger.info("ChromaDB initialized.")
            except Exception as e:
                logger.error(f"ChromaDB init failed: {e}")

    def retrieve(self, query, n_results=2):
        self._init_db()
        if not self.collection:
            return ""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            if results['documents'] and results['documents'][0]:
                return " ".join(results['documents'][0])
            return ""
        except Exception as e:
            logger.error(f"RAG Error: {e}")
            return ""

    def add_memory(self, text, metadata=None):
        self._init_db()
        if not self.collection:
            return
        try:
            # Simple ID generation
            import uuid
            self.collection.add(
                documents=[text],
                metadatas=[metadata] if metadata else None,
                ids=[str(uuid.uuid4())]
            )
            logger.debug("Memory added.")
        except Exception as e:
            logger.error(f"Memory Add Error: {e}")
