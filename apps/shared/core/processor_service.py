"""
Document Processor Service

This service integrates the processor interface with the existing document upload system.
It provides high-level methods for processing documents and managing processor pipelines.
"""

from typing import List, Dict, Any, Optional
import asyncio
from datetime import datetime

from .processor import (
    ProcessorRegistry, ProcessingPipeline, ProcessedDocument, ProcessingContext,
    ProcessingResult, DocumentChunk, ProcessorConfig, ProcessingType, DocumentFormat
)
from .example_processors import FixedSizeChunker, SimpleNERProcessor, MetadataExtractor
from .advanced_processors import RecursiveTextChunker, EnhancedNERProcessor
from ..models.user import User
from ..models.file import UserFile


class DocumentProcessorService:
    """
    Service for processing documents using the processor interface.
    """
    
    def __init__(self):
        self.registry = ProcessorRegistry()
        self.pipeline = ProcessingPipeline(self.registry)
        self._initialize_default_processors()
    
    def _initialize_default_processors(self):
        """Initialize default processors."""
        # Register chunkers
        fixed_chunker = FixedSizeChunker()
        self.registry.register_processor(fixed_chunker)
        
        recursive_chunker = RecursiveTextChunker()
        self.registry.register_processor(recursive_chunker)
        
        # Register NER processors
        simple_ner = SimpleNERProcessor()
        self.registry.register_processor(simple_ner)
        
        enhanced_ner = EnhancedNERProcessor()
        self.registry.register_processor(enhanced_ner)
        
        # Register other processors
        metadata_extractor = MetadataExtractor()
        self.registry.register_processor(metadata_extractor)
    
    async def process_user_document(
        self,
        user: User,
        user_file: UserFile,
        document_content: str,
        processing_config: Dict[str, Any]
    ) -> ProcessedDocument:
        """
        Process a user's document with specified configuration.
        
        Args:
            user: User who owns the document
            user_file: UserFile record from database
            document_content: Raw text content of the document
            processing_config: Configuration for processing
            
        Returns:
            ProcessedDocument with all processing results
        """
        # Create ProcessedDocument
        document = ProcessedDocument(
            document_id=f"doc_{user_file.id}_{user_file.file_hash[:8]}",
            original_filename=user_file.original_filename,
            file_hash=user_file.file_hash,
            user_id=user.id,
            content_type=user_file.content_type,
            raw_content=document_content
        )
        
        # Create processing context
        context = ProcessingContext(
            user_id=user.id,
            document_id=document.document_id,
            file_hash=user_file.file_hash,
            processing_pipeline=processing_config.get('pipeline', [])
        )
        
        # Execute processing pipeline
        pipeline_config = processing_config.get('pipeline', [])
        if pipeline_config:
            results = await self.pipeline.execute_pipeline(document, context, pipeline_config)
            document.processing_results.extend(results)
        
        return document
    
    async def chunk_document(
        self,
        user: User,
        user_file: UserFile,
        document_content: str,
        chunker_id: str = "fixed_size_chunker",
        chunk_size: int = 1000,
        overlap: int = 200,
        **kwargs
    ) -> List[DocumentChunk]:
        """
        Chunk a document using specified chunker.
        
        Args:
            user: User who owns the document
            user_file: UserFile record
            document_content: Document content to chunk
            chunker_id: ID of chunker to use
            chunk_size: Size of chunks
            overlap: Overlap between chunks
            **kwargs: Additional parameters for chunker
            
        Returns:
            List of DocumentChunk objects
        """
        # Get chunker
        chunker = self.registry.get_processor(chunker_id)
        if not chunker or chunker.processing_type != ProcessingType.CHUNKING:
            raise ValueError(f"Chunker '{chunker_id}' not found or not a chunker")
        
        # Create minimal document for chunking
        document = ProcessedDocument(
            document_id=f"doc_{user_file.id}_{user_file.file_hash[:8]}",
            original_filename=user_file.original_filename,
            file_hash=user_file.file_hash,
            user_id=user.id,
            content_type=user_file.content_type,
            raw_content=document_content
        )
        
        # Create processing context
        context = ProcessingContext(
            user_id=user.id,
            document_id=document.document_id,
            file_hash=user_file.file_hash
        )
        
        # Process document
        result = await chunker.process(
            document, 
            context, 
            chunk_size=chunk_size, 
            overlap=overlap, 
            **kwargs
        )
        
        # Return chunks with document_id set
        for chunk in document.chunks:
            chunk.document_id = document.document_id
        
        return document.chunks
    
    async def extract_entities(
        self,
        user: User,
        user_file: UserFile,
        document_content: str,
        ner_processor_id: str = "simple_ner",
        entity_types: Optional[List[str]] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Extract named entities from a document.
        
        Args:
            user: User who owns the document
            user_file: UserFile record
            document_content: Document content to analyze
            ner_processor_id: ID of NER processor to use
            entity_types: List of entity types to extract
            **kwargs: Additional parameters for NER processor
            
        Returns:
            List of entity dictionaries
        """
        # Get NER processor
        ner_processor = self.registry.get_processor(ner_processor_id)
        if not ner_processor or ner_processor.processing_type != ProcessingType.NER:
            raise ValueError(f"NER processor '{ner_processor_id}' not found or not a NER processor")
        
        # Create minimal document for NER
        document = ProcessedDocument(
            document_id=f"doc_{user_file.id}_{user_file.file_hash[:8]}",
            original_filename=user_file.original_filename,
            file_hash=user_file.file_hash,
            user_id=user.id,
            content_type=user_file.content_type,
            raw_content=document_content
        )
        
        # Create processing context
        context = ProcessingContext(
            user_id=user.id,
            document_id=document.document_id,
            file_hash=user_file.file_hash
        )
        
        # Process document
        result = await ner_processor.process(
            document, 
            context, 
            entity_types=entity_types, 
            **kwargs
        )
        
        # Return extracted entities
        return result.output_data.get("entities", [])
    
    def get_available_processors(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all available processors grouped by type.
        
        Returns:
            Dictionary mapping processing types to lists of processor info
        """
        return self.registry.list_processors_by_type()
    
    def get_processor_info(self, processor_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific processor.
        
        Args:
            processor_id: ID of processor to get info for
            
        Returns:
            Processor information dictionary or None if not found
        """
        processor = self.registry.get_processor(processor_id)
        return processor.get_processor_info() if processor else None
    
    async def validate_processing_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a processing configuration.
        
        Args:
            config: Processing configuration to validate
            
        Returns:
            Validation result with errors and warnings
        """
        pipeline_config = config.get('pipeline', [])
        return await self.pipeline.validate_pipeline(pipeline_config)
    
    def register_custom_processor(self, processor_class, config: ProcessorConfig):
        """
        Register a custom processor.
        
        Args:
            processor_class: Class that extends BaseDocumentProcessor
            config: Configuration for the processor
        """
        processor_instance = processor_class(config)
        self.registry.register_processor(processor_instance)
    
    async def get_processing_suggestions(
        self, 
        document_format: DocumentFormat,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get suggested processing configurations based on document format and user preferences.
        
        Args:
            document_format: Format of the document
            user_preferences: User's processing preferences
            
        Returns:
            List of suggested processing configurations
        """
        suggestions = []
        
        # Default chunking suggestion
        if document_format in [DocumentFormat.TEXT, DocumentFormat.MARKDOWN, DocumentFormat.PDF]:
            suggestions.append({
                "name": "Basic Text Processing",
                "description": "Extract metadata and chunk document for analysis",
                "pipeline": [
                    {
                        "processor_id": "metadata_extractor",
                        "parameters": {"extract_stats": True, "detect_language": True}
                    },
                    {
                        "processor_id": "fixed_size_chunker",
                        "parameters": {"chunk_size": 1000, "overlap": 200}
                    }
                ]
            })
        
        # NER suggestion
        suggestions.append({
            "name": "Entity Extraction",
            "description": "Extract named entities from document content",
            "pipeline": [
                {
                    "processor_id": "simple_ner",
                    "parameters": {"entity_types": ["PERSON", "EMAIL", "PHONE", "URL"]}
                }
            ]
        })
        
        # Combined processing suggestion
        suggestions.append({
            "name": "Complete Analysis",
            "description": "Full document analysis with chunking and entity extraction",
            "pipeline": [
                {
                    "processor_id": "metadata_extractor",
                    "parameters": {"extract_stats": True, "detect_language": True}
                },
                {
                    "processor_id": "fixed_size_chunker",
                    "parameters": {"chunk_size": 800, "overlap": 150}
                },
                {
                    "processor_id": "simple_ner",
                    "parameters": {"entity_types": ["PERSON", "EMAIL", "PHONE", "URL", "DATE"]}
                }
            ]
        })
        
        return suggestions


# Global service instance
document_processor_service = DocumentProcessorService() 