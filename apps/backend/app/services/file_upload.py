"""
File upload service for Brain_Net Backend
Handles file uploads to MinIO with user isolation and database tracking.
"""

import hashlib
import asyncio
from typing import Optional, Dict, Any, List
from minio import Minio
from minio.error import S3Error
from fastapi import UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import aiofiles
import tempfile
import os
from datetime import datetime

from app.core.config import get_settings
from apps.shared.models import User, UserFile

settings = get_settings()


class FileUploadService:
    """Service for handling file uploads to MinIO with user isolation."""
    
    def __init__(self, db: AsyncSession):
        """Initialize MinIO client and database session."""
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        self.bucket_name = settings.MINIO_BUCKET_NAME
        self.db = db
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Ensure the bucket exists, create if it doesn't."""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
        except S3Error as e:
            print(f"Error creating bucket: {e}")
    
    async def calculate_file_hash(self, file: UploadFile) -> str:
        """Calculate MD5 hash of the uploaded file."""
        md5_hash = hashlib.md5()
        
        # Save to temp file to calculate hash without consuming the stream
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        # Reset file position for later use
        await file.seek(0)
        
        # Calculate hash from temp file
        async with aiofiles.open(temp_file_path, 'rb') as f:
            while chunk := await f.read(8192):
                md5_hash.update(chunk)
        
        # Clean up temp file
        os.unlink(temp_file_path)
        
        return md5_hash.hexdigest()
    
    def _get_user_storage_path(self, user_id: int, file_hash: str) -> str:
        """Get user-specific storage path."""
        return f"user_{user_id}/{file_hash}"
    
    async def check_user_file_exists(self, user_id: int, file_hash: str) -> Optional[UserFile]:
        """Check if user already has this file uploaded."""
        stmt = select(UserFile).where(
            UserFile.user_id == user_id,
            UserFile.file_hash == file_hash
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    def check_file_exists_in_storage(self, storage_path: str) -> bool:
        """Check if a file exists in MinIO at the specified path."""
        try:
            self.client.stat_object(self.bucket_name, storage_path)
            return True
        except S3Error:
            return False
    
    async def upload_file(self, file: UploadFile, user: User) -> Dict[str, Any]:
        """
        Upload file to MinIO with user isolation.
        Returns upload result with file information.
        """
        try:
            # Calculate file hash
            file_hash = await self.calculate_file_hash(file)
            
            # Check if user already has this file
            existing_file = await self.check_user_file_exists(user.id, file_hash)
            if existing_file:
                return {
                    "status": "already_uploaded",
                    "message": "You have already uploaded this file",
                    "file_hash": file_hash,
                    "filename": file.filename,
                    "file_size": existing_file.file_size,
                    "upload_time": existing_file.uploaded_at.isoformat() if existing_file.uploaded_at else None
                }
            
            # Get user-specific storage path
            storage_path = self._get_user_storage_path(user.id, file_hash)
            
            # Read file content
            file_content = await file.read()
            file_size = len(file_content)
            
            # Upload to MinIO using user-specific path
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name
            
            # Upload file to MinIO
            # Note: MinIO metadata values must be ASCII-only, so we store filename in database only
            self.client.fput_object(
                self.bucket_name,
                storage_path,
                temp_file_path,
                content_type=file.content_type or "application/octet-stream",
                metadata={
                    "upload_time": datetime.utcnow().isoformat(),
                    "file_size": str(file_size),
                    "user_id": str(user.id)
                }
            )
            
            # Clean up temp file
            os.unlink(temp_file_path)
            
            # Save file information to database
            user_file = UserFile(
                user_id=user.id,
                file_hash=file_hash,
                original_filename=file.filename or "unknown",
                file_size=file_size,
                content_type=file.content_type or "application/octet-stream",
                storage_path=storage_path
            )
            
            self.db.add(user_file)
            await self.db.commit()
            await self.db.refresh(user_file)
            
            return {
                "status": "uploaded",
                "message": "File uploaded successfully",
                "file_hash": file_hash,
                "filename": file.filename,
                "file_size": file_size,
                "upload_time": user_file.uploaded_at.isoformat() if user_file.uploaded_at else None
            }
            
        except Exception as e:
            await self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"File upload failed: {str(e)}"
            )
    
    async def get_user_file_info(self, user_id: int, file_hash: str) -> Optional[Dict[str, Any]]:
        """Get information about a user's file."""
        user_file = await self.check_user_file_exists(user_id, file_hash)
        if not user_file:
            return None
            
        return {
            "file_hash": user_file.file_hash,
            "original_filename": user_file.original_filename,
            "file_size": user_file.file_size,
            "upload_time": user_file.uploaded_at.isoformat() if user_file.uploaded_at else None,
            "content_type": user_file.content_type,
            "last_modified": user_file.uploaded_at.isoformat() if user_file.uploaded_at else None
        }
    
    async def get_user_file_stream(self, user_id: int, file_hash: str):
        """Get file stream from MinIO for a specific user's file."""
        user_file = await self.check_user_file_exists(user_id, file_hash)
        if not user_file:
            raise HTTPException(
                status_code=404,
                detail="File not found or you don't have access to it"
            )
        
        try:
            return self.client.get_object(self.bucket_name, user_file.storage_path)
        except S3Error as e:
            raise HTTPException(
                status_code=404,
                detail=f"File not found in storage: {str(e)}"
            )
    
    async def list_user_files(self, user_id: int, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """List all files for a specific user."""
        # Get total count
        count_stmt = select(UserFile).where(UserFile.user_id == user_id)
        count_result = await self.db.execute(count_stmt)
        total_count = len(count_result.scalars().all())
        
        # Get files with pagination
        stmt = (
            select(UserFile)
            .where(UserFile.user_id == user_id)
            .order_by(UserFile.uploaded_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        files = result.scalars().all()
        
        return {
            "files": [
                {
                    "id": f.id,
                    "file_hash": f.file_hash,
                    "original_filename": f.original_filename,
                    "file_size": f.file_size,
                    "content_type": f.content_type,
                    "uploaded_at": f.uploaded_at
                }
                for f in files
            ],
            "total_count": total_count
        }

    # Legacy methods for backward compatibility (deprecated)
    def get_file_info(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """DEPRECATED: Legacy method without user context."""
        raise HTTPException(
            status_code=403,
            detail="File access requires authentication. Use get_user_file_info instead."
        )
    
    def get_file_stream(self, file_hash: str):
        """DEPRECATED: Legacy method without user context."""
        raise HTTPException(
            status_code=403,
            detail="File access requires authentication. Use get_user_file_stream instead."
        ) 