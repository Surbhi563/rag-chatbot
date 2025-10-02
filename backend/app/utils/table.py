"""Utilities for normalizing taxonomy nodes and flattening to table rows."""

from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

from app.schemas.responses import TaxonomyNode
from app.utils.text import slugify, similar


TempNode = Dict[str, Any]


def _build_parent_map(temp_nodes: List[TempNode]) -> Dict[str, List[TempNode]]:
    by_parent: Dict[Optional[str], List[TempNode]] = defaultdict(list)
    for n in temp_nodes:
        by_parent[n.get("parent_temp_id")].append(n)
    return by_parent


def _enforce_children_limits(
    children: List[TempNode], max_children: int
) -> List[TempNode]:
    """Drop near-duplicate siblings and enforce children limit preserving order."""

    seen: List[str] = []
    unique: List[TempNode] = []
    # Deterministic order (alphabetic by label) to keep trimming predictable
    for c in sorted(children, key=lambda x: str(x.get("label", "")).lower()):
        label = c.get("label", "").strip()
        if not label:
            continue
        if any(similar(label, s) for s in seen):
            continue
        unique.append(c)
        seen.append(label)
        if len(unique) >= max_children:
            break
    return unique


def normalize_and_validate(
    temp_nodes: List[TempNode], version_id: str, max_depth: int, max_children: int
) -> List[TaxonomyNode]:
    """Normalize raw nodes:

    - Prune by depth and children limits
    - Drop duplicate labels among siblings (fuzzy)
    - Assign node_id, parent_id, slug
    - Ensure roots have depth 1
    """

    if max_depth < 1:
        return []

    # Group children by parent_temp_id
    by_parent = _build_parent_map(temp_nodes)

    # Determine roots as those with parent_temp_id None and depth == 1
    roots = [n for n in by_parent.get(None, []) if int(n.get("depth", 1)) <= max_depth]
    roots = _enforce_children_limits(roots, max_children)

    normalized: List[TaxonomyNode] = []

    def visit(node: TempNode, parent_node_id: Optional[str], slug_path: List[str]) -> None:
        depth = int(node.get("depth", 1))
        if depth < 1 or depth > max_depth:
            return
        label = str(node.get("label", "")).strip()
        if not label:
            return
        slug = slugify(label)
        path_parts = slug_path + [slug]
        node_id = f"{version_id}/" + "/".join(path_parts)
        normalized.append(
            TaxonomyNode(
                node_id=node_id,
                label=label,
                depth=depth,
                parent_id=parent_node_id,
                slug=slug,
            )
        )

        # Recurse into children for this temp_id
        temp_id = node.get("temp_id")
        children = [c for c in by_parent.get(temp_id, []) if int(c.get("depth", depth + 1)) == depth + 1]
        children = _enforce_children_limits(children, max_children)
        for child in children:
            visit(child, node_id, path_parts)

    for r in roots:
        visit(r, None, [])

    return normalized


def flatten(nodes: List[TaxonomyNode]) -> List[Dict[str, Any]]:
    """Flatten taxonomy nodes into table rows with L1..Ln path columns.

    Expects nodes to be sorted in traversal order (parents before children).
    """

    # Build map for quick lookup
    by_id: Dict[str, TaxonomyNode] = {n.node_id: n for n in nodes}

    rows: List[Dict[str, Any]] = []

    def build_path(node: TaxonomyNode) -> List[str]:
        p: List[str] = []
        current: Optional[TaxonomyNode] = node
        # Climb up to root
        while current is not None:
            p.append(current.label)
            current = by_id.get(current.parent_id) if current.parent_id else None
        p.reverse()
        return p

    max_depth = 0
    paths_cache: Dict[str, List[str]] = {}
    for n in nodes:
        path = build_path(n)
        paths_cache[n.node_id] = path
        max_depth = max(max_depth, len(path))

    for n in nodes:
        path = paths_cache[n.node_id]
        row: Dict[str, Any] = {}
        # Only add L1, L2, L3, L4, L5 columns
        for i, label in enumerate(path, start=1):
            if i <= 5:  # Only go up to L5
                row[f"L{i}"] = label
        rows.append(row)

    return rows


