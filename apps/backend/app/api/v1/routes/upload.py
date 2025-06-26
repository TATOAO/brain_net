"""
File upload routes for Brain_Net Backend
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import httpx

from apps.shared.schemas.upload import FileUploadResponse, FileInfoResponse, FileProcessRequest, UserFileListResponse
from apps.shared.models import User
from app.services.file_upload import FileUploadService
from app.services.auth import get_current_user_dependency
from app.core.config import get_settings
from app.core.database import DatabaseManager

router = APIRouter()
settings = get_settings()
security = HTTPBearer()


async def get_db(request: Request) -> AsyncSession:
    """Dependency to get database session."""
    db_manager: DatabaseManager = request.app.state.db_manager
    async with db_manager.get_postgres_session() as session:
        yield session


async def get_file_upload_service(db: AsyncSession = Depends(get_db)) -> FileUploadService:
    """Dependency to get file upload service with database session."""
    return FileUploadService(db)


async def get_current_user_dep(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Dependency to get current authenticated user."""
    from app.services.auth import AuthService
    from app.schemas.auth import TokenData
    from fastapi.security import HTTPBearer
    
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not credentials:
        raise credentials_exception
    
    token_data = AuthService.verify_token(credentials.credentials)
    if token_data is None:
        raise credentials_exception
    
    user = await AuthService.get_user_by_id(db, token_data.user_id)
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    return user


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user_dep),
    file_service: FileUploadService = Depends(get_file_upload_service)
) -> FileUploadResponse:
    """
    Upload a file to MinIO storage with user isolation.
    Returns information about the upload or indicates if file already exists for this user.
    """
    # Validate file size
    if file.size and file.size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {settings.MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    result = await file_service.upload_file(file, current_user)
    return FileUploadResponse(**result)


@router.get("/info/{file_hash}", response_model=FileInfoResponse)
async def get_file_info(
    file_hash: str,
    current_user: User = Depends(get_current_user_dep),
    file_service: FileUploadService = Depends(get_file_upload_service)
) -> FileInfoResponse:
    """Get information about an uploaded file (user must own the file)."""
    file_info = await file_service.get_user_file_info(current_user.id, file_hash)
    if not file_info:
        raise HTTPException(status_code=404, detail="File not found or you don't have access to it")
    
    return FileInfoResponse(**file_info)


@router.post("/process")
async def process_document(
    request: FileProcessRequest,
    current_user: User = Depends(get_current_user_dep),
    file_service: FileUploadService = Depends(get_file_upload_service)
) -> dict:
    """
    Send document to LLM service for processing.
    User must own the file to process it.
    """
    # Verify user owns the file
    file_info = await file_service.get_user_file_info(current_user.id, request.file_hash)
    if not file_info:
        raise HTTPException(
            status_code=404, 
            detail="File not found or you don't have access to it"
        )
    
    try:
        # Make request to LLM service
        llm_url = f"{settings.LLM_SERVICE_URL}/api/v1/documents/process-by-hash"
        async with httpx.AsyncClient() as client:
            response = await client.post(
                llm_url,
                json={
                    "file_hash": request.file_hash,
                    "filename": request.filename or file_info["original_filename"],
                    "user_id": current_user.id  # Pass user context to LLM service
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
    current_user: User = Depends(get_current_user_dep),
    file_service: FileUploadService = Depends(get_file_upload_service)
):
    """Download a file by its hash (user must own the file)."""
    try:
        file_stream = await file_service.get_user_file_stream(current_user.id, file_hash)
        file_info = await file_service.get_user_file_info(current_user.id, file_hash)
        
        if not file_info:
            raise HTTPException(status_code=404, detail="File not found or you don't have access to it")
        
        from fastapi.responses import StreamingResponse
        
        return StreamingResponse(
            file_stream,
            media_type=file_info.get("content_type", "application/octet-stream"),
            headers={
                "Content-Disposition": f"attachment; filename={file_info.get('original_filename', file_hash)}"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"File download failed: {str(e)}"
        )


@router.get("/my-files", response_model=UserFileListResponse)
async def list_my_files(
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_user_dep),
    file_service: FileUploadService = Depends(get_file_upload_service)
) -> UserFileListResponse:
    """List all files uploaded by the current user."""
    try:
        result = await file_service.list_user_files(current_user.id, limit, offset)
        return UserFileListResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list files: {str(e)}"
        ) 