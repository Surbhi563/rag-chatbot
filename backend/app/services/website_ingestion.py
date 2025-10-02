"""Website ingestion service for RAG chatbot."""

import time
from typing import Any, Dict, List, Optional

from app.core.logging import get_logger
from app.services.rag_service import rag_service
from app.services.web_scraper import web_scraper

logger = get_logger(__name__)


class WebsiteIngestionService:
    """Service for ingesting website content into the RAG system."""
    
    def __init__(self):
        self.web_scraper = web_scraper
        self.rag_service = rag_service
    
    async def ingest_website(
        self, 
        url: str, 
        max_pages: int = 10,
        collection_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Ingest content from a website into the RAG system."""
        try:
            logger.info(f"Starting website ingestion: {url}")
            
            # Scrape website content
            scraped_pages = self.web_scraper.scrape_website(url, max_pages)
            
            if not scraped_pages:
                return {
                    "success": False,
                    "error": "No content scraped from website",
                    "url": url,
                    "pages_processed": 0
                }
            
            # Process and add content to RAG system
            successful_pages = [page for page in scraped_pages if page["success"]]
            total_chunks = 0
            
            for page in successful_pages:
                if page["content"]:
                    # Create chunks from the page content
                    chunks = self._create_chunks_from_content(
                        content=page["content"],
                        url=page["url"],
                        title=page["title"],
                        metadata=page["metadata"]
                    )
                    
                    if chunks:
                        # Add chunks to vector database
                        metadatas = []
                        for i, chunk in enumerate(chunks):
                            metadatas.append({
                                "source": "website",
                                "url": page["url"],
                                "title": page["title"],
                                "chunk_index": i,
                                "total_chunks": len(chunks),
                                "domain": page["metadata"].get("domain", ""),
                                "scraped_at": page["metadata"].get("scraped_at", time.time())
                            })
                        
                        # Add to vector database
                        chunk_ids = self.rag_service.vector_db.add_documents(
                            documents=chunks,
                            metadatas=metadatas
                        )
                        
                        total_chunks += len(chunks)
                        logger.info(f"Added {len(chunks)} chunks from {page['url']}")
            
            logger.info(f"Website ingestion complete: {url}, {len(successful_pages)} pages, {total_chunks} chunks")
            
            return {
                "success": True,
                "url": url,
                "pages_scraped": len(scraped_pages),
                "pages_processed": len(successful_pages),
                "chunks_added": total_chunks,
                "failed_pages": len(scraped_pages) - len(successful_pages)
            }
            
        except Exception as e:
            logger.error(f"Website ingestion failed for {url}: {e}")
            return {
                "success": False,
                "error": str(e),
                "url": url,
                "pages_processed": 0
            }
    
    async def ingest_multiple_websites(
        self, 
        urls: List[str], 
        max_pages_per_site: int = 10
    ) -> Dict[str, Any]:
        """Ingest content from multiple websites."""
        results = []
        total_chunks = 0
        total_pages = 0
        
        for url in urls:
            result = await self.ingest_website(url, max_pages_per_site)
            results.append(result)
            
            if result["success"]:
                total_chunks += result["chunks_added"]
                total_pages += result["pages_processed"]
        
        successful_sites = [r for r in results if r["success"]]
        
        return {
            "success": len(successful_sites) > 0,
            "total_sites": len(urls),
            "successful_sites": len(successful_sites),
            "total_pages": total_pages,
            "total_chunks": total_chunks,
            "results": results
        }
    
    def _create_chunks_from_content(
        self, 
        content: str, 
        url: str, 
        title: str, 
        metadata: Dict[str, Any]
    ) -> List[str]:
        """Create chunks from website content."""
        if not content or len(content.strip()) < 100:
            return []
        
        # Use the same chunking logic as the RAG service
        chunks = self.rag_service._split_text_into_chunks(content)
        
        # Add context to each chunk
        enhanced_chunks = []
        for i, chunk in enumerate(chunks):
            # Add title and URL context to the beginning of each chunk
            enhanced_chunk = f"Source: {title}\nURL: {url}\n\n{chunk}"
            enhanced_chunks.append(enhanced_chunk)
        
        return enhanced_chunks
    
    def get_website_sources(self) -> List[Dict[str, Any]]:
        """Get information about website sources in the vector database."""
        try:
            # Get all documents from the vector database
            all_docs = self.rag_service.vector_db.collection.get()
            
            if not all_docs['metadatas']:
                return []
            
            # Group by website source
            website_sources = {}
            
            for i, metadata in enumerate(all_docs['metadatas']):
                if metadata and metadata.get('source') == 'website':
                    url = metadata.get('url', 'Unknown')
                    domain = metadata.get('domain', 'Unknown')
                    
                    if url not in website_sources:
                        website_sources[url] = {
                            "url": url,
                            "domain": domain,
                            "title": metadata.get('title', 'Unknown'),
                            "chunks": 0,
                            "scraped_at": metadata.get('scraped_at', 0)
                        }
                    
                    website_sources[url]["chunks"] += 1
            
            # Convert to list and sort by scraped_at
            sources = list(website_sources.values())
            sources.sort(key=lambda x: x["scraped_at"], reverse=True)
            
            return sources
            
        except Exception as e:
            logger.error(f"Failed to get website sources: {e}")
            return []
    
    def clear_website_sources(self) -> bool:
        """Clear all website sources from the vector database."""
        try:
            # Get all documents
            all_docs = self.rag_service.vector_db.collection.get()
            
            if not all_docs['ids']:
                return True
            
            # Find IDs of website sources
            website_ids = []
            for i, metadata in enumerate(all_docs['metadatas']):
                if metadata and metadata.get('source') == 'website':
                    website_ids.append(all_docs['ids'][i])
            
            if website_ids:
                # Delete website sources
                self.rag_service.vector_db.delete_documents(website_ids)
                logger.info(f"Cleared {len(website_ids)} website source chunks")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear website sources: {e}")
            return False


# Global website ingestion service instance
website_ingestion_service = WebsiteIngestionService()
