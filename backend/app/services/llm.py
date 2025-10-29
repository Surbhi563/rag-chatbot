"""LLM adapter with deterministic dev mock."""

import json
import random
import time
from typing import Any, Dict, List, Optional

import httpx
from fastapi import HTTPException

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def _parse_json_object_from_content(content: str) -> Dict[str, Any]:
    """Parse JSON from LLM content, handling markdown fences and malformed JSON."""
    text = str(content).strip()
    
    # Strip Markdown fences if present
    if text.startswith("```"):
        # remove leading ```... and trailing ```
        first_newline = text.find("\n")
        if first_newline != -1:
            text = text[first_newline + 1 :]
        if text.endswith("```"):
            text = text[: -3]
        text = text.strip()
    
    # Try direct JSON parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Fallback: find first balanced JSON object
    start = text.find("{")
    if start == -1:
        return {"nodes": []}
    
    depth = 0
    for i in range(start, len(text)):
        ch = text[i]
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start : i + 1])
                except json.JSONDecodeError:
                    pass
    
    return {"nodes": []}


def _convert_hierarchical_to_flat(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Convert LLM's hierarchical format to flat nodes array."""
    flat_nodes = []
    
    def extract_node(node_data: Dict[str, Any], parent_temp_id: Optional[str] = None, depth: int = 1) -> None:
        # Extract node info
        label = node_data.get("name", node_data.get("label", ""))
        if not label:
            return
            
        temp_id = f"n{len(flat_nodes) + 1}"
        evidence_ids = node_data.get("evidence_ids", [])
        
        # Add to flat list
        flat_nodes.append({
            "temp_id": temp_id,
            "label": label,
            "parent_temp_id": parent_temp_id,
            "depth": depth,
            "evidence_ids": evidence_ids
        })
        
        # Process children recursively
        children = node_data.get("children", [])
        for child in children:
            extract_node(child, temp_id, depth + 1)
    
    # Start conversion
    extract_node(data)
    return flat_nodes


async def _call_openai_api(
    messages: List[Dict[str, str]],
    response_format: Optional[Dict[str, Any]] = None,
    temperature: float = 0.2,
) -> Dict[str, Any]:
    """Call OpenAI API for LLM completion."""
    
    # Determine model name - use configured model or default
    model_name = settings.llm_default_model if settings.llm_default_model else "gpt-3.5-turbo"
    
    # Construct OpenAI URL
    base_url = settings.llm_base_url.rstrip('/') if settings.llm_base_url else "https://api.openai.com/v1"
    if not base_url.endswith('/v1'):
        base_url = f"{base_url}/v1" if not base_url.endswith('/') else f"{base_url}v1"
    
    url = f"{base_url}/chat/completions"
    
    # Build payload for OpenAI API
    payload: Dict[str, Any] = {
        "model": model_name,
        "messages": messages,
        "temperature": settings.llm_default_temperature if settings.llm_default_temperature is not None else temperature,
        "max_tokens": settings.llm_default_max_tokens if settings.llm_default_max_tokens is not None else 2000,
    }
    
    if response_format:
        payload["response_format"] = response_format
    
    # Headers with API key
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.llm_api_key}",
    }
    
    logger.info("OpenAI API request",
                url=url,
                model=model_name,
                message_count=len(messages),
                has_response_format=response_format is not None,
                max_tokens=payload.get("max_tokens"))
    
    # Make request with retry logic
    timeout = httpx.Timeout(connect=30, read=90, write=30, pool=None)
    async with httpx.AsyncClient(timeout=timeout) as client:
        import asyncio as _asyncio
        
        max_retries = 3
        retry_delays = [2, 5, 10]
        
        for attempt in range(max_retries):
            try:
                resp = await client.post(url, json=payload, headers=headers)
                
                # Handle rate limiting (429) with exponential backoff
                if resp.status_code == 429:
                    if attempt < max_retries - 1:
                        delay = retry_delays[attempt]
                        logger.warning("OpenAI rate limited, retrying",
                                     attempt=attempt + 1,
                                     delay=delay)
                        await _asyncio.sleep(delay)
                        continue
                    else:
                        error_detail = resp.json().get("error", {}).get("message", "Rate limit exceeded") if resp.headers.get("content-type", "").startswith("application/json") else resp.text[:200]
                        raise HTTPException(
                            status_code=429,
                            detail=f"OpenAI API rate limit exceeded. Please try again in a moment. Error: {error_detail}"
                        )
                
                # Handle other errors
                if resp.status_code not in (200, 201):
                    try:
                        error_json = resp.json()
                        error_msg = error_json.get("error", {}).get("message", "Unknown error")
                    except:
                        error_msg = resp.text[:200] if resp.text else "Unknown error"
                    
                    logger.error("OpenAI API error",
                               status_code=resp.status_code,
                               error=error_msg,
                               model=model_name)
                    
                    raise HTTPException(
                        status_code=502,
                        detail=f"OpenAI API error: {error_msg}"
                    )
                
                # Success - parse response
                break
                
            except HTTPException:
                raise
            except Exception as exc:
                if attempt < max_retries - 1:
                    delay = retry_delays[attempt]
                    logger.warning("OpenAI request failed, retrying",
                                 error=str(exc),
                                 attempt=attempt + 1,
                                 delay=delay)
                    await _asyncio.sleep(delay)
                    continue
                else:
                    logger.error("OpenAI request failed after retries",
                               error=str(exc),
                               url=url)
                    raise HTTPException(status_code=502, detail=f"OpenAI API request failed: {str(exc)}")
        
        # Parse response
        try:
            response_json = resp.json()
        except (json.JSONDecodeError, ValueError) as json_exc:
            logger.error("OpenAI response is not valid JSON",
                        error=str(json_exc),
                        response_preview=resp.text[:500])
            raise HTTPException(status_code=502, detail="OpenAI returned invalid response format")
        
        # Extract content from OpenAI response
        try:
            choices = response_json.get("choices", [])
            if not choices:
                logger.error("OpenAI returned no choices",
                            response=response_json)
                raise HTTPException(status_code=502, detail="OpenAI returned no response choices")
            
            message = choices[0].get("message", {})
            content = message.get("content", "")
            
            if not content or content.strip() == "":
                logger.error("OpenAI returned empty content",
                            response=response_json)
                return {"content": "I don't have enough information to answer your question."}
            
            # For RAG chatbot, return content directly
            # If response_format requested JSON, parse it
            if response_format and response_format.get("type") == "json_object":
                parsed = _parse_json_object_from_content(content)
                if "nodes" in parsed:
                    return {"nodes": parsed.get("nodes", [])}
            
            return {"content": content}
            
        except (KeyError, TypeError) as exc:
            logger.error("OpenAI response parse error",
                        error=str(exc),
                        response_preview=json.dumps(response_json)[:800])
            raise HTTPException(status_code=502, detail=f"Failed to parse OpenAI response: {str(exc)}")


