"""
Schemas for file upload functionality
"""

from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime


class FileUploadResponse(BaseModel):
    """Response schema for file upload."""
    status: str  # "uploaded" or "already_uploaded"
    message: str
    file_hash: str
    filename: Optional[str]
    file_size: int
    upload_time: Optional[str]


class FileInfoResponse(BaseModel):
    """Response schema for file information."""
    file_hash: str
    original_filename: str
    file_size: int
    upload_time: Optional[str]
    content_type: str
    last_modified: Optional[str]


class FileProcessRequest(BaseModel):
    """Request schema for file processing by hash."""
    file_hash: str
    filename: Optional[str] = None


class UserFileResponse(BaseModel):
    """Response schema for user file information."""
    id: int
    file_hash: str
    original_filename: str
    file_size: int
    content_type: str
    uploaded_at: Optional[datetime]


class UserFileListResponse(BaseModel):
    """Response schema for listing user files."""
    files: List[UserFileResponse]
    total_count: int 