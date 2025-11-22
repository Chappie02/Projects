"""
Memory module for ChromaDB-based RAG and conversation history
Handles storing and retrieving conversation context
"""

import chromadb
from chromadb.config import Settings
import config
import os
from datetime import datetime


class MemorySystem:
    """Manages conversation history and RAG using ChromaDB"""
    
    def __init__(self):
        """Initialize ChromaDB client and collection"""
        self.client = None
        self.collection = None
        self._init_chromadb()
    
    def _init_chromadb(self):
        """Initialize ChromaDB client and create/load collection"""
        try:
            # Create persistent client
            self.client = chromadb.PersistentClient(
                path=config.CHROMA_DB_PATH,
                settings=Settings(anonymized_telemetry=False)
            )
            
            # Get or create collection
            try:
                self.collection = self.client.get_collection(name=config.COLLECTION_NAME)
                print(f"Loaded existing collection: {config.COLLECTION_NAME}")
            except:
                self.collection = self.client.create_collection(
                    name=config.COLLECTION_NAME,
                    metadata={"description": "Conversation history and RAG context"}
                )
                print(f"Created new collection: {config.COLLECTION_NAME}")
            
        except Exception as e:
            print(f"Error initializing ChromaDB: {e}")
            raise
    
    def add_conversation(self, user_query, assistant_response):
        """
        Store a conversation turn in ChromaDB
        
        Args:
            user_query: User's input text
            assistant_response: Assistant's response text
        """
        try:
            timestamp = datetime.now().isoformat()
            conversation_text = f"User: {user_query}\nAssistant: {assistant_response}"
            
            # Generate unique ID
            doc_id = f"conv_{datetime.now().timestamp()}"
            
            # Add to collection
            self.collection.add(
                documents=[conversation_text],
                ids=[doc_id],
                metadatas=[{
                    "timestamp": timestamp,
                    "user_query": user_query,
                    "type": "conversation"
                }]
            )
            
            print(f"Stored conversation: {user_query[:50]}...")
        except Exception as e:
            print(f"Error storing conversation: {e}")
    
    def add_knowledge(self, text, metadata=None):
        """
        Add knowledge/document to RAG collection
        
        Args:
            text: Text content to store
            metadata: Optional metadata dictionary
        """
        try:
            doc_id = f"doc_{datetime.now().timestamp()}"
            meta = metadata or {}
            meta["type"] = "knowledge"
            meta["timestamp"] = datetime.now().isoformat()
            
            self.collection.add(
                documents=[text],
                ids=[doc_id],
                metadatas=[meta]
            )
            
            print(f"Stored knowledge document")
        except Exception as e:
            print(f"Error storing knowledge: {e}")
    
    def retrieve_context(self, query, n_results=3):
        """
        Retrieve relevant context from ChromaDB using similarity search
        
        Args:
            query: Search query text
            n_results: Number of results to return
            
        Returns:
            list: List of relevant documents/metadata
        """
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            if results['documents'] and len(results['documents'][0]) > 0:
                contexts = []
                for i, doc in enumerate(results['documents'][0]):
                    contexts.append({
                        'text': doc,
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'distance': results['distances'][0][i] if results['distances'] else None
                    })
                return contexts
            else:
                return []
        except Exception as e:
            print(f"Error retrieving context: {e}")
            return []
    
    def get_recent_conversations(self, n=5):
        """
        Get recent conversation history
        
        Args:
            n: Number of recent conversations to retrieve
            
        Returns:
            list: List of recent conversation texts
        """
        try:
            # Query all conversations
            results = self.collection.get(
                where={"type": "conversation"},
                limit=n,
                include=["documents", "metadatas"]
            )
            
            if results['ids']:
                conversations = []
                for i, doc in enumerate(results['documents']):
                    conversations.append({
                        'text': doc,
                        'metadata': results['metadatas'][i] if results['metadatas'] else {}
                    })
                # Sort by timestamp (most recent first)
                conversations.sort(key=lambda x: x['metadata'].get('timestamp', ''), reverse=True)
                return conversations
            else:
                return []
        except Exception as e:
            print(f"Error retrieving recent conversations: {e}")
            return []
    
    def build_rag_prompt(self, user_query):
        """
        Build a RAG-enhanced prompt with retrieved context
        
        Args:
            user_query: User's query
            
        Returns:
            str: Enhanced prompt with context
        """
        # Retrieve relevant context
        contexts = self.retrieve_context(user_query, n_results=3)
        
        # Get recent conversation history
        recent_conv = self.get_recent_conversations(n=3)
        
        # Build prompt
        prompt_parts = []
        
        # Add system context
        prompt_parts.append("You are a helpful AI assistant running on a Raspberry Pi.")
        
        # Add retrieved context if available
        if contexts:
            prompt_parts.append("\nRelevant context from previous conversations:")
            for ctx in contexts:
                prompt_parts.append(f"- {ctx['text'][:200]}...")
        
        # Add recent conversation history
        if recent_conv:
            prompt_parts.append("\nRecent conversation history:")
            for conv in recent_conv:
                prompt_parts.append(f"- {conv['text'][:200]}...")
        
        # Add current query
        prompt_parts.append(f"\nUser: {user_query}")
        prompt_parts.append("Assistant:")
        
        return "\n".join(prompt_parts)
    
    def cleanup(self):
        """Cleanup resources (ChromaDB is persistent, no cleanup needed)"""
        pass

