"""RAG (Retrieval-Augmented Generation) service for chatbot."""

import re
from typing import Any, Dict, List, Optional

from app.core.logging import get_logger
from app.services.llm import call_llm
from app.services.vector_db import vector_db

logger = get_logger(__name__)


class RAGService:
    """RAG service for document processing and question answering."""
    
    def __init__(self):
        self.vector_db = vector_db
        self.max_chunk_size = 1000
        self.chunk_overlap = 200
    
    # Document upload functionality removed - using website ingestion only
    
    async def answer_question(
        self, 
        question: str, 
        context_limit: int = 5,
        temperature: float = 0.1
    ) -> Dict[str, Any]:
        """Answer a question using RAG."""
        try:
            # Retrieve relevant documents
            retrieved_docs = self.vector_db.search(
                query=question,
                n_results=context_limit
            )
            
            if not retrieved_docs:
                return {
                    "answer": "I don't have any relevant information to answer your question. Please upload some documents first.",
                    "sources": [],
                    "confidence": 0.0
                }
            
            # Prepare context
            context_parts = []
            sources = []
            
            for doc in retrieved_docs:
                context_parts.append(doc['document'])
                if doc['metadata']:
                    sources.append({
                        "upload_id": doc['metadata'].get('upload_id', 'unknown'),
                        "chunk_index": doc['metadata'].get('chunk_index', 0),
                        "relevance_score": 1.0 - doc['distance']  # Convert distance to similarity
                    })
            
            context = "\n\n".join(context_parts)
            
            # Generate answer using LLM
            system_prompt = """You are a helpful assistant that answers questions based on the provided context. 
            Use only the information from the context to answer the question. If the context doesn't contain 
            enough information to answer the question, say so clearly. Be concise but comprehensive."""
            
            user_prompt = f"""Context:
{context}

Question: {question}

Please provide a helpful answer based on the context above."""
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            # Call LLM
            response = await call_llm(messages, temperature=temperature)
            answer = response.get("content", "I couldn't generate an answer.") if isinstance(response, dict) else str(response)
            
            # Calculate confidence based on source relevance
            avg_relevance = sum(s['relevance_score'] for s in sources) / len(sources) if sources else 0.0
            
            logger.info(f"Answered question with {len(sources)} sources, avg relevance: {avg_relevance:.2f}")
            
            return {
                "answer": answer,
                "sources": sources,
                "confidence": avg_relevance,
                "context_used": len(context_parts)
            }
            
        except Exception as e:
            logger.error(f"Failed to answer question: {e}")
            return {
                "answer": "I encountered an error while processing your question. Please try again.",
                "sources": [],
                "confidence": 0.0,
                "error": str(e)
            }
    
    def _split_text_into_chunks(self, text: str) -> List[str]:
        """Split text into overlapping chunks."""
        # Clean text
        text = re.sub(r'\s+', ' ', text.strip())
        
        if len(text) <= self.max_chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.max_chunk_size
            
            if end >= len(text):
                chunks.append(text[start:])
                break
            
            # Try to break at sentence boundary
            last_period = text.rfind('.', start, end)
            last_exclamation = text.rfind('!', start, end)
            last_question = text.rfind('?', start, end)
            
            last_sentence_end = max(last_period, last_exclamation, last_question)
            
            if last_sentence_end > start + self.max_chunk_size // 2:
                end = last_sentence_end + 1
            
            chunks.append(text[start:end].strip())
            start = end - self.chunk_overlap
            
            if start < 0:
                start = end
        
        return [chunk for chunk in chunks if chunk.strip()]
    
    def get_document_stats(self) -> Dict[str, Any]:
        """Get statistics about stored documents."""
        collection_info = self.vector_db.get_collection_info()
        
        # Get all documents to analyze
        try:
            all_docs = self.vector_db.collection.get()
            upload_ids = set()
            total_chunks = 0
            
            if all_docs['metadatas']:
                for metadata in all_docs['metadatas']:
                    if metadata and 'upload_id' in metadata:
                        upload_ids.add(metadata['upload_id'])
                    total_chunks += 1
            
            return {
                "total_documents": len(upload_ids),
                "total_chunks": total_chunks,
                "collection_info": collection_info
            }
        except Exception as e:
            logger.error(f"Failed to get document stats: {e}")
            return {
                "total_documents": 0,
                "total_chunks": 0,
                "collection_info": collection_info,
                "error": str(e)
            }
    
    def clear_all_documents(self) -> bool:
        """Clear all documents from the RAG system."""
        return self.vector_db.clear_collection()


# Global RAG service instance
rag_service = RAGService()
