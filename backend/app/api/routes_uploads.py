"""Uploads endpoint."""

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services.storage import store_raw_file


router = APIRouter()


@router.post("/v1/uploads")
async def upload_file(file: UploadFile = File(...)) -> dict:
    if not file:
        raise HTTPException(status_code=400, detail="file is required")
    upload_id = await store_raw_file(file)
    return {"upload_id": upload_id}


