"""
File upload routes for Brain_Net Backend
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import Optional
import httpx

from apps.shared.schemas import FileUploadResponse, FileInfoResponse, FileProcessRequest
from app.services.file_upload import FileUploadService
from app.core.config import get_settings

router = APIRouter()
settings = get_settings()


def get_file_upload_service() -> FileUploadService:
    """Dependency to get file upload service."""
    return FileUploadService()


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    file_service: FileUploadService = Depends(get_file_upload_service)
) -> FileUploadResponse:
    """
    Upload a file to MinIO storage.
    Returns information about the upload or indicates if file already exists.
    """
    # Validate file size
    if file.size and file.size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {settings.MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    result = await file_service.upload_file(file)
    return FileUploadResponse(**result)


@router.get("/info/{file_hash}", response_model=FileInfoResponse)
async def get_file_info(
    file_hash: str,
    file_service: FileUploadService = Depends(get_file_upload_service)
) -> FileInfoResponse:
    """Get information about an uploaded file."""
    file_info = file_service.get_file_info(file_hash)
    if not file_info:
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileInfoResponse(**file_info)


@router.post("/process")
async def process_document(
    request: FileProcessRequest
) -> dict:
    """
    Send document to LLM service for processing.
    Returns processing result from LLM service.
    """
    try:
        # Make request to LLM service
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8001/api/v1/documents/process-by-hash",
                json={
                    "file_hash": request.file_hash,
                    "filename": request.filename
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"LLM service error: {response.text}"
                )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Failed to connect to LLM service: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Document processing failed: {str(e)}"
        )


@router.get("/download/{file_hash}")
async def download_file(
    file_hash: str,
    file_service: FileUploadService = Depends(get_file_upload_service)
):
    """Download a file by its hash."""
    try:
        file_stream = file_service.get_file_stream(file_hash)
        file_info = file_service.get_file_info(file_hash)
        
        if not file_info:
            raise HTTPException(status_code=404, detail="File not found")
        
        from fastapi.responses import StreamingResponse
        
        return StreamingResponse(
            file_stream,
            media_type=file_info.get("content_type", "application/octet-stream"),
            headers={
                "Content-Disposition": f"attachment; filename={file_info.get('original_filename', file_hash)}"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"File download failed: {str(e)}"
        ) 