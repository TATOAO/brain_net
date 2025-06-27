"""
Document Processor API routes for Brain_Net LLM Service
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from apps.shared.core.processor_service import document_processor_service
from apps.shared.core.processor import ProcessingType, DocumentFormat
from apps.shared.models.user import User
from apps.shared.models.file import UserFile
from app.services.minio_service import MinIOService
from app.core.dependencies import get_minio_service

router = APIRouter()


class ProcessorListResponse(BaseModel):
    """Response for listing available processors."""
    processors_by_type: Dict[ProcessingType, List[Dict[str, Any]]]
    total_processors: int


class ProcessorInfoResponse(BaseModel):
    """Response for processor information."""
    processor_info: Optional[Dict[str, Any]]


class ProcessingRequest(BaseModel):
    """Request for document processing."""
    file_hash: str
    user_id: int
    filename: Optional[str] = None
    pipeline: List[Dict[str, Any]]
    global_parameters: Optional[Dict[str, Any]] = None


class ChunkingRequest(BaseModel):
    """Request for document chunking."""
    file_hash: str
    user_id: int
    filename: Optional[str] = None
    chunker_id: str = "fixed_size_chunker"
    chunk_size: int = 1000
    overlap: int = 200
    additional_params: Optional[Dict[str, Any]] = None


class NERRequest(BaseModel):
    """Request for named entity recognition."""
    file_hash: str
    user_id: int
    filename: Optional[str] = None
    ner_processor_id: str = "simple_ner"
    entity_types: Optional[List[str]] = None
    additional_params: Optional[Dict[str, Any]] = None


class ProcessingSuggestionsRequest(BaseModel):
    """Request for processing suggestions."""
    document_format: DocumentFormat
    user_preferences: Optional[Dict[str, Any]] = None


@router.get("/processors", response_model=ProcessorListResponse)
async def list_processors() -> ProcessorListResponse:
    """List all available document processors grouped by type."""
    try:
        processors_by_type = document_processor_service.get_available_processors()
        total_processors = sum(len(processors) for processors in processors_by_type.values())
        
        return ProcessorListResponse(
            processors_by_type=processors_by_type,
            total_processors=total_processors
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list processors: {str(e)}")


@router.get("/processors/{processor_id}", response_model=ProcessorInfoResponse)
async def get_processor_info(processor_id: str) -> ProcessorInfoResponse:
    """Get information about a specific processor."""
    try:
        processor_info = document_processor_service.get_processor_info(processor_id)
        return ProcessorInfoResponse(processor_info=processor_info)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get processor info: {str(e)}")


@router.post("/process")
async def process_document(
    request: ProcessingRequest,
    background_tasks: BackgroundTasks,
    minio_service: MinIOService = Depends(get_minio_service)
) -> dict:
    """Process a document using specified processing pipeline."""
    try:
        # Validate pipeline configuration
        validation_result = await document_processor_service.validate_processing_config({
            "pipeline": request.pipeline,
            "global_parameters": request.global_parameters or {}
        })
        
        if not validation_result["valid"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid pipeline configuration: {validation_result['errors']}"
            )
        
        # Check if document exists in MinIO
        if not minio_service.file_exists(request.file_hash):
            raise HTTPException(status_code=404, detail="Document not found in storage")
        
        # Get document content
        file_stream = minio_service.get_file_stream(request.file_hash)
        document_content = file_stream.read().decode('utf-8', errors='ignore')
        file_stream.close()
        
        # Create mock user and user_file objects for processing
        # In a real implementation, you'd fetch these from the database
        class MockUser:
            def __init__(self, user_id: int):
                self.id = user_id
        
        class MockUserFile:
            def __init__(self, file_hash: str, filename: str):
                self.id = 1  # Mock ID
                self.file_hash = file_hash
                self.original_filename = filename or "document.txt"
                self.content_type = "text/plain"  # Default
                self.file_size = len(document_content)
                self.uploaded_at = None
        
        user = MockUser(request.user_id)
        user_file = MockUserFile(request.file_hash, request.filename)
        
        # Process document
        processing_config = {
            "pipeline": request.pipeline,
            "global_parameters": request.global_parameters or {}
        }
        
        processed_document = await document_processor_service.process_user_document(
            user=user,
            user_file=user_file,
            document_content=document_content,
            processing_config=processing_config
        )
        
        # Format response
        return {
            "status": "completed",
            "document_id": processed_document.document_id,
            "filename": processed_document.original_filename,
            "processing_results": [result.model_dump() for result in processed_document.processing_results],
            "chunks_created": len(processed_document.chunks),
            "total_chunks": len(processed_document.chunks),
            "metadata": processed_document.metadata
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document processing failed: {str(e)}")


@router.post("/chunk")
async def chunk_document(
    request: ChunkingRequest,
    minio_service: MinIOService = Depends(get_minio_service)
) -> dict:
    """Chunk a document using specified chunker."""
    try:
        # Check if document exists
        if not minio_service.file_exists(request.file_hash):
            raise HTTPException(status_code=404, detail="Document not found in storage")
        
        # Get document content
        file_stream = minio_service.get_file_stream(request.file_hash)
        document_content = file_stream.read().decode('utf-8', errors='ignore')
        file_stream.close()
        
        # Create mock objects
        class MockUser:
            def __init__(self, user_id: int):
                self.id = user_id
        
        class MockUserFile:
            def __init__(self, file_hash: str, filename: str):
                self.id = 1
                self.file_hash = file_hash
                self.original_filename = filename or "document.txt"
                self.content_type = "text/plain"
                self.file_size = len(document_content)
                self.uploaded_at = None
        
        user = MockUser(request.user_id)
        user_file = MockUserFile(request.file_hash, request.filename)
        
        # Chunk document
        additional_params = request.additional_params or {}
        chunks = await document_processor_service.chunk_document(
            user=user,
            user_file=user_file,
            document_content=document_content,
            chunker_id=request.chunker_id,
            chunk_size=request.chunk_size,
            overlap=request.overlap,
            **additional_params
        )
        
        return {
            "status": "completed",
            "chunker_id": request.chunker_id,
            "chunks_created": len(chunks),
            "chunks": [chunk.model_dump() for chunk in chunks],
            "parameters": {
                "chunk_size": request.chunk_size,
                "overlap": request.overlap,
                **additional_params
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document chunking failed: {str(e)}")


@router.post("/extract-entities")
async def extract_entities(
    request: NERRequest,
    minio_service: MinIOService = Depends(get_minio_service)
) -> dict:
    """Extract named entities from a document."""
    try:
        # Check if document exists
        if not minio_service.file_exists(request.file_hash):
            raise HTTPException(status_code=404, detail="Document not found in storage")
        
        # Get document content
        file_stream = minio_service.get_file_stream(request.file_hash)
        document_content = file_stream.read().decode('utf-8', errors='ignore')
        file_stream.close()
        
        # Create mock objects
        class MockUser:
            def __init__(self, user_id: int):
                self.id = user_id
        
        class MockUserFile:
            def __init__(self, file_hash: str, filename: str):
                self.id = 1
                self.file_hash = file_hash
                self.original_filename = filename or "document.txt"
                self.content_type = "text/plain"
                self.file_size = len(document_content)
                self.uploaded_at = None
        
        user = MockUser(request.user_id)
        user_file = MockUserFile(request.file_hash, request.filename)
        
        # Extract entities
        additional_params = request.additional_params or {}
        entities = await document_processor_service.extract_entities(
            user=user,
            user_file=user_file,
            document_content=document_content,
            ner_processor_id=request.ner_processor_id,
            entity_types=request.entity_types,
            **additional_params
        )
        
        return {
            "status": "completed",
            "ner_processor_id": request.ner_processor_id,
            "entity_types": request.entity_types,
            "entities_found": len(entities),
            "entities": entities
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Entity extraction failed: {str(e)}")


@router.post("/suggestions")
async def get_processing_suggestions(request: ProcessingSuggestionsRequest) -> dict:
    """Get processing suggestions based on document format and user preferences."""
    try:
        suggestions = await document_processor_service.get_processing_suggestions(
            document_format=request.document_format,
            user_preferences=request.user_preferences
        )
        
        return {
            "document_format": request.document_format,
            "suggestions": suggestions
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get suggestions: {str(e)}")


@router.post("/validate-pipeline")
async def validate_pipeline(pipeline_config: List[Dict[str, Any]]) -> dict:
    """Validate a processing pipeline configuration."""
    try:
        validation_result = await document_processor_service.validate_processing_config({
            "pipeline": pipeline_config
        })
        
        return validation_result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline validation failed: {str(e)}") 