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
    VISUAL_PARSING = "visual_parsing"  # Added for doc_visual_parsor integration
    LAYOUT_EXTRACTION = "layout_extraction"  # Added for layout analysis
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
    VISUAL_STRUCTURE = "visual_structure"  # Added for structure-aware chunking
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


# Added new models for visual parsing integration
class LayoutElement(BaseModel):
    """Represents a layout element from visual parsing."""
    id: int
    text: str
    type: str  # paragraph, title, table, figure, etc.
    bbox: List[float]  # [x1, y1, x2, y2] bounding box coordinates
    confidence: Optional[float] = None
    page_number: Optional[int] = None
    font_size: Optional[float] = None
    font_weight: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DocumentSection(BaseModel):
    """Represents a hierarchical document section from visual parsing."""
    title: str
    content: str
    level: int  # Hierarchy level (0 for main sections, 1 for subsections, etc.)
    element_id: Optional[int] = None
    sub_sections: List['DocumentSection'] = Field(default_factory=list)
    parent_section: Optional['DocumentSection'] = None
    bbox: Optional[List[float]] = None
    page_number: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        # Allow self-referencing for parent_section
        arbitrary_types_allowed = True


class VisualParsingResult(BaseModel):
    """Result of visual document parsing."""
    elements: List[LayoutElement] = Field(default_factory=list)
    sections: List[DocumentSection] = Field(default_factory=list)
    document_structure: Dict[str, Any] = Field(default_factory=dict)
    page_count: int = 0
    processing_metadata: Dict[str, Any] = Field(default_factory=dict)


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
    # Added fields for visual parsing integration
    section_title: Optional[str] = None
    section_level: Optional[int] = None
    layout_elements: List[LayoutElement] = Field(default_factory=list)
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
    # Added fields for visual parsing results
    visual_parsing_result: Optional[VisualParsingResult] = None
    document_sections: List[DocumentSection] = Field(default_factory=list)
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


