"""
Chat-related Pydantic schemas for Brain_Net LLM Service
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class ChatMessage(BaseModel):
    """Individual chat message."""
    role: str = Field(..., description="Role of the message sender (user, assistant, system)")
    content: str = Field(..., description="Content of the message")
    timestamp: Optional[datetime] = Field(default=None, description="Timestamp of the message")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional message metadata")


class ChatRequest(BaseModel):
    """Request for chat completion."""
    messages: List[ChatMessage] = Field(..., description="List of chat messages")
    model: Optional[str] = Field(default=None, description="Model to use for completion")
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: Optional[int] = Field(default=None, gt=0, description="Maximum tokens to generate")
    session_id: Optional[str] = Field(default=None, description="Session ID for context")
    stream: Optional[bool] = Field(default=False, description="Whether to stream the response")


class ChatResponse(BaseModel):
    """Response from chat completion."""
    message: ChatMessage = Field(..., description="Generated message")
    model: str = Field(..., description="Model used for generation")
    usage: Optional[Dict[str, int]] = Field(default=None, description="Token usage statistics")
    session_id: Optional[str] = Field(default=None, description="Session ID")
    response_time: Optional[float] = Field(default=None, description="Response time in seconds")


class ChatHistoryResponse(BaseModel):
    """Response containing chat history."""
    session_id: str = Field(..., description="Session ID")
    messages: List[ChatMessage] = Field(..., description="List of chat messages")
    total_messages: int = Field(..., description="Total number of messages in session")
    summary: Optional[str] = Field(default=None, description="Session summary if available") 