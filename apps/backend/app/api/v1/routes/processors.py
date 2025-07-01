"""
API routes for processor and pipeline management.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.processor_service import ProcessorService, get_processor_templates
from apps.shared.models import (
    UserProcessorCreate, UserPipelineCreate, ProcessorExecutionRequest,
    UserProcessorRead, UserPipelineRead, PipelineExecutionRead,
    UserProcessorList, UserPipelineList, PipelineExecutionList
)

router = APIRouter(prefix="/processors", tags=["processors"])


def get_processor_service(db: AsyncSession = Depends(get_db)) -> ProcessorService:
    """Get processor service instance."""
    return ProcessorService(db)


# ==================== PROCESSOR ROUTES ====================

@router.post("/", response_model=UserProcessorRead)
async def create_processor(
    processor_data: UserProcessorCreate,
    user_id: int = 1,  # TODO: Get from authentication
    service: ProcessorService = Depends(get_processor_service)
):
    """Create a new processor."""
    try:
        processor = await service.create_processor(user_id, processor_data)
        return UserProcessorRead.model_validate(processor)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=UserProcessorList)
async def get_processors(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    user_id: int = 1,  # TODO: Get from authentication
    service: ProcessorService = Depends(get_processor_service)
):
    """Get user's processors."""
    return await service.get_user_processors(user_id, skip, limit)


@router.get("/templates")
async def get_processor_templates_endpoint():
    """Get processor templates."""
    return {"templates": get_processor_templates()}


@router.get("/{processor_id}", response_model=UserProcessorRead)
async def get_processor(
    processor_id: int,
    user_id: int = 1,  # TODO: Get from authentication
    service: ProcessorService = Depends(get_processor_service)
):
    """Get a specific processor."""
    processor = await service.get_processor_by_id(user_id, processor_id)
    if not processor:
        raise HTTPException(status_code=404, detail="Processor not found")
    return UserProcessorRead.model_validate(processor)


@router.put("/{processor_id}", response_model=UserProcessorRead)
async def update_processor(
    processor_id: int,
    update_data: dict,
    user_id: int = 1,  # TODO: Get from authentication
    service: ProcessorService = Depends(get_processor_service)
):
    """Update a processor."""
    try:
        processor = await service.update_processor(user_id, processor_id, update_data)
        if not processor:
            raise HTTPException(status_code=404, detail="Processor not found")
        return UserProcessorRead.model_validate(processor)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{processor_id}")
async def delete_processor(
    processor_id: int,
    user_id: int = 1,  # TODO: Get from authentication
    service: ProcessorService = Depends(get_processor_service)
):
    """Delete a processor."""
    try:
        success = await service.delete_processor(user_id, processor_id)
        if not success:
            raise HTTPException(status_code=404, detail="Processor not found")
        return {"message": "Processor deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== PIPELINE ROUTES ====================

@router.post("/pipelines", response_model=UserPipelineRead)
async def create_pipeline(
    pipeline_data: UserPipelineCreate,
    user_id: int = 1,  # TODO: Get from authentication
    service: ProcessorService = Depends(get_processor_service)
):
    """Create a new pipeline."""
    try:
        pipeline = await service.create_pipeline(user_id, pipeline_data)
        return UserPipelineRead.model_validate(pipeline)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/pipelines", response_model=UserPipelineList)
async def get_pipelines(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    user_id: int = 1,  # TODO: Get from authentication
    service: ProcessorService = Depends(get_processor_service)
):
    """Get user's pipelines."""
    return await service.get_user_pipelines(user_id, skip, limit)


@router.get("/pipelines/{pipeline_id}", response_model=UserPipelineRead)
async def get_pipeline(
    pipeline_id: int,
    user_id: int = 1,  # TODO: Get from authentication
    service: ProcessorService = Depends(get_processor_service)
):
    """Get a specific pipeline."""
    pipeline = await service.get_pipeline_by_id(user_id, pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return UserPipelineRead.model_validate(pipeline)


@router.put("/pipelines/{pipeline_id}", response_model=UserPipelineRead)
async def update_pipeline(
    pipeline_id: int,
    update_data: dict,
    user_id: int = 1,  # TODO: Get from authentication
    service: ProcessorService = Depends(get_processor_service)
):
    """Update a pipeline."""
    try:
        pipeline = await service.update_pipeline(user_id, pipeline_id, update_data)
        if not pipeline:
            raise HTTPException(status_code=404, detail="Pipeline not found")
        return UserPipelineRead.model_validate(pipeline)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/pipelines/{pipeline_id}")
async def delete_pipeline(
    pipeline_id: int,
    user_id: int = 1,  # TODO: Get from authentication
    service: ProcessorService = Depends(get_processor_service)
):
    """Delete a pipeline."""
    try:
        success = await service.delete_pipeline(user_id, pipeline_id)
        if not success:
            raise HTTPException(status_code=404, detail="Pipeline not found")
        return {"message": "Pipeline deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== EXECUTION ROUTES ====================

@router.post("/pipelines/{pipeline_id}/execute")
async def execute_pipeline(
    pipeline_id: int,
    execution_request: ProcessorExecutionRequest,
    user_id: int = 1,  # TODO: Get from authentication
    service: ProcessorService = Depends(get_processor_service)
):
    """Execute a pipeline on a file."""
    try:
        execution_request.pipeline_id = pipeline_id
        execution_id = await service.execute_pipeline(user_id, execution_request)
        return {
            "execution_id": execution_id,
            "status": "started",
            "message": "Pipeline execution started successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/executions", response_model=PipelineExecutionList)
async def get_executions(
    pipeline_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    user_id: int = 1,  # TODO: Get from authentication
    service: ProcessorService = Depends(get_processor_service)
):
    """Get pipeline executions."""
    return await service.get_pipeline_executions(user_id, pipeline_id, skip, limit)


@router.get("/executions/{execution_id}", response_model=PipelineExecutionRead)
async def get_execution(
    execution_id: str,
    user_id: int = 1,  # TODO: Get from authentication
    service: ProcessorService = Depends(get_processor_service)
):
    """Get a specific pipeline execution."""
    execution = await service.get_execution_by_id(user_id, execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    return PipelineExecutionRead.model_validate(execution) 