async def call_llm(
    messages: List[Dict[str, str]],
    response_format: Optional[Dict[str, Any]] = None,
    temperature: float = 0.2,
) -> Dict[str, Any]:
    """Call configured LLM endpoint or return mock in dev when not configured."""

    if not settings.llm_base_url:
        # Return a mocked response envelope with nodes derived from input
        # Extract any topical seeds from messages for determinism
        seed_labels: List[str] = []
        for m in messages:
            content = (m.get("content") or "").lower()
            for line in content.splitlines():
                if line.startswith("- "):
                    seed_labels.append(line[2:].strip())
        if not seed_labels:
            seed_labels = ["Root Topic"]

        # Build a tiny tree up to depth 3 deterministically
        random.seed(42)
        nodes: List[Dict[str, Any]] = []
        for i, root in enumerate(seed_labels[:3], start=1):
            root_id = f"r{i}"
            nodes.append({"temp_id": root_id, "label": root, "parent_temp_id": None, "depth": 1})
            # two children each
            for c in range(2):
                child_label = f"{root} Child {c+1}"
                cid = f"{root_id}-c{c+1}"
                nodes.append({"temp_id": cid, "label": child_label, "parent_temp_id": root_id, "depth": 2})
                # grandchild
                gc_label = f"{child_label} Subtopic"
                gid = f"{cid}-g1"
                nodes.append({"temp_id": gid, "label": gc_label, "parent_temp_id": cid, "depth": 3})
        return {"nodes": nodes}

    # Determine provider based on URL or provider setting
    base_url = settings.llm_base_url.lower() if settings.llm_base_url else ""
    provider = (settings.llm_default_provider or "").lower()
    
    # Detect OpenAI: URL contains "openai.com" OR provider is "openai" OR has API key but no Ollama URL pattern
    is_openai = (
        "openai.com" in base_url or 
        provider == "openai" or
        (settings.llm_api_key and settings.llm_base_url and "openai.com" in base_url)
    )
    
    # OpenAI API call (if configured)
    if is_openai and settings.llm_api_key:
        return await _call_openai_api(messages, response_format, temperature)
    
    # Ollama API call (default)
    headers = {
        "Content-Type": "application/json"
    }
    
    # Convert messages to prompt format for Ollama
    prompt_parts = []
    for message in messages:
        role = message.get("role", "user")
        content = message.get("content", "")
        if role == "system":
            prompt_parts.append(f"System: {content}")
        elif role == "user":
            prompt_parts.append(f"Human: {content}")
        elif role == "assistant":
            prompt_parts.append(f"Assistant: {content}")
    
    prompt = "\n\n".join(prompt_parts) + "\n\nAssistant:"
    
    # Determine model name - use configured model or default
    model_name = settings.llm_default_model if settings.llm_default_model else "llama3.2:3b"
    
    # Build payload for Ollama API
    payload: Dict[str, Any] = {
        "model": model_name,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": settings.llm_default_temperature if settings.llm_default_temperature is not None else temperature,
            "num_predict": settings.llm_default_max_tokens if settings.llm_default_max_tokens is not None else 2000
        }
    }

    # Construct Ollama URL - handle cases where base_url might already include /api/generate
    if settings.llm_base_url:
        base_url = settings.llm_base_url.rstrip('/')
        # If base_url already includes /api/generate, use it as-is, otherwise append it
        if '/api/generate' in base_url:
            ollama_url = base_url
        else:
            ollama_url = f"{base_url}/api/generate"
    else:
        ollama_url = "http://localhost:11434/api/generate"
    
    # Debug logging for request
    logger.info("LLM gateway request", 
                url=ollama_url,
                model=payload.get("model"),
                message_count=len(messages),
                has_response_format=response_format is not None,
                max_tokens=payload.get("options", {}).get("num_predict"),
                system_msg_length=len(messages[0]["content"]) if messages else 0,
                user_msg_length=len(messages[1]["content"]) if len(messages) > 1 else 0)

    # Set sane timeouts with retry logic for transient errors
    timeout = httpx.Timeout(connect=30, read=90, write=30, pool=None)
    async with httpx.AsyncClient(timeout=timeout) as client:
        # Use the constructed URL
        url = ollama_url
        import asyncio as _asyncio
        
        max_retries = 3
        retry_delays = [2, 5, 10]  # Exponential backoff: 2s, 5s, 10s
        
        for attempt in range(max_retries):
            try:
                resp = await client.post(url, json=payload, headers=headers)
                
                # Handle rate limiting (429) with exponential backoff
                if resp.status_code == 429:
                    if attempt < max_retries - 1:
                        delay = retry_delays[attempt]
                        logger.warning(
                            "LLM rate limited, retrying",
                            attempt=attempt + 1,
                            max_retries=max_retries,
                            delay=delay,
                            url=url
                        )
                        await _asyncio.sleep(delay)
                        continue
                    else:
                        # Last attempt failed
                        error_detail = resp.json().get("error", {}).get("message", "Rate limit exceeded") if resp.headers.get("content-type", "").startswith("application/json") else resp.text[:200]
                        logger.error(
                            "LLM rate limit error after retries",
                            status_code=429,
                            url=url,
                            model=payload.get("model"),
                            error_detail=error_detail
                        )
                        raise HTTPException(
                            status_code=429,
                            detail=f"LLM service rate limit exceeded. Please try again in a moment. Error: {error_detail}"
                        )
                
                # Handle other transient errors (5xx)
                if resp.status_code in (500, 502, 503, 504):
                    if attempt < max_retries - 1:
                        delay = retry_delays[attempt]
                        logger.warning(
                            "LLM service error, retrying",
                            status_code=resp.status_code,
                            attempt=attempt + 1,
                            delay=delay,
                            url=url
                        )
                        await _asyncio.sleep(delay)
                        continue
                    else:
                        logger.error(
                            "LLM gateway error after retries",
                            status_code=resp.status_code,
                            url=url,
                            model=payload.get("model"),
                            body_preview=resp.text[:500],
                        )
                        raise HTTPException(status_code=502, detail=f"LLM gateway error {resp.status_code}: Service temporarily unavailable")
                
                # Handle 404 - endpoint not found or model not found
                if resp.status_code == 404:
                    # Try to parse error response to see if it's a model error
                    try:
                        error_json = resp.json()
                        if "error" in error_json and ("model" in str(error_json.get("error", "")).lower() or "not found" in str(error_json.get("error", "")).lower()):
                            error_msg = error_json.get("error", "Model not found")
                            logger.error(
                                "LLM model not found",
                                status_code=404,
                                url=url,
                                model=payload.get("model"),
                                error=error_msg,
                            )
                            raise HTTPException(
                                status_code=404,
                                detail=f"Model not available: {error_msg}. The Ollama service may need to pull the model first. Please check Ollama service logs on Render."
                            )
                    except (json.JSONDecodeError, ValueError):
                        pass
                    
                    # Generic 404 - endpoint not found
                    logger.error(
                        "LLM gateway 404 error - endpoint not found",
                        status_code=404,
                        url=url,
                        model=payload.get("model"),
                        body_preview=resp.text[:500],
                    )
                    raise HTTPException(
                        status_code=404,
                        detail=f"LLM endpoint not found at {url}. Please check LLM_BASE_URL configuration. Ollama service may not be accessible or path is incorrect."
                    )
                
                # Success or other errors
                if resp.status_code not in (200, 201):
                    logger.error(
                        "LLM gateway error",
                        status_code=resp.status_code,
                        url=url,
                        model=payload.get("model"),
                        body_preview=resp.text[:500],
                    )
                    raise HTTPException(status_code=502, detail=f"LLM gateway error {resp.status_code}: {resp.text[:200] if resp.text else 'Unknown error'}")
                
                # Success - break out of retry loop
                break
                
            except HTTPException:
                # Don't retry HTTPExceptions, just raise them
                raise
            except Exception as exc:
                if attempt < max_retries - 1:
                    delay = retry_delays[attempt]
                    logger.warning(
                        "LLM request failed, retrying",
                        error=str(exc),
                        attempt=attempt + 1,
                        delay=delay,
                        url=url
                    )
                    await _asyncio.sleep(delay)
                    continue
                else:
                    logger.error("LLM request failed after retries", error=str(exc), url=url)
                    raise HTTPException(status_code=502, detail=f"LLM request failed: {str(exc)}")

        # Parse JSON response with error handling
        try:
            raw_response_json = resp.json()
        except (json.JSONDecodeError, ValueError) as json_exc:
            logger.error("LLM response is not valid JSON", 
                        error=str(json_exc), 
                        url=url,
                        status_code=resp.status_code,
                        response_preview=resp.text[:500])
            raise HTTPException(status_code=502, detail="LLM returned invalid response format")
        
        # Check for Ollama error responses (model not found, etc.)
        if "error" in raw_response_json:
            error_msg = raw_response_json.get("error", "Unknown error")
            logger.error("LLM service returned error", 
                        error=error_msg,
                        url=url,
                        model=payload.get("model"),
                        response=raw_response_json)
            
            # Special handling for model not found
            if "not found" in str(error_msg).lower() or "model" in str(error_msg).lower():
                raise HTTPException(
                    status_code=404,
                    detail=f"Model not available: {error_msg}. The Ollama service may need to pull the model first. Please check Ollama service logs."
                )
            else:
                raise HTTPException(
                    status_code=502,
                    detail=f"LLM service error: {error_msg}"
                )
        
        # Ollama API response format
        try:
            content = raw_response_json.get("response", "")
                
            # Check if content is empty
            if not content or content.strip() == "":
                logger.error("LLM returned empty content", 
                            url=url, 
                            model=payload.get("model"),
                            data_preview=json.dumps(raw_response_json)[:800])
                return {"content": "I don't have enough information to answer your question."}
                
        except (KeyError, TypeError) as exc:
            logger.error("LLM response parse error: missing response", 
                        error=str(exc), url=url, 
                        data_preview=json.dumps(raw_response_json)[:800])
            return {"content": "I encountered an error processing your request."}
        
        # For RAG chatbot, return the content directly
        return {"content": content}


