"""
RAG-related Pydantic schemas for Brain_Net LLM Service
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class DocumentChunk(BaseModel):
    """Individual document chunk."""
    id: str = Field(..., description="Unique chunk identifier")
    content: str = Field(..., description="Chunk content")
    metadata: Dict[str, Any] = Field(..., description="Chunk metadata")
    score: Optional[float] = Field(default=None, description="Similarity score")


class RAGRequest(BaseModel):
    """Request for RAG query."""
    query: str = Field(..., description="Query string")
    collection: Optional[str] = Field(default="default", description="Document collection to search")
    top_k: Optional[int] = Field(default=5, gt=0, le=20, description="Number of documents to retrieve")
    threshold: Optional[float] = Field(default=0.7, ge=0.0, le=1.0, description="Similarity threshold")
    model: Optional[str] = Field(default=None, description="Model to use for generation")
    include_sources: Optional[bool] = Field(default=True, description="Whether to include source documents")


class RAGResponse(BaseModel):
    """Response from RAG query."""
    query: str = Field(..., description="Original query")
    answer: str = Field(..., description="Generated answer")
    sources: List[DocumentChunk] = Field(..., description="Source documents used")
    model: str = Field(..., description="Model used for generation")
    response_time: Optional[float] = Field(default=None, description="Response time in seconds")


class DocumentSearchRequest(BaseModel):
    """Request for document search."""
    query: str = Field(..., description="Search query")
    collection: Optional[str] = Field(default="default", description="Collection to search")
    top_k: Optional[int] = Field(default=10, gt=0, le=50, description="Number of results to return")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Additional filters")


class DocumentSearchResponse(BaseModel):
    """Response from document search."""
    query: str = Field(..., description="Original search query")
    documents: List[DocumentChunk] = Field(..., description="Matching documents")
    total_results: int = Field(..., description="Total number of matching documents")
    response_time: Optional[float] = Field(default=None, description="Response time in seconds") 