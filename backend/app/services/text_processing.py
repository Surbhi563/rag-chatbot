"""Text chunking and snippet selection utilities for evidence-based taxonomy generation."""

import re
from typing import Any, Dict, List


def chunk_text(text: str, max_chars: int = 800, overlap: int = 120) -> List[str]:
    """Split text into overlapping chunks of roughly max_chars."""
    if not text or len(text) <= max_chars:
        return [text] if text else []
    
    chunks = []
    start = 0
    while start < len(text):
        end = start + max_chars
        if end >= len(text):
            chunks.append(text[start:])
            break
        
        # Try to break at sentence or paragraph boundary
        chunk_text = text[start:end]
        last_period = chunk_text.rfind('.')
        last_newline = chunk_text.rfind('\n')
        
        if last_period > start + max_chars // 2:
            end = start + last_period + 1
        elif last_newline > start + max_chars // 2:
            end = start + last_newline + 1
        
        chunks.append(text[start:end])
        start = max(start + 1, end - overlap)  # Overlap for context
    
    return chunks


def build_snippets(user_text: str, additional_passages: List[str] = None, max_chars: int = 800) -> List[Dict[str, Any]]:
    """Build indexed snippets from user uploads and optional additional content.
    
    Args:
        user_text: Text extracted from user uploaded files
        additional_passages: Optional additional text passages (e.g. from external sources)
        max_chars: Maximum characters per snippet
        
    Returns:
        List of snippet dictionaries with id, text, and source fields
    """
    snippets = []
    additional_passages = additional_passages or []
    
    # Chunk user uploads
    if user_text:
        chunks = chunk_text(user_text, max_chars=max_chars, overlap=120)
        for i, chunk in enumerate(chunks):
            snippets.append({
                "id": f"S{i+1}",
                "text": chunk.strip(),
                "source": "user_upload"
            })
    
    # Add additional passages if provided
    base_id = len(snippets)
    for j, passage in enumerate(additional_passages, 1):
        if passage and passage.strip():
            snippets.append({
                "id": f"S{base_id+j}",
                "text": passage.strip()[:max_chars],  # Truncate if needed
                "source": "additional"
            })
    
    return snippets


def select_prompt_snippets(snippets: List[Dict[str, Any]], limit: int = 12, topics: List[str] = None) -> List[Dict[str, Any]]:
    """Select snippets to include in LLM prompt, prioritizing topic-relevant content.
    
    Args:
        snippets: List of snippet dictionaries
        limit: Maximum number of snippets to return
        topics: Optional list of topics for relevance scoring
        
    Returns:
        Selected snippets ordered by relevance score
    """
    if not topics or not snippets:
        return snippets[:limit]
    
    # Create topic keywords for relevance scoring
    topic_keywords = set()
    for topic in topics:
        # Extract keywords from topics
        words = topic.lower().replace('-', ' ').replace('_', ' ').split()
        topic_keywords.update(word for word in words if len(word) > 2)
    
    # Score snippets by topic relevance
    scored_snippets = []
    for snippet in snippets:
        text_lower = snippet['text'].lower()
        
        # Count topic keyword matches
        keyword_score = sum(1 for keyword in topic_keywords if keyword in text_lower)
        
        # Bonus for exact topic matches
        exact_matches = sum(1 for topic in topics if topic.lower() in text_lower)
        
        total_score = keyword_score + (exact_matches * 3)  # Weight exact matches higher
        scored_snippets.append((total_score, snippet))
    
    # Sort by relevance score (descending) and take top N
    scored_snippets.sort(key=lambda x: x[0], reverse=True)
    selected = [snippet for score, snippet in scored_snippets[:limit]]
    
    # If we don't have enough high-scoring snippets, fill with remaining ones
    if len(selected) < limit:
        remaining = [s for s in snippets if s not in selected]
        selected.extend(remaining[:limit - len(selected)])
    
    return selected
