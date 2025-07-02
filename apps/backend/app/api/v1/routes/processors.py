"""
API routes for processor and pipeline management.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import DatabaseManager
from app.services.processor_service import ProcessorService, get_processor_templates
from app.services.auth import AuthService, security
from apps.shared.models import (
    User, UserProcessorCreate, UserPipelineCreate, ProcessorExecutionRequest,
    UserProcessorRead, UserPipelineRead, PipelineExecutionRead,
    UserProcessorList, UserPipelineList, PipelineExecutionList
)

router = APIRouter(prefix="/processors", tags=["processors"])


async def get_db(request: Request) -> AsyncSession:
    """Dependency to get database session."""
    db_manager: DatabaseManager = request.app.state.db_manager
    async with db_manager.get_postgres_session() as session:
        yield session


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Dependency to get current authenticated user."""
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not credentials:
        raise credentials_exception
    
    token_data = AuthService.verify_token(credentials.credentials)
    if token_data is None:
        raise credentials_exception
    
    user = await AuthService.get_user_by_id(db, token_data.user_id)
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    return user


def get_processor_service(db: AsyncSession = Depends(get_db)) -> ProcessorService:
    """Get processor service instance."""
    return ProcessorService(db)


# ==================== PROCESSOR ROUTES ====================

@router.post("/", response_model=UserProcessorRead)
async def create_processor(
    processor_data: UserProcessorCreate,
    current_user: User = Depends(get_current_user),
    service: ProcessorService = Depends(get_processor_service)
):
    """Create a new processor."""
    try:
        processor = await service.create_processor(current_user.id, processor_data)
        return UserProcessorRead.model_validate(processor)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=UserProcessorList)
async def get_processors(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: ProcessorService = Depends(get_processor_service)
):
    """Get user's processors."""
    return await service.get_user_processors(current_user.id, skip, limit)


@router.get("/templates")
async def get_processor_templates_endpoint():
    """Get processor templates."""
    return {"templates": get_processor_templates()}


@router.get("/{processor_id}", response_model=UserProcessorRead)
async def get_processor(
    processor_id: int,
    current_user: User = Depends(get_current_user),
    service: ProcessorService = Depends(get_processor_service)
):
    """Get a specific processor."""
    processor = await service.get_processor_by_id(current_user.id, processor_id)
    if not processor:
        raise HTTPException(status_code=404, detail="Processor not found")
    return UserProcessorRead.model_validate(processor)


@router.put("/{processor_id}", response_model=UserProcessorRead)
async def update_processor(
    processor_id: int,
    update_data: dict,
    current_user: User = Depends(get_current_user),
    service: ProcessorService = Depends(get_processor_service)
):
    """Update a processor."""
    try:
        processor = await service.update_processor(current_user.id, processor_id, update_data)
        if not processor:
            raise HTTPException(status_code=404, detail="Processor not found")
        return UserProcessorRead.model_validate(processor)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{processor_id}")
async def delete_processor(
    processor_id: int,
    current_user: User = Depends(get_current_user),
    service: ProcessorService = Depends(get_processor_service)
):
    """Delete a processor."""
    try:
        success = await service.delete_processor(current_user.id, processor_id)
        if not success:
            raise HTTPException(status_code=404, detail="Processor not found")
        return {"message": "Processor deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== PIPELINE ROUTES ====================

@router.post("/pipelines", response_model=UserPipelineRead)
async def create_pipeline(
    pipeline_data: UserPipelineCreate,
    current_user: User = Depends(get_current_user),
    service: ProcessorService = Depends(get_processor_service)
):
    """Create a new pipeline."""
    try:
        pipeline = await service.create_pipeline(current_user.id, pipeline_data)
        return UserPipelineRead.model_validate(pipeline)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/pipelines", response_model=UserPipelineList)
async def get_pipelines(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: ProcessorService = Depends(get_processor_service)
):
    """Get user's pipelines."""
    return await service.get_user_pipelines(current_user.id, skip, limit)


@router.get("/pipelines/{pipeline_id}", response_model=UserPipelineRead)
async def get_pipeline(
    pipeline_id: int,
    current_user: User = Depends(get_current_user),
    service: ProcessorService = Depends(get_processor_service)
):
    """Get a specific pipeline."""
    pipeline = await service.get_pipeline_by_id(current_user.id, pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return UserPipelineRead.model_validate(pipeline)


@router.put("/pipelines/{pipeline_id}", response_model=UserPipelineRead)
async def update_pipeline(
    pipeline_id: int,
    update_data: dict,
    current_user: User = Depends(get_current_user),
    service: ProcessorService = Depends(get_processor_service)
):
    """Update a pipeline."""
    try:
        pipeline = await service.update_pipeline(current_user.id, pipeline_id, update_data)
        if not pipeline:
            raise HTTPException(status_code=404, detail="Pipeline not found")
        return UserPipelineRead.model_validate(pipeline)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/pipelines/{pipeline_id}")
async def delete_pipeline(
    pipeline_id: int,
    current_user: User = Depends(get_current_user),
    service: ProcessorService = Depends(get_processor_service)
):
    """Delete a pipeline."""
    try:
        success = await service.delete_pipeline(current_user.id, pipeline_id)
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
    current_user: User = Depends(get_current_user),
    service: ProcessorService = Depends(get_processor_service)
):
    """Execute a pipeline on a file."""
    try:
        execution_request.pipeline_id = pipeline_id
        execution_id = await service.execute_pipeline(current_user.id, execution_request)
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
    current_user: User = Depends(get_current_user),
    service: ProcessorService = Depends(get_processor_service)
):
    """Get pipeline executions."""
    return await service.get_pipeline_executions(current_user.id, pipeline_id, skip, limit)


