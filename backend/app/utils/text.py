"""Text utilities: slugify and fuzzy similarity."""

import re
from typing import Optional, Iterable

from rapidfuzz import fuzz


_slug_pattern = re.compile(r"[^a-z0-9-]+")


def slugify(label: str) -> str:
    """Create a URL-safe slug from a label.

    - Lowercase
    - Replace whitespace with '-'
    - Remove invalid chars
    - Collapse multiple dashes
    """

    s = label.strip().lower()
    s = re.sub(r"\s+", "-", s)
    s = _slug_pattern.sub("", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "untitled"


def similar(a: Optional[str], b: Optional[str]) -> bool:
    """Return True if two strings are very similar using token_sort_ratio >= 90."""

    if not a or not b:
        return False
    score = fuzz.token_sort_ratio(a, b)
    return score >= 90


def normalize_whitespace(text: str) -> str:
    """Collapse excessive whitespace and normalize line endings."""
    # Normalize Windows newlines, collapse runs of spaces, strip trailing spaces per line
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Replace tabs with single spaces
    text = text.replace("\t", " ")
    # Collapse 3+ newlines to 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Collapse multiple spaces
    text = re.sub(r"[ \f\v]{2,}", " ", text)
    # Trim trailing spaces per line
    text = "\n".join(line.rstrip() for line in text.split("\n"))
    return text.strip()


def drop_repeated_lines(text: str, min_len: int = 20) -> str:
    """Remove repeated lines to reduce noise; keep order.

    Only de-duplicate lines with length >= min_len to preserve short tokens.
    """
    seen: set[str] = set()
    out_lines: list[str] = []
    for line in text.split("\n"):
        key = line.strip()
        if len(key) >= min_len:
            if key in seen:
                continue
            seen.add(key)
        out_lines.append(line)
    return "\n".join(out_lines)


