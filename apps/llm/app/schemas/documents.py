"""
Document-related Pydantic schemas for Brain_Net LLM Service
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class DocumentChunk(BaseModel):
    """Individual document chunk."""
    id: str = Field(..., description="Unique chunk identifier")
    document_id: str = Field(..., description="Parent document ID")
    content: str = Field(..., description="Chunk content")
    metadata: Dict[str, Any] = Field(..., description="Chunk metadata")
    start_index: Optional[int] = Field(default=None, description="Start index in original document")
    end_index: Optional[int] = Field(default=None, description="End index in original document")


class DocumentMetadata(BaseModel):
    """Document metadata."""
    id: str = Field(..., description="Unique document identifier")
    filename: str = Field(..., description="Original filename")
    size: int = Field(..., description="File size in bytes")
    content_type: str = Field(..., description="MIME type")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: Optional[str] = Field(default=None, description="Last update timestamp")
    chunk_count: int = Field(..., description="Number of chunks")
    language: Optional[str] = Field(default=None, description="Detected language")
    tags: Optional[List[str]] = Field(default=None, description="Document tags")


class DocumentProcessRequest(BaseModel):
    """Request for document processing."""
    chunk_size: Optional[int] = Field(default=1000, gt=0, description="Size of text chunks")
    chunk_overlap: Optional[int] = Field(default=200, ge=0, description="Overlap between chunks")
    extract_metadata: Optional[bool] = Field(default=True, description="Whether to extract metadata")
    generate_embeddings: Optional[bool] = Field(default=True, description="Whether to generate embeddings")


class DocumentProcessResponse(BaseModel):
    """Response from document processing."""
    document_id: str = Field(..., description="Generated document ID")
    filename: str = Field(..., description="Original filename")
    chunks_created: int = Field(..., description="Number of chunks created")
    processing_time: float = Field(..., description="Processing time in seconds")
    metadata: Dict[str, Any] = Field(..., description="Extracted metadata")


class EmbeddingRequest(BaseModel):
    """Request for embedding generation."""
    texts: List[str] = Field(..., description="Texts to embed")
    model: Optional[str] = Field(default=None, description="Embedding model to use")
    batch_size: Optional[int] = Field(default=100, gt=0, description="Batch size for processing")


class EmbeddingResponse(BaseModel):
    """Response from embedding generation."""
    embeddings: List[List[float]] = Field(..., description="Generated embeddings")
    model: str = Field(..., description="Model used for embeddings")
    dimension: int = Field(..., description="Embedding dimension")
    processing_time: float = Field(..., description="Processing time in seconds") 