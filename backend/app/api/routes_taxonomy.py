"""Taxonomy generation API routes."""

import re
from typing import List, Optional

from fastapi import APIRouter, HTTPException

from app.schemas.requests import GenerateJobRequest
from app.schemas.responses import TaxonomyArtifact
from app.services.taxonomy_builder import build_taxonomy


router = APIRouter()


def _validate_upload_ids(upload_ids: Optional[List[str]]) -> Optional[List[str]]:
    """Validate upload_ids to prevent path traversal at API level."""
    if not upload_ids:
        return upload_ids
    
    validated_ids = []
    for upload_id in upload_ids:
        if not upload_id or not isinstance(upload_id, str):
            raise HTTPException(status_code=400, detail="Invalid upload_id: empty or non-string")
        
        # Security: Validate upload_id format at API level
        if ".." in upload_id or upload_id.startswith("/") or "\\" in upload_id:
            raise HTTPException(status_code=400, detail=f"Invalid upload_id: path traversal detected in '{upload_id}'")
        
        # Expected format: uploads/{uuid}/{filename}
        if not re.match(r'^uploads/[a-f0-9]{6}/[^/\\<>:"|?*]+$', upload_id):
            raise HTTPException(status_code=400, detail=f"Invalid upload_id format: '{upload_id}'")
        
        validated_ids.append(upload_id)
    
    return validated_ids


def _validate_text_inputs(topics: Optional[List[str]], prompt: Optional[str]) -> None:
    """Validate text inputs to prevent injection attacks."""
    # Validate topics
    if topics:
        for topic in topics:
            if not isinstance(topic, str):
                raise HTTPException(status_code=400, detail="Invalid topic: must be string")
            if len(topic.strip()) > 500:  # Reasonable limit
                raise HTTPException(status_code=400, detail="Topic too long (max 500 characters)")
    
    # Validate prompt
    if prompt:
        if not isinstance(prompt, str):
            raise HTTPException(status_code=400, detail="Invalid prompt: must be string")
        if len(prompt.strip()) > 2000:  # Reasonable limit
            raise HTTPException(status_code=400, detail="Prompt too long (max 2000 characters)")


@router.post("/v1/taxonomy/generate", response_model=TaxonomyArtifact)
async def taxonomy_generate(req: GenerateJobRequest) -> TaxonomyArtifact:
    """Generate taxonomy with evidence validation. Always returns 200 with best-effort results.
    
    Security: Validates all user inputs at API boundary to prevent path traversal and injection attacks.
    """
    # Security: Validate upload_ids at API level
    validated_upload_ids = _validate_upload_ids(req.upload_ids)
    
    # Security: Validate text inputs
    _validate_text_inputs(req.topics, req.prompt)
    
    # Create validated request object
    validated_req = GenerateJobRequest(
        topics=req.topics,
        prompt=req.prompt,
        max_depth=req.max_depth,
        max_children=req.max_children,
        use_user_uploads=req.use_user_uploads,
        upload_ids=validated_upload_ids,
    )
    
    artifact = await build_taxonomy(validated_req)
    return artifact


