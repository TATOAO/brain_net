"""
Schemas for file upload functionality
"""

from typing import Optional
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