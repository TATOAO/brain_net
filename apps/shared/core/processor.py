"""
Abstract Document Processor Interface for Brain_Net

This module defines abstract interfaces for document processing plugins that users can:
1. Select from available processors in the frontend
2. Chain together in processing pipelines
3. Implement custom processors by extending the base classes

Supports various processing types like chunking, NER, metadata extraction, etc.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, AsyncIterator, Protocol
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime
import asyncio
from pathlib import Path


class ProcessingType(str, Enum):
    """Types of document processing operations."""
    CHUNKING = "chunking"
    NER = "ner"  # Named Entity Recognition
    METADATA_EXTRACTION = "metadata_extraction"
    TEXT_EXTRACTION = "text_extraction"
    SUMMARIZATION = "summarization"
    KEYWORD_EXTRACTION = "keyword_extraction"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    LANGUAGE_DETECTION = "language_detection"
    STRUCTURE_ANALYSIS = "structure_analysis"
    EMBEDDING_GENERATION = "embedding_generation"
    CLASSIFICATION = "classification"
    CUSTOM = "custom"


class ProcessingStatus(str, Enum):
    """Status of processing operations."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ChunkingMethod(str, Enum):
    """Different text chunking strategies."""
    FIXED_SIZE = "fixed_size"
    SENTENCE_BASED = "sentence_based"
    PARAGRAPH_BASED = "paragraph_based"
    SEMANTIC = "semantic"
    RECURSIVE = "recursive"
    CUSTOM = "custom"


class DocumentFormat(str, Enum):
    """Supported document formats."""
    TEXT = "text/plain"
    PDF = "application/pdf"
    DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    HTML = "text/html"
    MARKDOWN = "text/markdown"
    JSON = "application/json"
    CSV = "text/csv"
    XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


class ProcessorConfig(BaseModel):
    """Configuration for a document processor."""
    processor_id: str
    processing_type: ProcessingType
    name: str
    description: Optional[str] = None
    version: str = "1.0.0"
    enabled: bool = True
    parameters: Dict[str, Any] = Field(default_factory=dict)
    supported_formats: List[DocumentFormat] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ProcessingResult(BaseModel):
    """Result of a processing operation."""
    processor_id: str
    processing_type: ProcessingType
    status: ProcessingStatus
    input_document_id: str
    output_data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    processing_time: Optional[float] = None
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DocumentChunk(BaseModel):
    """Represents a chunk of processed document."""
    chunk_id: str
    document_id: str
    content: str
    start_pos: Optional[int] = None
    end_pos: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    embeddings: Optional[List[float]] = None


class ProcessedDocument(BaseModel):
    """Complete processed document with all results."""
    document_id: str
    original_filename: str
    file_hash: str
    user_id: int
    content_type: str
    raw_content: Optional[str] = None
    processed_content: Optional[str] = None
    chunks: List[DocumentChunk] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    processing_results: List[ProcessingResult] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