async def llm_propose(req, shown_snippets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Build evidence-based prompt requiring citations per node."""

    # Build focused system prompt that forces user topics as roots
    if req.topics and len(req.topics) > 0:
        main_topics = req.topics
        system = f"""You are an expert ontology editor creating detailed domain taxonomies.

CRITICAL REQUIREMENT: Start with "{main_topics[0]}" as your L1 root node. Do NOT create a broader category above it.

Your task:
- L1 root: "{main_topics[0]}" 
- L2 children: Major subcategories within {main_topics[0]}
- L3+ children: Specific techniques, methods, algorithms, applications within each L2
- Include EVERY specific technique mentioned in the content snippets

Constraints:
- Depth ≤ {req.max_depth}, children ≤ {req.max_children} per node
- Use clear noun phrases (Title Case), ensure MECE siblings
- Include evidence_ids from relevant snippets for each node  
- Create separate nodes for each major concept mentioned (don't group under generic names)

Return STRICT JSON only:
{{"nodes":[
  {{"temp_id":"n1","label":"{main_topics[0]}", "parent_temp_id": null, "depth": 1, "evidence_ids":["S1"]}},
  {{"temp_id":"n2","label":"<Subcategory>", "parent_temp_id":"n1", "depth": 2, "evidence_ids":["S2"]}}
]}}"""
    else:
        # Fallback for no topics
        system = f"""You are an expert ontology editor creating comprehensive taxonomies.
Generate a hierarchical taxonomy based on the provided content snippets.

Constraints:
- Create depth ≤ {req.max_depth} with ≤ {req.max_children} children per node
- Use clear noun phrases (Title Case), ensure MECE siblings  
- Include evidence_ids from relevant snippets for each node

Return STRICT JSON only:
{{"nodes":[
  {{"temp_id":"n1","label":"<L1>", "parent_temp_id": null, "depth": 1, "evidence_ids":["S1"]}},
  {{"temp_id":"n2","label":"<L2>", "parent_temp_id":"n1", "depth": 2, "evidence_ids":["S2"]}}
]}}"""

    # Build seed topic from request
    seed_parts = []
    if req.prompt:
        seed_parts.append(req.prompt)
    if req.topics:
        seed_parts.extend(req.topics)
    seed = "\n".join(seed_parts).strip() or "ROOT"

    # Format snippets with IDs
    if shown_snippets:
        snips = "\n".join(f"{s['id']}: {s['text'][:600]}" for s in shown_snippets)
        user_content = f"""Build a detailed taxonomy for: {seed}

CRITICAL RULE: Use ONLY terminology that appears in the provided snippets.
DO NOT create generic organizational categories like "Learning Types", "Application Domains", "Core Tasks".
Instead, use the EXACT terms and concepts mentioned in the content.

Content Snippets (reference by ID in evidence_ids):
{snips}

STRICT Requirements:
- Use EXACT terminology from snippets (e.g., "Deep Learning", "Neural Networks", "Supervised Learning")
- DO NOT invent generic categories or organizational labels
- Every node label must have clear textual evidence in the referenced snippets
- Create nodes for specific concepts, algorithms, and methods mentioned
- Avoid abstract groupings - be concrete and specific
- Cite relevant snippet IDs in evidence_ids for each node

Build depth ≤ {req.max_depth} with ≤ {req.max_children} children per node.

Return JSON with ONLY concepts that are explicitly mentioned in the snippets."""
    else:
        # Fallback if no snippets (shouldn't happen with new flow)
        user_content = f"Create taxonomy for: {seed}"

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user_content},
    ]

    logger.info(
        "llm_request_debug",
        system_tokens_approx=len(system.split()),
        user_tokens_approx=len(user_content.split()),
        total_approx=len(system.split()) + len(user_content.split()),
        num_snippets=len(shown_snippets),
        seed_preview=seed[:100],
    )

    result = await call_llm(messages, response_format={"type": "json_object"}, temperature=0.1)
    nodes = result.get("nodes", []) if isinstance(result, dict) else []
    
    # Ensure required fields exist (including evidence_ids)
    out: List[Dict[str, Any]] = []
    for i, n in enumerate(nodes):
        label = str(n.get("label", "")).strip()
        if not label:
            continue
        out.append(
            {
                "temp_id": n.get("temp_id") or f"n{i}",
                "label": label,
                "parent_temp_id": n.get("parent_temp_id"),
                "depth": int(n.get("depth", 1)),
                "evidence_ids": n.get("evidence_ids", []),
            }
        )
    return out