class BaseVisualProcessor(BaseDocumentProcessor):
    """
    Abstract base class for visual document processing.
    
    This class provides the interface for processors that analyze document
    layout and structure using visual parsing techniques.
    """
    
    def __init__(self, config: ProcessorConfig):
        super().__init__(config)
        if self.processing_type not in [ProcessingType.VISUAL_PARSING, ProcessingType.LAYOUT_EXTRACTION, ProcessingType.STRUCTURE_ANALYSIS]:
            raise ValueError("Visual processors must have appropriate processing_type")
    
    @abstractmethod
    async def extract_layout(
        self, 
        file_path: str,
        **kwargs
    ) -> VisualParsingResult:
        """
        Extract layout and structure from document using visual parsing.
        
        Args:
            file_path: Path to the document file
            **kwargs: Additional parsing parameters
            
        Returns:
            VisualParsingResult with layout elements and sections
        """
        pass
    
    @abstractmethod
    async def build_document_structure(
        self, 
        layout_result: VisualParsingResult,
        **kwargs
    ) -> List[DocumentSection]:
        """
        Build hierarchical document structure from layout elements.
        
        Args:
            layout_result: Visual parsing result
            **kwargs: Additional structure building parameters
            
        Returns:
            List of hierarchical DocumentSection objects
        """
        pass
    
    async def process(
        self, 
        document: ProcessedDocument, 
        context: ProcessingContext,
        **kwargs
    ) -> ProcessingResult:
        """Process document using visual parsing."""
        start_time = datetime.utcnow()
        
        try:
            # For now, we'll assume the file is accessible via a path
            # In a real implementation, you might need to save the document to a temp file
            file_path = kwargs.get('file_path')
            if not file_path:
                raise ValueError("file_path is required for visual processing")
            
            # Extract layout using visual parsing
            visual_result = await self.extract_layout(file_path, **kwargs)
            
            # Build document structure
            sections = await self.build_document_structure(visual_result, **kwargs)
            
            # Update document with visual parsing results
            document.visual_parsing_result = visual_result
            document.document_sections = sections
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            return ProcessingResult(
                processor_id=self.processor_id,
                processing_type=self.processing_type,
                status=ProcessingStatus.COMPLETED,
                input_document_id=document.document_id,
                output_data={
                    "elements_extracted": len(visual_result.elements),
                    "sections_found": len(sections),
                    "page_count": visual_result.page_count,
                    "structure_metadata": visual_result.processing_metadata
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


class DocVisualParsorProcessor(BaseVisualProcessor):
    """
    Concrete implementation of visual processor using doc_visual_parsor.
    
    This processor integrates with the doc_visual_parsor library to provide
    layout extraction and structure analysis for PDF and DOCX documents.
    """
    
    def __init__(self, config: Optional[ProcessorConfig] = None):
        if config is None:
            config = ProcessorConfig(
                processor_id="doc_visual_parsor",
                processing_type=ProcessingType.VISUAL_PARSING,
                name="Document Visual Parser",
                description="Visual document parsing using DocLayout-YOLO for layout extraction and structure analysis",
                version="1.0.0",
                supported_formats=[DocumentFormat.PDF, DocumentFormat.DOCX],
                parameters={
                    "model_name": "doclayout-yolo",
                    "confidence_threshold": 0.5,
                    "use_llm_structure": True,
                    "chunk_size": 10
                }
            )
        super().__init__(config)
    
    def get_supported_formats(self) -> List[DocumentFormat]:
        """Return supported document formats."""
        return [DocumentFormat.PDF, DocumentFormat.DOCX]
    
    def get_required_parameters(self) -> Dict[str, Any]:
        """Return required parameters."""
        return {
            "file_path": {
                "type": "str",
                "description": "Path to the document file to process"
            }
        }
    
    def get_optional_parameters(self) -> Dict[str, Any]:
        """Return optional parameters."""
        return {
            "model_name": {
                "type": "str",
                "default": "doclayout-yolo",
                "description": "Name of the layout detection model to use"
            },
            "confidence_threshold": {
                "type": "float",
                "default": 0.5,
                "description": "Confidence threshold for layout element detection"
            },
            "use_llm_structure": {
                "type": "bool",
                "default": True,
                "description": "Whether to use LLM for structure analysis"
            },
            "chunk_size": {
                "type": "int",
                "default": 10,
                "description": "Chunk size for processing large documents"
            }
        }
    
    async def extract_layout(
        self, 
        file_path: str,
        **kwargs
    ) -> VisualParsingResult:
        """
        Extract layout using doc_visual_parsor library.
        
        This method integrates with your doc_visual_parsor project.
        """
        try:
            # Import doc_chunking library (your doc_visual_parsor)
            # Note: You'll need to install this in your environment
            import doc_chunking
            
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                raise FileNotFoundError(f"Document file not found: {file_path}")
            
            # Determine document type and process accordingly
            if file_path.lower().endswith('.pdf'):
                # Use quick_pdf_chunking from your library
                sections_result = doc_chunking.quick_pdf_chunking(file_path)
            elif file_path.lower().endswith('.docx'):
                # Use quick_docx_chunking from your library
                sections_result = doc_chunking.quick_docx_chunking(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_path}")
            
            # Convert the result to our internal format
            elements = []
            sections = []
            
            def process_section(section, level=0, element_id=0):
                """Recursively process sections from doc_visual_parsor."""
                nonlocal element_id
                
                section_obj = DocumentSection(
                    title=getattr(section, 'title', f'Section {element_id}'),
                    content=getattr(section, 'content', ''),
                    level=level,
                    element_id=element_id,
                    metadata={
                        'source': 'doc_visual_parsor',
                        'processing_time': datetime.utcnow().isoformat()
                    }
                )
                
                # Create layout element for this section
                element = LayoutElement(
                    id=element_id,
                    text=section_obj.content,
                    type='section' if level == 0 else 'subsection',
                    bbox=[0, 0, 0, 0],  # You might want to extract actual bbox if available
                    confidence=1.0,
                    metadata={'section_title': section_obj.title, 'level': level}
                )
                elements.append(element)
                element_id += 1
                
                # Process subsections
                if hasattr(section, 'sub_sections') and section.sub_sections:
                    for subsection in section.sub_sections:
                        child_section, element_id = process_section(subsection, level + 1, element_id)
                        section_obj.sub_sections.append(child_section)
                
                return section_obj, element_id
            
            # Process the main sections
            if hasattr(sections_result, 'sub_sections'):
                element_counter = 0
                for main_section in sections_result.sub_sections:
                    section_obj, element_counter = process_section(main_section, 0, element_counter)
                    sections.append(section_obj)
            else:
                # Handle case where sections_result is the main section itself
                section_obj, _ = process_section(sections_result, 0, 0)
                sections.append(section_obj)
            
            return VisualParsingResult(
                elements=elements,
                sections=sections,
                document_structure={
                    "total_sections": len(sections),
                    "max_depth": max((s.level for s in sections), default=0) + 1,
                    "processing_method": "doc_visual_parsor"
                },
                page_count=1,  # You might want to extract actual page count
                processing_metadata={
                    "processor": "doc_visual_parsor",
                    "file_path": file_path,
                    "processing_time": datetime.utcnow().isoformat()
                }
            )
            
        except ImportError:
            raise ImportError(
                "doc_chunking library not found. Please install doc_visual_parsor: "
                "pip install doc-chunking"
            )
        except Exception as e:
            raise Exception(f"Error in visual parsing: {str(e)}")
    
    async def build_document_structure(
        self, 
        layout_result: VisualParsingResult,
        **kwargs
    ) -> List[DocumentSection]:
        """Build document structure from layout result."""
        # The structure is already built in extract_layout
        return layout_result.sections


class VisualStructureChunker(BaseChunker):
    """
    Chunker that uses visual structure analysis for intelligent chunking.
    
    This chunker leverages the visual parsing results to create chunks
    based on document structure rather than just text length.
    """
    
    def __init__(self, config: Optional[ProcessorConfig] = None):
        if config is None:
            config = ProcessorConfig(
                processor_id="visual_structure_chunker",
                processing_type=ProcessingType.CHUNKING,
                name="Visual Structure Chunker",
                description="Structure-aware chunking using visual document analysis",
                version="1.0.0",
                supported_formats=[DocumentFormat.PDF, DocumentFormat.DOCX],
                parameters={
                    "max_chunk_size": 1000,
                    "preserve_sections": True,
                    "include_headers": True,
                    "chunk_overlap": 100
                },
                dependencies=["doc_visual_parsor"]  # Depends on visual processor
            )
        super().__init__(config)
    
    def get_supported_formats(self) -> List[DocumentFormat]:
        """Return supported document formats."""
        return [DocumentFormat.PDF, DocumentFormat.DOCX]
    
    def get_required_parameters(self) -> Dict[str, Any]:
        """Return required parameters."""
        return {}
    
    def get_optional_parameters(self) -> Dict[str, Any]:
        """Return optional parameters."""
        return {
            "max_chunk_size": {
                "type": "int",
                "default": 1000,
                "description": "Maximum size of each chunk in characters"
            },
            "preserve_sections": {
                "type": "bool",
                "default": True,
                "description": "Whether to preserve section boundaries"
            },
            "include_headers": {
                "type": "bool",
                "default": True,
                "description": "Whether to include section headers in chunks"
            },
            "chunk_overlap": {
                "type": "int",
                "default": 100,
                "description": "Overlap between chunks in characters"
            }
        }
    
    async def chunk_text(
        self, 
        text: str, 
        chunk_size: int = 1000, 
        overlap: int = 200,
        **kwargs
    ) -> List[DocumentChunk]:
        """
        This method won't be used directly as we override the process method
        to use document structure for chunking.
        """
        # Fallback to simple chunking if no structure is available
        chunks = []
        start = 0
        chunk_id = 0
        
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk_content = text[start:end]
            
            chunk = DocumentChunk(
                chunk_id=f"chunk_{chunk_id}",
                document_id="",  # Will be set in process method
                content=chunk_content,
                start_pos=start,
                end_pos=end,
                metadata={"chunking_method": "fallback_fixed_size"}
            )
            chunks.append(chunk)
            
            start = end - overlap
            chunk_id += 1
        
        return chunks
    
    async def process(
        self, 
        document: ProcessedDocument, 
        context: ProcessingContext,
        **kwargs
    ) -> ProcessingResult:
        """Process document using structure-aware chunking."""
        start_time = datetime.utcnow()
        
        try:
            # Check if document has visual parsing results
            if not document.visual_parsing_result or not document.document_sections:
                # Fall back to regular text chunking
                return await super().process(document, context, **kwargs)
            
            # Get chunking parameters
            max_chunk_size = kwargs.get('max_chunk_size', self.config.parameters.get('max_chunk_size', 1000))
            preserve_sections = kwargs.get('preserve_sections', self.config.parameters.get('preserve_sections', True))
            include_headers = kwargs.get('include_headers', self.config.parameters.get('include_headers', True))
            chunk_overlap = kwargs.get('chunk_overlap', self.config.parameters.get('chunk_overlap', 100))
            
            chunks = []
            chunk_id = 0
            
            def process_section_chunks(section: DocumentSection, parent_context: str = ""):
                """Recursively process sections into chunks."""
                nonlocal chunk_id
                section_chunks = []
                
                # Build context with parent sections
                context_text = parent_context
                if include_headers and section.title:
                    context_text += f"\n{section.title}\n" if context_text else section.title
                
                content = context_text + "\n" + section.content if context_text else section.content
                
                if preserve_sections and len(content) <= max_chunk_size:
                    # Keep section as single chunk if it fits
                    chunk = DocumentChunk(
                        chunk_id=f"section_chunk_{chunk_id}",
                        document_id=document.document_id,
                        content=content.strip(),
                        section_title=section.title,
                        section_level=section.level,
                        layout_elements=[elem for elem in document.visual_parsing_result.elements if elem.id == section.element_id],
                        metadata={
                            "chunking_method": "visual_structure",
                            "section_id": section.element_id,
                            "section_level": section.level,
                            "preserved_section": True
                        }
                    )
                    section_chunks.append(chunk)
                    chunk_id += 1
                else:
                    # Split section into smaller chunks
                    text_to_chunk = content
                    start = 0
                    
                    while start < len(text_to_chunk):
                        end = min(start + max_chunk_size, len(text_to_chunk))
                        chunk_content = text_to_chunk[start:end]
                        
                        chunk = DocumentChunk(
                            chunk_id=f"section_chunk_{chunk_id}",
                            document_id=document.document_id,
                            content=chunk_content,
                            start_pos=start,
                            end_pos=end,
                            section_title=section.title,
                            section_level=section.level,
                            layout_elements=[elem for elem in document.visual_parsing_result.elements if elem.id == section.element_id],
                            metadata={
                                "chunking_method": "visual_structure",
                                "section_id": section.element_id,
                                "section_level": section.level,
                                "preserved_section": False
                            }
                        )
                        section_chunks.append(chunk)
                        chunk_id += 1
                        
                        start = end - chunk_overlap
                
                # Process subsections
                for subsection in section.sub_sections:
                    subsection_chunks = process_section_chunks(subsection, context_text)
                    section_chunks.extend(subsection_chunks)
                
                return section_chunks
            
            # Process all document sections
            for section in document.document_sections:
                section_chunks = process_section_chunks(section)
                chunks.extend(section_chunks)
            
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
                    "sections_processed": len(document.document_sections),
                    "chunking_method": "visual_structure",
                    "max_chunk_size": max_chunk_size,
                    "preserve_sections": preserve_sections
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
