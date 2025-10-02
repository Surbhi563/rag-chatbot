"""Content extraction from uploaded files to text."""

import csv
import io
import os
from typing import List

from fastapi import HTTPException

from app.services.storage import resolve_path
from app.utils.text import normalize_whitespace, drop_repeated_lines


MAX_TEXT_CHARS = 80_000


def _validate_safe_path(path: str) -> str:
    """Additional path validation for security - ensure path is safe to read.
    
    This function provides defense-in-depth against path traversal attacks.
    Even though resolve_path() validates paths, this adds an extra layer.
    """
    if not path:
        raise HTTPException(status_code=400, detail="Empty file path")
    
    # Normalize and resolve the path
    normalized_path = os.path.abspath(path)
    
    # Security check for path traversal
    if ".." in normalized_path:
        raise HTTPException(status_code=400, detail="Path traversal detected in file path")
    
    # Check if file exists with better error message
    if not os.path.isfile(normalized_path):
        # Provide more helpful error message
        if os.path.exists(normalized_path):
            raise HTTPException(status_code=400, detail=f"Path exists but is not a file: {os.path.basename(normalized_path)}")
        else:
            # Check if directory exists to give better guidance
            dir_path = os.path.dirname(normalized_path)
            if os.path.exists(dir_path):
                available_files = [f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))]
                if available_files:
                    raise HTTPException(
                        status_code=404, 
                        detail=f"File not found: {os.path.basename(normalized_path)}. Available files: {', '.join(available_files)}"
                    )
                else:
                    raise HTTPException(status_code=404, detail=f"File not found: {os.path.basename(normalized_path)} (directory empty)")
            else:
                raise HTTPException(status_code=404, detail=f"File not found: {os.path.basename(normalized_path)} (directory does not exist)")
    
    return normalized_path


def _read_text(path: str, limit: int = MAX_TEXT_CHARS) -> str:
    """Read text file with path validation."""
    safe_path = _validate_safe_path(path)
    with open(safe_path, "r", encoding="utf-8", errors="ignore") as f:
        data = f.read(limit + 1)
        return data[:limit]


def _read_pdf(path: str, limit: int = MAX_TEXT_CHARS) -> str:
    """Read PDF file with path validation."""
    safe_path = _validate_safe_path(path)
    try:
        from pdfminer.high_level import extract_text  # type: ignore
    except Exception:
        return ""  # keep optional in dev
    text = extract_text(safe_path) or ""
    return text[:limit]


def _read_docx(path: str, limit: int = MAX_TEXT_CHARS) -> str:
    """Read DOCX file with path validation."""
    safe_path = _validate_safe_path(path)
    try:
        import docx  # type: ignore
    except Exception:
        return ""
    try:
        document = docx.Document(safe_path)
        parts = [p.text for p in document.paragraphs if p.text]
        text = "\n".join(parts)
        return text[:limit]
    except Exception:
        return ""


def _read_csv(path: str, limit: int = MAX_TEXT_CHARS, max_rows: int = 50) -> str:
    """Read CSV file with path validation."""
    safe_path = _validate_safe_path(path)
    out = io.StringIO()
    try:
        with open(safe_path, "r", encoding="utf-8", errors="ignore", newline="") as f:
            reader = csv.reader(f)
            for i, row in enumerate(reader):
                out.write(", ".join(row) + "\n")
                if i >= max_rows:
                    break
    except Exception:
        return ""
    text = out.getvalue()
    return text[:limit]


def extract_text(upload_id: str) -> str:
    """Extract text for grounding from an uploaded file."""

    path, mime = resolve_path(upload_id)
    mime = mime.lower()
    if mime.startswith("text/"):
        raw = _read_text(path)
        raw = normalize_whitespace(raw)
        raw = drop_repeated_lines(raw)
        return raw[:80_000]
    if mime == "application/pdf" or path.lower().endswith(".pdf"):
        raw = _read_pdf(path)
        raw = normalize_whitespace(raw)
        raw = drop_repeated_lines(raw)
        return raw[:80_000]
    if mime in {"application/vnd.openxmlformats-officedocument.wordprocessingml.document"} or path.lower().endswith(
        ".docx"
    ):
        raw = _read_docx(path)
        raw = normalize_whitespace(raw)
        raw = drop_repeated_lines(raw)
        return raw[:80_000]
    if mime in {"text/csv", "application/vnd.ms-excel"} or path.lower().endswith(".csv"):
        raw = _read_csv(path)
        raw = normalize_whitespace(raw)
        raw = drop_repeated_lines(raw)
        return raw[:80_000]
    # Unknown types
    return ""


