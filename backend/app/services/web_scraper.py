"""Web scraping service for extracting content from websites."""

import re
import time
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.core.logging import get_logger

logger = get_logger(__name__)


class WebScraper:
    """Web scraper for extracting content from websites."""
    
    def __init__(self, max_pages: int = 50, delay: float = 1.0):
        self.max_pages = max_pages
        self.delay = delay
        self.session = self._create_session()
        self.visited_urls: Set[str] = set()
        
        # Common content selectors
        self.content_selectors = [
            'article', 'main', '.content', '.post', '.entry',
            'section', '.article-content', '.post-content',
            '.entry-content', '.page-content', '.text-content'
        ]
        
        # Elements to remove
        self.remove_selectors = [
            'nav', 'header', 'footer', '.nav', '.navigation',
            '.sidebar', '.menu', '.advertisement', '.ads',
            'script', 'style', '.social', '.share', '.comments'
        ]
    
    def _create_session(self) -> requests.Session:
        """Create a requests session with retry strategy."""
        session = requests.Session()
        
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set headers to mimic a real browser
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
        return session
    
    def extract_content_from_url(self, url: str) -> Dict[str, Any]:
        """Extract content from a single URL."""
        try:
            logger.info(f"Scraping URL: {url}")
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove unwanted elements
            for selector in self.remove_selectors:
                for element in soup.select(selector):
                    element.decompose()
            
            # Extract title
            title = self._extract_title(soup)
            
            # Extract main content
            content = self._extract_main_content(soup)
            
            # Extract metadata
            metadata = self._extract_metadata(soup, url)
            
            # Clean and process content
            cleaned_content = self._clean_content(content)
            
            if not cleaned_content or len(cleaned_content.strip()) < 100:
                logger.warning(f"Minimal content extracted from {url}")
                return {
                    "url": url,
                    "title": title,
                    "content": "",
                    "metadata": metadata,
                    "success": False,
                    "error": "Insufficient content"
                }
            
            return {
                "url": url,
                "title": title,
                "content": cleaned_content,
                "metadata": metadata,
                "success": True,
                "word_count": len(cleaned_content.split())
            }
            
        except Exception as e:
            logger.error(f"Failed to scrape {url}: {e}")
            return {
                "url": url,
                "title": "",
                "content": "",
                "metadata": {},
                "success": False,
                "error": str(e)
            }
    
    def scrape_website(self, base_url: str, max_pages: Optional[int] = None) -> List[Dict[str, Any]]:
        """Scrape multiple pages from a website."""
        if max_pages is None:
            max_pages = self.max_pages
        
        logger.info(f"Starting website scrape: {base_url} (max {max_pages} pages)")
        
        results = []
        self.visited_urls.clear()
        
        # Start with the base URL
        urls_to_visit = [base_url]
        base_domain = urlparse(base_url).netloc
        
        while urls_to_visit and len(results) < max_pages:
            current_url = urls_to_visit.pop(0)
            
            if current_url in self.visited_urls:
                continue
            
            self.visited_urls.add(current_url)
            
            # Extract content from current URL
            result = self.extract_content_from_url(current_url)
            results.append(result)
            
            if result["success"]:
                # Find additional URLs to visit
                if len(results) < max_pages:
                    additional_urls = self._extract_internal_links(
                        result["content"], current_url, base_domain
                    )
                    
                    # Add new URLs to visit queue
                    for url in additional_urls:
                        if url not in self.visited_urls and url not in urls_to_visit:
                            urls_to_visit.append(url)
            
            # Respect rate limiting
            time.sleep(self.delay)
        
        successful_scrapes = [r for r in results if r["success"]]
        logger.info(f"Scraped {len(successful_scrapes)}/{len(results)} pages from {base_url}")
        
        return results
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title."""
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text().strip()
        
        h1_tag = soup.find('h1')
        if h1_tag:
            return h1_tag.get_text().strip()
        
        return "Untitled"
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract main content from the page."""
        # Try content selectors in order of preference
        for selector in self.content_selectors:
            content_elements = soup.select(selector)
            if content_elements:
                content = ""
                for element in content_elements:
                    content += element.get_text() + "\n"
                if len(content.strip()) > 200:  # Minimum content length
                    return content
        
        # Fallback: extract all text from body
        body = soup.find('body')
        if body:
            return body.get_text()
        
        return soup.get_text()
    
    def _extract_metadata(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract metadata from the page."""
        metadata = {
            "url": url,
            "domain": urlparse(url).netloc,
            "scraped_at": time.time()
        }
        
        # Extract meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            metadata["description"] = meta_desc.get('content', '')
        
        # Extract meta keywords
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords:
            metadata["keywords"] = meta_keywords.get('content', '')
        
        # Extract headings
        headings = []
        for level in range(1, 7):
            for heading in soup.find_all(f'h{level}'):
                headings.append({
                    "level": level,
                    "text": heading.get_text().strip()
                })
        metadata["headings"] = headings
        
        return metadata
    
    def _extract_internal_links(self, content: str, current_url: str, base_domain: str) -> List[str]:
        """Extract internal links from content."""
        # This is a simplified version - in practice, you'd parse the HTML
        # For now, we'll return an empty list to avoid infinite crawling
        return []
    
    def _clean_content(self, content: str) -> str:
        """Clean and normalize extracted content."""
        if not content:
            return ""
        
        # Remove extra whitespace
        content = re.sub(r'\s+', ' ', content)
        
        # Remove common unwanted patterns
        unwanted_patterns = [
            r'Cookie\s+Policy',
            r'Privacy\s+Policy',
            r'Terms\s+of\s+Service',
            r'Subscribe\s+to\s+our\s+newsletter',
            r'Follow\s+us\s+on',
            r'Share\s+this\s+article',
        ]
        
        for pattern in unwanted_patterns:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE)
        
        # Remove very short lines (likely navigation or ads)
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if len(line) > 20:  # Keep lines with substantial content
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines).strip()


# Global web scraper instance
web_scraper = WebScraper()