@router.get("/executions/{execution_id}", response_model=PipelineExecutionRead)
async def get_execution(
    execution_id: str,
    current_user: User = Depends(get_current_user),
    service: ProcessorService = Depends(get_processor_service)
):
    """Get a specific pipeline execution."""
    execution = await service.get_execution_by_id(current_user.id, execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    return PipelineExecutionRead.model_validate(execution)


# ==================== ADDITIONAL PROCESSOR UTILITY ROUTES ====================

@router.post("/{processor_id}/test")
async def test_processor(
    processor_id: int,
    test_data: dict,
    current_user: User = Depends(get_current_user),
    service: ProcessorService = Depends(get_processor_service)
):
    """Test a processor with sample data."""
    processor = await service.get_processor_by_id(current_user.id, processor_id)
    if not processor:
        raise HTTPException(status_code=404, detail="Processor not found")
    
    # TODO: Implement processor testing logic
    # This would create a temporary processor instance and test it with the provided data
    return {
        "message": "Processor test endpoint - implementation pending",
        "processor_id": processor_id,
        "test_data": test_data
    }


@router.get("/{processor_id}/usage-stats")
async def get_processor_usage_stats(
    processor_id: int,
    current_user: User = Depends(get_current_user),
    service: ProcessorService = Depends(get_processor_service)
):
    """Get usage statistics for a processor."""
    processor = await service.get_processor_by_id(current_user.id, processor_id)
    if not processor:
        raise HTTPException(status_code=404, detail="Processor not found")
    
    return {
        "processor_id": processor_id,
        "name": processor.name,
        "usage_count": processor.usage_count,
        "last_used": processor.last_used,
        "status": processor.status,
        "created_at": processor.created_at
    }


@router.get("/pipelines/{pipeline_id}/usage-stats")
async def get_pipeline_usage_stats(
    pipeline_id: int,
    current_user: User = Depends(get_current_user),
    service: ProcessorService = Depends(get_processor_service)
):
    """Get usage statistics for a pipeline."""
    pipeline = await service.get_pipeline_by_id(current_user.id, pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    return {
        "pipeline_id": pipeline_id,
        "name": pipeline.name,
        "execution_count": pipeline.execution_count,
        "last_executed": pipeline.last_executed,
        "average_execution_time": pipeline.average_execution_time,
        "status": pipeline.status,
        "created_at": pipeline.created_at
    }


# ==================== FILE-PROCESSOR INTEGRATION ROUTES ====================

@router.get("/compatible-processors")
async def get_compatible_processors(
    file_type: Optional[str] = Query(None, description="Filter by file type compatibility"),
    input_type: Optional[str] = Query(None, description="Filter by input type"),
    capability: Optional[str] = Query(None, description="Filter by processing capability"),
    current_user: User = Depends(get_current_user),
    service: ProcessorService = Depends(get_processor_service)
):
    """Get processors compatible with specific file types or requirements."""
    processors = await service.get_user_processors(current_user.id, 0, 1000)
    
    compatible_processors = []
    for processor in processors.processors:
        # Apply filters
        if file_type and file_type not in processor.input_types:
            continue
        if input_type and input_type not in processor.input_types:
            continue
        if capability and capability not in processor.processing_capabilities:
            continue
        
        compatible_processors.append({
            "id": processor.id,
            "name": processor.name,
            "description": processor.description,
            "input_types": processor.input_types,
            "output_types": processor.output_types,
            "processing_capabilities": processor.processing_capabilities,
            "usage_count": processor.usage_count,
            "status": processor.status
        })
    
    return {
        "compatible_processors": compatible_processors,
        "count": len(compatible_processors),
        "filters_applied": {
            "file_type": file_type,
            "input_type": input_type,
            "capability": capability
        }
    }


@router.post("/batch-execute")
async def batch_execute_pipeline(
    batch_request: dict,
    current_user: User = Depends(get_current_user),
    service: ProcessorService = Depends(get_processor_service)
):
    """Execute a pipeline on multiple files in batch."""
    pipeline_id = batch_request.get("pipeline_id")
    file_hashes = batch_request.get("file_hashes", [])
    custom_config = batch_request.get("custom_config", {})
    
    if not pipeline_id:
        raise HTTPException(status_code=400, detail="pipeline_id is required")
    if not file_hashes:
        raise HTTPException(status_code=400, detail="file_hashes list is required")
    
    # Verify pipeline exists
    pipeline = await service.get_pipeline_by_id(current_user.id, pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    execution_ids = []
    for file_hash in file_hashes:
        try:
            execution_request = ProcessorExecutionRequest(
                pipeline_id=pipeline_id,
                file_hash=file_hash,
                custom_config=custom_config
            )
            execution_id = await service.execute_pipeline(current_user.id, execution_request)
            execution_ids.append({
                "file_hash": file_hash,
                "execution_id": execution_id,
                "status": "started"
            })
        except Exception as e:
            execution_ids.append({
                "file_hash": file_hash,
                "execution_id": None,
                "status": "failed",
                "error": str(e)
            })
    
    return {
        "pipeline_id": pipeline_id,
        "batch_size": len(file_hashes),
        "executions": execution_ids,
        "successful_starts": len([e for e in execution_ids if e["status"] == "started"]),
        "failed_starts": len([e for e in execution_ids if e["status"] == "failed"])
    }


@router.get("/file/{file_hash}/processing-history")
async def get_file_processing_history(
    file_hash: str,
    current_user: User = Depends(get_current_user),
    service: ProcessorService = Depends(get_processor_service)
):
    """Get processing history for a specific file."""
    # Get all executions for this user that involve this file
    all_executions = await service.get_pipeline_executions(current_user.id, None, 0, 1000)
    
    file_executions = [
        execution for execution in all_executions.executions
        if execution.file_hash == file_hash
    ]
    
    return {
        "file_hash": file_hash,
        "processing_history": file_executions,
        "total_processes": len(file_executions),
        "successful_processes": len([e for e in file_executions if e.status == "COMPLETED"]),
        "failed_processes": len([e for e in file_executions if e.status == "FAILED"]),
        "running_processes": len([e for e in file_executions if e.status == "RUNNING"])
    }


@router.post("/pipeline-recommendations")
async def get_pipeline_recommendations(
    request_data: dict,
    current_user: User = Depends(get_current_user),
    service: ProcessorService = Depends(get_processor_service)
):
    """Get pipeline recommendations based on file type and processing goals."""
    file_type = request_data.get("file_type")
    processing_goals = request_data.get("processing_goals", [])
    user_preferences = request_data.get("user_preferences", {})
    
    # Get user's processors and pipelines
    processors = await service.get_user_processors(current_user.id, 0, 1000)
    pipelines = await service.get_user_pipelines(current_user.id, 0, 1000)
    
    recommendations = []
    
    # Recommend existing pipelines
    for pipeline in pipelines.pipelines:
        score = 0
        
        # Check if pipeline processors match file type
        pipeline_processors = []
        for step in pipeline.processor_sequence:
            processor_id = step.get("processor_id")
            processor = next((p for p in processors.processors if p.id == processor_id), None)
            if processor:
                pipeline_processors.append(processor)
        
        # Score based on input type compatibility
        if file_type:
            compatible_processors = [p for p in pipeline_processors if file_type in p.input_types]
            if compatible_processors:
                score += 40
        
        # Score based on processing goals
        for goal in processing_goals:
            matching_capabilities = [
                p for p in pipeline_processors 
                if goal in p.processing_capabilities
            ]
            score += len(matching_capabilities) * 20
        
        # Score based on usage frequency
        score += min(pipeline.execution_count * 5, 20)
        
        if score > 0:
            recommendations.append({
                "type": "existing_pipeline",
                "pipeline_id": pipeline.id,
                "name": pipeline.name,
                "description": pipeline.description,
                "score": score,
                "processors_count": len(pipeline_processors),
                "execution_count": pipeline.execution_count,
                "last_executed": pipeline.last_executed
            })
    
    # Recommend individual processors for new pipeline creation
    for processor in processors.processors:
        score = 0
        
        # Score based on file type compatibility
        if file_type and file_type in processor.input_types:
            score += 30
        
        # Score based on processing goals
        for goal in processing_goals:
            if goal in processor.processing_capabilities:
                score += 25
        
        # Score based on usage frequency
        score += min(processor.usage_count * 3, 15)
        
        if score > 0:
            recommendations.append({
                "type": "standalone_processor",
                "processor_id": processor.id,
                "name": processor.name,
                "description": processor.description,
                "score": score,
                "input_types": processor.input_types,
                "output_types": processor.output_types,
                "processing_capabilities": processor.processing_capabilities,
                "usage_count": processor.usage_count
            })
    
    # Sort by score (descending)
    recommendations.sort(key=lambda x: x["score"], reverse=True)
    
    return {
        "file_type": file_type,
        "processing_goals": processing_goals,
        "recommendations": recommendations[:10],  # Top 10 recommendations
        "total_found": len(recommendations)
    } 