class ProcessingContext(BaseModel):
    """Context for processing operations."""
    user_id: int
    document_id: str
    file_hash: str
    processing_pipeline: List[str] = Field(default_factory=list)
    global_parameters: Dict[str, Any] = Field(default_factory=dict)
    session_metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseDocumentProcessor(ABC):
    """
    Abstract base class for document processors.
    
    All document processors must inherit from this class and implement
    the abstract methods to provide specific processing functionality.
    """
    
    def __init__(self, config: ProcessorConfig):
        """Initialize the processor with configuration."""
        self.config = config
        self.processor_id = config.processor_id
        self.processing_type = config.processing_type
        self.enabled = config.enabled
        self._validate_config()
    
    def _validate_config(self) -> None:
        """Validate processor configuration."""
        if not self.config.processor_id:
            raise ValueError("Processor ID is required")
        if not self.config.name:
            raise ValueError("Processor name is required")
    
    @abstractmethod
    async def process(
        self, 
        document: ProcessedDocument, 
        context: ProcessingContext,
        **kwargs
    ) -> ProcessingResult:
        """
        Process a document and return the result.
        
        Args:
            document: The document to process
            context: Processing context with user info and pipeline
            **kwargs: Additional processing parameters
            
        Returns:
            ProcessingResult with the processed data
        """
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> List[DocumentFormat]:
        """Return list of supported document formats."""
        pass
    
    @abstractmethod
    def get_required_parameters(self) -> Dict[str, Any]:
        """Return dictionary of required parameters with their types and descriptions."""
        pass
    
    @abstractmethod
    def get_optional_parameters(self) -> Dict[str, Any]:
        """Return dictionary of optional parameters with their types, defaults, and descriptions."""
        pass
    
    async def validate_input(self, document: ProcessedDocument, context: ProcessingContext) -> bool:
        """
        Validate input document and context before processing.
        
        Args:
            document: Document to validate
            context: Processing context to validate
            
        Returns:
            True if input is valid, False otherwise
        """
        # Check if document format is supported
        doc_format = DocumentFormat(document.content_type)
        if doc_format not in self.get_supported_formats():
            return False
        
        # Validate required parameters are present
        required_params = self.get_required_parameters()
        for param_name in required_params.keys():
            if param_name not in self.config.parameters:
                return False
        
        return True
    
    async def preprocess(self, document: ProcessedDocument, context: ProcessingContext) -> ProcessedDocument:
        """
        Preprocess document before main processing.
        Override this method to add preprocessing steps.
        """
        return document
    
    async def postprocess(self, result: ProcessingResult, context: ProcessingContext) -> ProcessingResult:
        """
        Postprocess result after main processing.
        Override this method to add postprocessing steps.
        """
        return result
    
    def get_processor_info(self) -> Dict[str, Any]:
        """Get information about this processor."""
        return {
            "processor_id": self.processor_id,
            "name": self.config.name,
            "description": self.config.description,
            "version": self.config.version,
            "processing_type": self.processing_type.value,
            "supported_formats": [fmt.value for fmt in self.get_supported_formats()],
            "required_parameters": self.get_required_parameters(),
            "optional_parameters": self.get_optional_parameters(),
            "enabled": self.enabled,
            "dependencies": self.config.dependencies
        }


class BaseChunker(BaseDocumentProcessor):
    """
    Abstract base class for text chunking processors.
    
    Chunkers split documents into smaller pieces for further processing.
    """
    
    def __init__(self, config: ProcessorConfig):
        super().__init__(config)
        if self.processing_type != ProcessingType.CHUNKING:
            raise ValueError("Chunkers must have processing_type=CHUNKING")
    
    @abstractmethod
    async def chunk_text(
        self, 
        text: str, 
        chunk_size: int = 1000, 
        overlap: int = 200,
        **kwargs
    ) -> List[DocumentChunk]:
        """
        Split text into chunks.
        
        Args:
            text: Text to chunk
            chunk_size: Maximum size of each chunk
            overlap: Overlap between consecutive chunks
            **kwargs: Additional chunking parameters
            
        Returns:
            List of DocumentChunk objects
        """
        pass
    
    async def process(
        self, 
        document: ProcessedDocument, 
        context: ProcessingContext,
        **kwargs
    ) -> ProcessingResult:
        """Process document by chunking its content."""
        start_time = datetime.utcnow()
        
        try:
            # Extract text content
            text_content = document.processed_content or document.raw_content
            if not text_content:
                raise ValueError("No text content found in document")
            
            # Get chunking parameters
            chunk_size = kwargs.get('chunk_size', self.config.parameters.get('chunk_size', 1000))
            overlap = kwargs.get('overlap', self.config.parameters.get('overlap', 200))
            
            # Perform chunking
            chunks = await self.chunk_text(text_content, chunk_size, overlap, **kwargs)
            
            # Update document with chunks
            document.chunks.extend(chunks)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            return ProcessingResult(
                processor_id=self.processor_id,
                processing_type=self.processing_type,
                status=ProcessingStatus.COMPLETED,
                input_document_id=document.document_id,
                output_data={
                    "chunks": [chunk.model_dump() for chunk in chunks],
                    "chunks_created": len(chunks),
                    "total_characters": sum(len(chunk.content) for chunk in chunks),
                    "chunk_size": chunk_size,
                    "overlap": overlap
                },
                processing_time=processing_time
            )
            
        except Exception as e:
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            return ProcessingResult(
                processor_id=self.processor_id,
                processing_type=self.processing_type,
                status=ProcessingStatus.FAILED,
                input_document_id=document.document_id,
                error_message=str(e),
                processing_time=processing_time
            )


