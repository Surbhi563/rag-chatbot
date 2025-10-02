"""Chat API routes for RAG chatbot."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.logging import get_logger
from app.services.rag_service import rag_service

logger = get_logger(__name__)

router = APIRouter(prefix="/v1/chat", tags=["chat"])


class ChatMessage(BaseModel):
    """Chat message model."""
    role: str = Field(..., description="Message role: user, assistant, or system")
    content: str = Field(..., description="Message content")
    timestamp: Optional[str] = Field(default=None, description="Message timestamp")


class ChatRequest(BaseModel):
    """Chat request model."""
    message: str = Field(..., description="User message", max_length=2000)
    context_limit: int = Field(default=5, description="Number of context documents to retrieve", ge=1, le=10)
    temperature: float = Field(default=0.1, description="LLM temperature", ge=0.0, le=2.0)
    conversation_id: Optional[str] = Field(default=None, description="Conversation ID for context")


class ChatResponse(BaseModel):
    """Chat response model."""
    answer: str = Field(..., description="Assistant's response")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="Source documents used")
    confidence: float = Field(..., description="Confidence score (0-1)")
    context_used: int = Field(..., description="Number of context documents used")
    conversation_id: Optional[str] = Field(default=None, description="Conversation ID")


class DocumentAddRequest(BaseModel):
    """Request to add document to RAG system."""
    upload_id: str = Field(..., description="Upload ID of the document to add")


class DocumentAddResponse(BaseModel):
    """Response after adding document."""
    success: bool = Field(..., description="Whether the operation was successful")
    upload_id: str = Field(..., description="Upload ID")
    chunks_added: int = Field(..., description="Number of chunks added")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class DocumentStatsResponse(BaseModel):
    """Document statistics response."""
    total_documents: int = Field(..., description="Total number of documents")
    total_chunks: int = Field(..., description="Total number of chunks")
    collection_info: Dict[str, Any] = Field(..., description="Collection information")


@router.post("/message", response_model=ChatResponse)
async def chat_message(request: ChatRequest) -> ChatResponse:
    """Send a message to the chatbot and get a response."""
    try:
        logger.info("chat_message_request", message_length=len(request.message))
        
        # Get answer from RAG service
        result = await rag_service.answer_question(
            question=request.message,
            context_limit=request.context_limit,
            temperature=request.temperature
        )
        
        response = ChatResponse(
            answer=result["answer"],
            sources=result.get("sources", []),
            confidence=result.get("confidence", 0.0),
            context_used=result.get("context_used", 0),
            conversation_id=request.conversation_id
        )
        
        logger.info(
            "chat_message_response",
            answer_length=len(response.answer),
            sources_count=len(response.sources),
            confidence=response.confidence
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Chat message error: {e}")
        raise HTTPException(status_code=500, detail="Failed to process chat message")


@router.post("/documents/add", response_model=DocumentAddResponse)
async def add_document(request: DocumentAddRequest) -> DocumentAddResponse:
    """Add a document to the RAG system."""
    try:
        logger.info("add_document_request", upload_id=request.upload_id)
        
        result = await rag_service.add_document(request.upload_id)
        
        if result["success"]:
            response = DocumentAddResponse(
                success=True,
                upload_id=result["upload_id"],
                chunks_added=result["chunks_added"]
            )
            logger.info("add_document_success", upload_id=request.upload_id, chunks=result["chunks_added"])
        else:
            response = DocumentAddResponse(
                success=False,
                upload_id=request.upload_id,
                chunks_added=0,
                error=result.get("error", "Unknown error")
            )
            logger.warning("add_document_failed", upload_id=request.upload_id, error=result.get("error"))
        
        return response
        
    except Exception as e:
        logger.error(f"Add document error: {e}")
        raise HTTPException(status_code=500, detail="Failed to add document")


@router.get("/documents/stats", response_model=DocumentStatsResponse)
async def get_document_stats() -> DocumentStatsResponse:
    """Get statistics about stored documents."""
    try:
        stats = rag_service.get_document_stats()
        
        response = DocumentStatsResponse(
            total_documents=stats["total_documents"],
            total_chunks=stats["total_chunks"],
            collection_info=stats["collection_info"]
        )
        
        logger.info("document_stats", **stats)
        return response
        
    except Exception as e:
        logger.error(f"Document stats error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get document statistics")


@router.delete("/documents/clear")
async def clear_all_documents() -> Dict[str, str]:
    """Clear all documents from the RAG system."""
    try:
        success = rag_service.clear_all_documents()
        
        if success:
            logger.info("documents_cleared")
            return {"message": "All documents cleared successfully"}
        else:
            logger.warning("documents_clear_failed")
            raise HTTPException(status_code=500, detail="Failed to clear documents")
            
    except Exception as e:
        logger.error(f"Clear documents error: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear documents")


@router.get("/health")
async def chat_health() -> Dict[str, str]:
    """Health check for chat service."""
    return {"status": "healthy", "service": "chat"}
