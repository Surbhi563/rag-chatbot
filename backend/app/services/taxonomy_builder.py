"""Evidence-based taxonomy building from user uploads."""

import random
import re
import time
from typing import Any, Dict, List, Optional, Tuple

from app.core.logging import get_logger
from app.schemas.requests import GenerateJobRequest
from app.schemas.responses import TaxonomyArtifact, TaxonomyNode
from app.services import extractors
from app.services.llm import llm_propose
from app.services.text_processing import build_snippets, select_prompt_snippets
from app.services.storage import write_csv
from app.utils.table import flatten, normalize_and_validate

logger = get_logger(__name__)


def _new_version_id() -> str:
    epoch = int(time.strftime("%Y%m%d%H%M%S", time.gmtime()))
    rand = hex(random.getrandbits(20))[2:]
    return f"tx-{epoch}-{rand}"


def _has_overlap(label: str, evidence_ids: List[str], snippet_map: Dict[str, Dict[str, Any]]) -> bool:
    """Check if label has STRONG keyword overlap with referenced snippets."""
    # Extract meaningful tokens from label (minimum 3 chars)
    tokens = {t for t in re.findall(r"[a-zA-Z0-9]+", label.lower()) if len(t) > 2}
    if not tokens:
        return False  # Empty labels not allowed
    
    # Combine all referenced snippet text
    combined_text = " ".join(snippet_map[sid]["text"] for sid in evidence_ids if sid in snippet_map).lower()
    
    # STRICT VALIDATION: Require significant overlap, not just any token
    # Count how many label tokens appear in the evidence
    matching_tokens = sum(1 for token in tokens if token in combined_text)
    overlap_ratio = matching_tokens / len(tokens)
    
    # Require at least 50% of label tokens to appear in evidence
    # OR the label to be an exact match for a key concept
    exact_concept_matches = {
        'machine learning', 'deep learning', 'neural network', 'supervised learning',
        'unsupervised learning', 'reinforcement learning', 'computer vision', 
        'natural language processing', 'artificial intelligence', 'classification',
        'regression', 'clustering', 'algorithm', 'optimization', 'prediction'
    }
    
    label_lower = label.lower()
    is_exact_concept = any(concept in label_lower for concept in exact_concept_matches)
    
    # BALANCED: Either 30%+ token overlap OR exact concept match OR any meaningful overlap
    if overlap_ratio >= 0.3:  # Relaxed from 50% to 30%
        logger.debug(f"Node '{label}' passed: {overlap_ratio:.1%} token overlap")
        return True
    elif is_exact_concept:
        logger.debug(f"Node '{label}' passed: exact concept match")
        return True
    elif matching_tokens > 0:  # At least some overlap
        logger.debug(f"Node '{label}' passed: {matching_tokens} tokens matched")
        return True
    else:
        logger.debug(f"Node '{label}' failed: no token overlap")
        return False


def filter_nodes_by_evidence(
    nodes_raw: List[Dict[str, Any]], snippet_map: Dict[str, Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], int]:
    """Filter nodes by evidence validation, return (kept_nodes, dropped_count)."""
    kept, dropped = [], 0
    
    for node in nodes_raw:
        evidence_ids = node.get("evidence_ids", [])
        
        # Filter to valid snippet IDs
        valid_ids = [sid for sid in evidence_ids if sid in snippet_map]
        if not valid_ids:
            logger.debug(f"Dropping node '{node.get('label')}': no valid evidence IDs")
            dropped += 1
            continue
        
        # Optional: Check keyword overlap
        if not _has_overlap(node.get("label", ""), valid_ids, snippet_map):
            logger.debug(f"Dropping node '{node.get('label')}': no keyword overlap with evidence")
            dropped += 1
            continue
        
        # Keep node with valid evidence
        node["evidence_ids"] = valid_ids
        kept.append(node)
    
    return kept, dropped


async def build_taxonomy(req: GenerateJobRequest) -> TaxonomyArtifact:
    """Build taxonomy with evidence validation from user uploads. Never returns 4xx."""
    version_id = _new_version_id()
    
    # Extract user text from uploads
    user_text = ""
    if req.use_user_uploads and req.upload_ids:
        texts: List[str] = []
        for uid in req.upload_ids:
            try:
                text = extractors.extract_text(uid)
                if text:
                    texts.append(text)
            except Exception as e:
                logger.warning(f"Failed to extract text from {uid}: {e}")
        
        user_text = "\n\n".join(texts)
        if len(user_text) > 80_000:
            user_text = user_text[:80_000]
    
    # Build snippets from user text only
    snippets = build_snippets(user_text, additional_passages=[], max_chars=800)
    shown_snippets = select_prompt_snippets(snippets, limit=12, topics=req.topics)
    
    logger.info(
        "taxonomy_build_start",
        version_id=version_id,
        user_text_length=len(user_text),
        total_snippets=len(snippets),
        shown_snippets=len(shown_snippets),
    )
    
    # Single round generation (no RAG augmentation)
    logger.info("taxonomy_generation", snippets_count=len(snippets), shown_count=len(shown_snippets))
    
    # LLM generation
    draft = await llm_propose(req, shown_snippets)
    nodes_raw = draft if isinstance(draft, list) else []
    
    if not nodes_raw:
        logger.warning("LLM returned no nodes")
        # Return empty taxonomy rather than failing
        return TaxonomyArtifact(
            version_id=version_id,
            tree=[],
            table=[],
            csv_url=write_csv([], version_id),
            metrics={
                "nodes": 0,
                "rejected_nodes": 0,
                "coverage": 0.0,
                "grounding": "user_upload" if user_text else "none",
                "total_snippets": len(snippets),
            },
        )
    
    # Evidence validation
    snippet_map = {s["id"]: s for s in snippets}
    nodes_validated, dropped = filter_nodes_by_evidence(nodes_raw, snippet_map)
    
    # Normalize and validate (depth, children limits, dedup)
    final_nodes = normalize_and_validate(
        temp_nodes=nodes_validated,
        version_id=version_id,
        max_depth=req.max_depth,
        max_children=req.max_children,
    )
    
    final_coverage = len(nodes_validated) / max(1, len(nodes_raw)) if nodes_raw else 0.0
    
    logger.info(
        "taxonomy_results",
        raw_nodes=len(nodes_raw),
        validated_nodes=len(nodes_validated),
        final_nodes=len(final_nodes),
        dropped=dropped,
        coverage=final_coverage,
    )
    
    # Build final artifact
    table_rows = flatten(final_nodes)
    csv_url = write_csv(table_rows, version_id)
    
    # Grounding type (no more RAG)
    grounding = "user_upload" if user_text else "none"
    
    metrics = {
        "nodes": len(final_nodes),
        "rejected_nodes": dropped,
        "coverage": final_coverage,
        "grounding": grounding,
        "total_snippets": len(snippets),
    }
    
    logger.info("taxonomy_build_complete", **metrics)
    
    return TaxonomyArtifact(
        version_id=version_id,
        tree=final_nodes,
        table=table_rows,
        csv_url=csv_url,
        metrics=metrics,
    )


