"""Request schemas for taxonomy service."""

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, conint


class GenerateJobRequest(BaseModel):
    """Request model for generating a taxonomy."""

    topics: Optional[List[str]] = Field(default=None, description="Seed topics")
    prompt: Optional[str] = Field(default=None, description="Prompt text for generation")
    max_depth: conint(ge=1, le=5) = Field(default=4, description="Maximum depth of the taxonomy (1..5)")
    max_children: conint(ge=2, le=20) = Field(default=8, description="Maximum number of children per node (2..20)")
    use_user_uploads: bool = Field(default=False, description="Whether to use user uploads as grounding")
    upload_ids: Optional[List[str]] = Field(default=None, description="Uploaded file identifiers")

    @field_validator("topics")
    @classmethod
    def strip_empty_topics(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None:
            return v
        cleaned = [t.strip() for t in v if t and t.strip()]
        return cleaned or None


