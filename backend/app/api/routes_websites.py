"""Website ingestion API routes for RAG chatbot."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, HttpUrl

from app.core.logging import get_logger
from app.services.website_ingestion import website_ingestion_service

logger = get_logger(__name__)

router = APIRouter(prefix="/v1/websites", tags=["websites"])


class WebsiteIngestRequest(BaseModel):
    """Request to ingest a single website."""
    url: HttpUrl = Field(..., description="Website URL to ingest")
    max_pages: int = Field(default=10, description="Maximum pages to scrape", ge=1, le=50)


class MultipleWebsitesIngestRequest(BaseModel):
    """Request to ingest multiple websites."""
    urls: List[HttpUrl] = Field(..., description="List of website URLs to ingest", min_items=1, max_items=10)
    max_pages_per_site: int = Field(default=10, description="Maximum pages per website", ge=1, le=50)


class WebsiteIngestResponse(BaseModel):
    """Response after ingesting a website."""
    success: bool = Field(..., description="Whether the operation was successful")
    url: str = Field(..., description="Website URL")
    pages_scraped: int = Field(..., description="Total pages scraped")
    pages_processed: int = Field(..., description="Pages successfully processed")
    chunks_added: int = Field(..., description="Number of chunks added to vector database")
    failed_pages: int = Field(..., description="Number of pages that failed to process")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class MultipleWebsitesIngestResponse(BaseModel):
    """Response after ingesting multiple websites."""
    success: bool = Field(..., description="Whether any websites were successfully ingested")
    total_sites: int = Field(..., description="Total number of websites")
    successful_sites: int = Field(..., description="Number of successfully ingested websites")
    total_pages: int = Field(..., description="Total pages processed")
    total_chunks: int = Field(..., description="Total chunks added")
    results: List[WebsiteIngestResponse] = Field(..., description="Individual website results")


class WebsiteSource(BaseModel):
    """Website source information."""
    url: str = Field(..., description="Website URL")
    domain: str = Field(..., description="Website domain")
    title: str = Field(..., description="Website title")
    chunks: int = Field(..., description="Number of chunks from this website")
    scraped_at: float = Field(..., description="Timestamp when scraped")


class WebsiteSourcesResponse(BaseModel):
    """Response containing website sources."""
    sources: List[WebsiteSource] = Field(..., description="List of website sources")
    total_sources: int = Field(..., description="Total number of website sources")
    total_chunks: int = Field(..., description="Total chunks from all websites")


@router.post("/ingest", response_model=WebsiteIngestResponse)
async def ingest_website(request: WebsiteIngestRequest) -> WebsiteIngestResponse:
    """Ingest content from a single website."""
    try:
        logger.info(f"Website ingestion request: {request.url}")
        
        result = await website_ingestion_service.ingest_website(
            url=str(request.url),
            max_pages=request.max_pages
        )
        
        response = WebsiteIngestResponse(
            success=result["success"],
            url=result["url"],
            pages_scraped=result.get("pages_scraped", 0),
            pages_processed=result.get("pages_processed", 0),
            chunks_added=result.get("chunks_added", 0),
            failed_pages=result.get("failed_pages", 0),
            error=result.get("error")
        )
        
        if result["success"]:
            logger.info(f"Website ingestion successful: {request.url}, {result['chunks_added']} chunks")
        else:
            logger.warning(f"Website ingestion failed: {request.url}, {result.get('error')}")
        
        return response
        
    except Exception as e:
        logger.error(f"Website ingestion error: {e}")
        raise HTTPException(status_code=500, detail="Failed to ingest website")


@router.post("/ingest-multiple", response_model=MultipleWebsitesIngestResponse)
async def ingest_multiple_websites(request: MultipleWebsitesIngestRequest) -> MultipleWebsitesIngestResponse:
    """Ingest content from multiple websites."""
    try:
        logger.info(f"Multiple websites ingestion request: {len(request.urls)} websites")
        
        result = await website_ingestion_service.ingest_multiple_websites(
            urls=[str(url) for url in request.urls],
            max_pages_per_site=request.max_pages_per_site
        )
        
        # Convert individual results
        individual_results = []
        for r in result["results"]:
            individual_results.append(WebsiteIngestResponse(
                success=r["success"],
                url=r["url"],
                pages_scraped=r.get("pages_scraped", 0),
                pages_processed=r.get("pages_processed", 0),
                chunks_added=r.get("chunks_added", 0),
                failed_pages=r.get("failed_pages", 0),
                error=r.get("error")
            ))
        
        response = MultipleWebsitesIngestResponse(
            success=result["success"],
            total_sites=result["total_sites"],
            successful_sites=result["successful_sites"],
            total_pages=result["total_pages"],
            total_chunks=result["total_chunks"],
            results=individual_results
        )
        
        logger.info(f"Multiple websites ingestion complete: {result['successful_sites']}/{result['total_sites']} successful")
        
        return response
        
    except Exception as e:
        logger.error(f"Multiple websites ingestion error: {e}")
        raise HTTPException(status_code=500, detail="Failed to ingest websites")


@router.get("/sources", response_model=WebsiteSourcesResponse)
async def get_website_sources() -> WebsiteSourcesResponse:
    """Get information about website sources in the system."""
    try:
        sources_data = website_ingestion_service.get_website_sources()
        
        sources = []
        total_chunks = 0
        
        for source_data in sources_data:
            sources.append(WebsiteSource(
                url=source_data["url"],
                domain=source_data["domain"],
                title=source_data["title"],
                chunks=source_data["chunks"],
                scraped_at=source_data["scraped_at"]
            ))
            total_chunks += source_data["chunks"]
        
        response = WebsiteSourcesResponse(
            sources=sources,
            total_sources=len(sources),
            total_chunks=total_chunks
        )
        
        logger.info(f"Retrieved {len(sources)} website sources with {total_chunks} total chunks")
        
        return response
        
    except Exception as e:
        logger.error(f"Failed to get website sources: {e}")
        raise HTTPException(status_code=500, detail="Failed to get website sources")


@router.delete("/sources/clear")
async def clear_website_sources() -> Dict[str, str]:
    """Clear all website sources from the system."""
    try:
        success = website_ingestion_service.clear_website_sources()
        
        if success:
            logger.info("Website sources cleared successfully")
            return {"message": "All website sources cleared successfully"}
        else:
            logger.warning("Failed to clear website sources")
            raise HTTPException(status_code=500, detail="Failed to clear website sources")
            
    except Exception as e:
        logger.error(f"Clear website sources error: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear website sources")


@router.get("/health")
async def websites_health() -> Dict[str, str]:
    """Health check for website ingestion service."""
    return {"status": "healthy", "service": "website-ingestion"}
