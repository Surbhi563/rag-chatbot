"""Vector database service for RAG chatbot."""

import uuid
from typing import Any, Dict, List, Optional, Tuple

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class VectorDB:
    """ChromaDB-based vector database for document storage and retrieval."""
    
    def __init__(self, collection_name: str = "documents"):
        self.collection_name = collection_name
        # Initialize embedding model with reduced memory usage
        self.embedding_model = SentenceTransformer(
            'all-MiniLM-L6-v2',
            device=settings.embedding_device,  # Use configurable device
            trust_remote_code=True
        )
        
        # Initialize ChromaDB
        db_path = settings.vector_db_path or (settings.local_bucket_dir + "/chroma_db")
        self.client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(name=collection_name)
            logger.info(f"Loaded existing collection: {collection_name}")
        except Exception:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"description": "RAG chatbot document collection"}
            )
            logger.info(f"Created new collection: {collection_name}")
    
    def add_documents(
        self, 
        documents: List[str], 
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """Add documents to the vector database."""
        if not documents:
            return []
        
        # Generate IDs if not provided
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in documents]
        
        # Generate embeddings with memory optimization
        embeddings = self.embedding_model.encode(
            documents, 
            batch_size=settings.max_batch_size,  # Use configurable batch size
            show_progress_bar=True
        ).tolist()
        
        # Prepare metadatas
        if metadatas is None:
            metadatas = [{"source": "upload"} for _ in documents]
        
        # Add to collection
        self.collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        
        logger.info(f"Added {len(documents)} documents to vector database")
        return ids
    
    def search(
        self, 
        query: str, 
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar documents."""
        # Generate query embedding with memory optimization
        query_embedding = self.embedding_model.encode(
            [query], 
            batch_size=1,  # Process one at a time to reduce memory
            show_progress_bar=False
        ).tolist()[0]
        
        # Search collection
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where
        )
        
        # Format results
        formatted_results = []
        if results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                formatted_results.append({
                    'document': doc,
                    'metadata': results['metadatas'][0][i] if results['metadatas'] and results['metadatas'][0] else {},
                    'distance': results['distances'][0][i] if results['distances'] and results['distances'][0] else 0.0,
                    'id': results['ids'][0][i] if results['ids'] and results['ids'][0] else None
                })
        
        logger.info(f"Found {len(formatted_results)} similar documents for query")
        return formatted_results
    
    def delete_documents(self, ids: List[str]) -> bool:
        """Delete documents by IDs."""
        try:
            self.collection.delete(ids=ids)
            logger.info(f"Deleted {len(ids)} documents from vector database")
            return True
        except Exception as e:
            logger.error(f"Failed to delete documents: {e}")
            return False
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get collection statistics."""
        count = self.collection.count()
        return {
            "collection_name": self.collection_name,
            "document_count": count,
            "embedding_model": "all-MiniLM-L6-v2"
        }
    
    def clear_collection(self) -> bool:
        """Clear all documents from the collection."""
        try:
            # Get all IDs
            all_docs = self.collection.get()
            if all_docs['ids']:
                self.collection.delete(ids=all_docs['ids'])
                logger.info("Cleared all documents from vector database")
            return True
        except Exception as e:
            logger.error(f"Failed to clear collection: {e}")
            return False


# Global vector database instance
vector_db = VectorDB()
