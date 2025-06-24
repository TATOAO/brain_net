"""
Models API routes for Brain_Net LLM Service
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any

from app.schemas.models import ModelInfo, ModelLoadRequest, ModelLoadResponse
from app.services.models import ModelService
from app.core.dependencies import get_model_service

router = APIRouter()


@router.get("/available", response_model=List[ModelInfo])
async def list_available_models(
    model_service: ModelService = Depends(get_model_service)
) -> List[ModelInfo]:
    """List all available models."""
    try:
        models = await model_service.list_available_models()
        return models
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list models: {str(e)}")


@router.get("/loaded", response_model=List[ModelInfo])
async def list_loaded_models(
    model_service: ModelService = Depends(get_model_service)
) -> List[ModelInfo]:
    """List currently loaded models."""
    try:
        models = await model_service.list_loaded_models()
        return models
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list loaded models: {str(e)}")


@router.post("/load", response_model=ModelLoadResponse)
async def load_model(
    request: ModelLoadRequest,
    model_service: ModelService = Depends(get_model_service)
) -> ModelLoadResponse:
    """Load a model into memory."""
    try:
        response = await model_service.load_model(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model loading failed: {str(e)}")


@router.delete("/unload/{model_name}")
async def unload_model(
    model_name: str,
    model_service: ModelService = Depends(get_model_service)
) -> dict:
    """Unload a model from memory."""
    try:
        await model_service.unload_model(model_name)
        return {"message": f"Model {model_name} unloaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model unloading failed: {str(e)}")


@router.get("/info/{model_name}", response_model=ModelInfo)
async def get_model_info(
    model_name: str,
    model_service: ModelService = Depends(get_model_service)
) -> ModelInfo:
    """Get detailed information about a specific model."""
    try:
        info = await model_service.get_model_info(model_name)
        return info
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get model info: {str(e)}")


@router.get("/health/{model_name}")
async def check_model_health(
    model_name: str,
    model_service: ModelService = Depends(get_model_service)
) -> dict:
    """Check the health status of a specific model."""
    try:
        health = await model_service.check_model_health(model_name)
        return health
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model health check failed: {str(e)}")


@router.get("/stats")
async def get_model_stats(
    model_service: ModelService = Depends(get_model_service)
) -> Dict[str, Any]:
    """Get statistics about model usage and performance."""
    try:
        stats = await model_service.get_model_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get model stats: {str(e)}")


@router.post("/preload")
async def preload_default_models(
    model_service: ModelService = Depends(get_model_service)
) -> dict:
    """Preload default models for faster startup."""
    try:
        await model_service.preload_default_models()
        return {"message": "Default models preloading started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model preloading failed: {str(e)}")


@router.delete("/cache/clear")
async def clear_model_cache(
    model_service: ModelService = Depends(get_model_service)
) -> dict:
    """Clear the model cache."""
    try:
        await model_service.clear_cache()
        return {"message": "Model cache cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cache clearing failed: {str(e)}") 