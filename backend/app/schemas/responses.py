"""Response schemas for taxonomy service."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TaxonomyNode(BaseModel):
    """Normalized taxonomy node returned to clients."""

    node_id: str = Field(..., description="Stable node identifier")
    label: str = Field(..., description="Human-readable label")
    depth: int = Field(..., description="Depth starting from 1 at root")
    parent_id: Optional[str] = Field(default=None, description="Parent node id if any")
    slug: str = Field(..., description="URL-safe slug of label")


class TaxonomyArtifact(BaseModel):
    """Full taxonomy artifact payload."""

    version_id: str = Field(..., description="Version identifier for this generation run")
    tree: List[TaxonomyNode] = Field(default_factory=list, description="Flat list of nodes")
    table: List[Dict[str, Any]] = Field(default_factory=list, description="Flattened table rows")
    csv_url: str = Field(..., description="URL to CSV artifact (signed in prod, file:// in dev)")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="Summary metrics")


