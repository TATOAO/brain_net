"""
File upload service for Brain_Net Backend
Handles file uploads to MinIO with duplicate detection.
"""

import hashlib
import asyncio
from typing import Optional, Dict, Any
from minio import Minio
from minio.error import S3Error
from fastapi import UploadFile, HTTPException
import aiofiles
import tempfile
import os
from datetime import datetime

from app.core.config import get_settings

settings = get_settings()


class FileUploadService:
    """Service for handling file uploads to MinIO."""
    
    def __init__(self):
        """Initialize MinIO client."""
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        self.bucket_name = settings.MINIO_BUCKET_NAME
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
    
    def check_file_exists(self, file_hash: str) -> bool:
        """Check if a file with the given hash already exists in MinIO."""
        try:
            # Use hash as object name to check for existence
            self.client.stat_object(self.bucket_name, file_hash)
            return True
        except S3Error:
            return False
    
    async def upload_file(self, file: UploadFile) -> Dict[str, Any]:
        """
        Upload file to MinIO if it doesn't already exist.
        Returns upload result with file information.
        """
        try:
            # Calculate file hash
            file_hash = await self.calculate_file_hash(file)
            
            # Check if file already exists
            if self.check_file_exists(file_hash):
                return {
                    "status": "already_uploaded",
                    "message": "File already exists",
                    "file_hash": file_hash,
                    "filename": file.filename,
                    "file_size": 0,  # We don't need to calculate size for existing files
                    "upload_time": None
                }
            
            # File doesn't exist, upload it
            file_content = await file.read()
            file_size = len(file_content)
            
            # Upload to MinIO using hash as object name
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name
            
            # Upload file to MinIO
            self.client.fput_object(
                self.bucket_name,
                file_hash,
                temp_file_path,
                content_type=file.content_type or "application/octet-stream",
                metadata={
                    "original_filename": file.filename or "unknown",
                    "upload_time": datetime.utcnow().isoformat(),
                    "file_size": str(file_size)
                }
            )
            
            # Clean up temp file
            os.unlink(temp_file_path)
            
            return {
                "status": "uploaded",
                "message": "File uploaded successfully",
                "file_hash": file_hash,
                "filename": file.filename,
                "file_size": file_size,
                "upload_time": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"File upload failed: {str(e)}"
            )
    
    def get_file_info(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """Get information about a file from MinIO."""
        try:
            stat = self.client.stat_object(self.bucket_name, file_hash)
            return {
                "file_hash": file_hash,
                "original_filename": stat.metadata.get("original_filename", "unknown"),
                "file_size": int(stat.metadata.get("file_size", stat.size)),
                "upload_time": stat.metadata.get("upload_time"),
                "content_type": stat.content_type,
                "last_modified": stat.last_modified.isoformat() if stat.last_modified else None
            }
        except S3Error:
            return None
    
    def get_file_stream(self, file_hash: str):
        """Get file stream from MinIO."""
        try:
            return self.client.get_object(self.bucket_name, file_hash)
        except S3Error as e:
            raise HTTPException(
                status_code=404,
                detail=f"File not found: {str(e)}"
            ) 