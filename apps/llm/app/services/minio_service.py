"""
MinIO service for Brain_Net LLM Service
Handles file operations and storage.
"""

from typing import Optional, Dict, Any
from minio import Minio
from minio.error import S3Error
from fastapi import HTTPException
import tempfile
import os

from app.core.config import settings


class MinIOService:
    """Service for handling MinIO operations."""
    
    def __init__(self):
        """Initialize MinIO client."""
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=False  # For local development
        )
        self.bucket_name = "brain-net-documents"
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """Ensure the bucket exists."""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
        except S3Error as e:
            print(f"MinIO bucket error: {e}")
    
    def file_exists(self, file_hash: str) -> bool:
        """Check if a file exists in MinIO."""
        try:
            self.client.stat_object(self.bucket_name, file_hash)
            return True
        except S3Error:
            return False
    
    def get_file_info(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """Get file information from MinIO."""
        try:
            stat = self.client.stat_object(self.bucket_name, file_hash)
            return {
                "file_hash": file_hash,
                "original_filename": stat.metadata.get("original_filename", "unknown"),  # Fallback for legacy files
                "file_size": int(stat.metadata.get("file_size", stat.size)),
                "upload_time": stat.metadata.get("upload_time"),
                "content_type": stat.content_type,
                "last_modified": stat.last_modified.isoformat() if stat.last_modified else None
            }
        except S3Error:
            return None
    
    def download_file_to_temp(self, file_hash: str) -> str:
        """Download file from MinIO to a temporary file."""
        try:
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False)
            temp_file.close()
            
            # Download file
            self.client.fget_object(self.bucket_name, file_hash, temp_file.name)
            
            return temp_file.name
        except S3Error as e:
            raise HTTPException(
                status_code=404,
                detail=f"File not found in storage: {str(e)}"
            )
    
    def cleanup_temp_file(self, temp_file_path: str):
        """Clean up temporary file."""
        try:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
        except Exception as e:
            print(f"Failed to cleanup temp file {temp_file_path}: {e}") 