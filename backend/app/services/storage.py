"""Storage backends for uploads and artifacts.

Supports LocalFS in dev and GCS in prod.
"""

import csv
import io
import mimetypes
import os
import uuid
from datetime import timedelta
from typing import Dict, List, Optional, Tuple

from fastapi import HTTPException, UploadFile

from app.core.config import settings


MAX_UPLOAD_BYTES = 25 * 1024 * 1024  # 25 MB


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _local_bucket_dir() -> str:
    # For development, use a more accessible location
    if settings.is_dev:
        import os
        # Try Desktop first, fallback to Downloads, then temp
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop", "taxonomy-artifacts")
        downloads_path = os.path.join(os.path.expanduser("~"), "Downloads", "taxonomy-artifacts")
        
        # Use Desktop if it exists, otherwise Downloads
        if os.path.exists(os.path.dirname(desktop_path)):
            return desktop_path
        elif os.path.exists(os.path.dirname(downloads_path)):
            return downloads_path
    
    # Fallback to configured path or temp
    return settings.local_bucket_dir


def _local_uploads_root() -> str:
    return os.path.join(_local_bucket_dir(), "uploads")


def _local_artifacts_root() -> str:
    return os.path.join(_local_bucket_dir(), "artifacts")


async def store_raw_file(file: UploadFile) -> str:
    """Store an uploaded file and return an opaque upload_id.

    LocalFS: <bucket>/uploads/{uuid}/{filename}
    Returns: uploads/{uuid}/{filename}
    """

    filename = file.filename or "upload.bin"
    
    # Security: Validate filename to prevent path traversal
    if ".." in filename or "/" in filename or "\\" in filename or filename.startswith("."):
        raise HTTPException(status_code=400, detail="Invalid filename: path traversal detected")
    
    # Use only the basename to be extra safe
    filename = os.path.basename(filename)
    ext = os.path.splitext(filename)[1].lower()

    if settings.is_dev:
        # LocalFS
        bucket = _local_uploads_root()
        upload_uuid = uuid.uuid4().hex[:6]
        dest_dir = os.path.join(bucket, upload_uuid)
        _ensure_dir(dest_dir)
        dest_path = os.path.join(dest_dir, filename)

        size = 0
        with open(dest_path, "wb") as f:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_UPLOAD_BYTES:
                    try:
                        os.remove(dest_path)
                    except Exception:
                        pass
                    raise HTTPException(status_code=400, detail="File too large (max 25MB)")
                f.write(chunk)

        return f"uploads/{upload_uuid}/{filename}"

    # GCS backend
    try:
        from google.cloud import storage as gcs_storage  # type: ignore
    except Exception as exc:  # pragma: no cover - not executed in dev tests
        raise HTTPException(status_code=500, detail=f"GCS not available: {exc}")

    client = gcs_storage.Client()
    bucket = client.bucket(settings.gcs_bucket)
    upload_uuid = uuid.uuid4().hex[:6]
    object_name = f"uploads/{upload_uuid}/{filename}"
    blob = bucket.blob(object_name)

    size = 0
    # Stream in chunks via in-memory buffer; GCS client supports upload_from_file
    buf = io.BytesIO()
    while True:
        chunk = await file.read(1024 * 1024)
        if not chunk:
            break
        size += len(chunk)
        if size > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=400, detail="File too large (max 25MB)")
        buf.write(chunk)
    buf.seek(0)
    blob.upload_from_file(buf)
    return object_name


