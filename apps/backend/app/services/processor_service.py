"""
Processor Service for Brain_Net Backend
Manages user-defined processors and pipelines using the processor_pipeline module.
"""

import asyncio
import uuid
import json
import traceback
from datetime import datetime
from typing import Optional, Dict, Any, List, AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload

from app.core.processors import (
    AsyncPipeline, AsyncProcessor, execute_processor_code,
    create_processor_from_registry, create_pipeline_from_config
)
from apps.shared.models import (
    UserProcessor, UserPipeline, PipelineExecution,
    UserProcessorCreate, UserPipelineCreate, ProcessorExecutionRequest,
    UserProcessorRead, UserPipelineRead, PipelineExecutionRead,
    UserProcessorList, UserPipelineList, PipelineExecutionList,
    ProcessorStatus, ProcessorType, PipelineStatus
)


class ProcessorService:
    """Service for managing user processors and pipelines."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # ==================== PROCESSOR MANAGEMENT ====================
    
    async def create_processor(self, user_id: int, processor_data: UserProcessorCreate) -> UserProcessor:
        """Create a new user processor."""
        try:
            # Validate processor code by trying to execute it
            await self._validate_processor_code(processor_data.processor_code)
            
            processor = UserProcessor(
                user_id=user_id,
                **processor_data.model_dump()
            )
            
            self.db.add(processor)
            await self.db.commit()
            await self.db.refresh(processor)
            
            return processor
        
        except Exception as e:
            await self.db.rollback()
            raise ValueError(f"Failed to create processor: {str(e)}")
    
    async def get_user_processors(self, user_id: int, skip: int = 0, limit: int = 100) -> UserProcessorList:
        """Get all processors for a user."""
        # Get total count
        count_stmt = select(UserProcessor).where(UserProcessor.user_id == user_id)
        count_result = await self.db.execute(count_stmt)
        total_count = len(count_result.scalars().all())
        
        # Get paginated results
        stmt = select(UserProcessor).where(
            UserProcessor.user_id == user_id
        ).offset(skip).limit(limit).order_by(UserProcessor.created_at.desc())
        
        result = await self.db.execute(stmt)
        processors = result.scalars().all()
        
        processor_reads = [
            UserProcessorRead.model_validate(processor)
            for processor in processors
        ]
        
        return UserProcessorList(
            processors=processor_reads,
            total_count=total_count
        )
    
    async def get_processor_by_id(self, user_id: int, processor_id: int) -> Optional[UserProcessor]:
        """Get a specific processor by ID."""
        stmt = select(UserProcessor).where(
            UserProcessor.id == processor_id,
            UserProcessor.user_id == user_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def update_processor(self, user_id: int, processor_id: int, update_data: Dict[str, Any]) -> Optional[UserProcessor]:
        """Update a processor."""
        try:
            # If updating processor code, validate it first
            if 'processor_code' in update_data:
                await self._validate_processor_code(update_data['processor_code'])
            
            stmt = update(UserProcessor).where(
                UserProcessor.id == processor_id,
                UserProcessor.user_id == user_id
            ).values(**update_data).returning(UserProcessor)
            
            result = await self.db.execute(stmt)
            processor = result.scalar_one_or_none()
            
            if processor:
                await self.db.commit()
                await self.db.refresh(processor)
            else:
                await self.db.rollback()
            
            return processor
        
        except Exception as e:
            await self.db.rollback()
            raise ValueError(f"Failed to update processor: {str(e)}")
    
    async def delete_processor(self, user_id: int, processor_id: int) -> bool:
        """Delete a processor."""
        try:
            stmt = delete(UserProcessor).where(
                UserProcessor.id == processor_id,
                UserProcessor.user_id == user_id
            )
            
            result = await self.db.execute(stmt)
            await self.db.commit()
            
            return result.rowcount > 0
        
        except Exception as e:
            await self.db.rollback()
            raise ValueError(f"Failed to delete processor: {str(e)}")
    
    # ==================== PIPELINE MANAGEMENT ====================
    
    async def create_pipeline(self, user_id: int, pipeline_data: UserPipelineCreate) -> UserPipeline:
        """Create a new user pipeline."""
        try:
            # Validate that all processors in the sequence exist
            await self._validate_pipeline_sequence(user_id, pipeline_data.processor_sequence)
            
            pipeline = UserPipeline(
                user_id=user_id,
                **pipeline_data.model_dump()
            )
            
            self.db.add(pipeline)
            await self.db.commit()
            await self.db.refresh(pipeline)
            
            return pipeline
        
        except Exception as e:
            await self.db.rollback()
            raise ValueError(f"Failed to create pipeline: {str(e)}")
    
    async def get_user_pipelines(self, user_id: int, skip: int = 0, limit: int = 100) -> UserPipelineList:
        """Get all pipelines for a user."""
        # Get total count
        count_stmt = select(UserPipeline).where(UserPipeline.user_id == user_id)
        count_result = await self.db.execute(count_stmt)
        total_count = len(count_result.scalars().all())
        
        # Get paginated results
        stmt = select(UserPipeline).where(
            UserPipeline.user_id == user_id
        ).offset(skip).limit(limit).order_by(UserPipeline.created_at.desc())
        
        result = await self.db.execute(stmt)
        pipelines = result.scalars().all()
        
        pipeline_reads = [
            UserPipelineRead.model_validate(pipeline)
            for pipeline in pipelines
        ]
        
        return UserPipelineList(
            pipelines=pipeline_reads,
            total_count=total_count
        )
    
    async def get_pipeline_by_id(self, user_id: int, pipeline_id: int) -> Optional[UserPipeline]:
        """Get a specific pipeline by ID."""
        stmt = select(UserPipeline).where(
            UserPipeline.id == pipeline_id,
            UserPipeline.user_id == user_id
        ).options(selectinload(UserPipeline.executions))
        
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def update_pipeline(self, user_id: int, pipeline_id: int, update_data: Dict[str, Any]) -> Optional[UserPipeline]:
        """Update a pipeline."""
        try:
            # If updating processor sequence, validate it
            if 'processor_sequence' in update_data:
                await self._validate_pipeline_sequence(user_id, update_data['processor_sequence'])
            
            stmt = update(UserPipeline).where(
                UserPipeline.id == pipeline_id,
                UserPipeline.user_id == user_id
            ).values(**update_data).returning(UserPipeline)
            
            result = await self.db.execute(stmt)
            pipeline = result.scalar_one_or_none()
            
            if pipeline:
                await self.db.commit()
                await self.db.refresh(pipeline)
            else:
                await self.db.rollback()
            
            return pipeline
        
        except Exception as e:
            await self.db.rollback()
            raise ValueError(f"Failed to update pipeline: {str(e)}")
    
    async def delete_pipeline(self, user_id: int, pipeline_id: int) -> bool:
        """Delete a pipeline."""
        try:
            stmt = delete(UserPipeline).where(
                UserPipeline.id == pipeline_id,
                UserPipeline.user_id == user_id
            )
            
            result = await self.db.execute(stmt)
            await self.db.commit()
            
            return result.rowcount > 0
        
        except Exception as e:
            await self.db.rollback()
            raise ValueError(f"Failed to delete pipeline: {str(e)}")
    
    # ==================== PIPELINE EXECUTION ====================
    
    async def execute_pipeline(self, user_id: int, execution_request: ProcessorExecutionRequest) -> str:
        """Execute a pipeline on a file."""
        execution_id = str(uuid.uuid4())
        
        try:
            # Get the pipeline
            pipeline = await self.get_pipeline_by_id(user_id, execution_request.pipeline_id)
            if not pipeline:
                raise ValueError("Pipeline not found")
            
            # Create execution record
            execution = PipelineExecution(
                pipeline_id=execution_request.pipeline_id,
                user_id=user_id,
                file_hash=execution_request.file_hash,
                execution_id=execution_id,
                status=PipelineStatus.RUNNING,
                started_at=datetime.utcnow(),
                pipeline_config_snapshot=pipeline.model_dump()
            )
            
            self.db.add(execution)
            await self.db.commit()
            
            # Execute pipeline asynchronously
            asyncio.create_task(
                self._execute_pipeline_async(execution_id, pipeline, execution_request)
            )
            
            return execution_id
        
        except Exception as e:
            await self.db.rollback()
            raise ValueError(f"Failed to start pipeline execution: {str(e)}")
    
    async def get_pipeline_executions(self, user_id: int, pipeline_id: Optional[int] = None, 
                                    skip: int = 0, limit: int = 100) -> PipelineExecutionList:
        """Get pipeline executions for a user."""
        query_filters = [PipelineExecution.user_id == user_id]
        if pipeline_id:
            query_filters.append(PipelineExecution.pipeline_id == pipeline_id)
        
        # Get total count
        count_stmt = select(PipelineExecution).where(*query_filters)
        count_result = await self.db.execute(count_stmt)
        total_count = len(count_result.scalars().all())
        
        # Get paginated results
        stmt = select(PipelineExecution).where(*query_filters).offset(skip).limit(limit).order_by(
            PipelineExecution.started_at.desc()
        )
        
        result = await self.db.execute(stmt)
        executions = result.scalars().all()
        
        execution_reads = [
            PipelineExecutionRead.model_validate(execution)
            for execution in executions
        ]
        
        return PipelineExecutionList(
            executions=execution_reads,
            total_count=total_count
        )
    
    async def get_execution_by_id(self, user_id: int, execution_id: str) -> Optional[PipelineExecution]:
        """Get a specific pipeline execution."""
        stmt = select(PipelineExecution).where(
            PipelineExecution.execution_id == execution_id,
            PipelineExecution.user_id == user_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    # ==================== PRIVATE HELPER METHODS ====================
    
    async def _validate_processor_code(self, processor_code: str) -> None:
        """Validate that processor code is syntactically correct and safe."""
        try:
            # Check if the code compiles
            compile(processor_code, '<string>', 'exec')
            
            # TODO: Add more validation rules:
            # - Check for dangerous imports
            # - Validate AsyncProcessor inheritance
            # - Check for required methods
            
        except SyntaxError as e:
            raise ValueError(f"Processor code has syntax error: {str(e)}")
        except Exception as e:
            raise ValueError(f"Processor code validation failed: {str(e)}")
    
    async def _validate_pipeline_sequence(self, user_id: int, processor_sequence: List[Dict[str, Any]]) -> None:
        """Validate that all processors in a pipeline sequence exist and are accessible."""
        for step in processor_sequence:
            processor_id = step.get('processor_id')
            if not processor_id:
                continue
            
            processor = await self.get_processor_by_id(user_id, processor_id)
            if not processor:
                raise ValueError(f"Processor with ID {processor_id} not found")
            
            if processor.status != ProcessorStatus.ACTIVE:
                raise ValueError(f"Processor '{processor.name}' is not active")
    
    async def _execute_pipeline_async(self, execution_id: str, pipeline: UserPipeline, 
                                    execution_request: ProcessorExecutionRequest) -> None:
        """Execute a pipeline asynchronously and update the execution record."""
        start_time = datetime.utcnow()
        
        try:
            # Build the processor pipeline
            async_pipeline = await self._build_async_pipeline(pipeline, execution_request.custom_config)
            
            # Get file data (this would be implemented based on your file storage system)
            file_data = await self._get_file_data(execution_request.file_hash)
            
            # Execute the pipeline
            processor_outputs = {}
            result_data = None
            
            async for step_index, output in async_pipeline.process_with_callbacks(file_data):
                processor_outputs[f"step_{step_index}"] = output
                result_data = output  # Last output is the final result
            
            # Update execution record with success
            end_time = datetime.utcnow()
            execution_time = (end_time - start_time).total_seconds()
            
            await self._update_execution_record(
                execution_id=execution_id,
                status=PipelineStatus.COMPLETED,
                completed_at=end_time,
                execution_time=execution_time,
                result_data=result_data,
                processor_outputs=processor_outputs
            )
            
            # Update pipeline usage statistics
            await self._update_pipeline_stats(pipeline.id, execution_time)
        
        except Exception as e:
            # Update execution record with failure
            end_time = datetime.utcnow()
            execution_time = (end_time - start_time).total_seconds()
            
            await self._update_execution_record(
                execution_id=execution_id,
                status=PipelineStatus.FAILED,
                completed_at=end_time,
                execution_time=execution_time,
                error_details=str(e) + "\n" + traceback.format_exc()
            )
    
    async def _build_async_pipeline(self, pipeline: UserPipeline, custom_config: Optional[Dict[str, Any]] = None) -> AsyncPipeline:
        """Build an AsyncPipeline from a UserPipeline configuration."""
        processors = []
        
        for step in pipeline.processor_sequence:
            processor_id = step.get('processor_id')
            step_config = step.get('config', {})
            
            # Merge with custom config if provided
            if custom_config:
                step_config.update(custom_config.get(str(processor_id), {}))
            
            # Get the processor from database
            processor_record = await self.get_processor_by_id(pipeline.user_id, processor_id)
            if not processor_record:
                raise ValueError(f"Processor {processor_id} not found")
            
            # Create processor instance from code
            processor_instance = await self._create_processor_instance(processor_record, step_config)
            
            # Add after_process callback for data saving
            processor_instance.after_process_callback = self._create_after_process_callback(
                processor_record, step_config
            )
            
            processors.append(processor_instance)
        
        # Create the pipeline
        async_pipeline = AsyncPipeline(processors)
        
        # Set global pipeline configuration
        if pipeline.global_config:
            async_pipeline.set_global_config(pipeline.global_config)
        
        return async_pipeline
    
    async def _create_processor_instance(self, processor_record: UserProcessor, config: Dict[str, Any]) -> AsyncProcessor:
        """Create an AsyncProcessor instance from a processor record."""
        # Execute the processor code to create the class
        processor_class = execute_processor_code(processor_record.processor_code)
        
        # Create instance with configuration
        processor_instance = processor_class(config)
        
        # Set metadata
        processor_instance.meta = {
            'id': processor_record.id,
            'name': processor_record.name,
            'version': processor_record.version,
            'user_id': processor_record.user_id
        }
        
        return processor_instance
    
    def _create_after_process_callback(self, processor_record: UserProcessor, config: Dict[str, Any]):
        """Create an after_process callback for saving processed data."""
        async def after_process_callback(processor: AsyncProcessor, input_data: Any, 
                                       output_data: Any, execution_id: str, step_index: int, 
                                       *args, **kwargs) -> None:
            """
            After process callback for saving intermediate and final results.
            
            This is where you would integrate with your storage system:
            - Save to MinIO for file data
            - Save to vector database for embeddings
            - Save to graph database for relationships
            - Save to time-series database for analytics
            
            Future integration hints:
            - Use MinIO client to save binary data
            - Use vector database client for embeddings
            - Use graph database for entity relationships
            - Use analytics database for metrics
            """
            
            try:
                # Prepare save data with comprehensive metadata
                save_data = {
                    'execution_id': execution_id,
                    'step_index': step_index,
                    'processor_id': processor_record.id,
                    'processor_name': processor_record.name,
                    'processor_version': processor_record.version,
                    'input_data_type': str(type(input_data).__name__),
                    'output_data_type': str(type(output_data).__name__),
                    'timestamp': datetime.utcnow().isoformat(),
                    'config_used': config,
                    'output_data': output_data,
                    'metadata': {
                        'processor_capabilities': processor_record.processing_capabilities,
                        'input_types': processor_record.input_types,
                        'output_types': processor_record.output_types
                    }
                }
                
                # TODO: Implement storage logic based on data type and requirements
                # Examples:
                
                # For text chunks
                if 'chunker' in processor_record.name.lower():
                    # save_data['storage_hint'] = 'Save chunks to document store'
                    pass
                
                # For vectors/embeddings
                if 'vector' in processor_record.name.lower() or 'embedding' in processor_record.name.lower():
                    # save_data['storage_hint'] = 'Save vectors to vector database'
                    pass
                
                # For extracted entities
                if 'entity' in processor_record.name.lower() or 'extract' in processor_record.name.lower():
                    # save_data['storage_hint'] = 'Save entities to graph database'
                    pass
                
                # For now, just log the data (replace with actual storage logic)
                print(f"[PROCESSOR CALLBACK] Step {step_index}: {processor_record.name} processed data")
                print(f"[DATA HINT] Output type: {type(output_data).__name__}, Size: {len(str(output_data))}")
                
                # Update processor usage stats
                await self._update_processor_usage(processor_record.id)
                
            except Exception as e:
                print(f"Error in after_process callback: {str(e)}")
        
        return after_process_callback
    
    async def _get_file_data(self, file_hash: str) -> Any:
        """Get file data for processing. This should be implemented based on your file storage."""
        # TODO: Implement file retrieval from MinIO or other storage
        # For now, return mock data
        return f"File content for {file_hash}"
    
    async def _update_execution_record(self, execution_id: str, **update_fields) -> None:
        """Update a pipeline execution record."""
        try:
            stmt = update(PipelineExecution).where(
                PipelineExecution.execution_id == execution_id
            ).values(**update_fields)
            
            await self.db.execute(stmt)
            await self.db.commit()
        
        except Exception as e:
            print(f"Error updating execution record: {str(e)}")
    
    async def _update_pipeline_stats(self, pipeline_id: int, execution_time: float) -> None:
        """Update pipeline usage statistics."""
        try:
            pipeline_stmt = select(UserPipeline).where(UserPipeline.id == pipeline_id)
            result = await self.db.execute(pipeline_stmt)
            pipeline = result.scalar_one_or_none()
            
            if pipeline:
                new_count = pipeline.execution_count + 1
                
                # Calculate new average execution time
                if pipeline.average_execution_time:
                    new_avg = ((pipeline.average_execution_time * pipeline.execution_count) + execution_time) / new_count
                else:
                    new_avg = execution_time
                
                update_stmt = update(UserPipeline).where(
                    UserPipeline.id == pipeline_id
                ).values(
                    execution_count=new_count,
                    last_executed=datetime.utcnow(),
                    average_execution_time=new_avg
                )
                
                await self.db.execute(update_stmt)
                await self.db.commit()
        
        except Exception as e:
            print(f"Error updating pipeline stats: {str(e)}")
    
    async def _update_processor_usage(self, processor_id: int) -> None:
        """Update processor usage statistics."""
        try:
            update_stmt = update(UserProcessor).where(
                UserProcessor.id == processor_id
            ).values(
                usage_count=UserProcessor.usage_count + 1,
                last_used=datetime.utcnow()
            )
            
            await self.db.execute(update_stmt)
            await self.db.commit()
        
        except Exception as e:
            print(f"Error updating processor usage: {str(e)}")


# ==================== PROCESSOR TEMPLATES ====================

def get_processor_templates() -> List[Dict[str, Any]]:
    """Get predefined processor templates for users to start with."""
    return [
        {
            "name": "Text Chunker",
            "description": "Splits text into smaller chunks for processing",
            "processor_code": '''
from processor_pipeline import AsyncProcessor
from typing import AsyncGenerator, Any, List

class TextChunkerProcessor(AsyncProcessor):
    """Processor that chunks text into smaller pieces."""
    
    meta = {
        "name": "text_chunker",
        "input_type": str,
        "output_type": List[str]
    }
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.chunk_size = config.get('chunk_size', 1000)
        self.overlap = config.get('overlap', 200)
    
    async def process(self, data: AsyncGenerator[Any, None]) -> AsyncGenerator[List[str], None]:
        async for text in data:
            chunks = []
            text_str = str(text)
            
            for i in range(0, len(text_str), self.chunk_size - self.overlap):
                chunk = text_str[i:i + self.chunk_size]
                chunks.append(chunk)Pipeline, AsyncProcessor, execute_processor_code,
    create_processor_from_registry, create_pipeline_from_c
                    "chunk_size": {"type": "integer", "default": 1000},
                    "overlap": {"type": "integer", "default": 200}
                }
            },
            "default_config": {"chunk_size": 1000, "overlap": 200},
            "input_types": ["str", "text"],
            "output_types": ["List[str]", "chunks"],
            "processing_capabilities": ["text_chunking", "text_processing"]'''
        },
        {
            "name": "Simple Vector Generator",
            "description": "Generates simple vector representations of text",
            "processor_code": '''
from processor_pipeline import AsyncProcessor
from typing import AsyncGenerator, Any, Dict, List
import hashlib

class SimpleVectorProcessor(AsyncProcessor):
    """Processor that generates simple vectors from text."""
    
    meta = {
        "name": "simple_vector_generator",
        "input_type": List[str],
        "output_type": Dict[str, Any]
    }
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.vector_size = config.get('vector_size', 128)
    
    async def process(self, data: AsyncGenerator[Any, None]) -> AsyncGenerator[Dict[str, Any], None]:
        async for chunks in data:
            for i, chunk in enumerate(chunks):
                # Simple vector generation (replace with real embedding)
                vector = [hash(chunk + str(j)) % 1000 / 1000.0 for j in range(self.vector_size)]
                
                yield {
                    "chunk": chunk,
                    "vector": vector,
                    "chunk_index": i,
                    "vector_size": self.vector_size
                }
''',
            "config_schema": {
                "type": "object",
                "properties": {
                    "vector_size": {"type": "integer", "default": 128}
                }
            },
            "default_config": {"vector_size": 128},
            "input_types": ["List[str]", "chunks"],
            "output_types": ["Dict[str, Any]", "vectors"],
            "processing_capabilities": ["vector_generation", "embedding", "text_analysis"]
        }
    ] 