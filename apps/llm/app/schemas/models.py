"""
Model-related Pydantic schemas for Brain_Net LLM Service
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class ModelType(str, Enum):
    """Model types."""
    CHAT = "chat"
    EMBEDDING = "embedding"
    COMPLETION = "completion"
    CLASSIFICATION = "classification"


class ModelProvider(str, Enum):
    """Model providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    HUGGINGFACE = "huggingface"
    LOCAL = "local"


class ModelInfo(BaseModel):
    """Information about a model."""
    name: str = Field(..., description="Model name")
    provider: ModelProvider = Field(..., description="Model provider")
    type: ModelType = Field(..., description="Model type")
    description: str = Field(..., description="Model description")
    max_tokens: int = Field(..., description="Maximum tokens supported")
    is_loaded: bool = Field(default=False, description="Whether model is currently loaded")
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="Model parameters")
    pricing: Optional[Dict[str, float]] = Field(default=None, description="Pricing information")


class ModelLoadRequest(BaseModel):
    """Request to load a model."""
    model_name: str = Field(..., description="Name of the model to load")
    config: Optional[Dict[str, Any]] = Field(default=None, description="Model configuration")
    force_reload: Optional[bool] = Field(default=False, description="Force reload if already loaded")


class ModelLoadResponse(BaseModel):
    """Response from model loading."""
    model_name: str = Field(..., description="Name of the loaded model")
    success: bool = Field(..., description="Whether loading was successful")
    message: str = Field(..., description="Status message")
    load_time: float = Field(..., description="Time taken to load the model")
    memory_usage: Optional[str] = Field(default=None, description="Memory usage after loading") 