def resolve_path(upload_id: str) -> Tuple[str, str]:
    """Resolve an upload_id to a local path and MIME type.

    In dev, returns actual local file; in prod, downloads to tmp and returns temp path.
    
    Security: Validates paths to prevent directory traversal attacks.
    """
    
    # Security: Reject obviously malicious paths
    if not upload_id or ".." in upload_id or upload_id.startswith("/") or "\\" in upload_id:
        raise HTTPException(status_code=400, detail="Invalid upload_id: path traversal detected")

    if settings.is_dev:
        bucket_dir = os.path.abspath(_local_bucket_dir())
        local_path = os.path.abspath(os.path.join(bucket_dir, upload_id))
        
        # Security: Ensure the resolved path is within the bucket directory
        if not local_path.startswith(bucket_dir + os.sep) and local_path != bucket_dir:
            raise HTTPException(status_code=400, detail="Invalid upload_id: path traversal detected")
            
        mime, _ = mimetypes.guess_type(local_path)
        return local_path, (mime or "application/octet-stream")

    # GCS: download to tmp
    try:
        from google.cloud import storage as gcs_storage  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"GCS not available: {exc}")

    client = gcs_storage.Client()
    bucket = client.bucket(settings.gcs_bucket)
    object_name = upload_id
    blob = bucket.blob(object_name)
    tmp_dir = os.path.abspath(os.path.join("/tmp", "taxonomy-downloads"))
    _ensure_dir(tmp_dir)
    
    # Security: Only use basename to prevent traversal in temp path
    filename = os.path.basename(object_name)
    if not filename:  # Empty basename means path ended with /
        raise HTTPException(status_code=400, detail="Invalid upload_id: invalid filename")
        
    tmp_path = os.path.abspath(os.path.join(tmp_dir, filename))
    
    # Security: Ensure temp path is within tmp_dir
    if not tmp_path.startswith(tmp_dir + os.sep) and tmp_path != tmp_dir:
        raise HTTPException(status_code=400, detail="Invalid upload_id: path traversal detected")
        
    blob.download_to_filename(tmp_path)
    mime, _ = mimetypes.guess_type(filename)
    return tmp_path, (mime or "application/octet-stream")


def _validate_version_id(version_id: str) -> str:
    """Validate version_id to prevent path traversal."""
    import re
    if not version_id or not re.match(r'^tx-\d{14}-[a-f0-9]+$', version_id):
        raise HTTPException(status_code=400, detail="Invalid version_id format")
    return version_id


def _local_csv_path(version_id: str) -> str:
    safe_version_id = _validate_version_id(version_id)
    dest_dir = os.path.join(_local_artifacts_root(), safe_version_id)
    _ensure_dir(dest_dir)
    return os.path.join(dest_dir, "taxonomy.csv")


def write_csv(rows: List[Dict[str, str]], version_id: str) -> str:
    """Write CSV artifact and return URL.

    LocalFS: file://<bucket>/artifacts/{version_id}/taxonomy.csv
    GCS: https signed URL
    """

    if settings.is_dev:
        path = _local_csv_path(version_id)
        # Fixed header order: L1, L2, L3, L4, L5 only
        header_keys = ["L1", "L2", "L3", "L4", "L5"]
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=header_keys)
            writer.writeheader()
            for r in rows:
                writer.writerow(r)
        try:
            from pathlib import Path
            return f"file://{Path(path).as_posix()}"
        except Exception:
            return f"file://{path}"

    # GCS path
    try:
        from google.cloud import storage as gcs_storage  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"GCS not available: {exc}")

    safe_version_id = _validate_version_id(version_id)
    client = gcs_storage.Client()
    bucket = client.bucket(settings.gcs_bucket)
    object_name = f"artifacts/{safe_version_id}/taxonomy.csv"
    blob = bucket.blob(object_name)

    # Prepare CSV into memory with fixed header order
    header_keys = ["L1", "L2", "L3", "L4", "L5"]
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=header_keys)
    writer.writeheader()
    for r in rows:
        writer.writerow(r)
    data = buf.getvalue().encode("utf-8")
    blob.upload_from_file(io.BytesIO(data), content_type="text/csv")

    # Signed URL for 1 hour
    url = blob.generate_signed_url(expiration=timedelta(hours=1), method="GET")
    return url


