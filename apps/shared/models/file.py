"""
File models for tracking file uploads and ownership.
"""

from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Column, DateTime, ForeignKey
from sqlalchemy.sql import func


class UserFile(SQLModel, table=True):
    """Model for tracking user file uploads."""
    __tablename__ = "user_files"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    file_hash: str = Field(index=True, max_length=64)
    original_filename: str = Field(max_length=255)
    file_size: int
    content_type: str = Field(max_length=255)
    storage_path: str = Field(max_length=500)  # Path in MinIO: {user_id}/{file_hash}
    uploaded_at: Optional[datetime] = Field(
        default=None, 
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    
    # Composite index for efficient lookups
    __table_args__ = (
        {"sqlite_autoincrement": True}
    )


class UserFileRead(SQLModel):
    """Schema for reading user file information."""
    id: int
    file_hash: str
    original_filename: str
    file_size: int
    content_type: str
    uploaded_at: Optional[datetime]


class UserFileList(SQLModel):
    """Schema for listing user files."""
    files: list[UserFileRead]
    total_count: int 