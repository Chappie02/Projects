"""
RAG (Retrieval-Augmented Generation) Engine for the AI Assistant.
Handles document ingestion, embedding generation, and context retrieval.
"""

import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import hashlib
import json
from datetime import datetime


class RAGEngine:
    """
    Retrieval-Augmented Generation engine using ChromaDB and sentence transformers.
    Provides document ingestion, embedding, and context retrieval capabilities.
    """
    
    def __init__(self, 
                 knowledge_base_path: str = "knowledge_base",
                 embedding_model: str = "all-MiniLM-L6-v2",
                 chunk_size: int = 512,
                 chunk_overlap: int = 50,
                 top_k: int = 3):
        """
        Initialize the RAG engine.
        
        Args:
            knowledge_base_path: Path to knowledge base directory
            embedding_model: Name of the sentence transformer model
            chunk_size: Size of text chunks for processing
            chunk_overlap: Overlap between chunks
            top_k: Number of top relevant documents to retrieve
        """
        self.knowledge_base_path = Path(knowledge_base_path)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.top_k = top_k
        
        self.logger = logging.getLogger(__name__)
        
        # Initialize ChromaDB
        self._init_chromadb()
        
        # Initialize embedding model
        self._init_embedding_model(embedding_model)
        
        # Ensure knowledge base directory exists
        self.knowledge_base_path.mkdir(parents=True, exist_ok=True)
        
        self.logger.info("RAG Engine initialized successfully")
    
    def _init_chromadb(self) -> None:
        """Initialize ChromaDB client and collection."""
        try:
            # Use persistent storage in data directory
            chroma_path = Path("data/chroma_db")
            chroma_path.mkdir(parents=True, exist_ok=True)
            
            self.chroma_client = chromadb.PersistentClient(
                path=str(chroma_path),
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Create or get collection
            self.collection = self.chroma_client.get_or_create_collection(
                name="knowledge_base",
                metadata={"description": "AI Assistant Knowledge Base"}
            )
            
            self.logger.info("ChromaDB initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize ChromaDB: {e}")
            raise
    
    def _init_embedding_model(self, model_name: str) -> None:
        """Initialize the sentence transformer model."""
        try:
            self.logger.info(f"Loading embedding model: {model_name}")
            self.embedding_model = SentenceTransformer(model_name)
            self.logger.info("Embedding model loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load embedding model: {e}")
            raise
    
    def _chunk_text(self, text: str) -> List[str]:
        """
        Split text into overlapping chunks.
        
        Args:
            text: Input text to chunk
            
        Returns:
            List of text chunks
        """
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # If this isn't the last chunk, try to break at a sentence boundary
            if end < len(text):
                # Look for sentence endings within the last 100 characters
                sentence_end = text.rfind('.', start, end)
                if sentence_end > start + self.chunk_size - 100:
                    end = sentence_end + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start position with overlap
            start = end - self.chunk_overlap
            if start >= len(text):
                break
        
        return chunks
    
    def _generate_document_id(self, file_path: str, chunk_index: int) -> str:
        """Generate a unique ID for a document chunk."""
        file_hash = hashlib.md5(str(file_path).encode()).hexdigest()[:8]
        return f"{file_hash}_{chunk_index}"
    
    def ingest_document(self, file_path: str) -> bool:
        """
        Ingest a document into the knowledge base.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                self.logger.error(f"File not found: {file_path}")
                return False
            
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if not content.strip():
                self.logger.warning(f"Empty file: {file_path}")
                return False
            
            # Check if document already exists
            existing_docs = self.collection.get(
                where={"source_file": str(file_path)}
            )
            
            if existing_docs['ids']:
                self.logger.info(f"Document already exists: {file_path}")
                return True
            
            # Chunk the text
            chunks = self._chunk_text(content)
            
            if not chunks:
                self.logger.warning(f"No chunks generated for: {file_path}")
                return False
            
            # Generate embeddings and prepare data
            documents = []
            metadatas = []
            ids = []
            
            for i, chunk in enumerate(chunks):
                doc_id = self._generate_document_id(str(file_path), i)
                
                documents.append(chunk)
                metadatas.append({
                    "source_file": str(file_path),
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "ingestion_date": datetime.now().isoformat()
                })
                ids.append(doc_id)
            
            # Add to ChromaDB
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            self.logger.info(f"Successfully ingested {len(chunks)} chunks from {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error ingesting document {file_path}: {e}")
            return False
    
    def ingest_directory(self, directory_path: str, file_extensions: List[str] = None) -> int:
        """
        Ingest all documents from a directory.
        
        Args:
            directory_path: Path to directory containing documents
            file_extensions: List of file extensions to process (default: .txt, .md)
            
        Returns:
            Number of successfully ingested documents
        """
        if file_extensions is None:
            file_extensions = ['.txt', '.md']
        
        directory_path = Path(directory_path)
        if not directory_path.exists():
            self.logger.error(f"Directory not found: {directory_path}")
            return 0
        
        ingested_count = 0
        
        for file_path in directory_path.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in file_extensions:
                if self.ingest_document(str(file_path)):
                    ingested_count += 1
        
        self.logger.info(f"Ingested {ingested_count} documents from {directory_path}")
        return ingested_count
    
    def retrieve_context(self, query: str, top_k: Optional[int] = None) -> str:
        """
        Retrieve relevant context for a query.
        
        Args:
            query: User query
            top_k: Number of top documents to retrieve (uses default if None)
            
        Returns:
            Formatted context string
        """
        if top_k is None:
            top_k = self.top_k
        
        try:
            # Query ChromaDB
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k
            )
            
            if not results['documents'] or not results['documents'][0]:
                self.logger.warning("No relevant documents found for query")
                return ""
            
            # Format context
            context_parts = []
            documents = results['documents'][0]
            metadatas = results['metadatas'][0]
            distances = results['distances'][0]
            
            for i, (doc, metadata, distance) in enumerate(zip(documents, metadatas, distances)):
                source_file = Path(metadata['source_file']).name
                context_parts.append(f"Source: {source_file}\nContent: {doc}\n")
            
            context = "\n---\n".join(context_parts)
            
            self.logger.info(f"Retrieved {len(documents)} relevant documents for query")
            return context
            
        except Exception as e:
            self.logger.error(f"Error retrieving context: {e}")
            return ""
    
    def search_documents(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search documents and return detailed results.
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of search results with metadata
        """
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k
            )
            
            search_results = []
            if results['documents'] and results['documents'][0]:
                for doc, metadata, distance in zip(
                    results['documents'][0],
                    results['metadatas'][0],
                    results['distances'][0]
                ):
                    search_results.append({
                        'content': doc,
                        'source_file': metadata['source_file'],
                        'chunk_index': metadata['chunk_index'],
                        'similarity_score': 1 - distance,  # Convert distance to similarity
                        'ingestion_date': metadata['ingestion_date']
                    })
            
            return search_results
            
        except Exception as e:
            self.logger.error(f"Error searching documents: {e}")
            return []
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base collection."""
        try:
            count = self.collection.count()
            
            # Get sample of documents to analyze
            sample = self.collection.get(limit=min(100, count))
            
            sources = set()
            if sample['metadatas']:
                for metadata in sample['metadatas']:
                    sources.add(metadata['source_file'])
            
            return {
                'total_documents': count,
                'unique_sources': len(sources),
                'sources': list(sources)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting collection stats: {e}")
            return {'total_documents': 0, 'unique_sources': 0, 'sources': []}
    
    def delete_document(self, file_path: str) -> bool:
        """
        Delete all chunks of a document from the knowledge base.
        
        Args:
            file_path: Path to the document to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Find all chunks for this document
            results = self.collection.get(
                where={"source_file": str(file_path)}
            )
            
            if not results['ids']:
                self.logger.warning(f"No documents found for: {file_path}")
                return False
            
            # Delete the chunks
            self.collection.delete(ids=results['ids'])
            
            self.logger.info(f"Deleted {len(results['ids'])} chunks for {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting document {file_path}: {e}")
            return False
    
    def reset_knowledge_base(self) -> bool:
        """Reset the entire knowledge base."""
        try:
            self.chroma_client.delete_collection("knowledge_base")
            self.collection = self.chroma_client.create_collection(
                name="knowledge_base",
                metadata={"description": "AI Assistant Knowledge Base"}
            )
            self.logger.info("Knowledge base reset successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error resetting knowledge base: {e}")
            return False