class BaseNERProcessor(BaseDocumentProcessor):
    """
    Abstract base class for Named Entity Recognition processors.
    
    NER processors extract entities like persons, organizations, locations, etc.
    """
    
    def __init__(self, config: ProcessorConfig):
        super().__init__(config)
        if self.processing_type != ProcessingType.NER:
            raise ValueError("NER processors must have processing_type=NER")
    
    @abstractmethod
    async def extract_entities(
        self, 
        text: str,
        entity_types: Optional[List[str]] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Extract named entities from text.
        
        Args:
            text: Text to analyze
            entity_types: List of entity types to extract (None for all)
            **kwargs: Additional NER parameters
            
        Returns:
            List of entity dictionaries with type, text, start, end, confidence
        """
        pass
    
    async def process(
        self, 
        document: ProcessedDocument, 
        context: ProcessingContext,
        **kwargs
    ) -> ProcessingResult:
        """Process document by extracting named entities."""
        start_time = datetime.utcnow()
        
        try:
            # Extract text content
            text_content = document.processed_content or document.raw_content
            if not text_content:
                raise ValueError("No text content found in document")
            
            # Get NER parameters
            entity_types = kwargs.get('entity_types', self.config.parameters.get('entity_types'))
            
            # Perform NER
            entities = await self.extract_entities(text_content, entity_types, **kwargs)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            return ProcessingResult(
                processor_id=self.processor_id,
                processing_type=self.processing_type,
                status=ProcessingStatus.COMPLETED,
                input_document_id=document.document_id,
                output_data={
                    "entities": entities,
                    "entity_count": len(entities),
                    "entity_types_found": list(set(e.get('type', 'UNKNOWN') for e in entities))
                },
                processing_time=processing_time
            )
            
        except Exception as e:
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            return ProcessingResult(
                processor_id=self.processor_id,
                processing_type=self.processing_type,
                status=ProcessingStatus.FAILED,
                input_document_id=document.document_id,
                error_message=str(e),
                processing_time=processing_time
            )


class ProcessorRegistry:
    """Registry for managing available document processors."""
    
    def __init__(self):
        self._processors: Dict[str, BaseDocumentProcessor] = {}
        self._processors_by_type: Dict[ProcessingType, List[str]] = {}
    
    def register_processor(self, processor: BaseDocumentProcessor) -> None:
        """Register a processor instance."""
        self._processors[processor.processor_id] = processor
        
        # Add to type-based index
        proc_type = processor.processing_type
        if proc_type not in self._processors_by_type:
            self._processors_by_type[proc_type] = []
        self._processors_by_type[proc_type].append(processor.processor_id)
    
    def unregister_processor(self, processor_id: str) -> None:
        """Unregister a processor."""
        if processor_id in self._processors:
            processor = self._processors[processor_id]
            proc_type = processor.processing_type
            
            # Remove from type-based index
            if proc_type in self._processors_by_type:
                if processor_id in self._processors_by_type[proc_type]:
                    self._processors_by_type[proc_type].remove(processor_id)
            
            # Remove from main registry
            del self._processors[processor_id]
    
    def get_processor(self, processor_id: str) -> Optional[BaseDocumentProcessor]:
        """Get a processor by ID."""
        return self._processors.get(processor_id)
    
    def get_processors_by_type(self, processing_type: ProcessingType) -> List[BaseDocumentProcessor]:
        """Get all processors for a specific processing type."""
        processor_ids = self._processors_by_type.get(processing_type, [])
        return [self._processors[pid] for pid in processor_ids if pid in self._processors]
    
    def list_processors(self) -> List[Dict[str, Any]]:
        """List all registered processors with their info."""
        return [processor.get_processor_info() for processor in self._processors.values()]
    
    def list_processors_by_type(self) -> Dict[ProcessingType, List[Dict[str, Any]]]:
        """List processors grouped by processing type."""
        result = {}
        for proc_type in ProcessingType:
            processors = self.get_processors_by_type(proc_type)
            result[proc_type] = [p.get_processor_info() for p in processors]
        return result


class ProcessingPipeline:
    """
    Manages execution of processing pipelines.
    
    A pipeline is a sequence of processors that are applied to a document
    in order, with the output of one processor feeding into the next.
    """
    
    def __init__(self, registry: ProcessorRegistry):
        self.registry = registry
    
    async def execute_pipeline(
        self, 
        document: ProcessedDocument,
        context: ProcessingContext,
        pipeline_config: List[Dict[str, Any]]
    ) -> List[ProcessingResult]:
        """
        Execute a processing pipeline on a document.
        
        Args:
            document: Document to process
            context: Processing context
            pipeline_config: List of processor configurations
            
        Returns:
            List of ProcessingResult objects from each step
        """
        results = []
        current_document = document
        
        for step_config in pipeline_config:
            processor_id = step_config.get('processor_id')
            parameters = step_config.get('parameters', {})
            
            if not processor_id:
                continue
            
            processor = self.registry.get_processor(processor_id)
            if not processor or not processor.enabled:
                continue
            
            try:
                # Validate input
                if not await processor.validate_input(current_document, context):
                    raise ValueError(f"Input validation failed for processor {processor_id}")
                
                # Preprocess
                current_document = await processor.preprocess(current_document, context)
                
                # Main processing
                result = await processor.process(current_document, context, **parameters)
                
                # Postprocess
                result = await processor.postprocess(result, context)
                
                results.append(result)
                
                # Update document with processing result
                current_document.processing_results.append(result)
                current_document.updated_at = datetime.utcnow()
                
            except Exception as e:
                error_result = ProcessingResult(
                    processor_id=processor_id,
                    processing_type=processor.processing_type,
                    status=ProcessingStatus.FAILED,
                    input_document_id=document.document_id,
                    error_message=str(e)
                )
                results.append(error_result)
                
                # Decide whether to continue or stop pipeline on error
                if step_config.get('stop_on_error', True):
                    break
        
        return results
    
    async def validate_pipeline(self, pipeline_config: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate a pipeline configuration.
        
        Args:
            pipeline_config: Pipeline configuration to validate
            
        Returns:
            Dictionary with validation results and any errors
        """
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "processors_found": 0,
            "processors_enabled": 0
        }
        
        for i, step_config in enumerate(pipeline_config):
            processor_id = step_config.get('processor_id')
            
            if not processor_id:
                validation_result["errors"].append(f"Step {i}: processor_id is required")
                continue
            
            processor = self.registry.get_processor(processor_id)
            if not processor:
                validation_result["errors"].append(f"Step {i}: processor '{processor_id}' not found")
                continue
            
            validation_result["processors_found"] += 1
            
            if not processor.enabled:
                validation_result["warnings"].append(f"Step {i}: processor '{processor_id}' is disabled")
            else:
                validation_result["processors_enabled"] += 1
            
            # Validate required parameters
            required_params = processor.get_required_parameters()
            step_params = step_config.get('parameters', {})
            
            for param_name in required_params.keys():
                if param_name not in step_params and param_name not in processor.config.parameters:
                    validation_result["errors"].append(
                        f"Step {i}: required parameter '{param_name}' missing for processor '{processor_id}'"
                    )
        
        validation_result["valid"] = len(validation_result["errors"]) == 0
        return validation_result


# Global registry instance
processor_registry = ProcessorRegistry()
